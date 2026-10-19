"""Fähigkeitsbäume: jede Klasse hat drei Spezialisierungen (GDD Abschnitt 3).

Punkte: 1 pro Stufe ab Stufe 10. Ränge einer Stufe (tier) erfordern 5 * tier Punkte im selben Baum.
Die Talente verändern Werte über "mods"; Endtalente schalten eine neue Fähigkeit frei ("grants").

Mod-Schlüssel (pro Rang):
  str_pct agi_pct sta_pct int_pct spi_pct armor_pct hp_pct mana_pct  – Prozent auf Werte
  crit spell_crit dodge parry block haste                           – Prozentpunkte
  dmg_pct heal_pct threat_pct dmg_taken_pct speed_pct regen_pct      – Prozent
  school_pct:<schule>  ab_pct:<fähigkeit>  ab_crit:<fähigkeit>
  cd:<fähigkeit> (Sek.)  cost_pct:<fähigkeit> (%)  cast:<fähigkeit> (Sek.)  dur:<aura> (Sek.)
  pet_pct max_pets crit_dmg_pct lifesteal_pct dot_pct aoe_pct resource_gain_pct
"""


def T(tid, name, icon, tier, ranks, desc, mods=None, grants=None):
    return {"id": tid, "name": name, "icon": icon, "tier": tier, "ranks": ranks, "desc": desc,
            "mods": mods or {}, "grants": grants}


TREES = {
    # ===================================================================== Ritter
    "ritter": {
        "waechter": [
            T("ritter_zaehigkeit", "Zähigkeit", "armor-vest", 0, 5, "Erhöht Eure Rüstung um {v} %.", {"armor_pct": 2}),
            T("ritter_schildmeister", "Schildmeister", "shield", 0, 3, "Erhöht Eure Blockchance um {v} %.", {"block": 1.5}),
            T("ritter_wehrhaft", "Wehrhaft", "heart-plus", 1, 3, "Erhöht Eure maximale Gesundheit um {v} %.", {"hp_pct": 2}),
            T("ritter_provokation", "Provokation", "shouting", 1, 2, "Verringert die Abklingzeit von Herausforderung um {v} Sek.", {"cd:spott": -1.5}),
            T("ritter_standhaft", "Standhaftigkeit", "stone-tower", 2, 3, "Verringert erlittenen Schaden um {v} %.", {"dmg_taken_pct": -2}),
            T("ritter_bedrohlich", "Bedrohliche Präsenz", "crowned-skull", 2, 3, "Erhöht erzeugte Bedrohung um {v} %.", {"threat_pct": 10}),
            T("ritter_bollwerk", "Bollwerk", "checked-shield", 3, 1, "Schaltet die Fähigkeit Bollwerk frei.", grants="bollwerk"),
        ],
        "schwertmeister": [
            T("ritter_waffenkunde", "Waffenkunde", "crossed-swords", 0, 5, "Erhöht die Chance auf kritische Treffer um {v} %.", {"crit": 1}),
            T("ritter_wucht", "Verbesserter Wuchtschlag", "sword-wound", 0, 3, "Wuchtschlag verursacht {v} % mehr Schaden.", {"ab_pct:wuchtschlag": 10}),
            T("ritter_parade", "Fechtkunst", "sword-clash", 1, 3, "Erhöht Eure Parierchance um {v} %.", {"parry": 1}),
            T("ritter_konter", "Schneller Konter", "sword-slice", 1, 2, "Konterschlag verursacht {v} % mehr Schaden.", {"ab_pct:konterschlag": 15}),
            T("ritter_tempo", "Klingentanz", "sword-spin", 2, 3, "Erhöht das Angriffstempo um {v} %.", {"haste": 2}),
            T("ritter_praezision", "Präzision", "target-shot", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 2}),
            T("ritter_meisterhieb", "Meisterhieb", "broadsword", 3, 1, "Schaltet die Fähigkeit Meisterhieb frei.", grants="meisterhieb"),
        ],
        "vernichter": [
            T("ritter_kraft", "Rohe Kraft", "biceps", 0, 5, "Erhöht Eure Stärke um {v} %.", {"str_pct": 2}),
            T("ritter_schwung", "Schwung", "axe-swing", 0, 3, "Erhöht kritischen Schaden um {v} %.", {"crit_dmg_pct": 6}),
            T("ritter_gnadenlos", "Gnadenlos", "decapitation", 1, 3, "Gnadenstoß verursacht {v} % mehr Schaden.", {"ab_pct:gnadenstoss": 10}),
            T("ritter_wirbel", "Verheerende Wirbel", "spinning-sword", 1, 2, "Wirbelklinge und Spaltschlag verursachen {v} % mehr Schaden.", {"ab_pct:wirbelklinge": 12, "ab_pct:spaltschlag": 12}),
            T("ritter_zorn", "Heiliger Zorn", "fire-shield", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 3}),
            T("ritter_blutung", "Tiefe Wunden", "bleeding-wound", 2, 3, "Kritische Treffer erzeugen {v} zusätzliche Entschlossenheit.", {"crit_resource": 2}),
            T("ritter_vernichtung", "Vernichtungsschlag", "axe-sword", 3, 1, "Schaltet die Fähigkeit Vernichtungsschlag frei.", grants="vernichtungsschlag"),
        ],
    },
    # ===================================================================== Magier
    "magier": {
        "feuer": [
            T("magier_glut", "Glühende Macht", "fire", 0, 5, "Erhöht Feuerschaden um {v} %.", {"school_pct:fire": 2}),
            T("magier_zuendung", "Zündung", "fire-ray", 0, 3, "Verringert die Abklingzeit von Flammenstoß um {v} Sek.", {"cd:flammenstoss": -1}),
            T("magier_flammen", "Flammenwerfer", "fireball", 1, 3, "Verringert die Zauberzeit von Feuerball um {v} Sek.", {"cast:feuerball": -0.15}),
            T("magier_brand", "Brandstifter", "flame", 1, 2, "Schaden über Zeit verursacht {v} % mehr Schaden.", {"dot_pct": 15}),
            T("magier_kritfeuer", "Kritische Masse", "fire-ring", 2, 3, "Erhöht die kritische Trefferchance von Zaubern um {v} %.", {"spell_crit": 2}),
            T("magier_regen", "Inferno", "fire-silhouette", 2, 3, "Feuerregen verursacht {v} % mehr Schaden.", {"ab_pct:feuerregen": 15}),
            T("magier_pyro", "Pyroschlag", "fire-bomb", 3, 1, "Schaltet die Fähigkeit Pyroschlag frei.", grants="pyroschlag"),
        ],
        "frost": [
            T("magier_eiskalt", "Eiskalt", "ice-bolt", 0, 5, "Erhöht Frostschaden um {v} %.", {"school_pct:frost": 2}),
            T("magier_frostblitz", "Verbesserter Frostblitz", "ice-bolt", 0, 3, "Verringert die Zauberzeit von Frostblitz um {v} Sek.", {"cast:frostblitz": -0.1}),
            T("magier_eispanzer", "Eisige Haut", "frozen-body", 1, 3, "Erhöht Eure Rüstung um {v} %.", {"armor_pct": 5}),
            T("magier_nova", "Permafrost", "frostfire", 1, 2, "Verringert die Abklingzeit von Frostnova um {v} Sek.", {"cd:frostnova": -2}),
            T("magier_splitter", "Eissplitter", "ice-spear", 2, 3, "Erhöht kritischen Zauberschaden um {v} %.", {"crit_dmg_pct": 8}),
            T("magier_kaelte", "Bittere Kälte", "snowflake-2", 2, 3, "Verringert erlittenen Schaden um {v} %.", {"dmg_taken_pct": -2}),
            T("magier_eislanze", "Eislanze", "ice-spear", 3, 1, "Schaltet die Fähigkeit Eislanze frei.", grants="eislanze"),
        ],
        "arkan": [
            T("magier_intellekt", "Arkaner Geist", "brain", 0, 5, "Erhöht Eure Intelligenz um {v} %.", {"int_pct": 2}),
            T("magier_konzentration", "Arkane Konzentration", "concentration-orb", 0, 3, "Verringert Manakosten um {v} %.", {"cost_pct": -3}),
            T("magier_geschosse", "Verbesserte Geschosse", "magic-swirl", 1, 3, "Arkane Geschosse verursachen {v} % mehr Schaden.", {"ab_pct:arkane_geschosse": 10}),
            T("magier_blink", "Phasenverschiebung", "teleport", 1, 2, "Verringert die Abklingzeit von Blinzeln um {v} Sek.", {"cd:blinzeln": -2}),
            T("magier_arkan", "Arkane Macht", "magic-gate", 2, 3, "Erhöht Arkanschaden um {v} %.", {"school_pct:arcane": 4}),
            T("magier_mana", "Manastrom", "magic-potion", 2, 3, "Erhöht die Manaregeneration um {v} %.", {"regen_pct": 10}),
            T("magier_arkanmacht", "Arkanmacht", "magic-gate", 3, 1, "Schaltet die Fähigkeit Arkanmacht frei.", grants="arkanmacht"),
        ],
    },
    # ===================================================================== Räuber
    "raeuber": {
        "meuchelmord": [
            T("raeuber_gifte", "Tödliche Gifte", "poison-bottle", 0, 5, "Erhöht Naturschaden um {v} %.", {"school_pct:nature": 3}),
            T("raeuber_hinterhalt", "Hinterhalt", "backstab", 0, 3, "Meucheln verursacht {v} % mehr Schaden.", {"ab_pct:meucheln": 8}),
            T("raeuber_moerder", "Mörderinstinkt", "crossed-swords", 1, 3, "Erhöht kritische Treffer um {v} %.", {"crit": 1}),
            T("raeuber_ausweiden", "Verbessertes Ausweiden", "bloody-sword", 1, 2, "Ausweiden verursacht {v} % mehr Schaden.", {"ab_pct:ausweiden": 10}),
            T("raeuber_dot", "Schleichendes Gift", "poison-cloud", 2, 3, "Schaden über Zeit verursacht {v} % mehr Schaden.", {"dot_pct": 10}),
            T("raeuber_kalt", "Kaltblütig", "dripping-blade", 2, 3, "Erhöht kritischen Schaden um {v} %.", {"crit_dmg_pct": 8}),
            T("raeuber_todesstoss", "Todesstoß", "dripping-blade", 3, 1, "Schaltet die Fähigkeit Todesstoß frei.", grants="todesstoss"),
        ],
        "kampf": [
            T("raeuber_beidhaendig", "Beidhändigkeit", "daggers", 0, 5, "Erhöht den Schaden der Schildhand um {v} %.", {"offhand_pct": 10}),
            T("raeuber_ausdauer", "Zähigkeit", "heart-plus", 0, 3, "Erhöht Eure maximale Gesundheit um {v} %.", {"hp_pct": 2}),
            T("raeuber_tempo", "Klingenwirbel", "spinning-blades", 1, 3, "Erhöht das Angriffstempo um {v} %.", {"haste": 2}),
            T("raeuber_finster", "Verbesserter Finsterer Stoß", "plain-dagger", 1, 2, "Senkt die Kosten von Finsterer Stoß um {v} %.", {"cost_pct:finsterer_stoss": -12}),
            T("raeuber_dodge", "Ausweichmanöver", "dodging", 2, 3, "Erhöht Ausweichen um {v} %.", {"dodge": 1.5}),
            T("raeuber_aggression", "Aggression", "fist", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 2}),
            T("raeuber_adrenalin", "Adrenalinrausch", "lightning-helix", 3, 1, "Schaltet die Fähigkeit Adrenalinrausch frei.", grants="adrenalinrausch"),
        ],
        "schatten": [
            T("raeuber_tarnung", "Meister der Tarnung", "cloak-dagger", 0, 5, "Erhöht die Laufgeschwindigkeit um {v} %.", {"speed_pct": 2}),
            T("raeuber_ueberfall", "Überfall", "punch-blast", 0, 3, "Erhöht kritische Treffer um {v} %.", {"crit": 1}),
            T("raeuber_schattenhaut", "Schattenhaut", "shadow-follower", 1, 3, "Verringert erlittenen Schaden um {v} %.", {"dmg_taken_pct": -2}),
            T("raeuber_verschwinden", "Rasches Verschwinden", "invisible", 1, 2, "Verringert die Abklingzeit von Verschwinden um {v} Sek.", {"cd:verschwinden": -30}),
            T("raeuber_energie", "Energiefluss", "lightning-frequency", 2, 3, "Erhöht die Energieregeneration um {v} %.", {"regen_pct": 7}),
            T("raeuber_dunkel", "Dunkle Klingen", "shadow-grasp", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 2}),
            T("raeuber_schattenschritt", "Schattenschritt", "shadow-follower", 3, 1, "Schaltet die Fähigkeit Schattenschritt frei.", grants="schattenschritt"),
        ],
    },
    # ===================================================================== Samurai
    "samurai": {
        "klingenmeister": [
            T("samurai_schaerfe", "Klingenschärfe", "katana", 0, 5, "Erhöht kritische Treffer um {v} %.", {"crit": 1}),
            T("samurai_fluss", "Klingenfluss", "sword-brandish", 0, 3, "Iaido-Schlag verursacht {v} % mehr Schaden.", {"ab_pct:iaido": 8}),
            T("samurai_fokus", "Innerer Fokus", "meditation", 1, 3, "Erhöht erzeugten Fokus um {v} %.", {"resource_gain_pct": 8}),
            T("samurai_schnitt", "Verbesserter Klingenschnitt", "sword-slice", 1, 2, "Klingenschnitt verursacht {v} % mehr Schaden.", {"ab_pct:klingenschnitt": 12}),
            T("samurai_tempo", "Wind der Klinge", "wind-slap", 2, 3, "Erhöht das Angriffstempo um {v} %.", {"haste": 2}),
            T("samurai_kritdmg", "Tödliche Präzision", "shining-sword", 2, 3, "Erhöht kritischen Schaden um {v} %.", {"crit_dmg_pct": 8}),
            T("samurai_shogun", "Shogun-Schnitt", "shining-sword", 3, 1, "Schaltet die Fähigkeit Shogun-Schnitt frei.", grants="shogun_schnitt"),
        ],
        "konter": [
            T("samurai_parade", "Meisterparade", "sword-clash", 0, 5, "Erhöht Parieren um {v} %.", {"parry": 1}),
            T("samurai_ruestung", "Lackierte Rüstung", "samurai-helmet", 0, 3, "Erhöht Eure Rüstung um {v} %.", {"armor_pct": 4}),
            T("samurai_gegen", "Verbesserter Gegenschlag", "sword-slice", 1, 3, "Gegenschlag verursacht {v} % mehr Schaden.", {"ab_pct:gegenschlag": 10}),
            T("samurai_haltung", "Unerschütterliche Haltung", "sword-clash", 1, 2, "Verringert die Abklingzeit von Paradehaltung um {v} Sek.", {"cd:paradehaltung": -2}),
            T("samurai_leben", "Lebenskraft", "heart-plus", 2, 3, "Erhöht Eure maximale Gesundheit um {v} %.", {"hp_pct": 3}),
            T("samurai_ruhe", "Ruhe im Sturm", "meditation", 2, 3, "Verringert erlittenen Schaden um {v} %.", {"dmg_taken_pct": -2}),
            T("samurai_spiegel", "Spiegelklinge", "mirror-mirror", 3, 1, "Schaltet die Fähigkeit Spiegelklinge frei.", grants="spiegelklinge"),
        ],
        "sturm": [
            T("samurai_beweglich", "Beweglichkeit", "sprint", 0, 5, "Erhöht Eure Beweglichkeit um {v} %.", {"agi_pct": 2}),
            T("samurai_wind", "Windläufer", "wind-slap", 0, 3, "Verringert die Abklingzeit von Windschritt um {v} Sek.", {"cd:windschritt": -1.5}),
            T("samurai_sichel", "Weite Sichel", "crescent-blade", 1, 3, "Mondsichel und Sturmschnitt verursachen {v} % mehr Schaden.", {"ab_pct:mondsichel": 10, "ab_pct:sturmschnitt": 10}),
            T("samurai_schnell", "Leichtfüßig", "running-ninja", 1, 2, "Erhöht die Laufgeschwindigkeit um {v} %.", {"speed_pct": 4}),
            T("samurai_tausend", "Tausend Klingen", "sword-array", 2, 3, "Tausend Schnitte verursacht {v} % mehr Schaden.", {"ab_pct:tausend_schnitte": 12}),
            T("samurai_sturmwut", "Sturmwut", "lightning-frequency", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 2}),
            T("samurai_taifun", "Taifun", "tornado", 3, 1, "Schaltet die Fähigkeit Taifun frei.", grants="taifun"),
        ],
    },
    # ===================================================================== Bogenschütze
    "bogenschuetze": {
        "scharfschuetze": [
            T("bogen_auge", "Falkenauge", "eagle-emblem", 0, 5, "Erhöht kritische Treffer um {v} %.", {"crit": 1}),
            T("bogen_ruhig", "Ruhige Hand", "arrow-scope", 0, 3, "Verringert die Zauberzeit von Gezielter Schuss um {v} Sek.", {"cast:gezielter_schuss": -0.2}),
            T("bogen_schwach", "Schwachstellen", "arrowhead", 1, 3, "Schwachstellenschuss verursacht {v} % mehr Schaden.", {"ab_pct:schwachstellenschuss": 10}),
            T("bogen_mal", "Verbessertes Mal", "target-arrows", 1, 2, "Erhöht allen Schaden gegen markierte Ziele um {v} %.", {"vs_marked_pct": 5}),
            T("bogen_kritdmg", "Tödliche Schüsse", "crosshair-arrow", 2, 3, "Erhöht kritischen Schaden um {v} %.", {"crit_dmg_pct": 8}),
            T("bogen_konz", "Konzentration", "concentration-orb", 2, 3, "Erhöht die Konzentrationsregeneration um {v} %.", {"regen_pct": 8}),
            T("bogen_todesschuss", "Todesschuss", "crosshair-arrow", 3, 1, "Schaltet die Fähigkeit Todesschuss frei.", grants="todesschuss"),
        ],
        "fallensteller": [
            T("bogen_fallen", "Fallenkunde", "wolf-trap", 0, 5, "Verringert die Abklingzeit Eurer Fallen um {v} Sek.", {"cd:eisfalle": -1, "cd:sprengfalle": -1}),
            T("bogen_sprengstoff", "Sprengstoff", "fire-bomb", 0, 3, "Sprengfalle verursacht {v} % mehr Schaden.", {"ab_pct:sprengfalle": 12}),
            T("bogen_ueberleben", "Überlebenskünstler", "heart-plus", 1, 3, "Erhöht Eure maximale Gesundheit um {v} %.", {"hp_pct": 2}),
            T("bogen_salto", "Akrobatik", "backward-time", 1, 2, "Verringert die Abklingzeit von Rückwärtssalto um {v} Sek.", {"cd:rueckwaertssalto": -3}),
            T("bogen_kontrolle", "Kontrolle", "broken-arrow", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 2}),
            T("bogen_feuer", "Brandpfeile", "flaming-arrow", 2, 3, "Erhöht Feuerschaden um {v} %.", {"school_pct:fire": 5}),
            T("bogen_netz", "Netzfalle", "spider-web", 3, 1, "Schaltet die Fähigkeit Netzfalle frei.", grants="netzfalle"),
        ],
        "waldlaeufer": [
            T("bogen_flink", "Flink", "sprint", 0, 5, "Erhöht Eure Beweglichkeit um {v} %.", {"agi_pct": 2}),
            T("bogen_gift", "Waldgifte", "chemical-arrow", 0, 3, "Erhöht Naturschaden um {v} %.", {"school_pct:nature": 5}),
            T("bogen_schnell", "Schnellschütze", "fast-arrow", 1, 3, "Schneller Schuss verursacht {v} % mehr Schaden.", {"ab_pct:schneller_schuss": 10}),
            T("bogen_pfad", "Pfadfinder", "footprint", 1, 2, "Erhöht die Laufgeschwindigkeit um {v} %.", {"speed_pct": 4}),
            T("bogen_rudel", "Rudelführer", "wolf-head", 2, 3, "Euer Begleiter verursacht {v} % mehr Schaden.", {"pet_pct": 10}),
            T("bogen_hagel", "Pfeilsturm", "arrow-flights", 2, 3, "Pfeilhagel verursacht {v} % mehr Schaden.", {"ab_pct:pfeilhagel": 12}),
            T("bogen_wolf", "Begleitwolf", "wolf-howl", 3, 1, "Schaltet die Fähigkeit Begleitwolf frei.", grants="begleitwolf"),
        ],
    },
    # ===================================================================== Barbar
    "barbar": {
        "berserker": [
            T("barbar_raserei", "Blutige Raserei", "enrage", 0, 5, "Erhöht das Angriffstempo um {v} %.", {"haste": 1.5}),
            T("barbar_wut", "Unbändige Wut", "bleeding-heart", 0, 3, "Erhöht erzeugte Wut um {v} %.", {"resource_gain_pct": 6}),
            T("barbar_wirbel", "Verbesserter Wirbelwind", "spinning-sword", 1, 3, "Wirbelwind verursacht {v} % mehr Schaden.", {"ab_pct:wirbelwind": 10}),
            T("barbar_rausch", "Kampfrausch", "lightning-frequency", 1, 2, "Verringert die Abklingzeit von Berserkerwut um {v} Sek.", {"cd:berserkerwut": -15}),
            T("barbar_durst", "Blutdurst", "bloody-stash", 2, 3, "Heilt Euch um {v} % des verursachten Schadens.", {"lifesteal_pct": 1}),
            T("barbar_wildheit", "Wildheit", "barbarian", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 2}),
            T("barbar_raserei_t", "Raserei", "lightning-frequency", 3, 1, "Schaltet die Fähigkeit Raserei frei.", grants="raserei"),
        ],
        "schlaechter": [
            T("barbar_kraft", "Muskelberg", "biceps", 0, 5, "Erhöht Eure Stärke um {v} %.", {"str_pct": 2}),
            T("barbar_zerschmettern", "Schneller Schlag", "hammer-drop", 0, 3, "Verringert die Zauberzeit von Zerschmettern um {v} Sek.", {"cast:zerschmettern": -0.25}),
            T("barbar_hinrichten", "Henker", "decapitation", 1, 3, "Hinrichten verursacht {v} % mehr Schaden.", {"ab_pct:hinrichten": 10}),
            T("barbar_wucht", "Wucht", "axe-swing", 1, 2, "Erhöht kritischen Schaden um {v} %.", {"crit_dmg_pct": 10}),
            T("barbar_waffe", "Zweihandmeister", "battle-axe", 2, 3, "Erhöht kritische Treffer um {v} %.", {"crit": 1.5}),
            T("barbar_ruestung", "Rüstungsbrecher", "split-cross", 2, 3, "Eure Angriffe ignorieren {v} % Rüstung.", {"armor_pen": 4}),
            T("barbar_schaedel", "Schädelspalter", "split-cross", 3, 1, "Schaltet die Fähigkeit Schädelspalter frei.", grants="schaedelspalter"),
        ],
        "kriegsherr": [
            T("barbar_haut", "Dicke Haut", "armor-vest", 0, 5, "Erhöht Eure Rüstung um {v} %.", {"armor_pct": 3}),
            T("barbar_schrei", "Donnernder Schrei", "shouting", 0, 3, "Einschüchternder Schrei erzeugt {v} % mehr Bedrohung.", {"threat_pct": 8}),
            T("barbar_ausdauer", "Ausdauer der Ahnen", "heart-plus", 1, 3, "Erhöht Eure maximale Gesundheit um {v} %.", {"hp_pct": 3}),
            T("barbar_stampfer", "Erdbeben", "earth-crack", 1, 2, "Verringert die Abklingzeit von Kriegsstampfer um {v} Sek.", {"cd:kriegsstampfer": -5}),
            T("barbar_trotz", "Trotz", "last-stand", 2, 3, "Verringert erlittenen Schaden um {v} %.", {"dmg_taken_pct": -2}),
            T("barbar_anfuehrer", "Anführer", "horn-internal", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 1.5}),
            T("barbar_ahnen", "Schrei der Ahnen", "horn-internal", 3, 1, "Schaltet die Fähigkeit Schrei der Ahnen frei.", grants="ahnenschrei"),
        ],
    },
    # ===================================================================== Druide
    "druide": {
        "wiederherstellung": [
            T("druide_heilung", "Heilkunst", "healing", 0, 5, "Erhöht Eure Heilung um {v} %.", {"heal_pct": 2}),
            T("druide_beruehrung", "Sanfte Berührung", "healing", 0, 3, "Verringert die Zauberzeit von Heilende Berührung um {v} Sek.", {"cast:heilende_beruehrung": -0.2}),
            T("druide_verjuengung", "Verbesserte Verjüngung", "leaf-swirl", 1, 3, "Verjüngung heilt {v} % mehr.", {"ab_pct:verjuengung": 10}),
            T("druide_mana", "Lebensquell", "magic-potion", 1, 2, "Erhöht die Manaregeneration um {v} %.", {"regen_pct": 12}),
            T("druide_wildwuchs", "Üppiger Wildwuchs", "three-leaves", 2, 3, "Wildwuchs heilt {v} % mehr.", {"ab_pct:wildwuchs": 12}),
            T("druide_geist", "Geist der Natur", "fairy", 2, 3, "Euer Naturgeist ist {v} % stärker.", {"pet_pct": 15}),
            T("druide_baum", "Baum des Lebens", "tree-growth", 3, 1, "Schaltet die Fähigkeit Baum des Lebens frei.", grants="baum_des_lebens"),
        ],
        "gleichgewicht": [
            T("druide_zorn", "Naturzorn", "lightning-arc", 0, 5, "Erhöht Naturschaden um {v} %.", {"school_pct:nature": 2}),
            T("druide_mond", "Mondlicht", "moon-bats", 0, 3, "Erhöht Arkanschaden um {v} %.", {"school_pct:arcane": 3}),
            T("druide_schnell", "Rasche Zornesblitze", "lightning-arc", 1, 3, "Verringert die Zauberzeit von Zorn um {v} Sek.", {"cast:zorn": -0.15}),
            T("druide_wurzeln", "Dornenwurzeln", "vine-whip", 1, 2, "Wucherwurzeln kosten {v} % weniger Mana.", {"cost_pct:wucherwurzeln": -20}),
            T("druide_kritzauber", "Mondfuror", "moon", 2, 3, "Erhöht die kritische Trefferchance von Zaubern um {v} %.", {"spell_crit": 2}),
            T("druide_sturm", "Sturmgewalt", "tornado", 2, 3, "Hurrikan verursacht {v} % mehr Schaden.", {"ab_pct:hurrikan": 12}),
            T("druide_sterne", "Sternenregen", "falling-star", 3, 1, "Schaltet die Fähigkeit Sternenregen frei.", grants="sternenregen"),
        ],
        "wildheit": [
            T("druide_fell", "Dickes Fell", "bear-head", 0, 5, "Erhöht Eure Rüstung um {v} %.", {"armor_pct": 4}),
            T("druide_pranke", "Scharfe Krallen", "claw-slashes", 0, 3, "Prankenhieb verursacht {v} % mehr Schaden.", {"ab_pct:prankenhieb": 10}),
            T("druide_bedrohung", "Brüllen", "bear-face", 1, 3, "Erhöht erzeugte Bedrohung um {v} %.", {"threat_pct": 10}),
            T("druide_wild", "Wilde Kraft", "biceps", 1, 2, "Erhöht Eure Stärke um {v} %.", {"str_pct": 4}),
            T("druide_zaeh", "Zähigkeit des Bären", "heart-plus", 2, 3, "Erhöht Eure maximale Gesundheit um {v} %.", {"hp_pct": 3}),
            T("druide_instinkt", "Überlebensinstinkt", "dodging", 2, 3, "Erhöht Ausweichen um {v} %.", {"dodge": 1.5}),
            T("druide_zermalmen", "Zermalmen", "bear-face", 3, 1, "Schaltet die Fähigkeit Zermalmen frei.", grants="zermalmen"),
        ],
    },
    # ===================================================================== Totenbeschwörer
    "totenbeschwoerer": {
        "knochen": [
            T("tb_diener", "Starke Diener", "raise-skeleton", 0, 5, "Eure Diener verursachen {v} % mehr Schaden.", {"pet_pct": 5}),
            T("tb_heer", "Wachsendes Heer", "skeleton-inside", 0, 3, "Ihr könnt {v} zusätzlichen Diener befehligen.", {"max_pets": 0.34}),
            T("tb_knochenschild", "Dicker Knochenschild", "bone-gnawer", 1, 3, "Knochenschild absorbiert {v} % mehr.", {"ab_pct:knochenschild": 15}),
            T("tb_explosion", "Gewaltige Explosion", "explosion-rays", 1, 2, "Leichenexplosion verursacht {v} % mehr Schaden.", {"ab_pct:leichenexplosion": 15}),
            T("tb_bindung", "Seelenbindung", "chained-heart", 2, 3, "Verringert erlittenen Schaden um {v} %.", {"dmg_taken_pct": -2}),
            T("tb_armee", "Ewige Armee", "skeleton-inside", 2, 3, "Verringert die Abklingzeit von Armee der Toten um {v} Sek.", {"cd:armee_der_toten": -20}),
            T("tb_golem", "Knochengolem", "spiked-dragon-head", 3, 1, "Schaltet die Fähigkeit Knochengolem frei.", grants="knochengolem"),
        ],
        "fluch": [
            T("tb_schatten", "Schattenmacht", "burning-skull", 0, 5, "Erhöht Schattenschaden um {v} %.", {"school_pct:shadow": 2}),
            T("tb_qual", "Endlose Qual", "cursed-star", 0, 3, "Fluch der Qual hält {v} Sek. länger an.", {"dur:fluch_qual": 2}),
            T("tb_dot", "Verderbnis", "death-zone", 1, 3, "Schaden über Zeit verursacht {v} % mehr Schaden.", {"dot_pct": 10}),
            T("tb_furcht", "Grauen", "terror", 1, 2, "Verringert die Zauberzeit von Furcht um {v} Sek.", {"cast:furcht": -0.5}),
            T("tb_seuche", "Seuchenbringer", "poison-gas", 2, 3, "Seuchenwolke verursacht {v} % mehr Schaden.", {"ab_pct:seuchenwolke": 12}),
            T("tb_krit", "Dunkle Eingebung", "evil-book", 2, 3, "Erhöht die kritische Trefferchance von Zaubern um {v} %.", {"spell_crit": 2}),
            T("tb_faeule", "Seelenfäule", "death-zone", 3, 1, "Schaltet die Fähigkeit Seelenfäule frei.", grants="seelenfaeule"),
        ],
        "blut": [
            T("tb_leben", "Blutige Vitalität", "heart-plus", 0, 5, "Erhöht Eure maximale Gesundheit um {v} %.", {"hp_pct": 2}),
            T("tb_entzug", "Gieriger Entzug", "drain", 0, 3, "Lebensentzug verursacht {v} % mehr Schaden.", {"ab_pct:lebensentzug": 10}),
            T("tb_speer", "Knochenspeerschleuder", "bone-knife", 1, 3, "Verringert die Abklingzeit von Knochenspeer um {v} Sek.", {"cd:knochenspeer": -1}),
            T("tb_blutmagie", "Blutmagie", "blood", 1, 2, "Heilt Euch um {v} % des verursachten Schadens.", {"lifesteal_pct": 2}),
            T("tb_ausdauer", "Untote Ausdauer", "skull-shield", 2, 3, "Erhöht Eure Ausdauer um {v} %.", {"sta_pct": 3}),
            T("tb_macht", "Blutrausch", "bleeding-heart", 2, 3, "Erhöht allen verursachten Schaden um {v} %.", {"dmg_pct": 2}),
            T("tb_pakt", "Blutpakt", "blood", 3, 1, "Schaltet die Fähigkeit Blutpakt frei.", grants="blutpakt"),
        ],
    },
}

TALENTS: dict[str, dict] = {}
TALENT_TREE: dict[str, tuple[str, str]] = {}   # talent_id -> (class, spec)
for _cls, _trees in TREES.items():
    for _spec, _list in _trees.items():
        for _t in _list:
            TALENTS[_t["id"]] = _t
            TALENT_TREE[_t["id"]] = (_cls, _spec)


def talent_mods(class_id: str, ranks: dict[str, int]) -> tuple[dict, list[str]]:
    """Summiert die Mods aller gelernten Talente. Gibt (mods, freigeschaltete Fähigkeiten) zurück."""
    mods: dict[str, float] = {}
    grants: list[str] = []
    for tid, r in ranks.items():
        t = TALENTS.get(tid)
        if not t or TALENT_TREE[tid][0] != class_id or r <= 0:
            continue
        r = min(r, t["ranks"])
        for k, v in t["mods"].items():
            mods[k] = mods.get(k, 0.0) + v * r
        if t["grants"]:
            grants.append(t["grants"])
    return mods, grants


def spent_in_tree(class_id: str, spec: str, ranks: dict[str, int]) -> int:
    return sum(min(r, TALENTS[t]["ranks"]) for t, r in ranks.items() if t in TALENTS and TALENT_TREE[t] == (class_id, spec))


def can_learn(class_id: str, ranks: dict[str, int], tid: str, available: int) -> str | None:
    t = TALENTS.get(tid)
    if not t or TALENT_TREE[tid][0] != class_id:
        return "Unbekanntes Talent."
    if sum(ranks.values()) >= available:
        return "Ihr habt keine Fähigkeitspunkte mehr."
    if ranks.get(tid, 0) >= t["ranks"]:
        return "Dieses Talent ist bereits voll ausgebaut."
    spec = TALENT_TREE[tid][1]
    if spent_in_tree(class_id, spec, ranks) < 5 * t["tier"]:
        return f"Dafür braucht Ihr {5 * t['tier']} Punkte in diesem Baum."
    return None


def main_spec(class_id: str, ranks: dict[str, int]) -> str | None:
    best, best_n = None, 0
    for spec in TREES.get(class_id, {}):
        n = spent_in_tree(class_id, spec, ranks)
        if n > best_n:
            best, best_n = spec, n
    return best


def client_trees(class_id: str) -> dict:
    out = {}
    for spec, lst in TREES.get(class_id, {}).items():
        out[spec] = [{k: v for k, v in t.items() if k != "mods"} | {"per_rank": next(iter(t["mods"].values()), 0) if t["mods"] else 0}
                     for t in lst]
    return out
