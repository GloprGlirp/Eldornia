"""Gegner-KI (Bedrohung, Verfolgen, Fliehen, Ausweichen), Bossphasen und Begleiter-KI.

Bossmechaniken (GDD 4): mehrere Kampfphasen, erkennbare Angriffsmuster mit Bodenmarkierungen,
unterbrechbare Zauber, Beschwörungen, Raserei und Arenazerstörung.
"""
from __future__ import annotations

import math
import random

from ..content.mobs import mob_xp
from . import combat as C
from .entities import RUN_SPEED, Aura, Mob, Pet, Player, Unit, now


class AIMixin:
    # ================================================================== Bedrohung
    def tap_set(self, p: Player) -> set[int]:
        if p.party:
            return set(p.party.members)
        return {p.id}

    def add_threat(self, mob: Mob, unit: Unit, amount: float):
        if mob.dead or mob.state == "evade" or unit.dead or isinstance(mob, Pet):
            return
        if not isinstance(unit, (Player, Pet)):
            return
        if mob.look.get("critter") and amount <= 0:
            return
        owner = self.owner_player(unit)
        if owner is None:
            return
        mob.threat[unit.id] = mob.threat.get(unit.id, 0.0) + max(0.0, amount)
        if mob.tap is None:
            mob.tap = self.tap_set(owner)
        if mob.state in ("idle", "return"):
            self.engage(mob, unit)

    def engage(self, mob: Mob, unit: Unit):
        t = now()
        mob.state = "combat"
        mob.combat = True
        mob.engage_t = t
        mob.wander_to = None
        mob.swing_ready = max(mob.swing_ready, t + 0.4)
        for ab in self.mob_abilities(mob):
            mob.ab_next[ab["id"]] = t + ab.get("first", ab.get("cd", 10))
        if mob.tpl.get("ranged"):
            mob.ab_next["ranged"] = t + 0.3
        mob.mark("st")
        if mob.tpl.get("aggro_yell"):
            self.yell(mob, mob.tpl["aggro_yell"])
        elif mob.tpl.get("aggro_say") and random.random() < 0.5:
            self.mob_say(mob, random.choice(mob.tpl["aggro_say"]))
        social = mob.tpl.get("social", 0)
        if social:
            for other in mob.zone.mobs_near(mob.x, mob.z, social):
                if other is not mob and other.state == "idle" and other.tpl.get("family") == mob.tpl.get("family") \
                        and other.hostile and not other.look.get("critter") and not isinstance(other, Pet):
                    other.threat[unit.id] = 1.0
                    if other.tap is None:
                        other.tap = mob.tap
                    self.engage(other, unit)
        if mob.tpl.get("boss") and mob.zone.is_instance:
            mob.zone.boss_engaged(mob)

    def mob_abilities(self, m: Mob) -> list[dict]:
        tpl = m.tpl
        phases = tpl.get("phases")
        if phases:
            ph = phases[min(m.phase, len(phases) - 1)]
            return ph.get("abilities", [])
        return tpl.get("abilities", [])

    def yell(self, unit: Unit, text: str):
        for p in unit.zone.players.values():
            if p.dist(unit) < 150:
                self.send(p, {"t": "chat", "ch": "yell", "from": unit.name, "fid": unit.id, "text": text})

    def mob_say(self, unit: Unit, text: str, radius: float = 40):
        for p in unit.zone.players.values():
            if p.dist(unit) < radius:
                self.send(p, {"t": "chat", "ch": "npc", "from": unit.name, "fid": unit.id, "text": text})

    # ================================================================== Tick
    def mob_tick(self, m: Mob, t: float, dt: float):
        if m.hidden:
            if m.respawn_at and t >= m.respawn_at:
                self.respawn(m)
            return
        if m.dead:
            if t >= m.corpse_until:
                if m.respawn_at:
                    m.hidden = True
                else:
                    m.zone.remove(m)
            return
        self.update_auras(m, t)
        if m.dead:
            return
        if isinstance(m, Pet):
            self.pet_tick(m, t, dt)
            return
        if m.look.get("dummy"):
            if m.hp < m.max_hp and t - m.last_hit_t > 6:
                m.hp = m.max_hp
                m.mark("hp")
            if m.threat and t - m.last_hit_t > 6:
                m.threat.clear()
                m.state = "idle"
                m.combat = False
                m.tap = None
                m.mark("st")
            return
        if m.look.get("poly") and not any(a.poly for a in m.auras):
            m.look.pop("poly", None)
            m.mark("look")
        if m.cast and t >= m.cast["end"]:
            self.finish_mob_cast(m)
        if m.state == "idle":
            self.mob_idle(m, t, dt)
        elif m.state == "combat":
            self.mob_combat(m, t, dt)
        elif m.state == "evade":
            self.mob_evade(m, t, dt)
        elif m.state == "flee":
            self.mob_flee(m, t, dt)

    def respawn(self, m: Mob):
        m.hidden = False
        m.dead = False
        m.state = "idle"
        m.loot = {}
        m.tap = None
        m.threat.clear()
        m.auras = []
        m.ab_used.clear()
        m.fled = False
        m.phase = 0
        m.level = random.randint(*m.lvl_range)
        hx, hz, hr = m.home
        if m.spawn_r:
            hx, hz = m.zone._random_point(hx, hz, m.spawn_r)
        m.x, m.z, m.r = hx, hz, hr
        m.y = m.zone.height(hx, hz)
        m.reset_stats()
        m.mark("p", "st", "au", "lvl", "hp")

    def move_towards(self, u: Unit, tx: float, tz: float, speed: float, dt: float, stop: float = 0.0) -> bool:
        zone = u.zone
        if zone.nav:
            wx, wz = zone.nav.next_waypoint(u.x, u.z, tx, tz)
            final = (wx, wz) == (tx, tz)
        else:
            wx, wz = tx, tz
            final = True
        dx, dz = wx - u.x, wz - u.z
        d = math.hypot(dx, dz)
        if final and d <= stop:
            return True
        if d < 0.01:
            return True
        step = min(speed * dt, d - (stop if final else 0.0))
        if step <= 0:
            return True
        nx, nz = u.x + dx / d * step, u.z + dz / d * step
        nx, nz = zone.walkable_clamp(nx, nz)
        u.set_pos(nx, zone.height(nx, nz), nz, math.atan2(-dx, -dz))
        return False

    def face(self, u: Unit, o: Unit):
        r = u.angle_to(o)
        if abs((r - u.r + math.pi) % (2 * math.pi) - math.pi) > 0.05:
            u.r = r
            u.mark("p")

    def aggro_radius(self, m: Mob, p: Player) -> float:
        if m.tpl.get("aggro_radius"):
            r = m.tpl["aggro_radius"]
        else:
            base = 12.0 if m.tpl.get("elite") else 10.0
            r = max(3.5, min(22.0, base - (p.level - m.level) * 1.2))
        if p.stealthed:
            r = min(r, 2.5)
        return r

    def mob_idle(self, m: Mob, t: float, dt: float):
        tpl = m.tpl
        if m.incapacitated:
            return
        if tpl.get("aggro") and m.hostile:
            for p in m.zone.players.values():
                if p.dead or not p.ready or p.gm and p.misc.get("gm_invisible"):
                    continue
                if abs(p.y - m.y) < 8 and p.dist(m) < self.aggro_radius(m, p):
                    self.add_threat(m, p, 1.0)
                    return
        if tpl.get("patrol") and not m.rooted:
            pts = tpl["patrol"]
            i = getattr(m, "patrol_i", 0)
            tx, tz = pts[i % len(pts)]
            if self.move_towards(m, tx, tz, 2.4 * m.speed_mult(), dt, 0.4):
                m.patrol_i = (i + 1) % len(pts)
            return
        wander = tpl.get("wander", 0)
        if wander and not m.rooted:
            if m.wander_to:
                if self.move_towards(m, m.wander_to[0], m.wander_to[1], 2.2 * m.speed_mult(), dt, 0.2):
                    m.wander_to = None
                    m.next_wander = t + random.uniform(4, 12)
            elif t >= m.next_wander:
                hx, hz, _ = m.home
                rad = max(wander, m.spawn_r * 0.6)
                a = random.uniform(0, math.tau)
                d = random.uniform(0.3, 1.0) * rad
                tx, tz = hx + math.cos(a) * d, hz + math.sin(a) * d
                if not m.zone.walkable(tx, tz) or m.zone.in_water(tx, tz):
                    m.next_wander = t + 3
                else:
                    m.wander_to = (tx, tz)

    def select_target(self, m: Mob) -> Unit | None:
        zone = m.zone
        t = now()
        if m.taunt_by and t < m.taunt_until:
            u = zone.entities.get(m.taunt_by)
            if u and u.alive:
                return u
        cur = zone.entities.get(m.target) if m.target else None
        best, best_v = None, -1.0
        for uid, v in m.threat.items():
            u = zone.entities.get(uid)
            if not u or u.dead:
                continue
            if v > best_v:
                best, best_v = u, v
        if best is None:
            return None
        if cur and cur.alive and cur.id in m.threat and best is not cur:
            factor = 1.1 if cur.dist(m) < 6 else 1.3
            if best_v < m.threat[cur.id] * factor:
                return cur
        return best

    def start_evade(self, m: Mob):
        m.state = "evade"
        m.evade_t = now()
        m.threat.clear()
        m.target = None
        m.cast = None
        m.combat = False
        m.auras = []
        m.taunt_by = None
        m.tap = None
        m.fled = False
        m.ab_used.clear()
        m.phase = 0
        m.mark("st", "tg", "cast", "au")
        if m.tpl.get("evade_yell"):
            self.yell(m, m.tpl["evade_yell"])
        for sid in m.summons:
            s = m.zone.entities.get(sid)
            if s:
                m.zone.remove(s)
        m.summons = []
        if m.tpl.get("boss") and m.zone:
            m.zone.boss_reset(m)

    def mob_evade(self, m: Mob, t: float, dt: float):
        hx, hz, hr = m.home
        if self.move_towards(m, hx, hz, 10.0, dt, 0.3) or t - m.evade_t > 12:
            m.state = "idle"
            if m.dist_xz(hx, hz) > 1:
                m.set_pos(hx, m.zone.height(hx, hz), hz)
            m.r = hr
            m.hp = m.max_hp
            m.reset_stats()
            m.next_wander = t + random.uniform(4, 10)
            m.mark("hp", "st", "p")

    def mob_flee(self, m: Mob, t: float, dt: float):
        tgt = m.zone.entities.get(m.target) if m.target else None
        if t >= m.flee_until or not tgt or tgt.dead or not m.threat:
            m.state = "combat" if m.threat else "idle"
            if not m.threat:
                self.start_evade(m)
            m.mark("st")
            return
        if m.rooted:
            return
        dx, dz = m.x - tgt.x, m.z - tgt.z
        d = math.hypot(dx, dz) or 1
        tx, tz = m.zone.walkable_clamp(m.x + dx / d * 10, m.z + dz / d * 10)
        self.move_towards(m, tx, tz, RUN_SPEED * 0.55 * m.speed_mult(), dt)

    def check_phase(self, m: Mob):
        phases = m.tpl.get("phases")
        if not phases:
            return
        nxt = m.phase + 1
        if nxt < len(phases) and m.hp <= m.max_hp * phases[nxt]["hp"]:
            m.phase = nxt
            ph = phases[nxt]
            t = now()
            for ab in ph.get("abilities", []):
                m.ab_next[ab["id"]] = t + ab.get("first", 2.0)
            if ph.get("yell"):
                self.yell(m, ph["yell"])
            if ph.get("aura"):
                a = ph["aura"]
                m.add_aura(Aura(a, m.id, t, m.level, a.get("dur", 3600)))
            if ph.get("name"):
                for p in m.zone.players.values():
                    self.send(p, {"t": "phase", "boss": m.name, "phase": nxt + 1, "name": ph["name"]})
            for act in ph.get("on_enter", []):
                self.boss_action(m, act)
            m.cast = None
            m.mark("cast", "au")

    def boss_action(self, m: Mob, act: dict):
        zone = m.zone
        kind = act.get("kind")
        if kind == "hazards":
            # dauerhafte Gefahrenzonen (z. B. Arenazerstörung, Lava)
            for (x, z) in act.get("points", []):
                self.spawn_ground(m, {"name": act.get("name", "Lava"), "radius": act.get("radius", 5), "dur": act.get("dur", 0),
                                      "interval": 1.0, "flat": act.get("flat", 200), "school": act.get("school", "fire"),
                                      "fx": act.get("fx", "lava")}, m.home[0] + x, m.home[1] + z, "mob")
        elif kind == "summon":
            self.mob_summon(m, act, None)

    def mob_combat(self, m: Mob, t: float, dt: float):
        zone = m.zone
        tpl = m.tpl
        for uid in list(m.threat):
            u = zone.entities.get(uid)
            if not u or u.dead:
                del m.threat[uid]
        if not m.threat:
            self.start_evade(m)
            return
        hx, hz, _ = m.home
        leash = tpl.get("leash") or (90 if zone.is_instance else 60)
        if m.dist_xz(hx, hz) > leash:
            self.start_evade(m)
            return
        self.check_phase(m)
        # Furcht und Verwandlung
        if any(a.fear for a in m.auras):
            fd = m.fear_dir or (1.0, 0.0)
            tx, tz = zone.walkable_clamp(m.x + fd[0] * 4, m.z + fd[1] * 4)
            if not self.move_towards(m, tx, tz, RUN_SPEED * 0.6, dt) and random.random() < 0.05:
                ang = random.uniform(0, math.tau)
                m.fear_dir = (math.cos(ang), math.sin(ang))
            return
        if m.incapacitated:
            return
        if tpl.get("family") == "humanoid" and not m.fled and not tpl.get("elite") and not tpl.get("no_flee") \
                and m.hp < m.max_hp * 0.15 and not zone.is_instance:
            m.fled = True
            m.state = "flee"
            m.flee_until = t + 6
            m.cast = None
            m.mark("st", "cast")
            self.mob_say(m, f"{m.name} versucht zu fliehen!", 40)
            return
        target = self.select_target(m)
        if not target:
            self.start_evade(m)
            return
        if m.target != target.id:
            m.target = target.id
            m.mark("tg")
        if m.cast:
            if m.cast.get("kind") != "channel_move":
                self.face(m, target)
            return
        d = m.dist(target)
        reach = m.radius + target.radius + 1.6
        for ab in self.mob_abilities(m):
            if self.try_mob_ability(m, ab, target, d, reach, t):
                return
        rng = tpl.get("ranged")
        if rng and d > reach and t >= m.cast_lock_until:
            if d > rng["range"] * 0.92:
                if not m.rooted:
                    self.move_towards(m, target.x, target.z, RUN_SPEED * 0.97 * m.speed_mult(), dt, rng["range"] * 0.8)
                return
            self.face(m, target)
            if t >= m.ab_next.get("ranged", 0):
                m.ab_next["ranged"] = t + rng["cd"]
                if rng.get("cast"):
                    m.cast = {"name": rng["name"], "start": t, "end": t + rng["cast"], "school": rng["school"],
                              "tid": target.id, "kind": "ranged", "icon": rng.get("icon", "bolt")}
                    m.mark("cast")
                else:
                    self.mob_ranged_hit(m, target, rng)
            return
        if d > reach:
            if not m.rooted:
                self.move_towards(m, target.x, target.z, RUN_SPEED * tpl.get("run", 0.97) * m.speed_mult(), dt, reach - 0.4)
            return
        self.face(m, target)
        if t >= m.swing_ready:
            haste = 1.0 + m.aura_pct("haste") / 100.0
            m.swing_ready = t + tpl.get("speed", 2.0) / max(0.3, haste)
            self.mob_melee(m, target, 1.0, None)

    def mob_melee(self, m: Mob, target: Unit, mult: float, ab_name: str | None):
        front = target.facing(m)
        out = C.melee_outcome(m, target, front)
        if out in ("miss", "dodge", "parry"):
            self.miss_event(m, target, out, ab_name)
            if isinstance(target, Player) and out in ("dodge", "parry"):
                self.on_reactive(target, out)
                if out == "parry" and target.has_aura("spiegelklinge"):
                    pass
            return
        dmg = C.mob_melee_damage(m, mult)
        kind = "hit"
        if out == "crit":
            dmg *= 2
            kind = "crit"
        elif out == "block":
            bv = target.stats.get("block_value", 5) if isinstance(target, Player) else 0
            dmg = max(0, dmg - bv)
            kind = "block"
            if isinstance(target, Player):
                self.on_reactive(target, "block")
            if dmg <= 0:
                self.miss_event(m, target, "block", ab_name)
                return
        if isinstance(target, Player):
            sk = target.has_aura("spiegelklinge")
            if sk and front:
                target.remove_aura("spiegelklinge")
                self.damage(target, m, dmg, "physical", "Spiegelklinge", "hit")
                self.miss_event(m, target, "reflect", ab_name)
                return
        self.damage(m, target, dmg, "physical", ab_name, kind)

    def mob_ranged_hit(self, m: Mob, target: Unit, rng: dict):
        zone = m.zone
        d = m.dist(target)
        speed = 30.0
        zone.emit_fx(m.x, m.z, {"k": "proj", "from": m.id, "to": target.id, "sp": speed, "school": rng["school"], "name": rng["name"]})
        tid = target.id

        def hit():
            tgt = zone.entities.get(tid)
            if not tgt or tgt.dead or m.dead:
                return
            if rng["school"] == "physical":
                out = C.melee_outcome(m, tgt, False, 0, True)
                if out in ("miss", "dodge"):
                    self.miss_event(m, tgt, out, rng["name"])
                    return
            else:
                out = C.spell_outcome(m, tgt)
                if out == "miss":
                    self.miss_event(m, tgt, "resist", rng["name"], rng["school"])
                    return
            dmg = C.mob_melee_damage(m, rng.get("mult", 1.0))
            kind = "hit"
            if out == "crit":
                dmg = int(dmg * 1.5)
                kind = "crit"
            self.damage(m, tgt, dmg, rng["school"], rng["name"], kind)
            if rng.get("slow"):
                tgt.add_aura(Aura({"id": "mob_slow", "name": rng["name"], "debuff": True, "slow": rng["slow"]}, m.id, now(), m.level, 4))
                self.after_aura_change(tgt)

        zone.schedule(d / speed, hit)

    def finish_mob_cast(self, m: Mob):
        c = m.cast
        m.cast = None
        m.mark("cast")
        if c["kind"] == "ranged":
            tgt = m.zone.entities.get(c["tid"])
            rng = m.tpl.get("ranged")
            if tgt and tgt.alive and rng and m.dist(tgt) <= rng["range"] + 5:
                self.mob_ranged_hit(m, tgt, rng)
        elif c["kind"] == "spell":
            ab = c["abdef"]
            tgt = m.zone.entities.get(c["tid"])
            if ab.get("heal"):
                ally = m.zone.entities.get(c["tid"])
                if ally and ally.alive:
                    self.heal(m, ally, int(ally.max_hp * ab["heal"]), ab["name"])
                return
            if not tgt or tgt.dead:
                return
            if ab.get("aoe"):
                for u in list(m.zone.entities.values()):
                    if isinstance(u, (Player, Pet)) and not u.dead and m.dist(u) <= ab["aoe"]:
                        self.mob_spell_damage(m, u, ab)
            else:
                self.mob_spell_damage(m, tgt, ab)

    def mob_spell_damage(self, m: Mob, tgt: Unit, ab: dict):
        out = C.spell_outcome(m, tgt)
        if out == "miss":
            self.miss_event(m, tgt, "resist", ab["name"], ab.get("school", "shadow"))
            return
        dmg = C.mob_melee_damage(m, ab.get("mult", 1.5)) if not ab.get("flat") else ab["flat"] * random.uniform(0.9, 1.1)
        if out == "crit":
            dmg *= 1.5
        self.damage(m, tgt, dmg, ab.get("school", "shadow"), ab["name"], "crit" if out == "crit" else "hit")
        if ab.get("debuff") and not tgt.dead:
            d = ab["debuff"]
            a = Aura(d, m.id, now(), m.level, d.get("dur", 8))
            if a.dot:
                a.extra["tick"] = d["dot"].get("flat", max(1, int(C.mob_melee_damage(m, d["dot"].get("mult", 0.3)))))
            tgt.add_aura(a)
            self.after_aura_change(tgt)

    def mob_summon(self, m: Mob, ab: dict, target: Unit | None):
        from ..content.world import MOBS
        zone = m.zone
        for i in range(ab.get("count", 2)):
            a = i / max(1, ab.get("count", 2)) * math.tau
            sx, sz = zone.walkable_clamp(m.x + math.cos(a) * 5, m.z + math.sin(a) * 5)
            add = Mob(MOBS[ab["summon"]], sx, sz, 0, difficulty=m.difficulty)
            add.y = zone.height(sx, sz)
            add.owner_boss = m.id
            add.respawn_at = 0
            zone.add(add)
            m.summons.append(add.id)
            zone.emit_fx(sx, sz, {"k": "summon", "x": round(sx, 2), "z": round(sz, 2), "school": ab.get("school", "shadow")})
            for uid, v in m.threat.items():
                add.threat[uid] = 1.0
            add.tap = m.tap
            tgt = target or (zone.entities.get(next(iter(m.threat))) if m.threat else None)
            if tgt:
                self.engage(add, tgt)

    def try_mob_ability(self, m: Mob, ab: dict, target: Unit, d: float, reach: float, t: float) -> bool:
        aid = ab["id"]
        if ab.get("once") and aid in m.ab_used:
            return False
        if ab.get("hp_below") and m.hp > m.max_hp * ab["hp_below"]:
            return False
        if not ab.get("once") and t < m.ab_next.get(aid, 0):
            return False
        kind = ab["kind"]
        if t < m.cast_lock_until and kind in ("cast", "heal"):
            return False
        zone = m.zone
        if kind == "strike":
            if d > reach:
                return False
            m.ab_next[aid] = t + ab["cd"]
            self.face(m, target)
            self.mob_melee(m, target, ab["mult"], ab["name"])
            if ab.get("debuff") and not target.dead:
                dd = ab["debuff"]
                a = Aura(dd, m.id, t, m.level, dd.get("dur", 6))
                if a.dot:
                    a.extra["tick"] = max(1, int(C.mob_melee_damage(m, dd["dot"].get("mult", 0.3))))
                target.add_aura(a)
                self.after_aura_change(target)
            return False
        if kind == "cast":
            rng = ab.get("range", 30)
            if d > rng:
                return False
            m.ab_next[aid] = t + ab.get("cd", 10)
            m.cast = {"name": ab["name"], "start": t, "end": t + ab.get("cast", 2.0), "school": ab.get("school", "shadow"),
                      "tid": target.id, "kind": "spell", "icon": ab.get("icon", "bolt"), "abdef": ab,
                      "uninterruptible": ab.get("uninterruptible", False)}
            m.mark("cast")
            return True
        if kind == "heal":
            allies = [u for u in zone.mobs_near(m.x, m.z, 30) if u.hp < u.max_hp * ab.get("below", 0.5) and not u.dead]
            if not allies:
                return False
            ally = min(allies, key=lambda u: u.hp / u.max_hp)
            m.ab_next[aid] = t + ab.get("cd", 12)
            m.cast = {"name": ab["name"], "start": t, "end": t + ab.get("cast", 2.5), "school": "nature", "tid": ally.id,
                      "kind": "spell", "icon": "healing", "abdef": ab}
            m.mark("cast")
            return True
        if ab.get("once"):
            m.ab_used.add(aid)
        m.ab_next[aid] = t + ab.get("cd", 10)
        if ab.get("yell"):
            self.yell(m, ab["yell"])
        if kind == "enrage":
            m.add_aura(Aura({"id": "raserei_" + aid, "name": ab["name"], "icon": "enrage", "pct": {"dmg_done": 50, "haste": 30}},
                            m.id, t, m.level, 3600))
            zone.emit_fx(m.x, m.z, {"k": "enrage", "id": m.id})
            return False
        if kind == "summon":
            self.mob_summon(m, ab, target)
            return False
        if kind == "aura_self":
            a = ab["aura"]
            m.add_aura(Aura(a, m.id, t, m.level, a.get("dur", 10)))
            zone.emit_fx(m.x, m.z, {"k": "buff", "id": m.id, "school": ab.get("school", "shadow")})
            return False
        if kind == "teleport":
            cands = [zone.entities.get(uid) for uid in m.threat if zone.entities.get(uid)]
            if cands:
                v = random.choice(cands)
                zone.emit_fx(m.x, m.z, {"k": "blink", "id": m.id, "x": round(m.x, 2), "z": round(m.z, 2), "x2": round(v.x, 2), "z2": round(v.z, 2)})
                m.set_pos(v.x + 1.5, zone.height(v.x + 1.5, v.z), v.z)
            return False
        if kind == "hazard":
            # Feuerflächen o. Ä. unter zufälligen Spielern (bleiben eine Weile liegen)
            cands = [zone.entities.get(uid) for uid in m.threat if zone.entities.get(uid)]
            random.shuffle(cands)
            for v in cands[: ab.get("count", 2)]:
                self.spawn_ground(m, {"name": ab["name"], "radius": ab.get("radius", 4), "dur": ab.get("dur", 12),
                                      "interval": 1.0, "flat": ab.get("flat", 100), "school": ab.get("school", "fire"),
                                      "fx": ab.get("fx", "fire"), "delay": ab.get("warn", 1.5)}, v.x, v.z, "mob")
                zone.emit_fx(v.x, v.z, {"k": "tele", "dur": ab.get("warn", 1.5), "name": ab["name"], "shape": "circle",
                                        "x": round(v.x, 2), "z": round(v.z, 2), "r": ab.get("radius", 4)})
            return False
        # Bodenmarkierungen (Telegraphen)
        warn = ab.get("warn", 1.5)
        shapes = []
        if kind == "telegraph_circle_self":
            shapes.append({"shape": "circle", "x": m.x, "z": m.z, "r": ab["radius"]})
        elif kind == "telegraph_ring":
            shapes.append({"shape": "ring", "x": m.x, "z": m.z, "r": ab["radius"], "r0": ab.get("inner", 6)})
        elif kind == "telegraph_cone":
            if d > ab["radius"]:
                m.ab_next[aid] = t + 1.0
                return False
            rot = m.angle_to(target)
            m.r = rot
            m.mark("p")
            shapes.append({"shape": "cone", "x": m.x, "z": m.z, "r": ab["radius"], "rot": rot, "ang": math.radians(ab["angle"])})
        elif kind == "telegraph_line":
            rot = m.angle_to(target)
            m.r = rot
            m.mark("p")
            shapes.append({"shape": "line", "x": m.x, "z": m.z, "r": ab["radius"], "rot": rot, "w": ab.get("width", 4)})
        elif kind == "telegraph_circles_players":
            cands = [zone.entities.get(uid) for uid in m.threat if zone.entities.get(uid)]
            random.shuffle(cands)
            for p in cands[: ab.get("count", 1)]:
                shapes.append({"shape": "circle", "x": p.x, "z": p.z, "r": ab["radius"]})
        elif kind == "telegraph_random":
            for i in range(ab.get("count", 4)):
                a = random.uniform(0, math.tau)
                dd = random.uniform(3, ab.get("spread", 14))
                shapes.append({"shape": "circle", "x": m.x + math.cos(a) * dd, "z": m.z + math.sin(a) * dd, "r": ab["radius"]})
        if not shapes:
            return False
        is_self_cast = kind in ("telegraph_circle_self", "telegraph_cone", "telegraph_ring", "telegraph_line")
        if is_self_cast:
            m.cast = {"name": ab["name"], "start": t, "end": t + warn, "kind": "telegraph", "school": ab.get("school", "physical"),
                      "icon": "warn", "uninterruptible": True}
            m.mark("cast")
        for s in shapes:
            zone.emit_fx(s["x"], s["z"], {"k": "tele", "dur": warn, "name": ab["name"], "school": ab.get("school", "physical"),
                                          **{k: round(v, 3) if isinstance(v, float) else v for k, v in s.items()}})

        def boom():
            if m.dead or m.state != "combat":
                return
            for u in list(zone.entities.values()):
                if u.dead or not isinstance(u, (Player, Pet)):
                    continue
                for s in shapes:
                    if self._in_shape(u, s):
                        if ab.get("flat"):
                            dmg = ab["flat"] * random.uniform(0.9, 1.1) * m.difficulty.get("dmg", 1.0)
                        else:
                            dmg = C.mob_melee_damage(m, ab.get("mult", 1.0))
                        self.damage(m, u, dmg, ab.get("school", "physical"), ab["name"], "hit")
                        if ab.get("knockback") and not u.dead and isinstance(u, Player):
                            self.knockback(m, u, ab["knockback"])
                        if ab.get("debuff") and not u.dead:
                            dd = ab["debuff"]
                            a = Aura(dd, m.id, now(), m.level, dd.get("dur", 6))
                            if a.dot:
                                a.extra["tick"] = dd["dot"].get("flat", 20)
                            u.add_aura(a)
                            self.after_aura_change(u)
                        break
            for s in shapes:
                zone.emit_fx(s["x"], s["z"], {"k": "boom", "shape": s["shape"], "x": round(s["x"], 2), "z": round(s["z"], 2),
                                              "r": s["r"], "school": ab.get("school", "physical"), "rot": round(s.get("rot", 0.0), 3),
                                              "ang": round(s.get("ang", 0.0), 3)})
            if ab.get("leave_hazard"):
                for s in shapes:
                    self.spawn_ground(m, {"name": ab["name"], "radius": s["r"] * 0.8, "dur": ab["leave_hazard"], "interval": 1.0,
                                          "flat": ab.get("hazard_flat", 60), "school": ab.get("school", "fire"), "fx": "fire"},
                                      s["x"], s["z"], "mob")

        zone.schedule(warn, boom)
        return True

    def knockback(self, src: Unit, p: Player, dist: float):
        dx, dz = p.x - src.x, p.z - src.z
        d = math.hypot(dx, dz) or 1
        nx, nz = p.x + dx / d * dist, p.z + dz / d * dist
        nx, nz = p.zone.walkable_clamp(nx, nz)
        self.teleport(p, nx, nz, p.r, kind="knock")

    @staticmethod
    def _in_shape(p: Unit, s: dict) -> bool:
        dx, dz = p.x - s["x"], p.z - s["z"]
        dist = math.hypot(dx, dz)
        if s["shape"] == "line":
            rot = s["rot"]
            fx, fz = -math.sin(rot), -math.cos(rot)
            along = dx * fx + dz * fz
            side = abs(dx * fz - dz * fx)
            return 0 <= along <= s["r"] and side <= s.get("w", 4) / 2 + p.radius
        if dist > s["r"] + p.radius:
            return False
        if s["shape"] == "circle":
            return True
        if s["shape"] == "ring":
            return dist >= s.get("r0", 6) - p.radius
        ang = math.atan2(-dx, -dz)
        diff = (ang - s["rot"] + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) <= s["ang"] / 2 or dist < 1.2

    # ================================================================== Begleiter
    def pet_tick(self, pet: Pet, t: float, dt: float):
        zone = pet.zone
        owner = self.players.get(pet.owner_id)
        if not owner or owner.zone is not zone or (pet.expires and t >= pet.expires):
            zone.remove(pet)
            if owner and pet.id in owner.pets:
                owner.pets.remove(pet.id)
            return
        if pet.incapacitated:
            return
        if pet.cast and t >= pet.cast["end"]:
            self.finish_mob_cast(pet)
        if pet.cast:
            return
        # Heiler (Naturgeist)
        if pet.tpl.get("healer") and t >= pet.ab_next.get("heal", 0):
            pet.ab_next["heal"] = t + 3.0
            hurt = [m for m in self.party_members_near(owner, 30) if m.hp < m.max_hp * 0.92]
            if hurt:
                m = min(hurt, key=lambda u: u.hp / u.max_hp)
                amount = int((8 + owner.level * 3.2 + owner.stats.get("heal", 0) * 0.25) * pet.pet_mult)
                self.heal(pet, m, amount, "Heilende Sporen")
                zone.emit_fx(m.x, m.z, {"k": "buff", "id": m.id, "school": "nature"})
        # Ziel: Ziel des Besitzers oder wer den Besitzer angreift
        target = None
        if owner.target and owner.combat:
            u = zone.entities.get(owner.target)
            if u and not u.dead and self.is_enemy(owner, u):
                target = u
        if target is None and owner.combat:
            for u in zone.mobs_near(owner.x, owner.z, 25):
                if isinstance(u, Pet):
                    continue
                if owner.id in u.threat or pet.id in u.threat:
                    target = u
                    break
        if pet.tpl.get("taunt_aura") and target and isinstance(target, Mob) and t >= pet.ab_next.get("taunt", 0):
            pet.ab_next["taunt"] = t + 8
            target.threat[pet.id] = max(target.threat.values(), default=0) + 10
            self.add_threat(target, pet, 1)
        if target is None:
            # Folgen
            pet.combat = False
            a = owner.r + math.pi + pet.follow_angle
            fx, fz = owner.x + math.sin(a) * 2.5, owner.z + math.cos(a) * 2.5
            if pet.dist_xz(fx, fz) > 1.0:
                speed = RUN_SPEED * (owner.mount_speed if owner.mounted else 1.0) * 1.15
                if pet.dist(owner) > 40:
                    pet.set_pos(fx, zone.height(fx, fz), fz, owner.r)
                else:
                    self.move_towards(pet, fx, fz, speed, dt, 0.4)
            return
        pet.combat = True
        if pet.target != target.id:
            pet.target = target.id
            pet.mark("tg")
        d = pet.dist(target)
        rng = pet.tpl.get("ranged")
        if rng:
            if d > rng["range"] * 0.9:
                self.move_towards(pet, target.x, target.z, RUN_SPEED, dt, rng["range"] * 0.8)
                return
            self.face(pet, target)
            if t >= pet.ab_next.get("ranged", 0):
                pet.ab_next["ranged"] = t + rng["cd"]
                if rng.get("cast"):
                    pet.cast = {"name": rng["name"], "start": t, "end": t + rng["cast"], "school": rng["school"],
                                "tid": target.id, "kind": "ranged", "icon": "bolt"}
                    pet.mark("cast")
                else:
                    self.mob_ranged_hit(pet, target, rng)
            return
        reach = pet.radius + target.radius + 1.6
        if d > reach:
            self.move_towards(pet, target.x, target.z, RUN_SPEED * 1.1, dt, reach - 0.4)
            return
        self.face(pet, target)
        if t >= pet.swing_ready:
            pet.swing_ready = t + pet.tpl.get("speed", 2.0)
            out = C.melee_outcome(pet, target, target.facing(pet))
            if out in ("miss", "dodge", "parry"):
                self.miss_event(pet, target, out, None)
                if isinstance(target, Mob):
                    self.add_threat(target, pet, 1)
                return
            dmg = C.mob_melee_damage(pet) * (2 if out == "crit" else 1)
            self.damage(pet, target, dmg, "physical", None, "crit" if out == "crit" else "hit")

    def mob_xp_for(self, tpl: dict, mob_level: int, p: Player) -> int:
        return mob_xp(tpl, mob_level, p.level)
