"""Gegenstände von Eldornia (GDD Abschnitt 5).

Seltenheit (q): 0 Schlecht (grau), 1 Gewöhnlich (weiß), 2 Ungewöhnlich (grün), 3 Selten (blau),
4 Episch (lila), 5 Legendär (gold), 6 Mythisch (türkis).
Preise in Kupfer (100 Kupfer = 1 Silber, 100 Silber = 1 Gold).

Ausrüstungsslots: Kopf, Brust, Schultern, Hände, Beine, Füße, Haupthand, Nebenhand, Halskette,
zwei Ringe, Rücken und ein klassenspezifischer Slot.

Der Großteil der Ausrüstung wird aus Materialstufen, Slots und Werte-Themen erzeugt; dazu kommen
handgemachte Unikate (Quest- und Bossbeute), Sets mit Set-Boni, Verbrauchsgüter und Materialien.
"""
from __future__ import annotations

import random

RARITY_NAMES = ["Schlecht", "Gewöhnlich", "Ungewöhnlich", "Selten", "Episch", "Legendär", "Mythisch"]
RARITY_COLORS = ["#9d9d9d", "#ffffff", "#1eff00", "#0070dd", "#a335ee", "#ff8000", "#2ee6d6"]

EQUIP_SLOTS = ["head", "neck", "shoulders", "back", "chest", "hands", "legs", "feet",
               "ring1", "ring2", "main_hand", "off_hand", "class"]
SLOT_NAMES = {
    "head": "Kopf", "neck": "Hals", "shoulders": "Schultern", "back": "Rücken", "chest": "Brust",
    "hands": "Hände", "legs": "Beine", "feet": "Füße", "ring": "Finger", "ring1": "Finger", "ring2": "Finger",
    "main_hand": "Waffenhand", "off_hand": "Schildhand", "two_hand": "Zweihändig", "class": "Klassenslot",
}
ARMOR_NAMES = {"stoff": "Stoff", "leder": "Leder", "kette": "Kette", "platte": "Platte"}
WEAPON_NAMES = {
    "schwert": "Schwert", "zweihandschwert": "Zweihandschwert", "axt": "Axt", "zweihandaxt": "Zweihandaxt",
    "streitkolben": "Streitkolben", "kriegshammer": "Kriegshammer", "dolch": "Dolch", "katana": "Katana",
    "bogen": "Bogen", "stab": "Stab", "zauberstab": "Zauberstab", "schild": "Schild", "buch": "Folianten",
    "kugel": "Kugel", "schaedel": "Schädel",
}
TWO_HAND = {"zweihandschwert", "zweihandaxt", "kriegshammer", "stab", "bogen", "katana"}
OFFHAND_TYPES = {"schild", "buch", "kugel", "schaedel"}
STAT_NAMES = {
    "str": "Stärke", "agi": "Beweglichkeit", "sta": "Ausdauer", "int": "Intelligenz", "spi": "Willenskraft",
    "armor": "Rüstung", "ap": "Angriffskraft", "sp": "Zaubermacht", "crit": "Kritische Trefferchance",
    "haste": "Tempo", "block": "Blockchance", "dodge": "Ausweichen", "parry": "Parieren", "mp5": "Mana alle 5 Sek.",
    "fire_res": "Feuerwiderstand", "frost_res": "Frostwiderstand", "nature_res": "Naturwiderstand",
    "shadow_res": "Schattenwiderstand", "arcane_res": "Arkanwiderstand", "heal": "Heilkraft",
}
PERCENT_STATS = {"crit", "haste", "block", "dodge", "parry"}

ITEMS: dict[str, dict] = {}


def _reg(it: dict) -> dict:
    it.setdefault("stats", {})
    it.setdefault("stack", 1)
    it.setdefault("desc", "")
    it.setdefault("bind", None)
    it.setdefault("quest", False)
    it.setdefault("lvl", 1)
    it.setdefault("ilvl", it["lvl"])
    it.setdefault("sell", 0)
    it.setdefault("set", None)
    it.setdefault("unique", False)
    it.setdefault("cls", None)
    it.setdefault("vis", {})
    if it.get("buy") is None:
        it["buy"] = max(1, it.get("sell", 1) * 4)
    ITEMS[it["id"]] = it
    return it


# =============================================================================== Werte-Budget
QMULT = [0.0, 0.25, 0.62, 0.82, 1.0, 1.25, 1.5]
SLOT_W = {"head": 1.0, "chest": 1.0, "legs": 1.0, "shoulders": 0.75, "hands": 0.72, "feet": 0.72, "back": 0.56,
          "neck": 0.56, "ring": 0.56, "class": 0.6, "off_hand": 0.6, "main_hand": 0.5, "two_hand": 1.0}
ARMOR_K = {"stoff": 0.9, "leder": 1.7, "kette": 2.7, "platte": 4.2}
ARMOR_SLOT_K = {"chest": 1.0, "legs": 0.86, "head": 0.8, "shoulders": 0.74, "feet": 0.68, "hands": 0.62, "back": 0.35}

THEMES = {
    "baer": (" des Bären", {"str": 0.5, "sta": 0.5}),
    "tiger": (" des Tigers", {"str": 0.55, "agi": 0.45}),
    "affe": (" des Affen", {"agi": 0.55, "sta": 0.45}),
    "falke": (" des Falken", {"agi": 0.6, "crit": 0.4}),
    "eule": (" der Eule", {"int": 0.55, "spi": 0.45}),
    "adler": (" des Adlers", {"int": 0.55, "sta": 0.45}),
    "zauberei": (" der Zauberei", {"int": 0.45, "sp": 0.55}),
    "weise": (" des Weisen", {"int": 0.4, "spi": 0.3, "heal": 0.3}),
    "wal": (" des Wals", {"sta": 0.55, "spi": 0.45}),
    "waechter": (" des Wächters", {"sta": 0.6, "block": 0.15, "str": 0.25}),
}
STAT_COST = {"str": 1.0, "agi": 1.0, "sta": 1.0, "int": 1.0, "spi": 1.0, "sp": 0.86, "heal": 0.86, "ap": 0.5,
             "crit": 14.0, "haste": 14.0, "block": 12.0, "dodge": 14.0, "parry": 14.0}

THEMES_FOR = {
    "platte": ["baer", "tiger", "waechter"], "kette": ["baer", "tiger", "affe", "falke", "waechter"],
    "leder": ["affe", "falke", "tiger", "eule", "wal"], "stoff": ["eule", "adler", "zauberei", "weise", "wal"],
    "schwert": ["baer", "tiger", "falke"], "axt": ["baer", "tiger"], "streitkolben": ["baer", "weise", "waechter"],
    "kriegshammer": ["baer", "tiger"], "zweihandschwert": ["baer", "tiger"], "zweihandaxt": ["tiger", "baer"],
    "dolch": ["affe", "falke", "zauberei"], "katana": ["tiger", "falke"], "bogen": ["affe", "falke"],
    "stab": ["eule", "zauberei", "weise", "affe"], "zauberstab": ["zauberei", "adler"],
    "schild": ["waechter", "baer"], "buch": ["eule", "zauberei", "weise"], "kugel": ["zauberei", "adler"],
    "schaedel": ["zauberei", "adler"],
    "neck": list(THEMES), "ring": list(THEMES), "back": list(THEMES),
}


def stat_budget(ilvl: int, q: int, slot: str) -> float:
    return max(1.0, ilvl * QMULT[q] * SLOT_W.get(slot, 0.6) * 1.15 + (1.5 if q >= 2 else 0.0))


def make_stats(ilvl: int, q: int, slot: str, theme: str) -> dict:
    budget = stat_budget(ilvl, q, slot)
    out = {}
    for stat, share in THEMES[theme][1].items():
        v = budget * share / STAT_COST[stat]
        if stat in PERCENT_STATS:
            v = round(max(0.5, v), 1)
            if v >= 0.5:
                out[stat] = v
        else:
            v = int(round(v))
            if v > 0:
                out[stat] = v
    return out


def armor_value(ilvl: int, q: int, armor_type: str, slot: str) -> int:
    return int((8 + ilvl * 2.2) * ARMOR_K[armor_type] * ARMOR_SLOT_K.get(slot, 0.6) * (1.0 + 0.06 * max(0, q - 1)))


def weapon_dps(ilvl: int, q: int, sub: str) -> float:
    dps = (2.5 + ilvl * 0.95) * (1.0 + 0.09 * max(0, q - 2))
    if sub in ("zweihandschwert", "zweihandaxt", "kriegshammer", "katana"):
        dps *= 1.32
    if sub == "stab":
        dps *= 1.05
    if sub == "zauberstab":
        dps *= 0.8
    return dps


WEAPON_SPEED = {"schwert": 2.6, "axt": 2.7, "streitkolben": 2.7, "dolch": 1.8, "zweihandschwert": 3.4,
                "zweihandaxt": 3.5, "kriegshammer": 3.6, "katana": 2.9, "bogen": 2.8, "stab": 3.0, "zauberstab": 1.9}


def sell_price(ilvl: int, q: int, slot: str) -> int:
    return int((5 + ilvl * ilvl * 0.9) * (0.5 + QMULT[q] * 1.6) * SLOT_W.get(slot, 0.6))


# =============================================================================== Optik (für den Client)
METAL_TIERS = ["#8a8e96", "#9a8a70", "#b8bcc6", "#c0c4cc", "#a8a090", "#b8d0e8", "#d0dcf0", "#c8c8f0",
               "#6a5048", "#3e3846", "#8a3a2a", "#e8e0ff", "#f4f6ff"]
LEATHER_TIERS = ["#7a5232", "#6a4a2a", "#5a3a22", "#4a3a2a", "#6a6a5a", "#5a3e2a", "#7a8a98", "#4a5a6a",
                 "#3a2a3a", "#6a2a1a", "#3a2a26", "#5a4a6a", "#d8d0c0"]
THEME_COLORS = {"baer": "#7a2a20", "tiger": "#c06a20", "affe": "#5a6a2a", "falke": "#3a5a7a", "eule": "#4a3a8a",
                "adler": "#2a4a8a", "zauberei": "#6a2a8a", "weise": "#e0d8c0", "wal": "#2a6a7a", "waechter": "#2d4f9a"}
GLOW = {"baer": "#ff6a3a", "tiger": "#ffa040", "affe": "#a0ff60", "falke": "#80c0ff", "eule": "#b080ff",
        "adler": "#60a0ff", "zauberei": "#e070ff", "weise": "#fff0a0", "wal": "#60e0e0", "waechter": "#80b0ff"}


def make_vis(sub: str, tier: int, q: int, theme: str) -> dict:
    tier = max(0, min(12, tier))
    v = {"c": THEME_COLORS.get(theme, "#6a5a7a"), "m": METAL_TIERS[tier], "a": "#c9a040" if q >= 3 else "#8a6a3a"}
    if sub == "leder":
        v["c"] = LEATHER_TIERS[tier] if q < 3 else THEME_COLORS.get(theme, LEATHER_TIERS[tier])
    if q >= 4:
        v["g"] = GLOW.get(theme, "#a0c0ff")
    if q >= 5:
        v["gold"] = True
    if sub in ("bogen", "stab"):
        v["w"] = ["#7a5232", "#8a6038", "#5a3a22", "#9a7040", "#4a3020", "#a0b0c0", "#c0b8e0", "#3a2a3a"][tier % 8]
    return v


# =============================================================================== Generierte Ausrüstung
BRACKETS = [2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50]   # Stufen der Materialstufen
MATERIALS = {
    "stoff": ["Leinen", "Grobleinen", "Wollstoff", "Filz", "Seiden", "Brokat", "Magiestoff", "Mondseiden",
              "Runenstoff", "Glutseiden", "Aschenstoff", "Sternengarn", "Himmelsseiden"],
    "leder": ["Grobleder", "Wildleder", "Hartleder", "Gerbleder", "Wolfsleder", "Bärenleder", "Frostleder",
              "Mondleder", "Dämmerleder", "Drachenleder", "Aschenleder", "Wyrmleder", "Himmelsleder"],
    "kette": ["Eisenring", "Kettenring", "Stahlring", "Schuppen", "Zwergenring", "Frostring", "Mithrilring",
              "Silberschuppen", "Glutring", "Obsidianring", "Drachenschuppen", "Sternenring", "Himmelsschuppen"],
    "platte": ["Eisen", "Grobstahl", "Stahl", "Schmiedestahl", "Zwergenstahl", "Frostplatten", "Mithril", "Mondstahl",
               "Glutstahl", "Obsidian", "Drachenstahl", "Sternenstahl", "Himmelsstahl"],
}
NOUNS = {
    "stoff": {"head": "kapuze", "shoulders": "schultertuch", "chest": "robe", "hands": "handschuhe", "legs": "hose", "feet": "schuhe"},
    "leder": {"head": "kappe", "shoulders": "schulterstücke", "chest": "wams", "hands": "handschuhe", "legs": "hose", "feet": "stiefel"},
    "kette": {"head": "haube", "shoulders": "schulterstücke", "chest": "hemd", "hands": "handschuhe", "legs": "beinlinge", "feet": "stiefel"},
    "platte": {"head": "helm", "shoulders": "schulterplatten", "chest": "brustplatte", "hands": "panzerhandschuhe", "legs": "beinplatten", "feet": "stiefel"},
}
ICONS = {
    ("stoff", "head"): "hood", ("stoff", "shoulders"): "shoulder-armor", ("stoff", "chest"): "robe", ("stoff", "hands"): "gloves",
    ("stoff", "legs"): "trousers", ("stoff", "feet"): "boots",
    ("leder", "head"): "light-helm", ("leder", "shoulders"): "shoulder-armor", ("leder", "chest"): "leather-armor",
    ("leder", "hands"): "gloves", ("leder", "legs"): "trousers", ("leder", "feet"): "leather-boot",
    ("kette", "head"): "visored-helm", ("kette", "shoulders"): "shoulder-scales", ("kette", "chest"): "chain-mail",
    ("kette", "hands"): "gauntlet", ("kette", "legs"): "armored-pants", ("kette", "feet"): "boots",
    ("platte", "head"): "closed-barbute", ("platte", "shoulders"): "pauldrons", ("platte", "chest"): "breastplate",
    ("platte", "hands"): "mailed-fist", ("platte", "legs"): "leg-armor", ("platte", "feet"): "metal-boot",
}
WMAT = ["Kupfer", "Bronze", "Eisen", "Stahl", "Zwergen", "Frost", "Mithril", "Mond", "Glut", "Obsidian", "Drachen", "Sternen", "Himmels"]
WOOD = ["Eschen", "Weiden", "Eiben", "Eichen", "Bergeschen", "Frostholz", "Mondholz", "Elfenholz", "Glutholz",
        "Aschenholz", "Drachenholz", "Sternenholz", "Himmelsholz"]
GEMS = ["Quarz", "Bernstein", "Jade", "Karneol", "Saphir", "Frostkristall", "Mondstein", "Amethyst", "Rubin",
        "Obsidian", "Drachenauge", "Sternensaphir", "Himmelsdiamant"]
WNOUN = {"schwert": "schwert", "axt": "axt", "streitkolben": "streitkolben", "kriegshammer": "kriegshammer",
         "zweihandschwert": "zweihänder", "zweihandaxt": "streitaxt", "dolch": "dolch", "katana": "katana",
         "bogen": "bogen", "stab": "stab", "zauberstab": "zauberstab", "schild": "schild"}
WICON = {"schwert": "broadsword", "axt": "battle-axe", "streitkolben": "flanged-mace", "kriegshammer": "warhammer",
         "zweihandschwert": "two-handed-sword", "zweihandaxt": "war-axe", "dolch": "plain-dagger", "katana": "katana",
         "bogen": "pocket-bow", "stab": "wizard-staff", "zauberstab": "crystal-wand", "schild": "checked-shield",
         "buch": "spell-book", "kugel": "crystal-ball", "schaedel": "skull-crossed-bones"}
CLASS_SLOT = {
    "ritter": ("wappen", "Wappen", "griffin-shield", {"sta": 0.5, "block": 0.25, "str": 0.25}),
    "magier": ("fokuskristall", "Fokuskristall", "crystal-growth", {"int": 0.5, "sp": 0.5}),
    "raeuber": ("giftphiole", "Giftphiole", "poison-bottle", {"agi": 0.6, "crit": 0.4}),
    "samurai": ("tsuba", "Tsuba", "ninja-star", {"agi": 0.4, "str": 0.3, "parry": 0.3}),
    "bogenschuetze": ("koecher", "Köcher", "quiver", {"agi": 0.6, "haste": 0.4}),
    "barbar": ("trophaee", "Kriegstrophäe", "fangs", {"str": 0.6, "crit": 0.4}),
    "druide": ("goetze", "Naturgötze", "totem-head", {"int": 0.4, "spi": 0.3, "heal": 0.3}),
    "totenbeschwoerer": ("phylakterium", "Phylakterium", "crystal-eye", {"int": 0.5, "sp": 0.5}),
}
REGION_GEN = ["der Grünmark", "der Grünmark", "der Grünmark", "aus Frostklamm", "aus Frostklamm", "aus Frostklamm",
              "des Mondhains", "des Mondhains", "des Mondhains", "der Aschenlande", "der Aschenlande", "der Aschenlande",
              "des Himmelsbruchs"]


def _gen_id(*parts) -> str:
    return "g_" + "_".join(str(p) for p in parts)


def _make_armor(at: str, slot: str, tier: int, q: int, theme: str | None) -> dict:
    lvl = BRACKETS[tier]
    ilvl = lvl + (2 if q >= 3 else 0)
    name = MATERIALS[at][tier] + NOUNS[at][slot]
    if theme:
        name += THEMES[theme][0]
    return {
        "id": _gen_id(at, slot, tier, q, theme or "x"), "name": name, "q": q, "type": "armor", "slot": slot, "sub": at,
        "lvl": max(1, lvl - 1), "ilvl": ilvl, "stats": dict(make_stats(ilvl, q, slot, theme) if theme else {}),
        "armor": armor_value(ilvl, q, at, slot), "icon": ICONS[(at, slot)], "sell": sell_price(ilvl, q, slot),
        "vis": make_vis(at, tier, q, theme or "baer"), "bind": "boe" if q >= 3 else None, "gen": True, "tier": tier,
    }


def _make_weapon(sub: str, tier: int, q: int, theme: str) -> dict:
    lvl = BRACKETS[tier]
    ilvl = lvl + (2 if q >= 3 else 0)
    if sub in ("bogen", "stab"):
        name = WOOD[tier] + WNOUN[sub]
    elif sub == "zauberstab":
        name = GEMS[tier] + WNOUN[sub]
    else:
        name = WMAT[tier] + WNOUN[sub]
    name += THEMES[theme][0]
    slot = "main_hand"
    speed = WEAPON_SPEED[sub]
    dps = weapon_dps(ilvl, q, sub)
    avg = dps * speed
    w = {
        "id": _gen_id(sub, tier, q, theme), "name": name, "q": q, "type": "weapon", "slot": slot, "sub": sub,
        "two_hand": sub in TWO_HAND, "lvl": max(1, lvl - 1), "ilvl": ilvl, "speed": speed,
        "dmg": [max(1, int(avg * 0.78)), max(2, int(avg * 1.22))],
        "stats": make_stats(ilvl, q, "two_hand" if sub in TWO_HAND else "main_hand", theme),
        "icon": WICON[sub], "sell": sell_price(ilvl, q, "two_hand" if sub in TWO_HAND else "main_hand"),
        "vis": make_vis(sub, tier, q, theme), "bind": "boe" if q >= 3 else None, "gen": True, "tier": tier,
    }
    if sub in ("stab", "zauberstab"):
        w["stats"]["sp"] = w["stats"].get("sp", 0) + int(ilvl * 0.4 * QMULT[q])
    return w


def _make_offhand(sub: str, tier: int, q: int, theme: str) -> dict:
    lvl = BRACKETS[tier]
    ilvl = lvl + (2 if q >= 3 else 0)
    if sub == "schild":
        name = WMAT[tier] + "schild"
    elif sub == "buch":
        name = ["Lehrlings", "Novizen", "Gelehrten", "Runen", "Zwergen", "Frost", "Mond", "Sternen", "Glut", "Aschen",
                "Drachen", "Astral", "Himmels"][tier] + "foliant"
    elif sub == "kugel":
        name = GEMS[tier] + "kugel"
    else:
        name = ["Knochen", "Grab", "Gruft", "Ghul", "Seuchen", "Frost", "Geister", "Seelen", "Asche", "Dämonen",
                "Drachen", "Lich", "Himmels"][tier] + "schädel"
    name += THEMES[theme][0]
    it = {
        "id": _gen_id(sub, tier, q, theme), "name": name, "q": q, "type": "armor", "slot": "off_hand", "sub": sub,
        "lvl": max(1, lvl - 1), "ilvl": ilvl, "stats": make_stats(ilvl, q, "off_hand", theme),
        "icon": WICON[sub], "sell": sell_price(ilvl, q, "off_hand"), "vis": make_vis(sub, tier, q, theme),
        "bind": "boe" if q >= 3 else None, "gen": True, "tier": tier,
    }
    if sub == "schild":
        it["armor"] = int((20 + ilvl * 9) * (1 + 0.08 * max(0, q - 1)))
        it["stats"]["block"] = it["stats"].get("block", 0) + round(2 + ilvl * 0.05, 1)
    return it


def _make_jewel(slot: str, tier: int, q: int, theme: str) -> dict:
    lvl = BRACKETS[tier]
    ilvl = lvl + (2 if q >= 3 else 0)
    if slot == "neck":
        name, icon = GEMS[tier] + "amulett", "gem-pendant"
    elif slot == "ring":
        name, icon = (WMAT[tier] if tier % 2 == 0 else GEMS[tier]) + "ring", "ring"
    else:
        name, icon = (MATERIALS["stoff"][tier] if tier % 2 == 0 else MATERIALS["leder"][tier]) + "umhang", "cape"
    name += THEMES[theme][0]
    it = {
        "id": _gen_id(slot, tier, q, theme), "name": name, "q": q, "type": "armor" if slot == "back" else "jewelry",
        "slot": slot, "sub": "umhang" if slot == "back" else "schmuck", "lvl": max(1, lvl - 1), "ilvl": ilvl,
        "stats": make_stats(ilvl, q, slot, theme), "icon": icon, "sell": sell_price(ilvl, q, slot),
        "vis": make_vis("stoff", tier, q, theme), "bind": "boe" if q >= 3 else None, "gen": True, "tier": tier,
    }
    if slot == "back":
        it["armor"] = armor_value(ilvl, q, "stoff", "back") * 2
    return it


def _make_classslot(cls: str, tier: int, q: int) -> dict:
    key, noun, icon, shares = CLASS_SLOT[cls]
    lvl = BRACKETS[tier]
    ilvl = lvl + (2 if q >= 3 else 0)
    budget = stat_budget(ilvl, q, "class")
    stats = {}
    for s, share in shares.items():
        v = budget * share / STAT_COST[s]
        stats[s] = round(max(0.5, v), 1) if s in PERCENT_STATS else max(1, int(round(v)))
    return {
        "id": _gen_id("klasse", cls, tier, q), "name": f"{noun} {REGION_GEN[tier]}", "q": q, "type": "armor",
        "slot": "class", "sub": key, "cls": [cls], "lvl": max(1, lvl - 1), "ilvl": ilvl, "stats": stats, "icon": icon,
        "sell": sell_price(ilvl, q, "class"), "vis": {}, "bind": "boe" if q >= 3 else None, "gen": True, "tier": tier,
    }


def _generate():
    for tier in range(len(BRACKETS)):
        for at in ("stoff", "leder", "kette", "platte"):
            for slot in ("head", "shoulders", "chest", "hands", "legs", "feet"):
                _reg(_make_armor(at, slot, tier, 1, None))
                for i, theme in enumerate(THEMES_FOR[at]):
                    _reg(_make_armor(at, slot, tier, 2, theme))
                    if i < 3:
                        _reg(_make_armor(at, slot, tier, 3, theme))
        for sub in WNOUN:
            if sub == "schild":
                continue
            for i, theme in enumerate(THEMES_FOR[sub]):
                _reg(_make_weapon(sub, tier, 2, theme))
                if i < 2:
                    _reg(_make_weapon(sub, tier, 3, theme))
        for sub in ("schild", "buch", "kugel", "schaedel"):
            for i, theme in enumerate(THEMES_FOR[sub]):
                _reg(_make_offhand(sub, tier, 2, theme))
                if i < 1:
                    _reg(_make_offhand(sub, tier, 3, theme))
        for slot in ("neck", "ring", "back"):
            for theme in THEMES_FOR[slot]:
                _reg(_make_jewel(slot, tier, 2, theme))
                if theme in ("baer", "falke", "eule", "zauberei", "waechter"):
                    _reg(_make_jewel(slot, tier, 3, theme))
        for cls in CLASS_SLOT:
            _reg(_make_classslot(cls, tier, 2))
            _reg(_make_classslot(cls, tier, 3))


_generate()


def tier_for_level(level: int) -> int:
    t = 0
    for i, b in enumerate(BRACKETS):
        if level >= b - 1:
            t = i
    return t


_POOLS: dict[tuple, list[str]] = {}


def world_drop_pool(level: int, q: int = 2) -> list[str]:
    """Zufällige Weltbeute (grün/blau) passend zur Stufe."""
    t = tier_for_level(level)
    key = (t, q)
    if key not in _POOLS:
        _POOLS[key] = [i for i, it in ITEMS.items() if it.get("gen") and it["q"] == q and it.get("tier") == t]
    return _POOLS[key]


# =============================================================================== Unikate
def W(iid, name, q, sub, lvl, dmg, speed, stats=None, icon=None, desc="", bind=None, vis=None, ilvl=None, proc=None,
      set_id=None, sell=None, cls=None, unique=False, **kw):
    it = {"id": iid, "name": name, "q": q, "type": "weapon", "slot": "main_hand", "sub": sub, "two_hand": sub in TWO_HAND,
          "lvl": lvl, "ilvl": ilvl or lvl + (2 if q >= 3 else 0), "dmg": list(dmg), "speed": speed, "stats": stats or {},
          "icon": icon or WICON.get(sub, "broadsword"), "desc": desc, "bind": bind, "proc": proc, "set": set_id,
          "vis": vis or make_vis(sub, tier_for_level(lvl), q, "baer"), "cls": cls, "unique": unique}
    it["sell"] = sell if sell is not None else sell_price(it["ilvl"], q, "two_hand" if sub in TWO_HAND else "main_hand")
    it.update(kw)
    return _reg(it)


def AR(iid, name, q, slot, sub, lvl, stats, icon=None, desc="", bind=None, vis=None, ilvl=None, armor=None,
       set_id=None, sell=None, cls=None, proc=None, unique=False, **kw):
    t = "jewelry" if slot in ("neck", "ring") else "armor"
    il = ilvl or lvl + (2 if q >= 3 else 0)
    it = {"id": iid, "name": name, "q": q, "type": t, "slot": slot, "sub": sub, "lvl": lvl, "ilvl": il,
          "stats": stats, "desc": desc, "bind": bind, "set": set_id, "cls": cls, "proc": proc, "unique": unique,
          "icon": icon or (ICONS.get((sub, slot)) if (sub, slot) in ICONS else {"neck": "gem-pendant", "ring": "ring",
                           "back": "cape", "off_hand": WICON.get(sub, "checked-shield")}.get(slot, "chest-armor")),
          "vis": vis or make_vis(sub, tier_for_level(lvl), q, "waechter")}
    if armor is not None:
        it["armor"] = armor
    elif sub in ARMOR_K:
        it["armor"] = armor_value(il, q, sub, slot)
    elif sub == "umhang":
        it["armor"] = armor_value(il, q, "stoff", "back") * 2
    elif sub == "schild":
        it["armor"] = int((20 + il * 9) * (1 + 0.08 * max(0, q - 1)))
    it["sell"] = sell if sell is not None else sell_price(il, q, slot)
    it.update(kw)
    return _reg(it)


def CONS(iid, name, q, icon, use, desc, sell, buy=None, stack=20, lvl=1, **kw):
    it = {"id": iid, "name": name, "q": q, "type": "consumable", "icon": icon, "use": use, "desc": desc, "sell": sell,
          "buy": buy, "stack": stack, "lvl": lvl}
    it.update(kw)
    return _reg(it)


def MAT(iid, name, q, icon, sell, desc="", stack=50, prof=None, **kw):
    it = {"id": iid, "name": name, "q": q, "type": "material", "icon": icon, "sell": sell, "desc": desc, "stack": stack,
          "prof": prof}
    it.update(kw)
    return _reg(it)


def JUNK(iid, name, sell, icon, desc="", stack=20):
    return _reg({"id": iid, "name": name, "q": 0, "type": "junk", "sell": sell, "icon": icon, "desc": desc, "stack": stack})


def QUEST(iid, name, icon, desc="", stack=20):
    return _reg({"id": iid, "name": name, "q": 1, "type": "quest", "sell": 0, "icon": icon, "desc": desc, "stack": stack,
                 "quest": True, "bind": "bop"})


def V(c=None, m=None, a=None, g=None, gold=False, w=None):
    v = {}
    if c:
        v["c"] = c
    if m:
        v["m"] = m
    if a:
        v["a"] = a
    if g:
        v["g"] = g
    if gold:
        v["gold"] = True
    if w:
        v["w"] = w
    return v


# --------------------------------------------------------------------------- Startausrüstung
W("rostiges_langschwert", "Rostiges Langschwert", 1, "schwert", 1, (3, 6), 2.6, icon="rusty-sword", vis=V(m="#8a7a6a"))
W("schartiger_dolch", "Schartiger Dolch", 1, "dolch", 1, (2, 4), 1.8, vis=V(m="#8a8a8a"))
W("rostiges_messer", "Rostiges Messer", 1, "dolch", 1, (1, 3), 1.7, vis=V(m="#7a6a5a"))
W("uebungskatana", "Übungskatana", 1, "katana", 1, (4, 8), 2.9, vis=V(m="#a0a0a8"))
W("einfacher_kurzbogen", "Einfacher Kurzbogen", 1, "bogen", 1, (3, 7), 2.8, vis=V(w="#8a6038"))
W("schwere_holzfaelleraxt", "Schwere Holzfälleraxt", 1, "zweihandaxt", 1, (5, 9), 3.5, vis=V(m="#7a7a80"))
W("lehrlingsstab", "Lehrlingsstab", 1, "stab", 1, (2, 5), 3.0, stats={"int": 2, "sp": 2}, vis=V(w="#7a5232", g=None))
W("knorriger_eichenstab", "Knorriger Eichenstab", 1, "stab", 1, (2, 5), 3.0, stats={"int": 1, "spi": 1}, vis=V(w="#5a3a22"))
AR("abgenutzter_holzschild", "Abgenutzter Holzschild", 1, "off_hand", "schild", 1, {}, armor=18, vis=V(c="#6a4a2a", m="#7a7a80"))
AR("gepolsterte_rekrutenweste", "Gepolsterte Rekrutenweste", 1, "chest", "kette", 1, {}, armor=14, vis=V(c="#5a5a6a", m="#8a8e96"))
AR("abgewetztes_lederwams", "Abgewetztes Lederwams", 1, "chest", "leder", 1, {}, armor=8, vis=V(c="#6a4a2a"))
AR("rekrutenhose", "Rekrutenhose", 1, "legs", "leder", 1, {}, armor=6, vis=V(c="#4a3a2a"))
AR("abgetragene_stiefel", "Abgetragene Stiefel", 1, "feet", "leder", 1, {}, armor=4, vis=V(c="#4a3020"))
AR("lehrlingsrobe", "Lehrlingsrobe", 1, "chest", "stoff", 1, {"int": 1}, armor=4, vis=V(c="#5a4a8a"))
AR("lehrlingsschuhe", "Lehrlingsschuhe", 1, "feet", "stoff", 1, {}, armor=2, vis=V(c="#3a3050"))

# --------------------------------------------------------------------------- Verbrauchsgüter
CONS("frisches_brot", "Frisch gebackenes Brot", 1, "sliced-bread", {"type": "food", "amount": 61, "dur": 18},
     "Benutzen: Stellt im Sitzen über 18 Sek. 61 Gesundheit wieder her.", 1, 5)
CONS("klares_quellwasser", "Klares Quellwasser", 1, "water-flask", {"type": "drink", "amount": 151, "dur": 18},
     "Benutzen: Stellt im Sitzen über 18 Sek. 151 Mana wieder her.", 1, 5)
CONS("wildschweinbraten", "Saftiger Wildschweinbraten", 1, "meat", {"type": "food", "amount": 243, "dur": 21},
     "Benutzen: Stellt im Sitzen über 21 Sek. 243 Gesundheit wieder her.", 6, 25, lvl=5)
CONS("melonensaft", "Gekühlter Melonensaft", 1, "glass-heart", {"type": "drink", "amount": 436, "dur": 21},
     "Benutzen: Stellt im Sitzen über 21 Sek. 436 Mana wieder her.", 6, 25, lvl=5)
CONS("zwergenbrot", "Zwergisches Steinbrot", 1, "bread", {"type": "food", "amount": 874, "dur": 24},
     "Benutzen: Stellt im Sitzen über 24 Sek. 874 Gesundheit wieder her.", 25, 120, lvl=15)
CONS("bergquellwasser", "Eisiges Bergquellwasser", 1, "water-flask", {"type": "drink", "amount": 1344, "dur": 24},
     "Benutzen: Stellt im Sitzen über 24 Sek. 1344 Mana wieder her.", 25, 120, lvl=15)
CONS("mondbeerenkuchen", "Mondbeerenkuchen", 1, "cake-slice", {"type": "food", "amount": 1933, "dur": 27},
     "Benutzen: Stellt im Sitzen über 27 Sek. 1933 Gesundheit wieder her.", 60, 300, lvl=25)
CONS("tauwasser", "Mondtauwasser", 1, "water-flask", {"type": "drink", "amount": 2934, "dur": 27},
     "Benutzen: Stellt im Sitzen über 27 Sek. 2934 Mana wieder her.", 60, 300, lvl=25)
CONS("feuerbraten", "Feuergerösteter Braten", 1, "meat", {"type": "food", "amount": 3600, "dur": 30},
     "Benutzen: Stellt im Sitzen über 30 Sek. 3600 Gesundheit wieder her.", 120, 600, lvl=35)
CONS("sternenwasser", "Sternenquellwasser", 1, "water-flask", {"type": "drink", "amount": 5200, "dur": 30},
     "Benutzen: Stellt im Sitzen über 30 Sek. 5200 Mana wieder her.", 120, 600, lvl=35)
CONS("schwacher_heiltrank", "Schwacher Heiltrank", 1, "health-potion", {"type": "heal", "amount": 90, "cd": 60},
     "Benutzen: Stellt sofort 70 bis 110 Gesundheit wieder her.", 5, 40, stack=10)
CONS("schwacher_manatrank", "Schwacher Manatrank", 1, "magic-potion", {"type": "mana", "amount": 160, "cd": 60},
     "Benutzen: Stellt sofort 140 bis 180 Mana wieder her.", 5, 40, stack=10)
CONS("heiltrank", "Heiltrank", 1, "health-potion", {"type": "heal", "amount": 380, "cd": 60},
     "Benutzen: Stellt sofort 300 bis 460 Gesundheit wieder her.", 25, 150, stack=10, lvl=12)
CONS("manatrank", "Manatrank", 1, "magic-potion", {"type": "mana", "amount": 520, "cd": 60},
     "Benutzen: Stellt sofort 420 bis 620 Mana wieder her.", 25, 150, stack=10, lvl=12)
CONS("grosser_heiltrank", "Großer Heiltrank", 1, "health-potion", {"type": "heal", "amount": 1100, "cd": 60},
     "Benutzen: Stellt sofort 900 bis 1300 Gesundheit wieder her.", 80, 400, stack=10, lvl=25)
CONS("grosser_manatrank", "Großer Manatrank", 1, "magic-potion", {"type": "mana", "amount": 1400, "cd": 60},
     "Benutzen: Stellt sofort 1100 bis 1700 Mana wieder her.", 80, 400, stack=10, lvl=25)
CONS("maechtiger_heiltrank", "Mächtiger Heiltrank", 2, "health-potion", {"type": "heal", "amount": 2600, "cd": 60},
     "Benutzen: Stellt sofort 2100 bis 3100 Gesundheit wieder her.", 200, None, stack=10, lvl=40)
CONS("maechtiger_manatrank", "Mächtiger Manatrank", 2, "magic-potion", {"type": "mana", "amount": 3200, "cd": 60},
     "Benutzen: Stellt sofort 2600 bis 3800 Mana wieder her.", 200, None, stack=10, lvl=40)
CONS("elixier_der_staerke", "Elixier der Stärke", 2, "bubbling-flask", {"type": "elixir", "aura": "elixier_staerke",
     "stats": {"str": 15}, "dur": 3600}, "Benutzen: Erhöht 1 Std. lang Stärke um 15.", 60, stack=10, lvl=10)
CONS("elixier_der_weisheit", "Elixier der Weisheit", 2, "bubbling-flask", {"type": "elixir", "aura": "elixier_weisheit",
     "stats": {"int": 15, "spi": 8}, "dur": 3600}, "Benutzen: Erhöht 1 Std. lang Intelligenz um 15 und Willenskraft um 8.", 60, stack=10, lvl=10)
CONS("elixier_der_flinkheit", "Elixier der Flinkheit", 2, "bubbling-flask", {"type": "elixir", "aura": "elixier_flinkheit",
     "stats": {"agi": 15}, "dur": 3600}, "Benutzen: Erhöht 1 Std. lang Beweglichkeit um 15.", 60, stack=10, lvl=10)
CONS("elixier_der_festung", "Elixier der Festung", 2, "bubbling-flask", {"type": "elixir", "aura": "elixier_festung",
     "stats": {"sta": 25, "armor": 200}, "dur": 3600}, "Benutzen: Erhöht 1 Std. lang Ausdauer um 25 und Rüstung um 200.", 120, stack=10, lvl=25)
CONS("feuerschutztrank", "Feuerschutztrank", 2, "fire-bottle", {"type": "elixir", "aura": "feuerschutz",
     "stats": {"fire_res": 60}, "dur": 1800}, "Benutzen: Erhöht 30 Min. lang den Feuerwiderstand um 60. Ideal gegen Varkor.", 200, stack=10, lvl=35)
CONS("lebensgeistelixier", "Elixier des Kriegers", 3, "fizzing-flask", {"type": "elixir", "aura": "elixier_krieger",
     "stats": {"str": 30, "agi": 30, "sta": 30}, "dur": 3600}, "Benutzen: Erhöht 1 Std. lang Stärke, Beweglichkeit und Ausdauer um 30.", 400, stack=10, lvl=40)
CONS("elixier_der_magie", "Elixier der Arkanmagie", 3, "fizzing-flask", {"type": "elixir", "aura": "elixier_magie",
     "stats": {"sp": 45, "int": 25}, "dur": 3600}, "Benutzen: Erhöht 1 Std. lang Zaubermacht um 45 und Intelligenz um 25.", 400, stack=10, lvl=40)
CONS("wundgift", "Wundgift", 1, "poison-bottle", {"type": "weapon_oil", "aura": "wundgift", "proc": {"chance": 0.3,
     "dmg": {"school": "nature", "base": (5, 1.5, 7, 1.8)}}, "dur": 1800},
     "Benutzen: Eure Waffe wird 30 Min. vergiftet (30 % Chance auf Naturschaden).", 30, stack=10, lvl=8)
CONS("ruhestein", "Ruhestein", 1, "stone-tablet", {"type": "hearth", "cd": 900},
     "Benutzen: Bringt Euch zum zuletzt aktivierten Teleportationsstein zurück (15 Min. Abklingzeit).", 0, stack=1, bind="bop")

# --------------------------------------------------------------------------- Plunder (grau)
JUNK("raeudiges_wolfsfell", "Räudiges Wolfsfell", 14, "pelt")
JUNK("zerbrochener_reisszahn", "Zerbrochener Reißzahn", 9, "fangs")
JUNK("zaehes_fleisch", "Zähes Schweinefleisch", 11, "meat")
JUNK("rotdolch_abzeichen", "Rotdolch-Abzeichen", 31, "badge")
JUNK("verbogener_loeffel", "Verbogener Kobold-Löffel", 26, "spoon")
JUNK("knochensplitter", "Knochensplitter", 38, "broken-bone")
JUNK("vergilbter_schaedel", "Vergilbter Schädel", 55, "skull-crossed-bones")
JUNK("kaninchenpfote", "Glückliche Kaninchenpfote", 4, "rabbit", "Für das Kaninchen war sie offenbar nicht so glücklich.")
JUNK("gefrorene_zehe", "Gefrorene Riesenzehe", 120, "footprint")
JUNK("zerbrochene_spitzhacke", "Zerbrochene Spitzhacke", 95, "war-pick")
JUNK("verblasste_feenfluegel", "Verblasste Feenflügel", 210, "fairy-wings")
JUNK("verkohlte_knochen", "Verkohlte Knochen", 380, "broken-bone")
JUNK("schwefelbrocken", "Schwefelbrocken", 420, "rock")
JUNK("sternenstaub_plunder", "Erloschener Sternenstaub", 650, "sparkles")

# --------------------------------------------------------------------------- Materialien (Berufe)
MAT("kupfererz", "Kupfererz", 1, "ore", 5, "Bergbau (1). Wird zu Kupferbarren geschmolzen.", prof="bergbau")
MAT("eisenerz", "Eisenerz", 1, "ore", 25, "Bergbau (60).", prof="bergbau")
MAT("mithrilerz", "Mithrilerz", 1, "ore", 80, "Bergbau (120).", prof="bergbau")
MAT("glutsteinerz", "Glutsteinerz", 1, "ore", 160, "Bergbau (180).", prof="bergbau")
MAT("sternenerz", "Sternenerz", 2, "ore", 300, "Bergbau (240). Fällt angeblich vom Himmel.", prof="bergbau")
MAT("kupferbarren", "Kupferbarren", 1, "metal-bar", 12, "Schmiedekunst.")
MAT("eisenbarren", "Eisenbarren", 1, "metal-bar", 55, "Schmiedekunst.")
MAT("mithrilbarren", "Mithrilbarren", 1, "metal-bar", 170, "Schmiedekunst.")
MAT("glutstahlbarren", "Glutstahlbarren", 1, "metal-bar", 340, "Schmiedekunst.")
MAT("sternenstahlbarren", "Sternenstahlbarren", 2, "metal-bar", 640, "Schmiedekunst.")
MAT("friedblume", "Friedblume", 1, "flower-emblem", 4, "Kräuterkunde (1).", prof="kraeuter")
MAT("silberblatt", "Silberblatt", 1, "leaf-swirl", 6, "Kräuterkunde (1).", prof="kraeuter")
MAT("frostmoos", "Frostmoos", 1, "curled-leaf", 30, "Kräuterkunde (60).", prof="kraeuter")
MAT("mondkraut", "Mondkraut", 1, "moon", 70, "Kräuterkunde (120).", prof="kraeuter")
MAT("feuerbluete", "Feuerblüte", 1, "fire-flower", 150, "Kräuterkunde (180).", prof="kraeuter")
MAT("himmelsdistel", "Himmelsdistel", 2, "thistle", 280, "Kräuterkunde (240).", prof="kraeuter")
MAT("leichtes_leder", "Leichtes Leder", 1, "animal-hide", 8, "Lederverarbeitung. Von Tieren der Grünmark.")
MAT("mittleres_leder", "Mittleres Leder", 1, "animal-hide", 35, "Lederverarbeitung.")
MAT("schweres_leder", "Schweres Leder", 1, "animal-hide", 90, "Lederverarbeitung.")
MAT("dickes_leder", "Dickes Leder", 1, "animal-hide", 180, "Lederverarbeitung.")
MAT("drachenhaut", "Drachenhaut", 2, "dragon-head", 420, "Lederverarbeitung. Von Drachen und Drachkin.")
MAT("leinenstoff", "Leinenstoff", 1, "rolled-cloth", 3, "Von humanoiden Gegnern.")
MAT("wollstoff", "Wollstoff", 1, "rolled-cloth", 15, "Von humanoiden Gegnern.")
MAT("seidenstoff", "Seidenstoff", 1, "rolled-cloth", 40, "Von humanoiden Gegnern.")
MAT("runenstoff", "Runenstoff", 1, "rolled-cloth", 90, "Von humanoiden Gegnern.")
MAT("magischer_staub", "Magischer Staub", 1, "powder", 30, "Verzauberkunst. Entsteht beim Entzaubern grüner Gegenstände.")
MAT("glitzernde_essenz", "Glitzernde Essenz", 2, "sparkles", 120, "Verzauberkunst. Entsteht beim Entzaubern.")
MAT("strahlender_splitter", "Strahlender Splitter", 3, "crystal-growth", 600, "Verzauberkunst. Entsteht beim Entzaubern seltener Gegenstände.")
MAT("leerenkristall", "Leerenkristall", 4, "crystal-eye", 3000, "Verzauberkunst. Entsteht beim Entzaubern epischer Gegenstände.")
MAT("leeres_flaeschchen", "Leeres Fläschchen", 1, "round-bottom-flask", 1, "Alchemie.", buy=4)
MAT("kristallphiole", "Kristallphiole", 1, "round-bottom-flask", 20, "Alchemie.", buy=80)
MAT("grober_faden", "Grober Faden", 1, "sewing-string", 2, "Lederverarbeitung.", buy=10)
MAT("seidenfaden", "Seidenfaden", 1, "sewing-string", 25, "Lederverarbeitung.", buy=100)
MAT("schmiedekohle", "Schmiedekohle", 1, "coal-pile", 5, "Schmiedekunst.", buy=20)
MAT("drachenschuppe", "Schuppe des Aschendrachen", 4, "dragon-shield", 2000, "Ein Material von Varkor. Für die mächtigsten Rezepte.", stack=20, bind="bop")
MAT("weltenstein", "Weltenstein-Fragment", 5, "crystal-cluster", 5000, "Ein Splitter aus dem Thron des Weltenbrechers.", stack=10, bind="bop")
MAT("schmiedekern", "Glühender Schmiedekern", 3, "fire-gem", 800, "Herz eines Schmiedegolems.", stack=10)
MAT("verfluchte_reliquie", "Verfluchte Reliquie", 3, "relic-blade", 1200, "Aus der Kathedrale der Verdammten.", stack=10)
MAT("feenstaub", "Feenstaub", 2, "sparkles", 90, "Glitzert in allen Farben. Von Feenwesen des Mondhains.")
MAT("eiskern", "Eiskern", 2, "ice-cube", 140, "Kalt genug, um die Hand zu verbrennen. Von Eisriesen.")
MAT("daemonenblut", "Dämonenblut", 2, "drop", 260, "Brodelt auch noch nach Tagen. Aus den Aschenlanden.")

# --------------------------------------------------------------------------- Questgegenstände (Grünmark)
QUEST("wiesenkraut", "Wiesenkraut", "herbs-bundle", "Duftet nach Sommer. Kathi braucht es für die Burgküche.")
QUEST("wildschweinkeule", "Wildschweinkeule", "meat")
QUEST("schweineblase", "Aufgeblasene Schweineblase", "balloons", "Hüpft erstaunlich gut.")
QUEST("leonines_medaillon", "Leonines Medaillon", "pendant-key", "Ein silbernes Medaillon mit einer eingravierten Rose.", 1)
QUEST("kobold_kerze", "Kobold-Kerze", "candle-light", "\"Du nicht nehmen die Kerze!\"")
QUEST("liebesbrief", "Versiegelter Liebesbrief", "envelope", "Riecht stark nach Rosenwasser. Nicht öffnen!", 1)
QUEST("gackerle", "Gackerle", "chicken", "Das Lieblingshuhn des Dorftrottels. Es gackert empört.", 1)
QUEST("morgraths_siegel", "Morgraths Siegel", "seal", "Das Siegel des gefallenen Ritters Morgrath.", 1)

# --------------------------------------------------------------------------- Grünmark-Belohnungen (grün/blau)
AR("wolfsfellumhang", "Wolfsfellumhang", 2, "back", "umhang", 3, {"sta": 1, "agi": 1}, vis=V(c="#7a7a72"))
AR("jaegerhandschuhe", "Jägerhandschuhe der Grünmark", 2, "hands", "leder", 4, {"agi": 2, "sta": 1}, vis=V(c="#5a6a2a"))
AR("bauernstiefel", "Stiefel des Bauern", 2, "feet", "leder", 3, {"sta": 2}, vis=V(c="#6a4a2a"))
AR("rotdolch_kopftuch", "Rotdolch-Kopftuch", 2, "head", "leder", 5, {"agi": 2, "sta": 2}, vis=V(c="#8a1a1a"))
AR("banditenweste", "Gesteppte Banditenweste", 2, "chest", "leder", 5, {"str": 2, "sta": 2}, vis=V(c="#6a2a2a"))
AR("schimmernde_robe", "Schimmernde Robe", 2, "chest", "stoff", 5, {"int": 3, "spi": 2}, vis=V(c="#4a6aa8"))
AR("kerzenwachshose", "Kerzenwachsverschmierte Hose", 2, "legs", "stoff", 6, {"int": 2, "sta": 2}, vis=V(c="#c8b080"))
AR("stollenhandschuhe", "Stollenhandschuhe", 2, "hands", "kette", 6, {"str": 2, "sta": 1}, vis=V(m="#8a8070"))
AR("rekrutenhandschuhe", "Rekrutenhandschuhe aus Platte", 2, "hands", "platte", 2, {"str": 1, "sta": 1}, vis=V(m="#9a9ea6"))
AR("gewebte_handschuhe", "Gewebte Handschuhe", 2, "hands", "stoff", 2, {"int": 1, "spi": 1}, vis=V(c="#5a4a8a"))
AR("geschmeidige_handschuhe", "Geschmeidige Lederhandschuhe", 2, "hands", "leder", 2, {"agi": 1, "sta": 1}, vis=V(c="#6a4a2a"))
AR("kraeuterumhang", "Duftender Kräuterumhang", 2, "back", "umhang", 3, {"spi": 2, "sta": 1}, vis=V(c="#4a7a3a"))
AR("gauklerhandschuhe", "Gauklerhandschuhe", 2, "hands", "stoff", 4, {"agi": 2, "int": 2}, vis=V(c="#d43c8f"),
   desc="Fingerlos. Zum Jonglieren und Taschendiebstahl gleichermaßen geeignet.")
AR("glueckfeder", "Glücksfeder des Dorftrottels", 2, "neck", "schmuck", 2, {"str": 1, "agi": 1, "sta": 1, "int": 1, "spi": 1},
   icon="feather", desc="\"Die hat mir ein Vogel geschenkt. Glaub ich.\"")
AR("monokel", "Monokel des Einäugigen", 2, "head", "stoff", 6, {"int": 3, "spi": 2, "sta": 1}, icon="monocle",
   desc="Für ein Auge mehr als genug.", vis=V(c="#3a3a3a"))
AR("wachmannsschultern", "Wachmannsschulterstücke", 2, "shoulders", "platte", 6, {"str": 2, "sta": 2}, vis=V(m="#a8acb6", c="#3a5b8c"))
AR("lehrlingsschultertuch", "Schultertuch des Gelehrten", 2, "shoulders", "stoff", 6, {"int": 2, "spi": 2}, vis=V(c="#4a3a8a"))
AR("lederschultern_spaeher", "Späherschulterstücke", 2, "shoulders", "leder", 6, {"agi": 2, "sta": 2}, vis=V(c="#4a5a2a"))
AR("ring_standhaftigkeit", "Ring der Standhaftigkeit", 2, "ring", "schmuck", 5, {"str": 2, "sta": 2})
AR("ring_klarheit", "Ring der Klarheit", 2, "ring", "schmuck", 5, {"int": 2, "spi": 2})
AR("ring_der_schnelligkeit", "Ring der Schnelligkeit", 2, "ring", "schmuck", 5, {"agi": 2, "sta": 2})
W("gundolfs_breitschwert", "Gundolfs Breitschwert", 2, "schwert", 6, (9, 17), 2.7, {"str": 3})
W("gluehender_kupferstab", "Glühender Kupferstab", 2, "stab", 6, (8, 14), 3.0, {"int": 3, "sp": 4}, vis=V(w="#b07a3a", g="#ff9a40"))
W("gundolfs_kurzbogen", "Gundolfs Jagdbogen", 2, "bogen", 6, (8, 15), 2.8, {"agi": 3})
W("gundolfs_streitaxt", "Gundolfs Streitaxt", 2, "zweihandaxt", 6, (14, 23), 3.5, {"str": 3, "sta": 2})
W("gundolfs_katana", "Gundolfs Klinge des Ostens", 2, "katana", 6, (12, 20), 2.9, {"agi": 2, "str": 2})
W("gundolfs_dolch", "Gundolfs Stilett", 2, "dolch", 6, (5, 10), 1.8, {"agi": 3})
W("wolfszahnaxt", "Wolfszahnaxt", 2, "axt", 3, (5, 10), 2.5, {"str": 1, "sta": 1})
W("eichenstab", "Knorriger Eichenstab der Weisheit", 2, "stab", 3, (5, 10), 3.0, {"int": 1, "spi": 1})
W("stollenhammer", "Stollenhammer", 2, "streitkolben", 6, (8, 15), 2.6, {"str": 2, "sta": 1})
AR("zauberfoliant", "Abgegriffener Zauberfoliant", 2, "off_hand", "buch", 5, {"int": 2, "sp": 3})
AR("beschlagener_schild", "Eisenbeschlagener Schild", 2, "off_hand", "schild", 5, {"sta": 2}, armor=95, vis=V(c="#6a4a2a", m="#8a8e96"))
AR("knochenschaedel_fokus", "Polierter Kobold-Schädel", 2, "off_hand", "schaedel", 5, {"int": 2, "sp": 3})

# --------------------------------------------------------------------------- Krypta (blau/episch)
_KR = "Die vergessene Krypta"
W("grimbarts_dolch", "Grimbarts roter Dolch", 3, "dolch", 7, (7, 13), 1.8, {"agi": 3, "sta": 2, "int": 2},
  desc="An der Klinge klebt noch Lagerfeuerruß.", bind="bop", vis=V(m="#c03030", a="#c9a040"))
W("rotdolch_brecher", "Rotdolch-Brecher", 3, "streitkolben", 7, (13, 24), 2.8, {"str": 4, "sta": 3}, bind="bop")
AR("robe_der_wachsamkeit", "Robe der Wachsamkeit", 3, "chest", "stoff", 7, {"int": 5, "spi": 4, "sta": 3}, bind="bop", vis=V(c="#2a4a8a"))
AR("grabwaechter_schultern", "Schulterplatten des Grabwächters", 3, "shoulders", "platte", 9, {"str": 4, "sta": 4}, bind="bop", vis=V(m="#8a8a94", c="#3a3a4a"))
AR("leichentuchrobe", "Leichentuchrobe", 3, "chest", "stoff", 9, {"int": 6, "sta": 4, "sp": 5}, bind="bop", vis=V(c="#d8d4c8"))
AR("umhang_grabesruhe", "Umhang der Grabesruhe", 3, "back", "umhang", 9, {"sta": 3, "spi": 3}, bind="bop", vis=V(c="#3a3a4a"))
AR("ring_der_vergessenen", "Ring der Vergessenen", 3, "ring", "schmuck", 9, {"sta": 3, "int": 3, "str": 3}, bind="bop")
AR("wiedergaenger_stiefel", "Stiefel des Wiedergängers", 3, "feet", "platte", 9, {"str": 3, "sta": 4}, bind="bop")
AR("knochenmagier_kappe", "Kappe des Knochenmagiers", 3, "head", "stoff", 9, {"int": 5, "spi": 3, "sp": 4}, bind="bop", vis=V(c="#4a3a5a"))
AR("gruftschleicher_wams", "Wams des Gruftschleichers", 3, "chest", "leder", 9, {"agi": 6, "sta": 4}, bind="bop", vis=V(c="#2a2a32"))
AR("gruftkettenhemd", "Kettenhemd der Gruftwache", 3, "chest", "kette", 9, {"agi": 4, "str": 3, "sta": 4}, bind="bop", vis=V(m="#8a8e96", c="#3a3a4a"))
W("klinge_des_herrschers", "Klinge des Herrschers", 3, "schwert", 9, (15, 28), 2.6, {"str": 5, "sta": 4},
  desc="Ein Geschenk Simons, des zweiäugigen Herrschers.", bind="bop", vis=V(m="#e0e6f0", a="#e0b648"))
W("simons_zepter", "Simons Ersatzzepter", 3, "stab", 9, (11, 20), 3.0, {"int": 6, "spi": 4, "sp": 8},
  desc="\"Ich habe noch zwei davon. Für jedes Auge eins.\"", bind="bop", vis=V(w="#d0a840", g="#ffe080"))
W("simons_jagdbogen", "Simons Jagdbogen", 3, "bogen", 9, (14, 26), 2.8, {"agi": 6, "sta": 3}, bind="bop", vis=V(w="#d0a840"))
W("simons_zweihaender", "Simons Paradezweihänder", 3, "zweihandschwert", 9, (24, 38), 3.4, {"str": 7, "sta": 5}, bind="bop")
W("simons_katana", "Simons Klinge der zwei Augen", 3, "katana", 9, (20, 33), 2.9, {"agi": 5, "str": 4}, bind="bop")
W("simons_dolche", "Simons Brieföffner", 3, "dolch", 9, (9, 16), 1.8, {"agi": 5, "sta": 3}, bind="bop",
  desc="Erstaunlich scharf für einen Brieföffner.")
AR("gesegnete_handschuhe", "Gesegnete Panzerhandschuhe", 3, "hands", "platte", 8, {"str": 3, "sta": 4}, bind="bop",
   desc="Bruder Anselm hat sie dreimal gesegnet. Sicher ist sicher.")
AR("handschuhe_der_andacht", "Handschuhe der Andacht", 3, "hands", "stoff", 8, {"int": 4, "spi": 3, "sp": 4}, bind="bop")
AR("handschuhe_des_pilgers", "Handschuhe des Pilgers", 3, "hands", "leder", 8, {"agi": 4, "sta": 3}, bind="bop")
W("morgraths_seelenklinge", "Morgraths Seelenklinge", 4, "schwert", 10, (22, 38), 2.8, {"str": 8, "sta": 7},
  desc="Die Klinge flüstert Namen längst Vergessener.", bind="bop", vis=V(m="#7a8aa8", a="#3a3a4a", g="#60c0ff"),
  proc={"chance": 0.08, "dmg": {"school": "shadow", "base": (20, 3, 30, 4)}, "name": "Seelenbiss"})
AR("schild_des_gefallenen", "Schild des gefallenen Ritters", 4, "off_hand", "schild", 10, {"sta": 8, "str": 3},
   armor=260, bind="bop", vis=V(c="#2a2a3a", m="#6a7a98", a="#a0a0b0", g="#60c0ff"))
W("stab_verlorener_seelen", "Stab der verlorenen Seelen", 4, "stab", 10, (16, 29), 3.0, {"int": 10, "spi": 6, "sp": 18},
  bind="bop", vis=V(w="#3a3a4a", g="#80d0ff"))
W("morgraths_zweihaender", "Morgraths Grabzweihänder", 4, "zweihandschwert", 10, (32, 52), 3.4, {"str": 12, "sta": 9},
  bind="bop", vis=V(m="#7a8aa8", a="#3a3a4a", g="#60c0ff"))
W("morgraths_bogen", "Bogen des Totenwächters", 4, "bogen", 10, (20, 35), 2.8, {"agi": 10, "sta": 6}, bind="bop",
  vis=V(w="#3a3a4a", g="#80d0ff"))
AR("kapuze_der_grabesstille", "Kapuze der Grabesstille", 4, "head", "stoff", 10, {"int": 8, "sta": 6, "sp": 10},
   bind="bop", vis=V(c="#2a2a3a", g="#80d0ff"))
AR("morgraths_helm", "Morgraths gehörnter Helm", 4, "head", "platte", 10, {"str": 7, "sta": 8}, bind="bop",
   vis=V(m="#6a7a98", c="#2a2a3a", g="#60c0ff"))
AR("maske_des_grabraeubers", "Maske des Grabräubers", 4, "head", "leder", 10, {"agi": 8, "sta": 7}, bind="bop",
   vis=V(c="#2a2a32", g="#80d0ff"))
AR("eldornias_traene", "Eldornias Träne", 5, "ring", "schmuck", 10, {"str": 5, "agi": 5, "sta": 5, "int": 5, "spi": 5, "sp": 12},
   desc="Man sagt, Eldornia selbst habe diesen Stein geweint, als Morgrath fiel.", bind="bop", unique=True)


# =============================================================================== Sets
SETS = {
    "krypta_wacht": {
        "name": "Rüstung der Krypta-Wacht",
        "items": ["kw_helm", "kw_schultern", "kw_brust"],
        "bonuses": {2: {"stats": {"sta": 10}, "text": "+10 Ausdauer"},
                    3: {"stats": {"armor": 150, "shadow_res": 20}, "text": "+150 Rüstung und +20 Schattenwiderstand"}},
    },
    "schmiedefeuer": {
        "name": "Schmiedefeuer-Garnitur",
        "items": ["sf_helm", "sf_brust", "sf_handschuhe", "sf_beine"],
        "bonuses": {2: {"stats": {"fire_res": 25}, "text": "+25 Feuerwiderstand"},
                    4: {"pct": {"dmg_done": 5}, "text": "Erhöht verursachten Schaden um 5 %"}},
    },
    "aschendrache": {
        "name": "Set des Aschendrachen",
        "items": ["ad_helm", "ad_schultern", "ad_brust", "ad_handschuhe", "ad_beine", "ad_stiefel"],
        "bonuses": {2: {"stats": {"fire_res": 40}, "text": "Feuerresistenz erhöht (+40)"},
                    4: {"school_pct": {"fire": 15}, "text": "Feuerschaden um 15 % erhöht"},
                    6: {"proc": {"on": "crit", "chance": 1.0, "icd": 4.0, "aoe": {"school": "fire", "base": (40, 6, 60, 8), "radius": 6}},
                        "text": "Kritische Treffer lösen eine Feuerexplosion aus, die Flächenschaden verursacht (alle 4 Sek.)."}},
    },
    "kathedrale": {
        "name": "Gewänder der Verdammten",
        "items": ["kv_kopf", "kv_schultern", "kv_brust", "kv_beine", "kv_haende"],
        "bonuses": {2: {"stats": {"shadow_res": 30}, "text": "+30 Schattenwiderstand"},
                    3: {"pct": {"heal_done": 8}, "text": "Heilung um 8 % erhöht"},
                    5: {"pct": {"dmg_done": 8}, "text": "Schaden um 8 % erhöht"}},
    },
    "weltenbrecher": {
        "name": "Rüstung des Weltenbrechers",
        "items": ["wb_helm", "wb_schultern", "wb_brust", "wb_haende", "wb_beine", "wb_stiefel"],
        "bonuses": {2: {"stats": {"sta": 40}, "text": "+40 Ausdauer"},
                    4: {"pct": {"dmg_done": 6, "heal_done": 6}, "text": "Schaden und Heilung um 6 % erhöht"},
                    6: {"pct": {"dmg_taken": -8}, "stats": {"crit": 3}, "text": "Erlittener Schaden −8 %, +3 % kritische Treffer"}},
    },
}


def _set_piece(iid, set_id, slot, sub, lvl, q, name, stats, vis):
    return AR(iid, name, q, slot, sub, lvl, stats, set_id=set_id, bind="bop", vis=vis)


# Krypta-Wacht (Platte, blau)
_set_piece("kw_helm", "krypta_wacht", "head", "platte", 10, 3, "Helm der Krypta-Wacht", {"str": 5, "sta": 6}, V(m="#8a8e9a", c="#3a3a4a"))
_set_piece("kw_schultern", "krypta_wacht", "shoulders", "platte", 10, 3, "Schulterplatten der Krypta-Wacht", {"str": 4, "sta": 5}, V(m="#8a8e9a", c="#3a3a4a"))
_set_piece("kw_brust", "krypta_wacht", "chest", "platte", 10, 3, "Brustplatte der Krypta-Wacht", {"str": 6, "sta": 7}, V(m="#8a8e9a", c="#3a3a4a"))
# Schmiedefeuer (Kette, blau)
for _iid, _slot, _n, _st in [("sf_helm", "head", "Schmiedefeuerhaube", {"str": 9, "agi": 6, "sta": 10}),
                              ("sf_brust", "chest", "Schmiedefeuerhemd", {"str": 11, "agi": 7, "sta": 12}),
                              ("sf_handschuhe", "hands", "Schmiedefeuerhandschuhe", {"str": 7, "agi": 5, "sta": 7}),
                              ("sf_beine", "legs", "Schmiedefeuerbeinlinge", {"str": 10, "agi": 7, "sta": 11})]:
    _set_piece(_iid, "schmiedefeuer", _slot, "kette", 28, 3, _n, _st, V(m="#5a4a48", c="#8a3a1a", g=None))
# Aschendrache (Platte, episch – Varkor und Aschenlande)
for _iid, _slot, _n, _st in [("ad_helm", "head", "Krone des Aschendrachen", {"str": 22, "sta": 24, "crit": 1.0}),
                              ("ad_schultern", "shoulders", "Schwingen des Aschendrachen", {"str": 17, "sta": 18}),
                              ("ad_brust", "chest", "Brustpanzer des Aschendrachen", {"str": 24, "sta": 26, "crit": 1.0}),
                              ("ad_handschuhe", "hands", "Klauen des Aschendrachen", {"str": 16, "sta": 17, "haste": 1.0}),
                              ("ad_beine", "legs", "Beinschienen des Aschendrachen", {"str": 22, "sta": 25}),
                              ("ad_stiefel", "feet", "Tritte des Aschendrachen", {"str": 16, "sta": 18})]:
    _set_piece(_iid, "aschendrache", _slot, "platte", 48, 4, _n, _st, V(m="#3a3436", c="#8a2a10", a="#ff7a20", g="#ff6a1a"))
# Kathedrale (Stoff, episch)
for _iid, _slot, _n, _st in [("kv_kopf", "head", "Mitra der Verdammten", {"int": 18, "spi": 12, "sp": 22}),
                              ("kv_schultern", "shoulders", "Stola der Verdammten", {"int": 14, "spi": 9, "sp": 16}),
                              ("kv_brust", "chest", "Robe der Verdammten", {"int": 20, "spi": 13, "sp": 25}),
                              ("kv_beine", "legs", "Beinkleider der Verdammten", {"int": 18, "spi": 12, "sp": 22}),
                              ("kv_haende", "hands", "Handschuhe der Verdammten", {"int": 13, "spi": 9, "sp": 15})]:
    _set_piece(_iid, "kathedrale", _slot, "stoff", 42, 4, _n, _st, V(c="#3a1a4a", a="#c9a040", g="#b070ff"))
# Weltenbrecher (Platte, mythisch)
for _iid, _slot, _n, _st in [("wb_helm", "head", "Helm des Weltenbrechers", {"str": 30, "sta": 34, "crit": 1.5}),
                              ("wb_schultern", "shoulders", "Schulterstücke des Weltenbrechers", {"str": 23, "sta": 26}),
                              ("wb_brust", "chest", "Brustplatte des Weltenbrechers", {"str": 32, "sta": 36, "crit": 1.5}),
                              ("wb_haende", "hands", "Fäuste des Weltenbrechers", {"str": 22, "sta": 24, "haste": 1.5}),
                              ("wb_beine", "legs", "Beinplatten des Weltenbrechers", {"str": 30, "sta": 34}),
                              ("wb_stiefel", "feet", "Schreiter des Weltenbrechers", {"str": 22, "sta": 25})]:
    _set_piece(_iid, "weltenbrecher", _slot, "platte", 50, 6, _n, _st, V(m="#e8f0ff", c="#2a6ad8", a="#e0c070", g="#2ee6d6", gold=True))
    ITEMS[_iid]["ilvl"] = 62

for _sid, _s in SETS.items():
    for _iid in _s["items"]:
        ITEMS[_iid]["set"] = _sid


# =============================================================================== Hilfsfunktionen
def item_usable_by(item: dict, class_def: dict, class_id: str | None = None) -> bool:
    """Darf eine Klasse diesen Gegenstand anlegen?"""
    if item.get("cls") and class_id and class_id not in item["cls"]:
        return False
    t = item["type"]
    sub = item.get("sub")
    if t == "weapon":
        return sub in class_def["weapons"]
    if t in ("armor", "jewelry"):
        slot = item["slot"]
        if slot == "off_hand":
            return sub in class_def["offhand"] or (class_def.get("dual_wield") and sub in class_def["weapons"])
        if slot == "class":
            return sub == class_def.get("class_slot")
        if sub in ("schmuck", "umhang"):
            return True
        return sub in class_def["armor"]
    return False


def is_equippable(item: dict) -> bool:
    return item["type"] in ("weapon", "armor", "jewelry")


def item_client_info(item_id: str) -> dict:
    it = ITEMS[item_id]
    return {k: v for k, v in it.items() if k not in ("gen",)}
