"""Samurai – Präzision / Konter. Ressource: Fokus (durch Treffer und Paraden)."""
from ._base import *  # noqa: F401,F403

C = "samurai"

FLUSS = AURA("klingenfluss", "Klingenfluss", 6, stacks=3, pct={"iaido": 15})

ABILITIES = [
    ab("klingenschnitt", "Klingenschnitt", C, 1, "katana", slot=1,
       effects=[W(1.0, (4, 1.5)), GAIN((15, 0)), A(FLUSS, on="self")],
       desc="Schneller Schnitt: Waffenschaden plus {bonus}. Erzeugt 15 Fokus und einen Klingenfluss (bis 3)."),
    ab("iaido", "Iaido-Schlag", C, 1, "sword-brandish", cost=40, slot=2,
       effects=[W(1.6, (10, 3)), {"t": "consume_aura", "aura": "klingenfluss"}],
       desc="Blitzschneller Ziehschlag: 160 % Waffenschaden plus {bonus}. +15 % pro Klingenfluss (wird verbraucht)."),
    ab("paradehaltung", "Paradehaltung", C, 4, "sword-clash", cd=15, rng=0, target="self", off_gcd=True, slot=3,
       effects=[A(AURA("paradehaltung", "Paradehaltung", 3, parry_all=True), on="self")],
       desc="Timing! Pariert 3 Sek. lang jeden Nahkampfangriff von vorn. Jede Parade erzeugt 20 Fokus."),
    ab("gegenschlag", "Gegenschlag", C, 6, "sword-slice", cost=10, cd=3, slot=4, req={"after": ["parry"]},
       effects=[W(2.0, (15, 4))],
       desc="Nach einer Parade (5 Sek.): Vernichtender Gegenschlag mit 200 % Waffenschaden plus {bonus}."),
    ab("windschritt", "Windschritt", C, 8, "wind-slap", cd=12, rng=15, min_range=4, off_gcd=True, slot=5,
       effects=[CHARGE(0.0), GAIN((10, 0))],
       desc="Gleitet blitzschnell zum Ziel (bis 15 m) und erhält 10 Fokus."),
    ab("kiai", "Kiai", C, 10, "shouting", cost=15, cd=20, rng=0, target="self", slot=6,
       area=AREA("circle", 8, "self"), effects=[D("physical", (5, 2, 7, 2), coef=0.05, stat="ap"), INTERRUPT(3)],
       tags=["interrupt"], desc="Ein Kampfschrei, der alle Zauber im Umkreis von 8 m unterbricht und {dmg} Schaden verursacht."),
    ab("mondsichel", "Mondsichel", C, 12, "crescent-blade", cost=30, cd=6, slot=7,
       area=AREA("cone", 8, "self", 5, 120), effects=[W(0.9, (6, 2))],
       desc="Ein weiter Bogenschnitt: 90 % Waffenschaden an bis zu 5 Gegnern vor Euch."),
    ab("meditation", "Meditation", C, 14, "meditation", cd=60, cast=4.0, channel=True, ticks=4, rng=0, target="self", slot=8,
       effects=[H((0, 0, 0, 0), pct_max=0.08, on="self"), GAIN((8, 0))],
       desc="Kanalisiert 4 Sek. innere Ruhe: heilt 32 % Eurer Gesundheit und erzeugt Fokus."),
    ab("tausend_schnitte", "Tausend Schnitte", C, 18, "sword-array", cost=50, cd=15, cast=2.4, channel=True, ticks=6, slot=9,
       effects=[W(0.5, (3, 1))],
       desc="Ein Wirbel aus Schnitten: 6 Treffer mit je 50 % Waffenschaden über 2,4 Sek."),
    ab("sturmschnitt", "Sturmschnitt", C, 24, "spinning-blades", cost=40, cd=10, rng=0, target="self", slot=10,
       area=AREA("circle", 6, "self", 8), effects=[W(1.1, (5, 2))],
       desc="Dreht sich wie ein Sturm: 110 % Waffenschaden an allen Gegnern im Umkreis von 6 m."),
    ab("bushido", "Bushido", C, 30, "samurai-helmet", cd=120, rng=0, target="self", off_gcd=True, slot=11,
       effects=[A(AURA("bushido", "Bushido", 15, stats={"crit": (20, 0), "parry": (20, 0)}), on="self")],
       desc="Der Weg des Kriegers: +20 % kritische Treffer und +20 % Parieren für 15 Sek."),
    # ---------------------------------------------------------------- Talentfähigkeiten
    ab("shogun_schnitt", "Shogun-Schnitt", C, 10, "shining-sword", cost=50, cd=12, talent=True,
       effects=[W(2.4, (25, 7)), {"t": "consume_aura", "aura": "klingenfluss", "per_stack": 0.25}],
       desc="Klingenmeister: 240 % Waffenschaden plus {bonus}, +25 % pro Klingenfluss."),
    ab("spiegelklinge", "Spiegelklinge", C, 10, "mirror-mirror", cd=30, rng=0, target="self", off_gcd=True, talent=True,
       effects=[A(AURA("spiegelklinge", "Spiegelklinge", 5, reflect_melee=1.0, charges=1), on="self")],
       desc="Konter: Der nächste Nahkampfangriff innerhalb von 5 Sek. wird vollständig auf den Angreifer zurückgeworfen."),
    ab("taifun", "Taifun", C, 10, "tornado", cost=50, cd=20, rng=0, target="self", talent=True,
       area=AREA("circle", 9, "self", 10), effects=[W(1.5, (10, 3)), CC("stun", 1.5)],
       desc="Sturm: Ein Wirbelsturm aus Stahl: 150 % Waffenschaden und 1,5 Sek. Betäubung im Umkreis von 9 m."),
]
