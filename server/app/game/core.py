"""Kern der Weltsimulation: Schaden, Heilung, Tod, Beute, Erfahrung, Regeneration, Automatischer Angriff,
Bewegung zwischen Zonen, Instanzen und das Senden der Weltzustände an die Clients."""
from __future__ import annotations

import math
import random
import time

from ..content import world as W
from ..content.classes import MAX_LEVEL, talent_points, xp_to_next
from ..content.factions import FACTIONS
from ..content.items import ITEMS, item_usable_by, world_drop_pool
from ..content.mobs import mob_xp
from . import combat as C
from .entities import RUN_SPEED, Aura, GameObj, GroundEffect, Mob, Npc, Pet, Player, Trap, Unit, now
from .stats import recalc

ENERGY_REGEN = 10.0
CONCENTRATION_REGEN = 6.0
DEATH_DURABILITY = 10


class CoreMixin:
    # ================================================================== Senden
    def send(self, p: Player, msg: dict):
        if p.session:
            p.session.send(msg)

    def sys(self, p: Player, text: str):
        self.send(p, {"t": "sys", "text": text})

    def err(self, p: Player, text: str):
        self.send(p, {"t": "err", "text": text})

    def toast(self, p: Player, title: str, text: str = "", kind: str = "info", icon: str | None = None):
        self.send(p, {"t": "toast", "title": title, "text": text, "kind": kind, "icon": icon})

    def find_unit(self, zone, uid: int | None) -> Unit | None:
        if zone is None or uid is None:
            return None
        return zone.entities.get(uid)

    # ================================================================== Schaden
    def damage(self, src: Unit, dst: Unit, amount: float, school: str, ab: str | None, kind: str = "hit",
               threat_mult: float = 1.0, extra_threat: float = 0.0, periodic: bool = False, mitigate: bool = True,
               armor_pen: float = 0.0) -> int:
        if dst.dead or dst.hidden or isinstance(dst, (Npc, GameObj, Trap, GroundEffect)):
            return 0
        zone = dst.zone
        if zone is None:
            return 0
        t = now()
        if isinstance(dst, Mob) and dst.state == "evade":
            zone.emit(dst, {"s": src.id, "d": dst.id, "a": 0, "k": "evade", "ab": ab, "sc": school})
            return 0
        if dst.immune:
            zone.emit(dst, {"s": src.id, "d": dst.id, "a": 0, "k": "immune", "ab": ab, "sc": school})
            return 0
        # Rüstung & Widerstand
        if school == "physical" and mitigate and not periodic:
            armor = C.unit_armor(dst) * (1.0 - max(0.0, min(0.9, armor_pen)))
            amount *= 1.0 - C.armor_reduction(armor, src.level)
        elif school != "physical":
            amount *= C.resist_mult(dst, school, src.level)
        # Erlittener Schaden (Auren, Talente, Sets)
        taken_pct = dst.aura_pct("dmg_taken")
        if isinstance(dst, Player):
            taken_pct += dst.mods.get("dmg_taken_pct", 0.0)
            if dst.form() == "baer":
                taken_pct -= 10
        if isinstance(src, Player) and isinstance(dst, Player):
            amount *= 0.75       # PvP-Dämpfung
        amount *= max(0.05, 1.0 + taken_pct / 100.0)
        if isinstance(src, Mob) and not isinstance(src, Pet) and dst.zone and dst.zone.is_instance and "nekrotisch" in dst.zone.affixes:
            pass
        amount = max(1, int(round(amount)))
        # Absorption
        absorbed = 0
        for a in list(dst.auras):
            if a.absorb > 0 and amount > 0:
                take = min(a.absorb, amount)
                a.absorb -= take
                amount -= int(take)
                absorbed += int(take)
                if a.absorb <= 0.5:
                    dst.auras.remove(a)
                    dst.mark("au")
        if amount <= 0:
            zone.emit(dst, {"s": src.id, "d": dst.id, "a": 0, "k": "absorb", "ab": ab, "sc": school, "ab2": absorbed})
            self._after_hit_threat(src, dst, absorbed, threat_mult, extra_threat)
            return 0
        # Tod verhindern (z. B. Barbar "Unbeugsam", Duelle)
        if dst.hp - amount <= 0:
            cd = next((a for a in dst.auras if a.cheat_death), None)
            if cd:
                dst.auras.remove(cd)
                dst.mark("au")
                amount = max(0, dst.hp - 1)
            elif isinstance(dst, Player) and self._duel_finishing(src, dst):
                amount = max(0, dst.hp - 1)
        if isinstance(dst, Mob) and dst.look.get("dummy"):
            dst.hp = max(1, dst.hp - amount)
        else:
            dst.hp -= amount
        dst.mark("hp")
        dst.last_hit_t = t
        ev = {"s": src.id, "d": dst.id, "a": amount, "k": kind, "ab": ab, "sc": school}
        if periodic:
            ev["pe"] = 1
        if absorbed:
            ev["ab2"] = absorbed
        zone.emit(dst, ev)
        # Kontrolleffekte, die durch Schaden enden
        broke = False
        for a in list(dst.auras):
            if a.break_dmg is not None or a.sleep:
                a.dmg_taken_acc += amount
                lim = (a.break_dmg or 0.0) * dst.max_hp
                if a.sleep or a.poly or a.dmg_taken_acc > lim:
                    dst.auras.remove(a)
                    broke = True
        if broke:
            dst.mark("au")
            if isinstance(dst, Mob) and dst.look.get("poly") and not any(x.poly for x in dst.auras):
                dst.look.pop("poly", None)
                dst.mark("look")
        self._after_hit_threat(src, dst, amount, threat_mult, extra_threat)
        # Lebensentzug
        if isinstance(src, Unit) and not src.dead:
            ls = sum(a.lifesteal for a in src.auras) + (src.mods.get("lifesteal", 0.0) / 100.0 if isinstance(src, Player) else 0.0)
            if ls > 0 and not periodic:
                self.heal(src, src, int(amount * ls), "Lebensentzug", quiet=True)
        # Reaktionen des Ziels
        if not periodic and school == "physical" and src is not dst:
            for a in dst.auras:
                if a.chill_attackers and src.alive and isinstance(src, Mob):
                    src.add_aura(Aura({"id": "frostpanzer_kaelte", "name": "Frostpanzer", "debuff": True, "slow": a.chill_attackers,
                                       "icon": "frozen-body"}, dst.id, t, dst.level, 5))
                if a.reflect_melee and src.alive and src.dist(dst) < 6:
                    self.damage(dst, src, amount * a.reflect_melee, "nature", a.name, "hit", periodic=True)
        if isinstance(dst, Player):
            dst.combat_until = max(dst.combat_until, t + 5.0)
            if dst.eating:
                self.stop_eating(dst)
            if dst.cast and dst.cast.get("kind") in ("gather", "craft", "hearth", "mount", "use"):
                self.interrupt(dst)
            elif dst.cast and not dst.cast.get("channel") and dst.cast.get("kind") == "ability" and not periodic:
                # Zauber-Rückstoß (wie in WoW): 0,3 Sek. Verzögerung, höchstens zweimal
                if dst.cast.get("pushback", 0) < 2 and not dst.mods.get("no_pushback"):
                    dst.cast["pushback"] = dst.cast.get("pushback", 0) + 1
                    dst.cast["end"] = min(dst.cast["end"] + 0.3, dst.cast["end"] + 0.3)
                    dst.mark("cast")
            if dst.mounted and not periodic:
                self.dismount(dst)
            if not periodic:
                self.resource_on_damage_taken(dst, amount)
            if dst.sitting:
                dst.sitting = False
                dst.mark("st")
        if isinstance(src, Player):
            src.combat_until = max(src.combat_until, t + 5.0)
            self.progress_counter(src, "damage", amount)
            if isinstance(dst, Mob) and dst.look.get("dummy") and ab:
                self.quest_event(src, "dummy_ability", 1)
        owner = self.owner_player(src) if not isinstance(src, Player) else None
        if owner:
            owner.combat_until = max(owner.combat_until, t + 5.0)
        if dst.hp <= 0:
            self.kill(dst, src)
        return amount

    def _after_hit_threat(self, src: Unit, dst: Unit, amount: float, threat_mult: float, extra: float):
        if isinstance(dst, Mob) and not isinstance(dst, Pet):
            if isinstance(src, (Player, Pet)):
                m = threat_mult
                if isinstance(src, Player):
                    m *= 1.0 + src.aura_pct("threat") / 100.0
                self.add_threat(dst, src, amount * m + extra)

    def resource_on_damage_taken(self, p: Player, amount: int):
        conv = C.resource_conversion(p.level)
        if p.power_type == "rage":
            self.gain_power(p, 2.5 * amount / conv)
        elif p.power_type == "resolve":
            self.gain_power(p, 3.0 * amount / conv)

    def resource_on_damage_dealt(self, p: Player, amount: int, auto: bool):
        conv = C.resource_conversion(p.level)
        if p.power_type == "rage":
            self.gain_power(p, (7.5 if auto else 3.0) * amount / conv)
            if p.power >= p.max_power:
                self.quest_event(p, "rage_full", 1)
        elif p.power_type == "resolve" and auto:
            self.gain_power(p, 4.0 * amount / conv)
        elif p.power_type == "focus":
            self.gain_power(p, 8.0 if auto else 3.0)

    def heal(self, src: Unit, dst: Unit, amount: int, ab: str, crit: bool = False, quiet: bool = False):
        if dst.dead or amount <= 0:
            return 0
        if isinstance(dst, Player) or isinstance(dst, Pet):
            amount = int(amount * (1.0 + dst.aura_pct("heal_taken") / 100.0))
        before = dst.hp
        dst.hp = min(dst.max_hp, dst.hp + int(amount))
        gained = dst.hp - before
        dst.mark("hp")
        if dst.zone and not quiet:
            dst.zone.emit(dst, {"s": src.id, "d": dst.id, "a": gained, "k": "healcrit" if crit else "heal", "ab": ab, "sc": "holy",
                                "oh": int(amount) - gained})
        # Heilung erzeugt Bedrohung bei allen Gegnern, die das Ziel bekämpfen
        if isinstance(src, Player) and gained > 0 and dst.zone:
            if src is not dst and isinstance(dst, Player):
                self.quest_event(src, "heal_other", 1)
                self.progress_counter(src, "healing", gained)
            for m in dst.zone.mobs_near(dst.x, dst.z, 40):
                if dst.id in m.threat and not isinstance(m, Pet):
                    self.add_threat(m, src, gained * 0.5 / max(1, len(m.threat)))
        return gained

    def miss_event(self, src: Unit, dst: Unit, kind: str, ab: str | None, school: str = "physical"):
        if dst.zone:
            dst.zone.emit(dst, {"s": src.id, "d": dst.id, "a": 0, "k": kind, "ab": ab, "sc": school})
        if isinstance(dst, Player) and kind == "parry":
            self.quest_event(dst, "parry", 1)

    def kill(self, dst: Unit, killer: Unit):
        if isinstance(dst, Pet):
            dst.dead = True
            dst.hp = 0
            dst.mark("hp", "st")
            dst.corpse_until = now() + 3
            dst.respawn_at = 0
            owner = self.players.get(dst.owner_id)
            if owner and dst.id in owner.pets:
                owner.pets.remove(dst.id)
            return
        if isinstance(dst, Player):
            self.player_died(dst, killer)
        elif isinstance(dst, Mob):
            self.mob_died(dst, killer)

    # ================================================================== Tod eines Gegners
    def mob_died(self, mob: Mob, killer: Unit):
        t = now()
        zone = mob.zone
        tpl = mob.tpl
        mob.dead = True
        mob.hp = 0
        mob.cast = None
        mob.auras = []
        mob.state = "dead"
        mob.combat = False
        mob.target = None
        mob.mark("hp", "st", "cast", "au", "tg")
        if mob.look.pop("poly", None):
            mob.mark("look")
        if tpl.get("death_yell"):
            self.yell(mob, tpl["death_yell"])
        for sid in list(mob.summons):
            s = zone.entities.get(sid)
            if isinstance(s, Mob) and not s.dead:
                self.mob_died(s, killer)
        killer_p = self.owner_player(killer)
        if killer_p and isinstance(killer, Pet):
            self.quest_event(killer_p, "pet_kill", 1)
        tap = mob.tap or ({killer_p.id} if killer_p else set())
        eligible = [zone.players[pid] for pid in tap
                    if pid in zone.players and not zone.players[pid].dead and zone.players[pid].dist(mob) < 100]
        if not eligible and killer_p and killer_p.alive:
            eligible = [killer_p]
        mob.tap = set(p.id for p in eligible) or mob.tap
        n = len(eligible)
        boss = tpl.get("boss")
        for p in eligible:
            xp = int(mob_xp(tpl, mob.level, p.level) * C.group_xp_factor(n) / max(1, n))
            if zone.is_instance:
                xp = int(xp * (1.0 + zone.mode_cfg.get("loot_bonus", 0) * 0.5))
            if xp > 0:
                self.add_xp(p, xp, mob)
            self.quest_kill(p, tpl["id"])
            self.progress_counter(p, "kills", 1)
            if tpl.get("rare"):
                self.progress_counter(p, "rare_kills", 1)
            for fid, amount in (tpl.get("rep") or {}).items():
                self.add_rep(p, fid, amount)
            if boss:
                self.on_boss_kill(p, mob)
            loot = self.generate_loot(mob, p)
            if loot["items"] or loot["copper"]:
                mob.loot[p.id] = loot
        mob.threat.clear()
        if tpl.get("summoned") or mob.owner_boss:
            mob.corpse_until = t + 8
            mob.respawn_at = 0
        elif zone.is_instance:
            mob.corpse_until = t + 1800
            mob.respawn_at = 0
        else:
            mob.corpse_until = t + (180 if mob.loot else 40)
            resp = tpl.get("respawn", 60)
            mob.respawn_at = t + resp * random.uniform(0.9, 1.15) if resp else 0.0
        if zone.is_instance and boss:
            zone.bosses_killed.append(tpl["id"])
            if zone.encounter == mob.id:
                zone.encounter = None
            if tpl.get("final_boss"):
                for p in eligible:
                    self.on_dungeon_complete(p, zone)
        if tpl.get("world_boss"):
            for p in zone.players.values():
                self.toast(p, f"{mob.name} wurde besiegt!", "Ein Weltboss ist gefallen.", "boss")

    def player_needs_item(self, p: Player, item_id: str) -> bool:
        for qid in W.ITEM_QUESTS.get(item_id, []):
            if qid in p.quests_active:
                q = W.QUESTS[qid]
                for o in q["objectives"]:
                    if o["type"] == "collect" and o["item"] == item_id and p.count_item(item_id) < o["count"]:
                        return True
        return False

    def boss_locked(self, p: Player, zone, boss_id: str) -> bool:
        key = f"{zone.id}:{zone.mode}:{boss_id}"
        lock = p.misc.get("lockouts", {}).get(key)
        return bool(lock and lock > time.time())

    def set_boss_lock(self, p: Player, zone, boss_id: str):
        key = f"{zone.id}:{zone.mode}:{boss_id}"
        locks = p.misc.setdefault("lockouts", {})
        # Normal: tägliche Sperre (20 Std.), Heroisch & Mythisch: wöchentlich (Mittwoch 6 Uhr)
        if zone.mode == "normal":
            until = time.time() + 20 * 3600
        else:
            until = self.next_weekly_reset()
        locks[key] = until
        for k in [k for k, v in locks.items() if v < time.time()]:
            del locks[k]
        p.save_dirty = True

    @staticmethod
    def next_weekly_reset() -> float:
        tt = time.time()
        lt = time.gmtime(tt)
        days = (2 - lt.tm_wday) % 7       # Mittwoch
        base = tt - (lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec) + 4 * 3600
        target = base + days * 86400
        if target <= tt:
            target += 7 * 86400
        return target

    @staticmethod
    def next_daily_reset() -> float:
        tt = time.time()
        lt = time.gmtime(tt)
        base = tt - (lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec) + 4 * 3600
        return base if base > tt else base + 86400

    def generate_loot(self, mob: Mob, p: Player) -> dict:
        tpl = mob.tpl
        zone = mob.zone
        items: list[list] = []
        bonus = zone.mode_cfg.get("loot_bonus", 0.0) if zone.is_instance else 0.0
        for entry in tpl.get("loot", []):
            it = ITEMS.get(entry["item"])
            if not it:
                continue
            if it.get("quest") and not self.player_needs_item(p, entry["item"]):
                continue
            if random.random() < entry["chance"]:
                items.append([entry["item"], entry.get("n", 1)])
        fam = tpl.get("family")
        # Materialien
        if tpl.get("hide"):
            ch = tpl.get("hide_chance", 0.4) * (1.0 if "lederverarbeitung" in p.professions else 0.35)
            if random.random() < ch:
                items.append([tpl["hide"], random.randint(1, 2)])
        if tpl.get("cloth") and random.random() < 0.3:
            items.append([tpl["cloth"], random.randint(1, 2)])
        if tpl.get("mats"):
            for entry in tpl["mats"]:
                if random.random() < entry["chance"]:
                    items.append([entry["item"], random.randint(*entry.get("n", (1, 1)))])
        # Weltbeute
        wd = tpl.get("world_drop", 0.0)
        if wd and random.random() < wd * (1 + bonus):
            q = 3 if random.random() < 0.12 + bonus * 0.3 else 2
            pool = world_drop_pool(mob.level, q)
            usable = [i for i in pool if item_usable_by(ITEMS[i], p.cls, p.class_id)] or pool
            if usable:
                items.append([random.choice(usable), 1])
        # Bossbeute (persönliche Beute pro Spieler, GDD 5)
        bl = tpl.get("boss_loot")
        if bl:
            locked = self.boss_locked(p, zone, tpl["id"]) if zone.is_instance else self._world_boss_locked(p, tpl["id"])
            if not locked:
                pool = [i for i in bl.get("pool", []) if i in ITEMS]
                usable = [i for i in pool if item_usable_by(ITEMS[i], p.cls, p.class_id)] or pool
                n = bl.get("n", 1) + (1 if bonus >= 0.35 and random.random() < 0.5 else 0)
                picks = random.sample(usable, min(n, len(usable))) if usable else []
                for i in picks:
                    items.append([i, 1])
                if bl.get("legendary") and random.random() < bl.get("legendary_chance", 0) * (1 + bonus * 2):
                    items.append([bl["legendary"], 1])
                if bl.get("mythic") and zone.is_instance and zone.mode == "mythisch" and random.random() < bl.get("mythic_chance", 0.05):
                    items.append([bl["mythic"], 1])
                if bl.get("mount") and random.random() < bl.get("mount_chance", 0.01):
                    items.append([bl["mount"], 1])
                if zone.is_instance:
                    self.set_boss_lock(p, zone, tpl["id"])
                else:
                    self._set_world_boss_lock(p, tpl["id"])
            else:
                self.sys(p, "Ihr habt diesen Boss in diesem Zeitraum bereits geplündert – nur Gold und Materialien.")
        copper = 0
        if tpl.get("copper"):
            lo, hi = tpl["copper"]
            copper = random.randint(lo, hi)
        elif fam in ("humanoid", "untot", "daemon", "riese", "zwerg") and not tpl.get("critter") and not tpl.get("summoned"):
            copper = random.randint(int(mob.level * 1.5), int(mob.level * 4 + 4)) if random.random() < 0.7 else 0
        if tpl.get("elite"):
            copper = int(copper * 1.8)
        copper = int(copper * (1 + bonus))
        return {"items": items, "copper": copper}

    def _world_boss_locked(self, p: Player, boss_id: str) -> bool:
        lock = p.misc.get("lockouts", {}).get("welt:" + boss_id)
        return bool(lock and lock > time.time())

    def _set_world_boss_lock(self, p: Player, boss_id: str):
        p.misc.setdefault("lockouts", {})["welt:" + boss_id] = self.next_weekly_reset()
        p.save_dirty = True

    # ================================================================== Erfahrung & Stufen
    def add_xp(self, p: Player, amount: int, src: Unit | None = None):
        if p.level >= MAX_LEVEL or amount <= 0:
            return
        p.xp += amount
        self.send(p, {"t": "xp", "a": amount, "src": src.name if src else None, "xp": p.xp, "next": xp_to_next(p.level)})
        leveled = False
        while p.level < MAX_LEVEL and p.xp >= xp_to_next(p.level):
            p.xp -= xp_to_next(p.level)
            p.level += 1
            leveled = True
            self.on_level_up(p)
        if p.level >= MAX_LEVEL:
            p.xp = 0
        p.save_dirty = True
        if not leveled:
            self.send_xp(p)

    def send_xp(self, p: Player):
        self.send(p, {"t": "xpbar", "xp": p.xp, "next": xp_to_next(p.level), "lvl": p.level})

    def on_level_up(self, p: Player):
        recalc(p, full=True)
        p.mark("lvl", "hp", "pw")
        if p.zone:
            p.zone.emit_fx(p.x, p.z, {"k": "levelup", "id": p.id})
        from ..content.abilities import ABILITIES, class_abilities
        new = [a for a in class_abilities(p.class_id) if ABILITIES[a]["level"] == p.level]
        self.send(p, {"t": "levelup", "lvl": p.level, "new": new, "tp": talent_points(p.level)})
        self.sys(p, f"Glückwunsch! Ihr habt Stufe {p.level} erreicht!")
        for a in new:
            self.sys(p, f"Ihr habt eine neue Fähigkeit erlernt: {ABILITIES[a]['name']}.")
            self.auto_place_ability(p, a)
        if talent_points(p.level) > 0 and talent_points(p.level - 1) == 0:
            self.sys(p, "Ihr habt Euren ersten Talentpunkt erhalten! Öffnet das Talentfenster (N).")
        self.send_stats(p)
        self.send_abilities(p)
        self.send_xp(p)
        self.check_achievements(p, "level")
        if p.party:
            for m in self.party_players(p.party):
                if m is not p:
                    self.sys(m, f"{p.name} hat Stufe {p.level} erreicht!")
        if p.guild_id:
            self.guild_broadcast(p.guild_id, f"{p.name} hat Stufe {p.level} erreicht!", exclude=p.id)

    # ================================================================== Tod eines Spielers
    def _duel_finishing(self, src: Unit, dst: Player) -> bool:
        sp = self.owner_player(src)
        return bool(sp and dst.duel_with == sp.id and getattr(dst, "duel_active", False))

    def player_died(self, p: Player, killer: Unit | None = None):
        kp = self.owner_player(killer) if killer else None
        if kp and getattr(p, "duel_active", False) and p.duel_with == kp.id:
            self.end_duel(kp, p)
            return
        p.dead = True
        p.hp = 0
        p.cast = None
        p.auto_attack = False
        p.eating = None
        p.sitting = False
        p.auras = [a for a in p.auras if a.id.startswith("passiv_")]
        if p.mounted:
            self.dismount(p)
        recalc(p)
        p.hp = 0
        if p.power_type in ("rage", "resolve", "focus"):
            p.power = 0
        p.mark("hp", "pw", "st", "au", "cast")
        if p.zone:
            for e in p.zone.entities.values():
                if isinstance(e, Mob) and p.id in e.threat:
                    del e.threat[p.id]
            for pet in self.pets_of(p):
                p.zone.remove(pet)
            p.pets = []
        pvp = kp is not None and kp is not p
        if not pvp and not (p.zone and p.zone.is_arena):
            for slot, inst in p.equipment.items():
                if inst and ITEMS.get(inst["i"], {}).get("type") in ("weapon", "armor"):
                    inst["d"] = max(0, inst.get("d", 100) - DEATH_DURABILITY)
            p.save_dirty = True
        self.send(p, {"t": "died", "by": killer.name if killer else None, "pvp": pvp,
                      "arena": bool(p.zone and p.zone.is_arena)})
        self.sys(p, "Ihr seid gestorben." + (" Eure Ausrüstung hat 10 % Haltbarkeit verloren." if not pvp else ""))
        self.progress_counter(p, "deaths", 1)
        if pvp:
            self.on_pvp_kill(kp, p)
        if p.zone and p.zone.is_arena:
            self.arena_player_died(p)

    def release_spirit(self, p: Player):
        if not p.dead:
            return
        zone = p.zone
        if zone and zone.is_arena:
            return
        p.dead = False
        p.hp = max(1, p.max_hp // 2)
        if p.power_type == "mana":
            p.power = p.max_power // 2
        p.mark("hp", "pw", "st")
        if zone and zone.is_instance:
            sx, sz, sr = zone.cfg["start"]
            self.teleport(p, sx, sz, sr)
            self.sys(p, "Ihr erwacht am Eingang der Instanz.")
            return
        gy = zone.cfg.get("graveyard") if zone else None
        if not gy:
            home = self.zones.get("gruenmark")
            gx, gz, gr = W.ZONES["gruenmark"]["graveyard"]
            self.move_player(p, home, gx, gz, gr)
        else:
            self.teleport(p, gy[0], gy[1], gy[2])
        healer = zone.cfg.get("spirit_healer", "Bruder Anselm") if zone else "Bruder Anselm"
        self.sys(p, f"{healer} hat Euch ins Leben zurückgeholt. Möge das Licht mit Euch sein.")

    # ================================================================== Bewegung
    def teleport(self, p: Unit, x: float, z: float, r: float | None = None, kind: str = "tele"):
        zone = p.zone
        x, z = zone.walkable_clamp(x, z)
        y = zone.height(x, z)
        p.set_pos(x, y, z, r if r is not None else p.r)
        if isinstance(p, Player):
            p.move_budget = 14.0
            p.last_safe = (x, z)
            self.send(p, {"t": "force", "p": [round(x, 2), round(y, 2), round(z, 2), round(p.r, 3)], "k": kind})

    def move_player(self, p: Player, zone, x: float, z: float, r: float):
        old = p.zone
        if old:
            for pet in self.pets_of(p):
                old.remove(pet)
            old.remove(p)
        p.pets = []
        p.cast = None
        p.auto_attack = False
        p.target = None
        p.loot_open = None
        p.eating = None
        p.sitting = False
        if p.trade:
            self.cancel_trade(p, "Handel abgebrochen.")
        x, z = zone.walkable_clamp(x, z)
        p.x, p.z, p.r = x, z, r
        p.y = zone.height(x, z)
        p.zone_id = zone.id
        zone.add(p)
        p.known = set()
        p.flag_cache = {}
        p.ready = False
        p.move_budget = 14.0
        p.last_safe = (x, z)
        p.portal_lock = now() + 3.0
        p.mark("p", "tg", "cast", "st")
        p.save_dirty = True
        self.send(p, {"t": "zone", "zone": zone.id, "name": zone.cfg["name"], "inst": zone.is_instance, "mode": zone.mode,
                      "mode_name": zone.mode_cfg["name"] if zone.is_instance else None, "affixes": zone.affixes,
                      "p": [round(x, 2), round(p.y, 2), round(z, 2), round(r, 3)], "levels": zone.cfg.get("levels")})
        self.discover_zone(p, zone.id)
        self.quest_explore(p, zone.id)
        if zone.is_instance and not zone.is_arena:
            self.check_achievements(p, "dungeon_enter")

    def instance_for(self, p: Player, zone_id: str, mode: str = "normal"):
        from .zone import Zone
        cfg = W.ZONES[zone_id]
        owner = f"party{p.party.id}" if p.party else f"p{p.char_id}"
        key = f"{zone_id}:{mode}:{owner}"
        zone = self.zones.get(key)
        if zone is None and p.party:
            for m in self.party_players(p.party):
                if m.zone and m.zone.id == zone_id and m.zone.is_instance:
                    zone = m.zone
                    break
        if zone is None:
            affixes = self.current_affixes() if mode == "mythisch" else []
            zone = Zone(self, zone_id, key, mode, affixes)
            zone.owner_party = p.party.id if p.party else None
            self.zones[key] = zone
        if len(zone.players) >= cfg.get("max_players", 5):
            return None
        return zone

    def current_affixes(self) -> list[str]:
        week = int((time.time() - 4 * 3600) // (7 * 86400))
        keys = sorted(W.AFFIXES)
        rng = random.Random(week)
        return rng.sample(keys, 2)

    def enter_portal(self, p: Player, portal: dict, mode: str | None = None):
        if now() < p.portal_lock:
            return
        dest = portal["to"]
        dcfg = W.ZONES[dest]
        if p.level < portal.get("min_level", 1):
            if now() - p.misc.get("_portal_msg", 0) > 5:
                p.misc["_portal_msg"] = now()
                self.err(p, f"Ihr müsst mindestens Stufe {portal['min_level']} sein, um {dcfg['name']} zu betreten.")
            return
        p.portal_lock = now() + 3.0
        if dcfg["type"] == "dungeon":
            modes = dcfg.get("modes", ["normal"])
            if mode is None and len(modes) > 1:
                p.portal_lock = now() + 1.0
                self.send(p, {"t": "dungeon_select", "zone": dest, "name": dcfg["name"], "levels": dcfg.get("levels"),
                              "players": dcfg.get("players_text", ""), "modes": [
                                  {"id": m, "name": W.MODES[m]["name"], "desc": W.MODES[m]["desc"],
                                   "min_level": dcfg["levels"][0] + (0 if m == "normal" else (5 if m == "heroisch" else 8))}
                                  for m in modes],
                              "affixes": [{"id": a, **W.AFFIXES[a]} for a in self.current_affixes()],
                              "locks": self.lockout_info(p, dest)})
                return
            mode = mode or "normal"
            if mode not in modes:
                return
            need = dcfg["levels"][0] + (0 if mode == "normal" else (5 if mode == "heroisch" else 8))
            if p.level < need and not p.gm:
                self.err(p, f"Für {W.MODES[mode]['name']} braucht Ihr Stufe {need}.")
                return
            zone = self.instance_for(p, dest, mode)
            if zone is None:
                self.err(p, "Diese Instanz ist voll.")
                return
            sx, sz, sr = dcfg["start"]
            p.misc["instance_return"] = [p.zone.id, round(p.x, 1), round(p.z, 1), round(p.r + math.pi, 2)]
            self.move_player(p, zone, sx, sz, sr)
            self.sys(p, f"Ihr betretet: {dcfg['name']} ({W.MODES[mode]['name']}). Gegner in Instanzen erscheinen nicht erneut.")
            if zone.affixes:
                self.sys(p, "Mythische Modifikatoren: " + ", ".join(W.AFFIXES[a]["name"] for a in zone.affixes))
        else:
            dx, dz, dr = portal.get("dest") or dcfg.get("start")
            self.move_player(p, self.zones[dest], dx, dz, dr)

    def leave_instance(self, p: Player):
        zone = p.zone
        ret = p.misc.pop("instance_return", None)
        if ret and ret[0] in self.zones:
            self.move_player(p, self.zones[ret[0]], ret[1], ret[2], ret[3])
            return
        ex = zone.cfg.get("exit") or ["gruenmark", 0, 0, 0]
        self.move_player(p, self.zones[ex[0]], ex[1], ex[2], ex[3])

    def lockout_info(self, p: Player, zone_id: str) -> list:
        out = []
        for k, v in p.misc.get("lockouts", {}).items():
            if k.startswith(zone_id + ":") and v > time.time():
                _, mode, boss = k.split(":")
                out.append({"mode": mode, "boss": W.MOBS.get(boss, {}).get("name", boss), "left": int(v - time.time())})
        return out

    # ================================================================== Auren
    def update_auras(self, u: Unit, t: float):
        changed = False
        for a in list(u.auras):
            if (a.dot or a.hot) and a.next_tick and t >= a.next_tick and not u.dead:
                spec = a.dot or a.hot
                a.next_tick += spec.get("interval", 3)
                amount = a.extra.get("tick") or spec.get("flat", 5)
                src = self.find_unit(u.zone, a.src) or self.players.get(a.src) or u
                if a.dot:
                    amount *= a.stacks
                    self.damage(src, u, amount, spec.get("school", "physical"), a.name, "hit", periodic=True)
                    if a.spread and u.dead:
                        pass
                else:
                    self.heal(src, u, int(amount), a.name)
                if u.dead:
                    return
            if a.food and t >= a.next_tick:
                pass
            if t >= a.expires:
                if a in u.auras:
                    u.auras.remove(a)
                changed = True
                if a.taunt and isinstance(u, Mob):
                    u.taunt_by = None
                if a.poly and isinstance(u, Mob):
                    u.look.pop("poly", None)
                    u.mark("look")
                if a.form and isinstance(u, Player):
                    u.look["form"] = None
                    u.mark("look")
        if changed:
            u.mark("au")
            if isinstance(u, Player):
                self.after_aura_change(u)

    # ================================================================== Spieler-Tick
    def player_tick(self, p: Player, t: float, dt: float):
        if p.dead:
            return
        self.update_auras(p, t)
        if p.dead:
            return
        if p.cast:
            c = p.cast
            if c.get("channel"):
                while c["ticks_left"] > 0 and t >= c["next_tick"]:
                    c["ticks_left"] -= 1
                    c["next_tick"] += c["interval"]
                    self.channel_tick(p, c)
                    if not p.cast:
                        break
                if p.cast and (t >= c["end"] - 0.02 or c["ticks_left"] <= 0):
                    p.cast = None
                    p.mark("cast")
            elif t >= c["end"]:
                p.cast = None
                p.mark("cast")
                self.finish_player_cast(p, c)
        if p.auto_attack:
            self.player_auto_attack(p, t)
        if t >= p.next_regen:
            p.next_regen = t + 1.0
            self.player_regen(p, t)
        # Fallen in Dungeons
        zone = p.zone
        if zone.is_instance and zone.cfg.get("traps"):
            for tr in zone.cfg["traps"]:
                if (p.x - tr["x"]) ** 2 + (p.z - tr["z"]) ** 2 <= tr["r"] ** 2:
                    key = (tr["x"], tr["z"], p.id)
                    if t >= zone.trap_cd.get(key, 0):
                        zone.trap_cd[key] = t + tr.get("cd", 4)
                        zone.emit_fx(tr["x"], tr["z"], {"k": "trap", "x": tr["x"], "z": tr["z"], "fx": tr.get("fx", "blades")})
                        dmg = tr["flat"] * zone.mode_cfg.get("dmg", 1.0) * random.uniform(0.9, 1.1)
                        self.damage(p, p, dmg, tr.get("school", "physical"), tr["name"], "hit", mitigate=False)
                        if tr.get("debuff") and not p.dead:
                            d = tr["debuff"]
                            a = Aura(d, p.id, t, p.level, d.get("dur", 8))
                            if a.dot:
                                a.extra["tick"] = d["dot"].get("flat", 10) * zone.mode_cfg.get("dmg", 1.0)
                            p.add_aura(a)
                            self.after_aura_change(p)
        # Portale (beim Betreten)
        if t >= p.portal_lock:
            for portal in zone.cfg.get("portals", []):
                if (p.x - portal["x"]) ** 2 + (p.z - portal["z"]) ** 2 <= portal["r"] ** 2:
                    self.enter_portal(p, portal)
                    break
            if zone.is_instance and not zone.is_arena:
                sx, sz, _ = zone.cfg["start"]
                if (p.x - sx) ** 2 + (p.z - (sz + 4.5)) ** 2 <= 2.2 ** 2:
                    p.portal_lock = t + 3
                    self.leave_instance(p)
        # Unterzonen entdecken
        if t >= p.misc.get("_subzone_t", 0):
            p.misc["_subzone_t"] = t + 2.0
            sz = zone.subzone_at(p.x, p.z)
            if sz and sz != p.misc.get("_subzone"):
                p.misc["_subzone"] = sz
                self.send(p, {"t": "subzone", "name": sz, "pvp": zone.in_pvp_area(p.x, p.z)})
                self.discover_subzone(p, zone.id, sz)

    def player_regen(self, p: Player, t: float):
        st = p.stats
        changed = False
        if p.eating:
            e = p.eating
            if t >= e["until"]:
                self.stop_eating(p)
            else:
                if e.get("hp") and p.hp < p.max_hp:
                    p.hp = min(p.max_hp, p.hp + e["hp"])
                    changed = True
                if e.get("mp") and p.power_type == "mana" and p.power < p.max_power:
                    p.power = min(p.max_power, p.power + e["mp"])
                    changed = True
                full_hp = p.hp >= p.max_hp or not e.get("hp")
                full_mp = p.power_type != "mana" or p.power >= p.max_power or not e.get("mp")
                if full_hp and full_mp:
                    self.stop_eating(p)
        if not p.combat and p.hp < p.max_hp:
            p.hp = min(p.max_hp, p.hp + max(1, int(st.get("hp_regen", 1) * (3 if p.sitting else 1.5))))
            changed = True
        pt = p.power_type
        if pt == "mana" and p.power < p.max_power:
            rate = st.get("mp_regen", 1.0)
            if t - p.last_mana_spend < 5.0:
                rate *= p.mods.get("combat_regen", 0.0) / 100.0
            if rate > 0:
                p.power = min(p.max_power, p.power + rate)
                changed = True
        elif pt == "energy" and p.power < p.max_power:
            p.power = min(p.max_power, p.power + ENERGY_REGEN * (1 + st.get("haste", 0) / 100.0) * (1 + p.mods.get("energy_regen_pct", 0) / 100))
            changed = True
        elif pt == "concentration" and p.power < p.max_power:
            p.power = min(p.max_power, p.power + CONCENTRATION_REGEN * (1 + p.mods.get("regen_pct", 0) / 100.0))
            changed = True
        elif pt in ("rage", "resolve", "focus") and not p.combat and p.power > 0:
            p.power = max(0, p.power - (3 if pt == "rage" else 2))
            changed = True
        if changed:
            p.mark("hp", "pw")

    def stop_eating(self, p: Player):
        p.eating = None
        p.remove_aura("essen")
        p.remove_aura("trinken")
        if p.sitting:
            p.sitting = False
            p.mark("st")

    def player_auto_attack(self, p: Player, t: float):
        tgt = self.find_unit(p.zone, p.target) if p.target else None
        if not tgt or tgt.dead or tgt.hidden or not self.is_enemy(p, tgt):
            p.auto_attack = False
            return
        if p.stunned or p.incapacitated or p.form() is None and p.cast and not p.cast.get("allow_swing"):
            return
        ranged = p.stats.get("ranged")
        reach = (32.0 if ranged else p.radius + tgt.radius + 3.0)
        d = p.dist(tgt)
        if t >= p.swing_ready:
            if d > reach:
                if t - p.out_of_range_msg > 3:
                    p.out_of_range_msg = t
                    self.err(p, "Ihr seid zu weit entfernt.")
                p.swing_ready = t + 0.25
                return
            if ranged and d < 5.0:
                p.swing_ready = t + 0.25
                if t - p.out_of_range_msg > 3:
                    p.out_of_range_msg = t
                    self.err(p, "Ihr seid zu nah für den Bogen.")
                return
            if not p.facing(tgt):
                if t - p.out_of_range_msg > 3:
                    p.out_of_range_msg = t
                    self.err(p, "Ihr müsst Euer Ziel ansehen.")
                p.swing_ready = t + 0.25
                return
            if p.moving and ranged and now() - p.last_move_t < 0.25:
                p.swing_ready = t + 0.2
                return
            p.swing_ready = t + p.stats.get("speed", 2.0)
            self._swing(p, tgt, off=False, ranged=ranged)
        if p.dual_wielding() and t >= p.oh_swing_ready and d <= reach and p.facing(tgt):
            p.oh_swing_ready = t + p.stats.get("oh_speed", 2.0)
            self._swing(p, tgt, off=True, ranged=False)

    def _swing(self, p: Player, tgt: Unit, off: bool, ranged: bool):
        if p.sitting:
            p.sitting = False
            p.mark("st")
        if p.stealthed:
            self.break_stealth(p)
        crit_bonus = 0.0
        out = C.melee_outcome(p, tgt, tgt.facing(p), crit_bonus, ranged)
        if ranged:
            p.zone.emit_fx(p.x, p.z, {"k": "proj", "from": p.id, "to": tgt.id, "sp": 40.0, "school": "physical", "ab": "autoshot"})
        else:
            p.zone.emit_fx(tgt.x, tgt.z, {"k": "swing", "id": p.id, "to": tgt.id, "off": off})
        if out in ("miss", "dodge", "parry"):
            self.miss_event(p, tgt, out, "Automatischer Schuss" if ranged else None)
            if isinstance(tgt, Mob):
                self.add_threat(tgt, p, 1)
            if isinstance(tgt, Player) and out in ("dodge", "parry"):
                self.on_reactive(tgt, out)
            return
        dmg = C.player_melee_damage(p, off=off)
        dmg *= 1.0 + (p.mods.get("dmg_pct", 0.0) + p.aura_pct("dmg_done") + p.mods.get("auto_pct", 0.0)) / 100.0
        kind = "hit"
        if out == "crit":
            dmg *= 2.0 * (1 + p.mods.get("crit_dmg_pct", 0) / 100.0)
            kind = "crit"
            if p.mods.get("crit_resource"):
                self.gain_power(p, p.mods["crit_resource"])
        elif out == "block":
            dmg = max(0, dmg - (tgt.stats.get("block_value", 5) if isinstance(tgt, Player) else 0))
            kind = "block"
            if isinstance(tgt, Player):
                self.on_reactive(tgt, "block")
        threat_mult = 1.0 + p.mods.get("threat_pct", 0) / 100.0 + (0.3 if p.form() == "baer" else 0.0)
        if ranged:
            uid = tgt.id
            zone = p.zone

            def land(dmg=dmg, kind=kind):
                target = zone.entities.get(uid)
                if target and not target.dead:
                    dealt = self.damage(p, target, dmg, "physical", "Automatischer Schuss", kind, threat_mult=threat_mult)
                    if dealt:
                        self.resource_on_damage_dealt(p, dealt, True)
                        if p.dist(target) > 25:
                            self.quest_event(p, "long_shot", 1)
            zone.schedule(max(0.05, p.dist(tgt) / 40.0), land)
            return
        dealt = self.damage(p, tgt, dmg, "physical", None, kind, threat_mult=threat_mult,
                            armor_pen=p.mods.get("armor_pen", 0) / 100.0)
        if dealt:
            self.resource_on_damage_dealt(p, dealt, True)
            self.weapon_proc(p, tgt)

    # ================================================================== NPCs
    def npc_tick(self, n: Npc, t: float, dt: float):
        tpl = n.tpl
        if t < n.talk_until:
            return
        if n.talk_until and t >= n.talk_until:
            n.talk_until = 0
            if not tpl.get("wander") and not tpl.get("path"):
                n.r = n.home[2]
                n.mark("p")
        if tpl.get("path"):
            pts = tpl["path"]
            tx, tz = pts[n.path_i % len(pts)]
            if self.move_towards(n, tx, tz, tpl.get("speed", 1.6), dt, 0.3):
                n.path_i += 1
        elif tpl.get("wander"):
            if n.wander_to:
                if self.move_towards(n, n.wander_to[0], n.wander_to[1], 1.6, dt, 0.2):
                    n.wander_to = None
                    n.next_wander = t + random.uniform(4, 10)
            elif t >= n.next_wander:
                hx, hz, _ = n.home
                a = random.uniform(0, math.tau)
                d = random.uniform(1, tpl["wander"])
                tx, tz = hx + math.cos(a) * d, hz + math.sin(a) * d
                if n.zone.walkable(tx, tz):
                    n.wander_to = (tx, tz)
                else:
                    n.next_wander = t + 3
        if tpl.get("barks") and t >= n.next_bark:
            n.next_bark = t + random.uniform(35, 80)
            if any(p.dist(n) < 32 for p in n.zone.players.values()):
                self.mob_say(n, random.choice(tpl["barks"]), 36)

    # ================================================================== Zonen-Tick
    def zone_tick(self, zone, t: float, dt: float):
        in_combat: set[int] = set()
        for e in list(zone.entities.values()):
            if isinstance(e, Mob):
                self.mob_tick(e, t, dt)
                if e.threat and not e.dead:
                    for uid in e.threat:
                        in_combat.add(uid)
                        u = zone.entities.get(uid)
                        if isinstance(u, Pet):
                            in_combat.add(u.owner_id)
            elif isinstance(e, Npc):
                self.npc_tick(e, t, dt)
            elif isinstance(e, GameObj):
                if not e.available and e.respawn_at and t >= e.respawn_at:
                    e.available = True
                    e.hidden = False
                    e.mark("st")
            elif isinstance(e, Trap):
                if t >= e.expires:
                    zone.remove(e)
                elif t >= e.armed_at:
                    for u in zone.mobs_near(e.x, e.z, e.radius + 1.0):
                        owner = self.players.get(e.owner_id)
                        if owner and self.is_enemy(owner, u):
                            self.trigger_trap(e, u)
                            break
            elif isinstance(e, GroundEffect):
                self.ground_tick(e, t)
        for p in list(zone.players.values()):
            combat = (p.id in in_combat or t < p.combat_until) and not p.dead
            if combat != p.combat:
                p.combat = combat
                p.mark("st")
                if not combat:
                    p.last_reactive.clear()
            self.player_tick(p, t, dt)
        if zone.is_instance and zone.affixes and zone.encounter and t >= zone.next_affix:
            zone.next_affix = t + 22
            self.affix_pulse(zone)

    def affix_pulse(self, zone):
        boss = zone.entities.get(zone.encounter)
        if not boss or boss.dead:
            return
        if "bebend" in zone.affixes:
            for p in zone.players.values():
                if not p.dead:
                    zone.emit_fx(p.x, p.z, {"k": "tele", "dur": 2.0, "name": "Beben", "shape": "circle", "x": round(p.x, 2),
                                            "z": round(p.z, 2), "r": 5, "school": "physical"})
            pos = [(p.x, p.z) for p in zone.players.values() if not p.dead]

            def quake():
                for p in list(zone.players.values()):
                    if p.dead:
                        continue
                    if any((p.x - x) ** 2 + (p.z - z) ** 2 < 25 for x, z in pos):
                        self.damage(boss, p, p.max_hp * 0.12, "physical", "Beben", "hit", mitigate=False)
            zone.schedule(2.0, quake)
        if "vulkanisch" in zone.affixes:
            for p in list(zone.players.values())[:3]:
                if not p.dead:
                    self.spawn_ground(boss, {"name": "Vulkanisch", "radius": 3, "dur": 8, "interval": 1.0, "flat": p.max_hp * 0.06,
                                             "school": "fire", "fx": "fire", "delay": 1.5}, p.x, p.z, "mob")
                    zone.emit_fx(p.x, p.z, {"k": "tele", "dur": 1.5, "name": "Vulkanisch", "shape": "circle", "x": round(p.x, 2),
                                            "z": round(p.z, 2), "r": 3, "school": "fire"})

    # ================================================================== Senden der Welt
    def view_flags(self, p: Player, e: Unit) -> dict:
        if isinstance(e, Npc):
            return {"q": self.quest_marker(p, e.npc_id)}
        if isinstance(e, Mob) and not isinstance(e, Pet):
            tapped_other = e.tap is not None and p.id not in e.tap and not e.dead
            fl = {"l": bool(e.dead and e.loot.get(p.id)), "tap": tapped_other}
            if not e.dead and self.mob_needed_for_quest(p, e):
                fl["qm"] = True
            return fl
        if isinstance(e, GameObj):
            return {"u": e.available and self.obj_usable(p, e)}
        if isinstance(e, Player) and e is not p:
            return {"en": self.is_enemy(p, e), "pt": bool(p.party and e.party is p.party)}
        return {}

    def broadcast(self, zone):
        events, fxs = zone.events, zone.fx
        zone.events, zone.fx = [], []
        delta_cache: dict[int, dict] = {}
        for p in list(zone.players.values()):
            if not p.ready or not p.session:
                continue
            vis: set[int] = set()
            spawns, deltas = [], []
            px, pz = p.x, p.z
            v2 = zone.view2
            for e in zone.entities.values():
                if e is p or e.hidden:
                    continue
                if (e.x - px) ** 2 + (e.z - pz) ** 2 > v2:
                    continue
                if isinstance(e, Player) and e.stealthed and self.is_enemy(p, e) and e.dist(p) > 4:
                    continue
                if isinstance(e, Mob) and e.stealthed and e.dist(p) > 5:
                    continue
                if isinstance(e, GameObj) and e.spec.get("hidden_until_near") and e.dist(p) > 12:
                    continue
                vis.add(e.id)
                flags = self.view_flags(p, e)
                if e.id not in p.known:
                    info = e.spawn_info()
                    info["fl"] = flags
                    p.flag_cache[e.id] = flags
                    spawns.append(info)
                    continue
                d = None
                if e.dirty:
                    if e.id not in delta_cache:
                        delta_cache[e.id] = e.delta(e.dirty)
                    d = delta_cache[e.id]
                if p.flag_cache.get(e.id) != flags:
                    p.flag_cache[e.id] = flags
                    d = dict(d) if d else {"id": e.id}
                    d["fl"] = flags
                if d and len(d) > 1:
                    deltas.append(d)
            gone = p.known - vis
            for gid in gone:
                p.flag_cache.pop(gid, None)
            if p.dirty:
                deltas.append(p.delta(p.dirty, for_self=True))
            evs = [ev for (x, z, ev) in events if (x - px) ** 2 + (z - pz) ** 2 <= v2]
            fx = [f for (x, z, f) in fxs if (x - px) ** 2 + (z - pz) ** 2 <= v2]
            p.known = vis
            if spawns or deltas or gone or evs or fx:
                msg = {"t": "u"}
                if spawns:
                    msg["sp"] = spawns
                if gone:
                    msg["ds"] = list(gone)
                if deltas:
                    msg["e"] = deltas
                if evs:
                    msg["ev"] = evs
                if fx:
                    msg["fx"] = fx
                self.send(p, msg)
        for e in zone.entities.values():
            e.dirty.clear()
