"""Inventar, Ausrüstung, Beute, Händler, Reparaturen und das Benutzen von Gegenständen (GDD 5)."""
from __future__ import annotations

import math
import random

from ..content.collections import SKINS
from ..content.enchants import ENCHANTS
from ..content.factions import required_standing, standing
from ..content.items import EQUIP_SLOTS, ITEMS, RARITY_NAMES, TWO_HAND, is_equippable, item_client_info, item_usable_by
from ..content.professions import BAGS, RECIPES
from .entities import Aura, GameObj, Mob, Npc, Player, now
from .stats import recalc

BASE_BAG = 24
MAX_BAGS = 4
BUYBACK_MAX = 12
INTERACT_RANGE = 6.0


def item_slots(it: dict) -> list[str]:
    slot = it.get("slot")
    if slot == "ring":
        return ["ring1", "ring2"]
    if slot == "main_hand" and it["type"] == "weapon":
        return ["main_hand"]
    return [slot] if slot in EQUIP_SLOTS else []


class InventoryMixin:
    # ================================================================== Hilfen
    def capacity(self, p: Player) -> int:
        return BASE_BAG + sum(BAGS.get(b, 0) for b in p.misc.get("bagslots", []) if b)

    def fit_bags(self, p: Player):
        cap = self.capacity(p)
        if len(p.bags) < cap:
            p.bags.extend([None] * (cap - len(p.bags)))
        elif len(p.bags) > cap:
            extra = [s for s in p.bags[cap:] if s]
            p.bags = p.bags[:cap]
            for s in extra:
                for i in range(cap):
                    if p.bags[i] is None:
                        p.bags[i] = s
                        break

    def item_info_for(self, p: Player, ids) -> dict:
        """Gegenstandsdefinitionen, die der Client noch nicht kennt."""
        known = p.misc.setdefault("_known_items", set())
        out = {}
        for i in ids:
            if i and i not in known and i in ITEMS:
                out[i] = item_client_info(i)
                known.add(i)
        return out

    def send_inventory(self, p: Player):
        self.fit_bags(p)
        ids = [s["i"] for s in p.bags if s] + [s["i"] for s in p.equipment.values() if s] + [b for b in p.misc.get("bagslots", []) if b]
        self.send(p, {"t": "inv", "bags": p.bags, "eq": p.equipment, "copper": p.copper, "cap": self.capacity(p),
                      "bagslots": p.misc.get("bagslots", []), "items": self.item_info_for(p, ids), "cur": p.currencies,
                      "repair": self.repair_cost(p)})
        self.quest_items_changed(p)

    def update_gear_look(self, p: Player):
        gear = {}
        tm = p.misc.get("transmog", {})
        for slot, inst in p.equipment.items():
            if not inst:
                continue
            it = ITEMS.get(inst["i"])
            if not it:
                continue
            vis = dict(it.get("vis", {}))
            if slot in tm and tm[slot] in SKINS:
                vis.update(SKINS[tm[slot]]["vis"])
            gear[slot] = {"sub": it.get("sub"), "q": it["q"], "vis": vis, "id": inst["i"], "two": it.get("two_hand", False)}
        for slot, skin in tm.items():
            if slot not in gear and skin in SKINS:
                gear[slot] = {"sub": "stoff", "q": 3, "vis": SKINS[skin]["vis"], "id": skin}
        p.look["gear"] = gear
        p.look["cls"] = p.class_id
        p.mark("look")

    def loot_message(self, p: Player, item_id: str, n: int):
        it = ITEMS[item_id]
        self.send(p, {"t": "loot_msg", "i": item_id, "n": n, "name": it["name"], "q": it["q"],
                      "items": self.item_info_for(p, [item_id])})
        if it["q"] >= 4 and p.zone:
            for o in p.zone.players_near(p.x, p.z, 60):
                if o is not p:
                    self.sys(o, f"{p.name} erhält Beute: [{it['name']}]")
        if it["q"] >= 5 and p.guild_id:
            self.guild_broadcast(p.guild_id, f"{p.name} hat [{it['name']}] erbeutet!")

    def give_items(self, p: Player, items: list[tuple], source: str = "") -> bool:
        ok = p.add_items([(i, n, ITEMS[i].get("bind") == "bop") for i, n in items])
        if ok:
            for i, n in items:
                self.loot_message(p, i, n)
            self.send_inventory(p)
        return ok

    # ================================================================== Beute
    def open_loot(self, p: Player, mob: Mob):
        loot = mob.loot.get(p.id)
        if not loot:
            return
        p.loot_open = mob.id
        self.send(p, {"t": "loot", "id": mob.id, "name": mob.name, "items": loot["items"], "copper": loot["copper"],
                      "defs": self.item_info_for(p, [i[0] for i in loot["items"]])})

    def _loot_source(self, p: Player, m: dict):
        src = p.zone.entities.get(m.get("id"))
        if src is None or src.id != p.loot_open:
            return None, None
        if p.dist(src) > INTERACT_RANGE + 2:
            self.err(p, "Zu weit entfernt.")
            return None, None
        loot = src.loot.get(p.id) if hasattr(src, "loot") else None
        return src, loot

    def _finish_loot(self, p: Player, src, loot: dict):
        if not loot["items"] and not loot["copper"]:
            src.loot.pop(p.id, None)
            p.loot_open = None
            self.send(p, {"t": "loot_close"})
            if isinstance(src, Mob) and not any(src.loot.values()):
                src.corpse_until = min(src.corpse_until, now() + 10)
        else:
            self.send(p, {"t": "loot", "id": src.id, "name": src.name, "items": loot["items"], "copper": loot["copper"], "defs": {}})

    def take_copper(self, p: Player, loot: dict):
        if loot["copper"]:
            c = loot["copper"]
            share = [p]
            if p.party:
                share = [m for m in self.party_players(p.party) if m.zone is p.zone and m.dist(p) < 80 and not m.dead]
            per = c // len(share)
            rest = c - per * len(share)
            for m in share:
                m.copper += per + (rest if m is p else 0)
                self.sys(m, f"Ihr erhaltet Beute: {self.fmt_money(per + (rest if m is p else 0))}" + (" (Anteil)" if len(share) > 1 else ""))
                self.progress_counter(m, "gold_looted", per)
                self.set_counter_max(m, "max_gold", m.copper // 10000)
                m.save_dirty = True
                self.send_stats(m)
            loot["copper"] = 0

    def loot_take(self, p: Player, m: dict):
        src, loot = self._loot_source(p, m)
        if not loot:
            return
        idx = m.get("i")
        if idx == "c":
            self.take_copper(p, loot)
        elif isinstance(idx, int) and 0 <= idx < len(loot["items"]):
            iid, n = loot["items"][idx][0], loot["items"][idx][1]
            if not p.add_items([(iid, n, ITEMS[iid].get("bind") == "bop")]):
                self.err(p, "Eure Taschen sind voll.")
                return
            loot["items"].pop(idx)
            self.loot_message(p, iid, n)
            self.send_inventory(p)
            if ITEMS[iid].get("starts_quest"):
                self.sys(p, "Dieser Gegenstand beginnt eine Quest. Benutzt ihn (Rechtsklick).")
        self._finish_loot(p, src, loot)

    def loot_all(self, p: Player, m: dict):
        src, loot = self._loot_source(p, m)
        if not loot:
            return
        self.take_copper(p, loot)
        full = False
        for entry in list(loot["items"]):
            iid, n = entry[0], entry[1]
            if p.add_items([(iid, n, ITEMS[iid].get("bind") == "bop")]):
                loot["items"].remove(entry)
                self.loot_message(p, iid, n)
            else:
                full = True
        if full:
            self.err(p, "Eure Taschen sind voll.")
        self.send_inventory(p)
        self._finish_loot(p, src, loot)

    def loot_close(self, p: Player):
        p.loot_open = None

    # ================================================================== Händler
    def open_vendor(self, p: Player, npc: Npc):
        tpl = npc.tpl
        stock = []
        for iid in tpl.get("vendor", []):
            it = ITEMS.get(iid)
            if not it:
                continue
            price = it.get("buy") or max(1, it.get("sell", 1) * 4)
            entry = {"i": iid, "price": price}
            if it.get("req_rep"):
                entry["rep"] = list(it["req_rep"])
            if it.get("cost_cur"):
                entry["cur"] = it["cost_cur"]
            stock.append(entry)
        p.misc["_vendor"] = npc.id
        self.send(p, {"t": "vendor", "npc": npc.id, "name": npc.name, "stock": stock, "repair": "repair" in tpl.get("services", []),
                      "buyback": p.misc.get("_buyback", []), "items": self.item_info_for(p, [s["i"] for s in stock] +
                                                                                      [b["i"] for b in p.misc.get("_buyback", [])])})

    def _vendor_npc(self, p: Player, m: dict) -> Npc | None:
        npc = p.zone.entities.get(m.get("npc"))
        if not isinstance(npc, Npc) or p.dist(npc) > INTERACT_RANGE + 2:
            self.err(p, "Zu weit entfernt.")
            return None
        return npc

    def buy(self, p: Player, m: dict):
        npc = self._vendor_npc(p, m)
        if not npc:
            return
        iid = m.get("i")
        n = max(1, min(200, int(m.get("n", 1) or 1)))
        if iid not in npc.tpl.get("vendor", []) or iid not in ITEMS:
            return
        it = ITEMS[iid]
        n = min(n, it.get("stack", 1)) if it.get("stack", 1) > 1 else 1
        if it.get("req_rep"):
            fid, need = it["req_rep"]
            if standing(p.reputation.get(fid, 0)) < required_standing(need):
                self.err(p, f"Dafür braucht Ihr den Ruf {need}.")
                return
        if it.get("cost_cur"):
            for cid, amount in it["cost_cur"].items():
                if p.currency(cid) < amount * n:
                    self.err(p, "Nicht genug Abzeichen.")
                    return
        price = (it.get("buy") or max(1, it.get("sell", 1) * 4)) * n
        price = int(price * (1 - self.rep_discount(p, npc)))
        if p.copper < price:
            self.err(p, "Nicht genug Geld.")
            return
        if not p.add_items([(iid, n, it.get("bind") == "bop")]):
            self.err(p, "Eure Taschen sind voll.")
            return
        p.copper -= price
        for cid, amount in (it.get("cost_cur") or {}).items():
            p.add_currency(cid, -amount * n)
        p.save_dirty = True
        self.send_inventory(p)
        self.send_stats(p)

    def rep_discount(self, p: Player, npc: Npc) -> float:
        fid = npc.tpl.get("faction")
        if not fid:
            return 0.0
        st = standing(p.reputation.get(fid, 0))
        return {3: 0.05, 4: 0.1, 5: 0.15, 6: 0.2}.get(st, 0.0)

    def sell(self, p: Player, m: dict):
        npc = self._vendor_npc(p, m)
        if not npc or "vendor" not in npc.tpl.get("services", []):
            return
        slot = m.get("slot")
        if not isinstance(slot, int) or not (0 <= slot < len(p.bags)) or not p.bags[slot]:
            return
        inst = p.bags[slot]
        it = ITEMS[inst["i"]]
        if it.get("quest") or not it.get("sell"):
            self.err(p, "Das kauft Euch niemand ab.")
            return
        gain = it["sell"] * inst["n"]
        p.bags[slot] = None
        p.copper += gain
        bb = p.misc.setdefault("_buyback", [])
        bb.insert(0, dict(inst, price=gain))
        del bb[BUYBACK_MAX:]
        p.save_dirty = True
        self.sys(p, f"Verkauft: {it['name']}" + (f" ×{inst['n']}" if inst["n"] > 1 else "") + f" für {self.fmt_money(gain)}.")
        self.send_inventory(p)
        self.send_stats(p)
        self.open_vendor(p, npc)

    def buyback(self, p: Player, m: dict):
        npc = self._vendor_npc(p, m)
        if not npc:
            return
        bb = p.misc.get("_buyback", [])
        i = m.get("i")
        if not isinstance(i, int) or not (0 <= i < len(bb)):
            return
        e = bb[i]
        if p.copper < e["price"]:
            self.err(p, "Nicht genug Geld.")
            return
        inst = {k: v for k, v in e.items() if k != "price"}
        extra = {k: v for k, v in inst.items() if k not in ("i", "n", "b")}
        if not p.add_items([(inst["i"], inst["n"], bool(inst.get("b")), extra or None)]):
            self.err(p, "Eure Taschen sind voll.")
            return
        p.copper -= e["price"]
        bb.pop(i)
        self.send_inventory(p)
        self.send_stats(p)
        self.open_vendor(p, npc)

    def sell_junk(self, p: Player, m: dict):
        npc = self._vendor_npc(p, m)
        if not npc:
            return
        total = 0
        for i, inst in enumerate(p.bags):
            if inst and ITEMS[inst["i"]]["q"] == 0 and ITEMS[inst["i"]].get("sell"):
                total += ITEMS[inst["i"]]["sell"] * inst["n"]
                p.bags[i] = None
        if total:
            p.copper += total
            p.save_dirty = True
            self.sys(p, f"Plunder verkauft für {self.fmt_money(total)}.")
            self.send_inventory(p)
            self.send_stats(p)

    def repair_cost(self, p: Player) -> int:
        cost = 0
        for inst in p.equipment.values():
            if not inst:
                continue
            it = ITEMS.get(inst["i"])
            if it and it["type"] in ("weapon", "armor") and inst.get("d", 100) < 100:
                cost += int((100 - inst.get("d", 100)) / 100 * (it.get("ilvl", 1) * 6 + 10) * (1 + it["q"] * 0.4))
        return cost

    def repair(self, p: Player, m: dict):
        npc = self._vendor_npc(p, m)
        if not npc or "repair" not in npc.tpl.get("services", []):
            return
        cost = int(self.repair_cost(p) * (1 - self.rep_discount(p, npc)))
        if cost <= 0:
            return
        if p.copper < cost:
            self.err(p, "Nicht genug Geld für die Reparatur.")
            return
        p.copper -= cost
        for inst in p.equipment.values():
            if inst:
                inst["d"] = 100
        recalc(p)
        p.save_dirty = True
        self.sys(p, f"Alles repariert für {self.fmt_money(cost)}.")
        self.send_inventory(p)
        self.send_stats(p)

    # ================================================================== Ausrüstung
    def equip(self, p: Player, slot: int, target: str | None = None):
        if p.dead or p.combat and not self._combat_swap_ok(p, slot):
            self.err(p, "Das könnt Ihr im Kampf nicht tun.")
            return
        if not (0 <= slot < len(p.bags)) or not p.bags[slot]:
            return
        inst = p.bags[slot]
        it = ITEMS[inst["i"]]
        if it["type"] == "consumable" and it.get("use", {}).get("type") == "bag":
            self.use_item(p, slot)
            return
        if not is_equippable(it):
            return
        if p.level < it.get("lvl", 1):
            self.err(p, f"Ihr müsst Stufe {it['lvl']} sein.")
            return
        if not item_usable_by(it, p.cls, p.class_id):
            self.err(p, "Diesen Gegenstand könnt Ihr nicht benutzen.")
            return
        if it.get("req_rep"):
            fid, need = it["req_rep"]
            if standing(p.reputation.get(fid, 0)) < required_standing(need):
                self.err(p, f"Dafür braucht Ihr den Ruf {need}.")
                return
        if it.get("unique"):
            if any(s and s["i"] == inst["i"] for s in p.equipment.values()):
                self.err(p, "Ihr könnt nur einen davon tragen.")
                return
        slots = item_slots(it)
        if it["type"] == "weapon":
            if it.get("sub") in p.cls.get("offhand", []) and p.cls.get("dual_wield"):
                slots = ["main_hand", "off_hand"]
            else:
                slots = ["main_hand"]
        if not slots:
            return
        if target and target in slots:
            dest = target
        else:
            dest = next((s for s in slots if not p.equipment.get(s)), slots[0])
        displaced = []
        old = p.equipment.get(dest)
        if old:
            displaced.append(old)
        if dest == "main_hand" and it.get("two_hand") and p.equipment.get("off_hand"):
            displaced.append(p.equipment["off_hand"])
        if dest == "off_hand":
            mh = p.equipment.get("main_hand")
            if mh and ITEMS[mh["i"]].get("two_hand"):
                displaced.append(mh)
        needed = len(displaced) - 1
        if needed > p.free_slots():
            self.err(p, "Eure Taschen sind voll.")
            return
        p.bags[slot] = None
        new_inst = dict(inst)
        new_inst.setdefault("d", 100)
        if it.get("bind") in ("boe", "bop"):
            new_inst["b"] = 1
        p.equipment[dest] = new_inst
        if dest == "main_hand" and it.get("two_hand"):
            p.equipment.pop("off_hand", None)
        if dest == "off_hand":
            mh = p.equipment.get("main_hand")
            if mh and ITEMS[mh["i"]].get("two_hand"):
                p.equipment.pop("main_hand", None)
        first = True
        for d in displaced:
            if first:
                p.bags[slot] = d
                first = False
            else:
                for i in range(len(p.bags)):
                    if p.bags[i] is None:
                        p.bags[i] = d
                        break
        p.equipment = {k: v for k, v in p.equipment.items() if v}
        self.after_gear_change(p)

    def _combat_swap_ok(self, p: Player, slot: int) -> bool:
        inst = p.bags[slot] if 0 <= slot < len(p.bags) else None
        return bool(inst and ITEMS[inst["i"]]["type"] == "weapon")

    def unequip(self, p: Player, slot_name: str, to: int | None = None):
        if slot_name not in p.equipment or p.dead:
            return
        if p.combat and ITEMS[p.equipment[slot_name]["i"]]["type"] != "weapon":
            self.err(p, "Das könnt Ihr im Kampf nicht tun.")
            return
        if to is not None and 0 <= to < len(p.bags) and p.bags[to] is None:
            p.bags[to] = p.equipment.pop(slot_name)
        else:
            for i in range(len(p.bags)):
                if p.bags[i] is None:
                    p.bags[i] = p.equipment.pop(slot_name)
                    break
            else:
                self.err(p, "Eure Taschen sind voll.")
                return
        self.after_gear_change(p)

    def after_gear_change(self, p: Player):
        recalc(p)
        self.update_gear_look(p)
        p.save_dirty = True
        self.send_inventory(p)
        self.send_stats(p)
        self.send_abilities(p)

    def swap(self, p: Player, a: int, b: int):
        if not (0 <= a < len(p.bags) and 0 <= b < len(p.bags)) or a == b:
            return
        sa, sb = p.bags[a], p.bags[b]
        if sa and sb and sa["i"] == sb["i"] and not sa.get("e") and not sb.get("e"):
            stack = ITEMS[sa["i"]].get("stack", 1)
            if stack > 1 and bool(sa.get("b")) == bool(sb.get("b")):
                move = min(sa["n"], stack - sb["n"])
                if move > 0:
                    sb["n"] += move
                    sa["n"] -= move
                    if sa["n"] <= 0:
                        p.bags[a] = None
                    p.save_dirty = True
                    self.send_inventory(p)
                    return
        p.bags[a], p.bags[b] = sb, sa
        p.save_dirty = True
        self.send_inventory(p)

    def split(self, p: Player, slot: int, n: int):
        if not (0 <= slot < len(p.bags)) or not p.bags[slot]:
            return
        inst = p.bags[slot]
        n = int(n)
        if n <= 0 or n >= inst["n"]:
            return
        for i in range(len(p.bags)):
            if p.bags[i] is None:
                p.bags[i] = dict(inst, n=n)
                inst["n"] -= n
                p.save_dirty = True
                self.send_inventory(p)
                return
        self.err(p, "Eure Taschen sind voll.")

    def sort_bags(self, p: Player):
        items = [s for s in p.bags if s]

        def key(s):
            it = ITEMS[s["i"]]
            order = {"weapon": 0, "armor": 1, "jewelry": 2, "consumable": 3, "material": 4, "quest": 5, "junk": 6}
            return (order.get(it["type"], 9), -it["q"], it["name"])
        items.sort(key=key)
        p.bags = items + [None] * (len(p.bags) - len(items))
        p.save_dirty = True
        self.send_inventory(p)

    def destroy(self, p: Player, slot: int):
        if 0 <= slot < len(p.bags) and p.bags[slot]:
            it = ITEMS[p.bags[slot]["i"]]
            p.bags[slot] = None
            p.save_dirty = True
            self.sys(p, f"Zerstört: {it['name']}")
            self.send_inventory(p)

    # ================================================================== Benutzen
    def use_item(self, p: Player, slot: int, tid: int | None = None):
        if p.dead or not (0 <= slot < len(p.bags)) or not p.bags[slot]:
            return
        inst = p.bags[slot]
        it = ITEMS[inst["i"]]
        if it.get("starts_quest"):
            qid = it["starts_quest"]
            from ..content import world as W
            if qid in W.QUESTS:
                if self.quest_available(p, qid):
                    self.send(p, {"t": "quest_detail", "mode": "offer", "giver": "item", "q": self.quest_payload(W.QUESTS[qid], p)})
                else:
                    self.err(p, "Ihr könnt diese Quest im Moment nicht annehmen.")
            return
        if is_equippable(it):
            self.equip(p, slot)
            return
        use = it.get("use")
        if not use:
            return
        if p.level < it.get("lvl", 1):
            self.err(p, f"Ihr müsst Stufe {it['lvl']} sein.")
            return
        t = now()
        kind = use["type"]
        if kind in ("food", "drink"):
            if p.combat:
                self.err(p, "Das könnt Ihr im Kampf nicht tun.")
                return
            per = use["amount"] / use["dur"]
            if p.eating and p.eating.get("until", 0) > t:
                e = p.eating
            else:
                e = p.eating = {"until": t + use["dur"]}
            e["until"] = max(e["until"], t + use["dur"])
            if kind == "food":
                e["hp"] = per
                p.add_aura(Aura({"id": "essen", "name": "Essen", "icon": it["icon"], "food": {"hp": per}}, p.id, t, p.level, use["dur"]))
            else:
                e["mp"] = per
                p.add_aura(Aura({"id": "trinken", "name": "Trinken", "icon": it["icon"], "food": {"mp": per}}, p.id, t, p.level, use["dur"]))
            p.sitting = True
            p.auto_attack = False
            p.mark("st", "au")
            self._consume(p, slot)
        elif kind in ("heal", "mana"):
            if t < p.potion_cd_until:
                self.err(p, "Das ist noch nicht bereit.")
                return
            amount = int(use["amount"] * random.uniform(0.78, 1.22) * (1 + p.mods.get("potion_pct", 0) / 100.0))
            if kind == "heal":
                self.heal(p, p, amount, it["name"])
            else:
                if p.power_type != "mana":
                    self.err(p, "Ihr nutzt kein Mana.")
                    return
                p.power = min(p.max_power, p.power + amount)
                p.mark("pw")
            p.potion_cd_until = t + use.get("cd", 60)
            self.send(p, {"t": "cd", "ab": "trank", "cd": use.get("cd", 60), "gcd": 0})
            self._consume(p, slot)
        elif kind in ("elixir", "weapon_oil"):
            d = {"id": use["aura"], "name": it["name"], "icon": it["icon"], "stats": use.get("stats", {})}
            if use.get("proc"):
                d["proc"] = use["proc"]
            if use.get("pct"):
                d["pct"] = use["pct"]
            p.add_aura(Aura(d, p.id, t, 1, use.get("dur", 1800)))
            recalc(p)
            self.send_stats(p)
            self._consume(p, slot)
        elif kind == "cure":
            removed = False
            for a in list(p.auras):
                if a.debuff and a.dispel in use.get("kinds", ["poison", "disease"]):
                    p.auras.remove(a)
                    removed = True
            if removed:
                p.mark("au")
            self._consume(p, slot)
        elif kind == "hearth":
            self.use_hearth(p)
        elif kind == "learn_mount":
            if self.learn_collectible(p, "mounts", use["mount"]):
                self._consume(p, slot)
        elif kind == "learn_pet":
            if self.learn_collectible(p, "pets", use["pet"]):
                self._consume(p, slot)
        elif kind == "learn_skin":
            if self.learn_collectible(p, "skins", use["skin"]):
                self._consume(p, slot)
        elif kind == "learn_recipe":
            rid = use["recipe"]
            rc = RECIPES.get(rid)
            if not rc:
                return
            prof = p.professions.get(rc["prof"])
            if not prof:
                self.err(p, "Ihr beherrscht diesen Beruf nicht.")
                return
            if prof.get("skill", 0) < rc["skill"]:
                self.err(p, f"Benötigt {rc['skill']} Fertigkeit.")
                return
            if rid in prof.setdefault("recipes", []):
                self.err(p, "Das Rezept kennt Ihr bereits.")
                return
            prof["recipes"].append(rid)
            self.sys(p, f"Neues Rezept erlernt: {rc['name']}")
            self._consume(p, slot)
            self.send_professions(p)
        elif kind == "enchant":
            ench = ENCHANTS.get(use["enchant"])
            if not ench:
                return
            target_slot = next((s for s in ench["slots"] if p.equipment.get(s)), None)
            if not target_slot:
                self.err(p, "Ihr tragt keinen passenden Gegenstand.")
                return
            p.equipment[target_slot]["e"] = use["enchant"]
            recalc(p)
            self.sys(p, f"{ITEMS[p.equipment[target_slot]['i']]['name']} wurde verzaubert: {ench['name']}")
            p.zone.emit_fx(p.x, p.z, {"k": "buff", "id": p.id, "school": "arcane"})
            self._consume(p, slot)
            self.send_stats(p)
        elif kind == "bag":
            size = BAGS.get(inst["i"], 0)
            bags = p.misc.setdefault("bagslots", [])
            while len(bags) < MAX_BAGS:
                bags.append(None)
            idx = next((i for i, b in enumerate(bags) if b is None), None)
            if idx is None:
                small = min(range(MAX_BAGS), key=lambda i: BAGS.get(bags[i], 0))
                if BAGS.get(bags[small], 0) >= size:
                    self.err(p, "Alle Taschenplätze sind bereits mit gleich großen oder größeren Taschen belegt.")
                    return
                old = bags[small]
                bags[small] = inst["i"]
                p.bags[slot] = {"i": old, "n": 1}
            else:
                bags[idx] = inst["i"]
                p.bags[slot] = None
            self.sys(p, f"Tasche angelegt: {it['name']} ({size} Plätze)")
            p.save_dirty = True
            self.send_inventory(p)
        elif kind == "summon_pet_item":
            pass

    def _consume(self, p: Player, slot: int):
        inst = p.bags[slot]
        inst["n"] -= 1
        if inst["n"] <= 0:
            p.bags[slot] = None
        p.save_dirty = True
        self.send_inventory(p)
