"""Berufe (GDD 8): Bergbau und Kräuterkunde sammeln, Schmiedekunst, Alchemie, Lederverarbeitung und Verzauberung stellen her.

Jeder Beruf hat eigene Erfahrungsstufen (Fertigkeit 1–300, vier Ränge) und freischaltbare Rezepte.
Manche Rezepte droppen nur von Bossen oder werden über Fraktionsruf freigeschaltet.
"""
from __future__ import annotations

import random

from ..content.factions import required_standing, standing
from ..content.items import ITEMS, item_client_info
from ..content.professions import (DISENCHANT_SKILL, MAX_SKILL, NODES, PROFESSIONS, RANKS, RECIPES, SKILLUP_CHANCE,
                                   disenchant_yield, rank_index, recipes_for, skill_color, trainer_recipes)
from .entities import GameObj, Npc, Player, now

STATION_RANGE = 8.0
GATHER_TIME = 2.0


class CraftingMixin:
    # ================================================================== Übersicht
    def send_professions(self, p: Player):
        out = {}
        for pid, pr in p.professions.items():
            info = PROFESSIONS.get(pid)
            if not info:
                continue
            recs = []
            if info["kind"] == "craft":
                for rid in pr.get("recipes", []):
                    rc = RECIPES.get(rid)
                    if not rc:
                        continue
                    recs.append({"id": rid, "name": rc["name"], "skill": rc["skill"], "result": rc["result"], "n": rc["n"],
                                 "mats": rc["mats"], "station": rc["station"], "color": skill_color(pr["skill"], rc["skill"]),
                                 "can": self.craftable_count(p, rc), "cast": rc["cast"], "enchant": rc.get("enchant")})
                recs.sort(key=lambda r: (-r["skill"], r["name"]))
            out[pid] = {"name": info["name"], "icon": info["icon"], "kind": info["kind"], "skill": pr["skill"], "max": pr["max"],
                        "rank": RANKS[rank_index(pr["max"])][0], "recipes": recs}
        ids = set()
        for pr in out.values():
            for r in pr["recipes"]:
                ids.add(r["result"])
                for m, _ in r["mats"]:
                    ids.add(m)
        self.send(p, {"t": "professions", "list": out, "items": self.item_info_for(p, ids),
                      "all": {k: {"name": v["name"], "desc": v["desc"], "kind": v["kind"], "icon": v["icon"]} for k, v in PROFESSIONS.items()}})

    def craftable_count(self, p: Player, rc: dict) -> int:
        n = 999
        for m, need in rc["mats"]:
            n = min(n, p.count_item(m) // need)
        return n

    # ================================================================== Lehrer
    def open_prof_trainer(self, p: Player, npc: Npc):
        profs = npc.tpl.get("prof")
        profs = profs if isinstance(profs, list) else [profs]
        entries = []
        for pid in profs:
            if pid not in PROFESSIONS:
                continue
            pr = p.professions.get(pid)
            info = PROFESSIONS[pid]
            e = {"id": pid, "name": info["name"], "desc": info["desc"], "kind": info["kind"], "known": bool(pr)}
            if pr:
                ri = rank_index(pr["max"])
                if ri + 1 < len(RANKS) and pr["max"] == RANKS[ri][1]:
                    nxt = RANKS[ri + 1]
                    e["next_rank"] = {"name": nxt[0], "max": nxt[1], "level": nxt[2], "cost": nxt[3], "need": pr["max"] - 25}
                e["skill"], e["max"] = pr["skill"], pr["max"]
                if info["kind"] == "craft":
                    e["recipes"] = [{"id": r["id"], "name": r["name"], "skill": r["skill"], "cost": r["cost"], "result": r["result"],
                                     "mats": r["mats"]}
                                    for r in trainer_recipes(pid, pr["max"]) if r["id"] not in pr.get("recipes", [])][:60]
                    e["faction_recipes"] = self._faction_recipes(p, pid)
            else:
                e["cost"] = RANKS[0][3]
            entries.append(e)
        ids = set()
        for e in entries:
            for r in e.get("recipes", []) + e.get("faction_recipes", []):
                ids.add(r["result"])
        self.send(p, {"t": "prof_trainer", "npc": npc.id, "name": npc.name, "list": entries, "items": self.item_info_for(p, ids)})

    def _faction_recipes(self, p: Player, pid: str) -> list:
        out = []
        pr = p.professions.get(pid, {})
        for r in recipes_for(pid):
            src = r["source"]
            if not src.startswith("faction:") or r["id"] in pr.get("recipes", []):
                continue
            _, fid, need = src.split(":")
            ok = standing(p.reputation.get(fid, 0)) >= required_standing(need)
            out.append({"id": r["id"], "name": r["name"], "skill": r["skill"], "cost": r["cost"] * 3, "result": r["result"],
                        "mats": r["mats"], "rep": [fid, need], "ok": ok})
        return out

    def learn_profession(self, p: Player, npc: Npc, pid: str):
        if not self._is_prof_trainer(npc, pid):
            return
        if pid in p.professions:
            return
        cost = RANKS[0][3]
        if p.level < RANKS[0][2]:
            self.err(p, f"Ihr braucht Stufe {RANKS[0][2]}.")
            return
        if p.copper < cost:
            self.err(p, "Nicht genug Geld.")
            return
        p.copper -= cost
        p.professions[pid] = {"skill": 1, "max": RANKS[0][1], "recipes": [r["id"] for r in trainer_recipes(pid, 1) if r["skill"] <= 1]}
        p.save_dirty = True
        self.sys(p, f"Ihr habt {PROFESSIONS[pid]['name']} erlernt (Lehrling).")
        self.toast(p, f"Beruf erlernt: {PROFESSIONS[pid]['name']}", "Lehrling (max. 75)", "prof")
        self.open_prof_trainer(p, npc)
        self.send_professions(p)
        self.send_stats(p)

    def unlearn_profession(self, p: Player, pid: str):
        if pid in p.professions:
            del p.professions[pid]
            p.save_dirty = True
            self.sys(p, f"Ihr habt {PROFESSIONS[pid]['name']} verlernt.")
            self.send_professions(p)

    def upgrade_rank(self, p: Player, npc: Npc, pid: str):
        if not self._is_prof_trainer(npc, pid):
            return
        pr = p.professions.get(pid)
        if not pr:
            return
        ri = rank_index(pr["max"])
        if ri + 1 >= len(RANKS):
            return
        name, mx, lvl, cost = RANKS[ri + 1]
        if p.level < lvl:
            self.err(p, f"Ihr braucht Stufe {lvl}.")
            return
        if pr["skill"] < pr["max"] - 25:
            self.err(p, f"Ihr braucht mindestens {pr['max'] - 25} Fertigkeit.")
            return
        if p.copper < cost:
            self.err(p, "Nicht genug Geld.")
            return
        p.copper -= cost
        pr["max"] = mx
        p.save_dirty = True
        self.toast(p, f"{PROFESSIONS[pid]['name']}: {name}", f"Maximale Fertigkeit {mx}", "prof")
        self.open_prof_trainer(p, npc)
        self.send_professions(p)
        self.send_stats(p)

    def train_recipe(self, p: Player, npc: Npc, rid: str):
        rc = RECIPES.get(rid)
        if not rc or not self._is_prof_trainer(npc, rc["prof"]):
            return
        pr = p.professions.get(rc["prof"])
        if not pr or rid in pr.get("recipes", []):
            return
        cost = rc["cost"]
        if rc["source"].startswith("faction:"):
            _, fid, need = rc["source"].split(":")
            if standing(p.reputation.get(fid, 0)) < required_standing(need):
                self.err(p, f"Dafür braucht Ihr den Ruf {need}.")
                return
            cost *= 3
        elif rc["source"] != "trainer":
            return
        if rc["skill"] > pr["skill"]:
            self.err(p, f"Benötigt {rc['skill']} Fertigkeit.")
            return
        if p.copper < cost:
            self.err(p, "Nicht genug Geld.")
            return
        p.copper -= cost
        pr.setdefault("recipes", []).append(rid)
        p.save_dirty = True
        self.sys(p, f"Rezept erlernt: {rc['name']}")
        self.open_prof_trainer(p, npc)
        self.send_professions(p)
        self.send_stats(p)

    def _is_prof_trainer(self, npc: Npc, pid: str) -> bool:
        profs = npc.tpl.get("prof")
        profs = profs if isinstance(profs, list) else [profs]
        return pid in profs and "prof_trainer" in npc.tpl.get("services", [])

    # ================================================================== Fertigkeit
    def skill_up(self, p: Player, pid: str, req: int):
        pr = p.professions.get(pid)
        if not pr or pr["skill"] >= pr["max"]:
            return
        col = skill_color(pr["skill"], req)
        if random.random() < SKILLUP_CHANCE.get(col, 0):
            pr["skill"] += 1
            p.save_dirty = True
            self.send(p, {"t": "skillup", "prof": pid, "name": PROFESSIONS[pid]["name"], "skill": pr["skill"], "max": pr["max"]})
            if pr["skill"] in (75, 150, 225, 300):
                self.check_achievements(p, "prof")

    # ================================================================== Sammeln
    def obj_usable(self, p: Player, o: GameObj) -> bool:
        k = o.obj_kind
        if k == "node":
            pid = o.spec.get("prof")
            pr = p.professions.get(pid)
            return bool(pr and pr["skill"] >= o.spec.get("skill", 1))
        if k == "quest":
            return self.player_needs_item(p, o.item)
        if k == "chest":
            if o.spec.get("needs_item") and p.count_item(o.spec["needs_item"]) < 1:
                return False
            return o.id not in p.misc.get("_opened", set())
        return k in ("stone", "mailbox", "board", "forge", "alchemy", "anvil", "portal_obj", "bank")

    def start_gather(self, p: Player, o: GameObj):
        if not o.available:
            return
        if p.mounted:
            self.dismount(p)
        k = o.obj_kind
        if k == "node":
            pid = o.spec["prof"]
            pr = p.professions.get(pid)
            if not pr:
                self.err(p, f"Dafür braucht Ihr {PROFESSIONS[pid]['name']}.")
                return
            if pr["skill"] < o.spec.get("skill", 1):
                self.err(p, f"Benötigt {PROFESSIONS[pid]['name']} ({o.spec['skill']}).")
                return
            name = "Bergbau" if pid == "bergbau" else "Kräuter sammeln"
        elif k == "quest":
            if not self.player_needs_item(p, o.item):
                self.err(p, "Das braucht Ihr gerade nicht.")
                return
            name = "Sammeln"
        else:
            return
        t = now()
        p.cast = {"kind": "gather", "name": name, "start": t, "end": t + GATHER_TIME, "obj": o.id, "icon": "gathering",
                  "school": "nature"}
        p.mark("cast")

    def finish_gather(self, p: Player, c: dict):
        o = p.zone.entities.get(c["obj"])
        if not isinstance(o, GameObj) or not o.available or p.dist(o) > 6:
            return
        if o.obj_kind == "node":
            node = NODES[o.spec["node"]]
            n = random.randint(*node["n"])
            items = [(node["item"], n)]
            for extra, ch in node.get("extra", []):
                if random.random() < ch:
                    items.append((extra, 1))
            if not p.add_items(items):
                self.err(p, "Eure Taschen sind voll.")
                return
            for iid, cnt in items:
                self.loot_message(p, iid, cnt)
            self.skill_up(p, node["prof"], node["skill"])
            self.progress_counter(p, "gathered", 1)
        else:
            if not p.add_items([(o.item, 1)]):
                self.err(p, "Eure Taschen sind voll.")
                return
            self.loot_message(p, o.item, 1)
        o.available = False
        o.hidden = True
        o.respawn_at = now() + o.respawn * random.uniform(0.9, 1.2)
        o.mark("st")
        self.send_inventory(p)

    # ================================================================== Herstellen
    def near_station(self, p: Player, station: str | None) -> bool:
        if not station:
            return True
        kinds = {"forge": ("forge",), "anvil": ("forge", "anvil"), "alchemy": ("alchemy",)}.get(station, (station,))
        for e in p.zone.entities.values():
            if isinstance(e, GameObj) and e.obj_kind in kinds and p.dist(e) <= STATION_RANGE:
                return True
        # Schmiede-Requisiten zählen auch als Amboss
        if station in ("anvil", "forge"):
            for pr in p.zone.static.props:
                if pr["t"] in ("anvil", "forge", "smithy") and "x" in pr and (pr["x"] - p.x) ** 2 + (pr["z"] - p.z) ** 2 <= 64:
                    return True
        return False

    def craft(self, p: Player, rid: str, n: int = 1):
        rc = RECIPES.get(rid)
        if not rc:
            return
        pr = p.professions.get(rc["prof"])
        if not pr or rid not in pr.get("recipes", []):
            self.err(p, "Dieses Rezept kennt Ihr nicht.")
            return
        if p.cast or p.combat:
            self.err(p, "Ihr seid beschäftigt.")
            return
        if not self.near_station(p, rc["station"]):
            self.err(p, {"forge": "Dafür braucht Ihr eine Schmiede.", "anvil": "Dafür braucht Ihr einen Amboss.",
                         "alchemy": "Dafür braucht Ihr einen Alchemietisch."}.get(rc["station"], "Falscher Ort."))
            return
        if self.craftable_count(p, rc) < 1:
            self.err(p, "Euch fehlen Materialien.")
            return
        t = now()
        p.cast = {"kind": "craft", "name": rc["name"], "start": t, "end": t + rc["cast"], "recipe": rid,
                  "left": max(1, min(50, int(n))), "icon": PROFESSIONS[rc["prof"]]["icon"], "school": "physical"}
        p.mark("cast")

    def finish_craft(self, p: Player, c: dict):
        rc = RECIPES[c["recipe"]]
        if self.craftable_count(p, rc) < 1:
            self.err(p, "Euch fehlen Materialien.")
            return
        result = (rc["result"], rc["n"])
        backup = [dict(s) if s else None for s in p.bags]
        for m, need in rc["mats"]:
            p.remove_item(m, need)
        if not p.add_items([(result[0], result[1], ITEMS[result[0]].get("bind") == "bop")]):
            p.bags = backup
            self.err(p, "Eure Taschen sind voll.")
            return
        self.loot_message(p, result[0], result[1])
        self.skill_up(p, rc["prof"], rc["skill"])
        self.progress_counter(p, "crafts", 1)
        self.send_inventory(p)
        self.send_professions(p)
        left = c.get("left", 1) - 1
        if left > 0 and self.craftable_count(p, rc) > 0:
            t = now()
            p.cast = {"kind": "craft", "name": rc["name"], "start": t, "end": t + rc["cast"], "recipe": rc["id"], "left": left,
                      "icon": c.get("icon"), "school": "physical"}
            p.mark("cast")

    def disenchant(self, p: Player, slot: int):
        pr = p.professions.get("verzauberung")
        if not pr:
            self.err(p, "Dafür braucht Ihr Verzauberung.")
            return
        if not (0 <= slot < len(p.bags)) or not p.bags[slot]:
            return
        it = ITEMS[p.bags[slot]["i"]]
        if it["type"] not in ("weapon", "armor", "jewelry") or it["q"] < 2 or it["q"] > 5:
            self.err(p, "Das lässt sich nicht entzaubern.")
            return
        need = DISENCHANT_SKILL(it.get("ilvl", 1))
        if pr["skill"] < need:
            self.err(p, f"Benötigt Verzauberung ({need}).")
            return
        yields = disenchant_yield(it)
        p.bags[slot] = None
        if not p.add_items(yields):
            self.err(p, "Eure Taschen sind voll.")
            return
        for iid, n in yields:
            self.loot_message(p, iid, n)
        self.skill_up(p, "verzauberung", need)
        p.zone.emit_fx(p.x, p.z, {"k": "buff", "id": p.id, "school": "arcane"})
        self.send_inventory(p)
