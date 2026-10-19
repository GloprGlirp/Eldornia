"""Die Spielwelt: Zonen, Instanzen, Simulationsschleife, Gegner-KI und Kampfsystem.

Alles Spielrelevante passiert hier serverseitig (Schaden, Abklingzeiten, Beute, Erfahrung).
Der Client stellt nur dar und schickt Eingaben.
"""
from __future__ import annotations

import asyncio
import heapq
import itertools
import logging
import math
import random

from .. import config
from . import combat as C
from .actions import ActionsMixin
from .content import world as W
from .content.abilities import ABILITIES, GCD, ability_cost, ability_range, scaled, scaled_range
from .content.classes import MAX_LEVEL, xp_to_next
from .content.items import ITEMS, item_usable_by, world_drop_pool
from .content.mobs import MOBS, mob_xp
from .content.npcs import NPCS
from .content.quests import ITEM_QUESTS, QUESTS
from .entities import RUN_SPEED, Aura, GameObj, Mob, Npc, Player, Unit, now
from .terrain import gruenmark_heightmap, krypta_nav

log = logging.getLogger("eldornia.world")

VIEW_OUTDOOR = 150.0
INSTANCE_IDLE_TIMEOUT = 600.0
_seq = itertools.count()


class Party:
    _ids = itertools.count(1)

    def __init__(self, leader: Player):
        self.id = next(Party._ids)
        self.leader = leader.id
        self.members: list[int] = [leader.id]
        self.instance_key: str | None = None


# ============================================================================== Zone
class Zone:
    def __init__(self, world: "World", zone_id: str, key: str):
        self.world = world
        self.id = zone_id
        self.key = key
        self.cfg = W.ZONES[zone_id]
        self.is_instance = self.cfg["type"] == "dungeon"
        self.entities: dict[int, Unit] = {}
        self.players: dict[int, Player] = {}
        self.npcs: dict[str, Npc] = {}
        self.timers: list = []
        self.events: list = []
        self.fx: list = []
        self.empty_since = now()
        self.hm = gruenmark_heightmap() if zone_id == "gruenmark" else None
        self.nav = krypta_nav() if zone_id == "krypta" else None
        self.view2 = (VIEW_OUTDOOR if not self.is_instance else 1000.0) ** 2
        self._populate()

    def height(self, x: float, z: float) -> float:
        return self.hm.height(x, z) if self.hm else 0.0

    def _populate(self):
        for spec in W.SPAWNS.get(self.id, []):
            tpl = MOBS[spec["mob"]]
            if "pos" in spec:
                x, z = spec["pos"]
                self.add(Mob(tpl, x, z, spec.get("r", random.uniform(0, math.tau)), spec.get("lvl")))
            else:
                for _ in range(spec["n"]):
                    x, z = self._random_point(spec["x"], spec["z"], spec["r"])
                    self.add(Mob(tpl, x, z, random.uniform(0, math.tau), spec.get("lvl"), spawn_r=spec["r"]))
        for tpl in NPCS.values():
            if tpl["zone"] == self.id:
                npc = Npc(tpl)
                self.npcs[tpl["id"]] = npc
                self.add(npc)
        for spec in W.OBJECTS.get(self.id, []):
            self.add(GameObj(spec))
        for e in self.entities.values():
            e.y = self.height(e.x, e.z)

    def _random_point(self, cx, cz, r):
        for _ in range(40):
            a = random.uniform(0, math.tau)
            d = r * math.sqrt(random.random())
            x, z = cx + math.cos(a) * d, cz + math.sin(a) * d
            if self.hm:
                if any((x - w["x"]) ** 2 + (z - w["z"]) ** 2 < (w["r"] + 1) ** 2 for w in W.WATER):
                    continue
            return x, z
        return cx, cz

    def add(self, e: Unit):
        e.zone = self
        self.entities[e.id] = e
        if isinstance(e, Player):
            self.players[e.id] = e

    def remove(self, e: Unit):
        self.entities.pop(e.id, None)
        self.players.pop(e.id, None)
        if not self.players:
            self.empty_since = now()

    def schedule(self, delay: float, fn):
        heapq.heappush(self.timers, (now() + delay, next(_seq), fn))

    def run_timers(self, t: float):
        while self.timers and self.timers[0][0] <= t:
            _, _, fn = heapq.heappop(self.timers)
            try:
                fn()
            except Exception:  # pragma: no cover - Fehler in Effekten dürfen die Welt nicht stoppen
                log.exception("Timer-Fehler")

    def emit(self, at: Unit, ev: dict):
        self.events.append((at.x, at.z, ev))

    def emit_fx(self, x: float, z: float, fx: dict):
        self.fx.append((x, z, fx))

    def walkable_clamp(self, x: float, z: float) -> tuple[float, float]:
        if self.nav:
            return self.nav.clamp(x, z)
        lim = W.ZONES[self.id]["size"] / 2 - 6
        return max(-lim, min(lim, x)), max(-lim, min(lim, z))

    def mobs_near(self, x: float, z: float, r: float):
        r2 = r * r
        for e in self.entities.values():
            if isinstance(e, Mob) and not e.dead and not e.hidden and (e.x - x) ** 2 + (e.z - z) ** 2 <= r2:
                yield e


# ============================================================================== Welt
class World(ActionsMixin):
    def __init__(self):
        self.zones: dict[str, Zone] = {}
        self.players: dict[int, Player] = {}
        self.by_name: dict[str, Player] = {}
        self.by_char: dict[int, Player] = {}
        self.parties: dict[int, Party] = {}
        self.zones["gruenmark"] = Zone(self, "gruenmark", "gruenmark")
        self.last_tick = now()
        self.next_party_update = 0.0
        self.next_autosave = now() + config.SAVE_INTERVAL
        self.save_callback = None      # wird von main.py gesetzt (speichert Charaktere)
        self.running = False

    # ------------------------------------------------------------------ Hauptschleife
    async def run(self):
        self.running = True
        interval = 1.0 / config.TICK_RATE
        while self.running:
            start = now()
            try:
                self.tick()
            except Exception:  # pragma: no cover
                log.exception("Fehler im Welt-Tick")
            elapsed = now() - start
            await asyncio.sleep(max(0.0, interval - elapsed))

    def tick(self):
        t = now()
        dt = min(0.5, t - self.last_tick)
        self.last_tick = t
        for zone in list(self.zones.values()):
            zone.run_timers(t)
            self.zone_tick(zone, t, dt)
        for zone in list(self.zones.values()):
            self.broadcast(zone)
        if t >= self.next_party_update:
            self.next_party_update = t + 0.5
            for party in list(self.parties.values()):
                self.send_party(party)
        for key, zone in list(self.zones.items()):
            if zone.is_instance and not zone.players and t - zone.empty_since > INSTANCE_IDLE_TIMEOUT:
                del self.zones[key]
        if t >= self.next_autosave:
            self.next_autosave = t + config.SAVE_INTERVAL
            if self.save_callback:
                for p in list(self.players.values()):
                    self.save_callback(p)

    def zone_tick(self, zone: Zone, t: float, dt: float):
        in_combat: set[int] = set()
        for e in list(zone.entities.values()):
            if isinstance(e, Mob):
                self.mob_tick(e, t, dt)
                if e.threat and not e.dead:
                    in_combat.update(e.threat.keys())
            elif isinstance(e, Npc):
                self.npc_tick(e, t, dt)
            elif isinstance(e, GameObj):
                if not e.available and t >= e.respawn_at:
                    e.available = True
                    e.hidden = False
        for p in list(zone.players.values()):
            combat = (p.id in in_combat or t < p.combat_until) and not p.dead
            if combat != p.combat:
                p.combat = combat
                p.mark("st")
            self.player_tick(p, t, dt)

    # ------------------------------------------------------------------ Senden
    def send(self, p: Player, msg: dict):
        if p.session:
            p.session.send(msg)

    def sys(self, p: Player, text: str):
        self.send(p, {"t": "sys", "text": text})

    def err(self, p: Player, text: str):
        self.send(p, {"t": "err", "text": text})

    def view_flags(self, p: Player, e: Unit) -> dict:
        if isinstance(e, Npc):
            return {"q": self.quest_marker(p, e.npc_id)}
        if isinstance(e, Mob):
            tapped_other = e.tap is not None and p.id not in e.tap and not e.dead
            return {"l": bool(e.dead and p.id in e.loot), "tap": tapped_other}
        if isinstance(e, GameObj):
            return {"u": e.available and self.obj_usable(p, e)}
        return {}

    def broadcast(self, zone: Zone):
        events, fxs = zone.events, zone.fx
        zone.events, zone.fx = [], []
        delta_cache: dict[int, dict] = {}
        for p in zone.players.values():
            if not p.ready or not p.session:
                continue
            vis: set[int] = set()
            spawns, deltas = [], []
            px, pz = p.x, p.z
            for e in zone.entities.values():
                if e is p or getattr(e, "hidden", False):
                    continue
                if (e.x - px) ** 2 + (e.z - pz) ** 2 > zone.view2:
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
                if d:
                    deltas.append(d)
            gone = p.known - vis
            for gid in gone:
                p.flag_cache.pop(gid, None)
            if p.dirty:
                deltas.append(p.delta(p.dirty, for_self=True))
            v2 = zone.view2
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

    # ------------------------------------------------------------------ Bedrohung / Kampf
    def tap_set(self, p: Player) -> set[int]:
        if p.party:
            return set(p.party.members)
        return {p.id}

    def add_threat(self, mob: Mob, unit: Unit, amount: float):
        if mob.dead or mob.state == "evade" or not isinstance(unit, Player) or unit.dead:
            return
        if mob.look.get("critter") and amount <= 0:
            return
        mob.threat[unit.id] = mob.threat.get(unit.id, 0.0) + max(0.0, amount)
        if mob.tap is None:
            mob.tap = self.tap_set(unit)
        if mob.state == "idle":
            self.engage(mob, unit)

    def engage(self, mob: Mob, unit: Player):
        t = now()
        mob.state = "combat"
        mob.combat = True
        mob.engage_t = t
        mob.wander_to = None
        mob.swing_ready = max(mob.swing_ready, t + 0.4)
        for ab in mob.tpl["abilities"]:
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
                        and other.hostile and not other.look.get("critter"):
                    other.threat[unit.id] = 1.0
                    if other.tap is None:
                        other.tap = mob.tap
                    self.engage(other, unit)

    def yell(self, unit: Unit, text: str):
        for p in unit.zone.players.values():
            if p.dist(unit) < 120:
                self.send(p, {"t": "chat", "ch": "yell", "from": unit.name, "fid": unit.id, "text": text})

    def mob_say(self, unit: Unit, text: str, radius: float = 40):
        for p in unit.zone.players.values():
            if p.dist(unit) < radius:
                self.send(p, {"t": "chat", "ch": "npc", "from": unit.name, "fid": unit.id, "text": text})

    def damage(self, src: Unit, dst: Unit, amount: float, school: str, ab: str | None, kind: str = "hit",
               threat_mult: float = 1.0, extra_threat: float = 0.0, periodic: bool = False, mitigate: bool = True):
        if dst.dead or getattr(dst, "hidden", False):
            return 0
        zone = dst.zone
        if zone is None:
            return 0
        t = now()
        if isinstance(dst, Mob) and dst.state == "evade":
            zone.emit(dst, {"s": src.id, "d": dst.id, "a": 0, "k": "evade", "ab": ab, "sc": school})
            return 0
        if school == "physical" and mitigate and not periodic:
            amount *= 1.0 - C.armor_reduction(C.unit_armor(dst), src.level)
        amount = max(1, int(round(amount)))
        if isinstance(dst, Mob) and dst.look.get("dummy"):
            dst.hp = max(1, dst.hp - amount)
        else:
            dst.hp -= amount
        dst.mark("hp")
        zone.emit(dst, {"s": src.id, "d": dst.id, "a": amount, "k": kind, "ab": ab, "sc": school,
                        "pe": 1 if periodic else 0})
        if isinstance(dst, Mob):
            dst.last_hit_t = t
            if isinstance(src, Player):
                self.add_threat(dst, src, amount * threat_mult + extra_threat)
                if dst.state == "evade":
                    return amount
        if isinstance(src, Player):
            src.combat_until = max(src.combat_until, t + 1.5)
        if isinstance(dst, Player):
            dst.combat_until = max(dst.combat_until, t + 1.5)
            if dst.eating:
                self.stop_eating(dst)
            if dst.cast and dst.cast.get("kind") == "gather":
                self.interrupt(dst)
            if dst.power_type == "rage" and not periodic:
                gain = 2.5 * amount / C.rage_conversion(dst.level)
                dst.power = min(dst.max_power, dst.power + gain)
                dst.mark("pw")
            if isinstance(src, Mob) and school == "physical" and not periodic:
                fa = dst.has_aura("frostpanzer")
                if fa and fa.chill_attackers and src.alive:
                    src.add_aura(Aura("frostpanzer_kaelte", "Frostpanzer", dst.id, t + 5, 5, icon="frostarmor",
                                      color="#9fd8ff", debuff=True, slow=0.3))
        if dst.hp <= 0:
            self.kill(dst, src)
        return amount

    def heal(self, src: Unit, dst: Unit, amount: int, ab: str):
        if dst.dead:
            return
        before = dst.hp
        dst.hp = min(dst.max_hp, dst.hp + int(amount))
        dst.mark("hp")
        if dst.zone:
            dst.zone.emit(dst, {"s": src.id, "d": dst.id, "a": dst.hp - before, "k": "heal", "ab": ab, "sc": "holy"})

    def miss_event(self, src: Unit, dst: Unit, kind: str, ab: str | None, school: str = "physical"):
        if dst.zone:
            dst.zone.emit(dst, {"s": src.id, "d": dst.id, "a": 0, "k": kind, "ab": ab, "sc": school})

    def kill(self, dst: Unit, killer: Unit):
        if isinstance(dst, Player):
            self.player_died(dst)
        elif isinstance(dst, Mob):
            self.mob_died(dst, killer)

    # ------------------------------------------------------------------ Tod eines Gegners
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
        if tpl.get("death_yell"):
            self.yell(mob, tpl["death_yell"])
        for sid in mob.summons:
            s = zone.entities.get(sid)
            if isinstance(s, Mob) and not s.dead:
                self.mob_died(s, killer)
        tap = mob.tap or ({killer.id} if isinstance(killer, Player) else set())
        eligible = [zone.players[pid] for pid in tap
                    if pid in zone.players and not zone.players[pid].dead and zone.players[pid].dist(mob) < 90]
        if not eligible and isinstance(killer, Player) and killer.alive:
            eligible = [killer]
        mob.tap = set(p.id for p in eligible) or mob.tap
        n = len(eligible)
        for p in eligible:
            xp = int(mob_xp(tpl, mob.level, p.level) * C.group_xp_factor(n) / n)
            if xp > 0:
                self.add_xp(p, xp, mob)
            self.quest_kill(p, tpl["id"])
            loot = self.generate_loot(mob, p)
            if loot["items"] or loot["copper"]:
                mob.loot[p.id] = loot
        mob.threat.clear()
        if tpl.get("summoned"):
            mob.corpse_until = t + 6
        elif zone.is_instance:
            mob.corpse_until = t + 600
        else:
            mob.corpse_until = t + (150 if mob.loot else 30)
        resp = tpl.get("respawn", 0)
        mob.respawn_at = t + resp * random.uniform(0.9, 1.2) if resp and not zone.is_instance else 0.0

    def player_needs_item(self, p: Player, item_id: str) -> bool:
        for qid in ITEM_QUESTS.get(item_id, []):
            if qid in p.quests_active:
                for o in QUESTS[qid]["objectives"]:
                    if o["type"] == "collect" and o["item"] == item_id and p.count_item(item_id) < o["count"]:
                        return True
        return False

    def generate_loot(self, mob: Mob, p: Player) -> dict:
        tpl = mob.tpl
        items: list[list] = []
        for entry in tpl.get("loot", []):
            it = ITEMS[entry["item"]]
            if it.get("quest") and not self.player_needs_item(p, entry["item"]):
                continue
            if random.random() < entry["chance"]:
                items.append([entry["item"], 1])
        if tpl.get("world_drop") and random.random() < tpl["world_drop"]:
            pool = world_drop_pool(mob.level)
            if pool:
                items.append([random.choice(pool), 1])
        bl = tpl.get("boss_loot")
        if bl:
            epics = [i for i in bl["epics"] if item_usable_by(ITEMS[i], p.cls)] or bl["epics"]
            items.append([random.choice(epics), 1])
            if random.random() < 0.6:
                blues = [i for i in bl["blues"] if item_usable_by(ITEMS[i], p.cls)] or bl["blues"]
                items.append([random.choice(blues), 1])
            if random.random() < bl.get("legendary_chance", 0):
                items.append([bl["legendary"], 1])
        copper = 0
        if tpl.get("copper"):
            lo, hi = tpl["copper"]
            copper = random.randint(lo, hi)
        return {"items": items, "copper": copper}

    # ------------------------------------------------------------------ Erfahrung & Stufen
    def add_xp(self, p: Player, amount: int, src: Unit | None = None):
        if p.level >= MAX_LEVEL:
            return
        p.xp += amount
        self.send(p, {"t": "xp", "a": amount, "src": src.name if src else None})
        leveled = False
        while p.level < MAX_LEVEL and p.xp >= xp_to_next(p.level):
            p.xp -= xp_to_next(p.level)
            p.level += 1
            leveled = True
            self.on_level_up(p)
        if p.level >= MAX_LEVEL:
            p.xp = 0
        if not leveled:
            self.send_stats(p)

    def on_level_up(self, p: Player):
        p.recalc(full=True)
        p.mark("lvl", "hp", "pw")
        if p.zone:
            p.zone.emit_fx(p.x, p.z, {"k": "levelup", "id": p.id})
        self.sys(p, f"Glückwunsch! Ihr habt Stufe {p.level} erreicht!")
        new = [a for a in p.cls["abilities"] if ABILITIES[a]["level"] == p.level]
        for a in new:
            self.sys(p, f"Ihr habt eine neue Fähigkeit erlernt: {ABILITIES[a]['name']}.")
        self.send(p, {"t": "levelup", "lvl": p.level, "new": new})
        self.send_stats(p)
        self.send_abilities(p)
        if p.party:
            for mid in p.party.members:
                m = self.players.get(mid)
                if m and m is not p:
                    self.sys(m, f"{p.name} hat Stufe {p.level} erreicht!")

    # ------------------------------------------------------------------ Tod eines Spielers
    def player_died(self, p: Player):
        p.dead = True
        p.hp = 0
        p.cast = None
        p.auto_attack = False
        p.eating = None
        p.sitting = False
        p.auras = []
        p.recalc()
        p.hp = 0
        if p.power_type == "rage":
            p.power = 0
        p.mark("hp", "pw", "st", "au", "cast")
        if p.zone:
            for e in p.zone.entities.values():
                if isinstance(e, Mob) and p.id in e.threat:
                    del e.threat[p.id]
        self.send(p, {"t": "died"})
        self.sys(p, "Ihr seid gestorben.")

    def release_spirit(self, p: Player):
        if not p.dead:
            return
        gz = self.zones["gruenmark"]
        gx, gz_, gr = W.ZONES["gruenmark"]["graveyard"]
        p.dead = False
        p.hp = max(1, p.max_hp // 2)
        if p.power_type == "mana":
            p.power = p.max_power // 2
        p.mark("hp", "pw", "st")
        if p.zone is not gz:
            self.move_player(p, gz, gx, gz_, gr)
        else:
            self.teleport(p, gx, gz_, gr)
        self.sys(p, "Bruder Anselm hat Euch ins Leben zurückgeholt. Möge das Licht mit Euch sein.")

    # ------------------------------------------------------------------ Bewegung
    def teleport(self, p: Player, x: float, z: float, r: float | None = None, kind: str = "tele"):
        zone = p.zone
        x, z = zone.walkable_clamp(x, z)
        y = zone.height(x, z)
        p.set_pos(x, y, z, r if r is not None else p.r)
        p.move_budget = 12.0
        self.send(p, {"t": "force", "p": [round(x, 2), round(y, 2), round(z, 2), round(p.r, 3)], "k": kind})

    def move_player(self, p: Player, zone: Zone, x: float, z: float, r: float):
        old = p.zone
        if old:
            old.remove(p)
        p.cast = None
        p.auto_attack = False
        p.target = None
        p.loot_open = None
        p.eating = None
        p.sitting = False
        x, z = zone.walkable_clamp(x, z)
        p.x, p.z, p.r = x, z, r
        p.y = zone.height(x, z)
        zone.add(p)
        p.known = set()
        p.flag_cache = {}
        p.ready = False
        p.move_budget = 12.0
        p.portal_lock = now() + 3.0
        p.mark("p", "tg", "cast", "st")
        self.send(p, {"t": "zone", "zone": zone.id, "name": zone.cfg["name"], "inst": zone.is_instance,
                      "p": [round(x, 2), round(p.y, 2), round(z, 2), round(r, 3)]})

    def instance_for(self, p: Player, zone_id: str) -> Zone | None:
        owner = f"party{p.party.id}" if p.party else f"p{p.char_id}"
        key = f"{zone_id}:{owner}"
        zone = self.zones.get(key)
        if zone is None and p.party:
            # Gruppenmitglied ist schon in einer Instanz? Dann dorthin.
            for mid in p.party.members:
                m = self.players.get(mid)
                if m and m.zone and m.zone.id == zone_id:
                    zone = m.zone
                    break
        if zone is None:
            zone = Zone(self, zone_id, key)
            self.zones[key] = zone
        if len(zone.players) >= W.ZONES[zone_id].get("max_players", 5):
            return None
        return zone

    def enter_portal(self, p: Player, portal: dict):
        if now() < getattr(p, "portal_lock", 0):
            return
        p.portal_lock = now() + 3.0
        dest = portal["to"]
        if W.ZONES[dest]["type"] == "dungeon":
            zone = self.instance_for(p, dest)
            if zone is None:
                self.err(p, "Diese Instanz ist voll.")
                return
            sx, sz, sr = W.ZONES[dest]["start"]
            self.move_player(p, zone, sx, sz, sr)
            self.sys(p, f"Ihr betretet: {W.ZONES[dest]['name']}. Gegner in Instanzen erscheinen nicht erneut.")
        else:
            ex = p.zone.cfg.get("exit") or ["gruenmark", 0, 0, 0]
            self.move_player(p, self.zones[ex[0]], ex[1], ex[2], ex[3])

    # ------------------------------------------------------------------ Gegner-KI
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
        if zone.nav:
            nx, nz = zone.nav.clamp(nx, nz, 0.5)
        u.set_pos(nx, zone.height(nx, nz), nz, math.atan2(-dx, -dz))
        return False

    def face(self, u: Unit, o: Unit):
        r = u.angle_to(o)
        if abs((r - u.r + math.pi) % (2 * math.pi) - math.pi) > 0.05:
            u.r = r
            u.mark("p")

    def aggro_radius(self, m: Mob, p: Player) -> float:
        if m.tpl.get("aggro_radius"):
            return m.tpl["aggro_radius"]
        base = 12.0 if m.tpl.get("elite") else 10.0
        return max(3.5, min(22.0, base - (p.level - m.level) * 1.2))

    def mob_idle(self, m: Mob, t: float, dt: float):
        tpl = m.tpl
        if tpl.get("aggro") and m.hostile:
            for p in m.zone.players.values():
                if p.dead or not p.ready:
                    continue
                if abs(p.y - m.y) < 8 and p.dist(m) < self.aggro_radius(m, p):
                    self.add_threat(m, p, 1.0)
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
                if m.zone.hm and any((tx - w["x"]) ** 2 + (tz - w["z"]) ** 2 < (w["r"] + 1) ** 2 for w in W.WATER):
                    m.next_wander = t + 3
                else:
                    m.wander_to = (tx, tz)

    def select_target(self, m: Mob) -> Player | None:
        zone = m.zone
        t = now()
        if m.taunt_by and t < m.taunt_until:
            p = zone.players.get(m.taunt_by)
            if p and p.alive:
                return p
        cur = zone.players.get(m.target) if m.target else None
        best, best_v = None, -1.0
        for pid, v in m.threat.items():
            if v > best_v:
                best, best_v = pid, v
        if best is None:
            return None
        bp = zone.players.get(best)
        if cur and cur.alive and cur.id in m.threat and bp is not cur:
            factor = 1.1 if cur.dist(m) < 6 else 1.3
            if best_v < m.threat[cur.id] * factor:
                return cur
        return bp

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
        m.mark("st", "tg", "cast", "au")
        if m.tpl.get("evade_yell"):
            self.yell(m, m.tpl["evade_yell"])
        for sid in m.summons:
            s = m.zone.entities.get(sid)
            if s:
                m.zone.remove(s)
        m.summons = []

    def mob_evade(self, m: Mob, t: float, dt: float):
        hx, hz, hr = m.home
        if self.move_towards(m, hx, hz, 10.0, dt, 0.3) or t - m.evade_t > 12:
            m.state = "idle"
            if m.dist_xz(hx, hz) > 1:
                m.set_pos(hx, m.zone.height(hx, hz), hz)
            m.r = hr
            m.hp = m.max_hp
            m.next_wander = t + random.uniform(4, 10)
            m.mark("hp", "st", "p")

    def mob_flee(self, m: Mob, t: float, dt: float):
        tgt = m.zone.players.get(m.target) if m.target else None
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

    def mob_combat(self, m: Mob, t: float, dt: float):
        zone = m.zone
        tpl = m.tpl
        for pid in list(m.threat):
            p = zone.players.get(pid)
            if not p or p.dead:
                del m.threat[pid]
        if not m.threat:
            self.start_evade(m)
            return
        hx, hz, _ = m.home
        leash = tpl.get("leash") or (90 if zone.is_instance else 60)
        if m.dist_xz(hx, hz) > leash:
            self.start_evade(m)
            return
        if tpl.get("family") == "humanoid" and not m.fled and not tpl.get("elite") \
                and m.hp < m.max_hp * 0.15:
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
        if m.stunned:
            return
        if m.cast:
            self.face(m, target)
            return
        d = m.dist(target)
        reach = m.radius + target.radius + 1.6
        # Spezialfähigkeiten
        for ab in tpl["abilities"]:
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
                              "tid": target.id, "kind": "ranged", "icon": "bolt"}
                    m.mark("cast")
                else:
                    self.mob_ranged_hit(m, target, rng)
            return
        if d > reach:
            if not m.rooted:
                self.move_towards(m, target.x, target.z, RUN_SPEED * 0.97 * m.speed_mult(), dt, reach - 0.4)
            return
        self.face(m, target)
        if t >= m.swing_ready:
            haste = 1.0 + sum(a.haste for a in m.auras)
            m.swing_ready = t + tpl.get("speed", 2.0) / haste
            self.mob_melee(m, target, 1.0, None)

    def mob_melee(self, m: Mob, target: Player, mult: float, ab_name: str | None):
        front = target.facing(m)
        out = C.melee_outcome(m, target, front)
        if out in ("miss", "dodge", "parry"):
            self.miss_event(m, target, out, ab_name)
            return
        dmg = C.mob_melee_damage(m, mult)
        kind = "hit"
        if out == "crit":
            dmg *= 2
            kind = "crit"
        elif out == "block":
            dmg = max(0, dmg - target.stats.get("block_value", 5))
            kind = "block"
            if dmg <= 0:
                self.miss_event(m, target, "block", ab_name)
                return
        self.damage(m, target, dmg, "physical", ab_name, kind)

    def mob_ranged_hit(self, m: Mob, target: Player, rng: dict):
        zone = m.zone
        d = m.dist(target)
        speed = 30.0
        zone.emit_fx(m.x, m.z, {"k": "proj", "from": m.id, "to": target.id, "sp": speed,
                               "school": rng["school"], "name": rng["name"]})
        tid = target.id

        def hit():
            tgt = zone.players.get(tid)
            if not tgt or tgt.dead or m.dead:
                return
            if rng["school"] == "physical":
                out = C.melee_outcome(m, tgt, False)
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

        zone.schedule(d / speed, hit)

    def finish_mob_cast(self, m: Mob):
        c = m.cast
        m.cast = None
        m.mark("cast")
        if c["kind"] == "ranged":
            tgt = m.zone.players.get(c["tid"])
            rng = m.tpl.get("ranged")
            if tgt and tgt.alive and rng and m.dist(tgt) <= rng["range"] + 5:
                self.mob_ranged_hit(m, tgt, rng)
        elif c["kind"] == "telegraph":
            pass  # Schaden wird über Timer ausgelöst

    def try_mob_ability(self, m: Mob, ab: dict, target: Player, d: float, reach: float, t: float) -> bool:
        aid = ab["id"]
        if ab.get("once") and aid in m.ab_used:
            return False
        if ab.get("hp_below") and m.hp > m.max_hp * ab["hp_below"]:
            return False
        if not ab.get("once") and t < m.ab_next.get(aid, 0):
            return False
        if t < m.cast_lock_until and ab["kind"] not in ("summon", "enrage"):
            return False
        kind = ab["kind"]
        zone = m.zone
        if kind == "strike":
            if d > reach:
                return False
            m.ab_next[aid] = t + ab["cd"]
            self.face(m, target)
            self.mob_melee(m, target, ab["mult"], ab["name"])
            return False   # Schlag ersetzt keinen Bewegungs-Tick
        if ab.get("once"):
            m.ab_used.add(aid)
        m.ab_next[aid] = t + ab.get("cd", 10)
        if ab.get("yell"):
            self.yell(m, ab["yell"])
        if kind == "enrage":
            m.add_aura(Aura("ewiger_zorn", ab["name"], m.id, t + 3600, 3600, icon="enrage", color="#ff3030",
                            enrage=0.5, haste=0.3))
            zone.emit_fx(m.x, m.z, {"k": "enrage", "id": m.id})
            return False
        if kind == "summon":
            for i in range(ab.get("count", 2)):
                a = i / max(1, ab.get("count", 2)) * math.tau
                sx, sz = zone.walkable_clamp(m.x + math.cos(a) * 5, m.z + math.sin(a) * 5)
                add = Mob(MOBS[ab["summon"]], sx, sz, 0)
                add.y = zone.height(sx, sz)
                add.owner_boss = m.id
                add.respawn_at = 0
                zone.add(add)
                m.summons.append(add.id)
                zone.emit_fx(sx, sz, {"k": "summon", "x": sx, "z": sz})
                for pid, v in m.threat.items():
                    add.threat[pid] = 1.0
                p0 = zone.players.get(target.id)
                if p0:
                    add.tap = m.tap
                    self.engage(add, p0)
            return False
        # Bodenmarkierungen (Telegraphen)
        warn = ab.get("warn", 1.5)
        shapes = []
        if kind == "telegraph_circle_self":
            shapes.append({"shape": "circle", "x": m.x, "z": m.z, "r": ab["radius"]})
        elif kind == "telegraph_cone":
            if d > ab["radius"]:
                m.ab_next[aid] = t + 1.0
                return False
            rot = m.angle_to(target)
            m.r = rot
            m.mark("p")
            shapes.append({"shape": "cone", "x": m.x, "z": m.z, "r": ab["radius"], "rot": rot,
                           "ang": math.radians(ab["angle"])})
        elif kind == "telegraph_circles_players":
            cands = [zone.players[pid] for pid in m.threat if pid in zone.players]
            random.shuffle(cands)
            for p in cands[: ab.get("count", 1)]:
                shapes.append({"shape": "circle", "x": p.x, "z": p.z, "r": ab["radius"]})
        if not shapes:
            return False
        is_self_cast = kind in ("telegraph_circle_self", "telegraph_cone")
        if is_self_cast:
            m.cast = {"name": ab["name"], "start": t, "end": t + warn, "kind": "telegraph", "school": ab.get("school", "physical"),
                      "icon": "warn", "uninterruptible": True}
            m.mark("cast")
        for s in shapes:
            zone.emit_fx(s["x"], s["z"], {"k": "tele", "dur": warn, "name": ab["name"], **{k: round(v, 3) if isinstance(v, float) else v for k, v in s.items()}})

        def boom():
            if m.dead or m.state != "combat":
                return
            for p in list(zone.players.values()):
                if p.dead:
                    continue
                for s in shapes:
                    if self._in_shape(p, s):
                        if ab.get("flat"):
                            dmg = ab["flat"] * random.uniform(0.9, 1.1)
                        else:
                            dmg = C.mob_melee_damage(m, ab.get("mult", 1.0))
                        self.damage(m, p, dmg, ab.get("school", "physical"), ab["name"], "hit")
                        break
            for s in shapes:
                zone.emit_fx(s["x"], s["z"], {"k": "boom", "shape": s["shape"], "x": round(s["x"], 2),
                                              "z": round(s["z"], 2), "r": s["r"], "school": ab.get("school", "physical")})

        zone.schedule(warn, boom)
        return True

    @staticmethod
    def _in_shape(p: Unit, s: dict) -> bool:
        dx, dz = p.x - s["x"], p.z - s["z"]
        dist = math.hypot(dx, dz)
        if dist > s["r"] + p.radius:
            return False
        if s["shape"] == "circle":
            return True
        ang = math.atan2(-dx, -dz)
        diff = (ang - s["rot"] + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) <= s["ang"] / 2 or dist < 1.2

    # ------------------------------------------------------------------ NPCs
    def npc_tick(self, n: Npc, t: float, dt: float):
        tpl = n.tpl
        if t < n.talk_until:
            return
        if n.talk_until and t >= n.talk_until:
            n.talk_until = 0
            if not tpl.get("wander"):
                n.r = n.home[2]
                n.mark("p")
        if tpl.get("wander"):
            if n.wander_to:
                if self.move_towards(n, n.wander_to[0], n.wander_to[1], 1.6, dt, 0.2):
                    n.wander_to = None
                    n.next_wander = t + random.uniform(4, 10)
            elif t >= n.next_wander:
                hx, hz, _ = n.home
                a = random.uniform(0, math.tau)
                d = random.uniform(1, tpl["wander"])
                n.wander_to = (hx + math.cos(a) * d, hz + math.sin(a) * d)
        if tpl.get("barks") and t >= n.next_bark:
            n.next_bark = t + random.uniform(35, 80)
            if any(p.dist(n) < 32 for p in n.zone.players.values()):
                self.mob_say(n, random.choice(tpl["barks"]), 36)

    # ------------------------------------------------------------------ Auren
    def update_auras(self, u: Unit, t: float):
        changed = False
        for a in list(u.auras):
            if a.dot and t >= a.dot["next"] and not u.dead:
                a.dot["next"] += a.dot["interval"]
                src = self.find_unit(u.zone, a.src) or u
                self.damage(src, u, a.dot["amount"], a.dot["school"], a.name, "hit", periodic=True)
                if u.dead:
                    return
            if t >= a.expires:
                u.auras.remove(a)
                changed = True
                if a.taunt and isinstance(u, Mob):
                    u.taunt_by = None
        if changed:
            u.mark("au")
            if isinstance(u, Player):
                u.recalc()
                self.send_stats(u)

    def find_unit(self, zone: Zone | None, uid: int) -> Unit | None:
        if zone is None:
            return None
        return zone.entities.get(uid)

    # ------------------------------------------------------------------ Spieler-Tick
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
                if p.cast and (t >= c["end"] or c["ticks_left"] <= 0):
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
            p.hp = min(p.max_hp, p.hp + max(1, int(st["hp_regen"] * (3 if p.sitting else 1))))
            changed = True
        if p.power_type == "mana" and p.power < p.max_power and t - p.last_mana_spend >= 5.0:
            p.power = min(p.max_power, p.power + st["mp_regen"])
            changed = True
        if p.power_type == "rage" and not p.combat and p.power > 0:
            p.power = max(0, p.power - 2)
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
        if not tgt or tgt.dead or not tgt.hostile or getattr(tgt, "hidden", False):
            p.auto_attack = False
            return
        if t < p.swing_ready or p.stunned or (p.cast and not p.cast.get("allow_swing")):
            return
        if p.dist(tgt) > p.radius + tgt.radius + 3.2:
            if t - p.out_of_range_msg > 3:
                p.out_of_range_msg = t
                self.err(p, "Ihr seid zu weit entfernt.")
            p.swing_ready = t + 0.2
            return
        if not p.facing(tgt):
            if t - p.out_of_range_msg > 3:
                p.out_of_range_msg = t
                self.err(p, "Ihr müsst Euer Ziel ansehen.")
            p.swing_ready = t + 0.2
            return
        p.swing_ready = t + p.stats["speed"]
        if p.sitting:
            p.sitting = False
            p.mark("st")
        out = C.melee_outcome(p, tgt, tgt.facing(p))
        if out in ("miss", "dodge", "parry"):
            self.miss_event(p, tgt, out, None)
            if isinstance(tgt, Mob):
                self.add_threat(tgt, p, 1)
            return
        dmg = C.player_melee_damage(p)
        kind = "hit"
        if out == "crit":
            dmg *= 2
            kind = "crit"
        dealt = self.damage(p, tgt, dmg, "physical", None, kind)
        if p.power_type == "rage" and dealt:
            gain = 7.5 * dealt / C.rage_conversion(p.level)
            p.power = min(p.max_power, p.power + gain)
            p.mark("pw")

    # ------------------------------------------------------------------ Fähigkeiten
    def ability_error(self, p: Player, ab: dict, tgt: Unit | None, moving: bool) -> str | None:
        t = now()
        if p.dead:
            return "Ihr seid tot."
        if p.stunned:
            return "Ihr seid betäubt."
        if p.cast:
            return "Ihr seid gerade beschäftigt."
        if ab["level"] > p.level:
            return "Diese Fähigkeit habt Ihr noch nicht erlernt."
        if ab.get("gcd") and t < p.gcd_until:
            return "Diese Fähigkeit ist noch nicht bereit."
        if t < p.cooldowns.get(ab["id"], 0):
            return "Diese Fähigkeit ist noch nicht bereit."
        cost = ability_cost(ab, p.level)
        if p.power < cost:
            return "Nicht genug Wut." if p.power_type == "rage" else "Nicht genug Mana."
        if ab.get("cast", 0) > 0 and moving:
            return "Ihr könnt nicht zaubern, während Ihr Euch bewegt."
        if ab.get("needs_shield") and not p.has_shield():
            return "Dafür braucht Ihr einen Schild."
        if ab.get("no_combat") and p.combat:
            return "Ihr befindet Euch im Kampf."
        if ab.get("charge") and p.rooted:
            return "Ihr könnt Euch nicht bewegen."
        if ab["target"] == "enemy":
            if tgt is None:
                return "Ihr habt kein Ziel."
            if not tgt.hostile or not isinstance(tgt, Mob):
                return "Ungültiges Ziel."
            if tgt.dead:
                return "Euer Ziel ist tot."
            d = p.dist(tgt) - tgt.radius
            rng = ability_range(ab) + (p.radius + 1.2 if ab["range"] == "melee" else 0.5)
            if d > rng:
                return "Außer Reichweite."
            if d < ab.get("min_range", 0):
                return "Ihr seid zu nah."
            if not ab.get("charge") and not ab.get("taunt") and not p.facing(tgt):
                return "Ihr müsst Euer Ziel ansehen."
            if ab.get("execute") and tgt.hp > tgt.max_hp * ab["execute"]:
                return "Das könnt Ihr erst bei geschwächten Zielen einsetzen."
        return None

    def use_ability(self, p: Player, ab_id: str, tid: int | None):
        ab = ABILITIES.get(ab_id)
        if not ab or ab["cls"] != p.class_id:
            return
        if tid is not None and tid != p.target:
            p.target = tid
            p.mark("tg")
        tgt = self.find_unit(p.zone, p.target) if ab["target"] == "enemy" and p.target else None
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
        if ab.get("gcd"):
            p.gcd_until = t + GCD
        cast = ab.get("cast", 0)
        if ab["range"] == "melee" and tgt:
            p.auto_attack = True
        if cast > 0:
            p.cast = {"kind": "ability", "ab": ab_id, "name": ab["name"], "start": t, "end": t + cast,
                      "tid": tgt.id if tgt else None, "icon": ab["icon"], "school": ab["school"],
                      "channel": ab.get("channel", False)}
            if ab.get("channel"):
                self.spend(p, ab)
                ticks = ab.get("ticks", 3)
                p.cast.update({"ticks_left": ticks, "interval": cast / ticks, "next_tick": t + cast / ticks})
            p.mark("cast")
            self.send_cd(p, ab_id)
            return
        self.spend(p, ab)
        self.execute_ability(p, ab, tgt)
        self.send_cd(p, ab_id)

    def spend(self, p: Player, ab: dict):
        cost = ability_cost(ab, p.level)
        if cost:
            if ab.get("execute"):
                cost = p.power
            p.power = max(0, p.power - cost)
            if p.power_type == "mana":
                p.last_mana_spend = now()
            p.mark("pw")
        if ab.get("cd"):
            p.cooldowns[ab["id"]] = now() + ab["cd"]

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
                if p.dist(tgt) - tgt.radius > ability_range(ab) + 3:
                    self.err(p, "Außer Reichweite.")
                    return
            cost = ability_cost(ab, p.level)
            if p.power < cost:
                self.err(p, "Nicht genug Mana.")
                return
            self.spend(p, ab)
            self.execute_ability(p, ab, tgt)
        elif c["kind"] == "gather":
            self.finish_gather(p, c)

    def interrupt(self, u: Unit, lock: float = 0.0, by: Unit | None = None):
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
        return True

    def spell_damage(self, p: Player, ab: dict, tgt: Unit, mult: float = 1.0) -> tuple[int, str]:
        lo, hi = scaled_range(ab["dmg"], p.level)
        base = random.randint(lo, hi) * mult
        if ab["school"] != "physical":
            base += ab.get("coef", 0) * p.stats.get("sp", 0) * mult
            out = C.spell_outcome(p, tgt)
            if out == "crit":
                base *= 1.5
        else:
            base += p.stats.get("ap", 0) * 0.08
            out = C.melee_outcome(p, tgt, tgt.facing(p))
            if out == "crit":
                base *= 2
            elif out in ("block",):
                out = "hit"
        return int(base), out

    def apply_debuffs(self, p: Player, ab: dict, tgt: Unit):
        t = now()
        lvl = p.level
        if ab.get("slow"):
            tgt.add_aura(Aura(ab["id"], ab["name"], p.id, t + ab["duration"], ab["duration"], icon=ab["icon"],
                              color=ab["color"], debuff=True, slow=ab["slow"]))
        if ab.get("root"):
            tgt.add_aura(Aura(ab["id"], ab["name"], p.id, t + ab["root"], ab["root"], icon=ab["icon"],
                              color=ab["color"], debuff=True, root=True))
        if ab.get("dot"):
            per_tick = scaled(ab["dot"], lvl)
            dur = ab.get("dot_dur", 4)
            tgt.add_aura(Aura(ab["id"] + "_dot", ab["name"], p.id, t + dur + 0.05, dur, icon=ab["icon"],
                              color=ab["color"], debuff=True,
                              dot={"amount": per_tick, "school": ab["school"], "interval": 2.0, "next": t + 2.0}))

    def hit_with(self, p: Player, ab: dict, tgt: Unit, projectile: bool, mult: float = 1.0):
        """Schadensfähigkeit gegen ein Ziel (mit optionalem Projektilflug)."""
        zone = p.zone
        dmg, out = self.spell_damage(p, ab, tgt, mult)
        if ab.get("execute"):
            dmg += int(ab.get("rage_mult", 0) * p.power)
        threat_mult = ab.get("threat_mult", 1.0)
        tid = tgt.id

        def land():
            target = zone.entities.get(tid)
            if not target or target.dead:
                return
            if out in ("miss", "dodge", "parry"):
                kind = "resist" if ab["school"] != "physical" and out == "miss" else out
                self.miss_event(p, target, kind, ab["name"], ab["school"])
                if isinstance(target, Mob):
                    self.add_threat(target, p, 1)
                return
            self.damage(p, target, dmg, ab["school"], ab["name"], "crit" if out == "crit" else "hit",
                        threat_mult=threat_mult, extra_threat=ab.get("threat", 0))
            if not target.dead:
                self.apply_debuffs(p, ab, target)
                if ab.get("interrupt") and target.cast:
                    self.interrupt(target, ab["interrupt"], p)

        if projectile:
            speed = float(ab.get("projectile", 25))
            zone.emit_fx(p.x, p.z, {"k": "proj", "from": p.id, "to": tid, "sp": speed, "school": ab["school"],
                                    "ab": ab["id"]})
            zone.schedule(max(0.05, p.dist(tgt) / speed), land)
        else:
            land()

    def execute_ability(self, p: Player, ab: dict, tgt: Unit | None):
        t = now()
        zone = p.zone
        lvl = p.level
        aid = ab["id"]
        if ab.get("charge") and tgt:
            dx, dz = tgt.x - p.x, tgt.z - p.z
            d = math.hypot(dx, dz) or 1
            stop = tgt.radius + p.radius + 1.0
            nx, nz = tgt.x - dx / d * stop, tgt.z - dz / d * stop
            r = math.atan2(-dx, -dz)
            zone.emit_fx(p.x, p.z, {"k": "charge", "id": p.id, "x": round(nx, 2), "z": round(nz, 2)})
            self.teleport(p, nx, nz, r, kind="charge")
            p.power = min(p.max_power, p.power + scaled(ab["rage_gain"], lvl))
            p.mark("pw")
            tgt.add_aura(Aura("ansturm_betaeubung", "Betäubt", p.id, t + ab["stun"], ab["stun"], icon="stun",
                              color="#ffd24a", debuff=True, stun=True))
            if tgt.cast:
                self.interrupt(tgt, 0, p)
            self.add_threat(tgt, p, 5)
            p.auto_attack = True
            p.swing_ready = min(p.swing_ready, t + 0.3)
            return
        if ab.get("taunt") and tgt and isinstance(tgt, Mob):
            top = max(tgt.threat.values(), default=0.0)
            tgt.threat[p.id] = max(tgt.threat.get(p.id, 0.0), top)
            self.add_threat(tgt, p, 1)
            tgt.taunt_by = p.id
            tgt.taunt_until = t + ab["taunt"]
            tgt.add_aura(Aura("herausforderung", ab["name"], p.id, t + ab["taunt"], ab["taunt"], icon=ab["icon"],
                              color=ab["color"], debuff=True, taunt=True))
            zone.emit_fx(tgt.x, tgt.z, {"k": "taunt", "id": tgt.id, "by": p.id})
            return
        if ab.get("buff"):
            b = ab["buff"]
            stats = {k: scaled(v, lvl) for k, v in b.get("stats", {}).items()}
            targets = [p]
            if ab["target"] == "party" and p.party:
                targets = [self.players[m] for m in p.party.members
                           if m in self.players and self.players[m].zone is zone and self.players[m].alive
                           and self.players[m].dist(p) <= ab.get("radius", 30)]
            for u in targets:
                u.add_aura(Aura(b["id"], b["name"], p.id, t + b["dur"], b["dur"], icon=ab["icon"], color=ab["color"],
                                stats=stats, chill_attackers=b.get("chill_attackers", False)))
                u.recalc()
                self.send_stats(u)
                zone.emit_fx(u.x, u.z, {"k": "buff", "id": u.id, "school": ab["school"]})
            return
        if ab.get("blink"):
            dist = ab["blink"]
            fx, fz = -math.sin(p.r), -math.cos(p.r)
            nx, nz = p.x, p.z
            steps = int(dist / 0.5)
            for _ in range(steps):
                cx, cz = nx + fx * 0.5, nz + fz * 0.5
                if zone.nav and not zone.nav.contains(cx, cz, 0.4):
                    break
                nx, nz = cx, cz
            for a in list(p.auras):
                if a.stun or a.root:
                    p.auras.remove(a)
            p.mark("au")
            zone.emit_fx(p.x, p.z, {"k": "blink", "id": p.id, "x": round(p.x, 2), "z": round(p.z, 2),
                                    "x2": round(nx, 2), "z2": round(nz, 2)})
            self.teleport(p, nx, nz, p.r, kind="blink")
            return
        if ab["target"] == "self_aoe":
            zone.emit_fx(p.x, p.z, {"k": "nova", "id": p.id, "r": ab["radius"], "school": ab["school"], "ab": aid})
            for m in list(zone.mobs_near(p.x, p.z, ab["radius"])):
                if m.hostile and not m.look.get("critter"):
                    self.hit_with(p, ab, m, projectile=False)
            return
        if tgt is None:
            return
        if ab.get("weapon"):
            out = C.melee_outcome(p, tgt, tgt.facing(p))
            if out in ("miss", "dodge", "parry"):
                self.miss_event(p, tgt, out, ab["name"])
                if isinstance(tgt, Mob):
                    self.add_threat(tgt, p, ab.get("threat", 0))
                return
            dmg = C.player_melee_damage(p, scaled(ab["bonus"], lvl))
            kind = "hit"
            if out == "crit":
                dmg *= 2
                kind = "crit"
            zone.emit_fx(tgt.x, tgt.z, {"k": "strike", "id": p.id, "to": tgt.id, "ab": aid})
            self.damage(p, tgt, dmg, "physical", ab["name"], kind, extra_threat=ab.get("threat", 0))
            return
        if ab.get("channel"):
            return  # Schaden in channel_tick
        if "dmg" in ab:
            proj = bool(ab.get("projectile"))
            if not proj:
                zone.emit_fx(tgt.x, tgt.z, {"k": "impact", "id": tgt.id, "school": ab["school"], "ab": aid})
            self.hit_with(p, ab, tgt, projectile=proj)

    def channel_tick(self, p: Player, c: dict):
        ab = ABILITIES[c["ab"]]
        tgt = self.find_unit(p.zone, c["tid"])
        if not tgt or tgt.dead:
            p.cast = None
            p.mark("cast")
            return
        self.hit_with(p, ab, tgt, projectile=True)

    # ------------------------------------------------------------------ Sammeln
    def obj_usable(self, p: Player, o: GameObj) -> bool:
        if ITEMS[o.item].get("quest"):
            return self.player_needs_item(p, o.item)
        return True

    def finish_gather(self, p: Player, c: dict):
        o = self.find_unit(p.zone, c["obj"])
        if not isinstance(o, GameObj) or not o.available or p.dist(o) > 6:
            return
        if not self.obj_usable(p, o):
            self.err(p, "Das braucht Ihr nicht.")
            return
        if not p.add_items([(o.item, 1)]):
            self.err(p, "Euer Inventar ist voll.")
            return
        o.available = False
        o.hidden = True
        o.respawn_at = now() + o.respawn
        self.sys(p, f"Ihr erhaltet: [{ITEMS[o.item]['name']}].")
        self.send_inventory(p)
        self.send_quests(p)
