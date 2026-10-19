"""Klassendefinitionen. Zum Start spielbar: Ritter und Magier (siehe GDD, Abschnitt 16).

Weitere Klassen aus dem GDD (Räuber, Samurai, Bogenschütze, Barbar, Druide, Totenbeschwörer)
sind als "geplant" hinterlegt und werden in der Charaktererstellung angezeigt, aber noch gesperrt.
"""

CLASSES = {
    "ritter": {
        "name": "Ritter",
        "role": "Tank / Nahkampf",
        "desc": "Schwert und Schild. Hohe Verteidigung, baut im Kampf Wut auf und hält Gegner mit Herausforderung bei sich. "
                "Ideal, um Gruppenbosse zu tanken.",
        "resource": "rage",
        "hp_per_level": 22,
        "color": "#C79C6E",
        "armor_types": ["platte", "kette", "leder", "stoff"],
        "weapon_types": ["schwert", "axt", "streitkolben", "dolch"],
        "offhand_types": ["schild"],
        "abilities": ["wuchtschlag", "ansturm", "herausforderung", "bebenhieb", "schildstoss", "gnadenstoss", "schlachtruf"],
        "start_items": {
            "equip": {"main_hand": "rostiges_langschwert", "off_hand": "holzschild", "chest": "rekrutenweste",
                      "legs": "rekrutenhose", "feet": "abgetragene_stiefel"},
            "bags": [("brot", 5), ("heiltrank", 1)],
        },
        "playable": True,
    },
    "magier": {
        "name": "Magier",
        "role": "Fernkampf / Flächenschaden",
        "desc": "Feuer-, Frost- und Arkanmagie. Großer Schaden auf Distanz, aber verwundbar. Verlangsamt Gegner "
                "und friert sie fest.",
        "resource": "mana",
        "hp_per_level": 16,
        "color": "#69CCF0",
        "armor_types": ["stoff"],
        "weapon_types": ["stab", "dolch"],
        "offhand_types": ["buch"],
        "abilities": ["feuerball", "frostpfeil", "flammenstoss", "eisring", "phasensprung", "arkansalve", "frostpanzer"],
        "start_items": {
            "equip": {"main_hand": "lehrlingsstab", "chest": "lehrlingsrobe", "feet": "lehrlingsschuhe"},
            "bags": [("quellwasser", 5), ("brot", 2), ("manatrank", 1)],
        },
        "playable": True,
    },
}

PLANNED_CLASSES = [
    {"id": "raeuber", "name": "Räuber", "role": "Assassine / Burst-Schaden", "color": "#FFF569"},
    {"id": "samurai", "name": "Samurai", "role": "Präzision / Konter", "color": "#E05050"},
    {"id": "bogenschuetze", "name": "Bogenschütze", "role": "Präzisions-Fernkampf", "color": "#ABD473"},
    {"id": "barbar", "name": "Barbar", "role": "Berserker", "color": "#A0522D"},
    {"id": "druide", "name": "Druide", "role": "Heilung / Naturmagie", "color": "#FF7D0A"},
    {"id": "totenbeschwoerer", "name": "Totenbeschwörer", "role": "Beschwörung / Kontrolle", "color": "#9482C9"},
]


def base_stats(class_id: str, level: int) -> dict:
    """Grundattribute je Klasse und Stufe (ohne Ausrüstung).

    str Stärke, agi Beweglichkeit, sta Ausdauer, int Intelligenz, spi Willenskraft
    """
    if class_id == "ritter":
        return {
            "str": 10 + 2 * level,
            "agi": 6 + level,
            "sta": 5 + level,
            "int": 3,
            "spi": 4 + level // 2,
        }
    return {
        "str": 3,
        "agi": 4 + level // 2,
        "sta": 3 + level // 2,
        "int": 8 + 2 * level,
        "spi": 8 + (3 * level) // 2,
    }


# Erfahrung bis zur nächsten Stufe (Index = aktuelle Stufe)
XP_TABLE = [0, 250, 500, 800, 1100, 1500, 1900, 2400, 2900, 3500, 4200]
MAX_LEVEL = 10


def xp_to_next(level: int) -> int:
    if level >= MAX_LEVEL:
        return 0
    return XP_TABLE[level]
