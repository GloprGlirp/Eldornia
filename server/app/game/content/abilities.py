"""Spielerfähigkeiten (Aktionsleiste 1–7) – Kampfsystem im Stil von World of Warcraft.

Zahlenwerte skalieren mit der Charakterstufe L:
  dmg  = [min_basis, min_pro_stufe, max_basis, max_pro_stufe]
  cost = [basis, pro_stufe]

Felder:
  power   Ressource (rage = Wut, mana = Mana)
  cast    Zauberzeit in Sekunden (0 = sofort). Bewegung unterbricht das Wirken.
  channel Kanalisiert (Schaden in Ticks über die Zauberzeit)
  cd      Abklingzeit in Sekunden
  gcd     Löst die globale Abklingzeit (1,5 Sek.) aus
  range   "melee" oder Meter
  target  enemy | self | self_aoe | party
"""

GCD = 1.5  # globale Abklingzeit in Sekunden

ABILITIES = {
    # ------------------------------------------------------------------ Ritter
    "wuchtschlag": {
        "name": "Wuchtschlag", "cls": "ritter", "level": 1, "slot": 1,
        "cost": [15, 0], "power": "rage", "cast": 0, "cd": 0, "gcd": True,
        "range": "melee", "target": "enemy", "school": "physical",
        "weapon": True, "bonus": [11, 3], "threat": 20,
        "icon": "sword", "color": "#d9a441",
        "desc": "Ein wuchtiger Schlag, der Waffenschaden plus {bonus} verursacht und zusätzliche Bedrohung erzeugt.",
    },
    "ansturm": {
        "name": "Ansturm", "cls": "ritter", "level": 1, "slot": 2,
        "cost": [0, 0], "power": "rage", "cast": 0, "cd": 15, "gcd": False,
        "range": 25, "min_range": 8, "target": "enemy", "school": "physical",
        "rage_gain": [12, 1], "stun": 1.0, "charge": True, "no_combat": True,
        "icon": "charge", "color": "#c0583b",
        "desc": "Stürmt auf einen Gegner zu, betäubt ihn für 1 Sek. und erzeugt {rage} Wut. Nur außerhalb des Kampfes.",
    },
    "herausforderung": {
        "name": "Herausforderung", "cls": "ritter", "level": 2, "slot": 3,
        "cost": [0, 0], "power": "rage", "cast": 0, "cd": 8, "gcd": True,
        "range": 20, "target": "enemy", "school": "physical", "taunt": 3,
        "icon": "taunt", "color": "#b33a3a",
        "desc": "Fordert das Ziel heraus und zwingt es 3 Sek. lang, Euch anzugreifen. Ihr erhaltet so viel Bedrohung wie der Spitzenreiter.",
    },
    "schlachtruf": {
        "name": "Schlachtruf", "cls": "ritter", "level": 3, "slot": 7,
        "cost": [10, 0], "power": "rage", "cast": 0, "cd": 0, "gcd": True,
        "range": 0, "radius": 30, "target": "party", "school": "physical",
        "buff": {"id": "schlachtruf", "name": "Schlachtruf", "dur": 120, "stats": {"ap": [15, 4]}},
        "icon": "horn", "color": "#e0b040",
        "desc": "Ein mitreißender Ruf, der die Angriffskraft aller Gruppenmitglieder im Umkreis von 30 m 2 Min. lang um {ap} erhöht.",
    },
    "bebenhieb": {
        "name": "Bebenhieb", "cls": "ritter", "level": 4, "slot": 4,
        "cost": [20, 0], "power": "rage", "cast": 0, "cd": 6, "gcd": True,
        "range": 0, "radius": 8, "target": "self_aoe", "school": "physical",
        "dmg": [8, 3, 10, 3], "slow": 0.3, "duration": 10, "threat_mult": 1.75,
        "icon": "thunder", "color": "#7d8fd1",
        "desc": "Erschüttert den Boden: {dmg} Schaden an allen Gegnern im Umkreis von 8 m und verlangsamt sie 10 Sek. lang um 30 %.",
    },
    "schildstoss": {
        "name": "Schildstoß", "cls": "ritter", "level": 6, "slot": 5,
        "cost": [10, 0], "power": "rage", "cast": 0, "cd": 12, "gcd": True,
        "range": "melee", "target": "enemy", "school": "physical",
        "dmg": [5, 2, 7, 2], "interrupt": 4, "needs_shield": True,
        "icon": "shield", "color": "#8a8f99",
        "desc": "Stößt mit dem Schild zu: {dmg} Schaden und unterbricht das Wirken eines Zaubers. Erfordert einen Schild.",
    },
    "gnadenstoss": {
        "name": "Gnadenstoß", "cls": "ritter", "level": 8, "slot": 6,
        "cost": [15, 0], "power": "rage", "cast": 0, "cd": 0, "gcd": True,
        "range": "melee", "target": "enemy", "school": "physical",
        "dmg": [60, 5, 70, 5], "execute": 0.2, "rage_mult": 3,
        "icon": "skull", "color": "#7a1f1f",
        "desc": "Erlöst einen geschwächten Gegner: {dmg} Schaden plus 3 pro übriger Wut. Nur bei Zielen unter 20 % Gesundheit.",
    },
    # ------------------------------------------------------------------ Magier
    "feuerball": {
        "name": "Feuerball", "cls": "magier", "level": 1, "slot": 1,
        "cost": [20, 5], "power": "mana", "cast": 2.5, "cd": 0, "gcd": True,
        "range": 35, "target": "enemy", "school": "fire",
        "dmg": [12, 5, 18, 7], "coef": 0.714, "dot": [2, 1], "dot_dur": 4, "projectile": 22,
        "icon": "fireball", "color": "#ff7a1a",
        "desc": "Schleudert einen feurigen Ball auf den Gegner: {dmg} Feuerschaden und weitere {dot} Schaden über 4 Sek.",
    },
    "frostpanzer": {
        "name": "Frostpanzer", "cls": "magier", "level": 1, "slot": 7,
        "cost": [30, 4], "power": "mana", "cast": 0, "cd": 0, "gcd": True,
        "range": 0, "target": "self", "school": "frost",
        "buff": {"id": "frostpanzer", "name": "Frostpanzer", "dur": 1800,
                 "stats": {"armor": [30, 12]}, "chill_attackers": True},
        "icon": "frostarmor", "color": "#9fd8ff",
        "desc": "Hüllt Euch in Eis: Rüstung um {armor} erhöht. Nahkampfangreifer werden 5 Sek. lang verlangsamt. Hält 30 Min.",
    },
    "frostpfeil": {
        "name": "Frostpfeil", "cls": "magier", "level": 2, "slot": 2,
        "cost": [18, 4], "power": "mana", "cast": 2.0, "cd": 0, "gcd": True,
        "range": 30, "target": "enemy", "school": "frost",
        "dmg": [9, 4, 13, 5], "coef": 0.57, "slow": 0.4, "duration": 5, "projectile": 26,
        "icon": "frost", "color": "#7fd0ff",
        "desc": "Ein eisiger Pfeil: {dmg} Frostschaden und verlangsamt das Ziel 5 Sek. lang um 40 %.",
    },
    "flammenstoss": {
        "name": "Flammenstoß", "cls": "magier", "level": 3, "slot": 3,
        "cost": [20, 4], "power": "mana", "cast": 0, "cd": 8, "gcd": True,
        "range": 20, "target": "enemy", "school": "fire",
        "dmg": [11, 4, 15, 5], "coef": 0.43,
        "icon": "fireblast", "color": "#ff4d1a",
        "desc": "Sofortiger Flammenstoß: {dmg} Feuerschaden.",
    },
    "eisring": {
        "name": "Eisring", "cls": "magier", "level": 4, "slot": 4,
        "cost": [25, 3], "power": "mana", "cast": 0, "cd": 20, "gcd": True,
        "range": 0, "radius": 10, "target": "self_aoe", "school": "frost",
        "dmg": [4, 1, 6, 1], "coef": 0.1, "root": 6,
        "icon": "nova", "color": "#a8e6ff",
        "desc": "Eisige Explosion: {dmg} Frostschaden an Gegnern im Umkreis von 10 m, die 6 Sek. lang festgefroren werden.",
    },
    "phasensprung": {
        "name": "Phasensprung", "cls": "magier", "level": 6, "slot": 5,
        "cost": [20, 3], "power": "mana", "cast": 0, "cd": 15, "gcd": True,
        "range": 0, "target": "self", "school": "arcane", "blink": 15,
        "icon": "blink", "color": "#c27dff",
        "desc": "Springt durch die Arkanebene 15 m nach vorn und befreit Euch von Betäubungen und Bewegungsunfähigkeit.",
    },
    "arkansalve": {
        "name": "Arkansalve", "cls": "magier", "level": 8, "slot": 6,
        "cost": [40, 5], "power": "mana", "cast": 3.0, "channel": True, "ticks": 3, "cd": 0, "gcd": True,
        "range": 30, "target": "enemy", "school": "arcane",
        "dmg": [8, 3, 10, 4], "coef": 0.24, "projectile": 30,
        "icon": "missiles", "color": "#d58cff",
        "desc": "Kanalisiert 3 arkane Geschosse über 3 Sek., die jeweils {dmg} Arkanschaden verursachen.",
    },
}

for _id, _ab in ABILITIES.items():
    _ab["id"] = _id


def scaled_range(spec, level: int) -> tuple[int, int]:
    return spec[0] + spec[1] * level, spec[2] + spec[3] * level


def scaled(pair, level: int) -> int:
    return pair[0] + pair[1] * level


def ability_cost(ab: dict, level: int) -> int:
    return scaled(ab["cost"], level)


def describe(ab_id: str, level: int) -> str:
    ab = ABILITIES[ab_id]
    text = ab["desc"]
    if "dmg" in ab:
        lo, hi = scaled_range(ab["dmg"], level)
        text = text.replace("{dmg}", f"{lo}–{hi}")
    if "bonus" in ab:
        text = text.replace("{bonus}", str(scaled(ab["bonus"], level)))
    if "rage_gain" in ab:
        text = text.replace("{rage}", str(scaled(ab["rage_gain"], level)))
    if "dot" in ab:
        text = text.replace("{dot}", str(scaled(ab["dot"], level) * 2))
    if "buff" in ab:
        for stat, pair in ab["buff"].get("stats", {}).items():
            text = text.replace("{" + stat + "}", str(scaled(pair, level)))
    return text


def class_abilities(class_id: str):
    return sorted((a for a, d in ABILITIES.items() if d["cls"] == class_id), key=lambda a: ABILITIES[a]["slot"])


def ability_range(ab: dict) -> float:
    rng = ab["range"]
    return 5.0 if rng == "melee" else float(rng)


def ability_client_info(ab_id: str, level: int) -> dict:
    ab = ABILITIES[ab_id]
    return {
        "id": ab_id,
        "name": ab["name"],
        "slot": ab["slot"],
        "level": ab["level"],
        "cost": ability_cost(ab, level),
        "power": ab["power"],
        "cast": ab.get("cast", 0),
        "channel": ab.get("channel", False),
        "cd": ab.get("cd", 0),
        "gcd": ab.get("gcd", True),
        "range": ability_range(ab),
        "min_range": ab.get("min_range", 0),
        "melee": ab["range"] == "melee",
        "target": ab["target"],
        "icon": ab["icon"],
        "color": ab["color"],
        "school": ab["school"],
        "desc": describe(ab_id, level),
    }
