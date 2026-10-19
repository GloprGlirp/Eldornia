"""Die acht spielbaren Klassen von Eldornia (GDD Abschnitt 3).

Ressourcen:
  mana          Magier, Druide, Totenbeschwörer – regeneriert sich, wenn 5 Sek. nichts verbraucht wurde
  resolve       Ritter "Entschlossenheit" – entsteht durch erlittenen Schaden, Blocken und Parieren
  rage          Barbar "Wut" – entsteht durch ausgeteilten und erlittenen Schaden, verfällt außerhalb des Kampfes
  energy        Räuber "Energie" – regeneriert 10 pro Sekunde, dazu Kombopunkte
  focus         Samurai "Fokus" – baut sich durch Treffer und Paraden auf
  concentration Bogenschütze "Konzentration" – regeneriert sich stetig
"""

MAX_LEVEL = 50

RESOURCES = {
    "mana": {"name": "Mana", "color": "#3a7cff", "max": None},
    "resolve": {"name": "Entschlossenheit", "color": "#d8c070", "max": 100},
    "rage": {"name": "Wut", "color": "#d02a2a", "max": 100},
    "energy": {"name": "Energie", "color": "#f0e040", "max": 100},
    "focus": {"name": "Fokus", "color": "#ff8a3a", "max": 100},
    "concentration": {"name": "Konzentration", "color": "#7ac04a", "max": 100},
}

CLASSES = {
    "ritter": {
        "name": "Ritter", "role": "Tank / Nahkampf", "difficulty": "Einsteigerfreundlich",
        "desc": "Schwert und Schild oder Zweihänder. Hohe Verteidigung, Schutzfähigkeiten, Spottangriffe und starke "
                "Konter. Ideal, um Gruppenbosse zu tanken.",
        "resource": "resolve", "color": "#C79C6E", "icon": "knight-banner",
        "armor": ["platte", "kette", "leder", "stoff"],
        "weapons": ["schwert", "streitkolben", "axt", "zweihandschwert", "kriegshammer"],
        "offhand": ["schild"], "dual_wield": False,
        "class_slot": "wappen", "class_slot_name": "Wappen",
        "base": {"str": (12, 2.2), "agi": (7, 1.0), "sta": (11, 2.0), "int": (4, 0.3), "spi": (5, 0.5)},
        "hp": (30, 18), "parry": 5.0, "block": 5.0,
        "ap": {"str": 2.0},
        "specs": ["waechter", "schwertmeister", "vernichter"],
        "start": {"equip": {"main_hand": "rostiges_langschwert", "off_hand": "abgenutzter_holzschild",
                            "chest": "gepolsterte_rekrutenweste", "legs": "rekrutenhose", "feet": "abgetragene_stiefel"},
                  "bags": [("frisches_brot", 5), ("schwacher_heiltrank", 2)]},
        "trainer": "jonas",
    },
    "magier": {
        "name": "Magier", "role": "Fernkampf / Flächenschaden", "difficulty": "Mittel",
        "desc": "Feuer-, Eis- und Arkane Magie. Verursacht viel Schaden auf Distanz, ist aber relativ verwundbar. "
                "Kann Gegner verlangsamen und Gruppen mit Flächenzaubern treffen.",
        "resource": "mana", "color": "#69CCF0", "icon": "wizard-staff",
        "armor": ["stoff"], "weapons": ["stab", "dolch", "zauberstab"], "offhand": ["buch", "kugel"], "dual_wield": False,
        "class_slot": "fokuskristall", "class_slot_name": "Fokuskristall",
        "base": {"str": (3, 0.2), "agi": (5, 0.4), "sta": (6, 1.0), "int": (14, 2.4), "spi": (10, 1.6)},
        "hp": (20, 12), "ap": {"str": 1.0}, "sp_int": 0.45,
        "specs": ["feuer", "frost", "arkan"],
        "start": {"equip": {"main_hand": "lehrlingsstab", "chest": "lehrlingsrobe", "feet": "lehrlingsschuhe"},
                  "bags": [("klares_quellwasser", 5), ("frisches_brot", 2), ("schwacher_manatrank", 2)]},
        "trainer": "isolde",
    },
    "raeuber": {
        "name": "Räuber", "role": "Assassine / Burst-Schaden", "difficulty": "Anspruchsvoll",
        "desc": "Zwei Dolche, Ausweichen, Gift, Tarnung und kritische Treffer. Stark gegen einzelne Gegner und für "
                "Spieler, die Timing und Positionierung mögen.",
        "resource": "energy", "color": "#FFF569", "icon": "hooded-assassin",
        "armor": ["leder", "stoff"], "weapons": ["dolch", "schwert"], "offhand": ["dolch", "schwert"], "dual_wield": True,
        "class_slot": "giftphiole", "class_slot_name": "Giftphiole",
        "base": {"str": (7, 1.0), "agi": (13, 2.3), "sta": (8, 1.4), "int": (4, 0.3), "spi": (5, 0.5)},
        "hp": (24, 15), "ap": {"str": 1.0, "agi": 1.0},
        "specs": ["meuchelmord", "kampf", "schatten"],
        "start": {"equip": {"main_hand": "schartiger_dolch", "off_hand": "rostiges_messer", "chest": "abgewetztes_lederwams",
                            "legs": "rekrutenhose", "feet": "abgetragene_stiefel"},
                  "bags": [("frisches_brot", 5), ("schwacher_heiltrank", 2)]},
        "trainer": "schattenfinger",
    },
    "samurai": {
        "name": "Samurai", "role": "Präzision / Konter", "difficulty": "Anspruchsvoll",
        "desc": "Katana und leichte bis mittlere Rüstung. Baut Fokus auf, pariert Angriffe und führt schnelle "
                "Komboattacken aus. Besonders gut im Duell mit Bossen.",
        "resource": "focus", "color": "#E05050", "icon": "katana",
        "armor": ["kette", "leder", "stoff"], "weapons": ["katana", "schwert"], "offhand": [], "dual_wield": False,
        "class_slot": "tsuba", "class_slot_name": "Tsuba",
        "base": {"str": (10, 1.7), "agi": (11, 1.7), "sta": (9, 1.6), "int": (5, 0.4), "spi": (6, 0.6)},
        "hp": (26, 16), "parry": 8.0, "ap": {"str": 1.2, "agi": 0.9},
        "specs": ["klingenmeister", "konter", "sturm"],
        "start": {"equip": {"main_hand": "uebungskatana", "chest": "gepolsterte_rekrutenweste", "legs": "rekrutenhose",
                            "feet": "abgetragene_stiefel"},
                  "bags": [("frisches_brot", 5), ("schwacher_heiltrank", 2)]},
        "trainer": "kenjiro",
    },
    "bogenschuetze": {
        "name": "Bogenschütze", "role": "Präzisions-Fernkampf", "difficulty": "Mittel",
        "desc": "Bogen, Fallen und Spezialpfeile. Kann Schwachstellen ausnutzen, Gegner markieren und sich während "
                "des Kampfes neu positionieren.",
        "resource": "concentration", "color": "#ABD473", "icon": "high-shot",
        "armor": ["kette", "leder", "stoff"], "weapons": ["bogen", "dolch"], "offhand": [], "dual_wield": False,
        "class_slot": "koecher", "class_slot_name": "Köcher",
        "base": {"str": (6, 0.8), "agi": (13, 2.2), "sta": (8, 1.5), "int": (6, 0.6), "spi": (6, 0.6)},
        "hp": (24, 15), "ap": {"agi": 2.0}, "ranged": True,
        "specs": ["scharfschuetze", "fallensteller", "waldlaeufer"],
        "start": {"equip": {"main_hand": "einfacher_kurzbogen", "chest": "abgewetztes_lederwams", "legs": "rekrutenhose",
                            "feet": "abgetragene_stiefel"},
                  "bags": [("frisches_brot", 5), ("schwacher_heiltrank", 2)]},
        "trainer": "wilma",
    },
    "barbar": {
        "name": "Barbar", "role": "Berserker / hoher Nahkampfschaden", "difficulty": "Mittel",
        "desc": "Zweihändige Äxte, Wutmechanik und mächtige Schläge. Wird im Kampf gefährlicher, kann aber bei "
                "falschem Timing schnell sterben.",
        "resource": "rage", "color": "#A0522D", "icon": "barbarian",
        "armor": ["kette", "leder", "stoff"], "weapons": ["zweihandaxt", "zweihandschwert", "axt", "kriegshammer"],
        "offhand": [], "dual_wield": False,
        "class_slot": "trophaee", "class_slot_name": "Kriegstrophäe",
        "base": {"str": (13, 2.4), "agi": (8, 1.1), "sta": (10, 1.8), "int": (3, 0.2), "spi": (4, 0.4)},
        "hp": (28, 17), "parry": 4.0, "ap": {"str": 2.0},
        "specs": ["berserker", "schlaechter", "kriegsherr"],
        "start": {"equip": {"main_hand": "schwere_holzfaelleraxt", "chest": "abgewetztes_lederwams", "legs": "rekrutenhose",
                            "feet": "abgetragene_stiefel"},
                  "bags": [("frisches_brot", 5), ("schwacher_heiltrank", 2)]},
        "trainer": "thorgrim",
    },
    "druide": {
        "name": "Druide", "role": "Heilung / Naturmagie", "difficulty": "Mittel",
        "desc": "Heilzauber, Dornen, Naturgeister und Verwandlungen. Kann Verbündete unterstützen und sich je nach "
                "Situation offensiv oder defensiv spezialisieren.",
        "resource": "mana", "color": "#FF7D0A", "icon": "oak-leaf",
        "armor": ["leder", "stoff"], "weapons": ["stab", "streitkolben", "dolch"], "offhand": ["buch"], "dual_wield": False,
        "class_slot": "goetze", "class_slot_name": "Naturgötze",
        "base": {"str": (6, 0.7), "agi": (7, 0.9), "sta": (7, 1.2), "int": (12, 2.0), "spi": (12, 1.9)},
        "hp": (22, 13), "ap": {"str": 1.0}, "sp_int": 0.4,
        "specs": ["wiederherstellung", "gleichgewicht", "wildheit"],
        "start": {"equip": {"main_hand": "knorriger_eichenstab", "chest": "lehrlingsrobe", "feet": "lehrlingsschuhe"},
                  "bags": [("klares_quellwasser", 5), ("frisches_brot", 2), ("schwacher_manatrank", 2)]},
        "trainer": "eibenhain",
    },
    "totenbeschwoerer": {
        "name": "Totenbeschwörer", "role": "Beschwörung / Kontrolle", "difficulty": "Anspruchsvoll",
        "desc": "Beschwört Skelette, nutzt Flüche und dunkle Magie. Seine Stärke liegt in kontrollierten Kämpfen und "
                "darin, Gegner durch Begleiter unter Druck zu setzen.",
        "resource": "mana", "color": "#9482C9", "icon": "skull-staff",
        "armor": ["stoff"], "weapons": ["stab", "dolch", "zauberstab"], "offhand": ["schaedel", "buch"], "dual_wield": False,
        "class_slot": "phylakterium", "class_slot_name": "Phylakterium",
        "base": {"str": (4, 0.3), "agi": (5, 0.5), "sta": (7, 1.2), "int": (14, 2.3), "spi": (9, 1.5)},
        "hp": (21, 12), "ap": {"str": 1.0}, "sp_int": 0.45,
        "specs": ["knochen", "fluch", "blut"],
        "start": {"equip": {"main_hand": "lehrlingsstab", "chest": "lehrlingsrobe", "feet": "lehrlingsschuhe"},
                  "bags": [("klares_quellwasser", 5), ("frisches_brot", 2), ("schwacher_manatrank", 2)]},
        "trainer": "morwen",
    },
}

# Für spätere Updates (GDD): werden in der Charaktererstellung als "geplant" gezeigt
PLANNED_CLASSES = [
    {"id": "paladin", "name": "Paladin", "role": "Heiler und Tank mit Lichtmagie", "color": "#F58CBA"},
    {"id": "moench", "name": "Mönch", "role": "Schnelle Faustkampfkombos und Ausweichmanöver", "color": "#00FF96"},
    {"id": "hexenjaeger", "name": "Hexenjäger", "role": "Spezialisiert auf Dämonen, Flüche und Konter", "color": "#8A6A4A"},
    {"id": "ingenieur", "name": "Ingenieur", "role": "Türme, Fallen, Bomben und mechanische Begleiter", "color": "#C0A060"},
    {"id": "beschuetzer", "name": "Beschützer", "role": "Schwer gepanzerter Unterstützer mit Bannmagie", "color": "#A0B0C8"},
    {"id": "drachenritter", "name": "Drachenritter", "role": "Feuerfähigkeiten, Speer und Drachenaspekte", "color": "#E06A2A"},
]

SPEC_NAMES = {
    "waechter": ("Wächter", "Tank und Gruppenverteidigung"),
    "schwertmeister": ("Schwertmeister", "Ausgewogener Nahkampf"),
    "vernichter": ("Vernichter", "Hoher Schaden mit Zweihänder"),
    "feuer": ("Feuer", "Großer Einzel- und Flächenschaden"),
    "frost": ("Frost", "Kontrolle und Verlangsamung"),
    "arkan": ("Arkan", "Hoher Burst, hoher Manaverbrauch"),
    "meuchelmord": ("Meuchelmord", "Gifte und tödliche Hinterhalte"),
    "kampf": ("Kampf", "Ausdauernder Nahkampf"),
    "schatten": ("Schatten", "Tarnung und Überraschung"),
    "klingenmeister": ("Klingenmeister", "Komboattacken"),
    "konter": ("Konter", "Paraden und Gegenschläge"),
    "sturm": ("Sturm", "Mobilität und Flächenangriffe"),
    "scharfschuetze": ("Scharfschütze", "Schwachstellen und Präzision"),
    "fallensteller": ("Fallensteller", "Fallen und Kontrolle"),
    "waldlaeufer": ("Waldläufer", "Mobilität und Gifte"),
    "berserker": ("Berserker", "Raserei und Tempo"),
    "schlaechter": ("Schlächter", "Riesige Einzelschläge"),
    "kriegsherr": ("Kriegsherr", "Schreie, Gruppe und Ausdauer"),
    "wiederherstellung": ("Wiederherstellung", "Heilung der Gruppe"),
    "gleichgewicht": ("Gleichgewicht", "Naturmagie auf Distanz"),
    "wildheit": ("Wildheit", "Bärengestalt und Nahkampf"),
    "knochen": ("Knochen", "Mächtige Diener"),
    "fluch": ("Fluch", "Flüche und Schaden über Zeit"),
    "blut": ("Blut", "Lebensentzug und Ausdauer"),
}


def base_stats(class_id: str, level: int) -> dict:
    """Grundattribute je Klasse und Stufe (ohne Ausrüstung).

    str Stärke, agi Beweglichkeit, sta Ausdauer, int Intelligenz, spi Willenskraft
    """
    b = CLASSES[class_id]["base"]
    return {k: int(v[0] + v[1] * level) for k, v in b.items()}


def base_hp(class_id: str, level: int) -> int:
    a, b = CLASSES[class_id]["hp"]
    return int(a + b * level)


def xp_to_next(level: int) -> int:
    """Erfahrung bis zur nächsten Stufe."""
    if level >= MAX_LEVEL:
        return 0
    return int(320 + 95 * level + 21 * level * level)


def talent_points(level: int) -> int:
    """Ein Fähigkeitspunkt pro Stufe ab Stufe 10 (bis zu 41 Punkte auf Stufe 50)."""
    return max(0, level - 9)


def respec_cost(times: int) -> int:
    """Kosten für das Zurücksetzen der Talente in Kupfer (steigend, max. 50 Gold)."""
    return min(500000, [10000, 50000, 100000, 200000, 350000][min(times, 4)])
