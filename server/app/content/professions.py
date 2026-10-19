"""Berufe und Sammelsystem (GDD 8) – Fortschritt im Stil von RuneScape mit WoW-Rezeptfarben.

Sechs Berufe, alle gleichzeitig erlernbar:
  Sammeln:     Bergbau, Kräuterkunde
  Herstellen:  Schmiedekunst, Alchemie, Lederverarbeitung, Verzauberung

Jeder Beruf hat Fertigkeitspunkte (1–300) und vier Ränge, die bei Lehrern freigeschaltet werden.
Rezeptfarben: orange (sicherer Punkt), gelb (75 %), grün (25 %), grau (kein Punkt).
Rezepte stammen von Lehrern, aus Bossbeute ("Bauplan"/"Rezept") oder von Fraktionshändlern.
"""
from __future__ import annotations

from . import items as I
from .enchants import ENCHANTS

MAX_SKILL = 300

PROFESSIONS = {
    "bergbau": {"name": "Bergbau", "icon": "mining", "kind": "gather",
                "desc": "Kupfer, Eisen, Mithril und seltene magische Erze abbauen."},
    "kraeuterkunde": {"name": "Kräuterkunde", "icon": "herbs-bundle", "kind": "gather",
                      "desc": "Pflanzen und seltene Pilze sammeln – für Tränke und Verzauberungen."},
    "schmiedekunst": {"name": "Schmiedekunst", "icon": "anvil-impact", "kind": "craft",
                      "desc": "Erze zu Barren verarbeiten und Waffen, Plattenrüstungen oder Verbesserungsmaterialien herstellen."},
    "alchemie": {"name": "Alchemie", "icon": "round-bottom-flask", "kind": "craft",
                 "desc": "Tränke, Gifte, Heilmittel und zeitlich begrenzte Kampfverstärkungen brauen."},
    "lederverarbeitung": {"name": "Lederverarbeitung", "icon": "leather-vest", "kind": "craft",
                          "desc": "Leder und Monsterhäute zu leichter Rüstung, Taschen und Fernkampfausrüstung verarbeiten."},
    "verzauberung": {"name": "Verzauberung", "icon": "magic-swirl", "kind": "craft",
                     "desc": "Waffen und Rüstungen mit Runen und magischen Effekten verbessern."},
}

# (Name, maximale Fertigkeit, Mindeststufe des Charakters, Kosten in Kupfer)
RANKS = [
    ("Lehrling", 75, 5, 100),
    ("Geselle", 150, 10, 500),
    ("Experte", 225, 20, 5000),
    ("Fachmann", 300, 35, 50000),
]


def rank_index(max_skill: int) -> int:
    for i, r in enumerate(RANKS):
        if max_skill <= r[1]:
            return i
    return len(RANKS) - 1


def skill_color(skill: int, req: int) -> str:
    if skill < req:
        return "red"
    if skill < req + 25:
        return "orange"
    if skill < req + 50:
        return "yellow"
    if skill < req + 75:
        return "green"
    return "grey"


SKILLUP_CHANCE = {"orange": 1.0, "yellow": 0.75, "green": 0.25, "grey": 0.0, "red": 0.0}

# ============================================================================ Zusätzliche Materialien
I.MAT("spinnenseide", "Spinnenseide", 1, "spider-web", 6, "Lederverarbeitung und Alchemie. Von Waldspinnen.")
I.MAT("geisteressenz", "Ruhelose Geisteressenz", 1, "spectre", 18, "Verzauberung. Schimmert bläulich.")
I.MAT("leuchtpilz", "Leuchtpilz", 1, "mushroom-gills", 60, "Kräuterkunde (100). Seltener Pilz aus dem Mondhain.", prof="kraeuter")
I.MAT("aschenmorchel", "Aschenmorchel", 2, "mushrooms", 140, "Kräuterkunde (200). Wächst nur auf warmer Asche.", prof="kraeuter")
I.MAT("mondstein", "Mondstein", 2, "moon-orbit", 220, "Seltener Edelstein aus Mithrilvorkommen.")
I.MAT("feuerrubin", "Feuerrubin", 3, "gem-chain", 650, "Seltener Edelstein aus Glutsteinvorkommen.")
I.MAT("sternensaphir", "Sternensaphir", 3, "crystal-shine", 1100, "Seltener Edelstein aus Sternenerz.")
I.MAT("frostsplitter", "Frostsplitter", 1, "ice-spell-cast", 40, "Verzauberung. Von Frostwesen.")

# Taschen (vergrößern das Inventar)
BAGS = {"leinensack": 6, "lederbeutel": 8, "wildledertasche": 10, "baerenledertasche": 12, "frostledertasche": 14,
        "drachenledertasche": 16}
I._reg({"id": "leinensack", "name": "Leinensack", "q": 1, "type": "bag", "slots": 6, "icon": "knapsack", "sell": 25, "buy": 100,
        "desc": "Eine Tasche mit 6 Plätzen."})
I._reg({"id": "lederbeutel", "name": "Lederbeutel", "q": 1, "type": "bag", "slots": 8, "icon": "swap-bag", "sell": 120,
        "desc": "Eine Tasche mit 8 Plätzen."})
I._reg({"id": "wildledertasche", "name": "Wildledertasche", "q": 2, "type": "bag", "slots": 10, "icon": "swap-bag", "sell": 600,
        "desc": "Eine Tasche mit 10 Plätzen."})
I._reg({"id": "baerenledertasche", "name": "Bärenledertasche", "q": 2, "type": "bag", "slots": 12, "icon": "swap-bag", "sell": 2500,
        "desc": "Eine Tasche mit 12 Plätzen."})
I._reg({"id": "frostledertasche", "name": "Frostledertasche", "q": 3, "type": "bag", "slots": 14, "icon": "swap-bag", "sell": 9000,
        "desc": "Eine Tasche mit 14 Plätzen."})
I._reg({"id": "drachenledertasche", "name": "Drachenledertasche", "q": 4, "type": "bag", "slots": 16, "icon": "swap-bag", "sell": 30000,
        "desc": "Eine Tasche mit 16 Plätzen."})
I._reg({"id": "abgenutzter_rucksack", "name": "Abgenutzter Rucksack", "q": 1, "type": "bag", "slots": 8, "icon": "backpack",
        "sell": 5, "bind": "bop", "desc": "Eine Tasche mit 8 Plätzen. Jeder Abenteurer beginnt mit einem."})

# Heilmittel und Wetzsteine
I.CONS("gegengift", "Gegengift", 1, "potion-ball", {"type": "cure", "kinds": ["poison"], "cd": 10},
       "Benutzen: Entfernt einen Gifteffekt.", 8, 40, stack=10, lvl=5)
I.CONS("fluchbann", "Fluchbann-Tinktur", 2, "potion-ball", {"type": "cure", "kinds": ["curse", "disease"], "cd": 10},
       "Benutzen: Entfernt einen Fluch oder eine Krankheit.", 40, stack=10, lvl=25)
I.CONS("grober_wetzstein", "Grober Wetzstein", 1, "stone-wheel", {"type": "elixir", "aura": "wetzstein", "stats": {"ap": 12}, "dur": 1800},
       "Benutzen: Schärft Eure Waffe. Erhöht 30 Min. lang die Angriffskraft um 12.", 6, stack=20, lvl=5)
I.CONS("schwerer_wetzstein", "Schwerer Wetzstein", 1, "stone-wheel", {"type": "elixir", "aura": "wetzstein", "stats": {"ap": 30}, "dur": 1800},
       "Benutzen: Schärft Eure Waffe. Erhöht 30 Min. lang die Angriffskraft um 30.", 30, stack=20, lvl=20)
I.CONS("glutwetzstein", "Glutwetzstein", 2, "stone-wheel", {"type": "elixir", "aura": "wetzstein", "stats": {"ap": 60}, "dur": 1800},
       "Benutzen: Schärft Eure Waffe. Erhöht 30 Min. lang die Angriffskraft um 60.", 90, stack=20, lvl=40)
I.CONS("zauberoel", "Funkelndes Zauberöl", 1, "oil-drum", {"type": "elixir", "aura": "zauberoel", "stats": {"sp": 14}, "dur": 1800},
       "Benutzen: Erhöht 30 Min. lang die Zaubermacht um 14.", 20, stack=20, lvl=15)
I.CONS("sternenzauberoel", "Sternenzauberöl", 2, "oil-drum", {"type": "elixir", "aura": "zauberoel", "stats": {"sp": 40}, "dur": 1800},
       "Benutzen: Erhöht 30 Min. lang die Zaubermacht um 40.", 120, stack=20, lvl=40)

# Runenrollen der Verzauberer (handelbar → Marktplatz)
for _eid, _e in ENCHANTS.items():
    I.CONS("rolle_" + _eid, "Runenrolle: " + _e["name"], 2 if _e["skill"] < 200 else 3, "scroll-unfurled",
           {"type": "enchant", "enchant": _eid},
           f"Benutzen: Verzaubert einen angelegten Gegenstand ({', '.join(I.SLOT_NAMES[s] for s in _e['slots'])}) dauerhaft: "
           + ", ".join(f"+{v} {I.STAT_NAMES.get(k, k)}" for k, v in _e["stats"].items()) + ".",
           max(20, _e["skill"] * 3), stack=20, lvl=max(1, _e["skill"] // 7))

# ============================================================================ Sammelvorkommen
# skill: benötigte Fertigkeit, item: Ertrag (Anzahl lo..hi), extra: seltener Zusatzfund
NODES = {
    "kupfer": {"name": "Kupferader", "prof": "bergbau", "skill": 1, "item": "kupfererz", "n": (1, 3), "model": "ore_copper",
               "respawn": 90, "extra": [("rohquarz", 0.05)]},
    "eisen": {"name": "Eisenvorkommen", "prof": "bergbau", "skill": 60, "item": "eisenerz", "n": (1, 3), "model": "ore_iron",
              "respawn": 100, "extra": [("rohquarz", 0.06)]},
    "mithril": {"name": "Mithrilader", "prof": "bergbau", "skill": 120, "item": "mithrilerz", "n": (1, 3), "model": "ore_mithril",
                "respawn": 110, "extra": [("mondstein", 0.06)]},
    "glutstein": {"name": "Glutsteinvorkommen", "prof": "bergbau", "skill": 180, "item": "glutsteinerz", "n": (1, 3),
                  "model": "ore_glut", "respawn": 120, "extra": [("feuerrubin", 0.05)]},
    "sternen": {"name": "Sternenerzbrocken", "prof": "bergbau", "skill": 240, "item": "sternenerz", "n": (1, 2),
                "model": "ore_star", "respawn": 150, "extra": [("sternensaphir", 0.05)]},
    "friedblume": {"name": "Friedblume", "prof": "kraeuterkunde", "skill": 1, "item": "friedblume", "n": (1, 3), "model": "herb_peace",
                   "respawn": 60},
    "silberblatt": {"name": "Silberblatt", "prof": "kraeuterkunde", "skill": 1, "item": "silberblatt", "n": (1, 3),
                    "model": "herb_silver", "respawn": 60},
    "frostmoos": {"name": "Frostmoos", "prof": "kraeuterkunde", "skill": 60, "item": "frostmoos", "n": (1, 3), "model": "herb_frost",
                  "respawn": 70},
    "mondkraut": {"name": "Mondkraut", "prof": "kraeuterkunde", "skill": 120, "item": "mondkraut", "n": (1, 3), "model": "herb_moon",
                  "respawn": 80},
    "leuchtpilz": {"name": "Leuchtpilz", "prof": "kraeuterkunde", "skill": 100, "item": "leuchtpilz", "n": (1, 2),
                   "model": "herb_mushroom", "respawn": 120},
    "feuerbluete": {"name": "Feuerblüte", "prof": "kraeuterkunde", "skill": 180, "item": "feuerbluete", "n": (1, 3),
                    "model": "herb_fire", "respawn": 90},
    "aschenmorchel": {"name": "Aschenmorchel", "prof": "kraeuterkunde", "skill": 200, "item": "aschenmorchel", "n": (1, 2),
                      "model": "herb_ashshroom", "respawn": 140},
    "himmelsdistel": {"name": "Himmelsdistel", "prof": "kraeuterkunde", "skill": 240, "item": "himmelsdistel", "n": (1, 2),
                      "model": "herb_sky", "respawn": 120},
}
I.MAT("rohquarz", "Rohquarz", 2, "crystal-cluster", 45, "Ein ungeschliffener Kristall. Selten beim Bergbau.")

# ============================================================================ Rezepte
RECIPES: dict[str, dict] = {}


def R(rid, prof, skill, result, mats, n=1, station=None, source="trainer", cost=None, name=None, cast=3.0, kind="craft",
      enchant=None):
    """source: trainer | drop | faction:<id>:<Rufstufe>"""
    it = I.ITEMS.get(result) if result else None
    RECIPES[rid] = {
        "id": rid, "prof": prof, "skill": skill, "result": result, "n": n, "mats": list(mats), "station": station,
        "source": source, "cost": cost if cost is not None else max(10, skill * skill // 3),
        "name": name or (it["name"] if it else rid), "cast": cast, "kind": kind, "enchant": enchant,
    }
    return RECIPES[rid]


def recipe_item(rid: str, q: int = 2, lvl: int = 1, sell: int | None = None):
    rc = RECIPES[rid]
    kind = {"schmiedekunst": "Bauplan", "lederverarbeitung": "Muster", "alchemie": "Rezept", "verzauberung": "Formel"}[rc["prof"]]
    I.CONS("rezept_" + rid, f"{kind}: {rc['name']}", q, "scroll-quill", {"type": "learn_recipe", "recipe": rid},
           f"Benutzen: Lehrt Euch, {rc['name']} herzustellen. Benötigt {PROFESSIONS[rc['prof']]['name']} ({rc['skill']}).",
           sell if sell is not None else max(50, rc["skill"] * 20), stack=1, lvl=lvl)
    rc["source"] = rc["source"] if rc["source"] != "trainer" else "drop"


# ---------------------------------------------------------------- Schmiedekunst: Verhütten
R("verhuetten_kupfer", "schmiedekunst", 1, "kupferbarren", [("kupfererz", 1)], station="forge", cost=10, name="Kupfer verhütten", cast=2.0)
R("verhuetten_eisen", "schmiedekunst", 60, "eisenbarren", [("eisenerz", 1)], station="forge", name="Eisen verhütten", cast=2.0)
R("verhuetten_mithril", "schmiedekunst", 120, "mithrilbarren", [("mithrilerz", 2)], station="forge", name="Mithril verhütten", cast=2.0)
R("verhuetten_glutstahl", "schmiedekunst", 180, "glutstahlbarren", [("glutsteinerz", 2), ("schmiedekohle", 1)], station="forge",
  name="Glutstahl verhütten", cast=2.0)
R("verhuetten_sternenstahl", "schmiedekunst", 240, "sternenstahlbarren", [("sternenerz", 2), ("glutstahlbarren", 1)],
  station="forge", name="Sternenstahl verhütten", cast=2.0)
R("grober_wetzstein", "schmiedekunst", 10, "grober_wetzstein", [("kupferbarren", 1)], n=3, cost=50)
R("schwerer_wetzstein", "schmiedekunst", 110, "schwerer_wetzstein", [("eisenbarren", 1), ("schmiedekohle", 1)], n=3)
R("glutwetzstein", "schmiedekunst", 230, "glutwetzstein", [("glutstahlbarren", 1), ("feuerbluete", 1)], n=3)


def _bar_for_tier(tier: int) -> list[tuple]:
    if tier <= 2:
        return [("kupferbarren", 1)]
    if tier <= 5:
        return [("eisenbarren", 1)]
    if tier <= 8:
        return [("mithrilbarren", 1)]
    if tier <= 10:
        return [("glutstahlbarren", 1)]
    return [("sternenstahlbarren", 1)]


def _leather_for_tier(tier: int) -> str:
    return ["leichtes_leder", "leichtes_leder", "leichtes_leder", "mittleres_leder", "mittleres_leder", "mittleres_leder",
            "schweres_leder", "schweres_leder", "schweres_leder", "dickes_leder", "dickes_leder", "drachenhaut", "drachenhaut"][tier]


_SLOT_MATS = {"chest": 8, "legs": 7, "head": 6, "shoulders": 5, "hands": 4, "feet": 4}
_WEAPON_MATS = {"schwert": 6, "axt": 6, "streitkolben": 6, "dolch": 4, "katana": 8, "zweihandschwert": 10, "zweihandaxt": 10,
                "kriegshammer": 10}
_FLAVOR = {0: [], 3: [("rohquarz", 1)], 6: [("mondstein", 1)], 9: [("feuerrubin", 1)], 11: [("sternensaphir", 1)]}


def _flavor(tier: int) -> list:
    best = []
    for k, v in _FLAVOR.items():
        if tier >= k:
            best = v
    return best


def _skill_for_tier(tier: int) -> int:
    return max(1, min(290, tier * 24 + 5))


for _tier in range(13):
    sk = _skill_for_tier(_tier)
    bar = _bar_for_tier(_tier)[0][0]
    # Plattenrüstung (Bär) und Kettenrüstung (Tiger)
    for _slot, _n in _SLOT_MATS.items():
        rid = f"platte_{_slot}_{_tier}"
        R(rid, "schmiedekunst", sk + (5 if _slot in ("hands", "feet") else 0), f"g_platte_{_slot}_{_tier}_2_baer",
          [(bar, _n)] + ([("schmiedekohle", 1)] if _tier < 6 else _flavor(_tier)), station="anvil")
    for _slot in ("chest", "legs", "head", "hands"):
        R(f"kette_{_slot}_{_tier}", "schmiedekunst", sk + 3, f"g_kette_{_slot}_{_tier}_2_tiger",
          [(bar, _SLOT_MATS[_slot] - 1)] + _flavor(_tier), station="anvil")
    for _sub, _n in _WEAPON_MATS.items():
        theme = {"dolch": "affe", "katana": "tiger", "zweihandaxt": "tiger", "axt": "tiger"}.get(_sub, "baer")
        R(f"waffe_{_sub}_{_tier}", "schmiedekunst", sk + 8, f"g_{_sub}_{_tier}_2_{theme}",
          [(bar, _n), ("schmiedekohle", 1)] + _flavor(_tier) + ([("leichtes_leder", 1)] if _sub in ("dolch", "katana") else []),
          station="anvil")
    R(f"schild_{_tier}", "schmiedekunst", sk + 6, f"g_schild_{_tier}_2_waechter", [(bar, 8)] + _flavor(_tier), station="anvil")
    # Seltene Baupläne (blau) – aus Bossbeute und von Fraktionen
    if _tier >= 1:
        R(f"platte_chest_{_tier}_blau", "schmiedekunst", min(300, sk + 15), f"g_platte_chest_{_tier}_3_baer",
          [(bar, 12)] + _flavor(_tier) * 2 + [("glitzernde_essenz" if _tier < 8 else "strahlender_splitter", 1)], station="anvil",
          source="drop")
        recipe_item(f"platte_chest_{_tier}_blau", 3, max(1, I.BRACKETS[_tier] - 3))
        R(f"waffe_schwert_{_tier}_blau", "schmiedekunst", min(300, sk + 18), f"g_schwert_{_tier}_3_baer",
          [(bar, 10), ("schmiedekohle", 2)] + _flavor(_tier) * 2, station="anvil", source="drop")
        recipe_item(f"waffe_schwert_{_tier}_blau", 3, max(1, I.BRACKETS[_tier] - 3))

# ---------------------------------------------------------------- Lederverarbeitung
R("leder_beutel", "lederverarbeitung", 40, "lederbeutel", [("leichtes_leder", 4), ("grober_faden", 2)], cost=200)
R("leder_wildledertasche", "lederverarbeitung", 90, "wildledertasche", [("mittleres_leder", 6), ("grober_faden", 3)])
R("leder_baerentasche", "lederverarbeitung", 160, "baerenledertasche", [("schweres_leder", 8), ("seidenfaden", 3)])
R("leder_frosttasche", "lederverarbeitung", 220, "frostledertasche", [("dickes_leder", 10), ("seidenfaden", 4), ("eiskern", 1)],
  source="faction:eisenbart:Respektvoll")
R("leder_drachentasche", "lederverarbeitung", 280, "drachenledertasche", [("drachenhaut", 8), ("seidenfaden", 6), ("feuerrubin", 1)],
  source="drop")
recipe_item("leder_drachentasche", 4, 45)
for _tier in range(13):
    sk = _skill_for_tier(_tier)
    lea = _leather_for_tier(_tier)
    thread = "grober_faden" if _tier < 6 else "seidenfaden"
    for _slot, _n in _SLOT_MATS.items():
        for theme in ("affe", "falke") if _slot in ("chest", "legs") else ("affe",):
            R(f"leder_{_slot}_{_tier}_{theme}", "lederverarbeitung", sk + (4 if theme == "falke" else 0),
              f"g_leder_{_slot}_{_tier}_2_{theme}", [(lea, _n), (thread, 1)] + ([("spinnenseide", 1)] if _tier < 3 and _slot == "chest" else []))
    R(f"koecher_{_tier}", "lederverarbeitung", sk + 6, f"g_klasse_bogenschuetze_{_tier}_2", [(lea, 6), (thread, 2)])
    R(f"umhang_{_tier}", "lederverarbeitung", sk + 2, f"g_back_{_tier}_2_falke", [(lea, 5), (thread, 1)])

# ---------------------------------------------------------------- Alchemie
for rid, sk, res, mats, n in [
    ("schwacher_heiltrank", 1, "schwacher_heiltrank", [("friedblume", 1), ("silberblatt", 1), ("leeres_flaeschchen", 1)], 1),
    ("schwacher_manatrank", 15, "schwacher_manatrank", [("silberblatt", 2), ("leeres_flaeschchen", 1)], 1),
    ("gegengift", 20, "gegengift", [("friedblume", 1), ("silberblatt", 1), ("leeres_flaeschchen", 1)], 2),
    ("wundgift", 30, "wundgift", [("spinnenseide", 1), ("friedblume", 1), ("leeres_flaeschchen", 1)], 2),
    ("heiltrank", 60, "heiltrank", [("frostmoos", 1), ("friedblume", 2), ("leeres_flaeschchen", 1)], 1),
    ("manatrank", 65, "manatrank", [("frostmoos", 1), ("silberblatt", 2), ("leeres_flaeschchen", 1)], 1),
    ("elixier_der_staerke", 70, "elixier_der_staerke", [("frostmoos", 2), ("friedblume", 1), ("leeres_flaeschchen", 1)], 1),
    ("elixier_der_weisheit", 75, "elixier_der_weisheit", [("frostmoos", 1), ("silberblatt", 2), ("leeres_flaeschchen", 1)], 1),
    ("elixier_der_flinkheit", 80, "elixier_der_flinkheit", [("frostmoos", 2), ("silberblatt", 1), ("leeres_flaeschchen", 1)], 1),
    ("zauberoel", 100, "zauberoel", [("leuchtpilz", 1), ("silberblatt", 2), ("leeres_flaeschchen", 1)], 1),
    ("grosser_heiltrank", 130, "grosser_heiltrank", [("mondkraut", 2), ("frostmoos", 1), ("kristallphiole", 1)], 1),
    ("grosser_manatrank", 135, "grosser_manatrank", [("mondkraut", 2), ("silberblatt", 2), ("kristallphiole", 1)], 1),
    ("fluchbann", 140, "fluchbann", [("mondkraut", 1), ("leuchtpilz", 1), ("kristallphiole", 1)], 2),
    ("elixier_der_festung", 160, "elixier_der_festung", [("mondkraut", 2), ("eiskern", 1), ("kristallphiole", 1)], 1),
    ("feuerschutztrank", 200, "feuerschutztrank", [("feuerbluete", 2), ("eiskern", 1), ("kristallphiole", 1)], 1),
    ("maechtiger_heiltrank", 210, "maechtiger_heiltrank", [("feuerbluete", 2), ("mondkraut", 1), ("kristallphiole", 1)], 1),
    ("maechtiger_manatrank", 215, "maechtiger_manatrank", [("feuerbluete", 1), ("mondkraut", 2), ("kristallphiole", 1)], 1),
    ("sternenzauberoel", 240, "sternenzauberoel", [("himmelsdistel", 1), ("aschenmorchel", 1), ("kristallphiole", 1)], 1),
    ("lebensgeistelixier", 260, "lebensgeistelixier", [("himmelsdistel", 2), ("feuerbluete", 2), ("daemonenblut", 1), ("kristallphiole", 1)], 1),
    ("elixier_der_magie", 265, "elixier_der_magie", [("himmelsdistel", 2), ("mondkraut", 2), ("feenstaub", 1), ("kristallphiole", 1)], 1),
]:
    R("alch_" + rid, "alchemie", sk, res, mats, n=n, station="alchemy" if sk >= 60 else None, cast=2.5)
RECIPES["alch_feuerschutztrank"]["source"] = "faction:aschenwacht:Wohlwollend"
RECIPES["alch_lebensgeistelixier"]["source"] = "drop"
recipe_item("alch_lebensgeistelixier", 3, 40)
RECIPES["alch_elixier_der_magie"]["source"] = "faction:mondzirkel:Respektvoll"

# ---------------------------------------------------------------- Verzauberung
DISENCHANT_SKILL = lambda ilvl: max(1, min(300, (ilvl - 8) * 6))  # noqa: E731


def disenchant_yield(item: dict) -> list[tuple[str, int]]:
    q = item["q"]
    ilvl = item.get("ilvl", item.get("lvl", 1))
    big = max(1, ilvl // 12)
    if q == 2:
        return [("magischer_staub", 1 + big)] + ([("glitzernde_essenz", 1)] if ilvl >= 20 else [])
    if q == 3:
        return [("strahlender_splitter", 1), ("glitzernde_essenz", big)]
    if q >= 4:
        return [("leerenkristall", 1 if q == 4 else 2), ("strahlender_splitter", big)]
    return []


for _eid, _e in ENCHANTS.items():
    sk = _e["skill"]
    mats = [("magischer_staub", 2 + sk // 40)]
    if sk >= 80:
        mats.append(("glitzernde_essenz", 1 + sk // 120))
    if sk >= 150:
        mats.append(("geisteressenz" if sk < 200 else "frostsplitter", 2))
    if sk >= 200:
        mats.append(("strahlender_splitter", 1 + (sk >= 250)))
    if _eid == "w_feuerzunge":
        mats = [("leerenkristall", 1), ("feuerbluete", 4), ("feuerrubin", 1)]
    R("vz_" + _eid, "verzauberung", sk, "rolle_" + _eid, mats, name=_e["name"], cast=3.0, enchant=_eid)
RECIPES["vz_w_feuerzunge"]["source"] = "drop"
recipe_item("vz_w_feuerzunge", 4, 45)
RECIPES["vz_c_alle_3"]["source"] = "faction:himmelswaechter:Respektvoll"
RECIPES["vz_b_feuer"]["source"] = "faction:aschenwacht:Respektvoll"

# Plausibilitätsprüfung: alle Zutaten und Ergebnisse müssen existieren
for _r in RECIPES.values():
    for _m, _n in _r["mats"]:
        assert _m in I.ITEMS, (_r["id"], _m)
    assert _r["result"] in I.ITEMS, (_r["id"], _r["result"])


def recipes_for(prof: str) -> list[dict]:
    return sorted((r for r in RECIPES.values() if r["prof"] == prof), key=lambda r: (r["skill"], r["name"]))


def trainer_recipes(prof: str, max_skill: int) -> list[dict]:
    return [r for r in recipes_for(prof) if r["source"] == "trainer" and r["skill"] <= max_skill]
