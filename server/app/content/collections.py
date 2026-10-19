"""Sammlungen (GDD 5 und 7): Reittiere, Haustiere, Titel und kosmetische Ausrüstungsskins.

Diese Belohnungen geben keine Kampfwerte – sie sind langfristige Ziele für Sammler.
"""
from . import items as I

# ----------------------------------------------------------------------------- Reittiere
# speed: Faktor auf die Laufgeschwindigkeit. lvl: Mindeststufe. model: Client-Modell
MOUNTS = {
    "pferd_braun": {"name": "Braunes Reitpferd", "model": "horse", "look": {"tint": "#6a4428", "mane": "#2a1a10"}, "speed": 1.6, "lvl": 10},
    "pferd_schimmel": {"name": "Weißer Schimmel", "model": "horse", "look": {"tint": "#e8e4dc", "mane": "#c8c0b0"}, "speed": 1.6, "lvl": 10},
    "pony": {"name": "Gescheckes Pony", "model": "horse", "look": {"tint": "#c89a68", "mane": "#f0e8d8", "scale": 0.8}, "speed": 1.6, "lvl": 10},
    "schlachtross": {"name": "Schlachtross von Eldenstein", "model": "horse",
                     "look": {"tint": "#3a3a40", "mane": "#1a1a1a", "barding": "#8f1d2c", "armor": True}, "speed": 2.0, "lvl": 30},
    "frostwolf": {"name": "Frostwolf", "model": "wolf_mount", "look": {"tint": "#d8e0ea", "tint2": "#8a98a8"}, "speed": 1.6, "lvl": 15},
    "zwergenwidder": {"name": "Zwergischer Bergwidder", "model": "ram", "look": {"tint": "#8a7a68", "horn": "#d8c8a8"}, "speed": 2.0, "lvl": 30},
    "mondhirsch": {"name": "Mondhirsch", "model": "stag", "look": {"tint": "#d0d8ff", "glow": "#a0c0ff"}, "speed": 2.0, "lvl": 30},
    "feenmotte": {"name": "Leuchtende Feenmotte", "model": "moth", "look": {"tint": "#e0a0ff", "glow": "#ffd0ff"}, "speed": 2.0, "lvl": 35},
    "aschenwolf": {"name": "Glutpelzwolf", "model": "wolf_mount", "look": {"tint": "#3a2a26", "tint2": "#ff6a1a", "glow": "#ff8a3a"}, "speed": 2.0, "lvl": 40},
    "aschenwyrm": {"name": "Zügel des Aschenwyrms", "model": "drake", "look": {"tint": "#3a2a2a", "tint2": "#ff6a1a", "glow": "#ff6a1a"}, "speed": 2.0, "lvl": 40, "rare": True},
    "himmelsgreif": {"name": "Himmelsgreif", "model": "gryphon", "look": {"tint": "#f0f4ff", "tint2": "#e0c070"}, "speed": 2.0, "lvl": 45},
    "weltenbrecher_ross": {"name": "Seelenross des Weltenbrechers", "model": "horse",
                           "look": {"tint": "#2a3a6a", "mane": "#2ee6d6", "glow": "#2ee6d6", "armor": True, "barding": "#e0c070"},
                           "speed": 2.0, "lvl": 50, "rare": True},
}

# ----------------------------------------------------------------------------- Haustiere (folgen dem Spieler)
PETS = {
    "gackerkueken": {"name": "Gackerküken", "model": "chicken", "look": {"tint": "#f8e060", "scale": 0.6}},
    "waldwelpe": {"name": "Waldwelpe", "model": "wolf", "look": {"tint": "#8a7a6a", "scale": 0.45}},
    "kerzenkobold": {"name": "Kleiner Kerzenkobold", "model": "humanoid", "look": {"kind": "kobold", "skin": "#9c6b3c", "top": "#c9862f", "scale": 0.45, "hat": "mining"}},
    "schneehase": {"name": "Schneehase", "model": "rabbit", "look": {"tint": "#f4f6fa"}},
    "irrlicht": {"name": "Irrlicht", "model": "wisp", "look": {"tint": "#a0ffd0"}},
    "glutsalamander": {"name": "Glutsalamander", "model": "lizard", "look": {"tint": "#3a2a2a", "glow": "#ff6a1a", "scale": 0.5}},
    "sternenfuchs": {"name": "Sternenfuchs", "model": "fox", "look": {"tint": "#3a4a8a", "glow": "#c0d8ff"}},
    "drachenwelpe": {"name": "Aschendrachenwelpe", "model": "drake", "look": {"tint": "#3a2a2a", "tint2": "#ff6a1a", "scale": 0.3}},
}

# ----------------------------------------------------------------------------- Titel
TITLES = {
    "held_eldornias": "Held Eldornias",
    "freund_des_trottels": "Freund des Dorftrottels",
    "wolfsjaeger": "Wolfsjäger",
    "kryptenwaechter": "Kryptenwächter",
    "schmiedebezwinger": "Bezwinger der Schwarzen Schmiede",
    "erloeser": "Erlöser der Verdammten",
    "drachentoeter": "Drachentöter",
    "weltenbrecher": "Weltenbrecher",
    "meister_der_berufe": "Meister der Berufe",
    "entdecker": "Entdecker",
    "sammler": "Sammler",
    "gladiator": "Gladiator",
    "duellant": "Duellant",
    "kopfgeldjaeger": "Kopfgeldjäger",
    "der_reiche": "der Reiche",
    "ritter_der_krone": "Ritter der Krone",
    "freund_der_zwerge": "Freund der Zwerge",
    "huter_des_hains": "Hüter des Hains",
    "aschenwacht": "der Aschenwacht",
    "himmelswanderer": "Himmelswanderer",
    # Klassenquest-Titel
    "schildtraeger": "Schildträger", "flammenweber": "Flammenweber", "schattenhand": "Schattenhand",
    "klingenweiser": "Klingenweiser", "falkenauge": "Falkenauge", "zornesfaust": "Zornesfaust",
    "waldhueter": "Waldhüter", "knochenfuerst": "Knochenfürst",
}

# ----------------------------------------------------------------------------- Kosmetische Skins (Transmogrifikation)
# Ein Skin ersetzt das Aussehen eines Slots, ohne die Werte zu ändern.
SKINS = {
    "wappenrock_eldenstein": {"name": "Wappenrock von Eldenstein", "slot": "chest", "vis": {"c": "#8f1d2c", "a": "#e0b648", "tabard": "#8f1d2c"}},
    "narrenkappe": {"name": "Narrenkappe", "slot": "head", "vis": {"c": "#d43c8f", "hat": "jester"}},
    "zwergenhelm_skin": {"name": "Gehörnter Zwergenhelm", "slot": "head", "vis": {"m": "#a8acb6", "horns": True}},
    "mondmantel": {"name": "Mantel des Mondzirkels", "slot": "back", "vis": {"c": "#3a3a8a", "g": "#a0c0ff"}},
    "aschenschultern_skin": {"name": "Glühende Aschenschultern", "slot": "shoulders", "vis": {"m": "#3a3436", "g": "#ff6a1a"}},
    "himmelsrobe": {"name": "Gewand der Himmelswächter", "slot": "chest", "vis": {"c": "#f0f4ff", "a": "#e0c070", "g": "#c0e0ff"}},
    # Klassenquest-Skins
    "skin_ritter": {"name": "Löwenwappen des Schildträgers", "slot": "chest", "vis": {"c": "#2d4f9a", "m": "#d8dce6", "a": "#e0b648"}},
    "skin_magier": {"name": "Robe des Flammenwebers", "slot": "chest", "vis": {"c": "#8a2a1a", "a": "#ffb040", "g": "#ff7a1a"}},
    "skin_raeuber": {"name": "Kapuze der Schattenhand", "slot": "head", "vis": {"c": "#1a1a22", "g": "#8a5ad0"}},
    "skin_samurai": {"name": "Kabuto des Klingenweisen", "slot": "head", "vis": {"m": "#2a2a2a", "c": "#8a1a1a", "a": "#e0b648"}},
    "skin_bogenschuetze": {"name": "Federumhang des Falkenauges", "slot": "back", "vis": {"c": "#5a6a2a", "a": "#e0d8c0"}},
    "skin_barbar": {"name": "Schädelschultern der Zornesfaust", "slot": "shoulders", "vis": {"m": "#e6dcc0", "c": "#5a3a2a"}},
    "skin_druide": {"name": "Geweihkrone des Waldhüters", "slot": "head", "vis": {"c": "#5a7a3a", "antlers": True}},
    "skin_totenbeschwoerer": {"name": "Knochenkrone des Knochenfürsten", "slot": "head", "vis": {"c": "#e6dcc0", "g": "#7affc8"}},
}

# ----------------------------------------------------------------------------- Gegenstände dazu
_MOUNT_ICONS = {"horse": "horse-head", "wolf_mount": "wolf-head", "ram": "ram", "stag": "deer", "moth": "moth",
                "drake": "dragon-head", "gryphon": "griffin-symbol"}
_MOUNT_PRICE = {1.6: 40000, 2.0: 400000}


def _mount_item(mid: str, q: int = 3, buy: int | None = None, bind="bop", desc=""):
    m = MOUNTS[mid]
    return I.CONS(f"reittier_{mid}", m["name"], q, _MOUNT_ICONS.get(m["model"], "horse-head"),
                  {"type": "learn_mount", "mount": mid},
                  desc or f"Benutzen: Lehrt Euch das Reittier {m['name']}. (Stufe {m['lvl']}, "
                          f"{int((m['speed'] - 1) * 100)} % schneller)",
                  0, buy if buy is not None else _MOUNT_PRICE[m["speed"]], stack=1, lvl=m["lvl"], bind=bind)


for _mid in ("pferd_braun", "pferd_schimmel", "pony"):
    _mount_item(_mid, 3)
_mount_item("schlachtross", 4, 600000)
_mount_item("frostwolf", 3, 60000)
_mount_item("zwergenwidder", 4, 500000)
_mount_item("mondhirsch", 4, 500000)
_mount_item("feenmotte", 4, 0, desc="Benutzen: Lehrt Euch die Leuchtende Feenmotte. Belohnung des Mondzirkels.")
_mount_item("aschenwolf", 4, 700000)
_mount_item("aschenwyrm", 4, 0, desc="Benutzen: Lehrt Euch den Aschenwyrm. Sehr selten von Varkor.")
_mount_item("himmelsgreif", 4, 900000)
_mount_item("weltenbrecher_ross", 6, 0, desc="Benutzen: Lehrt Euch das Seelenross des Weltenbrechers.")

for _pid, _p in PETS.items():
    I.CONS(f"haustier_{_pid}", _p["name"], 2 if _pid not in ("drachenwelpe", "sternenfuchs") else 3, "paw",
           {"type": "learn_pet", "pet": _pid}, f"Benutzen: Fügt {_p['name']} Eurer Haustiersammlung hinzu.",
           0, 2500, stack=1, bind=None)

for _sid, _s in SKINS.items():
    I.CONS(_sid, _s["name"], 3, {"chest": "chest-armor", "head": "pointy-hat", "back": "cape",
                                 "shoulders": "shoulder-armor"}.get(_s["slot"], "chest-armor"),
           {"type": "learn_skin", "skin": _sid},
           f"Benutzen: Schaltet das Aussehen \"{_s['name']}\" für den Slot {I.SLOT_NAMES[_s['slot']]} frei (Transmogrifikation).",
           0, 0, stack=1, bind="bop")
