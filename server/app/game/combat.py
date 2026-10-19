"""Kampfformeln im Stil von World of Warcraft (vereinfacht).

Angriffstabelle Nahkampf: Verfehlen → Ausweichen → Parieren → Blocken → Kritisch → Treffer
Zauber: Verfehlen (Widerstehen) → Kritisch → Treffer
Positionierung: Angriffe von hinten können nicht pariert oder geblockt werden.
Widerstände & Schwächen: Gegner haben je Schadensschule eigene Werte (z. B. Feuer -50 % = Schwäche).
"""
from __future__ import annotations

import random

from .entities import Mob, Player, Unit


def armor_reduction(armor: float, attacker_level: int) -> float:
    r = armor / (armor + 400.0 + 85.0 * attacker_level)
    return max(0.0, min(0.75, r))


def unit_armor(u: Unit) -> float:
    if isinstance(u, Player):
        return u.stats.get("armor", 0)
    if isinstance(u, Mob):
        return max(0.0, u.armor + u.aura_stat("armor"))
    return 0.0


def resist_mult(dst: Unit, school: str, attacker_level: int) -> float:
    """Multiplikator für magischen Schaden einer Schule (Widerstand oder Schwäche)."""
    if school == "physical":
        return 1.0
    if isinstance(dst, Mob):
        r = dst.resist.get(school, 0.0)       # -0.5 = 50 % Schwäche, 0.5 = 50 % Widerstand
        return max(0.0, 1.0 - r)
    res = dst.resist.get(school, 0.0) if dst.resist else 0.0
    res += dst.aura_stat(school + "_res")
    red = res / (res + 5.0 * attacker_level + 50.0)
    return max(0.25, 1.0 - min(0.75, red))


def resource_conversion(level: int) -> float:
    return 0.0091107836 * level * level + 3.225598133 * level + 4.2652911


def melee_outcome(att: Unit, tgt: Unit, front: bool, crit_bonus: float = 0.0, ranged: bool = False) -> str:
    """Würfelt das Ergebnis eines Nahkampf- oder Fernkampfangriffs aus."""
    lvl_diff = tgt.level - att.level
    miss = 5.0 + max(0, lvl_diff) * 1.5 - max(0, -lvl_diff) * 0.5
    dodge = parry = block = 0.0
    if isinstance(tgt, Player):
        dodge = tgt.stats.get("dodge", 3)
        if front and not ranged:
            parry = tgt.stats.get("parry", 0)
            block = tgt.stats.get("block", 0)
        for a in tgt.auras:
            if a.parry_all and front and not ranged:
                return "parry"
            if a.block_all and front and not ranged:
                return "block"
    elif isinstance(tgt, Mob):
        fam = tgt.tpl.get("family")
        dodge = 0.0 if tgt.look.get("dummy") else 5.0
        if front and not ranged and fam in ("humanoid", "untot", "daemon", "zwerg"):
            parry = 5.0
    if ranged:
        dodge *= 0.5
    if isinstance(att, Player):
        crit = att.stats.get("crit", 5)
    else:
        crit = 5.0
    crit += crit_bonus
    if tgt.incapacitated:
        dodge = parry = block = 0.0
    roll = random.uniform(0, 100)
    for name, chance in (("miss", max(0.0, miss)), ("dodge", dodge), ("parry", parry), ("block", block), ("crit", crit)):
        if roll < chance:
            return name
        roll -= chance
    return "hit"


def spell_outcome(att: Unit, tgt: Unit, crit_bonus: float = 0.0, heal: bool = False) -> str:
    lvl_diff = tgt.level - att.level
    miss = 0.0 if heal else 4.0 + max(0, min(3, lvl_diff)) * 1.0 + max(0, lvl_diff - 3) * 9.0
    crit = att.stats.get("spell_crit", 5) if isinstance(att, Player) else 5.0
    crit += crit_bonus
    roll = random.uniform(0, 100)
    if roll < miss:
        return "miss"
    if roll < miss + crit:
        return "crit"
    return "hit"


def player_melee_damage(p: Player, mult: float = 1.0, extra: float = 0.0, off: bool = False) -> float:
    st = p.stats
    if off:
        return random.randint(st.get("oh_min", 1), max(st.get("oh_min", 1), st.get("oh_max", 2))) * mult + extra
    return random.randint(st["dmg_min"], max(st["dmg_min"], st["dmg_max"])) * mult + extra


def mob_melee_damage(m: Mob, mult: float = 1.0) -> float:
    lo, hi = m.dmg
    return max(1.0, random.randint(lo, max(lo, hi)) * mult * (1.0 + m.aura_pct("dmg_done") / 100.0))


def group_xp_factor(n: int) -> float:
    return {1: 1.0, 2: 1.0, 3: 1.166, 4: 1.3, 5: 1.4}.get(n, 1.4)
