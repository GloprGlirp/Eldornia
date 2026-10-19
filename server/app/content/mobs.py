"""Gegner-Formeln und allgemeine Vorlagen (Begleiter, Kleintiere, Übungspuppen).

Die Gegner der einzelnen Regionen stehen in content/zones/*.py.

family: tier, humanoid, untot, daemon, elementar, drache, riese, fee, mechanisch, kleintier, objekt, zwerg
aggro:  True = greift Spieler in Reichweite an (rot), False = neutral (gelb)
resist: {"fire": 0.5} = 50 % Feuerwiderstand, {"fire": -0.5} = 50 % Schwäche
"""


def mob_max_hp(tpl: dict, level: int) -> int:
    return max(1, int((30 + 25 * level + 0.6 * level * level) * tpl.get("hp_mult", 1.0)))


def mob_damage(tpl: dict, level: int) -> tuple[int, int]:
    m = tpl.get("dmg_mult", 1.0)
    lo = (2 + 2.0 * level + 0.03 * level * level) * m
    hi = (4 + 2.6 * level + 0.045 * level * level) * m
    return int(round(lo)), max(int(round(lo)), int(round(hi)))


def mob_armor(tpl: dict, level: int) -> int:
    mult = 1.5 if tpl.get("elite") else 1.0
    return int(20 * level * mult * tpl.get("armor_mult", 1.0))


def mob_xp(tpl: dict, mob_level: int, player_level: int) -> int:
    """Erfahrung nach WoW-Classic-Formel (vereinfacht)."""
    if tpl.get("critter") or tpl.get("summoned") or tpl.get("dummy") or tpl.get("pet"):
        return 0
    base = player_level * 5 + 45
    diff = mob_level - player_level
    if diff >= 0:
        xp = base * (1 + 0.05 * min(diff, 4))
    else:
        zero_diff = 5 if player_level < 8 else (6 if player_level < 20 else 8)
        if -diff >= zero_diff:
            return 0
        xp = base * (1 - (-diff) / zero_diff)
    if tpl.get("elite"):
        xp *= 2
    if tpl.get("boss"):
        xp *= 2.5
    return int(xp * tpl.get("xp_mult", 1.0))


# =============================================================================== Allgemeine Vorlagen
COMMON = {
    "kaninchen": {"name": "Kaninchen", "lvl": [1, 1], "family": "kleintier", "model": "rabbit", "hp_mult": 0.08,
                  "dmg_mult": 0.0, "critter": True, "respawn": 30, "radius": 0.3, "wander": 10,
                  "loot": [{"item": "kaninchenpfote", "chance": 0.5}]},
    "huhn": {"name": "Huhn", "lvl": [1, 1], "family": "kleintier", "model": "chicken", "hp_mult": 0.08, "dmg_mult": 0.0,
             "critter": True, "respawn": 30, "radius": 0.3, "wander": 6},
    "uebungspuppe": {"name": "Übungspuppe", "lvl": [1, 1], "family": "objekt", "model": "dummy", "hp_mult": 400.0,
                     "dmg_mult": 0.0, "respawn": 5, "radius": 0.6, "dummy": True},
    # ---------------------------------------------------------------- Begleiter (Spieler)
    "skelett_krieger": {"name": "Skelettkrieger", "lvl": [1, 1], "family": "untot", "model": "humanoid",
                        "look": {"kind": "skeleton", "held": "sword", "eye_glow": "#7affc8"}, "hp_mult": 0.55,
                        "dmg_mult": 0.5, "pet": True, "undead": True, "radius": 0.5, "speed": 2.2},
    "skelett_magier": {"name": "Skelettmagier", "lvl": [1, 1], "family": "untot", "model": "humanoid",
                       "look": {"kind": "skeleton", "held": "staff", "hood": True, "hood_color": "#2a2a3a", "eye_glow": "#c080ff"},
                       "hp_mult": 0.4, "dmg_mult": 0.25, "pet": True, "undead": True, "radius": 0.5,
                       "ranged": {"range": 28, "name": "Schattenblitz", "school": "shadow", "cd": 2.5, "cast": 1.8, "mult": 1.6}},
    "skelett_soldat": {"name": "Skelettsoldat", "lvl": [1, 1], "family": "untot", "model": "humanoid",
                       "look": {"kind": "skeleton", "held": "axe", "eye_glow": "#7affc8"}, "hp_mult": 0.35,
                       "dmg_mult": 0.35, "pet": True, "undead": True, "radius": 0.5},
    "knochengolem": {"name": "Knochengolem", "lvl": [1, 1], "family": "untot", "model": "golem",
                     "look": {"tint": "#e6dcc0", "glow": "#7affc8"}, "hp_mult": 1.6, "dmg_mult": 0.55, "pet": True,
                     "undead": True, "radius": 1.0, "scale": 0.8, "taunt_aura": True},
    "naturgeist": {"name": "Naturgeist", "lvl": [1, 1], "family": "fee", "model": "wisp", "look": {"tint": "#a0ffa0"},
                   "hp_mult": 0.4, "dmg_mult": 0.2, "pet": True, "radius": 0.4, "healer": True,
                   "ranged": {"range": 25, "name": "Dornenwurf", "school": "nature", "cd": 2.5, "mult": 1.2}},
    "begleitwolf": {"name": "Begleitwolf", "lvl": [1, 1], "family": "tier", "model": "wolf",
                    "look": {"tint": "#7a6a5a", "tint2": "#d8c8b0"}, "hp_mult": 0.7, "dmg_mult": 0.55, "pet": True, "radius": 0.7},
}
for _id, _m in COMMON.items():
    _m["id"] = _id
