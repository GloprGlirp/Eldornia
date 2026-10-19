"""Verarbeitung der Client-Nachrichten: Bewegung, Ziel, Interaktion, Quests, Inventar, Handel, Chat, Gruppen."""
from __future__ import annotations

import math
import random
import time

from .. import config
from .content import world as W
from .content.abilities import ABILITIES, ability_client_info
from .content.classes import MAX_LEVEL, xp_to_next
from .content.items import EQUIP_SLOTS, ITEMS, RARITY_NAMES, item_usable_by
from .content.mobs import MOBS
from .content.npcs import NPCS
from .content.quests import QUESTS, quests_ended_by, quests_given_by
from .entities import RUN_SPEED, Aura, GameObj, Mob, Npc, Player, now

QUEST_LOG_MAX = 20
INTERACT_RANGE = 6.0
EMOTES = {
    "tanzen": ("dance", "tanzt."), "winken": ("wave", "winkt."), "verbeugen": ("bow", "verbeugt sich."),
    "lachen": ("laugh", "lacht."), "jubeln": ("cheer", "jubelt."), "sitzen": ("sit", "setzt sich."),
    "weinen": ("cry", "weint."), "zeigen": ("point", "zeigt nach vorn."), "salutieren": ("salute", "salutiert."),
}


def fmt_money(copper: int) -> str:
    g, rest = divmod(copper, 10000)
    s, c = divmod(rest, 100)
    parts = []
    if g:
        parts.append(f"{g} Gold")
    if s:
        parts.append(f"{s} Silber")
    if c or not parts:
        parts.append(f"{c} Kupfer")
    return " ".join(parts)


class ActionsMixin:
    # ================================================================= An- und Abmelden
    def add_player(self, p: Player):
        old = self.by_char.get(p.char_id)
        if old:
            self.remove_player(old)
            if old.session:
                old.session.kick("Dieser Charakter wurde an anderer Stelle angemeldet.")
        zone_id = p.zone_id if p.zone_id in self.zones else "gruenmark"
        zone = self.zones[zone_id]
        p.x, p.z = zone.walkable_clamp(p.x, p.z)
        p.y = zone.height(p.x, p.z)
        zone.add(p)
        self.players[p.id] = p
        self.by_name[p.name.lower()] = p
        self.by_char[p.char_id] = p
        p.move_budget = 12.0
        p.move_budget_t = now()
        self.send(p, {"t": "welcome", "you": p.id, "name": p.name, "cls": p.class_id, "zone": zone.id,
                      "zname": zone.cfg["name"], "p": [round(p.x, 2), round(p.y, 2), round(p.z, 2), round(p.r, 3)],
                      "version": config.VERSION, "world": W.WORLD_NAME})
        self.send_stats(p)
        self.send_abilities(p)
        self.send_inventory(p)
        self.send_quests(p)
        self.sys(p, f"Willkommen in {W.WORLD_NAME}, {p.name}!")
        online = len(self.players)
        self.sys(p, f"Spieler online: {online}. Mit /hilfe seht Ihr alle Befehle.")

    def remove_player(self, p: Player):
        if p.party:
            self.leave_party(p, silent=True)
        if p.zone:
            for e in p.zone.entities.values():
                if isinstance(e, Mob) and p.id in e.threat:
                    del e.threat[p.id]
            p.zone.remove(p)
        self.players.pop(p.id, None)
        if self.by_name.get(p.name.lower()) is p:
            self.by_name.pop(p.name.lower(), None)
        if self.by_char.get(p.char_id) is p:
            self.by_char.pop(p.char_id, None)

    def save_data(self, p: Player) -> dict:
        d = p.record_data()
        if p.zone and p.zone.is_instance:
            ex = p.zone.cfg["exit"]
            d.update({"zone": ex[0], "x": ex[1], "y": 0.0, "z": ex[2], "rot": ex[3]})
        else:
            d.update({"zone": p.zone.id if p.zone else "gruenmark", "x": p.x, "y": p.y, "z": p.z, "rot": p.r})
        return d

    # ================================================================= Nachrichten an den Client
    def send_stats(self, p: Player):
        st = p.stats
        self.send(p, {"t": "stats", "lvl": p.level, "xp": p.xp, "xpmax": xp_to_next(p.level), "maxlvl": MAX_LEVEL,
                      "copper": p.copper,
                      "s": {k: (round(v, 1) if isinstance(v, float) else v) for k, v in st.items()}})

    def send_abilities(self, p: Player):
        lst = []
        for a in p.cls["abilities"]:
            info = ability_client_info(a, p.level)
            info["known"] = ABILITIES[a]["level"] <= p.level
            lst.append(info)
        self.send(p, {"t": "abilities", "list": lst})

    def send_inventory(self, p: Player):
        self.send(p, {"t": "inv", "bags": p.bags, "eq": p.equipment, "copper": p.copper})

    def quest_progress(self, p: Player, qid: str) -> tuple[list[dict], bool]:
        q = QUESTS[qid]
        counts = p.quests_active.get(qid, [])
        out = []
        done = True
        for i, o in enumerate(q["objectives"]):
            if o["type"] == "kill":
                have = counts[i] if i < len(counts) else 0
                text = f"{MOBS[o['mob']]['name']} getötet"
            else:
                have = p.count_item(o["item"])
                text = ITEMS[o["item"]]["name"]
            have = min(have, o["count"])
            if have < o["count"]:
                done = False
            out.append({"text": text, "have": have, "need": o["count"]})
        return out, done

    def send_quests(self, p: Player):
        log = []
        for qid in p.quests_active:
            q = QUESTS[qid]
            objs, done = self.quest_progress(p, qid)
            log.append({"id": qid, "title": q["title"], "level": q["level"], "text": q["text"],
                        "objective": q["objective"], "objectives": objs, "complete": done,
                        "ender": NPCS[q["ender"]]["name"], "elite": "Elite" in q["objective"] or "Dungeon" in q["text"]})
        self.send(p, {"t": "quests", "log": log, "done": len(p.quests_done)})

    def send_party(self, party):
        members = []
        for mid in party.members:
            m = self.players.get(mid)
            if not m:
                continue
            members.append({"id": m.id, "name": m.name, "lvl": m.level, "cls": m.class_id, "hp": m.hp, "mhp": m.max_hp,
                            "pw": int(m.power), "mpw": m.max_power, "pt": m.power_type, "dead": m.dead,
                            "zone": m.zone.cfg["name"] if m.zone else "", "zkey": m.zone.key if m.zone else "",
                            "x": round(m.x, 1), "z": round(m.z, 1), "au": m.client_auras(now())})
        for mid in party.members:
            m = self.players.get(mid)
            if m:
                self.send(m, {"t": "party", "leader": party.leader, "members": members})

    # ================================================================= Questlogik
    def quest_state_for(self, p: Player, qid: str) -> str | None:
        q = QUESTS[qid]
        if qid in p.quests_done:
            return None
        if qid in p.quests_active:
            _, done = self.quest_progress(p, qid)
            return "complete" if done else "active"
        if q["prev"] and q["prev"] not in p.quests_done:
            return None
        if p.level < q["min_level"]:
            return None
        return "available"

    def quest_marker(self, p: Player, npc_id: str) -> str | None:
        mark = None
        for q in quests_ended_by(npc_id):
            if q["id"] in p.quests_active:
                st = self.quest_state_for(p, q["id"])
                if st == "complete":
                    return "?"
                mark = "g?"
        for q in quests_given_by(npc_id):
            if self.quest_state_for(p, q["id"]) == "available":
                return "!"
        return mark

    def quest_kill(self, p: Player, mob_id: str):
        changed = False
        for qid, counts in p.quests_active.items():
            q = QUESTS[qid]
            for i, o in enumerate(q["objectives"]):
                if o["type"] == "kill" and o["mob"] == mob_id:
                    while len(counts) <= i:
                        counts.append(0)
                    if counts[i] < o["count"]:
                        counts[i] += 1
                        changed = True
                        self.send(p, {"t": "qprog", "text": f"{MOBS[mob_id]['name']} getötet: {counts[i]}/{o['count']}"})
                        _, done = self.quest_progress(p, qid)
                        if done:
                            self.send(p, {"t": "qprog", "text": f"{q['title']} (Abgeschlossen)", "done": True})
        if changed:
            self.send_quests(p)

    def quest_payload(self, q: dict, p: Player) -> dict:
        objs, done = self.quest_progress(p, q["id"]) if q["id"] in p.quests_active else (
            [{"text": (f"{MOBS[o['mob']]['name']} getötet" if o["type"] == "kill" else ITEMS[o["item"]]["name"]),
              "have": 0, "need": o["count"]} for o in q["objectives"]], False)
        rw = q["rewards"]
        return {"id": q["id"], "title": q["title"], "level": q["level"], "text": q["text"], "objective": q["objective"],
                "objectives": objs, "progress": q["progress"], "complete_text": q["complete"],
                "rewards": {"xp": rw.get("xp", 0) if p.level < MAX_LEVEL else 0, "copper": rw["copper"],
                            "items": rw["items"], "choice": rw["choice"]}}

    def open_gossip(self, p: Player, npc: Npc):
        quests = []
        for q in quests_ended_by(npc.npc_id):
            st = self.quest_state_for(p, q["id"])
            if st in ("complete", "active"):
                quests.append({"id": q["id"], "title": q["title"], "state": st, "level": q["level"]})
        for q in quests_given_by(npc.npc_id):
            if self.quest_state_for(p, q["id"]) == "available":
                quests.append({"id": q["id"], "title": q["title"], "state": "available", "level": q["level"]})
        npc.talk_until = now() + 12
        npc.r = npc.angle_to(p)
        npc.mark("p")
        self.send(p, {"t": "gossip", "id": npc.id, "npc": npc.npc_id, "name": npc.name, "title": npc.title,
                      "text": npc.tpl.get("greeting", "Seid gegrüßt."), "quests": quests,
                      "vendor": bool(npc.tpl.get("vendor"))})

    def show_quest(self, p: Player, npc: Npc, qid: str):
        q = QUESTS.get(qid)
        if not q:
            return
        st = self.quest_state_for(p, qid)
        if st == "available" and q["giver"] == npc.npc_id:
            mode = "offer"
        elif st == "complete" and q["ender"] == npc.npc_id:
            mode = "complete"
        elif st == "active" and q["ender"] == npc.npc_id:
            mode = "progress"
        else:
            return
        self.send(p, {"t": "quest", "id": npc.id, "name": npc.name, "mode": mode, "q": self.quest_payload(q, p)})

    def accept_quest(self, p: Player, npc: Npc, qid: str):
        q = QUESTS.get(qid)
        if not q or q["giver"] != npc.npc_id or self.quest_state_for(p, qid) != "available":
            return
        if len(p.quests_active) >= QUEST_LOG_MAX:
            self.err(p, "Euer Questlog ist voll.")
            return
        if q["start_item"]:
            if not p.add_items([(q["start_item"], 1)]):
                self.err(p, "Euer Inventar ist voll.")
                return
            self.send_inventory(p)
        p.quests_active[qid] = [0] * len(q["objectives"])
        self.sys(p, f"Quest angenommen: {q['title']}")
        self.send(p, {"t": "qaccept", "id": qid, "title": q["title"]})
        self.send_quests(p)
        # Botenquests ohne Ziele sind sofort abgabebereit, wenn Geber == Abgeber
        if q["ender"] == npc.npc_id:
            self.open_gossip(p, npc)

    def complete_quest(self, p: Player, npc: Npc, qid: str, choice: int | None):
        q = QUESTS.get(qid)
        if not q or q["ender"] != npc.npc_id or self.quest_state_for(p, qid) != "complete":
            return
        rw = q["rewards"]
        items = list(rw["items"])
        if rw["choice"]:
            if choice is None or not (0 <= choice < len(rw["choice"])):
                self.err(p, "Bitte wählt eine Belohnung aus.")
                return
            items.append((rw["choice"][choice], 1))
        # Questgegenstände entfernen (vorher prüfen, ob Belohnungen passen)
        backup = [list(s) if s else None for s in p.bags]
        for o in q["objectives"]:
            if o["type"] == "collect":
                p.remove_item(o["item"], o["count"])
        if q["start_item"]:
            p.remove_item(q["start_item"], 1)
        if items and not p.add_items([(i, n) for i, n in items]):
            p.bags = backup
            self.err(p, "Euer Inventar ist voll.")
            return
        del p.quests_active[qid]
        p.quests_done.add(qid)
        p.copper += rw["copper"]
        self.send(p, {"t": "qdone", "id": qid, "title": q["title"], "xp": rw.get("xp", 0), "copper": rw["copper"]})
        self.sys(p, f"{q['title']} abgeschlossen.")
        if rw["copper"]:
            self.sys(p, f"Ihr erhaltet: {fmt_money(rw['copper'])}.")
        for i, n in items:
            self.sys(p, f"Ihr erhaltet: [{ITEMS[i]['name']}]" + (f" x{n}" if n > 1 else "") + ".")
        if rw.get("xp"):
            self.add_xp(p, rw["xp"])
        self.send_inventory(p)
        self.send_quests(p)
        self.send_stats(p)
        if p.zone:
            p.zone.emit_fx(p.x, p.z, {"k": "questdone", "id": p.id})
        # Folgequest beim selben NPC direkt anbieten
        for nq in quests_given_by(npc.npc_id):
            if nq["prev"] == qid and self.quest_state_for(p, nq["id"]) == "available":
                self.show_quest(p, npc, nq["id"])
                return
        self.open_gossip(p, npc)

    def abandon_quest(self, p: Player, qid: str):
        if qid not in p.quests_active:
            return
        q = QUESTS[qid]
        del p.quests_active[qid]
        for o in q["objectives"]:
            if o["type"] == "collect" and ITEMS[o["item"]].get("quest"):
                p.remove_item(o["item"], 999)
        if q["start_item"]:
            p.remove_item(q["start_item"], 999)
        self.sys(p, f"Quest abgebrochen: {q['title']}")
        self.send_quests(p)
        self.send_inventory(p)

    # ================================================================= Nachrichten-Dispatcher
    def handle(self, p: Player, msg: dict):
        t = msg.get("t")
        h = getattr(self, f"on_{t}", None) if isinstance(t, str) and t.isidentifier() else None
        if h is None:
            return
        h(p, msg)

    def on_ready(self, p: Player, m: dict):
        p.ready = True
        p.known = set()
        p.flag_cache = {}

    def on_ping(self, p: Player, m: dict):
        self.send(p, {"t": "pong", "ts": m.get("ts")})

    def on_move(self, p: Player, m: dict):
        if not p.ready or not p.zone:
            return
        try:
            x, y, z, r = float(m["x"]), float(m["y"]), float(m["z"]), float(m["r"])
        except (KeyError, TypeError, ValueError):
            return
        if not all(math.isfinite(v) for v in (x, y, z, r)):
            return
        t = now()
        zone = p.zone
        p.move_budget = min(12.0, p.move_budget + (t - p.move_budget_t) * RUN_SPEED * 1.35)
        p.move_budget_t = t
        dist = math.hypot(x - p.x, z - p.z)
        if p.dead:
            if dist > 0.05:
                self.send(p, {"t": "force", "p": [p.x, p.y, p.z, p.r], "k": "tele"})
            return
        if dist > 0.05 and (p.rooted or dist > p.move_budget + 0.5):
            if p.rooted and dist < 0.6:
                return
            self.send(p, {"t": "force", "p": [round(p.x, 2), round(p.y, 2), round(p.z, 2), round(r, 3)], "k": "tele"})
            p.r = r
            p.mark("p")
            return
        p.move_budget -= dist
        x, z = zone.walkable_clamp(x, z)
        ground = zone.height(x, z)
        y = max(ground - 0.6, min(ground + 6.0, y))
        moving = bool(m.get("m"))
        if dist > 0.08:
            p.last_move_t = t
            if p.cast and not p.cast.get("allow_move"):
                self.interrupt(p)
            if p.eating:
                self.stop_eating(p)
            if p.sitting:
                p.sitting = False
                p.mark("st")
            if p.emote:
                p.emote = None
                p.mark("emote")
            if p.loot_open:
                p.loot_open = None
        p.moving = moving
        p.set_pos(x, y, z, r)
        for portal in W.PORTALS.get(zone.id, []):
            if p.dist_xz(portal["x"], portal["z"]) < portal["r"]:
                self.enter_portal(p, portal)
                break

    def on_target(self, p: Player, m: dict):
        tid = m.get("id")
        if tid is None:
            p.target = None
            p.auto_attack = False
        elif isinstance(tid, int) and p.zone and tid in p.zone.entities:
            if tid != p.target:
                p.auto_attack = False
            p.target = tid
        else:
            return
        p.mark("tg")

    def on_attack(self, p: Player, m: dict):
        tid = m.get("id", p.target)
        tgt = self.find_unit(p.zone, tid) if isinstance(tid, int) else None
        if not tgt or not isinstance(tgt, Mob) or tgt.dead or not tgt.hostile:
            self.err(p, "Ungültiges Ziel.")
            return
        if p.dead:
            return
        p.target = tgt.id
        p.mark("tg")
        p.auto_attack = True
        if p.eating:
            self.stop_eating(p)
        if p.sitting:
            p.sitting = False
            p.mark("st")

    def on_stopattack(self, p: Player, m: dict):
        p.auto_attack = False

    def on_cast(self, p: Player, m: dict):
        ab = m.get("ab")
        tid = m.get("tid")
        if not isinstance(ab, str):
            return
        if tid is not None and not isinstance(tid, int):
            tid = None
        self.use_ability(p, ab, tid)

    def on_stopcast(self, p: Player, m: dict):
        if p.cast:
            self.interrupt(p)

    def on_release(self, p: Player, m: dict):
        self.release_spirit(p)

    def on_sit(self, p: Player, m: dict):
        if p.dead or p.cast:
            return
        p.sitting = not p.sitting if m.get("toggle") else bool(m.get("v", True))
        if not p.sitting and p.eating:
            self.stop_eating(p)
        p.mark("st")

    def on_emote(self, p: Player, m: dict):
        e = m.get("e")
        if e not in EMOTES or p.dead:
            return
        anim, text = EMOTES[e]
        if anim == "sit":
            p.sitting = True
            p.mark("st")
        else:
            p.emote = anim
            p.mark("emote")
        for o in p.zone.players.values():
            if o.dist(p) < 40:
                self.send(o, {"t": "chat", "ch": "emote", "from": p.name, "fid": p.id, "text": f"{p.name} {text}"})

    # ----------------------------------------------------------------- Interaktion
    def on_interact(self, p: Player, m: dict):
        tid = m.get("id")
        e = self.find_unit(p.zone, tid) if isinstance(tid, int) else None
        if not e or p.dead:
            return
        if isinstance(e, Npc):
            if p.dist(e) > INTERACT_RANGE:
                self.err(p, "Ihr seid zu weit entfernt.")
                return
            p.target = e.id
            p.mark("tg")
            self.open_gossip(p, e)
        elif isinstance(e, Mob):
            if e.dead:
                if p.id in e.loot:
                    if p.dist(e) > INTERACT_RANGE:
                        self.err(p, "Ihr seid zu weit entfernt.")
                        return
                    self.open_loot(p, e)
                return
            if e.hostile:
                self.on_attack(p, {"id": e.id})
        elif isinstance(e, GameObj):
            if not e.available:
                return
            if p.dist(e) > INTERACT_RANGE:
                self.err(p, "Ihr seid zu weit entfernt.")
                return
            if not self.obj_usable(p, e):
                self.err(p, "Das braucht Ihr im Moment nicht.")
                return
            if p.cast:
                self.err(p, "Ihr seid gerade beschäftigt.")
                return
            if p.combat and e.obj_kind != "gackerle":
                self.err(p, "Das könnt Ihr im Kampf nicht tun.")
                return
            name = {"herb": "Kräuter sammeln", "ore": "Bergbau", "gackerle": "Huhn einfangen"}.get(e.obj_kind, "Sammeln")
            t = now()
            p.cast = {"kind": "gather", "obj": e.id, "name": name, "start": t, "end": t + 1.8,
                      "icon": {"herb": "herb", "ore": "pick", "gackerle": "chicken"}.get(e.obj_kind, "herb"),
                      "school": "nature"}
            p.mark("cast")

    # ----------------------------------------------------------------- Beute
    def open_loot(self, p: Player, mob: Mob):
        loot = mob.loot.get(p.id)
        if not loot:
            return
        p.loot_open = mob.id
        self.send(p, {"t": "loot", "id": mob.id, "name": mob.name, "copper": loot["copper"],
                      "items": [{"i": i, "id": it[0], "n": it[1]} for i, it in enumerate(loot["items"]) if it]})

    def _loot_source(self, p: Player, m: dict) -> tuple[Mob, dict] | tuple[None, None]:
        mob = self.find_unit(p.zone, m.get("id")) if isinstance(m.get("id"), int) else None
        if not isinstance(mob, Mob) or not mob.dead or p.id not in mob.loot or p.dist(mob) > INTERACT_RANGE + 2:
            return None, None
        return mob, mob.loot[p.id]

    def _finish_loot(self, p: Player, mob: Mob, loot: dict):
        if not loot["copper"] and not any(loot["items"]):
            mob.loot.pop(p.id, None)
            if not mob.loot:
                mob.corpse_until = min(mob.corpse_until, now() + 25)
            self.send(p, {"t": "loot_close", "id": mob.id})
            p.loot_open = None
        else:
            self.open_loot(p, mob)

    def take_copper(self, p: Player, loot: dict):
        if loot["copper"]:
            c = loot["copper"]
            loot["copper"] = 0
            # persönliche Beute: jedes Gruppenmitglied hat eigene Münzen im Beutefenster
            p.copper += c
            self.sys(p, f"Ihr erbeutet {fmt_money(c)}.")
            self.send_stats(p)

    def on_loot_take(self, p: Player, m: dict):
        mob, loot = self._loot_source(p, m)
        if not mob:
            return
        idx = m.get("i")
        if idx == "copper":
            self.take_copper(p, loot)
        elif isinstance(idx, int) and 0 <= idx < len(loot["items"]) and loot["items"][idx]:
            item_id, n = loot["items"][idx]
            if not p.add_items([(item_id, n)]):
                self.err(p, "Euer Inventar ist voll.")
                return
            loot["items"][idx] = None
            self.loot_message(p, item_id, n)
            self.send_inventory(p)
            self.send_quests(p)
        self._finish_loot(p, mob, loot)

    def loot_message(self, p: Player, item_id: str, n: int):
        it = ITEMS[item_id]
        self.send(p, {"t": "lootmsg", "id": item_id, "n": n, "q": it["q"]})
        if it["q"] >= 3 and p.party:
            for mid in p.party.members:
                o = self.players.get(mid)
                if o and o is not p:
                    self.send(o, {"t": "lootmsg", "id": item_id, "n": n, "q": it["q"], "who": p.name})

    def on_loot_all(self, p: Player, m: dict):
        mob, loot = self._loot_source(p, m)
        if not mob:
            return
        self.take_copper(p, loot)
        full = False
        for idx, entry in enumerate(loot["items"]):
            if not entry:
                continue
            if p.add_items([(entry[0], entry[1])]):
                loot["items"][idx] = None
                self.loot_message(p, entry[0], entry[1])
            else:
                full = True
        if full:
            self.err(p, "Euer Inventar ist voll.")
        self.send_inventory(p)
        self.send_quests(p)
        self._finish_loot(p, mob, loot)

    def on_loot_close(self, p: Player, m: dict):
        p.loot_open = None

    # ----------------------------------------------------------------- Quests
    def _npc_in_range(self, p: Player, m: dict) -> Npc | None:
        npc = self.find_unit(p.zone, m.get("id")) if isinstance(m.get("id"), int) else None
        if not isinstance(npc, Npc) or p.dist(npc) > INTERACT_RANGE + 2 or p.dead:
            return None
        return npc

    def on_quest_view(self, p: Player, m: dict):
        npc = self._npc_in_range(p, m)
        if npc and isinstance(m.get("q"), str):
            self.show_quest(p, npc, m["q"])

    def on_quest_accept(self, p: Player, m: dict):
        npc = self._npc_in_range(p, m)
        if npc and isinstance(m.get("q"), str):
            self.accept_quest(p, npc, m["q"])

    def on_quest_complete(self, p: Player, m: dict):
        npc = self._npc_in_range(p, m)
        choice = m.get("choice")
        if npc and isinstance(m.get("q"), str):
            self.complete_quest(p, npc, m["q"], choice if isinstance(choice, int) else None)

    def on_quest_abandon(self, p: Player, m: dict):
        if isinstance(m.get("q"), str):
            self.abandon_quest(p, m["q"])

    def on_gossip(self, p: Player, m: dict):
        npc = self._npc_in_range(p, m)
        if npc:
            self.open_gossip(p, npc)

    # ----------------------------------------------------------------- Händler
    def on_vendor(self, p: Player, m: dict):
        npc = self._npc_in_range(p, m)
        if not npc or not npc.tpl.get("vendor"):
            return
        self.send(p, {"t": "vendor", "id": npc.id, "name": npc.name,
                      "items": [{"id": i, "price": ITEMS[i]["buy"]} for i in npc.tpl["vendor"]]})

    def on_buy(self, p: Player, m: dict):
        npc = self._npc_in_range(p, m)
        item_id = m.get("item")
        n = m.get("n", 1)
        if not npc or not npc.tpl.get("vendor") or item_id not in npc.tpl["vendor"]:
            return
        if not isinstance(n, int) or not 1 <= n <= 20:
            return
        price = ITEMS[item_id]["buy"] * n
        if p.copper < price:
            self.err(p, "Ihr habt nicht genug Geld.")
            return
        if not p.add_items([(item_id, n)]):
            self.err(p, "Euer Inventar ist voll.")
            return
        p.copper -= price
        self.send_inventory(p)
        self.send_stats(p)

    def on_sell(self, p: Player, m: dict):
        npc = self._npc_in_range(p, m)
        slot = m.get("slot")
        if not npc or not npc.tpl.get("vendor") or not isinstance(slot, int) or not 0 <= slot < len(p.bags):
            return
        s = p.bags[slot]
        if not s:
            return
        it = ITEMS[s[0]]
        if it.get("quest") or not it.get("sell"):
            self.err(p, "Das kauft Euch niemand ab.")
            return
        p.copper += it["sell"] * s[1]
        p.bags[slot] = None
        self.send_inventory(p)
        self.send_stats(p)

    def on_sell_junk(self, p: Player, m: dict):
        npc = self._npc_in_range(p, m)
        if not npc or not npc.tpl.get("vendor"):
            return
        total = 0
        for i, s in enumerate(p.bags):
            if s and ITEMS[s[0]]["q"] == 0:
                total += ITEMS[s[0]]["sell"] * s[1]
                p.bags[i] = None
        if total:
            p.copper += total
            self.sys(p, f"Plunder verkauft für {fmt_money(total)}.")
            self.send_inventory(p)
            self.send_stats(p)

    # ----------------------------------------------------------------- Inventar
    def on_use(self, p: Player, m: dict):
        slot = m.get("slot")
        if not isinstance(slot, int) or not 0 <= slot < len(p.bags) or not p.bags[slot] or p.dead:
            return
        item_id = p.bags[slot][0]
        it = ITEMS[item_id]
        if it["type"] in ("weapon", "armor"):
            self.equip(p, slot)
            return
        use = it.get("use")
        if not use:
            return
        t = now()
        if use["type"] in ("food", "drink"):
            if p.combat:
                self.err(p, "Das könnt Ihr im Kampf nicht tun.")
                return
            if p.cast:
                self.err(p, "Ihr seid gerade beschäftigt.")
                return
            per = use["amount"] / use["dur"]
            eating = p.eating or {"until": t + use["dur"]}
            eating["until"] = max(eating.get("until", 0), t + use["dur"])
            if use["type"] == "food":
                eating["hp"] = per
                p.add_aura(Aura("essen", "Essen", p.id, t + use["dur"], use["dur"], icon="bread", color="#d9a050"))
            else:
                eating["mp"] = per
                p.add_aura(Aura("trinken", "Trinken", p.id, t + use["dur"], use["dur"], icon="water", color="#5aa0ff"))
            p.eating = eating
            p.sitting = True
            p.auto_attack = False
            p.mark("st")
        elif use["type"] in ("heal", "mana"):
            if t < p.potion_cd_until:
                self.err(p, "Dieser Gegenstand ist noch nicht bereit.")
                return
            p.potion_cd_until = t + use.get("cd", 60)
            amount = int(use["amount"] * random.uniform(0.78, 1.22))
            if use["type"] == "heal":
                self.heal(p, p, amount, it["name"])
            else:
                if p.power_type != "mana":
                    self.err(p, "Das bringt Euch nichts.")
                    p.potion_cd_until = t
                    return
                p.power = min(p.max_power, p.power + amount)
                p.mark("pw")
            p.zone.emit_fx(p.x, p.z, {"k": "potion", "id": p.id, "c": "#ff4040" if use["type"] == "heal" else "#4080ff"})
            self.send(p, {"t": "icd", "cd": use.get("cd", 60)})
        else:
            return
        p.remove_item(item_id, 1)
        self.send_inventory(p)

    def equip(self, p: Player, slot: int):
        s = p.bags[slot]
        it = ITEMS[s[0]]
        if p.combat and it["type"] == "armor" and it["slot"] not in ("main_hand", "off_hand"):
            self.err(p, "Das könnt Ihr im Kampf nicht tun.")
            return
        if it.get("lvl", 1) > p.level:
            self.err(p, f"Ihr müsst Stufe {it['lvl']} sein, um das anzulegen.")
            return
        if not item_usable_by(it, p.cls):
            self.err(p, "Das könnt Ihr nicht anlegen.")
            return
        eslot = it["slot"]
        if eslot == "ring":
            eslot = "ring1" if not p.equipment.get("ring1") else ("ring2" if not p.equipment.get("ring2") else "ring1")
        old = p.equipment.get(eslot)
        p.equipment[eslot] = s[0]
        p.bags[slot] = [old, 1] if old else None
        p.recalc()
        p.update_gear_look()
        p.swing_ready = max(p.swing_ready, now() + 0.5)
        self.send_inventory(p)
        self.send_stats(p)

    def on_unequip(self, p: Player, m: dict):
        eslot = m.get("slot")
        if eslot not in EQUIP_SLOTS or not p.equipment.get(eslot):
            return
        to = m.get("to")
        if isinstance(to, int) and 0 <= to < len(p.bags) and p.bags[to] is None:
            idx = to
        else:
            idx = next((i for i, s in enumerate(p.bags) if s is None), None)
        if idx is None:
            self.err(p, "Euer Inventar ist voll.")
            return
        p.bags[idx] = [p.equipment.pop(eslot), 1]
        p.recalc()
        p.update_gear_look()
        self.send_inventory(p)
        self.send_stats(p)

    def on_equip(self, p: Player, m: dict):
        slot = m.get("slot")
        if isinstance(slot, int) and 0 <= slot < len(p.bags) and p.bags[slot]:
            if ITEMS[p.bags[slot][0]]["type"] in ("weapon", "armor"):
                self.equip(p, slot)

    def on_swap(self, p: Player, m: dict):
        a, b = m.get("a"), m.get("b")
        n = len(p.bags)
        if not (isinstance(a, int) and isinstance(b, int) and 0 <= a < n and 0 <= b < n) or a == b:
            return
        sa, sb = p.bags[a], p.bags[b]
        if sa and sb and sa[0] == sb[0]:
            stack = ITEMS[sa[0]].get("stack", 1)
            move = min(sa[1], stack - sb[1])
            if move > 0:
                sb[1] += move
                sa[1] -= move
                if sa[1] <= 0:
                    p.bags[a] = None
                self.send_inventory(p)
                return
        p.bags[a], p.bags[b] = sb, sa
        self.send_inventory(p)

    def on_destroy(self, p: Player, m: dict):
        slot = m.get("slot")
        if isinstance(slot, int) and 0 <= slot < len(p.bags) and p.bags[slot]:
            name = ITEMS[p.bags[slot][0]]["name"]
            p.bags[slot] = None
            self.sys(p, f"{name} wurde zerstört.")
            self.send_inventory(p)
            self.send_quests(p)

    # ----------------------------------------------------------------- Chat
    def on_chat(self, p: Player, m: dict):
        text = m.get("text")
        ch = m.get("ch", "say")
        if not isinstance(text, str):
            return
        text = text.strip()[:240]
        if not text:
            return
        t = now()
        p.chat_times = [x for x in p.chat_times if t - x < 6]
        if len(p.chat_times) >= 6:
            self.err(p, "Ihr schreibt zu schnell.")
            return
        p.chat_times.append(t)
        if text.startswith("."):
            self.admin_command(p, text)
            return
        msg = {"t": "chat", "ch": ch, "from": p.name, "fid": p.id, "text": text}
        if ch == "say":
            for o in p.zone.players.values():
                if o.dist(p) < 45:
                    self.send(o, msg)
        elif ch == "yell":
            for o in p.zone.players.values():
                if o.dist(p) < 200:
                    self.send(o, msg)
        elif ch == "general":
            for o in self.players.values():
                self.send(o, msg)
        elif ch == "party":
            if not p.party:
                self.err(p, "Ihr seid in keiner Gruppe.")
                return
            for mid in p.party.members:
                o = self.players.get(mid)
                if o:
                    self.send(o, msg)
        elif ch == "whisper":
            to = m.get("to")
            o = self.by_name.get(str(to).lower()) if to else None
            if not o:
                self.err(p, f"Spieler '{to}' ist nicht online.")
                return
            msg["to"] = o.name
            self.send(o, msg)
            self.send(p, {**msg, "ch": "whisper_out"})
        elif ch == "emote":
            msg["text"] = f"{p.name} {text}"
            for o in p.zone.players.values():
                if o.dist(p) < 45:
                    self.send(o, msg)

    def admin_command(self, p: Player, text: str):
        if not (config.DEBUG_COMMANDS or p.session and p.session.username.lower() in config.ADMIN_USERS):
            self.err(p, "Unbekannter Befehl.")
            return
        parts = text[1:].split()
        cmd = parts[0].lower() if parts else ""
        arg = parts[1:] if len(parts) > 1 else []
        try:
            if cmd == "stufe" and arg:
                lvl = max(1, min(MAX_LEVEL, int(arg[0])))
                p.level = lvl
                p.xp = 0
                p.recalc(full=True)
                p.mark("lvl")
                self.send_stats(p)
                self.send_abilities(p)
            elif cmd == "gold" and arg:
                p.copper += int(float(arg[0]) * 10000)
                self.send_stats(p)
                self.send_inventory(p)
            elif cmd == "tp" and len(arg) >= 2:
                self.teleport(p, float(arg[0]), float(arg[1]))
            elif cmd == "item" and arg and arg[0] in ITEMS:
                p.add_items([(arg[0], int(arg[1]) if len(arg) > 1 else 1)])
                self.send_inventory(p)
            elif cmd == "heilen":
                p.hp = p.max_hp
                p.power = p.max_power if p.power_type == "mana" else p.power
                p.mark("hp", "pw")
            elif cmd == "krypta":
                self.enter_portal(p, W.PORTALS["gruenmark"][0])
            elif cmd == "pos":
                self.sys(p, f"Position: {p.x:.1f}, {p.z:.1f} ({p.zone.key})")
            else:
                self.sys(p, "Befehle: .stufe N, .gold N, .tp X Z, .item ID [N], .heilen, .krypta, .pos")
                return
            self.sys(p, "OK.")
        except (ValueError, IndexError):
            self.err(p, "Ungültige Eingabe.")

    def on_who(self, p: Player, m: dict):
        names = sorted(f"{o.name} (Stufe {o.level} {o.cls['name']}, {o.zone.cfg['name'] if o.zone else '?'})"
                       for o in self.players.values())
        self.sys(p, f"{len(names)} Spieler online: " + ", ".join(names[:30]))

    # ----------------------------------------------------------------- Gruppen
    def on_invite(self, p: Player, m: dict):
        name = str(m.get("name", "")).strip().lower()
        o = self.by_name.get(name)
        if not o:
            self.err(p, "Dieser Spieler ist nicht online.")
            return
        if o is p:
            self.err(p, "Ihr könnt Euch nicht selbst einladen.")
            return
        if o.party:
            self.err(p, f"{o.name} ist bereits in einer Gruppe.")
            return
        if p.party and p.party.leader != p.id:
            self.err(p, "Nur der Gruppenleiter kann einladen.")
            return
        if p.party and len(p.party.members) >= 5:
            self.err(p, "Eure Gruppe ist voll.")
            return
        o.invite_from = p.id
        self.send(o, {"t": "party_invite", "from": p.name})
        self.sys(p, f"Ihr habt {o.name} in Eure Gruppe eingeladen.")

    def on_party_accept(self, p: Player, m: dict):
        inviter = self.players.get(p.invite_from) if p.invite_from else None
        p.invite_from = None
        if not inviter or p.party:
            return
        party = inviter.party
        if party is None:
            from .world import Party
            party = Party(inviter)
            inviter.party = party
            self.parties[party.id] = party
        if len(party.members) >= 5:
            self.err(p, "Die Gruppe ist voll.")
            return
        party.members.append(p.id)
        p.party = party
        for mid in party.members:
            o = self.players.get(mid)
            if o:
                self.sys(o, f"{p.name} ist der Gruppe beigetreten.")
        self.send_party(party)

    def on_party_decline(self, p: Player, m: dict):
        inviter = self.players.get(p.invite_from) if p.invite_from else None
        p.invite_from = None
        if inviter:
            self.sys(inviter, f"{p.name} hat Eure Einladung abgelehnt.")

    def on_party_leave(self, p: Player, m: dict):
        if p.party:
            self.leave_party(p)

    def on_party_kick(self, p: Player, m: dict):
        if not p.party or p.party.leader != p.id:
            return
        o = self.by_name.get(str(m.get("name", "")).lower())
        if o and o.party is p.party and o is not p:
            self.sys(o, "Ihr wurdet aus der Gruppe entfernt.")
            self.leave_party(o)

    def leave_party(self, p: Player, silent: bool = False):
        party = p.party
        if not party:
            return
        party.members = [m for m in party.members if m != p.id]
        p.party = None
        self.send(p, {"t": "party", "leader": None, "members": []})
        if not silent:
            self.sys(p, "Ihr habt die Gruppe verlassen.")
        for mid in party.members:
            o = self.players.get(mid)
            if o:
                self.sys(o, f"{p.name} hat die Gruppe verlassen.")
        if len(party.members) <= 1:
            for mid in party.members:
                o = self.players.get(mid)
                if o:
                    o.party = None
                    self.send(o, {"t": "party", "leader": None, "members": []})
                    self.sys(o, "Eure Gruppe wurde aufgelöst.")
            self.parties.pop(party.id, None)
            return
        if party.leader == p.id:
            party.leader = party.members[0]
            o = self.players.get(party.leader)
            if o:
                self.sys(o, "Ihr seid jetzt Gruppenleiter.")
        self.send_party(party)
