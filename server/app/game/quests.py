"""Quests (GDD 7): Haupt-, Neben-, Tages-, Wochen-, Klassen-, versteckte und Kopfgeldquests."""
from __future__ import annotations

import time

from ..content import world as W
from ..content.items import ITEMS, item_client_info
from .entities import Mob, Npc, Player, now

QUEST_LOG_MAX = 25
TYPE_NAMES = {"main": "Hauptquest", "side": "Nebenquest", "daily": "Täglicher Auftrag", "weekly": "Wöchentliche Herausforderung",
              "class": "Klassenquest", "hidden": "Versteckte Quest", "bounty": "Kopfgeld", "event": "Ereignis"}


class QuestMixin:
    # ================================================================== Zustand
    def quest_done_recently(self, p: Player, qid: str) -> bool:
        q = W.QUESTS[qid]
        ts = p.quests_done.get(qid)
        if ts is None:
            return False
        if q["type"] == "daily":
            return ts > self.next_daily_reset() - 86400
        if q["type"] == "weekly":
            return ts > self.next_weekly_reset() - 7 * 86400
        if q["type"] == "bounty":
            return ts > self.next_daily_reset() - 86400
        return True

    def quest_available(self, p: Player, qid: str) -> bool:
        q = W.QUESTS[qid]
        if qid in p.quests_active or self.quest_done_recently(p, qid):
            return False
        if p.level < q["min_level"]:
            return False
        if q.get("cls") and q["cls"] != p.class_id:
            return False
        if q.get("prev") and q["prev"] not in p.quests_done:
            return False
        if q.get("req_rep"):
            from ..content.factions import required_standing, standing
            fid, name = q["req_rep"]
            if standing(p.reputation.get(fid, 0)) < required_standing(name):
                return False
        return True

    def quest_progress(self, p: Player, qid: str) -> tuple[list[dict], bool]:
        q = W.QUESTS[qid]
        prog = p.quests_active.get(qid, [])
        out = []
        done = True
        for i, o in enumerate(q["objectives"]):
            if o["type"] == "collect":
                have = min(o["count"], p.count_item(o["item"]))
                text = o.get("text") or ITEMS[o["item"]]["name"]
            else:
                have = min(o["count"], prog[i] if i < len(prog) else 0)
                if o["type"] == "kill":
                    mobs = o["mob"] if isinstance(o["mob"], list) else [o["mob"]]
                    text = o.get("text") or (W.MOBS[mobs[0]]["name"] + " besiegt")
                else:
                    text = o.get("text") or o["type"]
            out.append({"text": text, "have": have, "need": o["count"]})
            if have < o["count"]:
                done = False
        return out, done

    def quest_state_for(self, p: Player, qid: str) -> str | None:
        if qid in p.quests_active:
            _, done = self.quest_progress(p, qid)
            return "complete" if done else "active"
        if self.quest_available(p, qid):
            return "available"
        return None

    def quest_marker(self, p: Player, npc_id: str) -> str | None:
        best = None
        for qid in W.QUESTS_BY_ENDER.get(npc_id, []):
            if qid in p.quests_active:
                _, done = self.quest_progress(p, qid)
                if done:
                    return "?b" if W.QUESTS[qid]["type"] in ("daily", "weekly") else "?"
                best = best or "?g"
        for qid in W.QUESTS_BY_GIVER.get(npc_id, []):
            q = W.QUESTS[qid]
            if q["type"] == "hidden":
                continue
            if self.quest_available(p, qid):
                if q["type"] in ("daily", "weekly"):
                    if best not in ("!",):
                        best = "!b"
                else:
                    return "!"
            elif p.level < q["min_level"] <= p.level + 3 and not self.quest_done_recently(p, qid) and qid not in p.quests_active \
                    and (not q.get("prev") or q["prev"] in p.quests_done) and (not q.get("cls") or q["cls"] == p.class_id):
                best = best or "!g"
        return best

    def mob_needed_for_quest(self, p: Player, mob: Mob) -> bool:
        mid = mob.tpl["id"]
        for qid, prog in p.quests_active.items():
            q = W.QUESTS[qid]
            for i, o in enumerate(q["objectives"]):
                if o["type"] == "kill":
                    mobs = o["mob"] if isinstance(o["mob"], list) else [o["mob"]]
                    if mid in mobs and (prog[i] if i < len(prog) else 0) < o["count"]:
                        return True
                elif o["type"] == "collect" and p.count_item(o["item"]) < o["count"]:
                    if any(l["item"] == o["item"] for l in mob.tpl.get("loot", [])):
                        return True
        return False

    # ================================================================== Fortschritt
    def _bump(self, p: Player, match) -> bool:
        changed = False
        for qid, prog in list(p.quests_active.items()):
            q = W.QUESTS[qid]
            for i, o in enumerate(q["objectives"]):
                if match(o) and i < len(prog) and prog[i] < o["count"]:
                    prog[i] += 1
                    changed = True
                    _, done = self.quest_progress(p, qid)
                    text = o.get("text") or (W.MOBS[o["mob"] if isinstance(o["mob"], str) else o["mob"][0]]["name"] + " besiegt"
                                             if o["type"] == "kill" else o["type"])
                    self.send(p, {"t": "qprog", "q": qid, "text": f"{text}: {prog[i]}/{o['count']}", "done": done})
                    if done:
                        self.sys(p, f"{q['title']} (abgeschlossen)")
        if changed:
            p.save_dirty = True
            self.send_quests(p)
        return changed

    def quest_kill(self, p: Player, mob_id: str):
        def m(o):
            if o["type"] != "kill":
                return False
            return mob_id in (o["mob"] if isinstance(o["mob"], list) else [o["mob"]])
        self._bump(p, m)
        # Gruppenmitglieder in der Nähe erhalten ebenfalls Fortschritt (WoW-artig)
        if p.party:
            for mm in self.party_players(p.party):
                if mm is not p and mm.zone is p.zone and mm.dist(p) < 80 and not mm.dead and mm.id not in getattr(p.zone, "_qk", ()):
                    pass
        if mob_id.startswith(("waldwolf", "schattenwolf", "graumaehne", "frostwolf", "mondwolf")):
            self.progress_counter(p, "kills_wolf", 1)

    def quest_event(self, p: Player, event: str, n: int = 1):
        for _ in range(n):
            self._bump(p, lambda o: o["type"] == "event" and o["event"] == event)

    def quest_talk(self, p: Player, npc_id: str) -> bool:
        return self._bump(p, lambda o: o["type"] == "talk" and o["npc"] == npc_id)

    def quest_emote(self, p: Player, emote: str, npc_id: str):
        self._bump(p, lambda o: o["type"] == "emote" and o["npc"] == npc_id and o.get("emote") in (emote, None))

    def quest_explore(self, p: Player, zone_id: str, subzone: str | None = None):
        def m(o):
            if o["type"] != "explore":
                return False
            if o.get("zone") and o["zone"] != zone_id:
                return False
            if o.get("subzone") and o["subzone"] != subzone:
                return False
            if not o.get("subzone") and subzone is not None:
                return False
            return True
        self._bump(p, m)

    def quest_items_changed(self, p: Player):
        """Nach Inventaränderungen: Sammelziele neu bewerten."""
        if any(o["type"] == "collect" for qid in p.quests_active for o in W.QUESTS[qid]["objectives"]):
            self.send_quests(p)

    # ================================================================== Dialoge
    def quest_payload(self, q: dict, p: Player) -> dict:
        r = q["rewards"]
        items = [it[0] for it in r.get("items", [])] + list(r.get("choice", []))
        return {
            "id": q["id"], "title": q["title"], "text": q.get("text", ""), "objective": q.get("objective", ""),
            "level": q["level"], "type": q["type"], "type_name": TYPE_NAMES.get(q["type"], ""),
            "rewards": {"xp": self.quest_xp(p, q), "copper": r.get("copper", 0), "items": r.get("items", []),
                        "choice": r.get("choice", []), "rep": r.get("rep", {}), "currency": r.get("currency", {}),
                        "title": r.get("title")},
            "items": {i: item_client_info(i) for i in items if i in ITEMS},
            "dungeon": W.ZONES[q["dungeon"]]["name"] if q.get("dungeon") in W.ZONES else None,
        }

    def quest_xp(self, p: Player, q: dict) -> int:
        xp = q["rewards"].get("xp", 0)
        diff = p.level - q["level"]
        if diff >= 8:
            return int(xp * 0.1)
        if diff >= 6:
            return int(xp * 0.4)
        if diff >= 4:
            return int(xp * 0.7)
        return xp

    def gossip_quests(self, p: Player, giver_id: str) -> list:
        quests = []
        for qid in W.QUESTS_BY_ENDER.get(giver_id, []):
            st = self.quest_state_for(p, qid)
            if st in ("complete", "active"):
                quests.append({"id": qid, "title": W.QUESTS[qid]["title"], "state": st, "type": W.QUESTS[qid]["type"]})
        for qid in W.QUESTS_BY_GIVER.get(giver_id, []):
            if self.quest_available(p, qid) and not any(x["id"] == qid for x in quests):
                quests.append({"id": qid, "title": W.QUESTS[qid]["title"], "state": "available", "type": W.QUESTS[qid]["type"]})
        return quests

    def open_gossip(self, p: Player, npc: Npc):
        tpl = npc.tpl
        npc.talk_until = now() + 12
        npc.r = npc.angle_to(p)
        npc.mark("p")
        self.quest_talk(p, npc.npc_id)
        p.misc["_gossip_npc"] = npc.id
        quests = self.gossip_quests(p, npc.npc_id)
        self.send(p, {"t": "gossip", "npc": npc.id, "npc_id": npc.npc_id, "name": npc.name, "title": npc.title,
                      "text": tpl.get("greeting", "Seid gegrüßt."), "quests": quests, "services": tpl.get("services", []),
                      "options": tpl.get("options", []), "look": npc.look, "model": npc.model})

    def open_board(self, p: Player, board_zone: str, obj_id: int):
        giver = "board:" + board_zone
        quests = self.gossip_quests(p, giver)
        self.send(p, {"t": "gossip", "npc": obj_id, "npc_id": giver, "name": "Anschlagbrett", "title": "Kopfgelder",
                      "text": "Gesucht – tot oder lebendig (lieber tot). Belohnung bei Abgabe am Brett.", "quests": quests,
                      "services": [], "options": []})

    def show_quest(self, p: Player, giver_id: str, qid: str):
        q = W.QUESTS.get(qid)
        if not q:
            return
        st = self.quest_state_for(p, qid)
        if st == "available" and q["giver"] == giver_id:
            self.send(p, {"t": "quest_detail", "mode": "offer", "giver": giver_id, "q": self.quest_payload(q, p)})
        elif st == "complete" and q["ender"] == giver_id:
            pl = self.quest_payload(q, p)
            pl["text"] = q["complete"]
            self.send(p, {"t": "quest_detail", "mode": "complete", "giver": giver_id, "q": pl})
        elif st == "active" and q["ender"] == giver_id:
            pl = self.quest_payload(q, p)
            pl["text"] = q["progress"]
            pl["progress"], _ = self.quest_progress(p, qid)
            self.send(p, {"t": "quest_detail", "mode": "progress", "giver": giver_id, "q": pl})

    def accept_quest(self, p: Player, giver_id: str, qid: str):
        q = W.QUESTS.get(qid)
        if not q or q["giver"] != giver_id or not self.quest_available(p, qid):
            return
        if len(p.quests_active) >= QUEST_LOG_MAX:
            self.err(p, "Euer Questlog ist voll.")
            return
        if q.get("start_item") and not p.add_items([(q["start_item"], 1, True)]):
            self.err(p, "Eure Taschen sind voll.")
            return
        p.quests_active[qid] = [0] * len(q["objectives"])
        p.save_dirty = True
        self.sys(p, f"Quest angenommen: {q['title']}")
        self.send(p, {"t": "quest_accepted", "q": qid, "title": q["title"]})
        # bereits erledigte Ziele (z. B. Erkundung der aktuellen Zone)
        if p.zone:
            self.quest_explore(p, p.zone.id)
        self.send_quests(p)
        self.send_inventory(p)
        self.refresh_markers(p)

    def complete_quest(self, p: Player, giver_id: str, qid: str, choice: int | None):
        q = W.QUESTS.get(qid)
        if not q or q["ender"] != giver_id or qid not in p.quests_active:
            return
        _, done = self.quest_progress(p, qid)
        if not done:
            return
        r = q["rewards"]
        rewards = [(i[0], i[1], ITEMS[i[0]].get("bind") == "bop") for i in r.get("items", [])]
        if r.get("choice"):
            if choice is None or not (0 <= int(choice) < len(r["choice"])):
                self.err(p, "Wählt eine Belohnung.")
                return
            iid = r["choice"][int(choice)]
            rewards.append((iid, 1, ITEMS[iid].get("bind") == "bop"))
        # Sammelgegenstände entfernen (vorher Platz prüfen)
        removed = []
        for o in q["objectives"]:
            if o["type"] == "collect":
                removed.append((o["item"], p.remove_item(o["item"], o["count"])))
        if q.get("start_item"):
            p.remove_item(q["start_item"], 1)
        if rewards and not p.add_items(rewards):
            for iid, n in removed:
                if n:
                    p.add_items([(iid, n)])
            self.err(p, "Eure Taschen sind voll.")
            return
        del p.quests_active[qid]
        p.quests_done[qid] = time.time()
        p.copper += r.get("copper", 0)
        self.progress_counter(p, "quests", 1)
        if q["type"] == "daily":
            self.progress_counter(p, "dailies", 1)
        if q["type"] == "bounty":
            self.progress_counter(p, "bounties", 1)
        for fid, amount in r.get("rep", {}).items():
            self.add_rep(p, fid, amount)
        for cid, amount in r.get("currency", {}).items():
            p.add_currency(cid, amount)
            self.sys(p, f"Erhalten: {amount}× {cid}")
        if r.get("title"):
            self.grant_title(p, r["title"])
        p.save_dirty = True
        self.sys(p, f"{q['title']} abgeschlossen.")
        if r.get("copper"):
            self.sys(p, f"Erhalten: {self.fmt_money(r['copper'])}.")
        self.send(p, {"t": "quest_done", "q": qid, "title": q["title"]})
        xp = self.quest_xp(p, q)
        if xp:
            self.add_xp(p, xp)
        self.send_inventory(p)
        self.send_quests(p)
        self.check_achievements(p, "quest")
        self.refresh_markers(p)
        # Folgequest direkt anbieten
        for nqid in W.QUESTS_BY_GIVER.get(giver_id, []):
            if W.QUESTS[nqid].get("prev") == qid and self.quest_available(p, nqid):
                self.show_quest(p, giver_id, nqid)
                break

    def abandon_quest(self, p: Player, qid: str):
        if qid not in p.quests_active:
            return
        q = W.QUESTS[qid]
        del p.quests_active[qid]
        if q.get("start_item"):
            p.remove_item(q["start_item"], 1)
        p.save_dirty = True
        self.sys(p, f"Quest abgebrochen: {q['title']}")
        self.send_quests(p)
        self.send_inventory(p)
        self.refresh_markers(p)

    def refresh_markers(self, p: Player):
        """Questmarkierungen der sichtbaren NPCs sofort aktualisieren."""
        p.flag_cache = {k: v for k, v in p.flag_cache.items() if not isinstance(p.zone.entities.get(k), Npc)}

    def send_quests(self, p: Player):
        out = []
        for qid in p.quests_active:
            q = W.QUESTS[qid]
            prog, done = self.quest_progress(p, qid)
            ender = W.NPCS.get(q["ender"])
            out.append({"id": qid, "title": q["title"], "level": q["level"], "type": q["type"], "objective": q.get("objective", ""),
                        "text": q.get("text", ""), "progress": prog, "done": done,
                        "ender": ender["name"] if ender else ("Anschlagbrett" if q["ender"].startswith("board:") else q["ender"]),
                        "ender_pos": ender["pos"] if ender and ender["zone"] == (p.zone.id if p.zone else "") else None,
                        "zone": W.ZONES.get(ender["zone"], {}).get("name") if ender else None,
                        "targets": self.quest_target_hints(p, q)})
        self.send(p, {"t": "quests", "quests": out, "done": len(p.quests_done)})

    def quest_target_hints(self, p: Player, q: dict) -> list:
        """Grobe Kartenhinweise (Spawngebiete der benötigten Gegner/Objekte) für Minimap und Weltkarte."""
        if not p.zone:
            return []
        zid = p.zone.id
        hints = []
        for o in q["objectives"]:
            if o["type"] == "kill":
                mobs = o["mob"] if isinstance(o["mob"], list) else [o["mob"]]
                for s in W.SPAWNS.get(zid, []):
                    if s["mob"] in mobs:
                        if "pos" in s:
                            hints.append([s["pos"][0], s["pos"][1], 8])
                        else:
                            hints.append([s["x"], s["z"], s["r"]])
            elif o["type"] == "collect":
                for s in W.SPAWNS.get(zid, []):
                    tpl = W.MOBS[s["mob"]]
                    if any(l["item"] == o["item"] for l in tpl.get("loot", [])):
                        hints.append([s["x"], s["z"], s["r"]] if "x" in s else [s["pos"][0], s["pos"][1], 8])
                pts = [ob["pos"] for ob in W.OBJECTS.get(zid, []) if ob.get("item") == o["item"]]
                if pts:
                    cx = sum(pt[0] for pt in pts) / len(pts)
                    cz = sum(pt[1] for pt in pts) / len(pts)
                    rad = max(10.0, max(((pt[0] - cx) ** 2 + (pt[1] - cz) ** 2) ** 0.5 for pt in pts))
                    hints.append([cx, cz, rad])
            elif o["type"] in ("talk", "emote"):
                n = W.NPCS.get(o["npc"])
                if n and n["zone"] == zid:
                    hints.append([n["pos"][0], n["pos"][1], 3])
        return hints[:6]
