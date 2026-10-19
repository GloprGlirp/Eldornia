"""Rufsystem (GDD 7): Fraktionen bieten Quests, Rezepte und kosmetische Gegenstände.

Ruf steigt durch Quests, tägliche Aufträge und das Besiegen bestimmter Gegner.
Fraktionsmünzen (Währung "muenzen_<fraktion>") gibt es für tägliche Aufträge der Fraktion.
"""

STANDINGS = [
    # (Name, ab Ruf)
    ("Feindselig", -3000),
    ("Unfreundlich", -1),
    ("Neutral", 0),
    ("Freundlich", 3000),
    ("Wohlwollend", 9000),
    ("Respektvoll", 21000),
    ("Ehrfürchtig", 42000),
]
REP_MAX = 42999

FACTIONS = {
    "krone": {"name": "Krone von Eldenstein", "zone": "gruenmark", "icon": "crown",
              "desc": "Simon, der zweiäugige Herrscher, und seine treuen Diener auf Burg Eldenstein."},
    "eisenbart": {"name": "Eisenbart-Klan", "zone": "frostklamm", "icon": "dwarf-face",
                  "desc": "Die Zwerge der Frostklamm verteidigen ihre Festungen gegen Eisriesen."},
    "mondzirkel": {"name": "Zirkel des Mondes", "zone": "mondhain", "icon": "moon",
                   "desc": "Druiden und Feen, die die magischen Wälder des Mondhains hüten."},
    "aschenwacht": {"name": "Die Aschenwacht", "zone": "aschenlande", "icon": "fire-shield",
                    "desc": "Ein Orden von Kriegern, der die Dämonen der Aschenlande in Schach hält."},
    "himmelswaechter": {"name": "Wächter des Himmelsbruchs", "zone": "himmelsbruch", "icon": "angel-wings",
                        "desc": "Die letzten Hüter der uralten Tempel auf den schwebenden Inseln."},
}

CURRENCIES = {
    "dungeonmarken": {"name": "Dungeonmarken", "icon": "rune-stone", "desc": "Belohnung für Dungeonbosse. Bei Rüstmeistern eintauschbar."},
    "eventmarken": {"name": "Eventmarken", "icon": "party-popper", "desc": "Zeitlich begrenzte Belohnungen saisonaler Feste."},
    "arenapunkte": {"name": "Arenapunkte", "icon": "crossed-swords", "desc": "Belohnung aus Arenakämpfen."},
    "ehrenabzeichen": {"name": "Ehrenabzeichen", "icon": "medal", "desc": "Für Siege im offenen PvP-Gebiet."},
}
for _fid, _f in FACTIONS.items():
    CURRENCIES["muenzen_" + _fid] = {"name": f"Münzen: {_f['name']}", "icon": "two-coins",
                                     "desc": f"Fraktionswährung der {_f['name']}."}


def standing(rep: int) -> int:
    """Index in STANDINGS für einen Rufwert."""
    idx = 0
    for i, (_, lo) in enumerate(STANDINGS):
        if rep >= lo:
            idx = i
    return idx


def standing_name(rep: int) -> str:
    return STANDINGS[standing(rep)][0]


def standing_bounds(rep: int) -> tuple[int, int]:
    i = standing(rep)
    lo = STANDINGS[i][1]
    hi = STANDINGS[i + 1][1] if i + 1 < len(STANDINGS) else REP_MAX + 1
    return lo, hi


def required_standing(name: str) -> int:
    for i, (n, _) in enumerate(STANDINGS):
        if n == name:
            return i
    return 2
