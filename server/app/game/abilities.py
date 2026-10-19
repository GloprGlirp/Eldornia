"""Fähigkeiten-Engine: Prüfen, Wirken, Kanalisieren und Ausführen aller Spielerfähigkeiten.

Alles passiert serverseitig: Kosten, Abklingzeiten, globale Abklingzeit, Reichweite, Blickrichtung,
Positionierung (hinter dem Ziel), Reaktionsfenster (nach Block/Parade), Kombopunkte und Effekte.
"""
from __future__ import annotations

import math
import random

from ..content.abilities import ABILITIES, FAST_GCD_CLASSES, GCD, GCD_FAST, ability_range, scaled, scaled_range
from ..content.mobs import COMMON
from . import combat as C
from .entities import Aura, GameObj, GroundEffect, Mob, Npc, Pet, Player, Trap, Unit, now

ERR_NAMES = {"resolve": "Entschlossenheit", "rage": "Wut", "mana": "Mana", "energy": "Energie", "focus": "Fokus",
             "concentration": "Konzentration"}


class AbilityMixin:
    # ================================================================== Feindschaft
    def is_enemy(self, a: Unit, b: Unit) -> bool:
        if a is b or a.dead and not isinstance(a, Player):
            return False
        if isinstance(a, (Npc, GameObj)) or isinstance(b, (Npc, GameObj)):
            return False
        if a.side == "mob" and b.side == "mob":
            return False
        if a.side == "mob" or b.side == "mob":
            mob = a if a.side == "mob" else b
            return isinstance(mob, Mob) and (mob.hostile or mob.look.get("critter") or mob.look.get("dummy"))
        # Spieler gegen Spieler (inkl. Begleiter und Fallen)
        pa = self.owner_player(a)
        pb = self.owner_player(b)
        if not pa or not pb or pa is pb:
            return False
        if pa.duel_with == pb.id and pb.duel_with == pa.id and getattr(pa, "duel_active", False):
            return True
        if pa.team is not None and pb.team is not None and pa.team != pb.team:
            return True
        z = pa.zone
        if z and z.cfg.get("pvp_areas") and pa.zone is pb.zone:
            if z.in_pvp_area(pa.x, pa.z) and z.in_pvp_area(pb.x, pb.z):
                same_group = pa.party is not None and pa.party is pb.party
                same_guild = pa.guild_id is not None and pa.guild_id == pb.guild_id
                if not same_group and not same_guild:
                    return True
        return False

    def owner_player(self, u: Unit) -> Player | None:
        if isinstance(u, Player):
            return u
        oid = getattr(u, "owner_id", None)
        if oid:
            o = self.players.get(oid)
            return o
        return None

    def is_friendly(self, a: Unit, b: Unit) -> bool:
        if isinstance(b, Player) and isinstance(a, Player):
            return not self.is_enemy(a, b)
        if isinstance(b, Pet):
            return not self.is_enemy(a, b)
        return False

    # ================================================================== Bekannte Fähigkeiten
    def knows(self, p: Player, ab: dict) -> bool:
        if ab["cls"] != p.class_id:
            return False
        if ab["talent"]:
            return ab["id"] in getattr(p, "granted", [])
        return ab["level"] <= p.level

    def ab_cost(self, p: Player, ab: dict) -> int:
        if ab["cost_pct"]:
            base_mana = 40 + 15 * p.level + p.stats.get("int", 0) * 12 * 0.4
            cost = ab["cost_pct"] * base_mana
        else:
            cost = ab["cost"]
        mult = 1.0 + (p.mods.get("cost_pct:" + ab["id"], 0.0) + p.mods.get("cost_pct", 0.0) * (1 if ab["cost_pct"] else 0)
                      + p.aura_pct("cost")) / 100.0
        return int(max(0, cost * mult))

    def ab_cd(self, p: Player, ab: dict) -> float:
        return max(0.0, ab["cd"] + p.mods.get("cd:" + ab["id"], 0.0))

    def ab_cast(self, p: Player, ab: dict) -> float:
        if not ab["cast"]:
            return 0.0
        base = max(0.0, ab["cast"] + p.mods.get("cast:" + ab["id"], 0.0))
        if ab["channel"]:
            return base
        return base / (1.0 + p.stats.get("haste", 0) / 100.0)

    def gcd_for(self, p: Player) -> float:
        base = GCD_FAST if p.class_id in FAST_GCD_CLASSES or p.form() == "baer" else GCD
        return max(1.0, base / (1.0 + p.stats.get("haste", 0) / 100.0))

    # ================================================================== Prüfung
    def resolve_target(self, p: Player, ab: dict, tid: int | None) -> Unit | None:
        zone = p.zone
        tgt = zone.entities.get(tid) if tid is not None else (zone.entities.get(p.target) if p.target else None)
        t = ab["target"]
        if t == "enemy":
            return tgt
        if t == "friendly":
            if tgt is None or tgt.dead or not (tgt is p or self.is_friendly(p, tgt)):
                return p
            return tgt
        if t == "friendly_dead":
            return tgt
        return p

    def ability_error(self, p: Player, ab: dict, tgt: Unit | None, moving: bool) -> str | None:
        t = now()
        if p.dead:
            return "Ihr seid tot."
        if p.incapacitated:
            return "Ihr könnt gerade nichts tun."
        if p.silenced and ab["school"] != "physical":
            return "Ihr seid zum Schweigen gebracht."
        if p.cast:
            return "Ihr seid gerade beschäftigt."
        if not self.knows(p, ab):
            return "Diese Fähigkeit habt Ihr noch nicht erlernt."
        if ab["gcd"] and t < p.gcd_until:
            return "Diese Fähigkeit ist noch nicht bereit."
        if t < p.cooldowns.get(ab["id"], 0):
            return "Diese Fähigkeit ist noch nicht bereit."
        if p.mounted:
            self.dismount(p)
        form = p.form()
        if ab["form"] and form != ab["form"]:
            return "Dafür müsst Ihr in Bärengestalt sein."
        if form == "baer" and not ab["form"] and ab["id"] != "baerengestalt" and ab["school"] != "physical" and ab["target"] != "self":
            return "Das könnt Ihr in Bärengestalt nicht wirken."
        cost = self.ab_cost(p, ab)
        if p.power < cost:
            return f"Nicht genug {ERR_NAMES.get(p.power_type, 'Ressourcen')}."
        if self.ab_cast(p, ab) > 0 and moving:
            return "Ihr könnt nicht zaubern, während Ihr Euch bewegt."
        req = ab["req"]
        if req.get("shield") and not p.has_shield():
            return "Dafür braucht Ihr einen Schild."
        if req.get("two_hand") and not p.stats.get("two_hand"):
            return "Dafür braucht Ihr eine Zweihandwaffe."
        if req.get("weapon"):
            w = p.weapon()
            if w.get("sub") not in req["weapon"]:
                return "Dafür braucht Ihr einen Dolch." if "dolch" in req["weapon"] else "Falsche Waffe."
        if req.get("no_combat") and p.combat:
            return "Ihr befindet Euch im Kampf."
        if req.get("stealth") and not p.stealthed:
            return "Das geht nur aus der Tarnung."
        if req.get("combo") and (p.combo < req["combo"] or (tgt and p.combo_target != tgt.id)):
            return "Dafür braucht Ihr Kombopunkte."
        if req.get("after"):
            ok = any(t - p.last_reactive.get(k, -99) <= 5.0 for k in req["after"])
            if not ok:
                if req["after"] == ["parry"]:
                    return "Erst nach einer erfolgreichen Parade möglich."
                return "Erst nach einem Block, Ausweichen oder Parieren möglich."
        if ab["target"] == "enemy":
            if tgt is None:
                return "Ihr habt kein Ziel."
            if tgt.dead:
                return "Euer Ziel ist tot."
            if not self.is_enemy(p, tgt):
                return "Ungültiges Ziel."
            if req.get("not_boss") and isinstance(tgt, Mob) and (tgt.tpl.get("boss") or tgt.tpl.get("cc_immune")):
                return "Dieses Ziel ist immun."
            d = p.dist(tgt) - tgt.radius
            rng = ability_range(ab) + (p.radius + 1.0 if ab["range"] == "melee" else 0.5)
            if d > rng:
                return "Außer Reichweite."
            if ab["min_range"] and d < ab["min_range"] - 0.5:
                return "Ihr seid zu nah."
            no_face = any(e["t"] in ("charge", "taunt", "leap", "shadowstep") for e in ab["effects"])
            if not no_face and not p.facing(tgt):
                return "Ihr müsst Euer Ziel ansehen."
            if req.get("behind") and not p.behind(tgt):
                return "Ihr müsst hinter Eurem Ziel stehen."
            if req.get("execute") and tgt.hp > tgt.max_hp * req["execute"]:
                return "Das könnt Ihr erst bei geschwächten Zielen einsetzen."
            if abs(p.y - tgt.y) > 12 and ab["range"] == "melee":
                return "Außer Reichweite."
        elif ab["target"] == "friendly":
            if tgt and tgt is not p and p.dist(tgt) > ability_range(ab) + 1:
                return "Außer Reichweite."
        elif ab["target"] == "friendly_dead":
            if not tgt or not isinstance(tgt, Player) or not tgt.dead or self.is_enemy(p, tgt):
                return "Ungültiges Ziel."
            if p.dist(tgt) > ability_range(ab) + 1:
                return "Außer Reichweite."
        if any(e["t"] == "explode_pet" for e in ab["effects"]) and not self.pets_of(p):
            return "Ihr habt keinen Diener."
        return None

    # ================================================================== Wirken
    def use_ability(self, p: Player, ab_id: str, tid: int | None, ground: tuple | None = None):
        ab = ABILITIES.get(ab_id)
        if not ab:
            return
        # Bärengestalt: erneutes Wirken verwandelt zurück
        if ab_id == "baerengestalt" and p.form() == "baer":
            p.remove_aura("baerengestalt")
            self.after_aura_change(p)
            return
        if ab_id == "eisblock" and p.has_aura("eisblock"):
            p.remove_aura("eisblock")
            self.after_aura_change(p)
            return
        if tid is not None and ab["target"] == "enemy" and tid != p.target:
            p.target = tid
            p.mark("tg")
        tgt = self.resolve_target(p, ab, tid)
        moving = p.moving and now() - p.last_move_t < 0.25
        e = self.ability_error(p, ab, tgt, moving)
        if e:
            self.err(p, e)
            return
        t = now()
        if p.eating:
            self.stop_eating(p)
        if p.sitting:
            p.sitting = False
            p.mark("st")
        p.emote = None
        keep_stealth = ab["req"].get("stealth") or any(x["t"] == "stealth" for x in ab["effects"]) or ab_id in ("sprint",)
        if p.stealthed and not keep_stealth:
            self.break_stealth(p)
        if ab["gcd"]:
            p.gcd_until = t + self.gcd_for(p)
        gp = None
        if ab["ground"] or (ab["area"] and ab["area"]["center"] == "target"):
            if ground:
                gp = (float(ground[0]), float(ground[1]))
            elif tgt and tgt is not p:
                gp = (tgt.x, tgt.z)
        cast = self.ab_cast(p, ab)
        if ab["range"] == "melee" and tgt and ab["target"] == "enemy":
            p.auto_attack = True
        if cast > 0:
            p.cast = {"kind": "ability", "ab": ab_id, "name": ab["name"], "start": t, "end": t + cast,
                      "tid": tgt.id if tgt else None, "icon": ab["icon"], "school": ab["school"],
                      "channel": ab["channel"], "gp": [round(gp[0], 2), round(gp[1], 2)] if gp else None}
            if ab["channel"]:
                self.spend(p, ab)
                ticks = max(1, ab["ticks"])
                p.cast.update({"ticks_left": ticks, "interval": cast / ticks, "next_tick": t + cast / ticks})
            p.mark("cast")
            self.send_cd(p, ab_id)
            return
        self.spend(p, ab)
        self.execute(p, ab, tgt, gp)
        self.send_cd(p, ab_id)

    def spend(self, p: Player, ab: dict):
        cost = self.ab_cost(p, ab)
        if cost:
            p.power = max(0.0, p.power - cost)
            if p.power_type == "mana":
                p.last_mana_spend = now()
            p.mark("pw")
        cd = self.ab_cd(p, ab)
        if cd:
            p.cooldowns[ab["id"]] = now() + cd

    def send_cd(self, p: Player, ab_id: str):
        t = now()
        self.send(p, {"t": "cd", "ab": ab_id, "cd": round(max(0.0, p.cooldowns.get(ab_id, 0) - t), 2),
                      "gcd": round(max(0.0, p.gcd_until - t), 2)})

    def finish_player_cast(self, p: Player, c: dict):
        if c["kind"] == "ability":
            ab = ABILITIES[c["ab"]]
            tgt = self.find_unit(p.zone, c["tid"]) if c.get("tid") else None
            if ab["target"] == "enemy":
                if not tgt or tgt.dead:
                    self.err(p, "Euer Ziel ist tot.")
                    return
                if p.dist(tgt) - tgt.radius > ability_range(ab) + 4:
                    self.err(p, "Außer Reichweite.")
                    return
            cost = self.ab_cost(p, ab)
            if p.power < cost:
                self.err(p, f"Nicht genug {ERR_NAMES.get(p.power_type, 'Ressourcen')}.")
                return
            self.spend(p, ab)
            gp = tuple(c["gp"]) if c.get("gp") else None
            self.execute(p, ab, tgt, gp)
            if p.zone:
                p.zone.emit(p, {"s": p.id, "d": tgt.id if tgt else p.id, "a": 0, "k": "release", "ab": ab["id"], "sc": ab["school"]})
        elif c["kind"] == "gather":
            self.finish_gather(p, c)
        elif c["kind"] == "craft":
            self.finish_craft(p, c)
        elif c["kind"] == "mount":
            self.finish_mount(p, c)
        elif c["kind"] == "hearth":
            self.finish_hearth(p, c)
        elif c["kind"] == "use":
            self.finish_use(p, c)

    def channel_tick(self, p: Player, c: dict):
        ab = ABILITIES[c["ab"]]
        tgt = self.find_unit(p.zone, c["tid"]) if c.get("tid") else None
        if ab["target"] == "enemy" and (not tgt or tgt.dead) and not ab["area"]:
            p.cast = None
            p.mark("cast")
            return
        gp = tuple(c["gp"]) if c.get("gp") else None
        self.apply_effects(p, ab, tgt, gp, channel_tick=True)

    def interrupt(self, u: Unit, lock: float = 0.0, by: Unit | None = None) -> bool:
        if not u.cast or u.cast.get("uninterruptible"):
            return False
        name = u.cast["name"]
        u.cast = None
        u.mark("cast")
        if lock:
            u.cast_lock_until = now() + lock
        if u.zone:
            u.zone.emit(u, {"s": by.id if by else u.id, "d": u.id, "a": 0, "k": "interrupt", "ab": name, "sc": "physical"})
        if isinstance(u, Player):
            self.err(u, "Unterbrochen")
        elif by and isinstance(by, Player):
            self.progress_counter(by, "interrupts", 1)
        return True

    # ================================================================== Ausführen
    def execute(self, p: Player, ab: dict, tgt: Unit | None, gp: tuple | None):
        self.apply_effects(p, ab, tgt, gp)
        if ab["req"].get("stealth"):
            self.break_stealth(p)
        if ab["req"].get("after"):
            for k in ab["req"]["after"]:
                p.last_reactive.pop(k, None)

    def area_targets(self, p: Unit, ab: dict, tgt: Unit | None, gp: tuple | None, friendly=False) -> list[Unit]:
        area = ab["area"]
        zone = p.zone
        if area["center"] == "self":
            cx, cz = p.x, p.z
        elif gp:
            cx, cz = gp
        elif tgt:
            cx, cz = tgt.x, tgt.z
        else:
            cx, cz = p.x, p.z
        r = area["radius"]
        out = []
        for u in list(zone.entities.values()):
            if u.dead or u.hidden or isinstance(u, (Npc, GameObj, Trap, GroundEffect)):
                continue
            if friendly:
                if not (u is p or self.is_friendly(p, u)):
                    continue
            elif not self.is_enemy(p, u):
                continue
            d = math.hypot(u.x - cx, u.z - cz) - u.radius
            if d > r:
                continue
            if abs(u.y - p.y) > 10 and area["center"] == "self":
                continue
            if area["shape"] == "cone":
                ang = math.atan2(-(u.x - p.x), -(u.z - p.z))
                diff = (ang - p.r + math.pi) % (2 * math.pi) - math.pi
                if abs(diff) > math.radians(area["angle"]) / 2 and d > 1.0:
                    continue
            out.append(u)
        out.sort(key=lambda u: (u is not tgt, math.hypot(u.x - cx, u.z - cz)))
        return out[: area.get("max", 10)]

    def apply_effects(self, p: Player, ab: dict, tgt: Unit | None, gp: tuple | None, channel_tick=False):
        zone = p.zone
        lvl = p.level
        t = now()
        effects = ab["effects"]
        # Ziele bestimmen
        if ab["area"]:
            targets = self.area_targets(p, ab, tgt, gp)
            center = gp or ((tgt.x, tgt.z) if tgt and ab["area"]["center"] == "target" else (p.x, p.z))
            zone.emit_fx(center[0], center[1], {"k": "area", "id": p.id, "ab": ab["id"], "school": ab["school"],
                                                "x": round(center[0], 2), "z": round(center[1], 2), "r": ab["area"]["radius"],
                                                "shape": ab["area"]["shape"], "rot": round(p.r, 3)})
        else:
            targets = [tgt] if tgt else []
        # Bewegungs- und Sonder-Effekte zuerst (Ansturm, Sprung ...)
        for e in effects:
            et = e["t"]
            if et == "charge" and tgt:
                self.do_charge(p, tgt, e.get("stun", 0.0))
            elif et == "leap" and tgt:
                self.do_leap(p, tgt, ab)
            elif et == "blink":
                self.do_blink(p, e["dist"])
            elif et == "disengage":
                self.do_disengage(p, e["dist"])
            elif et == "shadowstep" and tgt:
                self.do_shadowstep(p, tgt)
            elif et == "stealth":
                self.enter_stealth(p)
            elif et == "drop_threat":
                self.drop_threat(p)
            elif et == "form":
                self.toggle_form(p, e["form"])
            elif et == "summon":
                self.summon_pets(p, e)
            elif et == "trap":
                self.place_trap(p, e["trap"])
            elif et == "ground_dot":
                cx, cz = gp or ((tgt.x, tgt.z) if tgt else (p.x, p.z))
                self.spawn_ground(p, e, cx, cz, "player")
            elif et == "explode_pet":
                self.explode_pet(p, e)
            elif et == "rez" and tgt:
                self.resurrect(p, tgt, e["pct"])
            elif et == "gain":
                self.gain_power(p, scaled(e["amount"], lvl))
        last_dealt = 0
        hits_any = False
        for u in targets:
            if u is None:
                continue
            landed_crit = False
            for e in effects:
                et = e["t"]
                if et == "weapon":
                    res = self.weapon_hit(p, u, ab, e)
                    if res:
                        hits_any = True
                        last_dealt = res[0]
                        landed_crit = landed_crit or res[1]
                elif et == "dmg":
                    res = self.spell_hit(p, u, ab, e)
                    if res:
                        hits_any = True
                        last_dealt = res[0]
                        landed_crit = landed_crit or res[1]
                elif et == "heal":
                    on = e.get("on", "target")
                    who = p if on == "self" else u
                    if on in ("self", "target"):
                        self.ability_heal(p, who, ab, e)
                elif et == "aura":
                    if e.get("on") == "target" and u is not p and not self.is_enemy(p, u) and ab["target"] == "enemy":
                        continue
                    if e.get("on", "target") == "target":
                        self.apply_aura(p, u, ab, e["aura"])
                elif et == "cc":
                    self.apply_cc(p, u, ab, e)
                elif et == "taunt":
                    self.do_taunt(p, u, e["dur"], ab)
                elif et == "interrupt":
                    if u.cast:
                        self.interrupt(u, e.get("lock", 4), p)
                elif et == "combo":
                    if not getattr(self, "_cp_done", False):
                        self.add_combo(p, u, e["n"])
                elif et == "leech" and last_dealt:
                    self.heal(p, p, int(last_dealt * e["pct"]), ab["name"])
                elif et == "threat" and isinstance(u, Mob):
                    self.add_threat(u, p, e["amount"] * (1 + p.mods.get("threat_pct", 0) / 100.0))
                elif et == "dispel":
                    self.dispel(p, u, e)
            if landed_crit and getattr(p, "set_procs", None):
                self.set_proc_crit(p, u)
        # Effekte, die nicht pro Ziel sind
        for e in effects:
            et = e["t"]
            if et == "aura" and e.get("on") in ("self", "party", "pet"):
                if e["on"] == "self":
                    self.apply_aura(p, p, ab, e["aura"])
                elif e["on"] == "party":
                    for m in self.party_members_near(p, 30):
                        self.apply_aura(p, m, ab, e["aura"])
                elif e["on"] == "pet":
                    for pet in self.pets_of(p):
                        self.apply_aura(p, pet, ab, e["aura"])
            elif et == "heal" and e.get("on") == "party":
                for m in self.party_members_near(p, 30):
                    self.ability_heal(p, m, ab, e)
            elif et == "heal" and e.get("on") == "self" and not targets:
                self.ability_heal(p, p, ab, e)
            elif et == "consume_aura":
                a = p.has_aura(e["aura"])
                if a and hits_any:
                    p.remove_aura(e["aura"])
            elif et == "consume_cp" or (et in ("dmg", "weapon", "cc") and (e.get("cp_finish") or e.get("per_cp"))):
                if hits_any or et == "consume_cp":
                    p.combo = 0
                    p.combo_target = None
                    self.send_combo(p)
        if ab["area"] and ab["id"] == "heldensprung":
            pass

    # ------------------------------------------------------------------ Schaden durch Spieler
    def _mult(self, p: Player, ab: dict, u: Unit, school: str, e: dict) -> float:
        m = 1.0
        m += (p.mods.get("dmg_pct", 0.0) + p.aura_pct("dmg_done") + p.mods.get("school_pct:" + school, 0.0)
              + p.mods.get("ab_pct:" + ab["id"], 0.0)) / 100.0
        if ab["area"]:
            m += p.mods.get("aoe_pct", 0.0) / 100.0
        if any(a.marked for a in u.auras):
            m += (p.mods.get("vs_marked_pct", 0.0)) / 100.0
            m += e.get("marked_bonus", 0.0)
        bv = e.get("bonus_vs") or {}
        if bv:
            if bv.get("rooted") and u.rooted:
                m += bv["rooted"]
            elif bv.get("slowed") and any(a.slow > 0 for a in u.auras):
                m += bv["slowed"]
            if bv.get("poisoned") and any(a.dispel == "poison" for a in u.auras):
                m += bv["poisoned"]
        if "range_bonus" in ab["tags"] and p.dist(u) > 25:
            m += 0.2
        if e.get("behind_bonus") and p.behind(u):
            m += e["behind_bonus"]
        if ab["id"] in ("iaido",):
            fl = p.has_aura("klingenfluss")
            if fl:
                m += 0.15 * fl.stacks
        if ab["id"] == "shogun_schnitt":
            fl = p.has_aura("klingenfluss")
            if fl:
                m += 0.25 * fl.stacks
        ss = p.has_aura("schattenschritt")
        if ss:
            p.remove_aura("schattenschritt")
        return m

    def weapon_hit(self, p: Player, u: Unit, ab: dict, e: dict):
        zone = p.zone
        lvl = p.level
        ranged = ab["range"] != "melee" and ab["range"] not in (0, "0") and float(ab["range"]) > 6
        front = u.facing(p)
        out = C.melee_outcome(p, u, front, e.get("crit_bonus", 0) + p.mods.get("ab_crit:" + ab["id"], 0), ranged)
        if out in ("miss", "dodge", "parry"):
            self.miss_event(p, u, out, ab["name"])
            if isinstance(u, Mob):
                self.add_threat(u, p, e.get("threat", 0) + 1)
            if isinstance(u, Player) and out in ("dodge", "parry"):
                self.on_reactive(u, out)
            return None
        extra = scaled(e["bonus"], lvl)
        if e.get("per_cp") and p.combo:
            extra += scaled(e["per_cp"], lvl) * p.combo
        if e.get("rage_scale"):
            extra += e["rage_scale"] * p.power
            p.power = 0
            p.mark("pw")
        dmg = C.player_melee_damage(p, e["mult"], extra)
        dmg *= self._mult(p, ab, u, "physical", e)
        kind = "hit"
        crit = False
        if out == "crit":
            dmg *= 2.0 * (1 + p.mods.get("crit_dmg_pct", 0) / 100.0)
            kind = "crit"
            crit = True
        elif out == "block":
            dmg = max(0, dmg - (u.stats.get("block_value", 5) if isinstance(u, Player) else 0))
            kind = "block"
            if isinstance(u, Player):
                self.on_reactive(u, "block")
        threat_mult = 1.0 + p.mods.get("threat_pct", 0) / 100.0 + p.aura_pct("threat") / 100.0
        if p.form() == "baer":
            threat_mult += 0.3
        proj = ab.get("proj")
        if proj and ranged:
            dist = p.dist(u)
            zone.emit_fx(p.x, p.z, {"k": "proj", "from": p.id, "to": u.id, "sp": float(proj), "school": "physical", "ab": ab["id"]})
            uid = u.id

            def land(dmg=dmg, kind=kind):
                target = zone.entities.get(uid)
                if target and not target.dead:
                    self.damage(p, target, dmg, "physical", ab["name"], kind, threat_mult=threat_mult, extra_threat=e.get("threat", 0),
                                armor_pen=e.get("ignore_armor", 0) + p.mods.get("armor_pen", 0) / 100.0)
                    self.weapon_proc(p, target)
            zone.schedule(max(0.05, dist / float(proj)), land)
            return (int(dmg), crit)
        zone.emit_fx(u.x, u.z, {"k": "strike", "id": p.id, "to": u.id, "ab": ab["id"]})
        dealt = self.damage(p, u, dmg, "physical", ab["name"], kind, threat_mult=threat_mult, extra_threat=e.get("threat", 0),
                            armor_pen=e.get("ignore_armor", 0) + p.mods.get("armor_pen", 0) / 100.0)
        if crit and p.mods.get("crit_resource"):
            self.gain_power(p, p.mods["crit_resource"])
        self.weapon_proc(p, u)
        return (dealt, crit)

    def spell_hit(self, p: Player, u: Unit, ab: dict, e: dict):
        zone = p.zone
        lvl = p.level
        school = e["school"]
        lo, hi = scaled_range(e["base"], lvl)
        base = random.randint(lo, max(lo, hi))
        stat = p.stats.get(e.get("stat", "sp"), 0)
        base += e.get("coef", 0) * stat
        if e.get("per_cp") and p.combo:
            base += scaled(e["per_cp"], lvl) * p.combo + p.stats.get("ap", 0) * 0.03 * p.combo
        base *= self._mult(p, ab, u, school, e)
        if school == "physical":
            out = C.melee_outcome(p, u, u.facing(p), e.get("crit_bonus", 0) + p.mods.get("ab_crit:" + ab["id"], 0))
            if out in ("parry", "block"):
                out = "hit"
            crit_mult = 2.0
        else:
            out = C.spell_outcome(p, u, e.get("crit_bonus", 0) + p.mods.get("ab_crit:" + ab["id"], 0))
            crit_mult = 1.5
        if out in ("miss", "dodge"):
            self.miss_event(p, u, "resist" if school != "physical" else out, ab["name"], school)
            if isinstance(u, Mob):
                self.add_threat(u, p, 1)
            return None
        crit = out == "crit"
        if crit:
            base *= crit_mult * (1 + p.mods.get("crit_dmg_pct", 0) / 100.0)
        threat_mult = e.get("threat", 1.0) * (1.0 + p.mods.get("threat_pct", 0) / 100.0)
        proj = ab.get("proj")
        if proj and not ab["area"]:
            uid = u.id
            zone.emit_fx(p.x, p.z, {"k": "proj", "from": p.id, "to": uid, "sp": float(proj), "school": school, "ab": ab["id"]})

            def land(dmg=base, crit=crit):
                target = zone.entities.get(uid)
                if target and not target.dead:
                    self.damage(p, target, dmg, school, ab["name"], "crit" if crit else "hit", threat_mult=threat_mult)
            zone.schedule(max(0.05, p.dist(u) / float(proj)), land)
            return (int(base), crit)
        if not ab["area"]:
            zone.emit_fx(u.x, u.z, {"k": "impact", "id": u.id, "school": school, "ab": ab["id"]})
        dealt = self.damage(p, u, base, school, ab["name"], "crit" if crit else "hit", threat_mult=threat_mult)
        return (dealt, crit)

    def ability_heal(self, p: Player, u: Unit, ab: dict, e: dict):
        lvl = p.level
        lo, hi = scaled_range(e["base"], lvl)
        amount = random.randint(lo, max(lo, hi)) + e.get("coef", 0) * p.stats.get("heal", 0)
        if e.get("pct_max"):
            amount += u.max_hp * e["pct_max"]
        amount *= 1.0 + (p.mods.get("heal_pct", 0) + p.aura_pct("heal_done") + p.mods.get("ab_pct:" + ab["id"], 0)) / 100.0
        out = C.spell_outcome(p, u, 0, heal=True)
        crit = out == "crit"
        if crit:
            amount *= 1.5
        self.heal(p, u, int(amount), ab["name"], crit)

    # ------------------------------------------------------------------ Auren und Kontrolle
    def apply_aura(self, src: Unit, u: Unit, ab: dict | None, d: dict):
        t = now()
        if u.dead:
            return
        if d.get("debuff") and u.immune:
            return
        lvl = src.level
        dur = d.get("dur", 10)
        if isinstance(src, Player):
            dur += src.mods.get("dur:" + d["id"], 0.0)
        a = Aura(d, src.id, t, lvl, dur)
        if ab:
            a.icon = a.icon or ab["icon"]
            a.ability = ab["id"]
            a.school = ab["school"]
        if a.dot:
            per = scaled(a.dot["base"], lvl) + a.dot.get("coef", 0) * src.stats.get(a.dot.get("stat", "sp"), 0)
            if isinstance(src, Player):
                per *= 1.0 + (src.mods.get("dot_pct", 0) + src.mods.get("dmg_pct", 0) + src.aura_pct("dmg_done")
                              + src.mods.get("school_pct:" + a.dot.get("school", "physical"), 0)) / 100.0
            a.extra["tick"] = max(1.0, per)
        if a.hot:
            per = scaled(a.hot["base"], lvl) + a.hot.get("coef", 0) * src.stats.get("heal", 0)
            if isinstance(src, Player):
                per *= 1.0 + (src.mods.get("heal_pct", 0) + src.aura_pct("heal_done") + (src.mods.get("ab_pct:" + ab["id"], 0) if ab else 0)) / 100.0
            a.extra["tick"] = max(1.0, per)
        if d.get("absorb"):
            a.absorb = scaled(d["absorb"], lvl) + d.get("absorb_coef", 0) * src.stats.get("sp", 0)
            if isinstance(src, Player) and ab:
                a.absorb *= 1.0 + src.mods.get("ab_pct:" + ab["id"], 0) / 100.0
        if d.get("chill_attackers"):
            a.chill_attackers = d["chill_attackers"]
        u.add_aura(a)
        if u.zone and not d.get("debuff"):
            u.zone.emit_fx(u.x, u.z, {"k": "buff", "id": u.id, "school": ab["school"] if ab else "holy"})
        if isinstance(u, Mob) and d.get("debuff") and isinstance(src, Player):
            self.add_threat(u, src, 5)
        self.after_aura_change(u)

    def after_aura_change(self, u: Unit):
        if isinstance(u, Player):
            u.recalc_cb(u) if u.recalc_cb else None
            self.send_stats(u)

    def apply_cc(self, src: Unit, u: Unit, ab: dict | None, e: dict):
        if u.dead or u.immune:
            return
        kind = e["kind"]
        dur = e["dur"]
        if e.get("per_cp") and isinstance(src, Player):
            dur += e["per_cp"] * src.combo
        if isinstance(u, Mob) and (u.tpl.get("boss") or u.tpl.get("cc_immune")) and kind in ("stun", "fear", "poly", "root", "sleep"):
            if kind in ("root",) and not u.tpl.get("boss"):
                pass
            else:
                self.miss_event(src, u, "immune", ab["name"] if ab else "", "physical")
                return
        if isinstance(u, Player) and isinstance(src, Player):
            dur *= 0.6   # PvP: kürzere Kontrolle
        d = {"id": (ab["id"] if ab else "cc") + "_" + kind, "name": (ab["name"] if ab else "Kontrolle"), "dur": dur,
             "debuff": True, "icon": ab["icon"] if ab else None}
        if kind == "stun":
            d["stun"] = True
        elif kind == "root":
            d["root"] = True
        elif kind == "fear":
            d["fear"] = True
        elif kind == "poly":
            d["poly"] = True
        elif kind == "sleep":
            d["sleep"] = True
        elif kind == "silence":
            d["silence"] = True
        elif kind == "slow":
            d["slow"] = e.get("slow", 0.5)
        if "break_dmg" in e:
            d["break_dmg"] = e["break_dmg"]
        a = Aura(d, src.id, now(), src.level, dur)
        u.add_aura(a)
        if kind in ("stun", "fear", "poly", "sleep") and u.cast:
            self.interrupt(u, 0, src)
        if isinstance(u, Mob):
            if kind == "fear":
                ang = random.uniform(0, math.tau)
                u.fear_dir = (math.cos(ang), math.sin(ang))
            if kind == "poly":
                u.look["poly"] = True
                u.mark("look")
            self.add_threat(u, src, 3) if isinstance(src, Player) else None
        if isinstance(u, Player):
            u.moving = False
            self.after_aura_change(u)

    def dispel(self, p: Player, u: Unit, e: dict):
        n = e.get("n", 1)
        removed = 0
        friendly = u is p or self.is_friendly(p, u)
        for a in list(u.auras):
            if removed >= n:
                break
            if friendly and a.debuff and a.dispel in e["kinds"]:
                u.auras.remove(a)
                removed += 1
            elif not friendly and not a.debuff and a.removable and "magic" in e["kinds"]:
                u.auras.remove(a)
                removed += 1
        if removed:
            u.mark("au")
            self.after_aura_change(u)

    def do_taunt(self, p: Player, u: Unit, dur: float, ab: dict):
        if not isinstance(u, Mob):
            return
        top = max(u.threat.values(), default=0.0)
        u.threat[p.id] = max(u.threat.get(p.id, 0.0), top + 1)
        self.add_threat(u, p, 1)
        u.taunt_by = p.id
        u.taunt_until = now() + dur
        u.add_aura(Aura({"id": "spott", "name": ab["name"], "debuff": True, "taunt": True, "icon": ab["icon"]}, p.id, now(), p.level, dur))
        u.zone.emit_fx(u.x, u.z, {"k": "taunt", "id": u.id, "by": p.id})

    def add_combo(self, p: Player, u: Unit, n: int):
        if p.combo_target != u.id:
            p.combo = 0
            p.combo_target = u.id
        p.combo = min(5, p.combo + n)
        self.send_combo(p)

    def send_combo(self, p: Player):
        self.send(p, {"t": "combo", "n": p.combo, "tg": p.combo_target})

    def gain_power(self, p: Unit, amount: float):
        if not isinstance(p, Player) or amount <= 0:
            return
        if p.power_type in ("rage", "resolve", "focus"):
            amount *= 1.0 + p.mods.get("resource_gain_pct", 0) / 100.0
        p.power = min(p.max_power, p.power + amount)
        p.mark("pw")

    def on_reactive(self, p: Player, kind: str):
        """Block, Ausweichen, Parieren: Fenster für Konterfähigkeiten und Ressourcengewinn."""
        p.last_reactive[kind] = now()
        if p.power_type == "resolve":
            self.gain_power(p, 5)
        if p.power_type == "focus" and kind == "parry":
            self.gain_power(p, 20)
        sk = p.has_aura("spiegelklinge")
        if sk:
            pass
        self.send(p, {"t": "reactive", "k": kind})

    # ------------------------------------------------------------------ Bewegungsfähigkeiten
    def do_charge(self, p: Player, tgt: Unit, stun: float):
        zone = p.zone
        dx, dz = tgt.x - p.x, tgt.z - p.z
        d = math.hypot(dx, dz) or 1
        stop = tgt.radius + p.radius + 0.8
        nx, nz = tgt.x - dx / d * stop, tgt.z - dz / d * stop
        r = math.atan2(-dx, -dz)
        zone.emit_fx(p.x, p.z, {"k": "charge", "id": p.id, "x": round(nx, 2), "z": round(nz, 2)})
        self.teleport(p, nx, nz, r, kind="charge")
        if stun > 0 and not tgt.dead:
            self.apply_cc(p, tgt, {"id": "ansturm", "name": "Betäubt", "icon": "charging-bull"}, {"kind": "stun", "dur": stun})
        if isinstance(tgt, Mob):
            self.add_threat(tgt, p, 5)
        p.auto_attack = True
        p.swing_ready = min(p.swing_ready, now() + 0.3)

    def do_leap(self, p: Player, tgt: Unit, ab: dict):
        zone = p.zone
        dx, dz = tgt.x - p.x, tgt.z - p.z
        d = math.hypot(dx, dz) or 1
        stop = tgt.radius + p.radius + 0.6
        nx, nz = tgt.x - dx / d * stop, tgt.z - dz / d * stop
        zone.emit_fx(p.x, p.z, {"k": "leap", "id": p.id, "x": round(nx, 2), "z": round(nz, 2)})
        self.teleport(p, nx, nz, math.atan2(-dx, -dz), kind="leap")
        lvl = p.level

        def land():
            if p.dead or p.zone is not zone:
                return
            zone.emit_fx(p.x, p.z, {"k": "nova", "id": p.id, "r": 5, "school": "physical", "ab": ab["id"]})
            for u in self.area_targets(p, {"area": {"shape": "circle", "radius": 5, "center": "self", "max": 8}}, None, None):
                dmg = (6 + 2 * lvl + random.randint(0, 2 + lvl // 2)) + p.stats.get("ap", 0) * 0.1
                self.damage(p, u, dmg, "physical", ab["name"], "hit")
        zone.schedule(0.45, land)

    def do_blink(self, p: Player, dist: float):
        zone = p.zone
        fx, fz = -math.sin(p.r), -math.cos(p.r)
        nx, nz = p.x, p.z
        for _ in range(int(dist / 0.5)):
            cx, cz = nx + fx * 0.5, nz + fz * 0.5
            if not zone.walkable(cx, cz):
                break
            nx, nz = cx, cz
        for a in list(p.auras):
            if a.stun or a.root:
                p.auras.remove(a)
        p.mark("au")
        zone.emit_fx(p.x, p.z, {"k": "blink", "id": p.id, "x": round(p.x, 2), "z": round(p.z, 2), "x2": round(nx, 2), "z2": round(nz, 2)})
        self.teleport(p, nx, nz, p.r, kind="blink")

    def do_disengage(self, p: Player, dist: float):
        zone = p.zone
        fx, fz = math.sin(p.r), math.cos(p.r)
        nx, nz = p.x, p.z
        for _ in range(int(dist / 0.5)):
            cx, cz = nx + fx * 0.5, nz + fz * 0.5
            if not zone.walkable(cx, cz):
                break
            nx, nz = cx, cz
        zone.emit_fx(p.x, p.z, {"k": "leap", "id": p.id, "x": round(nx, 2), "z": round(nz, 2)})
        self.teleport(p, nx, nz, p.r, kind="leap")

    def do_shadowstep(self, p: Player, tgt: Unit):
        bx = tgt.x + math.sin(tgt.r) * (tgt.radius + 0.9)
        bz = tgt.z + math.cos(tgt.r) * (tgt.radius + 0.9)
        p.zone.emit_fx(p.x, p.z, {"k": "blink", "id": p.id, "x": round(p.x, 2), "z": round(p.z, 2), "x2": round(bx, 2), "z2": round(bz, 2)})
        self.teleport(p, bx, bz, tgt.r, kind="blink")

    # ------------------------------------------------------------------ Tarnung, Gestalt, Bedrohung
    def enter_stealth(self, p: Player):
        p.add_aura(Aura({"id": "tarnung", "name": "Tarnung", "stealth": True, "pct": {"speed": -30}, "icon": "cloak-dagger"},
                        p.id, now(), p.level, 3600))
        p.auto_attack = False
        if p.zone:
            for u in p.zone.entities.values():
                if isinstance(u, Mob) and u.target == p.id and u.state != "combat":
                    u.target = None
        self.after_aura_change(p)

    def break_stealth(self, p: Player):
        if p.remove_aura("tarnung"):
            p.cooldowns["tarnung"] = max(p.cooldowns.get("tarnung", 0), now() + 2.0)
            self.after_aura_change(p)

    def drop_threat(self, p: Player):
        if not p.zone:
            return
        for u in p.zone.entities.values():
            if isinstance(u, Mob) and p.id in u.threat:
                del u.threat[p.id]
                if u.target == p.id:
                    u.target = None
                if u.taunt_by == p.id:
                    u.taunt_by = None

    def toggle_form(self, p: Player, form: str):
        if p.form() == form:
            p.remove_aura("baerengestalt")
        else:
            p.add_aura(Aura({"id": "baerengestalt", "name": "Bärengestalt", "form": form, "icon": "bear-head"}, p.id, now(), p.level, 36000))
            p.power = p.power
        p.look["form"] = p.form()
        p.mark("look")
        self.after_aura_change(p)
        if p.zone:
            p.zone.emit_fx(p.x, p.z, {"k": "shapeshift", "id": p.id})

    # ------------------------------------------------------------------ Begleiter
    def pets_of(self, p: Player) -> list[Pet]:
        out = []
        if not p.zone:
            return out
        for pid in list(p.pets):
            u = p.zone.entities.get(pid)
            if isinstance(u, Pet) and not u.dead:
                out.append(u)
            else:
                p.pets.remove(pid)
        return out

    def summon_pets(self, p: Player, e: dict):
        tpl = COMMON.get(e["pet"])
        if not tpl:
            return
        zone = p.zone
        t = now()
        count = e.get("count", 1)
        dur = e.get("dur", 0.0)
        existing = [u for u in self.pets_of(p) if not u.expires]
        if not dur:
            max_pets = e.get("max", 1)
            if p.class_id == "totenbeschwoerer":
                max_pets = 1 + (1 if p.level >= 20 else 0) + int(p.mods.get("max_pets", 0))
                if e["pet"] == "knochengolem":
                    max_pets = max_pets
            same = [u for u in existing if u.tpl["id"] == e["pet"]]
            if e["pet"] in ("begleitwolf", "naturgeist", "knochengolem") and same:
                for u in same:
                    zone.remove(u)
                    p.pets.remove(u.id) if u.id in p.pets else None
            while len([u for u in self.pets_of(p) if not u.expires]) >= max_pets:
                old = [u for u in self.pets_of(p) if not u.expires][0]
                zone.remove(old)
                if old.id in p.pets:
                    p.pets.remove(old.id)
        for i in range(count):
            a = p.r + math.pi + (i - (count - 1) / 2) * 0.8
            x, z = zone.walkable_clamp(p.x + math.sin(a) * 2.0, p.z + math.cos(a) * 2.0)
            pet = Pet(tpl, p, x, z, t + dur if dur else 0.0)
            mult = 1.0 + p.mods.get("pet_pct", 0) / 100.0
            pet.pet_mult = mult
            pet.max_hp = int(pet.max_hp * mult)
            pet.hp = pet.max_hp
            pet.dmg = (int(pet.dmg[0] * mult), int(pet.dmg[1] * mult))
            pet.y = zone.height(x, z)
            zone.add(pet)
            p.pets.append(pet.id)
            zone.emit_fx(x, z, {"k": "summon", "x": round(x, 2), "z": round(z, 2), "school": "shadow" if tpl.get("undead") else "nature"})

    def explode_pet(self, p: Player, e: dict):
        pets = self.pets_of(p)
        if not pets:
            return
        pet = pets[-1]
        zone = p.zone
        lo, hi = scaled_range(e["base"], p.level)
        zone.emit_fx(pet.x, pet.z, {"k": "nova", "id": pet.id, "r": e["radius"], "school": "shadow", "ab": "leichenexplosion"})
        for u in list(zone.entities.values()):
            if u.dead or not self.is_enemy(p, u) or math.hypot(u.x - pet.x, u.z - pet.z) > e["radius"] + u.radius:
                continue
            dmg = (random.randint(lo, hi) + e["coef"] * p.stats.get("sp", 0)) * (1 + (p.mods.get("ab_pct:leichenexplosion", 0) + p.mods.get("dmg_pct", 0)) / 100.0)
            self.damage(p, u, dmg, "shadow", "Leichenexplosion", "hit")
        zone.remove(pet)
        if pet.id in p.pets:
            p.pets.remove(pet.id)

    # ------------------------------------------------------------------ Fallen & Bodeneffekte
    def place_trap(self, p: Player, spec: dict):
        zone = p.zone
        for u in list(zone.entities.values()):
            if isinstance(u, Trap) and u.owner_id == p.id and u.spec["id"] == spec["id"]:
                zone.remove(u)
        tr = Trap(p, spec, p.x, p.z, now())
        tr.y = zone.height(p.x, p.z)
        zone.add(tr)

    def trigger_trap(self, tr: Trap, victim: Unit):
        zone = tr.zone
        owner = self.players.get(tr.owner_id)
        zone.remove(tr)
        if not owner:
            return
        spec = tr.spec
        zone.emit_fx(tr.x, tr.z, {"k": "nova", "id": tr.id, "r": spec.get("area", 3), "school": {"frost": "frost", "fire": "fire"}.get(spec.get("fx"), "nature"), "ab": spec["id"]})
        fake_ab = {"id": spec["id"], "name": spec["name"], "icon": "wolf-trap", "school": spec.get("fx", "frost"), "area": None,
                   "tags": [], "range": 30}
        if spec.get("area"):
            targets = [u for u in zone.entities.values() if not u.dead and self.is_enemy(owner, u)
                       and math.hypot(u.x - tr.x, u.z - tr.z) <= spec["area"] + u.radius]
        else:
            targets = [victim]
        for u in targets:
            for e in spec.get("on_trigger", []):
                if e["t"] == "cc":
                    self.apply_cc(owner, u, fake_ab, e)
                elif e["t"] == "dmg":
                    self.spell_hit(owner, u, fake_ab, e)
                elif e["t"] == "aura":
                    self.apply_aura(owner, u, fake_ab, e["aura"])
            if isinstance(u, Mob):
                self.add_threat(u, owner, 10)

    def spawn_ground(self, src: Unit, spec: dict, x: float, z: float, side: str):
        ge = GroundEffect(src, spec, x, z, now(), side)
        ge.y = src.zone.height(x, z)
        src.zone.add(ge)
        return ge

    def ground_tick(self, ge: GroundEffect, t: float):
        zone = ge.zone
        if ge.expires and t >= ge.expires:
            zone.remove(ge)
            return
        if t < ge.next_tick:
            return
        ge.next_tick = t + ge.spec.get("interval", 1.0)
        src = zone.entities.get(ge.src_id) or self.players.get(ge.src_id)
        for u in list(zone.entities.values()):
            if u.dead or isinstance(u, (Npc, GameObj, Trap, GroundEffect)):
                continue
            if math.hypot(u.x - ge.x, u.z - ge.z) > ge.radius + u.radius * 0.5:
                continue
            if ge.side == "player":
                if not src or not self.is_enemy(src, u):
                    continue
                fake_ab = {"id": ge.spec.get("ab", "ground"), "name": ge.spec.get("name", "Seuchenwolke"), "icon": "poison-gas",
                           "school": "shadow", "area": None, "tags": [], "range": 30}
                for e in ge.spec.get("effects", []):
                    if e["t"] == "dmg" and isinstance(src, Player):
                        self.spell_hit(src, u, fake_ab, e)
            else:
                if not isinstance(u, (Player, Pet)):
                    continue
                dmg = ge.spec.get("flat", 50) * random.uniform(0.9, 1.1)
                self.damage(src or u, u, dmg, ge.spec.get("school", "fire"), ge.spec.get("name", "Feuer"), "hit", periodic=True)

    # ------------------------------------------------------------------ Wiederbelebung
    def resurrect(self, p: Player, tgt: Unit, pct: float):
        if not isinstance(tgt, Player) or not tgt.dead:
            return
        tgt.dead = False
        tgt.hp = max(1, int(tgt.max_hp * pct))
        if tgt.power_type == "mana":
            tgt.power = int(tgt.max_power * pct)
        tgt.mark("hp", "pw", "st")
        tgt.zone.emit_fx(tgt.x, tgt.z, {"k": "rez", "id": tgt.id})
        self.send(tgt, {"t": "revived"})
        self.sys(tgt, f"{p.name} hat Euch wiederbelebt.")

    # ------------------------------------------------------------------ Procs
    def weapon_proc(self, p: Player, u: Unit):
        if u.dead:
            return
        w = p.weapon()
        procs = []
        if w.get("proc"):
            procs.append(w["proc"])
        for a in p.auras:
            if a.proc:
                procs.append(a.proc)
        for pr in procs:
            if random.random() < pr.get("chance", 0.1):
                d = pr.get("dmg")
                if d:
                    lo, hi = scaled_range(d["base"], p.level)
                    self.damage(p, u, random.randint(lo, max(lo, hi)), d["school"], pr.get("name", "Waffeneffekt"), "hit")
                    u.zone.emit_fx(u.x, u.z, {"k": "impact", "id": u.id, "school": d["school"], "ab": "proc"})

    def set_proc_crit(self, p: Player, u: Unit):
        t = now()
        for pr in p.set_procs:
            if pr.get("on") != "crit":
                continue
            if t < p.misc.get("_set_icd", 0):
                continue
            p.misc["_set_icd"] = t + pr.get("icd", 4.0)
            aoe = pr.get("aoe")
            if not aoe:
                continue
            zone = p.zone
            zone.emit_fx(u.x, u.z, {"k": "nova", "id": u.id, "r": aoe["radius"], "school": aoe["school"], "ab": "setproc"})
            lo, hi = scaled_range(aoe["base"], p.level)
            for v in list(zone.entities.values()):
                if v.dead or not self.is_enemy(p, v) or math.hypot(v.x - u.x, v.z - u.z) > aoe["radius"] + v.radius:
                    continue
                self.damage(p, v, random.randint(lo, max(lo, hi)), aoe["school"], "Aschenexplosion", "hit")

    def party_members_near(self, p: Player, radius: float) -> list[Player]:
        if not p.party:
            return [p]
        out = []
        for mid in p.party.members:
            m = self.players.get(mid)
            if m and m.zone is p.zone and not m.dead and m.dist(p) <= radius:
                out.append(m)
        return out or [p]
