"""Langzeitfortschritt (GDD 7): Talente, Erfolge, Ruf, Sammlungen (Reittiere, Haustiere, Titel, Skins),
Erkundung, Teleportationssteine, Ruhestein und Reittiere."""
from __future__ import annotations

import math
import time

from ..content import world as W
from ..content.abilities import ABILITIES, ability_client_info, class_abilities
from ..content.achievements import ACHIEVEMENTS
from ..content.classes import CLASSES, SPEC_NAMES, respec_cost, talent_points, xp_to_next
from ..content.collections import MOUNTS, PETS, SKINS, TITLES
from ..content.factions import FACTIONS, REP_MAX, STANDINGS, required_standing, standing, standing_bounds, standing_name
from ..content.talents import TALENTS, can_learn, client_trees, main_spec
from .entities import Aura, GameObj, Mob, Pet, Player, now
from .stats import client_stats, recalc

# Zähler -> Erfolge (für schnelle Prüfung)
_COUNTER_ACH: dict[str, list[dict]] = {}
for _a in ACHIEVEMENTS.values():
    c = _a["cond"]
    if "counter" in c:
        _COUNTER_ACH.setdefault(c["counter"], []).append(_a)

STONE_TRAVEL_COST = 50       # Kupfer pro Reise (pro Stufe dazu)
HEARTH_CD = 900


class ProgressMixin:
    @staticmethod
    def fmt_money(copper: int) -> str:
        g, rest = divmod(int(copper), 10000)
        s, c = divmod(rest, 100)
        parts = []
        if g:
            parts.append(f"{g} Gold")
        if s:
            parts.append(f"{s} Silber")
        if c or not parts:
            parts.append(f"{c} Kupfer")
        return " ".join(parts)

    # ================================================================== Werte & Fähigkeiten
    def send_stats(self, p: Player):
        self.send(p, {"t": "stats", "st": client_stats(p), "lvl": p.level, "xp": p.xp, "next": xp_to_next(p.level),
                      "copper": p.copper, "cur": p.currencies, "hp": p.hp, "mhp": p.max_hp, "pw": int(p.power),
                      "mpw": p.max_power, "pt": p.power_type, "title": p.title, "spec": main_spec(p.class_id, p.talents)})

    def send_abilities(self, p: Player):
        ids = [a for a in class_abilities(p.class_id) if ABILITIES[a]["level"] <= p.level]
        ids += [g for g in getattr(p, "granted", []) if g in ABILITIES]
        future = [a for a in class_abilities(p.class_id) if ABILITIES[a]["level"] > p.level]
        t = now()
        self.send(p, {"t": "abilities", "list": [ability_client_info(a, p.level, p.mods) for a in ids],
                      "future": [{"id": a, "name": ABILITIES[a]["name"], "level": ABILITIES[a]["level"], "icon": ABILITIES[a]["icon"]}
                                 for a in future],
                      "cds": {k: round(v - t, 1) for k, v in p.cooldowns.items() if v > t}, "bars": p.action_bars})

    def auto_place_ability(self, p: Player, ab_id: str):
        bars = p.action_bars
        if len(bars) < 36:
            bars.extend([None] * (36 - len(bars)))
        if any(isinstance(b, dict) and b.get("ab") == ab_id for b in bars):
            return
        for i in range(12):
            if bars[i] is None:
                bars[i] = {"ab": ab_id}
                p.save_dirty = True
                return
        for i in range(12, 36):
            if bars[i] is None:
                bars[i] = {"ab": ab_id}
                p.save_dirty = True
                return

    def default_bars(self, p: Player):
        bars = [None] * 36
        ids = [a for a in class_abilities(p.class_id) if ABILITIES[a]["level"] <= p.level]
        ids.sort(key=lambda a: ABILITIES[a]["slot"] or 99)
        for i, a in enumerate(ids[:12]):
            bars[i] = {"ab": a}
        p.action_bars = bars

    # ================================================================== Talente (Fähigkeitsbaum)
    def send_talents(self, p: Player):
        self.send(p, {"t": "talents", "trees": client_trees(p.class_id), "ranks": p.talents,
                      "points": talent_points(p.level) - sum(p.talents.values()), "total": talent_points(p.level),
                      "specs": {s: {"name": SPEC_NAMES[s][0], "role": SPEC_NAMES[s][1]} for s in CLASSES[p.class_id]["specs"]},
                      "respec_cost": respec_cost(p.misc.get("respecs", 0))})

    def learn_talent(self, p: Player, tid: str):
        if p.combat:
            self.err(p, "Nicht im Kampf.")
            return
        e = can_learn(p.class_id, p.talents, tid, talent_points(p.level))
        if e:
            self.err(p, e)
            return
        p.talents[tid] = p.talents.get(tid, 0) + 1
        p.save_dirty = True
        recalc(p)
        t = TALENTS[tid]
        if t.get("grants") and p.talents[tid] == 1:
            self.sys(p, f"Neue Fähigkeit: {ABILITIES[t['grants']]['name']}")
            self.auto_place_ability(p, t["grants"])
        self.send_talents(p)
        self.send_stats(p)
        self.send_abilities(p)

    def reset_talents(self, p: Player):
        cost = respec_cost(p.misc.get("respecs", 0))
        if not p.talents:
            self.err(p, "Ihr habt keine Talente gelernt.")
            return
        if p.copper < cost:
            self.err(p, f"Das Zurücksetzen kostet {self.fmt_money(cost)}.")
            return
        p.copper -= cost
        p.misc["respecs"] = p.misc.get("respecs", 0) + 1
        granted = list(getattr(p, "granted", []))
        p.talents = {}
        recalc(p)
        p.action_bars = [b if not (isinstance(b, dict) and b.get("ab") in granted) else None for b in p.action_bars]
        p.save_dirty = True
        self.sys(p, f"Eure Talente wurden für {self.fmt_money(cost)} zurückgesetzt.")
        self.send_talents(p)
        self.send_stats(p)
        self.send_abilities(p)

    # ================================================================== Zähler & Erfolge
    def progress_counter(self, p: Player, key: str, n: int = 1):
        c = p.achievements.setdefault("_c", {})
        old = c.get(key, 0)
        new = old + n
        c[key] = new
        if p.guild_id and key in ("kills", "gathered", "quests", "crafts", "dungeons"):
            self.guild_progress(p, key, n)
        for a in _COUNTER_ACH.get(key, ()):
            if a["id"] not in p.achievements and old < a["cond"]["n"] <= new:
                self.award_achievement(p, a)

    def set_counter_max(self, p: Player, key: str, value: int):
        c = p.achievements.setdefault("_c", {})
        if value > c.get(key, 0):
            self.progress_counter(p, key, value - c.get(key, 0))

    def ach_done(self, p: Player, a: dict) -> bool:
        c = a["cond"]
        cnt = p.achievements.get("_c", {})
        if "counter" in c:
            return cnt.get(c["counter"], 0) >= c["n"]
        if "level" in c:
            return p.level >= c["level"]
        if "kill" in c:
            return c["kill"] in p.achievements.get("_kills", [])
        if "kill_any" in c:
            k = set(p.achievements.get("_kills", []))
            return len(k & set(c["kill_any"])) >= c["n"]
        if "dungeon" in c:
            return f"{c['dungeon']}:{c['mode']}" in p.achievements.get("_dkills", [])
        if "explore" in c:
            subs = [s["name"] for s in W.ZONES.get(c["explore"], {}).get("subzones", [])]
            have = set(p.discovered.get("subzones", []))
            return bool(subs) and all(f"{c['explore']}:{s}" in have for s in subs)
        if "quest" in c:
            return c["quest"] in p.quests_done
        if "prof" in c:
            return p.professions.get(c["prof"], {}).get("skill", 0) >= c["n"]
        if "rep" in c:
            return standing(p.reputation.get(c["rep"], 0)) >= required_standing(c["standing"])
        if "collect" in c:
            return len(p.collections.get(c["collect"], [])) >= c["n"]
        if "all" in c:
            return all(x in p.achievements for x in c["all"])
        return False

    def check_achievements(self, p: Player, hint: str = ""):
        for _ in range(2):           # zweimal für "all"-Erfolge
            for a in ACHIEVEMENTS.values():
                if a["id"] not in p.achievements and "counter" not in a["cond"] and self.ach_done(p, a):
                    self.award_achievement(p, a)

    def award_achievement(self, p: Player, a: dict):
        if a["id"] in p.achievements:
            return
        p.achievements[a["id"]] = int(time.time())
        p.save_dirty = True
        self.send(p, {"t": "achievement", "id": a["id"], "name": a["name"], "desc": a["desc"], "points": a["points"],
                      "icon": a["icon"]})
        if p.zone:
            p.zone.emit_fx(p.x, p.z, {"k": "achievement", "id": p.id})
            for o in p.zone.players_near(p.x, p.z, 50):
                if o is not p:
                    self.sys(o, f"{p.name} hat den Erfolg [{a['name']}] errungen!")
        if p.guild_id:
            self.guild_broadcast(p.guild_id, f"{p.name} hat den Erfolg [{a['name']}] errungen!", exclude=p.id)
        if a.get("title"):
            self.grant_title(p, a["title"])
        if a.get("item"):
            if not p.add_items([(a["item"], 1, True)]):
                self.mail_system(p.char_id, "Erfolgsbelohnung", f"Für den Erfolg {a['name']}.", [(a["item"], 1)], 0)
            self.send_inventory(p)

    def send_achievements(self, p: Player):
        from ..content.achievements import CATEGORIES
        out = []
        cnt = p.achievements.get("_c", {})
        for a in ACHIEVEMENTS.values():
            done = a["id"] in p.achievements
            if a["hidden"] and not done:
                continue
            prog = None
            c = a["cond"]
            if "counter" in c:
                prog = [min(cnt.get(c["counter"], 0), c["n"]), c["n"]]
            elif "kill_any" in c:
                prog = [len(set(p.achievements.get("_kills", [])) & set(c["kill_any"])), c["n"]]
            out.append({"id": a["id"], "name": a["name"], "desc": a["desc"], "points": a["points"], "icon": a["icon"],
                        "cat": a["cat"], "done": p.achievements.get(a["id"]), "prog": prog,
                        "title": TITLES.get(a["title"]) if a.get("title") else None})
        pts = sum(ACHIEVEMENTS[k]["points"] for k in p.achievements if k in ACHIEVEMENTS)
        self.send(p, {"t": "achievements", "list": out, "cats": CATEGORIES, "points": pts, "counters": cnt})

    # ================================================================== Bosse & Dungeons
    def on_boss_kill(self, p: Player, mob: Mob):
        kills = p.achievements.setdefault("_kills", [])
        mid = mob.tpl["id"]
        if mid not in kills:
            kills.append(mid)
        zone = mob.zone
        if zone.is_instance and zone.mode != "normal":
            dk = p.achievements.setdefault("_dkills", [])
            key = f"{mid}:{'heroic' if zone.mode == 'heroisch' else 'mythic'}"
            if key not in dk:
                dk.append(key)
            if zone.mode == "mythisch":
                k2 = f"{mid}:heroic"
                if k2 not in dk:
                    dk.append(k2)
        if zone.is_instance:
            marks = zone.mode_cfg.get("marks", 1) * (2 if mob.tpl.get("final_boss") else 1)
            p.add_currency("dungeonmarken", marks)
            self.sys(p, f"Erhalten: {marks} Dungeonmarken.")
        self.check_achievements(p, "kill")
        p.save_dirty = True

    def on_dungeon_complete(self, p: Player, zone):
        self.progress_counter(p, "dungeons", 1)
        self.toast(p, f"{zone.cfg['name']} abgeschlossen!", f"Schwierigkeit: {zone.mode_cfg['name']}", "dungeon")
        self.quest_event(p, "dungeon_" + zone.id, 1)
        if getattr(p, "finder_group", False):
            self.progress_counter(p, "finder_dungeons", 1)
            p.add_currency("dungeonmarken", 3)
            self.sys(p, "Bonus des Gruppenfinders: 3 Dungeonmarken.")
        wk = p.misc.setdefault("weekly", {})
        wid = int(self.next_weekly_reset())
        if wk.get("id") != wid:
            wk.clear()
            wk["id"] = wid
        wk[zone.id] = wk.get(zone.id, 0) + 1
        challenge = self.weekly_challenge()
        if challenge and challenge["zone"] == zone.id and not wk.get("challenge_done") and zone.mode != "normal":
            wk["challenge_done"] = True
            p.add_currency("dungeonmarken", 15)
            p.copper += 5000 * max(1, p.level // 10)
            self.toast(p, "Wöchentliche Herausforderung erfüllt!", f"{challenge['name']}: +15 Dungeonmarken", "weekly")
        p.save_dirty = True

    def weekly_challenge(self) -> dict | None:
        """Rotierender Boss der Woche (GDD 6: wöchentliche Herausforderungen)."""
        dungeons = [z for z in W.DUNGEONS.values() if not z.get("hidden") and not z.get("arena")]
        if not dungeons:
            return None
        week = int((time.time() - 4 * 3600) // (7 * 86400))
        z = dungeons[week % len(dungeons)]
        return {"zone": z["id"], "name": f"{z['name']} auf Heroisch oder Mythisch abschließen"}

    # ================================================================== Ruf
    def add_rep(self, p: Player, fid: str, amount: int):
        if fid not in FACTIONS:
            return
        old = p.reputation.get(fid, 0)
        amount = int(amount * (1 + p.mods.get("rep_pct", 0) / 100.0))
        new = max(-42000, min(REP_MAX, old + amount))
        p.reputation[fid] = new
        p.save_dirty = True
        self.send(p, {"t": "rep", "f": fid, "name": FACTIONS[fid]["name"], "a": amount, "v": new, "st": standing_name(new)})
        if standing(new) != standing(old):
            self.toast(p, f"{FACTIONS[fid]['name']}", f"Euer Ruf ist jetzt {standing_name(new)}.", "rep")
            self.check_achievements(p, "rep")

    def send_reputation(self, p: Player):
        out = []
        for fid, f in FACTIONS.items():
            v = p.reputation.get(fid, 0)
            lo, hi = standing_bounds(v)
            out.append({"id": fid, "name": f["name"], "desc": f["desc"], "v": v, "st": standing_name(v), "lo": lo, "hi": hi,
                        "icon": f["icon"]})
        self.send(p, {"t": "reputation", "list": out, "cur": p.currencies})

    # ================================================================== Sammlungen
    def grant_title(self, p: Player, tid: str):
        lst = p.collections.setdefault("titles", [])
        if tid not in lst and tid in TITLES:
            lst.append(tid)
            p.save_dirty = True
            self.toast(p, "Neuer Titel", TITLES[tid], "title")

    def set_title(self, p: Player, tid: str | None):
        if tid and tid not in p.collections.get("titles", []):
            return
        p.misc["title"] = tid
        p.title = TITLES.get(tid, "") if tid else ""
        p.misc["title_text"] = p.title
        p.mark("name")
        p.save_dirty = True
        self.send_collections(p)

    def learn_collectible(self, p: Player, kind: str, cid: str) -> bool:
        lst = p.collections.setdefault(kind, [])
        if cid in lst:
            self.err(p, "Das besitzt Ihr bereits.")
            return False
        lst.append(cid)
        p.save_dirty = True
        names = {"mounts": MOUNTS, "pets": PETS, "skins": SKINS}
        nm = names[kind][cid]["name"]
        self.toast(p, {"mounts": "Neues Reittier", "pets": "Neues Haustier", "skins": "Neues Aussehen"}[kind], nm, "collection")
        self.check_achievements(p, "collect")
        self.send_collections(p)
        return True

    def send_collections(self, p: Player):
        self.send(p, {"t": "collections",
                      "mounts": [{"id": m, **MOUNTS[m]} for m in p.collections.get("mounts", []) if m in MOUNTS],
                      "pets": [{"id": m, **PETS[m]} for m in p.collections.get("pets", []) if m in PETS],
                      "titles": [{"id": t, "name": TITLES[t]} for t in p.collections.get("titles", []) if t in TITLES],
                      "skins": [{"id": s, **SKINS[s]} for s in p.collections.get("skins", []) if s in SKINS],
                      "all_mounts": len(MOUNTS), "all_pets": len(PETS), "all_titles": len(TITLES), "all_skins": len(SKINS),
                      "title": p.misc.get("title"), "pet": p.misc.get("pet"), "transmog": p.misc.get("transmog", {})})

    # ------------------------------------------------------------------ Reittiere
    def summon_mount(self, p: Player, mid: str):
        if mid not in p.collections.get("mounts", []):
            return
        m = MOUNTS[mid]
        if p.level < m["lvl"]:
            self.err(p, f"Ihr braucht Stufe {m['lvl']}.")
            return
        if p.mounted:
            self.dismount(p)
            return
        if p.combat or p.dead or p.cast:
            self.err(p, "Das könnt Ihr jetzt nicht tun.")
            return
        if p.zone.is_instance and not p.zone.cfg.get("mounts_allowed"):
            self.err(p, "Hier könnt Ihr nicht reiten.")
            return
        if p.moving and now() - p.last_move_t < 0.25:
            self.err(p, "Ihr könnt nicht zaubern, während Ihr Euch bewegt.")
            return
        t = now()
        p.cast = {"kind": "mount", "name": m["name"], "start": t, "end": t + 1.5, "icon": "horse-head", "school": "physical",
                  "mount": mid}
        p.mark("cast")

    def finish_mount(self, p: Player, c: dict):
        mid = c["mount"]
        m = MOUNTS[mid]
        p.mounted = mid
        p.mount_speed = m["speed"] * (1 + p.mods.get("mount_pct", 0) / 100.0)
        p.look["mount"] = {"id": mid, "model": m["model"], "look": m.get("look", {})}
        p.mark("look", "st")
        p.zone.emit_fx(p.x, p.z, {"k": "summon", "x": round(p.x, 2), "z": round(p.z, 2), "school": "holy"})

    def dismount(self, p: Player):
        if not p.mounted:
            return
        p.mounted = None
        p.mount_speed = 1.0
        p.look.pop("mount", None)
        p.mark("look", "st")

    def summon_companion(self, p: Player, pid: str | None):
        if pid and pid not in p.collections.get("pets", []):
            return
        p.misc["pet"] = pid
        if pid:
            p.look["companion"] = {"id": pid, "model": PETS[pid]["model"], "look": PETS[pid].get("look", {}), "name": PETS[pid]["name"]}
        else:
            p.look.pop("companion", None)
        p.mark("look")
        p.save_dirty = True

    def set_transmog(self, p: Player, slot: str, skin: str | None):
        tm = p.misc.setdefault("transmog", {})
        if skin:
            if skin not in p.collections.get("skins", []) or SKINS[skin]["slot"] != slot:
                return
            tm[slot] = skin
        else:
            tm.pop(slot, None)
        self.update_gear_look(p)
        p.save_dirty = True
        self.send_collections(p)

    # ================================================================== Erkundung
    def discover_zone(self, p: Player, zone_id: str):
        z = p.discovered.setdefault("zones", [])
        if zone_id not in z and W.ZONES[zone_id].get("region"):
            z.append(zone_id)
            p.save_dirty = True
            self.toast(p, f"Neue Region entdeckt: {W.ZONES[zone_id]['name']}", f"Stufe {W.ZONES[zone_id]['levels'][0]}–"
                       f"{W.ZONES[zone_id]['levels'][1]}" if W.ZONES[zone_id].get("levels") else "", "explore")
        if W.ZONES[zone_id].get("hidden") and zone_id == "hoehle_einauge":
            self.progress_counter(p, "secret_gruenmark", 1) if "secret_gruenmark" not in p.achievements.get("_c", {}) else None

    def discover_subzone(self, p: Player, zone_id: str, name: str):
        key = f"{zone_id}:{name}"
        lst = p.discovered.setdefault("subzones", [])
        if key not in lst:
            lst.append(key)
            p.save_dirty = True
            xp = 20 + p.level * 8 if p.level < 50 else 0
            self.send(p, {"t": "discover", "name": name, "xp": xp})
            if xp:
                self.add_xp(p, xp)
            self.check_achievements(p, "explore")
        self.quest_explore(p, zone_id, name)

    # ================================================================== Teleportationssteine & Ruhestein
    def activate_stone(self, p: Player, o: GameObj):
        sid = o.spec["stone"]
        lst = p.discovered.setdefault("stones", [])
        if sid not in lst:
            lst.append(sid)
            p.save_dirty = True
            self.toast(p, "Teleportationsstein aktiviert", W.STONES[sid]["name"], "stone")
            self.progress_counter(p, "stones", 1)
            p.zone.emit_fx(o.x, o.z, {"k": "nova", "id": o.id, "r": 3, "school": "arcane", "ab": "stone"})
        self.send(p, {"t": "stones", "here": sid, "list": [
            {"id": s, "name": W.STONES[s]["name"], "zone": W.ZONES[W.STONES[s]["zone"]]["name"], "zid": W.STONES[s]["zone"],
             "cost": self.travel_cost(p, s), "lvl": W.ZONES[W.STONES[s]["zone"]].get("levels", [1])[0]}
            for s in lst if s in W.STONES and s != sid]})

    def travel_cost(self, p: Player, sid: str) -> int:
        return STONE_TRAVEL_COST + p.level * 12

    def travel_to_stone(self, p: Player, sid: str):
        here = p.misc.get("_stone_obj")
        o = p.zone.entities.get(here) if here else None
        if not o or not isinstance(o, GameObj) or o.obj_kind != "stone" or p.dist(o) > 8:
            self.err(p, "Ihr müsst an einem Teleportationsstein stehen.")
            return
        if sid not in p.discovered.get("stones", []) or sid not in W.STONES:
            return
        if p.combat:
            self.err(p, "Nicht im Kampf.")
            return
        cost = self.travel_cost(p, sid)
        if p.copper < cost:
            self.err(p, "Nicht genug Geld.")
            return
        p.copper -= cost
        st = W.STONES[sid]
        dest = self.zones.get(st["zone"])
        x, z = st["pos"][0] + 2.5, st["pos"][1] + 2.5
        p.zone.emit_fx(p.x, p.z, {"k": "blink", "id": p.id, "x": round(p.x, 2), "z": round(p.z, 2), "x2": round(p.x, 2), "z2": round(p.z, 2)})
        if dest is p.zone:
            self.teleport(p, x, z, p.r, "tele")
        else:
            self.move_player(p, dest, x, z, p.r)
        self.send_stats(p)

    def use_hearth(self, p: Player):
        t = now()
        if t < p.cooldowns.get("ruhestein", 0):
            self.err(p, f"Der Ruhestein ist noch nicht bereit ({int(p.cooldowns['ruhestein'] - t)} Sek.).")
            return
        if p.combat:
            self.err(p, "Nicht im Kampf.")
            return
        if p.zone.is_arena:
            return
        p.cast = {"kind": "hearth", "name": "Ruhestein", "start": t, "end": t + 8.0, "icon": "stone-tablet", "school": "arcane"}
        p.mark("cast")

    def finish_hearth(self, p: Player, c: dict):
        sid = p.misc.get("hearth", "stein_eichenau")
        st = W.STONES.get(sid) or W.STONES.get("stein_eichenau")
        p.cooldowns["ruhestein"] = now() + HEARTH_CD
        self.send_cd(p, "ruhestein")
        dest = self.zones[st["zone"]]
        x, z = st["pos"][0] + 2.5, st["pos"][1] + 1.5
        if dest is p.zone:
            self.teleport(p, x, z, p.r)
        else:
            self.move_player(p, dest, x, z, p.r)

    def set_hearth(self, p: Player, sid: str, inn_name: str):
        p.misc["hearth"] = sid
        p.save_dirty = True
        self.sys(p, f"Euer Ruhestein ist jetzt an {inn_name} gebunden.")
