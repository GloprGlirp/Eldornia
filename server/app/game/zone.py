"""Zonen: offene Regionen und Instanzen (Dungeons, Raids, Arena).

Jede Zone verwaltet ihre Einheiten, Timer, Ereignisse und die Begehbarkeit (Höhenkarte, Hindernisse,
Wasser). Die statischen Geländedaten werden einmal pro Zonentyp erzeugt und zwischengespeichert.
"""
from __future__ import annotations

import base64
import heapq
import itertools
import logging
import math
import random
import zlib
from functools import lru_cache

from ..content import world as W
from ..content.professions import NODES
from .entities import GameObj, Mob, Npc, Player, Unit, now
from .terrain import Heightmap, RectNav, build_heightmap, generate_props, obstacles_for

log = logging.getLogger("eldornia.zone")
_seq = itertools.count()

VIEW_OUTDOOR = 160.0
CELL = 1.0
MAX_SLOPE = 1.05


# ============================================================================== Statische Daten
class StaticZone:
    """Gelände, Requisiten und Begehbarkeitsraster eines Zonentyps (für alle Instanzen gleich)."""

    def __init__(self, zone_id: str):
        cfg = W.ZONES[zone_id]
        self.id = zone_id
        self.cfg = cfg
        self.outdoor = cfg["type"] != "dungeon"
        self.hm: Heightmap | None = None
        self.nav: RectNav | None = None
        if "terrain" in cfg:
            self.hm = build_heightmap(cfg)
            special = []
            for n in W.NPCS.values():
                if n["zone"] == zone_id:
                    special.append(tuple(n["pos"]))
            for o in W.OBJECTS.get(zone_id, []):
                special.append(tuple(o["pos"]))
            for p in cfg.get("portals", []):
                special.append((p["x"], p["z"]))
            for s in cfg.get("stones", []):
                special.append(tuple(s["pos"]))
            self.props = generate_props(cfg, self.hm, special)
        else:
            self.props = list(cfg.get("props", []))
        if "rects" in cfg:
            self.nav = RectNav(cfg["rects"])
        self.obstacles = obstacles_for(self.props)
        self.size = cfg.get("size", 0) if self.hm else self._dungeon_extent()
        self.half = self.size / 2
        self.n = int(self.size / CELL)
        self.grid = bytearray(self.n * self.n)      # 0 frei, 1 Hindernis, 2 tiefes Wasser, 3 zu steil/Leere
        self._rasterize()

    def _dungeon_extent(self) -> float:
        m = 10.0
        for r in self.cfg.get("rects", []):
            m = max(m, abs(r[0]), abs(r[1]), abs(r[2]), abs(r[3]))
        return math.ceil(m + 4) * 2

    def cell(self, x: float, z: float) -> tuple[int, int]:
        return int((x + self.half) / CELL), int((z + self.half) / CELL)

    def _mark(self, i: int, j: int, v: int):
        if 0 <= i < self.n and 0 <= j < self.n:
            k = j * self.n + i
            if self.grid[k] == 0 or v == 1:
                self.grid[k] = v

    def _rasterize(self):
        n = self.n
        half = self.half
        # Gelände: Steilhänge, Leere, Wasser
        if self.hm:
            water = self.cfg.get("water", [])
            for j in range(n):
                z = -half + (j + 0.5) * CELL
                for i in range(n):
                    x = -half + (i + 0.5) * CELL
                    h = self.hm.height(x, z)
                    if self.hm.void is not None and h <= self.hm.void + 1.0:
                        self.grid[j * n + i] = 3
                        continue
                    if abs(x) > half - 3 or abs(z) > half - 3:
                        self.grid[j * n + i] = 3
                        continue
                    if self.hm.slope(x, z) > MAX_SLOPE:
                        self.grid[j * n + i] = 3
                        continue
                    for w in water:
                        if w.get("lava") and (x - w["x"]) ** 2 + (z - w["z"]) ** 2 < (w["r"] - 1.5) ** 2:
                            self.grid[j * n + i] = 3
                        elif (x - w["x"]) ** 2 + (z - w["z"]) ** 2 < w["r"] ** 2 and h < w.get("level", -0.8) - 1.2:
                            self.grid[j * n + i] = 2
        else:
            for j in range(n):
                z = -half + (j + 0.5) * CELL
                for i in range(n):
                    x = -half + (i + 0.5) * CELL
                    if not self.nav.contains(x, z, 0.35):
                        self.grid[j * n + i] = 3
        # Hindernisse
        for o in self.obstacles:
            k = o["k"]
            if k == "circle":
                r = o["rad"]
                i0, j0 = self.cell(o["x"] - r, o["z"] - r)
                i1, j1 = self.cell(o["x"] + r, o["z"] + r)
                for j in range(j0, j1 + 1):
                    for i in range(i0, i1 + 1):
                        cx = -half + (i + 0.5) * CELL
                        cz = -half + (j + 0.5) * CELL
                        if (cx - o["x"]) ** 2 + (cz - o["z"]) ** 2 <= r * r:
                            self._mark(i, j, 1)
            elif k == "box":
                cr, sr = math.cos(o.get("r", 0.0)), math.sin(o.get("r", 0.0))
                hw, hd = o["w"] / 2, o["d"] / 2
                ext = math.hypot(hw, hd)
                i0, j0 = self.cell(o["x"] - ext, o["z"] - ext)
                i1, j1 = self.cell(o["x"] + ext, o["z"] + ext)
                for j in range(j0, j1 + 1):
                    for i in range(i0, i1 + 1):
                        dx = -half + (i + 0.5) * CELL - o["x"]
                        dz = -half + (j + 0.5) * CELL - o["z"]
                        lx = dx * cr - dz * sr
                        lz = dx * sr + dz * cr
                        if abs(lx) <= hw and abs(lz) <= hd:
                            self._mark(i, j, 1)
            elif k == "seg":
                ax, az, bx, bz, w = o["x1"], o["z1"], o["x2"], o["z2"], o["w"] / 2 + 0.2
                i0, j0 = self.cell(min(ax, bx) - w, min(az, bz) - w)
                i1, j1 = self.cell(max(ax, bx) + w, max(az, bz) + w)
                dx, dz = bx - ax, bz - az
                l2 = dx * dx + dz * dz or 1.0
                for j in range(j0, j1 + 1):
                    for i in range(i0, i1 + 1):
                        px = -half + (i + 0.5) * CELL
                        pz = -half + (j + 0.5) * CELL
                        t = max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / l2))
                        if math.hypot(px - (ax + t * dx), pz - (az + t * dz)) <= w:
                            self._mark(i, j, 1)
        # Tore & Durchgänge wieder freigeben (Mauern mit Tor)
        for p in self.props:
            if p["t"] in ("gatearch", "gate"):
                w = p.get("w", 10) / 2 - 2.2
                cr, sr = math.cos(p.get("r", 0.0)), math.sin(p.get("r", 0.0))
                for a in range(-int(w * 2), int(w * 2) + 1):
                    for b in range(-4, 5):
                        lx, lz = a * 0.5, b * 0.5
                        x = p["x"] + lx * cr + lz * sr
                        z = p["z"] - lx * sr + lz * cr
                        i, j = self.cell(x, z)
                        if 0 <= i < n and 0 <= j < n and self.grid[j * n + i] == 1:
                            self.grid[j * n + i] = 0

    def blocked(self, x: float, z: float, for_mob: bool = False) -> bool:
        i, j = self.cell(x, z)
        if not (0 <= i < self.n and 0 <= j < self.n):
            return True
        v = self.grid[j * self.n + i]
        if v == 2:
            return for_mob
        return v != 0

    def height(self, x: float, z: float) -> float:
        if self.hm:
            return self.hm.height(x, z)
        return 0.0

    def client_data(self) -> dict:
        cfg = self.cfg
        d = {
            "id": self.id, "name": cfg["name"], "type": cfg["type"], "theme": cfg.get("theme", "gruen"),
            "levels": cfg.get("levels"), "props": self.props, "portals": [p for p in cfg.get("portals", []) if not p.get("hidden")],
            "hidden_portals": [{"x": p["x"], "z": p["z"], "r": p["r"]} for p in cfg.get("portals", []) if p.get("hidden")],
            "stones": cfg.get("stones", []), "waypoints": cfg.get("waypoints", []), "subzones": cfg.get("subzones", []),
            "grid_n": self.n, "grid_cell": CELL, "grid": base64.b64encode(zlib.compress(bytes(self.grid), 9)).decode(),
            "music": cfg.get("music", cfg.get("theme", "gruen")),
        }
        if self.hm:
            d.update({"size": self.hm.size, "step": self.hm.step, "n": self.hm.n, "heights": self.hm.encoded(),
                      "water": cfg.get("water", []), "roads": cfg.get("roads", []), "plaza": cfg.get("plaza"),
                      "paved": cfg.get("paved", []), "accent": cfg.get("accent", []), "graveyard": cfg.get("graveyard")})
            if self.hm.void is not None:
                d["void"] = self.hm.void
                d["islands"] = cfg["terrain"].get("islands", [])
        else:
            d.update({"rects": cfg["rects"], "rooms": cfg.get("rooms", []), "style": cfg.get("style", "krypta"),
                      "open_sky": cfg.get("open_sky", False), "pools": cfg.get("pools", []),
                      "traps": [{"x": t["x"], "z": t["z"], "r": t["r"], "fx": t.get("fx")} for t in cfg.get("traps", [])]})
        return d


@lru_cache(maxsize=None)
def static_zone(zone_id: str) -> StaticZone:
    return StaticZone(zone_id)


# ============================================================================== Laufende Zone
class Zone:
    def __init__(self, world, zone_id: str, key: str, mode: str = "normal", affixes: list[str] | None = None):
        self.world = world
        self.id = zone_id
        self.key = key
        self.cfg = W.ZONES[zone_id]
        self.static = static_zone(zone_id)
        self.is_instance = self.cfg["type"] == "dungeon"
        self.is_arena = bool(self.cfg.get("arena"))
        self.mode = mode
        self.mode_cfg = W.MODES.get(mode, W.MODES["normal"])
        self.affixes = affixes or []
        self.entities: dict[int, Unit] = {}
        self.players: dict[int, Player] = {}
        self.npcs: dict[str, Npc] = {}
        self.timers: list = []
        self.events: list = []
        self.fx: list = []
        self.empty_since = now()
        self.created = now()
        self.nav = self.static.nav
        self.hm = self.static.hm
        self.view2 = (VIEW_OUTDOOR if not self.is_instance else 1000.0) ** 2
        self.trap_cd: dict[tuple, float] = {}
        self.bosses_killed: list[str] = []
        self.encounter: int | None = None
        self.owner_party: int | None = None
        self.next_affix = now() + 20
        self._populate()

    # ------------------------------------------------------------------ Aufbau
    def difficulty(self) -> dict:
        if not self.is_instance:
            return {}
        return {"hp": self.mode_cfg["hp"], "dmg": self.mode_cfg["dmg"], "level_add": self.mode_cfg.get("level_add", 0)}

    def _populate(self):
        diff = self.difficulty()
        for spec in W.SPAWNS.get(self.id, []):
            tpl = W.MOBS[spec["mob"]]
            lvl = spec.get("lvl") or tpl["lvl"]
            if diff.get("level_add"):
                lvl = [lvl[0] + diff["level_add"], lvl[1] + diff["level_add"]]
            if "pos" in spec:
                x, z = spec["pos"]
                m = Mob(tpl, x, z, spec.get("r", random.uniform(0, math.tau)), lvl, difficulty=diff)
                if spec.get("patrol"):
                    m.tpl = dict(tpl, patrol=spec["patrol"])
                self.add(m)
            else:
                for _ in range(spec["n"]):
                    x, z = self._random_point(spec["x"], spec["z"], spec["r"])
                    self.add(Mob(tpl, x, z, random.uniform(0, math.tau), lvl, spawn_r=spec["r"], difficulty=diff))
        for tpl in W.NPCS.values():
            if tpl["zone"] == self.id:
                npc = Npc(tpl)
                self.npcs[tpl["id"]] = npc
                self.add(npc)
        for spec in W.OBJECTS.get(self.id, []):
            name = spec.get("name")
            if spec["kind"] == "node":
                node = NODES[spec["node"]]
                name = node["name"]
                spec = dict(spec, model=node["model"], respawn=node.get("respawn", 90), prof=node["prof"], skill=node["skill"])
            elif spec["kind"] == "quest" and not name:
                from ..content.items import ITEMS
                name = ITEMS[spec["item"]]["name"]
            self.add(GameObj(spec, name or spec["kind"]))
        for st in self.cfg.get("stones", []):
            self.add(GameObj({"kind": "stone", "pos": st["pos"], "stone": st["id"], "r": 0.0, "radius": 1.0}, f"Teleportstein: {st['name']}"))
        for e in self.entities.values():
            e.y = self.height(e.x, e.z)

    def _random_point(self, cx: float, cz: float, r: float) -> tuple[float, float]:
        for _ in range(60):
            a = random.uniform(0, math.tau)
            d = r * math.sqrt(random.random())
            x, z = cx + math.cos(a) * d, cz + math.sin(a) * d
            if self.static.blocked(x, z, for_mob=True):
                continue
            if self.in_water(x, z):
                continue
            return x, z
        return cx, cz

    # ------------------------------------------------------------------ Einheiten
    def add(self, e: Unit):
        e.zone = self
        self.entities[e.id] = e
        if isinstance(e, Player):
            self.players[e.id] = e

    def remove(self, e: Unit):
        self.entities.pop(e.id, None)
        if self.players.pop(e.id, None) is not None and not self.players:
            self.empty_since = now()

    def mobs_near(self, x: float, z: float, r: float):
        r2 = r * r
        for e in list(self.entities.values()):
            if isinstance(e, Mob) and not e.dead and not e.hidden and (e.x - x) ** 2 + (e.z - z) ** 2 <= r2:
                yield e

    def players_near(self, x: float, z: float, r: float):
        r2 = r * r
        for p in list(self.players.values()):
            if (p.x - x) ** 2 + (p.z - z) ** 2 <= r2:
                yield p

    # ------------------------------------------------------------------ Timer & Ereignisse
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

    # ------------------------------------------------------------------ Gelände
    def height(self, x: float, z: float) -> float:
        return self.static.height(x, z)

    def water_level(self, x: float, z: float) -> float | None:
        for w in self.cfg.get("water", []):
            if (x - w["x"]) ** 2 + (z - w["z"]) ** 2 < w["r"] ** 2:
                return w.get("level", -0.8)
        return None

    def in_water(self, x: float, z: float) -> bool:
        lvl = self.water_level(x, z)
        return lvl is not None and self.height(x, z) < lvl - 0.3

    def walkable(self, x: float, z: float) -> bool:
        return not self.static.blocked(x, z)

    def walkable_clamp(self, x: float, z: float) -> tuple[float, float]:
        if self.nav:
            x, z = self.nav.clamp(x, z)
        lim = self.static.half - 4
        x, z = max(-lim, min(lim, x)), max(-lim, min(lim, z))
        if not self.static.blocked(x, z, for_mob=True):
            return x, z
        # nächste freie Zelle in der Umgebung suchen
        for rad in (0.7, 1.4, 2.2, 3.2, 4.5):
            for k in range(12):
                a = k / 12 * math.tau
                nx, nz = x + math.cos(a) * rad, z + math.sin(a) * rad
                if not self.static.blocked(nx, nz, for_mob=True):
                    return nx, nz
        return x, z

    def try_move(self, x0: float, z0: float, x1: float, z1: float, for_mob: bool = True) -> tuple[float, float]:
        """Bewegt von (x0,z0) nach (x1,z1) und gleitet an Hindernissen entlang."""
        if not self.static.blocked(x1, z1, for_mob):
            return x1, z1
        dx, dz = x1 - x0, z1 - z0
        if not self.static.blocked(x0 + dx, z0, for_mob):
            return x0 + dx, z0
        if not self.static.blocked(x0, z0 + dz, for_mob):
            return x0, z0 + dz
        d = math.hypot(dx, dz)
        if d > 1e-4:
            base = math.atan2(dz, dx)
            for off in (0.6, -0.6, 1.1, -1.1, 1.5, -1.5):
                nx, nz = x0 + math.cos(base + off) * d, z0 + math.sin(base + off) * d
                if not self.static.blocked(nx, nz, for_mob):
                    return nx, nz
        return x0, z0

    def in_pvp_area(self, x: float, z: float) -> bool:
        for a in self.cfg.get("pvp_areas", []):
            if (x - a["x"]) ** 2 + (z - a["z"]) ** 2 <= a["r"] ** 2:
                return True
        return False

    def subzone_at(self, x: float, z: float) -> str | None:
        best, bd = None, 1e18
        for s in self.cfg.get("subzones", []):
            d = (x - s["x"]) ** 2 + (z - s["z"]) ** 2
            if d <= s["r"] ** 2 and d < bd:
                best, bd = s["name"], d
        if not best and self.is_instance:
            for room in self.cfg.get("rooms", []):
                r = self.cfg["rects"][room["rect"]]
                if r[0] <= x <= r[2] and r[1] <= z <= r[3]:
                    return room["name"]
        return best

    # ------------------------------------------------------------------ Bosse (Instanzen)
    def boss_engaged(self, mob: Mob):
        self.encounter = mob.id

    def boss_reset(self, mob: Mob):
        if self.encounter == mob.id:
            self.encounter = None
