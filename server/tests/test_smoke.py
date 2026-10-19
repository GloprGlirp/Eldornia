import time

from fastapi.testclient import TestClient

from app.main import app


def recv_until(ws, pred, limit=400):
    for _ in range(limit):
        m = ws.receive_json()
        if pred(m):
            return m
    raise AssertionError("Nachricht nicht empfangen")


def test_full_flow():
    with TestClient(app) as c:
        r = c.post("/api/register", json={"username": "tester", "password": "geheim123"})
        assert r.status_code == 200, r.text
        tok = r.json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = c.post("/api/characters", json={"name": "Gloppy", "cls": "ritter", "look": {"skin": "#e0b090"}}, headers=h)
        assert r.status_code == 200, r.text
        cid = r.json()["id"]
        assert c.get("/api/characters", headers=h).json()["characters"][0]["name"] == "Gloppy"
        z = c.get("/api/zone/gruenmark").json()
        assert z["n"] == 241 and len(z["props"]) > 100
        assert c.get("/api/zone/krypta").json()["rects"]
        content = c.get("/api/content").json()
        assert "rostiges_langschwert" in content["items"]
        with c.websocket_connect(f"/ws?token={tok}&char={cid}") as ws:
            w = recv_until(ws, lambda m: m["t"] == "welcome")
            me = w["you"]
            ws.send_json({"t": "ready"})
            u = recv_until(ws, lambda m: m["t"] == "u" and "sp" in m)
            ents = {e["id"]: e for e in u["sp"]}
            npcs = {e.get("npc"): e for e in ents.values() if e["k"] == "npc"}
            assert "roderich" in npcs and npcs["roderich"]["fl"]["q"] == "!"
            rod = npcs["roderich"]
            # zu Roderich laufen
            x, y, zz, r = w["p"]
            tx, tz = rod["p"][0], rod["p"][2] + 2
            ws.send_json({"t": "move", "x": tx, "y": 0, "z": tz, "r": 0, "m": False})
            ws.send_json({"t": "interact", "id": rod["id"]})
            g = recv_until(ws, lambda m: m["t"] in ("gossip", "force"))
            assert g["t"] == "gossip", g
            assert any(q["id"] == "wolfsplage" for q in g["quests"])
            ws.send_json({"t": "quest_accept", "id": rod["id"], "q": "wolfsplage"})
            q = recv_until(ws, lambda m: m["t"] == "quests")
            assert q["log"][0]["id"] == "wolfsplage"
            # Admin: zu den Wölfen teleportieren und einen Wolf angreifen
            ws.send_json({"t": "chat", "ch": "say", "text": ".stufe 5"})
            ws.send_json({"t": "chat", "ch": "say", "text": ".tp -62 -58"})
            f = recv_until(ws, lambda m: m["t"] == "force")
            wolves = {}
            t0 = time.time()
            while time.time() - t0 < 3:
                m = ws.receive_json()
                if m["t"] == "u":
                    for e in m.get("sp", []):
                        if e.get("mob") == "waldwolf":
                            wolves[e["id"]] = e
                if wolves:
                    break
            assert wolves, "keine Wölfe gesehen"
            wolf = min(wolves.values(), key=lambda e: (e["p"][0] + 62) ** 2 + (e["p"][2] + 58) ** 2)
            import math
            wx, wz = wolf["p"][0], wolf["p"][2]
            px, pz = wx + 1.8, wz
            ws.send_json({"t": "chat", "ch": "say", "text": f".tp {px} {pz}"})
            recv_until(ws, lambda m: m["t"] == "force")
            ws.send_json({"t": "target", "id": wolf["id"]})
            ws.send_json({"t": "move", "x": px, "y": 0, "z": pz, "r": math.atan2(-(wx - px), -(wz - pz)), "m": False})
            ws.send_json({"t": "attack", "id": wolf["id"]})
            dmg_events = 0
            died = False
            t0 = time.time()
            while time.time() - t0 < 40 and not died:
                m = ws.receive_json()
                if m["t"] == "u":
                    for ev in m.get("ev", []):
                        if ev["s"] == me and ev["d"] == wolf["id"]:
                            dmg_events += 1
                    for d in m.get("e", []):
                        if d["id"] == wolf["id"] and d.get("st", 0) & 1:
                            died = True
                        if d["id"] == wolf["id"] and "p" in d:
                            wx, wz = d["p"][0], d["p"][2]
                    # immer zum Wolf schauen
                    ws.send_json({"t": "move", "x": px, "y": 0, "z": pz, "r": math.atan2(-(wx - px), -(wz - pz)), "m": False})
                    if m.get("ev") and dmg_events % 3 == 0:
                        ws.send_json({"t": "cast", "ab": "wuchtschlag", "tid": wolf["id"]})
            assert dmg_events > 0
            assert died, "Wolf nicht gestorben"
