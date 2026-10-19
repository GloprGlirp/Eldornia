"""Spielobjekte: Spieler, Gegner, Begleiter, NPCs, Sammelobjekte, Fallen und Bodeneffekte."""
from __future__ import annotations

import itertools
import math
import random
import time

from ..content.classes import CLASSES, RESOURCES

_ids = itertools.count(1)
BAG_SLOTS = 40
RUN_SPEED = 7.0
BACK_SPEED = 4.5
SPRINT_MULT = 1.35
MOUNT_SPEED = {1: 1.6, 2: 2.0}      # Faktor auf Laufgeschwindigkeit (normal / episch)


def new_id() -> int:
    return next(_ids)


def now() -> float:
    return time.monotonic()


# =============================================================================== Auren
class Aura:
    """Buff oder Debuff. Die Definition stammt aus den Inhaltsdaten (AURA(...))."""

    __slots__ = ("id", "name", "src", "expires", "dur", "icon", "debuff", "stats", "pct", "slow", "root", "stun",
                 "silence", "fear", "poly", "stealth", "immune", "dot", "hot", "absorb", "reflect", "stacks",
                 "max_stacks", "charges", "break_dmg", "taunt", "form", "marked", "parry_all", "block_all",
                 "cheat_death", "lifesteal", "chill_attackers", "reflect_melee", "dispel", "next_tick", "dmg_taken_acc",
                 "removable", "proc", "spread", "school", "ability", "food", "sleep", "extra")

    def __init__(self, d: dict, src_id: int, t: float, level: int = 1, dur: float | None = None, scale_stats=True):
        self.id = d["id"]
        self.name = d.get("name", self.id)
        self.src = src_id
        self.dur = float(dur if dur is not None else d.get("dur", 10))
        self.expires = t + self.dur
        self.icon = d.get("icon")
        self.debuff = bool(d.get("debuff", False))
        stats = d.get("stats", {})
        self.stats = {}
        for k, v in stats.items():
            self.stats[k] = (v[0] + v[1] * level) if isinstance(v, (tuple, list)) else v
        self.pct = dict(d.get("pct", {}))
        self.slow = float(d.get("slow", 0.0))
        self.root = bool(d.get("root", False))
        self.stun = bool(d.get("stun", False))
        self.silence = bool(d.get("silence", False))
        self.fear = bool(d.get("fear", False))
        self.poly = bool(d.get("poly", False))
        self.sleep = bool(d.get("sleep", False))
        self.stealth = bool(d.get("stealth", False))
        self.immune = bool(d.get("immune", False))
        self.dot = dict(d["dot"]) if d.get("dot") else None
        self.hot = dict(d["hot"]) if d.get("hot") else None
        self.absorb = 0.0
        self.reflect = d.get("reflect")
        self.max_stacks = int(d.get("stacks", 1))
        self.stacks = 1
        self.charges = int(d.get("charges", 0))
        self.break_dmg = d.get("break_dmg")
        self.taunt = bool(d.get("taunt", False))
        self.form = d.get("form")
        self.marked = bool(d.get("marked", False))
        self.parry_all = bool(d.get("parry_all", False))
        self.block_all = bool(d.get("block_all", False))
        self.cheat_death = bool(d.get("cheat_death", False))
        self.lifesteal = float(d.get("lifesteal", 0.0))
        self.chill_attackers = float(d.get("chill_attackers", 0.0))
        self.reflect_melee = float(d.get("reflect_melee", 0.0))
        self.dispel = d.get("dispel", "magic" if self.debuff else None)
        self.removable = bool(d.get("removable", not self.debuff))
        self.proc = d.get("proc")
        self.spread = d.get("spread")
        self.school = d.get("school")
        self.ability = d.get("ability")
        self.food = d.get("food")
        self.extra = {}
        self.dmg_taken_acc = 0.0
        tick = None
        if self.dot:
            tick = self.dot.get("interval", 3)
        elif self.hot:
            tick = self.hot.get("interval", 3)
        self.next_tick = t + tick if tick else 0.0

    @property
    def cc(self) -> bool:
        return self.stun or self.root or self.fear or self.poly or self.sleep or self.silence

    def client(self, t: float) -> list:
        fl = 0
        if self.stun or self.sleep or self.poly or self.fear:
            fl |= 1
        if self.root:
            fl |= 2
        if self.silence:
            fl |= 4
        if self.stealth:
            fl |= 8
        if self.slow:
            fl |= 16
        if self.immune:
            fl |= 32
        if self.form:
            fl |= 64
        return [self.id, self.name, round(max(0.0, self.expires - t), 1), round(self.dur, 1), self.icon or "",
                1 if self.debuff else 0, self.stacks, self.src, fl, self.school or ""]


# =============================================================================== Basis
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
        self.power = 0.0
        self.max_power = 0
        self.power_type: str | None = None
        self.target: int | None = None
        self.auras: list[Aura] = []
        self.cast: dict | None = None
        self.dead = False
        self.radius = 0.5
        self.scale = 1.0
        self.model = "human"
        self.look: dict = {}
        self.hostile = False          # aus Sicht der Spieler feindlich
        self.side = "neutral"         # player | mob | neutral
        self.dirty: set[str] = set()
        self.combat = False
        self.emote: str | None = None
        self.cast_lock_until = 0.0
        self.stats: dict = {}
        self.mods: dict = {}
        self.resist: dict = {}
        self.hidden = False
        self.last_hit_t = 0.0
        self.last_reactive: dict[str, float] = {}   # block/dodge/parry/crit -> Zeitpunkt
        self.team: int | None = None   # Arena / Duell

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

    def dist3(self, o: "Unit") -> float:
        return math.sqrt((self.x - o.x) ** 2 + (self.z - o.z) ** 2 + (self.y - o.y) ** 2)

    def dist_xz(self, x: float, z: float) -> float:
        return math.hypot(self.x - x, self.z - z)

    def angle_to(self, o) -> float:
        return math.atan2(-(o.x - self.x), -(o.z - self.z))

    def angle_to_xz(self, x: float, z: float) -> float:
        return math.atan2(-(x - self.x), -(z - self.z))

    def facing(self, o: "Unit", arc: float = math.pi) -> bool:
        """Steht o im Sichtkegel (Standard: vordere 180°)?"""
        if self.dist(o) < 0.6:
            return True
        diff = (self.angle_to(o) - self.r + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) <= arc / 2

    def behind(self, o: "Unit") -> bool:
        """Steht self hinter o?"""
        return not o.facing(self, math.pi * 1.1)

    @property
    def alive(self) -> bool:
        return not self.dead

    def has_aura(self, aura_id: str) -> Aura | None:
        for a in self.auras:
            if a.id == aura_id:
                return a
        return None

    def add_aura(self, aura: Aura) -> Aura:
        old = self.has_aura(aura.id)
        if old and old.max_stacks > 1:
            old.stacks = min(old.max_stacks, old.stacks + 1)
            old.expires = aura.expires
            old.dur = aura.dur
            if aura.dot:
                old.dot = aura.dot
            self.mark("au")
            return old
        if old:
            self.auras.remove(old)
        self.auras.append(aura)
        self.mark("au")
        return aura

    def remove_aura(self, aura_id: str) -> bool:
        before = len(self.auras)
        self.auras = [a for a in self.auras if a.id != aura_id]
        if len(self.auras) != before:
            self.mark("au")
            return True
        return False

    def _flag(self, name: str) -> bool:
        for a in self.auras:
            if getattr(a, name):
                return True
        return False

    @property
    def stunned(self) -> bool:
        return self._flag("stun") or self._flag("sleep")

    @property
    def incapacitated(self) -> bool:
        return self._flag("stun") or self._flag("poly") or self._flag("fear") or self._flag("sleep")

    @property
    def rooted(self) -> bool:
        return self._flag("root") or self.incapacitated

    @property
    def silenced(self) -> bool:
        return self._flag("silence")

    @property
    def stealthed(self) -> bool:
        return self._flag("stealth")

    @property
    def immune(self) -> bool:
        return self._flag("immune")

    def form(self) -> str | None:
        for a in self.auras:
            if a.form:
                return a.form
        return None

    def speed_mult(self) -> float:
        slow = max((a.slow for a in self.auras), default=0.0)
        bonus = sum(a.pct.get("speed", 0) for a in self.auras) / 100.0
        return max(0.2, (1.0 - slow) * (1.0 + bonus))

    def aura_pct(self, key: str) -> float:
        return sum(a.pct.get(key, 0) * (a.stacks if key in ("iaido",) else 1) for a in self.auras)

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
        if self.stealthed:
            f |= 32
        return f

    def spawn_info(self) -> dict:
        return {
            "id": self.id, "k": self.kind, "name": self.name, "title": self.title, "lvl": self.level,
            "model": self.model, "scale": self.scale, "look": self.look, "rad": self.radius,
            "p": [round(self.x, 2), round(self.y, 2), round(self.z, 2), round(self.r, 3)],
            "hp": self.hp, "mhp": self.max_hp, "pw": int(self.power), "mpw": self.max_power, "pt": self.power_type,
            "tg": self.target, "hostile": self.hostile, "side": self.side, "st": self.state_flags(),
            "cast": self.cast_client(), "au": self.client_auras(now()), "emote": self.emote, "team": self.team,
        }

    def cast_client(self):
        if not self.cast:
            return None
        c = self.cast
        return {"name": c["name"], "dur": round(c["end"] - c["start"], 2), "left": round(c["end"] - now(), 2),
                "ch": c.get("channel", False), "icon": c.get("icon"), "school": c.get("school"), "tg": c.get("tid"),
                "ab": c.get("ab"), "ni": bool(c.get("uninterruptible")), "gp": c.get("gp")}

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
                d["pt"] = self.power_type
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
                d["title"] = self.title
            elif f == "model":
                d["model"] = self.model
                d["scale"] = self.scale
            elif f == "team":
                d["team"] = self.team
                d["hostile"] = self.hostile
        return d


# =============================================================================== Spieler
class Player(Unit):
    kind = "player"

    def __init__(self, data: dict, session):
        super().__init__(data["name"], data["level"], data["x"], data["z"], data["rot"])
        self.session = session
        self.user_id = data["user_id"]
        self.username = data.get("username", "")
        self.char_id = data["id"]
        self.class_id = data["class_id"]
        self.cls = CLASSES[self.class_id]
        self.xp = data["xp"]
        self.copper = data["copper"]
        self.zone_id = data["zone"]
        self.y = data["y"]
        self.look = dict(data.get("look") or {})
        self.base_look = {k: v for k, v in self.look.items() if k not in ("gear", "cls")}
        self.bags: list = (list(data.get("bags") or []) + [None] * BAG_SLOTS)[:BAG_SLOTS]
        self.equipment: dict = dict(data.get("equipment") or {})
        self.quests_active: dict[str, list[int]] = dict(data.get("quests_active") or {})
        self.quests_done: dict[str, float] = dict(data.get("quests_done") or {})   # quest_id -> Zeitstempel
        self.talents: dict[str, int] = dict(data.get("talents") or {})
        self.action_bars: list = list(data.get("action_bars") or [])
        self.professions: dict = dict(data.get("professions") or {})
        self.reputation: dict = dict(data.get("reputation") or {})
        self.currencies: dict = dict(data.get("currencies") or {})
        self.achievements: dict = dict(data.get("achievements") or {})
        self.collections: dict = dict(data.get("collections") or {"mounts": [], "pets": [], "titles": [], "skins": []})
        self.discovered: dict = dict(data.get("discovered") or {"stones": [], "subzones": [], "zones": []})
        self.misc: dict = dict(data.get("misc") or {})
        self.guild_id: int | None = data.get("guild_id")
        self.guild_rank: str | None = None
        self.played_seconds = data.get("played_seconds") or 0
        self.login_time = now()
        self.power_type = self.cls["resource"]
        self.model = "human"
        self.radius = 0.5
        self.side = "player"
        self.hostile = False
        self.cooldowns: dict[str, float] = {k: now() + v for k, v in (data.get("cooldowns") or {}).items() if v > 0}
        self.gcd_until = 0.0
        self.potion_cd_until = 0.0
        self.auto_attack = False
        self.swing_ready = 0.0
        self.oh_swing_ready = 0.0
        self.combat_until = 0.0
        self.last_mana_spend = -100.0
        self.party = None
        self.known: set[int] = set()
        self.flag_cache: dict[int, dict] = {}
        self.eating: dict | None = None
        self.sitting = False
        self.loot_open: int | None = None
        self.moving = False
        self.sprinting = False
        self.mounted: str | None = None
        self.mount_speed = 1.0
        self.last_move_t = now()
        self.move_budget = 14.0
        self.move_budget_t = now()
        self.portal_lock = 0.0
        self.invite_from: int | None = None
        self.guild_invite: int | None = None
        self.duel_with: int | None = None
        self.duel_invite: int | None = None
        self.trade = None
        self.chat_times: list[float] = []
        self.next_regen = now() + 1.0
        self.out_of_range_msg = 0.0
        self.ready = False
        self.combo = 0
        self.combo_target: int | None = None
        self.pets: list[int] = []
        self.companion: int | None = None
        self.queue: dict | None = None
        self.instance_key: str | None = None
        self.last_safe = (self.x, self.z)
        self.busy = False            # laufende Wirtschaftstransaktion
        self.save_dirty = True
        self.gm = bool(data.get("is_admin", False))
        self.title = self.misc.get("title_text", "")
        self.recalc_cb = None         # wird von der Welt gesetzt

    # ------------------------------------------------------------------ Waffen
    def item_def(self, slot: str) -> dict | None:
        from ..content.items import ITEMS
        inst = self.equipment.get(slot)
        if not inst:
            return None
        return ITEMS.get(inst["i"])

    def weapon(self, off: bool = False) -> dict:
        it = self.item_def("off_hand" if off else "main_hand")
        if it and it["type"] == "weapon":
            return {"min": it["dmg"][0], "max": it["dmg"][1], "speed": it["speed"], "sub": it["sub"],
                    "two": it.get("two_hand", False), "proc": it.get("proc")}
        if off:
            return {}
        return {"min": 1 + self.level // 2, "max": 3 + self.level, "speed": 2.0, "sub": "faust", "two": False, "proc": None}

    def has_shield(self) -> bool:
        it = self.item_def("off_hand")
        return bool(it and it.get("sub") == "schild")

    def dual_wielding(self) -> bool:
        it = self.item_def("off_hand")
        return bool(it and it["type"] == "weapon")

    def ranged(self) -> bool:
        it = self.item_def("main_hand")
        return bool(it and it.get("sub") in ("bogen",))

    def state_flags(self) -> int:
        f = super().state_flags()
        if self.sitting:
            f |= 4
        if self.mounted:
            f |= 64
        return f

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["cls"] = self.class_id
        d["guild"] = self.look.get("guild_name")
        return d

    # ------------------------------------------------------------------ Inventar
    def count_item(self, item_id: str) -> int:
        return sum(s["n"] for s in self.bags if s and s["i"] == item_id)

    @staticmethod
    def _add_to(bags: list, items: list[tuple], stacks: dict) -> bool:
        for entry in items:
            item_id, n = entry[0], entry[1]
            bound = entry[2] if len(entry) > 2 else False
            extra = entry[3] if len(entry) > 3 else None
            stack = stacks.get(item_id, 1)
            if stack > 1 and not extra:
                for s in bags:
                    if n <= 0:
                        break
                    if s and s["i"] == item_id and s["n"] < stack and bool(s.get("b")) == bool(bound):
                        add = min(n, stack - s["n"])
                        s["n"] += add
                        n -= add
            for i in range(len(bags)):
                if n <= 0:
                    break
                if bags[i] is None:
                    add = min(n, stack)
                    inst = {"i": item_id, "n": add}
                    if bound:
                        inst["b"] = 1
                    if extra:
                        inst.update(extra)
                    bags[i] = inst
                    n -= add
            if n > 0:
                return False
        return True

    def can_add(self, items: list[tuple]) -> bool:
        from ..content.items import ITEMS
        bags = [dict(s) if s else None for s in self.bags]
        return self._add_to(bags, items, {i[0]: ITEMS[i[0]].get("stack", 1) for i in items})

    def add_items(self, items: list[tuple]) -> bool:
        """items: [(item_id, anzahl[, gebunden[, extra])]. Alles oder nichts."""
        from ..content.items import ITEMS
        bags = [dict(s) if s else None for s in self.bags]
        if not self._add_to(bags, items, {i[0]: ITEMS[i[0]].get("stack", 1) for i in items}):
            return False
        self.bags = bags
        self.save_dirty = True
        return True

    def remove_item(self, item_id: str, n: int) -> int:
        removed = 0
        for i in range(len(self.bags) - 1, -1, -1):
            s = self.bags[i]
            if n <= 0:
                break
            if s and s["i"] == item_id:
                take = min(n, s["n"])
                s["n"] -= take
                n -= take
                removed += take
                if s["n"] <= 0:
                    self.bags[i] = None
        if removed:
            self.save_dirty = True
        return removed

    def free_slots(self) -> int:
        return sum(1 for s in self.bags if s is None)

    def currency(self, key: str) -> int:
        return int(self.currencies.get(key, 0))

    def add_currency(self, key: str, n: int):
        self.currencies[key] = max(0, self.currency(key) + n)
        self.save_dirty = True


# =============================================================================== Gegner
class Mob(Unit):
    kind = "mob"

    def __init__(self, tpl: dict, x: float, z: float, r: float = 0.0, lvl_range=None, spawn_r: float = 0.0,
                 difficulty: dict | None = None):
        lo, hi = lvl_range or tpl["lvl"]
        super().__init__(tpl["name"], random.randint(lo, hi), x, z, r)
        self.tpl = tpl
        self.lvl_range = (lo, hi)
        self.title = tpl.get("title", "")
        self.model = tpl["model"]
        self.scale = tpl.get("scale", 1.0)
        self.radius = tpl.get("radius", 0.5)
        self.hostile = not tpl.get("critter", False) and not tpl.get("friendly", False)
        self.side = "mob"
        self.look = dict(tpl.get("look", {}))
        self.look.update({"elite": tpl.get("elite", False), "rare": tpl.get("rare", False), "boss": tpl.get("boss", False),
                          "aggro": tpl.get("aggro", False), "critter": tpl.get("critter", False),
                          "dummy": tpl.get("dummy", False)})
        if tpl.get("tint"):
            self.look["tint"] = tpl["tint"]
        self.home = (x, z, r)
        self.spawn_r = spawn_r
        self.state = "idle"
        self.threat: dict[int, float] = {}
        self.swing_ready = 0.0
        self.ab_next: dict[str, float] = {}
        self.ab_used: set[str] = set()
        self.wander_to = None
        self.next_wander = now() + random.uniform(2, 10)
        self.tap: set[int] | None = None
        self.loot: dict[int, dict] = {}
        self.respawn_at = 0.0
        self.corpse_until = 0.0
        self.flee_until = 0.0
        self.fled = False
        self.taunt_by: int | None = None
        self.taunt_until = 0.0
        self.summons: list[int] = []
        self.owner_boss: int | None = None
        self.evade_t = 0.0
        self.engage_t = 0.0
        self.phase = 0
        self.difficulty = difficulty or {}
        self.resist = dict(tpl.get("resist", {}))
        self.fear_dir = None
        self.spawn_group = None
        self.reset_stats()

    def reset_stats(self):
        from ..content.mobs import mob_armor, mob_damage, mob_max_hp
        d = self.difficulty
        self.max_hp = int(mob_max_hp(self.tpl, self.level) * d.get("hp", 1.0))
        self.hp = self.max_hp
        self.armor = mob_armor(self.tpl, self.level)
        lo, hi = mob_damage(self.tpl, self.level)
        m = d.get("dmg", 1.0)
        self.dmg = (int(lo * m), int(hi * m))
        rt = self.tpl.get("power")
        if rt:
            self.power_type = "mana"
            self.max_power = 100 + self.level * 20
            self.power = self.max_power
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
        d["fam"] = self.tpl.get("family")
        return d


class Pet(Mob):
    """Begleiter eines Spielers (Skelette, Naturgeist, Wolf)."""
    kind = "pet"

    def __init__(self, tpl: dict, owner: Player, x: float, z: float, expires: float = 0.0):
        super().__init__(tpl, x, z, owner.r, (owner.level, owner.level))
        self.owner_id = owner.id
        self.owner_name = owner.name
        self.hostile = False
        self.side = "player"
        self.title = f"Diener von {owner.name}" if tpl.get("undead") else f"Begleiter von {owner.name}"
        self.expires = expires
        self.state = "follow"
        self.follow_angle = random.uniform(-1.5, 1.5)
        self.pet_mult = 1.0
        self.team = owner.team

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["owner"] = self.owner_id
        return d


# =============================================================================== NPCs
class Npc(Unit):
    kind = "npc"

    def __init__(self, tpl: dict):
        x, z = tpl["pos"]
        super().__init__(tpl["name"], tpl.get("lvl", 10), x, z, tpl.get("rot", 0.0))
        self.tpl = tpl
        self.npc_id = tpl["id"]
        self.title = tpl.get("title", "")
        self.model = tpl.get("model", "human")
        self.scale = tpl.get("scale", 1.0)
        self.look = dict(tpl.get("look", {}))
        self.radius = 0.5
        self.hostile = False
        self.side = "neutral"
        self.max_hp = self.hp = 100 + 40 * self.level
        self.home = (x, z, tpl.get("rot", 0.0))
        self.wander_to = None
        self.next_wander = now() + random.uniform(3, 8)
        self.next_bark = now() + random.uniform(20, 60)
        self.talk_until = 0.0
        self.path_i = 0

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["npc"] = self.npc_id
        d["svc"] = self.tpl.get("services", [])
        d["guard"] = self.tpl.get("guard", False)
        return d


# =============================================================================== Objekte
class GameObj(Unit):
    """Sammelobjekte (Kräuter, Erze), Truhen, Teleportationssteine, Questobjekte, Briefkästen, Werkbänke."""
    kind = "obj"

    def __init__(self, spec: dict, name: str):
        x, z = spec["pos"]
        super().__init__(name, spec.get("lvl", 1), x, z, spec.get("r", random.uniform(0, math.tau)))
        self.spec = spec
        self.obj_kind = spec["kind"]
        self.item = spec.get("item")
        self.respawn = spec.get("respawn", 60)
        self.model = spec.get("model", spec["kind"])
        self.available = True
        self.respawn_at = 0.0
        self.max_hp = self.hp = 1
        self.radius = spec.get("radius", 0.8)
        self.look = dict(spec.get("look", {}))

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["obj"] = self.obj_kind
        d["sub"] = self.spec.get("sub") or self.spec.get("node")
        return d


class Trap(Unit):
    kind = "trap"

    def __init__(self, owner: Player, spec: dict, x: float, z: float, t: float):
        super().__init__(spec["name"], owner.level, x, z, 0.0)
        self.owner_id = owner.id
        self.spec = spec
        self.expires = t + spec.get("dur", 60)
        self.armed_at = t + 1.0
        self.model = "trap_" + spec.get("fx", "frost")
        self.side = "player"
        self.max_hp = self.hp = 1
        self.radius = spec.get("radius", 2.5)
        self.team = owner.team

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["owner"] = self.owner_id
        d["fx"] = self.spec.get("fx")
        return d


class GroundEffect(Unit):
    """Bodeneffekt (Seuchenwolke, Feuerflächen von Bossen, Lava)."""
    kind = "ground"

    def __init__(self, src: Unit, spec: dict, x: float, z: float, t: float, friendly_to: str):
        super().__init__(spec.get("name", "Bodeneffekt"), src.level, x, z, 0.0)
        self.src_id = src.id
        self.spec = spec
        self.expires = t + spec.get("dur", 10) if spec.get("dur", 10) > 0 else 0.0
        self.next_tick = t + spec.get("delay", 0.5)
        self.radius = spec.get("radius", 6)
        self.model = "ground_" + spec.get("fx", "fire")
        self.side = friendly_to
        self.max_hp = self.hp = 1

    def spawn_info(self) -> dict:
        d = super().spawn_info()
        d["fx"] = self.spec.get("fx")
        d["r2"] = self.radius
        return d


def resource_max(rtype: str) -> int | None:
    return RESOURCES.get(rtype, {}).get("max")
