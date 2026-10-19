"""Durchstich-Tests: Account, Charaktere aller Klassen, Weltverbindung, Kampf, Beute, Quests, Berufe, Wirtschaft."""
import math
import time

from fastapi.testclient import TestClient

from app.content import world as W
from app.content.classes import CLASSES
from app.main import app, world


def recv_until(ws, pred, limit=3000):
    seen = []
    for _ in range(limit):
        m = ws.receive_json()
        seen.append(m.get("t"))
        if pred(m):
            return m
    raise AssertionError(f"Nachricht nicht empfangen. Gesehen: {seen[-40:]}")


def tick(n=1):
    for _ in range(n):
        world.tick()


def make_account(c, name):
    r = c.post("/api/register", json={"username": name, "password": "geheim123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}, r.json()["token"]


def test_accounts_and_content():
    with TestClient(app) as c:
        h, _ = make_account(c, "tester")
        assert c.post("/api/register", json={"username": "tester", "password": "geheim123"}).status_code == 400
        assert c.post("/api/login", json={"username": "tester", "password": "falsch"}).status_code == 401
        for i, cls in enumerate(CLASSES):
            r = c.post("/api/characters", json={"name": "Held" + "abcdefgh"[i], "cls": cls, "look": {"skin": "#e0b090", "body": "f"}}, headers=h)
            assert r.status_code == 200, r.text
        chars = c.get("/api/characters", headers=h).json()["characters"]
        assert len(chars) == 8
        assert c.post("/api/characters", json={"name": "Simon", "cls": "ritter"}, headers=h).status_code == 400
        z = c.get("/api/zone/gruenmark").json()
        assert z["n"] == 241 and len(z["props"]) > 100 and z["grid"]
        assert c.get("/api/zone/krypta").json()["rects"]
        content = c.get("/api/content").json()
        assert len(content["classes"]) == 8
        assert all(len(cl["talents"]) == 3 for cl in content["classes"].values())


def _connect(c, h, token, cls, name):
    r = c.post("/api/characters", json={"name": name, "cls": cls}, headers=h)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    ws = c.websocket_connect(f"/ws?token={token}&char={cid}")
    return ws, cid


def test_play_session():
    with TestClient(app) as c:
        h, token = make_account(c, "spieler")
        with c.websocket_connect("/ws?token=x&char=1") as bad:
            assert bad.receive_json()["t"] == "kick"
        ws_cm, cid = _connect(c, h, token, "ritter", "Gloppy")
        with ws_cm as ws:
            welcome = recv_until(ws, lambda m: m["t"] == "welcome")
            pid = welcome["id"]
            p = world.players[pid]
            ws.send_json({"t": "ready"})
            # Gegner suchen und angreifen
            wolf = min((e for e in p.zone.entities.values() if getattr(e, "tpl", {}).get("id") == "waldwolf"), key=lambda e: p.dist(e))
            world.teleport(p, wolf.x + 1.5, wolf.z)
            p.r = p.angle_to(wolf)
            ws.send_json({"t": "tg", "id": wolf.id})
            ws.send_json({"t": "atk", "id": wolf.id})
            t0 = time.monotonic()
            while time.monotonic() - t0 < 40:
                tick()
                p.r = p.angle_to(wolf)
                if wolf.dead:
                    break
                if p.power >= 12:
                    world.use_ability(p, "wuchtschlag", wolf.id)
                p.hp = p.max_hp
                time.sleep(0.02)
            assert wolf.dead, "Wolf sollte tot sein"
            assert p.xp > 0
            # Quest bei Roderich annehmen
            rod = p.zone.npcs["roderich"]
            world.teleport(p, rod.x + 1, rod.z + 1)
            ws.send_json({"t": "interact", "id": rod.id})
            g = recv_until(ws, lambda m: m["t"] == "gossip")
            assert g["quests"]
            q = g["quests"][0]["id"]
            ws.send_json({"t": "quest_accept", "giver": "roderich", "q": q})
            recv_until(ws, lambda m: m["t"] == "quest_accepted")
            assert q in p.quests_active
            # Händler
            hilde = p.zone.npcs["hilde"]
            world.teleport(p, hilde.x + 1, hilde.z)
            p.copper = 1000
            ws.send_json({"t": "buy", "npc": hilde.id, "i": "frisches_brot", "n": 5})
            tick(2)
            assert p.count_item("frisches_brot") >= 10
            ws.send_json({"t": "chat", "ch": "say", "text": "Hallo Eldornia!"})
            recv_until(ws, lambda m: m["t"] == "chat" and m["text"] == "Hallo Eldornia!")
        # gespeichert?
        tick(2)
        with c.websocket_connect(f"/ws?token={token}&char={cid}") as ws:
            w2 = recv_until(ws, lambda m: m["t"] == "welcome")
            p2 = world.players[w2["id"]]
            assert p2.count_item("frisches_brot") >= 10
            assert q in p2.quests_active


def test_all_classes_abilities():
    """Jede Klasse kann jede ihrer Fähigkeiten ohne Fehler einsetzen."""
    from app.content.abilities import ABILITIES, class_abilities
    with TestClient(app) as c:
        h, token = make_account(c, "klassen")
        for i, cls in enumerate(CLASSES):
            ws_cm, cid = _connect(c, h, token, cls, "Probe" + "abcdefgh"[i])
            with ws_cm as ws:
                w = recv_until(ws, lambda m: m["t"] == "welcome")
                p = world.players[w["id"]]
                ws.send_json({"t": "ready"})
                world.admin_command(p, ".stufe 50")
                for ab in ABILITIES.values():
                    if ab["cls"] == cls and ab["talent"]:
                        p.granted.append(ab["id"])
                dummy = min((e for e in p.zone.entities.values() if getattr(e, "tpl", {}).get("id") == "uebungspuppe"), key=lambda e: p.dist(e))
                for ab_id in class_abilities(cls, True):
                    world.teleport(p, dummy.x, dummy.z + 3.0)
                    p.r = p.angle_to(dummy)
                    p.power = p.max_power
                    p.cooldowns.clear()
                    p.gcd_until = 0
                    p.cast = None
                    p.combat = False
                    p.combo = 5
                    p.combo_target = dummy.id
                    p.last_reactive = {"block": time.monotonic(), "parry": time.monotonic(), "dodge": time.monotonic()}
                    world.use_ability(p, ab_id, dummy.id)
                    if p.cast:
                        p.cast["end"] = time.monotonic() - 0.01
                        if p.cast.get("channel"):
                            p.cast["next_tick"] = time.monotonic() - 0.01
                    tick(3)
                    for pet in world.pets_of(p):
                        pass
                    if p.form():
                        world.toggle_form(p, p.form())
                    if p.has_aura("eisblock"):
                        p.remove_aura("eisblock")
                    p.hp = p.max_hp
                assert dummy.hp < dummy.max_hp


def test_dungeon_and_economy():
    with TestClient(app) as c:
        h, token = make_account(c, "dungeon")
        ws_cm, cid = _connect(c, h, token, "magier", "Feuerfuchs")
        with ws_cm as ws:
            w = recv_until(ws, lambda m: m["t"] == "welcome")
            p = world.players[w["id"]]
            ws.send_json({"t": "ready"})
            world.admin_command(p, ".stufe 15")
            portal = next(pt for pt in p.zone.cfg["portals"] if pt["to"] == "krypta")
            p.portal_lock = 0
            world.enter_portal(p, portal, "heroisch")
            assert p.zone.is_instance and p.zone.mode == "heroisch"
            boss = next(e for e in p.zone.entities.values() if getattr(e, "tpl", {}).get("id") == "morgrath")
            assert boss.max_hp > 1000
            world.add_threat(boss, p, 10)
            boss.hp = 1
            world.damage(p, boss, 50, "fire", "Feuerball")
            assert boss.dead and boss.loot.get(p.id)
            assert p.currency("dungeonmarken") > 0
            world.leave_instance(p)
            assert p.zone.id == "gruenmark"
            # Markt: einstellen und von zweitem Charakter kaufen
            ludwig = p.zone.npcs["ludwig"]
            world.teleport(p, ludwig.x + 1, ludwig.z)
            p.copper = 100000
            world.give_items(p, [("kupfererz", 10)])
            slot = next(i for i, s in enumerate(p.bags) if s and s["i"] == "kupfererz")
            world.market_post(p, {"slot": slot, "price": 500, "hours": 12})
            assert p.count_item("kupfererz") == 0
        h2, token2 = make_account(c, "kaeufer")
        ws_cm, cid2 = _connect(c, h2, token2, "barbar", "Grobian")
        with ws_cm as ws:
            w = recv_until(ws, lambda m: m["t"] == "welcome")
            b = world.players[w["id"]]
            ludwig = b.zone.npcs["ludwig"]
            world.teleport(b, ludwig.x + 1, ludwig.z)
            b.copper = 2000
            ws.send_json({"t": "market_search", "q": "Kupfer"})
            res = recv_until(ws, lambda m: m["t"] == "market")
            assert res["list"]
            world.market_buy(b, res["list"][0]["id"])
            assert b.count_item("kupfererz") == 10 and b.copper == 1500
            world.market_buy(b, res["list"][0]["id"])     # doppelt kaufen darf nicht gehen
            assert b.count_item("kupfererz") == 10 and b.copper == 1500
