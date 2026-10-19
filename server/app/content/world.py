"""Weltaufbau von Eldornia: sammelt Zonen, Gegner, NPCs, Spawns, Objekte und Quests aller Regionen.

Regionen (GDD 2): Grünmark (1–10), Frostklamm (10–25), Mondhain (20–35), Aschenlande (30–50),
Himmelsbruch (Endgame). Dazu instanzierte Dungeons (GDD 6) und die PvP-Arena (GDD 10).
"""
from __future__ import annotations

import importlib

from . import items as I
from .mobs import COMMON

WORLD_NAME = "Eldornia"

ZONE_MODULES = ["gruenmark", "krypta", "hoehle", "frostklamm", "schmiede", "mondhain", "aschenlande", "kathedrale",
                "himmelsbruch", "thron", "arena"]
QUEST_MODULES = ["gruenmark", "frostklamm", "mondhain", "aschenlande", "himmelsbruch"]

ZONES: dict[str, dict] = {}
MOBS: dict[str, dict] = {}
NPCS: dict[str, dict] = {}
SPAWNS: dict[str, list] = {}
OBJECTS: dict[str, list] = {}
QUESTS: dict[str, dict] = {}

for _name in ZONE_MODULES:
    try:
        _m = importlib.import_module(f".zones.{_name}", __package__)
    except ModuleNotFoundError as _e:  # Region noch nicht vorhanden
        if _name not in str(_e):
            raise
        continue
    _z = _m.ZONE
    ZONES[_z["id"]] = _z
    for _nid, _n in getattr(_m, "NPCS", {}).items():
        _n["id"] = _nid
        _n["zone"] = _z["id"]
        NPCS[_nid] = _n
    for _mid, _mob in getattr(_m, "MOBS", {}).items():
        _mob["id"] = _mid
        _mob.setdefault("zone", _z["id"])
        MOBS[_mid] = _mob
    SPAWNS[_z["id"]] = list(getattr(_m, "SPAWNS", []))
    OBJECTS[_z["id"]] = list(getattr(_m, "OBJECTS", []))

for _mid, _mob in COMMON.items():
    MOBS.setdefault(_mid, _mob)

for _mob in MOBS.values():
    _mob.setdefault("abilities", [])
    _mob.setdefault("loot", [])
    _mob.setdefault("title", "")
    _mob.setdefault("respawn", 60)

for _name in QUEST_MODULES:
    try:
        _q = importlib.import_module(f".quests.{_name}", __package__)
    except ModuleNotFoundError as _e:
        if _name not in str(_e):
            raise
        continue
    for _qid, _quest in _q.QUESTS.items():
        _quest["id"] = _qid
        _quest.setdefault("zone", _name)
        QUESTS[_qid] = _quest

for _quest in QUESTS.values():
    _quest.setdefault("objectives", [])
    _quest.setdefault("rewards", {})
    _quest.setdefault("type", "side")
    _quest.setdefault("min_level", 1)
    _quest.setdefault("level", _quest["min_level"])
    _quest.setdefault("progress", "Habt Ihr es erledigt?")
    _quest.setdefault("complete", "Habt Dank!")
    _quest.setdefault("objective", "")

# Questgegenstände -> Quests (Questgegenstände droppen nur, solange sie benötigt werden)
ITEM_QUESTS: dict[str, list[str]] = {}
for _qid, _quest in QUESTS.items():
    for _o in _quest["objectives"]:
        if _o["type"] == "collect":
            ITEM_QUESTS.setdefault(_o["item"], []).append(_qid)

QUESTS_BY_GIVER: dict[str, list[str]] = {}
QUESTS_BY_ENDER: dict[str, list[str]] = {}
for _qid, _quest in QUESTS.items():
    QUESTS_BY_GIVER.setdefault(_quest["giver"], []).append(_qid)
    QUESTS_BY_ENDER.setdefault(_quest["ender"], []).append(_qid)
    if _quest.get("start_item"):
        pass

# ============================================================================== Dungeon-Modi (GDD 6)
MODES = {
    "normal": {"name": "Normal", "hp": 1.0, "dmg": 1.0, "loot_bonus": 0.0, "level_add": 0, "marks": 1,
               "desc": "Für die erste Erkundung und das Erlernen der Mechaniken."},
    "heroisch": {"name": "Heroisch", "hp": 1.6, "dmg": 1.35, "loot_bonus": 0.35, "level_add": 3, "marks": 2, "q_up": 0.3,
                 "desc": "Stärkere Gegner und bessere Beute."},
    "mythisch": {"name": "Mythisch", "hp": 2.4, "dmg": 1.7, "loot_bonus": 0.7, "level_add": 5, "marks": 4, "q_up": 0.6,
                 "affixes": True, "desc": "Anspruchsvolle Mechaniken, besondere Modifikatoren und sehr seltene Drops."},
}

# Mythische Modifikatoren (rotieren wöchentlich)
AFFIXES = {
    "wuetend": {"name": "Wütend", "desc": "Gegner geraten unter 30 % Gesundheit in Raserei (+50 % Schaden)."},
    "bebend": {"name": "Bebend", "desc": "Der Boden erbebt regelmäßig unter allen Spielern."},
    "verstaerkt": {"name": "Verstärkt", "desc": "Gegner, die in der Nähe sterben, stärken ihre Verbündeten."},
    "nekrotisch": {"name": "Nekrotisch", "desc": "Nahkampftreffer der Gegner verringern erhaltene Heilung."},
    "vulkanisch": {"name": "Vulkanisch", "desc": "Unter Spielern brechen Feuerflächen auf."},
}

DUNGEONS = {zid: z for zid, z in ZONES.items() if z["type"] == "dungeon"}
REGIONS = [zid for zid, z in ZONES.items() if z.get("region")]


def zone_portals(zone_id: str) -> list[dict]:
    return ZONES[zone_id].get("portals", [])


def all_stones() -> dict[str, dict]:
    out = {}
    for zid, z in ZONES.items():
        for s in z.get("stones", []):
            out[s["id"]] = dict(s, zone=zid)
    return out


STONES = all_stones()


def quest_item_ids() -> set[str]:
    return {i for i, it in I.ITEMS.items() if it.get("quest")}
