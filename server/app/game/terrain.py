"""Gelände, Hindernisse und Wegfindung.

Die Höhenkarte der Grünmark wird beim Serverstart deterministisch erzeugt und an den Client
übertragen (eine Quelle der Wahrheit für Server und Client).
"""
from __future__ import annotations

import base64
import math
import random
import struct
from functools import lru_cache

from .content import world as W


# ----------------------------------------------------------------------------- Rauschen
def _hash(ix: int, iz: int, seed: int) -> float:
    h = (ix * 374761393 + iz * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF) / 65535.0


def _smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def value_noise(x: float, z: float, seed: int = 0) -> float:
    ix, iz = math.floor(x), math.floor(z)
    fx, fz = x - ix, z - iz
    a = _hash(ix, iz, seed)
    b = _hash(ix + 1, iz, seed)
    c = _hash(ix, iz + 1, seed)
    d = _hash(ix + 1, iz + 1, seed)
    u, v = _smooth(fx), _smooth(fz)
    return (a + (b - a) * u) + ((c + (d - c) * u) - (a + (b - a) * u)) * v  # 0..1


def fbm(x: float, z: float, octaves: int = 4, seed: int = 0) -> float:
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += (value_noise(x * freq, z * freq, seed + o * 31) * 2 - 1) * amp
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm  # -1..1


def smoothstep(e0: float, e1: float, x: float) -> float:
    if e1 == e0:
        return 0.0 if x < e0 else 1.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------- Höhenkarte
def _natural_height(x: float, z: float) -> float:
    h = fbm(x * 0.011, z * 0.011, 4, 7) * 6.5
    h += fbm(x * 0.045, z * 0.045, 2, 99) * 0.9
    for hill in W.HILLS:
        d2 = (x - hill["x"]) ** 2 + (z - hill["z"]) ** 2
        h += hill["h"] * math.exp(-d2 / (2 * hill["s"] ** 2))
    # Gebirge am Rand (abgerundetes Quadrat)
    d = (abs(x) ** 4 + abs(z) ** 4) ** 0.25
    edge = 178.0
    if d > edge:
        t = min(1.25, (d - edge) / (240.0 - edge))
        h += (t ** 1.6) * 48.0 * (0.75 + 0.5 * value_noise(x * 0.03, z * 0.03, 5))
    return h


@lru_cache(maxsize=None)
def _flatten_target(idx: int) -> float:
    f = W.FLATTEN[idx]
    return f["h"] if f["h"] is not None else _natural_height(f["x"], f["z"])


def _height(x: float, z: float) -> float:
    h = _natural_height(x, z)
    for idx, f in enumerate(W.FLATTEN):
        d = math.hypot(x - f["x"], z - f["z"])
        if d >= f["r"] + f["falloff"]:
            continue
        target = _flatten_target(idx)
        w = 1.0 - smoothstep(f["r"], f["r"] + f["falloff"], d)
        h = h + (target - h) * w
    return h


class Heightmap:
    def __init__(self, size: float, step: float):
        self.size = size
        self.step = step
        self.half = size / 2
        self.n = int(size / step) + 1
        self.data = [0.0] * (self.n * self.n)
        for j in range(self.n):
            z = -self.half + j * step
            row = j * self.n
            for i in range(self.n):
                x = -self.half + i * step
                self.data[row + i] = _height(x, z)

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
        # gleiche Dreiecksaufteilung wie im Client (PlaneGeometry)
        if tx + tz <= 1:
            return a + (b - a) * tx + (c - a) * tz
        return e + (c - e) * (1 - tx) + (b - e) * (1 - tz)

    def encoded(self) -> str:
        """Höhen in Zentimetern als Int16, base64-kodiert."""
        packed = struct.pack(f"<{len(self.data)}h", *(max(-32000, min(32000, int(round(h * 100)))) for h in self.data))
        return base64.b64encode(packed).decode()


@lru_cache(maxsize=None)
def gruenmark_heightmap() -> Heightmap:
    z = W.ZONES["gruenmark"]
    return Heightmap(z["size"], z["step"])


# ----------------------------------------------------------------------------- Straßen
def _seg_dist(px, pz, ax, az, bx, bz):
    dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


def road_distance(x: float, z: float) -> float:
    best = 1e9
    for road in W.ROADS:
        pts = road["pts"]
        for k in range(len(pts) - 1):
            best = min(best, _seg_dist(x, z, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]) - road["w"] / 2)
    return best


# ----------------------------------------------------------------------------- Hindernisse
# Kollisions-Grundflächen je Requisitentyp (Kreis: rad, Rechteck: w x d)
_CIRCLE = {"well": 1.5, "tower": None, "fountain": 2.8, "windmill": 3.6, "haystack": 1.6, "tent": 2.4,
           "bigtent": 3.6, "campfire": 0.9, "watchtower": 2.2, "brazier": 0.6, "barrel": 0.5, "crate": 0.6,
           "lantern": 0.25, "deadtree": 0.6, "cauldron": 0.8, "anvil": 0.6, "stall": 1.6, "wagon": 1.8,
           "minecart": 1.0, "orepile": 1.2, "scarecrow": 0.4, "pillar": 1.0, "sarcophagus": 1.4,
           "altar": 1.8, "throne": 1.0, "sign": 0.25, "cart": 1.4, "weaponrack": 0.8, "bench": 0.8}
_BOX = {"house", "inn", "smithy", "chapel", "keep", "kitchen", "barn", "shed", "hut", "mausoleum", "mine"}
_SEGMENT = {"wall": 3.0, "palisade": 0.8, "fence": 0.3, "ironfence": 0.25}


def obstacles_for(props: list[dict]) -> list[dict]:
    out = []
    for p in props:
        t = p["t"]
        if t in _SEGMENT:
            out.append({"k": "seg", "x1": p["x1"], "z1": p["z1"], "x2": p["x2"], "z2": p["z2"], "w": _SEGMENT[t]})
        elif t in _BOX:
            w, d = p.get("w", 6), p.get("d", 6)
            if t == "smithy":       # offene Schmiede: nur die hintere Hälfte ist massiv
                w, d = w, d * 0.5
            if t == "mine":
                w, d = 7, 4
            out.append({"k": "box", "x": p["x"], "z": p["z"], "w": w, "d": d, "r": p.get("r", 0.0)})
        elif t == "tower":
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": p["rad"]})
        elif t == "pillar":
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": 1.6 if p.get("big") else 1.0})
        elif t in _CIRCLE and _CIRCLE[t]:
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": _CIRCLE[t] * p.get("s", 1.0)})
        elif t in ("tree", "pine", "birch"):
            out.append({"k": "circle", "x": p["x"], "z": p["z"], "rad": 0.45 * p.get("s", 1.0)})
        elif t == "rock" and p.get("s", 1.0) > 0.8:
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


@lru_cache(maxsize=None)
def gruenmark_props() -> list[dict]:
    """Feste Requisiten plus prozedural verteilte Bäume, Büsche und Felsen."""
    hm = gruenmark_heightmap()
    rng = random.Random(4711)
    fixed = list(W.PROPS)
    occupied = [(p["x"], p["z"], _footprint_radius(p) + 3.5) for p in fixed if "x" in p]
    segs = [(p["x1"], p["z1"], p["x2"], p["z2"]) for p in fixed if "x1" in p]
    for f in W.FLATTEN[:2]:   # Dorf und Burg frei halten
        occupied.append((f["x"], f["z"], f["r"] - 4))
    for npc_like in _special_points():
        occupied.append((npc_like[0], npc_like[1], 6))
    for wtr in W.WATER:
        occupied.append((wtr["x"], wtr["z"], wtr["r"] + 2))
    fields = [p for p in fixed if p["t"] == "field"]

    def free(x, z, margin=0.0):
        if abs(x) > 228 or abs(z) > 228:
            return False
        if road_distance(x, z) < 3.5:
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

    out = []

    def forest_density(x, z):
        d = 0.08 + 0.12 * (fbm(x * 0.02, z * 0.02, 3, 21) + 1)
        # Wolfsforst im Westen/Nordwesten
        dist_forest = math.hypot(x + 135, z + 55)
        d += 0.9 * (1 - smoothstep(30, 95, dist_forest))
        # Waldrand im Norden hinter der Burg und im Süden
        d += 0.35 * (1 - smoothstep(10, 60, math.hypot(x + 80, z + 150)))
        d += 0.35 * (1 - smoothstep(10, 60, math.hypot(x - 40, z - 170)))
        d += 0.25 * (1 - smoothstep(10, 50, math.hypot(x + 170, z - 40)))
        # Gebirgsrand
        ring = (abs(x) ** 4 + abs(z) ** 4) ** 0.25
        d += 0.5 * smoothstep(165, 195, ring) * (1 - smoothstep(205, 225, ring))
        return d

    attempts = 0
    while len(out) < 1500 and attempts < 30000:
        attempts += 1
        x = rng.uniform(-226, 226)
        z = rng.uniform(-226, 226)
        if rng.random() > forest_density(x, z):
            continue
        if not free(x, z):
            continue
        h = hm.height(x, z)
        ring = (abs(x) ** 4 + abs(z) ** 4) ** 0.25
        if ring > 190 or h > 14 or math.hypot(x + 135, z + 55) < 70 and rng.random() < 0.3:
            kind = "pine"
        elif math.hypot(x + 70, z) < 50 and rng.random() < 0.6:
            kind = "birch"
        else:
            kind = "tree"
        s = rng.uniform(0.8, 1.35)
        out.append({"t": kind, "x": round(x, 1), "z": round(z, 1), "s": round(s, 2),
                    "r": round(rng.uniform(0, math.tau), 2)})
        occupied.append((x, z, 2.2 * s))

    # Büsche und Felsen
    for _ in range(420):
        x = rng.uniform(-224, 224)
        z = rng.uniform(-224, 224)
        if not free(x, z):
            continue
        ring = (abs(x) ** 4 + abs(z) ** 4) ** 0.25
        if ring > 180 and rng.random() < 0.7 or rng.random() < 0.3:
            s = rng.uniform(0.5, 1.8) if ring < 180 else rng.uniform(1.2, 3.2)
            out.append({"t": "rock", "x": round(x, 1), "z": round(z, 1), "s": round(s, 2),
                        "r": round(rng.uniform(0, math.tau), 2)})
        else:
            out.append({"t": "bush", "x": round(x, 1), "z": round(z, 1), "s": round(rng.uniform(0.7, 1.3), 2),
                        "r": round(rng.uniform(0, math.tau), 2)})
    # Blumenwiesen (rein dekorativ, ohne Kollision)
    for _ in range(260):
        x = rng.uniform(-170, 170)
        z = rng.uniform(-170, 170)
        if road_distance(x, z) < 2 or math.hypot(x - 2, z - 18) < 14:
            continue
        if any((x - wx["x"]) ** 2 + (z - wx["z"]) ** 2 < (wx["r"] + 1) ** 2 for wx in W.WATER):
            continue
        out.append({"t": "flowers", "x": round(x, 1), "z": round(z, 1), "s": round(rng.uniform(0.7, 1.4), 2),
                    "v": rng.randint(0, 3)})
    return fixed + out


def _special_points():
    from .content.npcs import NPCS
    pts = [(n["pos"][0], n["pos"][1]) for n in NPCS.values() if n["zone"] == "gruenmark"]
    for s in W.SPAWNS["gruenmark"]:
        if "pos" in s:
            pts.append(tuple(s["pos"]))
    for o in W.OBJECTS["gruenmark"]:
        pts.append(tuple(o["pos"]))
    for p in W.PORTALS["gruenmark"]:
        pts.append((p["x"], p["z"]))
    return pts


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
        # Breitensuche über benachbarte Rechtecke
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
        # Ist der Wegpunkt erreicht, direkt ins nächste Rechteck weiterlaufen
        if math.hypot(cx - sx, cz - sz) < 1.0:
            r = self.rects[node]
            return (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        return cx, cz


@lru_cache(maxsize=None)
def krypta_nav() -> RectNav:
    return RectNav(W.KRYPTA_RECTS)


def zone_static_data(zone_id: str) -> dict:
    """Alles, was der Client zum Aufbau einer Zone braucht."""
    z = W.ZONES[zone_id]
    data = {
        "id": zone_id,
        "name": z["name"],
        "type": z["type"],
        "sky": z["sky"],
        "portals": W.PORTALS.get(zone_id, []),
    }
    if zone_id == "gruenmark":
        hm = gruenmark_heightmap()
        props = gruenmark_props()
        data.update({
            "size": hm.size, "step": hm.step, "n": hm.n, "heights": hm.encoded(),
            "water": W.WATER, "roads": W.ROADS, "plaza": W.PLAZA, "props": props,
            "obstacles": obstacles_for(props), "subzones": W.SUBZONES,
            "graveyard": z["graveyard"],
        })
    else:
        data.update({
            "rects": W.KRYPTA_RECTS, "rooms": W.KRYPTA_ROOMS, "props": W.KRYPTA_PROPS,
            "obstacles": obstacles_for(W.KRYPTA_PROPS),
        })
    return data
