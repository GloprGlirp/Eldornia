"""Gegenstandsvorlagen.

Seltenheit (q): 0 schlecht (grau), 1 gewöhnlich (weiß), 2 ungewöhnlich (grün),
3 selten (blau), 4 episch (lila), 5 legendär (gold), 6 mythisch (türkis).
Preise in Kupfer (100 Kupfer = 1 Silber, 100 Silber = 1 Gold).
"""

RARITY_NAMES = ["Schlecht", "Gewöhnlich", "Ungewöhnlich", "Selten", "Episch", "Legendär", "Mythisch"]

EQUIP_SLOTS = ["head", "neck", "shoulders", "back", "chest", "hands", "legs", "feet",
               "ring1", "ring2", "main_hand", "off_hand"]

SLOT_NAMES = {
    "head": "Kopf", "neck": "Hals", "shoulders": "Schultern", "back": "Rücken", "chest": "Brust",
    "hands": "Hände", "legs": "Beine", "feet": "Füße", "ring": "Finger", "ring1": "Finger",
    "ring2": "Finger", "main_hand": "Waffenhand", "off_hand": "Schildhand",
}

SUB_NAMES = {
    "schwert": "Schwert", "axt": "Axt", "streitkolben": "Streitkolben", "dolch": "Dolch", "stab": "Stab",
    "schild": "Schild", "buch": "In der Schildhand geführt", "platte": "Platte", "kette": "Kette",
    "leder": "Leder", "stoff": "Stoff", "schmuck": "", "umhang": "Umhang",
}


def _w(name, q, sub, lvl, dmg, speed, sell, stats=None, icon=None, desc="", bind=None, buy=None):
    return {"name": name, "q": q, "type": "weapon", "slot": "main_hand", "sub": sub, "lvl": lvl,
            "dmg": dmg, "speed": speed, "stats": stats or {}, "sell": sell, "buy": buy,
            "icon": icon or {"schwert": "sword", "axt": "axe", "streitkolben": "mace", "dolch": "dagger",
                             "stab": "staff"}[sub], "desc": desc, "bind": bind, "stack": 1}


def _a(name, q, slot, sub, lvl, stats, sell, icon, desc="", bind=None, buy=None):
    return {"name": name, "q": q, "type": "armor", "slot": slot, "sub": sub, "lvl": lvl,
            "stats": stats, "sell": sell, "buy": buy, "icon": icon, "desc": desc, "bind": bind, "stack": 1}


def _junk(name, sell, icon, desc="", stack=10):
    return {"name": name, "q": 0, "type": "junk", "sell": sell, "icon": icon, "desc": desc, "stack": stack}


def _quest(name, icon, desc="", stack=10):
    return {"name": name, "q": 1, "type": "quest", "sell": 0, "icon": icon, "desc": desc, "stack": stack,
            "quest": True}


ITEMS = {
    # ------------------------------------------------------------ Startausrüstung
    "rostiges_langschwert": _w("Rostiges Langschwert", 1, "schwert", 1, [3, 6], 2.6, 9),
    "holzschild": _a("Abgenutzter Holzschild", 1, "off_hand", "schild", 1, {"armor": 18}, 6, "shield"),
    "rekrutenweste": _a("Gepolsterte Rekrutenweste", 1, "chest", "kette", 1, {"armor": 14}, 5, "chest"),
    "rekrutenhose": _a("Rekrutenhose", 1, "legs", "leder", 1, {"armor": 7}, 4, "pants"),
    "abgetragene_stiefel": _a("Abgetragene Stiefel", 1, "feet", "leder", 1, {"armor": 4}, 3, "boots"),
    "lehrlingsstab": _w("Lehrlingsstab", 1, "stab", 1, [2, 5], 3.0, 8, {"int": 2}),
    "lehrlingsrobe": _a("Lehrlingsrobe", 1, "chest", "stoff", 1, {"armor": 4, "int": 1}, 4, "robe"),
    "lehrlingsschuhe": _a("Lehrlingsschuhe", 1, "feet", "stoff", 1, {"armor": 2}, 2, "boots"),

    # ------------------------------------------------------------ Verbrauchsgüter
    "brot": {"name": "Frisch gebackenes Brot", "q": 1, "type": "consumable", "sell": 1, "buy": 5, "stack": 20,
             "icon": "bread", "use": {"type": "food", "amount": 61, "dur": 18},
             "desc": "Benutzen: Stellt im Sitzen über 18 Sek. 61 Gesundheit wieder her."},
    "quellwasser": {"name": "Klares Quellwasser", "q": 1, "type": "consumable", "sell": 1, "buy": 5, "stack": 20,
                    "icon": "water", "use": {"type": "drink", "amount": 151, "dur": 18},
                    "desc": "Benutzen: Stellt im Sitzen über 18 Sek. 151 Mana wieder her."},
    "wildschweinbraten": {"name": "Saftiger Wildschweinbraten", "q": 1, "type": "consumable", "sell": 6,
                          "buy": 25, "stack": 20, "icon": "meat",
                          "use": {"type": "food", "amount": 243, "dur": 21},
                          "desc": "Benutzen: Stellt im Sitzen über 21 Sek. 243 Gesundheit wieder her."},
    "melonensaft": {"name": "Gekühlter Melonensaft", "q": 1, "type": "consumable", "sell": 6, "buy": 25,
                    "stack": 20, "icon": "water", "use": {"type": "drink", "amount": 436, "dur": 21},
                    "desc": "Benutzen: Stellt im Sitzen über 21 Sek. 436 Mana wieder her."},
    "heiltrank": {"name": "Schwacher Heiltrank", "q": 1, "type": "consumable", "sell": 5, "buy": 40, "stack": 5,
                  "icon": "potion_red", "use": {"type": "heal", "amount": 90, "cd": 60},
                  "desc": "Benutzen: Stellt sofort 70 bis 110 Gesundheit wieder her."},
    "manatrank": {"name": "Schwacher Manatrank", "q": 1, "type": "consumable", "sell": 5, "buy": 40, "stack": 5,
                  "icon": "potion_blue", "use": {"type": "mana", "amount": 160, "cd": 60},
                  "desc": "Benutzen: Stellt sofort 140 bis 180 Mana wieder her."},

    # ------------------------------------------------------------ Plunder (grau)
    "wolfsfell": _junk("Räudiges Wolfsfell", 14, "pelt"),
    "reisszahn": _junk("Zerbrochener Reißzahn", 9, "fang"),
    "zaehes_fleisch": _junk("Zähes Schweinefleisch", 11, "meat"),
    "rotdolch_abzeichen": _junk("Rotdolch-Abzeichen", 31, "badge"),
    "kobold_loeffel": _junk("Verbogener Kobold-Löffel", 26, "spoon"),
    "knochensplitter": _junk("Knochensplitter", 38, "bone"),
    "vergilbter_schaedel": _junk("Vergilbter Schädel", 55, "skull"),
    "kaninchenpfote": _junk("Glückliche Kaninchenpfote", 4, "fang", "Für das Kaninchen war sie offenbar nicht so glücklich."),

    # ------------------------------------------------------------ Questgegenstände
    "wiesenkraut": _quest("Wiesenkraut", "herb", "Duftet nach Sommer. Kathi braucht es für die Burgküche."),
    "wildschweinkeule": _quest("Wildschweinkeule", "meat"),
    "schweineblase": _quest("Aufgeblasene Schweineblase", "bladder", "Hüpft erstaunlich gut."),
    "leonines_medaillon": _quest("Leonines Medaillon", "medallion", "Ein silbernes Medaillon mit einer eingravierten Rose.", 1),
    "kobold_kerze": _quest("Kobold-Kerze", "candle", "\"Du nicht nehmen die Kerze!\""),
    "kupfererz": {"name": "Kupfererz", "q": 1, "type": "material", "sell": 5, "stack": 20, "icon": "ore",
                  "desc": "Wird für die Schmiedekunst benötigt."},
    "liebesbrief": _quest("Versiegelter Liebesbrief", "letter", "Riecht stark nach Rosenwasser. Nicht öffnen!", 1),
    "gackerle": _quest("Gackerle", "chicken", "Das Lieblingshuhn des Dorftrottels. Es gackert empört.", 1),
    "morgraths_siegel": _quest("Morgraths Siegel", "seal", "Das Siegel des gefallenen Ritters Morgrath.", 1),

    # ------------------------------------------------------------ Ungewöhnlich (grün)
    "wolfsfellumhang": _a("Wolfsfellumhang", 2, "back", "umhang", 3, {"armor": 9, "sta": 1, "agi": 1}, 45, "cloak"),
    "jaegerhandschuhe": _a("Jägerhandschuhe der Grünmark", 2, "hands", "leder", 4, {"armor": 10, "agi": 2, "sta": 1}, 52, "gloves"),
    "bauernstiefel": _a("Stiefel des Bauern", 2, "feet", "leder", 3, {"armor": 11, "sta": 2}, 48, "boots"),
    "rotdolch_kopftuch": _a("Rotdolch-Kopftuch", 2, "head", "leder", 5, {"armor": 13, "agi": 2, "sta": 2}, 70, "helm"),
    "banditenweste": _a("Gesteppte Banditenweste", 2, "chest", "leder", 5, {"armor": 20, "str": 2, "sta": 2}, 82, "chest"),
    "schimmernde_robe": _a("Schimmernde Robe", 2, "chest", "stoff", 5, {"armor": 8, "int": 3, "spi": 2}, 80, "robe"),
    "kerzenwachshose": _a("Kerzenwachsverschmierte Hose", 2, "legs", "stoff", 6, {"armor": 7, "int": 2, "sta": 2}, 76, "pants"),
    "stollenhandschuhe": _a("Stollenhandschuhe", 2, "hands", "kette", 6, {"armor": 22, "str": 2, "sta": 1}, 74, "gloves"),
    "rekrutenhandschuhe": _a("Rekrutenhandschuhe aus Platte", 2, "hands", "platte", 2, {"armor": 18, "str": 1, "sta": 1}, 30, "gloves"),
    "gewebte_handschuhe": _a("Gewebte Handschuhe", 2, "hands", "stoff", 2, {"armor": 3, "int": 1, "spi": 1}, 28, "gloves"),
    "kraeuterumhang": _a("Duftender Kräuterumhang", 2, "back", "umhang", 3, {"armor": 8, "spi": 2, "sta": 1}, 40, "cloak"),
    "gauklerhandschuhe": _a("Gauklerhandschuhe", 2, "hands", "stoff", 4, {"armor": 5, "agi": 2, "int": 2}, 50, "gloves",
                             "Fingerlos. Zum Jonglieren und Taschendiebstahl gleichermaßen geeignet."),
    "glueckfeder": _a("Glücksfeder des Dorftrottels", 2, "neck", "schmuck", 2,
                      {"str": 1, "agi": 1, "sta": 1, "int": 1, "spi": 1}, 35, "feather",
                      "\"Die hat mir ein Vogel geschenkt. Glaub ich.\""),
    "monokel": _a("Monokel des Einäugigen", 2, "head", "stoff", 6, {"armor": 6, "int": 3, "spi": 2, "sta": 1}, 88, "monocle",
                  "Für ein Auge mehr als genug."),
    "wachmannsschultern": _a("Wachmannsschulterstücke", 2, "shoulders", "platte", 6, {"armor": 34, "str": 2, "sta": 2}, 95, "shoulder"),
    "lehrlingsschultertuch": _a("Schultertuch des Gelehrten", 2, "shoulders", "stoff", 6, {"armor": 7, "int": 2, "spi": 2}, 90, "shoulder"),
    "ring_standhaftigkeit": _a("Ring der Standhaftigkeit", 2, "ring", "schmuck", 5, {"str": 2, "sta": 2}, 120, "ring"),
    "ring_klarheit": _a("Ring der Klarheit", 2, "ring", "schmuck", 5, {"int": 2, "spi": 2}, 120, "ring"),
    "gundolfs_breitschwert": _w("Gundolfs Breitschwert", 2, "schwert", 6, [9, 17], 2.7, 140, {"str": 3}),
    "gluehender_kupferstab": _w("Glühender Kupferstab", 2, "stab", 6, [6, 11], 3.2, 140, {"int": 3, "sp": 4}),
    "wolfszahnaxt": _w("Wolfszahnaxt", 2, "axt", 3, [5, 10], 2.5, 60, {"str": 1, "sta": 1}),
    "eichenstab": _w("Knorriger Eichenstab", 2, "stab", 3, [4, 8], 3.0, 58, {"int": 1, "spi": 1}),
    "stollenhammer": _w("Stollenhammer", 2, "streitkolben", 6, [8, 15], 2.6, 110, {"str": 2, "sta": 1}),
    "zauberfoliant": _a("Abgegriffener Zauberfoliant", 2, "off_hand", "buch", 5, {"int": 2, "sp": 3}, 80, "book"),
    "beschlagener_schild": _a("Eisenbeschlagener Schild", 2, "off_hand", "schild", 5, {"armor": 95, "sta": 2}, 85, "shield"),

    # ------------------------------------------------------------ Selten (blau)
    "grimbarts_dolch": _w("Grimbarts roter Dolch", 3, "dolch", 7, [7, 13], 1.8, 260, {"agi": 3, "sta": 2, "int": 2},
                          desc="An der Klinge klebt noch Lagerfeuerruß.", bind="bop"),
    "rotdolch_brecher": _w("Rotdolch-Brecher", 3, "streitkolben", 7, [13, 24], 2.8, 300, {"str": 4, "sta": 3}, bind="bop"),
    "robe_der_wachsamkeit": _a("Robe der Wachsamkeit", 3, "chest", "stoff", 7, {"armor": 12, "int": 5, "spi": 4, "sta": 3},
                               290, "robe", bind="bop"),
    "grabwaechter_schultern": _a("Schulterplatten des Grabwächters", 3, "shoulders", "platte", 9,
                                 {"armor": 62, "str": 4, "sta": 4}, 360, "shoulder", bind="bop"),
    "leichentuchrobe": _a("Leichentuchrobe", 3, "chest", "stoff", 9, {"armor": 14, "int": 6, "sta": 4, "sp": 5}, 360, "robe", bind="bop"),
    "umhang_grabesruhe": _a("Umhang der Grabesruhe", 3, "back", "umhang", 9, {"armor": 16, "sta": 3, "spi": 3}, 330, "cloak", bind="bop"),
    "ring_der_vergessenen": _a("Ring der Vergessenen", 3, "ring", "schmuck", 9, {"sta": 3, "int": 3, "str": 3}, 400, "ring", bind="bop"),
    "wiedergaenger_stiefel": _a("Stiefel des Wiedergängers", 3, "feet", "platte", 9, {"armor": 55, "str": 3, "sta": 4}, 340, "boots", bind="bop"),
    "knochenmagier_kappe": _a("Kappe des Knochenmagiers", 3, "head", "stoff", 9, {"armor": 11, "int": 5, "spi": 3, "sp": 4}, 350, "helm", bind="bop"),
    "klinge_des_herrschers": _w("Klinge des Herrschers", 3, "schwert", 9, [15, 28], 2.6, 450, {"str": 5, "sta": 4},
                                desc="Ein Geschenk Simons, des zweiäugigen Herrschers.", bind="bop"),
    "gesegnete_handschuhe": _a("Gesegnete Panzerhandschuhe", 3, "hands", "platte", 8, {"armor": 48, "str": 3, "sta": 4},
                               320, "gloves", "Bruder Anselm hat sie dreimal gesegnet. Sicher ist sicher.", bind="bop"),
    "handschuhe_der_andacht": _a("Handschuhe der Andacht", 3, "hands", "stoff", 8, {"armor": 9, "int": 4, "spi": 3, "sp": 4},
                                 320, "gloves", bind="bop"),
    "simons_zepter": _w("Simons Ersatzzepter", 3, "stab", 9, [11, 20], 3.0, 450, {"int": 6, "spi": 4, "sp": 8},
                        desc="\"Ich habe noch zwei davon. Für jedes Auge eins.\"", bind="bop"),

    # ------------------------------------------------------------ Episch (lila) – Sir Morgrath
    "morgraths_seelenklinge": _w("Morgraths Seelenklinge", 4, "schwert", 10, [22, 38], 2.8, 1200,
                                 {"str": 8, "sta": 7}, desc="Die Klinge flüstert Namen längst Vergessener.", bind="bop"),
    "schild_des_gefallenen": _a("Schild des gefallenen Ritters", 4, "off_hand", "schild", 10,
                                {"armor": 260, "sta": 8, "str": 3}, 1100, "shield", bind="bop"),
    "stab_verlorener_seelen": _w("Stab der verlorenen Seelen", 4, "stab", 10, [16, 29], 3.0, 1200,
                                 {"int": 10, "spi": 6, "sp": 18}, bind="bop"),
    "kapuze_der_grabesstille": _a("Kapuze der Grabesstille", 4, "head", "stoff", 10,
                                  {"armor": 16, "int": 8, "sta": 6, "sp": 10}, 1000, "helm", bind="bop"),
    "morgraths_helm": _a("Morgraths gehörnter Helm", 4, "head", "platte", 10, {"armor": 110, "str": 7, "sta": 8}, 1000, "helm",
                         bind="bop"),

    # ------------------------------------------------------------ Legendär (gold)
    "eldornias_traene": _a("Eldornias Träne", 5, "ring", "schmuck", 10,
                           {"str": 5, "agi": 5, "sta": 5, "int": 5, "spi": 5, "sp": 12}, 5000, "ring",
                           "Man sagt, Eldornia selbst habe diesen Stein geweint, als Morgrath fiel.", bind="bop"),
}

for _id, _it in ITEMS.items():
    _it["id"] = _id
    _it.setdefault("stats", {})
    _it.setdefault("stack", 1)
    _it.setdefault("desc", "")
    _it.setdefault("bind", None)
    _it.setdefault("quest", False)
    if _it.get("buy") is None:
        _it["buy"] = max(1, _it.get("sell", 1) * 4)


# Zufällige Weltdrops nach Stufenbereich (grüne Gegenstände)
WORLD_DROPS = [
    (2, 4, ["wolfsfellumhang", "bauernstiefel", "wolfszahnaxt", "eichenstab", "jaegerhandschuhe"]),
    (4, 7, ["rotdolch_kopftuch", "banditenweste", "schimmernde_robe", "jaegerhandschuhe", "zauberfoliant",
            "beschlagener_schild", "kerzenwachshose", "stollenhandschuhe", "stollenhammer"]),
    (7, 10, ["kerzenwachshose", "stollenhandschuhe", "stollenhammer", "zauberfoliant", "beschlagener_schild",
             "banditenweste", "schimmernde_robe"]),
]


def world_drop_pool(level: int):
    pool = []
    for lo, hi, items in WORLD_DROPS:
        if lo <= level <= hi:
            pool.extend(items)
    return pool


def item_usable_by(item: dict, class_def: dict) -> bool:
    """Darf eine Klasse diesen Gegenstand anlegen?"""
    if item["type"] == "weapon":
        return item["sub"] in class_def["weapon_types"]
    if item["type"] == "armor":
        sub = item["sub"]
        if item["slot"] == "off_hand":
            return sub in class_def["offhand_types"]
        if sub in ("schmuck", "umhang"):
            return True
        return sub in class_def["armor_types"]
    return False


def item_client_info(item_id: str) -> dict:
    it = ITEMS[item_id]
    info = {k: v for k, v in it.items() if k not in ("buy",)}
    info["buy"] = it.get("buy")
    return info
