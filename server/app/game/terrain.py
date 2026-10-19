"""Gelände, Vegetation, Hindernisse und Wegfindung.

Die Höhenkarten aller Außenzonen werden beim Serverstart deterministisch erzeugt (numpy) und an den
Client übertragen – eine Quelle der Wahrheit für Server und Client. Die Dreiecksaufteilung der
Interpolation ist mit dem Godot-Client identisch.
"""
from __future__ import annotations

import base64
import math
import random
from functools import lru_cache

import numpy as np


# ----------------------------------------------------------------------------- Rauschen (numpy)
def _hash(ix, iz, seed: int):
    h = (ix.astype(np.int64) * 374761393 + iz.astype(np.int64) * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(np.float64) / 65535.0


def value_noise(x, z, seed: int = 0):
    ix = np.floor(x)
    iz = np.floor(z)
    fx = x - ix
    fz = z - iz
    ix = ix.astype(np.int64)
    iz = iz.astype(np.int64)
    a = _hash(ix, iz, seed)
    b = _hash(ix + 1, iz, seed)
    c = _hash(ix, iz + 1, seed)
    d = _hash(ix + 1, iz + 1, seed)
    u = fx * fx * (3 - 2 * fx)
    v = fz * fz * (3 - 2 * fz)
    return (a + (b - a) * u) + ((c + (d - c) * u) - (a + (b - a) * u)) * v


def fbm(x, z, octaves: int = 4, seed: int = 0):
    total = np.zeros_like(x, dtype=np.float64)
    amp, freq, norm = 1.0, 1.0, 0.0
    for o in range(octaves):
        total += (value_noise(x * freq, z * freq, seed + o * 31) * 2 - 1) * amp
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-9), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _seg_dist_grid(X, Z, ax, az, bx, bz):
    dx, dz = bx - ax, bz - az
    l2 = dx * dx + dz * dz
    if l2 == 0:
        return np.hypot(X - ax, Z - az)
    t = np.clip(((X - ax) * dx + (Z - az) * dz) / l2, 0.0, 1.0)
    return np.hypot(X - (ax + t * dx), Z - (az + t * dz))


def _polyline_dist(X, Z, pts):
    best = np.full(X.shape, 1e9)
    for k in range(len(pts) - 1):
        best = np.minimum(best, _seg_dist_grid(X, Z, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]))
    return best


# ----------------------------------------------------------------------------- Höhenkarte
class Heightmap:
    def __init__(self, size: float, step: float, data: np.ndarray, void: float | None = None):
        self.size = size
        self.step = step
        self.half = size / 2
        self.n = data.shape[0]
        self.arr = data.astype(np.float32)
        self.data = self.arr.ravel().tolist()
        self.void = void

    def height(self, x: float, z: float) -> float:
        fx = (x + self.half) / self.step
        fz = (z + self.half) / self.step
        fx = max(0.0, min(self.n - 1.001, fx))
        fz = max(0.0, min(self.n - 1.001, fz))
        i, j = int(fx), int(fz)
        tx, tz = fx - i, fz - j
        d = self.data
        n = self.n
        a = d[j * n + i]
        b = d[j * n + i + 1]
        c = d[(j + 1) * n + i]
        e = d[(j + 1) * n + i + 1]
        if tx + tz <= 1:
            return a + (b - a) * tx + (c - a) * tz
        return e + (c - e) * (1 - tx) + (b - e) * (1 - tz)

    def is_void(self, x: float, z: float) -> bool:
        return self.void is not None and self.height(x, z) <= self.void + 1.0

    def slope(self, x: float, z: float) -> float:
        d = self.step
        hx = self.height(x + d, z) - self.height(x - d, z)
        hz = self.height(x, z + d) - self.height(x, z - d)
        return math.hypot(hx, hz) / (2 * d)

    def encoded(self) -> str:
        packed = np.clip(np.round(self.arr * 100), -32000, 32000).astype("<i2").tobytes()
        return base64.b64encode(packed).decode()


def build_heightmap(zone: dict) -> Heightmap:
    cfg = zone["terrain"]
    size = zone["size"]
    step = zone.get("step", 2)
    n = int(size / step) + 1
    half = size / 2
    coords = -half + np.arange(n) * step
    X, Z = np.meshgrid(coords, coords)   # Z: Zeilen (j), X: Spalten (i)
    seed = cfg.get("seed", 7)
    freq = cfg.get("freq", 0.011)
    h = fbm(X * freq, Z * freq, 4, seed) * cfg.get("base", 6.5)
    h += fbm(X * cfg.get("detail_freq", 0.045), Z * cfg.get("detail_freq", 0.045), 2, seed + 92) * cfg.get("detail", 0.9)
    if cfg.get("ridged"):
        r = 1.0 - np.abs(fbm(X * cfg["ridged"]["freq"], Z * cfg["ridged"]["freq"], 4, seed + 17))
        h += (r ** 2) * cfg["ridged"]["amp"]
    for hill in cfg.get("hills", []):
        d2 = (X - hill["x"]) ** 2 + (Z - hill["z"]) ** 2
        h += hill["h"] * np.exp(-d2 / (2 * hill["s"] ** 2))
    for cr in cfg.get("craters", []):
        d = np.hypot(X - cr["x"], Z - cr["z"])
        rim = np.exp(-((d - cr["r"]) ** 2) / (2 * (cr["r"] * 0.25) ** 2)) * cr.get("rim", 4)
        bowl = -(1 - smoothstep(0, cr["r"], d)) * cr["depth"]
        h += rim + bowl
    for rg in cfg.get("ridges", []):
        d = _polyline_dist(X, Z, rg["pts"])
        h += np.exp(-(d ** 2) / (2 * rg["w"] ** 2)) * rg["h"] * (0.75 + 0.5 * value_noise(X * 0.03, Z * 0.03, seed + 3))
    for v in cfg.get("valleys", []):
        d = _polyline_dist(X, Z, v["pts"])
        w = v["w"]
        target = v.get("level", None)
        carve = 1 - smoothstep(w * 0.5, w * 0.5 + v.get("falloff", 10), d)
        if target is None:
            h -= carve * v.get("depth", 4)
        else:
            h = h + (target - h) * carve
    edge = cfg.get("edge")
    if edge:
        dd = (np.abs(X) ** 4 + np.abs(Z) ** 4) ** 0.25
        t = np.clip((dd - edge["start"]) / (edge["end"] - edge["start"]), 0.0, 1.25)
        h += (t ** 1.6) * edge["height"] * (0.75 + 0.5 * value_noise(X * 0.03, Z * 0.03, 5))
    # Einebnungen (Dörfer, Burghügel, Lager)
    for f in cfg.get("flatten", []):
        d = np.hypot(X - f["x"], Z - f["z"])
        target = f["h"]
        if target is None:
            i = int(round((f["x"] + half) / step))
            j = int(round((f["z"] + half) / step))
            target = float(h[min(n - 1, max(0, j)), min(n - 1, max(0, i))])
            f["h_resolved"] = target
        w = 1.0 - smoothstep(f["r"], f["r"] + f["falloff"], d)
        h = h + (target - h) * w
    void = None
    if cfg.get("islands") is not None:
        void = cfg.get("void", -60.0)
        mask = np.zeros_like(h)
        base = np.full_like(h, -1e9)
        for isl in cfg["islands"]:
            d = np.hypot(X - isl["x"], Z - isl["z"])
            edge_noise = 1.0 + (value_noise(X * 0.08, Z * 0.08, seed + 41) - 0.5) * 0.25
            m = 1 - smoothstep(isl["r"] * 0.82 * edge_noise, isl["r"] * edge_noise, d)
            mask = np.maximum(mask, m)
            base = np.where(m > 0.01, np.maximum(base, isl.get("h", 0.0)), base)
        base = np.where(base < -1e8, 0.0, base)
        h = np.where(mask > 0.02, base + h * 0.35 * mask, void)
    return Heightmap(size, step, h, void)


# ----------------------------------------------------------------------------- Straßen
def _seg_dist(px, pz, ax, az, bx, bz):
    dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


def road_distance(roads: list, x: float, z: float) -> float:
    best = 1e9
    for road in roads:
        pts = road["pts"]
        for k in range(len(pts) - 1):
            best = min(best, _seg_dist(x, z, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]) - road["w"] / 2)
    return best


# ----------------------------------------------------------------------------- Requisiten & Hindernisse
_CIRCLE = {"well": 1.5, "fountain": 2.8, "windmill": 3.6, "haystack": 1.6, "tent": 2.4, "bigtent": 3.6, "campfire": 0.9,
           "watchtower": 2.2, "brazier": 0.6, "barrel": 0.5, "crate": 0.6, "lantern": 0.25, "deadtree": 0.6,
           "cauldron": 0.8, "anvil": 0.6, "stall": 1.6, "wagon": 1.8, "minecart": 1.0, "orepile": 1.2, "scarecrow": 0.4,
           "sarcophagus": 1.4, "altar": 1.8, "throne": 1.2, "sign": 0.25, "cart": 1.4, "weaponrack": 0.8, "bench": 0.8,
           "statue": 1.2, "obelisk": 1.0, "runestone": 0.8, "crystal_big": 1.6, "brazier_big": 1.2, "forge": 1.6,
           "mailbox": 0.4, "moonwell": 2.5, "standing_stone": 0.9, "ice_spike": 1.2, "lava_rock": 1.5, "portal_ring": 2.0,
           "bonfire": 1.4, "beehive": 0.6, "totem": 0.6, "tree_house": 2.0, "giant_mushroom": 1.0, "column": 0.9}
_BOX = {"house", "inn", "smithy", "chapel", "keep", "kitchen", "barn", "shed", "hut", "mausoleum", "mine", "dwarf_hall",
        "dwarf_house", "elf_house", "temple", "ruin_wall", "watch_post", "hall", "bank", "auction", "stable", "tavern",
        "forge_house", "ash_fort", "sky_temple", "arena_wall"}
_SEGMENT = {"wall": 3.0, "palisade": 0.8, "fence": 0.3, "ironfence": 0.25, "ice_wall": 3.0, "ruin_line": 1.5}


def obstacles_for(props: list[dict]) -> list[dict]:
    out = []
    for p in props:
        t = p["t"]
        if t in _SEGMENT:
            out.append({"k": "seg", "x1": p["x1"], "z1": p["z1"], "x2": p["x2"], "z2": p["z2"], "w": p.get("th", _SEGMENT[t])})
        elif t in _BOX:
            w, d = p.get("w", 6), p.get("d", 6)
            if t == "smithy":
                d = d * 0.5
            if t == "mine":
                w, d = 7, 4
            out.append({"k": "box", "x": p["x"], "z": p["z"], "w": w, "d": d, "r": p.get("r", 0.0)})
        elif t == "tower":
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": p["rad"]})
        elif t == "gatearch":
            w = p.get("w", 10)
            r = p.get("r", 0.0)
            for s in (-1, 1):
                ox = math.cos(r) * s * (w / 2 - 1)
                oz = -math.sin(r) * s * (w / 2 - 1)
                out.append({"k": "circle", "x": p["x"] + ox, "z": p["z"] + oz, "rad": 1.6})
        elif t == "pillar":
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": 1.6 if p.get("big") else 1.0})
        elif t in _CIRCLE:
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": _CIRCLE[t] * p.get("s", 1.0)})
        elif t in ("tree", "pine", "birch", "skytree", "ashtree", "mushroom"):
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": 0.45 * p.get("s", 1.0)})
        elif t in ("rock", "crystal") and p.get("s", 1.0) > 0.8:
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": 1.1 * p.get("s", 1.0)})
    return out


def _footprint_radius(p: dict) -> float:
    t = p["t"]
    if t in _SEGMENT:
        return 0.0
    if "w" in p:
        return math.hypot(p["w"], p.get("d", p["w"])) / 2
    if t == "tower":
        return p["rad"]
    return _CIRCLE.get(t) or 2.0


def generate_props(zone: dict, hm: Heightmap, special_points: list[tuple]) -> list[dict]:
    """Feste Requisiten plus prozedural verteilte Bäume, Büsche, Felsen und Blumen."""
    cfg = zone.get("veg", {})
    rng = random.Random(cfg.get("seed", 4711))
    fixed = list(zone.get("props", []))
    lim = zone["size"] / 2 - 12
    occupied = [(p["x"], p["z"], _footprint_radius(p) + 3.5) for p in fixed if "x" in p]
    segs = [(p["x1"], p["z1"], p["x2"], p["z2"]) for p in fixed if "x1" in p]
    for c in cfg.get("clear", []):
        occupied.append((c["x"], c["z"], c["r"]))
    for (x, z) in special_points:
        occupied.append((x, z, 5))
    for wtr in zone.get("water", []):
        occupied.append((wtr["x"], wtr["z"], wtr["r"] + 2))
    for pv in zone.get("paved", []):
        if "r" in pv:
            occupied.append((pv["x"], pv["z"], pv["r"] + 1))
    fields = [p for p in fixed if p["t"] == "field"]
    roads = zone.get("roads", [])

    def free(x, z, margin=0.0):
        if abs(x) > lim or abs(z) > lim:
            return False
        if hm.is_void(x, z):
            return False
        if roads and road_distance(roads, x, z) < 3.5:
            return False
        for (ox, oz, r) in occupied:
            if (x - ox) ** 2 + (z - oz) ** 2 < (r + margin) ** 2:
                return False
        for (ax, az, bx, bz) in segs:
            if _seg_dist(x, z, ax, az, bx, bz) < 2.5:
                return False
        for fl in fields:
            if abs(x - fl["x"]) < fl["w"] / 2 + 3 and abs(z - fl["z"]) < fl["d"] / 2 + 3:
                return False
        return True

    def density(x, z):
        d = cfg.get("base", 0.1) * (1 + 0.8 * math.sin(x * 0.021 + 1.3) * math.cos(z * 0.017 + 0.4))
        for f in cfg.get("forests", []):
            dd = math.hypot(x - f["x"], z - f["z"])
            if dd < f["r"] + 30:
                d += f.get("density", 0.8) * max(0.0, 1 - max(0.0, dd - f["r"] * 0.6) / (f["r"] * 0.4 + 30))
        if cfg.get("edge_density"):
            ring = (abs(x) ** 4 + abs(z) ** 4) ** 0.25
            d += cfg["edge_density"] * max(0.0, min(1.0, (ring - lim * 0.75) / (lim * 0.12)))
        return d

    def pick_kind(x, z):
        for f in cfg.get("forests", []):
            if f.get("kinds") and math.hypot(x - f["x"], z - f["z"]) < f["r"]:
                return _weighted(rng, f["kinds"])
        h = hm.height(x, z)
        if cfg.get("high_kind") and h > cfg.get("high_level", 14):
            return cfg["high_kind"]
        return _weighted(rng, cfg.get("kinds", [("tree", 1.0)]))

    out = []
    attempts = 0
    target = cfg.get("count", 1500)
    while len(out) < target and attempts < target * 25:
        attempts += 1
        x = rng.uniform(-lim, lim)
        z = rng.uniform(-lim, lim)
        if rng.random() > density(x, z):
            continue
        if not free(x, z):
            continue
        if hm.slope(x, z) > 0.9:
            continue
        kind = pick_kind(x, z)
        s = rng.uniform(0.8, 1.35)
        out.append({"t": kind, "x": round(x, 1), "z": round(z, 1), "s": round(s, 2), "r": round(rng.uniform(0, math.tau), 2)})
        occupied.append((x, z, 2.2 * s))
    for _ in range(cfg.get("rocks", 300)):
        x = rng.uniform(-lim, lim)
        z = rng.uniform(-lim, lim)
        if not free(x, z):
            continue
        ring = (abs(x) ** 4 + abs(z) ** 4) ** 0.25
        big = ring > lim * 0.8
        kind = cfg.get("rock_kind", "rock")
        if rng.random() < cfg.get("bush_share", 0.45) and not big:
            out.append({"t": cfg.get("bush_kind", "bush"), "x": round(x, 1), "z": round(z, 1),
                        "s": round(rng.uniform(0.7, 1.3), 2), "r": round(rng.uniform(0, math.tau), 2)})
        else:
            s = rng.uniform(1.2, 3.2) if big else rng.uniform(0.5, 1.8)
            out.append({"t": kind, "x": round(x, 1), "z": round(z, 1), "s": round(s, 2), "r": round(rng.uniform(0, math.tau), 2)})
    for _ in range(cfg.get("flowers", 260)):
        x = rng.uniform(-lim * 0.8, lim * 0.8)
        z = rng.uniform(-lim * 0.8, lim * 0.8)
        if hm.is_void(x, z):
            continue
        if roads and road_distance(roads, x, z) < 2:
            continue
        if any((x - wx["x"]) ** 2 + (z - wx["z"]) ** 2 < (wx["r"] + 1) ** 2 for wx in zone.get("water", [])):
            continue
        out.append({"t": "flowers", "x": round(x, 1), "z": round(z, 1), "s": round(rng.uniform(0.7, 1.4), 2), "v": rng.randint(0, 3)})
    for extra in cfg.get("scatter", []):
        for _ in range(extra["n"]):
            x = rng.uniform(-lim, lim)
            z = rng.uniform(-lim, lim)
            if extra.get("area"):
                a = extra["area"]
                ang = rng.uniform(0, math.tau)
                dd = a["r"] * math.sqrt(rng.random())
                x, z = a["x"] + math.cos(ang) * dd, a["z"] + math.sin(ang) * dd
            if not free(x, z):
                continue
            out.append({"t": extra["t"], "x": round(x, 1), "z": round(z, 1), "s": round(rng.uniform(*extra.get("s", (0.8, 1.3))), 2),
                        "r": round(rng.uniform(0, math.tau), 2)})
            occupied.append((x, z, 2.0))
    return fixed + out


def _weighted(rng: random.Random, items: list) -> str:
    total = sum(w for _, w in items)
    r = rng.uniform(0, total)
    for k, w in items:
        r -= w
        if r <= 0:
            return k
    return items[-1][0]


# ----------------------------------------------------------------------------- Wegfindung (Dungeon)
class RectNav:
    """Begehbare Fläche als Vereinigung achsenparalleler Rechtecke mit einfacher Wegfindung."""

    def __init__(self, rects: list[list[float]]):
        self.rects = [tuple(r) for r in rects]
        self.adj: dict[int, list[int]] = {i: [] for i in range(len(self.rects))}
        for i, a in enumerate(self.rects):
            for j, b in enumerate(self.rects):
                if i < j and self._touch(a, b):
                    self.adj[i].append(j)
                    self.adj[j].append(i)

    @staticmethod
    def _touch(a, b) -> bool:
        return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]

    def rect_of(self, x: float, z: float, margin: float = 0.0) -> int:
        for i, r in enumerate(self.rects):
            if r[0] + margin <= x <= r[2] - margin and r[1] + margin <= z <= r[3] - margin:
                return i
        return -1

    def contains(self, x: float, z: float, margin: float = 0.3) -> bool:
        return self.rect_of(x, z, margin) >= 0

    def clamp(self, x: float, z: float, margin: float = 0.4) -> tuple[float, float]:
        if self.contains(x, z, margin):
            return x, z
        best, bd = (x, z), 1e18
        for r in self.rects:
            cx = max(r[0] + margin, min(r[2] - margin, x))
            cz = max(r[1] + margin, min(r[3] - margin, z))
            d = (cx - x) ** 2 + (cz - z) ** 2
            if d < bd:
                bd, best = d, (cx, cz)
        return best

    def _overlap_center(self, a, b) -> tuple[float, float]:
        x1, z1 = max(a[0], b[0]), max(a[1], b[1])
        x2, z2 = min(a[2], b[2]), min(a[3], b[3])
        return (x1 + x2) / 2, (z1 + z2) / 2

    def next_waypoint(self, sx: float, sz: float, tx: float, tz: float) -> tuple[float, float]:
        a = self.rect_of(sx, sz)
        b = self.rect_of(tx, tz)
        if a < 0:
            return self.clamp(sx, sz, 0.6)
        if b < 0 or a == b:
            return tx, tz
        prev = {a: None}
        queue = [a]
        while queue:
            cur = queue.pop(0)
            if cur == b:
                break
            for nb in self.adj[cur]:
                if nb not in prev:
                    prev[nb] = cur
                    queue.append(nb)
        if b not in prev:
            return tx, tz
        node = b
        while prev[node] != a:
            node = prev[node]
        cx, cz = self._overlap_center(self.rects[a], self.rects[node])
        if math.hypot(cx - sx, cz - sz) < 1.0:
            r = self.rects[node]
            return (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        return cx, cz


@lru_cache(maxsize=None)
def nav_for(zone_id: str) -> RectNav:
    from ..content.world import ZONES
    return RectNav(ZONES[zone_id]["rects"])
