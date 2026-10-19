"""Kampfformeln im Stil von World of Warcraft (vereinfacht).

Angriffstabelle Nahkampf: Verfehlen → Ausweichen → Parieren → Blocken → Kritisch → Treffer
Zauber: Verfehlen → Kritisch → Treffer
"""
from __future__ import annotations

import random

from .entities import Mob, Player


def armor_reduction(armor: float, attacker_level: int) -> float:
    r = armor / (armor + 400.0 + 85.0 * attacker_level)
    return max(0.0, min(0.75, r))


def unit_armor(u) -> float:
    if isinstance(u, Player):
        return u.stats.get("armor", 0) + 0
    if isinstance(u, Mob):
        return u.armor + u.aura_stat("armor")
    return 0.0


def rage_conversion(level: int) -> float:
    return 0.0091107836 * level * level + 3.225598133 * level + 4.2652911


def melee_outcome(att, tgt, front: bool) -> str:
    """Würfelt das Ergebnis eines Nahkampfangriffs aus."""
    lvl_diff = tgt.level - att.level
    miss = 5.0 + max(0, lvl_diff) * 1.5 - max(0, -lvl_diff) * 0.5
    if isinstance(tgt, Player):
        dodge = tgt.stats.get("dodge", 3)
        parry = tgt.stats.get("parry", 0) if front else 0.0
        block = tgt.stats.get("block", 0) if front else 0.0
    else:
        fam = tgt.tpl.get("family") if isinstance(tgt, Mob) else ""
        dodge = 5.0 if not tgt.look.get("dummy") else 0.0
        parry = 5.0 if front and fam in ("humanoid", "untot") else 0.0
        block = 0.0
    if isinstance(att, Player):
        crit = att.stats.get("crit", 5)
    else:
        crit = 5.0
    roll = random.uniform(0, 100)
    for name, chance in (("miss", miss), ("dodge", dodge), ("parry", parry), ("block", block), ("crit", crit)):
        if roll < chance:
            return name
        roll -= chance
    return "hit"


def spell_outcome(att, tgt) -> str:
    lvl_diff = tgt.level - att.level
    miss = 4.0 + max(0, min(3, lvl_diff)) * 1.0 + max(0, lvl_diff - 3) * 9.0
    crit = att.stats.get("spell_crit", 5) if isinstance(att, Player) else 5.0
    roll = random.uniform(0, 100)
    if roll < miss:
        return "miss"
    if roll < miss + crit:
        return "crit"
    return "hit"


def player_melee_damage(p: Player, extra: int = 0) -> int:
    st = p.stats
    return random.randint(st["dmg_min"], max(st["dmg_min"], st["dmg_max"])) + extra


def mob_melee_damage(m: Mob, mult: float = 1.0) -> int:
    lo, hi = m.dmg
    enrage = 1.0 + max((a.enrage for a in m.auras), default=0.0)
    return max(1, int(random.randint(lo, max(lo, hi)) * mult * enrage))


def group_xp_factor(n: int) -> float:
    return {1: 1.0, 2: 1.0, 3: 1.166, 4: 1.3, 5: 1.4}.get(n, 1.4)
