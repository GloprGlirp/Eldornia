"""Gegnervorlagen (Mobs) für Grünmark und die Vergessene Krypta.

family: "tier" (keine Münzen), "humanoid" (flieht bei wenig Leben), "untot", "kleintier"
aggro:  True = greift Spieler in Reichweite an (rot), False = neutral (gelb)
"""

MOBS = {
    # ------------------------------------------------------------------ Kleintiere
    "kaninchen": {
        "name": "Kaninchen", "lvl": [1, 1], "family": "kleintier", "model": "rabbit", "scale": 1.0,
        "hp_mult": 0.08, "dmg_mult": 0.0, "aggro": False, "critter": True, "respawn": 30, "radius": 0.3,
        "loot": [{"item": "kaninchenpfote", "chance": 0.5}], "wander": 10,
    },
    "huhn": {
        "name": "Huhn", "lvl": [1, 1], "family": "kleintier", "model": "chicken", "scale": 1.0,
        "hp_mult": 0.08, "dmg_mult": 0.0, "aggro": False, "critter": True, "respawn": 30, "radius": 0.3,
        "loot": [], "wander": 6,
    },
    "uebungspuppe": {
        "name": "Übungspuppe", "lvl": [1, 1], "family": "objekt", "model": "dummy", "scale": 1.0,
        "hp_mult": 400.0, "dmg_mult": 0.0, "aggro": False, "respawn": 5, "radius": 0.6, "wander": 0,
        "loot": [], "dummy": True, "level_as_attacker": True,
    },
    # ------------------------------------------------------------------ Grünmark
    "waldwolf": {
        "name": "Waldwolf", "lvl": [1, 3], "family": "tier", "model": "wolf", "scale": 1.0,
        "hp_mult": 1.0, "dmg_mult": 1.0, "aggro": True, "respawn": 45, "radius": 0.7, "wander": 10,
        "loot": [
            {"item": "wolfsfell", "chance": 0.55},
            {"item": "reisszahn", "chance": 0.35},
        ],
        "world_drop": 0.05,
    },
    "graumaehne": {
        "name": "Graumähne", "title": "Rudelführer", "lvl": [4, 4], "family": "tier", "model": "wolf", "scale": 1.5,
        "hp_mult": 2.2, "dmg_mult": 1.3, "aggro": True, "respawn": 240, "radius": 1.0, "wander": 6, "elite": True,
        "rare": True, "tint": "#8a8f99",
        "loot": [{"item": "wolfsfellumhang", "chance": 0.6}, {"item": "wolfszahnaxt", "chance": 0.4}],
        "abilities": [{"id": "biss", "name": "Zerfleischen", "kind": "strike", "cd": 8, "first": 4, "mult": 1.8}],
    },
    "wildschwein": {
        "name": "Wildschwein", "lvl": [2, 4], "family": "tier", "model": "boar", "scale": 1.0,
        "hp_mult": 1.1, "dmg_mult": 0.95, "aggro": False, "respawn": 45, "radius": 0.8, "wander": 12,
        "loot": [
            {"item": "wildschweinkeule", "chance": 0.6, "quest": "wildschweinbraten"},
            {"item": "schweineblase", "chance": 0.45, "quest": "baelle_fuer_den_gaukler"},
            {"item": "zaehes_fleisch", "chance": 0.4},
        ],
        "world_drop": 0.05,
    },
    "bandit": {
        "name": "Rotdolch-Schläger", "lvl": [4, 6], "family": "humanoid", "model": "bandit", "scale": 1.0,
        "hp_mult": 1.0, "dmg_mult": 1.0, "aggro": True, "respawn": 50, "radius": 0.5, "wander": 6, "social": 10,
        "copper": [6, 18],
        "loot": [
            {"item": "leonines_medaillon", "chance": 0.3, "quest": "das_verlorene_medaillon"},
            {"item": "rotdolch_abzeichen", "chance": 0.4},
            {"item": "brot", "chance": 0.12},
        ],
        "world_drop": 0.07,
        "abilities": [{"id": "stich", "name": "Hinterhältiger Stich", "kind": "strike", "cd": 9, "first": 5, "mult": 1.5}],
    },
    "armbrustschuetze": {
        "name": "Rotdolch-Armbrustschütze", "lvl": [4, 6], "family": "humanoid", "model": "bandit_archer",
        "scale": 1.0, "hp_mult": 0.85, "dmg_mult": 0.9, "aggro": True, "respawn": 50, "radius": 0.5, "wander": 3,
        "social": 10, "copper": [6, 18],
        "ranged": {"range": 25, "name": "Armbrustschuss", "school": "physical", "cd": 2.6, "mult": 1.0},
        "loot": [
            {"item": "leonines_medaillon", "chance": 0.3, "quest": "das_verlorene_medaillon"},
            {"item": "rotdolch_abzeichen", "chance": 0.4},
        ],
        "world_drop": 0.07,
    },
    "grimbart": {
        "name": "Grimbart Rotdolch", "title": "Anführer der Rotdolche", "lvl": [7, 7], "family": "humanoid",
        "model": "bandit_boss", "scale": 1.35, "hp_mult": 3.2, "dmg_mult": 1.35, "aggro": True, "respawn": 180,
        "radius": 0.8, "wander": 0, "elite": True, "copper": [180, 260], "social": 15,
        "loot": [
            {"item": "grimbarts_dolch", "chance": 0.5},
            {"item": "rotdolch_brecher", "chance": 0.5},
            {"item": "rotdolch_kopftuch", "chance": 0.4},
        ],
        "abilities": [
            {"id": "maechtiger_schlag", "name": "Mächtiger Schlag", "kind": "strike", "cd": 10, "first": 6, "mult": 2.0},
            {"id": "wirbelwind", "name": "Wirbelwind", "kind": "telegraph_circle_self", "cd": 14, "first": 3,
             "radius": 6, "warn": 1.8, "mult": 2.2, "hp_below": 0.6,
             "yell": "Ihr wollt meinen Schatz? Dann tanzt mit meinen Klingen!"},
        ],
        "aggro_yell": "Wer wagt es, mein Lager zu betreten?! Schnappt sie euch, Jungs!",
        "death_yell": "Das ... war ... mein ... Lieblingsdolch ...",
    },
    "tunnelkobold": {
        "name": "Tunnelkobold", "lvl": [5, 7], "family": "humanoid", "model": "kobold", "scale": 0.8,
        "hp_mult": 0.95, "dmg_mult": 1.0, "aggro": True, "respawn": 45, "radius": 0.5, "wander": 6, "social": 8,
        "copper": [4, 14],
        "loot": [
            {"item": "kobold_kerze", "chance": 0.55, "quest": "kerzen_der_tiefe"},
            {"item": "kobold_loeffel", "chance": 0.4},
        ],
        "world_drop": 0.06,
        "aggro_say": ["Du nicht nehmen Kerze!", "Kerze gehört uns!", "Weg da, Großfuß!"],
    },
    "kobold_geomant": {
        "name": "Kobold-Geomant", "lvl": [6, 7], "family": "humanoid", "model": "kobold_caster", "scale": 0.85,
        "hp_mult": 0.8, "dmg_mult": 0.8, "aggro": True, "respawn": 50, "radius": 0.5, "wander": 3, "social": 8,
        "copper": [6, 16],
        "ranged": {"range": 25, "name": "Steinsplitter", "school": "nature", "cd": 3.5, "cast": 2.0, "mult": 1.6},
        "loot": [
            {"item": "kobold_kerze", "chance": 0.55, "quest": "kerzen_der_tiefe"},
            {"item": "kobold_loeffel", "chance": 0.4},
        ],
        "world_drop": 0.08,
    },
    # ------------------------------------------------------------------ Vergessene Krypta
    "skelett": {
        "name": "Ruheloses Skelett", "lvl": [8, 9], "family": "untot", "model": "skeleton", "scale": 1.0,
        "hp_mult": 1.1, "dmg_mult": 1.0, "aggro": True, "respawn": 0, "radius": 0.5, "wander": 0, "social": 12,
        "copper": [10, 25],
        "loot": [{"item": "knochensplitter", "chance": 0.5}, {"item": "vergilbter_schaedel", "chance": 0.2}],
        "world_drop": 0.1,
    },
    "knochenmagier": {
        "name": "Knochenmagier", "lvl": [9, 9], "family": "untot", "model": "skeleton_mage", "scale": 1.0,
        "hp_mult": 0.9, "dmg_mult": 0.9, "aggro": True, "respawn": 0, "radius": 0.5, "wander": 0, "social": 12,
        "copper": [12, 28],
        "ranged": {"range": 28, "name": "Schattenblitz", "school": "shadow", "cd": 3.0, "cast": 2.5, "mult": 1.9},
        "loot": [{"item": "knochensplitter", "chance": 0.5}, {"item": "knochenmagier_kappe", "chance": 0.08}],
        "world_drop": 0.1,
    },
    "grabwaechter": {
        "name": "Grabwächter", "lvl": [9, 9], "family": "untot", "model": "skeleton_guard", "scale": 1.45,
        "hp_mult": 2.6, "dmg_mult": 1.3, "aggro": True, "respawn": 0, "radius": 0.9, "wander": 0, "elite": True,
        "social": 12, "copper": [60, 90],
        "loot": [
            {"item": "grabwaechter_schultern", "chance": 0.3},
            {"item": "umhang_grabesruhe", "chance": 0.3},
            {"item": "wiedergaenger_stiefel", "chance": 0.25},
            {"item": "ring_der_vergessenen", "chance": 0.15},
        ],
        "abilities": [{"id": "zerschmettern", "name": "Zerschmettern", "kind": "strike", "cd": 11, "first": 5, "mult": 2.0}],
    },
    "erweckter": {
        "name": "Erweckter Diener", "lvl": [8, 8], "family": "untot", "model": "skeleton", "scale": 0.9,
        "hp_mult": 0.6, "dmg_mult": 0.7, "aggro": True, "respawn": 0, "radius": 0.5, "wander": 0,
        "loot": [], "summoned": True, "tint": "#7affc8",
    },
    "morgrath": {
        "name": "Sir Morgrath", "title": "Der Gefallene", "lvl": [10, 10], "family": "untot", "model": "death_knight",
        "scale": 1.9, "hp_mult": 6.0, "dmg_mult": 1.25, "aggro": True, "respawn": 0, "radius": 1.6, "wander": 0,
        "elite": True, "boss": True, "copper": [500, 800], "leash": 999, "aggro_radius": 18,
        "loot": [
            {"item": "morgraths_siegel", "chance": 1.0, "quest": "die_vergessene_krypta"},
        ],
        "boss_loot": {
            "epics": ["morgraths_seelenklinge", "schild_des_gefallenen", "stab_verlorener_seelen",
                      "kapuze_der_grabesstille", "morgraths_helm"],
            "blues": ["leichentuchrobe", "grabwaechter_schultern", "umhang_grabesruhe", "ring_der_vergessenen"],
            "legendary": "eldornias_traene", "legendary_chance": 0.03,
        },
        "abilities": [
            {"id": "grabesschlag", "name": "Grabesschlag", "kind": "telegraph_cone", "cd": 12, "first": 7,
             "radius": 10, "angle": 100, "warn": 1.6, "mult": 3.0},
            {"id": "diener", "name": "Erhebt euch!", "kind": "summon", "hp_below": 0.6, "once": True,
             "summon": "erweckter", "count": 3,
             "yell": "Erhebt euch, meine treuen Diener! Verteidigt euren Herrn!"},
            {"id": "zorn", "name": "Ewiger Zorn", "kind": "enrage", "hp_below": 0.3, "once": True,
             "yell": "Ich habe diesen Ort tausend Jahre bewacht ... ich werde nicht fallen!"},
            {"id": "seelenfeuer", "name": "Seelenfeuer", "kind": "telegraph_circles_players", "cd": 9, "first": 2,
             "radius": 4, "warn": 2.0, "flat": 130, "school": "shadow", "hp_below": 0.3, "count": 3},
        ],
        "aggro_yell": "Wer stört meine ewige Wacht? Ihr werdet hier neben mir ruhen!",
        "death_yell": "Jonas ... mein Schüler ... vergib ... mir ...",
        "evade_yell": "Ruht in Frieden ... in meiner Krypta.",
    },
}

for _id, _m in MOBS.items():
    _m["id"] = _id
    _m.setdefault("title", "")
    _m.setdefault("abilities", [])
    _m.setdefault("elite", False)
    _m.setdefault("boss", False)
    _m.setdefault("rare", False)
    _m.setdefault("critter", False)
    _m.setdefault("copper", None)
    _m.setdefault("world_drop", 0.0)
    _m.setdefault("social", 0)
    _m.setdefault("tint", None)
    _m.setdefault("dummy", False)
    _m.setdefault("summoned", False)
    _m.setdefault("ranged", None)
    _m.setdefault("speed", 2.0)


def mob_max_hp(tpl: dict, level: int) -> int:
    return max(1, int((30 + 25 * level) * tpl["hp_mult"]))


def mob_damage(tpl: dict, level: int) -> tuple[int, int]:
    lo = (2 + 2.0 * level) * tpl["dmg_mult"]
    hi = (4 + 2.6 * level) * tpl["dmg_mult"]
    return int(round(lo)), max(int(round(lo)), int(round(hi)))


def mob_armor(tpl: dict, level: int) -> int:
    mult = 1.5 if tpl.get("elite") else 1.0
    return int(20 * level * mult)


def mob_xp(tpl: dict, mob_level: int, player_level: int) -> int:
    """Erfahrung nach WoW-Classic-Formel (vereinfacht)."""
    if tpl.get("critter") or tpl.get("summoned"):
        return 0
    base = player_level * 5 + 45
    diff = mob_level - player_level
    if diff >= 0:
        xp = base * (1 + 0.05 * min(diff, 4))
    else:
        zero_diff = 5 if player_level < 8 else 6
        if -diff >= zero_diff:
            return 0
        xp = base * (1 - (-diff) / zero_diff)
    if tpl.get("elite"):
        xp *= 2
    if tpl.get("boss"):
        xp *= 2.5
    return int(xp)
