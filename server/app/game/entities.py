"""Spielobjekte: Spieler, Gegner (Mobs), NPCs und Sammelobjekte."""
from __future__ import annotations

import itertools
import math
import random
import time
from dataclasses import dataclass, field

from .content.classes import CLASSES, base_stats
from .content.items import EQUIP_SLOTS, ITEMS
from .content.mobs import mob_armor, mob_damage, mob_max_hp

_ids = itertools.count(1)
BAG_SLOTS = 24
RUN_SPEED = 7.0


def new_id() -> int:
    return next(_ids)


def now() -> float:
    return time.monotonic()


@dataclass
class Aura:
    id: str
    name: str
    src: int
    expires: float
    dur: float
    icon: str = "buff"
    color: str = "#ffffff"
    debuff: bool = False
    stats: dict = field(default_factory=dict)
    slow: float = 0.0
    root: bool = False
    stun: bool = False
    dot: dict | None = None          # {"amount": n, "school": s, "interval": 1.0, "next": t, "name": ...}
    enrage: float = 0.0              # Schadensbonus (0.5 = +50 %)
    haste: float = 0.0               # Angriffstempo-Bonus
    chill_attackers: bool = False
    taunt: bool = False
    food: dict | None = None         # {"hp": pro Sek., "mp": pro Sek.}

    def client(self, t: float) -> list:
        return [self.id, self.name, round(max(0.0, self.expires - t), 1), round(self.dur, 1), self.icon,
                self.color, 1 if self.debuff else 0]


class Unit:
    kind = "unit"

    def __init__(self, name: str, level: int, x: float, z: float, r: float = 0.0):
        self.id = new_id()
        self.name = name
        self.title = ""
        self.level = level
        self.x, self.y, self.z, self.r = x, 0.0, z, r
        self.zone = None
        self.hp = 1
        self.max_hp = 1
        self.power = 0
        self.max_power = 0
        self.power_type = None
        self.target: int | None = None
        self.auras: list[Aura] = []
        self.cast: dict | None = None
        self.dead = False
        self.radius = 0.5
        self.scale = 1.0
        self.model = "human"
        self.look: dict = {}
        self.hostile = False
        self.dirty: set[str] = set()
        self.combat = False
        self.emote: str | None = None
        self.cast_lock_until = 0.0

    # ------------------------------------------------------------------ Hilfen
    def mark(self, *fields: str):
        self.dirty.update(fields)

    def set_pos(self, x: float, y: float, z: float, r: float | None = None):
        self.x, self.y, self.z = x, y, z
        if r is not None:
            self.r = r
        self.mark("p")

    def dist(self, o: "Unit") -> float:
        return math.hypot(self.x - o.x, self.z - o.z)

    def dist_xz(self, x: float, z: float) -> float:
        return math.hypot(self.x - x, self.z - z)

    def angle_to(self, o) -> float:
        return math.atan2(-(o.x - self.x), -(o.z - self.z))

    def facing(self, o: "Unit", arc: float = math.pi) -> bool:
        """Steht o im Sichtkegel (Standard: vordere 180°)?"""
        if self.dist(o) < 0.6:
            return True
        diff = (self.angle_to(o) - self.r + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) <= arc / 2

    @property
    def alive(self) -> bool:
        return not self.dead

    def has_aura(self, aura_id: str) -> Aura | None:
        for a in self.auras:
            if a.id == aura_id:
                return a
        return None

    def add_aura(self, aura: Aura):
        self.remove_aura(aura.id)
        self.auras.append(aura)
        self.mark("au")

    def remove_aura(self, aura_id: str) -> bool:
        before = len(self.auras)
        self.auras = [a for a in self.auras if a.id != aura_id]
        if len(self.auras) != before:
            self.mark("au")
            return True
        return False

    @property
    def stunned(self) -> bool:
        return any(a.stun for a in self.auras)

    @property
    def rooted(self) -> bool:
        return any(a.root for a in self.auras) or self.stunned

    def speed_mult(self) -> float:
        slow = max((a.slow for a in self.auras), default=0.0)
        return max(0.2, 1.0 - slow)

    def aura_stat(self, stat: str) -> float:
        return sum(a.stats.get(stat, 0) for a in self.auras)

    def client_auras(self, t: float) -> list:
        return [a.client(t) for a in self.auras]

    def state_flags(self) -> int:
        f = 0
        if self.dead:
            f |= 1
        if self.combat:
            f |= 2
        return f

    def spawn_info(self) -> dict:
        return {
            "id": self.id, "k": self.kind, "name": self.name, "title": self.title, "lvl": self.level,
            "model": self.model, "scale": self.scale, "look": self.look, "rad": self.radius,
            "p": [round(self.x, 2), round(self.y, 2), round(self.z, 2), round(self.r, 3)],
            "hp": self.hp, "mhp": self.max_hp, "pw": int(self.power), "mpw": self.max_power, "pt": self.power_type,
            "tg": self.target, "hostile": self.hostile, "st": self.state_flags(),
            "cast": self.cast_client(), "au": self.client_auras(now()), "emote": self.emote,
        }

    def cast_client(self):
        if not self.cast:
            return None
        c = self.cast
        return {"name": c["name"], "dur": round(c["end"] - c["start"], 2), "left": round(c["end"] - now(), 2),
                "ch": c.get("channel", False), "icon": c.get("icon"), "school": c.get("school"), "tg": c.get("tid")}

    def delta(self, fields: set[str], for_self: bool = False) -> dict:
        d = {"id": self.id}
        t = now()
        for f in fields:
            if f == "p":
                if not for_self:
                    d["p"] = [round(self.x, 2), round(self.y, 2), round(self.z, 2), round(self.r, 3)]
            elif f == "hp":
                d["hp"] = self.hp
                d["mhp"] = self.max_hp
            elif f == "pw":
                d["pw"] = int(self.power)
                d["mpw"] = self.max_power
            elif f == "tg":
                d["tg"] = self.target
            elif f == "st":
                d["st"] = self.state_flags()
            elif f == "cast":
                d["cast"] = self.cast_client()
            elif f == "au":
                d["au"] = self.client_auras(t)
            elif f == "lvl":
                d["lvl"] = self.level
            elif f == "look":
                d["look"] = self.look
            elif f == "emote":
                d["emote"] = self.emote
            elif f == "name":
                d["name"] = self.name
        return d


# ============================================================================== Spieler
class Player(Unit):
    kind = "player"

    def __init__(self, record, session):
        super().__init__(record.name, record.level, record.x, record.z, record.rot)
        self.session = session
        self.user_id = record.user_id
        self.char_id = record.id
        self.class_id = record.class_id
        self.cls = CLASSES[record.class_id]
        self.xp = record.xp
        self.copper = record.copper
        self.zone_id = record.zone or "gruenmark"
        self.y = record.y
        self.look = dict(record.look or {})
        self.bags: list = list(record.inventory or [])
        self.bags = (self.bags + [None] * BAG_SLOTS)[:BAG_SLOTS]
        self.equipment: dict = {k: v for k, v in (record.equipment or {}).items() if k in EQUIP_SLOTS and v in ITEMS}
        q = record.quests or {}
        self.quests_active: dict[str, list[int]] = dict(q.get("active", {}))
        self.quests_done: set[str] = set(q.get("done", []))
        self.played_seconds = record.played_seconds or 0
        self.login_time = now()
        self.power_type = self.cls["resource"]
        self.model = "human"
        self.radius = 0.5
        self.hostile = False
        self.stats: dict = {}
        self.cooldowns: dict[str, float] = {}
        self.gcd_until = 0.0
        self.potion_cd_until = 0.0
        self.auto_attack = False
        self.swing_ready = 0.0
        self.combat_until = 0.0
        self.last_mana_spend = -100.0
        self.party = None
        self.known: set[int] = set()
        self.flag_cache: dict[int, dict] = {}
        self.eating: dict | None = None
        self.sitting = False
        self.loot_open: int | None = None
        self.moving = False
        self.last_move_t = now()
        self.move_budget = 12.0                 # Bewegungsprüfung (Token-Bucket in Metern)
        self.move_budget_t = now()
        self.portal_lock = 0.0
        self.invite_from: int | None = None
        self.chat_times: list[float] = []
        self.next_regen = now() + 1.0
        self.out_of_range_msg = 0.0
        self.taunt_target = None
        self.ready = False
        self.recalc(full=record.hp < 0)
        if record.hp >= 0:
            self.hp = max(1, min(self.max_hp, record.hp))
            self.power = max(0, min(self.max_power, record.res)) if record.res >= 0 else self.max_power
        if self.power_type == "rage":
            self.power = 0
        self.update_gear_look()

    # ------------------------------------------------------------------ Werte
    def weapon(self) -> dict:
        it = ITEMS.get(self.equipment.get("main_hand") or "")
        if it and it["type"] == "weapon":
            return {"min": it["dmg"][0], "max": it["dmg"][1], "speed": it["speed"]}
        return {"min": 1, "max": 3, "speed": 2.0}

    def has_shield(self) -> bool:
        it = ITEMS.get(self.equipment.get("off_hand") or "")
        return bool(it and it.get("sub") == "schild")

    def recalc(self, full: bool = False):
        st = base_stats(self.class_id, self.level)
        st.update({"armor": 0, "sp": 0, "ap": 0})
        for slot, item_id in self.equipment.items():
            it = ITEMS.get(item_id)
            if not it:
                continue
            for k, v in it.get("stats", {}).items():
                st[k] = st.get(k, 0) + v
        for a in self.auras:
            for k, v in a.stats.items():
                st[k] = st.get(k, 0) + v
        lvl = self.level
        st["armor"] += st["agi"] * 2
        if self.class_id == "ritter":
            st["ap"] += st["str"] * 2 + lvl * 2
            st["parry"] = 5.0
        else:
            st["ap"] += st["str"]
            st["parry"] = 0.0
        st["crit"] = 5.0 + st["agi"] / 20.0
        st["spell_crit"] = 5.0 + st["int"] / 60.0 + (1.0 if self.class_id == "magier" else 0.0)
        st["dodge"] = 3.0 + st["agi"] / 20.0
        st["block"] = 5.0 if self.has_shield() else 0.0
        st["block_value"] = 5 + st["str"] // 4
        old_max_hp, old_max_pw = self.max_hp, self.max_power
        self.max_hp = int(20 + self.cls["hp_per_level"] * lvl + st["sta"] * 10)
        if self.power_type == "mana":
            self.max_power = int(40 + st["int"] * 15)
        else:
            self.max_power = 100
        st["hp_regen"] = 0.6 + st["spi"] * 0.12
        st["mp_regen"] = 2.0 + st["spi"] * 0.35
        w = self.weapon()
        bonus = st["ap"] / 14.0 * w["speed"]
        st["dmg_min"] = int(w["min"] + bonus)
        st["dmg_max"] = int(w["max"] + bonus)
        st["speed"] = w["speed"]
        self.stats = st
        if full:
            self.hp = self.max_hp
            self.power = self.max_power if self.power_type == "mana" else 0
        else:
            if self.max_hp > old_max_hp and old_max_hp > 1:
                self.hp = min(self.max_hp, self.hp + (self.max_hp - old_max_hp))
            self.hp = min(self.hp, self.max_hp)
            if self.power_type == "mana" and self.max_power > old_max_pw and old_max_pw > 0:
                self.power = min(self.max_power, self.power + (self.max_power - old_max_pw))
            self.power = min(self.power, self.max_power)
        self.mark("hp", "pw")

    def update_gear_look(self):
        gear = {}
        for slot in ("main_hand", "off_hand", "head", "shoulders", "back", "chest", "legs", "hands", "feet"):
            item_id = self.equipment.get(slot)
            if item_id:
                gear[slot] = item_id
        self.look["gear"] = gear
        self.look["cls"] = self.class_id
        self.mark("look")

    def state_flags(self) -> int:
        f = super().state_flags()
        if self.sitting:
            f |= 4
        return f

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["cls"] = self.class_id
        return d

    # ------------------------------------------------------------------ Inventar
    def count_item(self, item_id: str) -> int:
        return sum(s[1] for s in self.bags if s and s[0] == item_id)

    def can_add(self, items: list[tuple[str, int]]) -> bool:
        bags = [list(s) if s else None for s in self.bags]
        return self._add_to(bags, items)

    @staticmethod
    def _add_to(bags: list, items: list[tuple[str, int]]) -> bool:
        for item_id, n in items:
            stack = ITEMS[item_id].get("stack", 1)
            for s in bags:
                if n <= 0:
                    break
                if s and s[0] == item_id and s[1] < stack:
                    add = min(n, stack - s[1])
                    s[1] += add
                    n -= add
            for i in range(len(bags)):
                if n <= 0:
                    break
                if bags[i] is None:
                    add = min(n, stack)
                    bags[i] = [item_id, add]
                    n -= add
            if n > 0:
                return False
        return True

    def add_items(self, items: list[tuple[str, int]]) -> bool:
        bags = [list(s) if s else None for s in self.bags]
        if not self._add_to(bags, items):
            return False
        self.bags = bags
        return True

    def remove_item(self, item_id: str, n: int) -> int:
        removed = 0
        for i in range(len(self.bags) - 1, -1, -1):
            s = self.bags[i]
            if n <= 0:
                break
            if s and s[0] == item_id:
                take = min(n, s[1])
                s[1] -= take
                n -= take
                removed += take
                if s[1] <= 0:
                    self.bags[i] = None
        return removed

    def free_slots(self) -> int:
        return sum(1 for s in self.bags if s is None)

    # ------------------------------------------------------------------ Speichern
    def record_data(self) -> dict:
        return {
            "level": self.level, "xp": self.xp, "copper": self.copper,
            "hp": self.hp if not self.dead else max(1, self.max_hp // 2),
            "res": int(self.power) if self.power_type == "mana" else 0,
            "inventory": [list(s) if s else None for s in self.bags],
            "equipment": dict(self.equipment),
            "quests": {"active": {k: list(v) for k, v in self.quests_active.items()}, "done": sorted(self.quests_done)},
            "look": {k: v for k, v in self.look.items() if k not in ("gear", "cls")},
            "played_seconds": self.played_seconds + int(now() - self.login_time),
        }


# ============================================================================== Gegner
class Mob(Unit):
    kind = "mob"

    def __init__(self, tpl: dict, x: float, z: float, r: float = 0.0, lvl_range=None, spawn_r: float = 0.0):
        lo, hi = lvl_range or tpl["lvl"]
        super().__init__(tpl["name"], random.randint(lo, hi), x, z, r)
        self.tpl = tpl
        self.lvl_range = (lo, hi)
        self.title = tpl.get("title", "")
        self.model = tpl["model"]
        self.scale = tpl.get("scale", 1.0)
        self.radius = tpl.get("radius", 0.5)
        self.hostile = not tpl.get("critter", False)
        self.look = {"tint": tpl.get("tint"), "elite": tpl.get("elite", False), "rare": tpl.get("rare", False),
                     "boss": tpl.get("boss", False), "aggro": tpl.get("aggro", False),
                     "critter": tpl.get("critter", False), "dummy": tpl.get("dummy", False)}
        self.home = (x, z, r)
        self.spawn_r = spawn_r
        self.state = "idle"
        self.threat: dict[int, float] = {}
        self.swing_ready = 0.0
        self.ab_next: dict[str, float] = {}
        self.ab_used: set[str] = set()
        self.wander_to = None
        self.next_wander = now() + random.uniform(2, 10)
        self.tap: set[int] | None = None      # Spieler-IDs mit Beuterecht
        self.tap_owner = None
        self.loot: dict[int, dict] = {}
        self.respawn_at = 0.0
        self.corpse_until = 0.0
        self.hidden = False
        self.flee_until = 0.0
        self.fled = False
        self.taunt_by: int | None = None
        self.taunt_until = 0.0
        self.summons: list[int] = []
        self.owner_boss: int | None = None
        self.last_hit_t = 0.0
        self.evade_t = 0.0
        self.engage_t = 0.0
        self.reset_stats()

    def reset_stats(self):
        self.max_hp = mob_max_hp(self.tpl, self.level)
        self.hp = self.max_hp
        self.armor = mob_armor(self.tpl, self.level)
        self.dmg = mob_damage(self.tpl, self.level)
        self.mark("hp", "lvl")

    def state_flags(self) -> int:
        f = super().state_flags()
        if self.state == "evade":
            f |= 8
        if self.state == "flee":
            f |= 16
        return f

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["mob"] = self.tpl["id"]
        return d


# ============================================================================== NPCs
class Npc(Unit):
    kind = "npc"

    def __init__(self, tpl: dict):
        x, z = tpl["pos"]
        super().__init__(tpl["name"], tpl["lvl"], x, z, tpl["rot"])
        self.tpl = tpl
        self.npc_id = tpl["id"]
        self.title = tpl.get("title", "")
        self.model = tpl.get("model", "human")
        self.scale = tpl.get("scale", 1.0)
        self.look = dict(tpl.get("look", {}))
        self.radius = 0.5
        self.hostile = False
        self.max_hp = self.hp = 100 + 40 * self.level
        self.home = (x, z, tpl["rot"])
        self.wander_to = None
        self.next_wander = now() + random.uniform(3, 8)
        self.next_bark = now() + random.uniform(20, 60)
        self.talk_until = 0.0

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["npc"] = self.npc_id
        d["vendor"] = bool(self.tpl.get("vendor"))
        d["guard"] = self.tpl.get("guard", False)
        return d


# ============================================================================== Sammelobjekte
class GameObj(Unit):
    kind = "obj"

    NAMES = {"herb": "Wiesenkraut", "ore": "Kupferader", "gackerle": "Gackerle"}

    def __init__(self, spec: dict):
        x, z = spec["pos"]
        super().__init__(self.NAMES.get(spec["kind"], spec["kind"]), 1, x, z, random.uniform(0, math.tau))
        self.obj_kind = spec["kind"]
        self.item = spec["item"]
        self.respawn = spec.get("respawn", 45)
        self.model = spec["kind"]
        self.available = True
        self.respawn_at = 0.0
        self.max_hp = self.hp = 1
        self.hidden = False

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["obj"] = self.obj_kind
        return d
