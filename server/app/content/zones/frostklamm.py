"""Frostklamm – Region (Stufe 10–25).

Schneebedeckte Berge, Zwergenfestungen, Eisriesen und verlassene Minen. Fokus auf schwere Rüstung und
seltene Erze. Hauptstadt: Hammerfeste des Eisenbart-Klans unter König Brogar. Im Nordosten liegt der
Eingang zur Schwarzen Schmiede (Dungeon, Stufe 20–30).

Koordinaten wie in der Grünmark: x = Osten, z = Süden. Der Pass aus der Grünmark endet im Süden.
"""
import math

from .. import items as I

N, S, E, W = 0.0, math.pi, -math.pi / 2, math.pi / 2
NE, NW, SE, SW = -math.pi / 4, math.pi / 4, -3 * math.pi / 4, 3 * math.pi / 4

# ============================================================================== Gegenstände der Region
I.QUEST("eisriesenzahn", "Eisriesenzahn", "fangs", "So groß wie ein Unterarm und eiskalt.")
I.QUEST("frostwolfpelz", "Makelloser Frostwolfpelz", "fur-shirt", "Weich, weiß und warm.")
I.QUEST("verlorene_spitzhacke", "Verlorene Zwergenspitzhacke", "war-pick", "Eingeritzt: \"Eigentum von Durin Kieselbart\".")
I.QUEST("runenstein_fragment", "Runensteinfragment", "rune-stone", "Leuchtet schwach blau, wenn man es anhaucht.")
I.QUEST("yetifell", "Zotteliges Yetifell", "animal-hide", "Riecht nach nassem Hund. Einem sehr großen nassen Hund.")
I.QUEST("schwarzeisen_befehle", "Schwarzeisen-Befehle", "scroll-unfurled", "Unterzeichnet mit einem rußigen Daumenabdruck.", 1)
I.QUEST("frostkern", "Pulsierender Frostkern", "ice-cube", "Kalt genug, um Gedanken einzufrieren.")
I.QUEST("grubenlaterne", "Alte Grubenlaterne", "lantern-flame", "Sie brennt noch. Irgendwie.")
I.QUEST("hrimgars_krone", "Hrimgars Eiskrone", "crown", "Schmilzt nicht. Nicht einmal im Schmiedefeuer.", 1)
I.QUEST("brogars_bart", "Brogars Bartspange", "pendant-key", "Aus reinem Mithril. Brogar vermisst sie seit Wochen.", 1)

I.AR("frostwolfumhang", "Frostwolfumhang", 2, "back", "umhang", 12, {"sta": 3, "agi": 2}, vis=I.V(c="#d8e0ea"))
I.AR("zwergische_stiefel", "Zwergische Marschstiefel", 2, "feet", "platte", 13, {"str": 4, "sta": 3}, vis=I.V(m="#9aa0aa", c="#5a3a22"))
I.AR("kuerschnerhandschuhe", "Kürschnerhandschuhe", 2, "hands", "leder", 13, {"agi": 4, "sta": 3}, vis=I.V(c="#8a7a6a"))
I.AR("runengewirkte_kapuze", "Runengewirkte Kapuze", 2, "head", "stoff", 14, {"int": 5, "spi": 3}, vis=I.V(c="#3a5a8a", g="#80c0ff"))
I.AR("stollenkette", "Stollenkettenhemd", 2, "chest", "kette", 15, {"agi": 4, "str": 3, "sta": 4}, vis=I.V(m="#8a8e96", c="#4a3a2a"))
I.AR("eisbrecher_schultern", "Eisbrecher-Schulterplatten", 3, "shoulders", "platte", 17, {"str": 7, "sta": 6}, vis=I.V(m="#b8d0e8", c="#3a5a8a"))
I.AR("yetijaegerwams", "Wams des Yetijägers", 3, "chest", "leder", 18, {"agi": 9, "sta": 7}, vis=I.V(c="#e8e4dc"))
I.AR("robe_des_runenmeisters", "Robe des Runenmeisters", 3, "chest", "stoff", 18, {"int": 9, "spi": 6, "sp": 9}, vis=I.V(c="#2a4a8a", g="#80c0ff"))
I.AR("ring_des_eisenbarts", "Siegelring des Eisenbarts", 3, "ring", "schmuck", 20, {"str": 5, "sta": 6})
I.AR("frostfeuer_amulett", "Frostfeueramulett", 3, "neck", "schmuck", 20, {"int": 6, "sp": 8, "frost_res": 10})
I.W("brogars_hammer", "Brogars Ersatzhammer", 3, "kriegshammer", 20, (48, 74), 3.6, {"str": 10, "sta": 8}, bind="bop",
    desc="\"Ich habe noch elf davon.\" – König Brogar", vis=I.V(m="#b8bcc6", a="#e0b648"))
I.W("runenklinge_frostklamm", "Runenklinge der Frostklamm", 3, "schwert", 20, (30, 54), 2.6, {"str": 8, "sta": 6}, bind="bop",
    vis=I.V(m="#b8d0e8", g="#80c0ff"))
I.W("eiszapfenstab", "Eiszapfenstab", 3, "stab", 20, (30, 52), 3.0, {"int": 9, "spi": 6, "sp": 14}, bind="bop",
    vis=I.V(w="#a0c0e0", g="#b0e0ff"))
I.W("bergbogen", "Bogen der Bergwacht", 3, "bogen", 20, (32, 58), 2.8, {"agi": 9, "sta": 6}, bind="bop", vis=I.V(w="#5a4a40"))
I.W("frostkatana", "Klinge des Ewigen Winters", 3, "katana", 20, (44, 70), 2.9, {"agi": 7, "str": 6}, bind="bop", vis=I.V(m="#d0e8ff", g="#a0d8ff"))
I.W("eisdolch", "Frostzahn", 3, "dolch", 20, (18, 33), 1.8, {"agi": 8, "sta": 5}, bind="bop", vis=I.V(m="#c0e0ff", g="#a0d8ff"))
I.W("eisriesenaxt", "Axt des Eisriesen", 3, "zweihandaxt", 20, (52, 80), 3.5, {"str": 11, "sta": 7}, bind="bop", vis=I.V(m="#a8c8e8"))
I.AR("eisbrecher_schild", "Schild des Eisbrechers", 3, "off_hand", "schild", 20, {"sta": 8, "str": 4}, bind="bop",
     vis=I.V(c="#3a5a8a", m="#b8d0e8"))
# Weltboss Hrimgar
I.W("hrimgars_frostklinge", "Hrimgars Frostklinge", 4, "zweihandschwert", 24, (72, 108), 3.4, {"str": 16, "sta": 14},
    bind="bop", vis=I.V(m="#d0e8ff", a="#80c0ff", g="#a0e0ff"),
    proc={"chance": 0.1, "dmg": {"school": "frost", "base": (40, 6, 60, 7)}, "name": "Frostbiss"})
I.AR("krone_des_frostkoenigs", "Krone des Frostkönigs", 4, "head", "platte", 24, {"str": 13, "sta": 15, "frost_res": 15},
     bind="bop", vis=I.V(m="#d0e8ff", c="#3a5a8a", g="#a0e0ff"))
I.AR("eisriesengurt", "Gürtelschnalle der Eisriesen", 4, "hands", "kette", 24, {"agi": 11, "sta": 10}, bind="bop",
     vis=I.V(m="#b8d0e8", g="#a0e0ff"))
I.AR("mantel_des_ewigen_winters", "Mantel des Ewigen Winters", 4, "back", "umhang", 24, {"int": 9, "sta": 9, "sp": 12, "frost_res": 15},
     bind="bop", vis=I.V(c="#e8f0ff", g="#a0e0ff"))
I.W("frostherz_stab", "Stab des Frostherzens", 4, "stab", 24, (44, 72), 3.0, {"int": 15, "spi": 9, "sp": 24}, bind="bop",
    vis=I.V(w="#c0e0ff", g="#80d0ff"))

ZONE = {
    "id": "frostklamm", "name": "Frostklamm", "type": "outdoor", "theme": "frost", "levels": [10, 25],
    "size": 480, "step": 2, "region": True,
    "start": [-10.0, 205.0, N], "graveyard": [-2.0, 176.0, N], "spirit_healer": "Runenpriesterin Edda",
    "music": "frost",
    "terrain": {
        "seed": 23, "base": 9.0, "freq": 0.012, "detail": 1.4, "detail_freq": 0.05,
        "edge": {"start": 170, "end": 236, "height": 70},
        "hills": [{"x": -150, "z": -170, "h": 34, "s": 40}, {"x": 160, "z": -60, "h": 28, "s": 34},
                  {"x": -170, "z": 40, "h": 24, "s": 34}, {"x": 100, "z": 170, "h": 22, "s": 30},
                  {"x": -60, "z": -60, "h": 18, "s": 26}, {"x": 60, "z": -180, "h": 26, "s": 30}],
        "flatten": [
            {"x": -8, "z": 186, "r": 26, "falloff": 16, "h": 2.0},          # Lager Frosthauch
            {"x": 0, "z": -100, "r": 56, "falloff": 26, "h": 6.0},          # Hammerfeste
            {"x": 160, "z": 30, "r": 30, "falloff": 18, "h": None},         # Tiefenstollen
            {"x": 70, "z": 100, "r": 26, "falloff": 14, "h": -3.4},         # Gefrorener See
            {"x": -150, "z": -40, "r": 22, "falloff": 14, "h": None},       # Yetihöhlen
            {"x": -120, "z": -165, "r": 34, "falloff": 18, "h": 16.0},      # Eisriesenhorst
            {"x": 140, "z": -135, "r": 30, "falloff": 18, "h": None},       # Schwarzeisen-Lager
            {"x": -140, "z": 100, "r": 26, "falloff": 16, "h": None},       # Frostwolftal
        ],
        "valleys": [
            {"pts": [[-10, 236], [-10, 200], [-6, 160]], "w": 20, "falloff": 14, "level": 2.0},
            {"pts": [[140, -135], [158, -158], [176, -180]], "w": 14, "falloff": 12, "level": None},
        ],
    },
    "water": [{"x": 70, "z": 100, "r": 24, "level": -1.0, "name": "Gefrorener See", "ice": True}],
    "roads": [
        {"w": 4.5, "pts": [[-10, 232], [-10, 200], [-8, 170], [-2, 140], [4, 110], [6, 80], [4, 50], [2, 20], [0, -10], [0, -40], [0, -56]]},
        {"w": 3.0, "pts": [[4, 50], [30, 46], [60, 40], [90, 36], [120, 32], [146, 30]]},
        {"w": 3.0, "pts": [[2, 20], [-30, 22], [-60, 30], [-90, 50], [-120, 80], [-140, 98]]},
        {"w": 3.0, "pts": [[0, -10], [-30, -18], [-70, -30], [-110, -38], [-140, -40]]},
        {"w": 3.0, "pts": [[24, -70], [60, -86], [90, -104], [118, -122], [140, -134], [160, -160], [174, -176]]},
        {"w": 3.0, "pts": [[-24, -80], [-60, -110], [-90, -140], [-112, -160]]},
        {"w": 2.5, "pts": [[6, 80], [30, 92], [46, 98]]},
    ],
    "paved": [{"x": 0, "z": -104, "w": 76, "d": 92}],
    "subzones": [
        {"name": "Lager Frosthauch", "x": -8, "z": 186, "r": 34},
        {"name": "Hammerfeste", "x": 0, "z": -104, "r": 56},
        {"name": "Verlassener Tiefenstollen", "x": 160, "z": 30, "r": 34},
        {"name": "Gefrorener See", "x": 70, "z": 100, "r": 32},
        {"name": "Yetihöhlen", "x": -150, "z": -40, "r": 30},
        {"name": "Eisriesenhorst", "x": -120, "z": -165, "r": 44},
        {"name": "Schwarzeisen-Lager", "x": 140, "z": -135, "r": 36},
        {"name": "Frostwolftal", "x": -140, "z": 100, "r": 50},
        {"name": "Weißer Grat", "x": 60, "z": -180, "r": 40},
        {"name": "Runenfeld", "x": -60, "z": -60, "r": 30},
    ],
    "portals": [
        {"x": -10, "z": 230, "r": 4.5, "to": "gruenmark", "dest": [190, -220, S], "name": "Pass in die Grünmark"},
        {"x": 176, "z": -178, "r": 2.6, "to": "schmiede", "name": "Die Schwarze Schmiede", "dungeon": True},
    ],
    "stones": [{"id": "stein_frosthauch", "name": "Lager Frosthauch", "pos": [4, 196]},
               {"id": "stein_hammerfeste", "name": "Hammerfeste", "pos": [10, -58]},
               {"id": "stein_tiefenstollen", "name": "Tiefenstollen", "pos": [138, 40]}],
    "waypoints": [
        {"id": "wp_tor", "name": "Tor der Hammerfeste", "pos": [0, -52]},
        {"id": "wp_thronhalle", "name": "Vor der Königshalle", "pos": [0, -118]},
    ],
    "accent": [],
    "veg": {"seed": 1337, "count": 1300, "base": 0.08,
            "kinds": [("pine", 0.82), ("deadtree", 0.1), ("birch", 0.08)],
            "forests": [{"x": -140, "z": 100, "r": 60, "density": 0.85, "kinds": [("pine", 0.9), ("birch", 0.1)]},
                        {"x": 90, "z": 160, "r": 50, "density": 0.6}, {"x": -60, "z": 150, "r": 40, "density": 0.5},
                        {"x": 70, "z": -30, "r": 40, "density": 0.45}],
            "edge_density": 0.4, "high_kind": "pine", "high_level": 18, "rocks": 620, "flowers": 60,
            "clear": [{"x": -8, "z": 186, "r": 24}, {"x": 0, "z": -100, "r": 54}, {"x": -120, "z": -165, "r": 30},
                      {"x": 140, "z": -135, "r": 26}, {"x": 160, "z": 30, "r": 22}]},
    "props": [
        # ---------------------------------------------------------------- Lager Frosthauch
        {"t": "bigtent", "x": -18, "z": 182, "r": E, "c": "#5a6a8a"},
        {"t": "tent", "x": 6, "z": 176, "r": W, "c": "#7a5a3a"},
        {"t": "tent", "x": -20, "z": 198, "r": E, "c": "#7a5a3a"},
        {"t": "campfire", "x": -6, "z": 188},
        {"t": "palisade", "x1": -30, "z1": 168, "x2": 14, "z2": 168},
        {"t": "watchtower", "x": 16, "z": 170, "r": S},
        {"t": "banner", "x": -2, "z": 168, "c": "#2d4f9a"},
        {"t": "crate", "x": -14, "z": 174}, {"t": "barrel", "x": -12, "z": 175.5}, {"t": "cart", "x": 10, "z": 192, "r": N},
        {"t": "sign", "x": -4, "z": 162, "r": N, "text": ["Hammerfeste ↑", "Tiefenstollen ↗", "Frostwolftal ↖"]},
        # ---------------------------------------------------------------- Hammerfeste
        {"t": "wall", "x1": -38, "z1": -58, "x2": -9, "z2": -58},
        {"t": "wall", "x1": 9, "z1": -58, "x2": 38, "z2": -58},
        {"t": "wall", "x1": -38, "z1": -58, "x2": -38, "z2": -150},
        {"t": "wall", "x1": 38, "z1": -58, "x2": 38, "z2": -150},
        {"t": "wall", "x1": -38, "z1": -150, "x2": 38, "z2": -150},
        {"t": "tower", "x": -38, "z": -58, "rad": 6, "h": 18}, {"t": "tower", "x": 38, "z": -58, "rad": 6, "h": 18},
        {"t": "tower", "x": -38, "z": -150, "rad": 6, "h": 18}, {"t": "tower", "x": 38, "z": -150, "rad": 6, "h": 18},
        {"t": "gatearch", "x": 0, "z": -58, "r": S, "w": 18},
        {"t": "keep", "x": 0, "z": -128, "r": S, "w": 36, "d": 22, "name": "Königshalle von Hammerfeste", "style": "dwarf"},
        {"t": "smithy", "x": 26, "z": -86, "r": W, "w": 10, "d": 9},
        {"t": "anvil", "x": 18, "z": -84, "r": W}, {"t": "anvil", "x": 18, "z": -90, "r": W},
        {"t": "inn", "x": -26, "z": -84, "r": E, "w": 12, "d": 10, "name": "Zum Frostigen Humpen"},
        {"t": "house", "x": -27, "z": -108, "r": E, "w": 9, "d": 8, "v": 4},
        {"t": "house", "x": 27, "z": -110, "r": W, "w": 9, "d": 8, "v": 4},
        {"t": "fountain", "x": 0, "z": -92, "frozen": True},
        {"t": "brazier", "x": -8, "z": -64}, {"t": "brazier", "x": 8, "z": -64},
        {"t": "brazier", "x": -10, "z": -112}, {"t": "brazier", "x": 10, "z": -112},
        {"t": "banner", "x": -14, "z": -114, "c": "#8a3a1a"}, {"t": "banner", "x": 14, "z": -114, "c": "#8a3a1a"},
        {"t": "weaponrack", "x": 30, "z": -98, "r": W}, {"t": "orepile", "x": 31, "z": -78},
        {"t": "barrel", "x": -18, "z": -76}, {"t": "barrel", "x": -17, "z": -74.6}, {"t": "crate", "x": 20, "z": -70},
        {"t": "stall", "x": -12, "z": -98, "r": E, "c": "#3a5a8a"}, {"t": "stall", "x": 12, "z": -98, "r": W, "c": "#8a3a1a"},
        {"t": "statue", "x": 0, "z": -76, "r": S, "name": "Statue Durgins des Ersten"},
        # ---------------------------------------------------------------- Tiefenstollen
        {"t": "mine", "x": 176, "z": 22, "r": W, "name": "Verlassener Tiefenstollen"},
        {"t": "rails", "x1": 172, "z1": 24, "x2": 140, "z2": 34}, {"t": "minecart", "x": 150, "z": 31, "r": W},
        {"t": "orepile", "x": 156, "z": 40}, {"t": "orepile", "x": 164, "z": 16}, {"t": "shed", "x": 140, "z": 18, "r": N, "w": 5, "d": 5},
        {"t": "lantern", "x": 168, "z": 32}, {"t": "lantern", "x": 168, "z": 12}, {"t": "crate", "x": 146, "z": 22},
        # ---------------------------------------------------------------- Gefrorener See
        {"t": "pier", "x": 50, "z": 92, "r": E, "len": 6}, {"t": "hut", "x": 38, "z": 86, "r": E, "w": 6, "d": 6},
        {"t": "campfire", "x": 42, "z": 96},
        # ---------------------------------------------------------------- Eisriesenhorst
        *[{"t": "pillar", "x": round(-120 + 26 * math.cos(a), 1), "z": round(-165 + 26 * math.sin(a), 1), "big": True, "ice": True}
          for a in [i * math.pi / 4 for i in range(8)]],
        {"t": "throne", "x": -120, "z": -184, "r": S, "scale": 2.6, "ice": True},
        {"t": "bonepile", "x": -104, "z": -150}, {"t": "bonepile", "x": -136, "z": -150}, {"t": "campfire", "x": -120, "z": -160, "blue": True},
        # ---------------------------------------------------------------- Schwarzeisen-Lager
        {"t": "palisade", "x1": 120, "z1": -116, "x2": 160, "z2": -116},
        {"t": "palisade", "x1": 120, "z1": -116, "x2": 120, "z2": -150},
        {"t": "bigtent", "x": 132, "z": -140, "r": S, "c": "#2a2224"},
        {"t": "tent", "x": 150, "z": -128, "r": W, "c": "#3a2a2a"}, {"t": "tent", "x": 128, "z": -124, "r": E, "c": "#3a2a2a"},
        {"t": "anvil", "x": 142, "z": -136, "r": S}, {"t": "brazier", "x": 146, "z": -138}, {"t": "brazier", "x": 136, "z": -130},
        {"t": "orepile", "x": 154, "z": -146}, {"t": "banner", "x": 140, "z": -118, "c": "#1a1a1a"},
        {"t": "gatearch", "x": 176, "z": -182, "r": SW, "w": 10, "dark": True},
        # ---------------------------------------------------------------- Yetihöhlen / Runenfeld
        {"t": "mine", "x": -164, "z": -46, "r": E, "name": "Yetihöhle", "cave": True},
        {"t": "bonepile", "x": -146, "z": -34}, {"t": "bones", "x": -152, "z": -50},
        *[{"t": "runestone", "x": round(-60 + 12 * math.cos(a), 1), "z": round(-60 + 12 * math.sin(a), 1)}
          for a in [i * math.pi * 2 / 6 for i in range(6)]],
        {"t": "altar", "x": -60, "z": -60, "r": S},
        {"t": "sign", "x": 6, "z": 20, "r": N, "text": ["Hammerfeste ↑", "Tiefenstollen →", "Frostwolftal ←"]},
        {"t": "sign", "x": 20, "z": -66, "r": E, "text": ["Schwarzeisen-Lager ↗", "Eisriesenhorst ↖"]},
    ],
}

NPCS = {
    # ---------------------------------------------------------------- Hammerfeste
    "brogar": {
        "name": "König Brogar Eisenbart", "title": "Herr der Hammerfeste", "lvl": 50, "pos": [0, -118], "rot": S, "scale": 1.15,
        "model": "humanoid",
        "look": {"kind": "dwarf", "skin": "#e0a888", "hair": "#c8c8c8", "beard": "#e0e0e0", "top": "#8a3a1a", "bottom": "#3a2a1a",
                 "armor": True, "cape": "#5a1a0a", "crown": True, "held": "hammer", "anim": "throne"},
        "greeting": "Bei meinem Bart! Ein Großling aus der Grünmark! Simon schickt Euch? Gut, gut. Wir können jede Axt "
                    "gebrauchen. Die Eisriesen werden jeden Winter dreister – und dieser Winter dauert schon elf Jahre.",
        "barks": ["Bei meinem Bart!", "Ein Zwerg ohne Bart ist wie ein Amboss ohne Hammer.",
                  "Wo ist nur meine Bartspange? Ich hatte sie gestern noch. Oder letztes Jahr.",
                  "Simon mit seinen zwei Augen ... ich habe auch zwei! Hat nur nie jemand gezählt."],
        "services": [],
    },
    "grimhild": {
        "name": "Grimhild Hammerschlag", "title": "Meisterschmiedin", "lvl": 40, "pos": [20, -88], "rot": W, "model": "humanoid",
        "look": {"kind": "dwarf", "body": "f", "skin": "#e8b090", "hair": "#a84a1a", "hair_style": "braid", "top": "#5a3a2a",
                 "bottom": "#3a3a3a", "apron": "#4a3020", "held": "hammer", "anim": "anvil", "bare_arms": True},
        "greeting": "Ihr wollt Stahl, der nicht bricht? Dann seid Ihr hier richtig. Ich schmiede seit 140 Jahren. "
                    "Die ersten hundert waren Übung.",
        "barks": ["*Klong* *Klong* Gutes Erz singt unterm Hammer.", "Die Schwarzeisenzwerge ... Schande über ihre Bärte."],
        "services": ["vendor", "repair", "prof_trainer"], "prof": ["schmiedekunst", "bergbau"],
        "vendor": ["schmiedekohle", "g_platte_chest_3_2_baer", "g_kette_chest_3_2_baer", "g_platte_head_3_2_waechter",
                   "g_schild_3_2_waechter", "g_kriegshammer_3_2_baer", "g_axt_3_2_baer"],
    },
    "olaf": {
        "name": "Olaf Fassbauch", "title": "Wirt des Frostigen Humpens", "lvl": 30, "pos": [-19, -84], "rot": E, "model": "humanoid",
        "look": {"kind": "dwarf", "skin": "#f0b896", "hair": "#6a4422", "beard": "#6a4422", "top": "#7a5a3a", "bottom": "#4a3a2a",
                 "apron": "#e8e0d0", "anim": "idle"},
        "greeting": "Willkommen im Frostigen Humpen! Das Bier ist kalt, das Feuer ist warm, und die Geschichten sind gelogen.",
        "barks": ["Noch ein Humpen? Natürlich noch ein Humpen!", "Prost! Auf die Bärte!"],
        "services": ["vendor", "innkeeper"], "vendor": ["zwergenbrot", "bergquellwasser", "wildschweinbraten", "melonensaft"],
        "bind_stone": "stein_hammerfeste",
    },
    "thrain": {
        "name": "Thrain Silberaxt", "title": "Rüstmeister des Eisenbart-Klans", "lvl": 40, "pos": [12, -100], "rot": W,
        "model": "humanoid",
        "look": {"kind": "dwarf", "skin": "#d49a7a", "hair": "#3a2a1a", "beard": "#3a2a1a", "top": "#3a5a8a", "bottom": "#3a3a3a",
                 "armor": True, "anim": "idle"},
        "greeting": "Treue zum Klan wird belohnt. Wer uns hilft, trägt bald Stahl aus Hammerfeste.",
        "services": ["vendor"], "faction": "eisenbart",
        "vendor": ["eisbrecher_schultern", "ring_des_eisenbarts", "frostfeuer_amulett", "reittier_zwergenwidder", "heiltrank", "manatrank"],
    },
    "edda": {
        "name": "Runenpriesterin Edda", "title": "Geistheilerin", "lvl": 35, "pos": [-12, 178], "rot": N, "model": "humanoid",
        "look": {"kind": "dwarf", "body": "f", "skin": "#e8c0a0", "hair": "#d8d8d8", "hair_style": "braid", "top": "#3a5a8a",
                 "robe": True, "held": "staff", "anim": "idle"},
        "greeting": "Die Runen flüstern, dass Ihr kommt. Wer in der Frostklamm fällt, erwacht hier am Feuer.",
        "services": ["spirit", "prof_trainer"], "prof": "verzauberung",
    },
    "sigrun": {
        "name": "Späherin Sigrun", "title": "Bergwacht", "lvl": 25, "pos": [-2, 182], "rot": S, "model": "humanoid",
        "look": {"kind": "human", "body": "f", "skin": "#f2c9a8", "hair": "#e3d0a0", "hair_style": "braid", "top": "#5a6a8a",
                 "bottom": "#3a3a4a", "hood": True, "hood_color": "#d8e0ea", "held": "bow", "anim": "idle"},
        "greeting": "Ihr kommt aus dem Süden? Dann seid Ihr die Kälte nicht gewohnt. Bleibt in Bewegung, sonst friert Ihr fest. "
                    "Ich meine das wörtlich – fragt den Kerl da hinten am Hang.",
        "barks": ["Frostwölfe im Westen, Yetis im Nordwesten, Eisriesen überall. Schöne Gegend.",
                  "Wer hier oben ein Feuer ausgehen lässt, hat es nicht lange."],
        "services": ["vendor"], "vendor": ["zwergenbrot", "bergquellwasser", "heiltrank", "manatrank", "seidenfaden"],
    },
    "durin": {
        "name": "Durin Kieselbart", "title": "Verzweifelter Bergmann", "lvl": 20, "pos": [134, 36], "rot": E, "model": "humanoid",
        "look": {"kind": "dwarf", "skin": "#e0ae8c", "hair": "#4a3a2a", "beard": "#4a3a2a", "top": "#5a5a6a", "bottom": "#4a3a2a",
                 "hat": "mining", "anim": "idle"},
        "greeting": "Mein Stollen! Mein schöner Stollen! Erst kamen die Kobolde, dann die Geister – und jetzt ist auch noch "
                    "meine Spitzhacke weg!",
        "barks": ["Wer hat meine Spitzhacke? WER?", "Da unten singt es manchmal. Es ist kein schönes Lied."],
        "services": ["vendor", "prof_trainer"], "prof": "bergbau", "vendor": ["schmiedekohle", "bergquellwasser"],
    },
    "ingrid": {
        "name": "Eisfischerin Ingrid", "title": "", "lvl": 15, "pos": [40, 92], "rot": E, "model": "humanoid",
        "look": {"kind": "human", "body": "f", "skin": "#e8c0a0", "hair": "#a86a32", "hair_style": "bun", "top": "#8a5a3a",
                 "bottom": "#4a3a2a", "hood": True, "hood_color": "#e8e0d0", "held": "rod", "anim": "sit"},
        "greeting": "Ruhig, ruhig ... die Fische hören jedes Wort. Unter dem Eis leben aber nicht nur Fische. Seit einiger "
                    "Zeit leuchtet der See nachts blau.",
        "barks": ["Ein Biss! ... Nein, das war mein Fuß."],
    },
    "kragg": {
        "name": "Kragg Steinfaust", "title": "Hauptmann der Bergwacht", "lvl": 40, "pos": [-6, -64], "rot": S, "model": "humanoid",
        "look": {"kind": "dwarf", "skin": "#c98a6a", "hair": "#1a1a1a", "beard": "#1a1a1a", "top": "#3a5a8a", "bottom": "#3a3a3a",
                 "armor": True, "helm": True, "held": "axe", "shield": True, "anim": "guard"},
        "greeting": "Halt, Großling! ... Ah, Ihr seid der Held aus der Grünmark. Willkommen in Hammerfeste. Die Bergwacht "
                    "braucht jeden Arm, der eine Waffe halten kann.",
        "barks": ["Haltung, Wachen! Bärte gerade!", "Die Schwarzeisen wagen sich immer näher an die Mauern."],
    },
    "wache_hf_1": {"name": "Bergwache", "lvl": 35, "pos": [-6, -54], "rot": S, "model": "humanoid", "guard": True,
                   "look": {"kind": "dwarf", "skin": "#d49a7a", "hair": "#6a4422", "beard": "#6a4422", "top": "#3a5a8a",
                            "bottom": "#3a3a3a", "armor": True, "helm": True, "held": "axe2h", "anim": "guard"},
                   "greeting": "Hammerfeste steht Euch offen."},
    "wache_hf_2": {"name": "Bergwache", "lvl": 35, "pos": [6, -54], "rot": S, "model": "humanoid", "guard": True,
                   "look": {"kind": "dwarf", "skin": "#c98a6a", "hair": "#2a1a10", "beard": "#2a1a10", "top": "#3a5a8a",
                            "bottom": "#3a3a3a", "armor": True, "helm": True, "held": "axe2h", "anim": "guard"},
                   "greeting": "Bart ab vor dem König!"},
    "ulla": {"name": "Ulla Pfeffermühle", "title": "Kräuterkunde & Alchemie", "lvl": 30, "pos": [-28, -100], "rot": E, "model": "humanoid",
             "look": {"kind": "dwarf", "body": "f", "skin": "#e8b090", "hair": "#e8e0d0", "hair_style": "bun", "top": "#5a6a3a",
                      "robe": True, "anim": "idle"},
             "greeting": "Frostmoos, Bergwurz, Eisblume ... hier oben wächst mehr, als man denkt. Man muss nur unter dem Schnee suchen.",
             "services": ["vendor", "prof_trainer"], "prof": ["alchemie", "kraeuterkunde"],
             "vendor": ["heiltrank", "manatrank", "leeres_flaeschchen", "kristallphiole"]},
    "frode": {"name": "Frode Wolfspelz", "title": "Lederverarbeitung", "lvl": 30, "pos": [-28, -116], "rot": E, "model": "humanoid",
              "look": {"kind": "human", "skin": "#d9a07a", "hair": "#e0d0b0", "hair_style": "long", "beard": "#e0d0b0",
                       "top": "#d8d0c0", "bottom": "#5a4a3a", "anim": "idle"},
              "greeting": "Frostwolfpelz, Yetifell, Luchsleder – die Frostklamm ist ein Paradies für Gerber. Und eine Hölle für alles andere.",
              "services": ["vendor", "prof_trainer"], "prof": "lederverarbeitung", "vendor": ["grober_faden", "seidenfaden"]},
    "bjarne": {"name": "Bjarne", "title": "Auktionator", "lvl": 20, "pos": [-12, -94], "rot": E, "model": "humanoid",
               "look": {"kind": "dwarf", "skin": "#ecbc98", "hair": "#8a8a8a", "beard": "#8a8a8a", "top": "#2a4a8a",
                        "bottom": "#2a2a3a", "held": "book", "anim": "idle"},
               "greeting": "Kaufen, verkaufen, feilschen! Der Marktplatz ist überall gleich – nur hier oben frieren die Münzen.",
               "services": ["auction", "mail"]},
}

MOBS = {
    # ---------------------------------------------------------------- Frostwolftal (10–13)
    "frostwolf": {"name": "Frostwolf", "lvl": [10, 12], "family": "tier", "model": "wolf", "look": {"tint": "#d8e0ea", "tint2": "#8a98a8"},
                  "hp_mult": 1.05, "dmg_mult": 1.0, "aggro": True, "respawn": 45, "radius": 0.75, "wander": 10, "social": 10,
                  "hide": "mittleres_leder", "hide_chance": 0.55, "resist": {"frost": 0.4, "fire": -0.25},
                  "loot": [{"item": "frostwolfpelz", "chance": 0.5}, {"item": "zerbrochener_reisszahn", "chance": 0.3}],
                  "world_drop": 0.06,
                  "abilities": [{"id": "frostbiss", "name": "Frostbiss", "kind": "strike", "cd": 10, "first": 4, "mult": 1.3,
                                 "debuff": {"id": "frostbiss", "name": "Frostbiss", "debuff": True, "slow": 0.3, "dur": 5}}]},
    "schneeluchs": {"name": "Schneeluchs", "lvl": [11, 13], "family": "tier", "model": "lynx", "look": {"tint": "#e8e4dc", "tint2": "#8a8070"},
                    "hp_mult": 0.95, "dmg_mult": 1.1, "aggro": True, "respawn": 45, "radius": 0.6, "wander": 8,
                    "hide": "mittleres_leder", "hide_chance": 0.5, "world_drop": 0.06,
                    "abilities": [{"id": "anspringen", "name": "Anspringen", "kind": "strike", "cd": 12, "first": 1, "mult": 1.6}]},
    "weisszahn": {"name": "Weißzahn", "title": "Leitwolf des Tals", "lvl": [13, 13], "family": "tier", "model": "wolf", "scale": 1.6,
                  "look": {"tint": "#f4f6fa", "tint2": "#a8b8c8"}, "hp_mult": 2.4, "dmg_mult": 1.3, "aggro": True, "respawn": 600,
                  "rare": True, "elite": True, "radius": 1.0, "hide": "mittleres_leder", "hide_chance": 1.0, "bounty": True,
                  "loot": [{"item": "frostwolfumhang", "chance": 0.7}, {"item": "kuerschnerhandschuhe", "chance": 0.4}],
                  "abilities": [{"id": "rudelruf", "name": "Ruf des Rudels", "kind": "summon", "cd": 30, "first": 6,
                                 "summon": "frostwolf_welpe", "count": 2, "yell": "*Ohrenbetäubendes Heulen*"},
                                {"id": "eisatem", "name": "Eisatem", "kind": "telegraph_cone", "cd": 12, "first": 8, "radius": 9,
                                 "angle": 70, "warn": 1.5, "mult": 2.0, "school": "frost"}]},
    "frostwolf_welpe": {"name": "Frostwolfwelpe", "lvl": [11, 11], "family": "tier", "model": "wolf", "scale": 0.6,
                        "look": {"tint": "#e8eef4"}, "hp_mult": 0.5, "dmg_mult": 0.6, "aggro": True, "radius": 0.5, "summoned": True},
    # ---------------------------------------------------------------- Gefrorener See (13–15)
    "frostgeist": {"name": "Frostgeist", "lvl": [13, 15], "family": "elementar", "model": "ice_elemental",
                   "hp_mult": 1.0, "dmg_mult": 1.05, "aggro": True, "respawn": 50, "radius": 0.7, "wander": 6,
                   "resist": {"frost": 0.8, "fire": -0.5}, "loot": [{"item": "frostkern", "chance": 0.55}, {"item": "eiskern", "chance": 0.1}],
                   "world_drop": 0.07,
                   "ranged": {"range": 26, "name": "Frostblitz", "school": "frost", "cd": 3.0, "cast": 2.2, "mult": 1.7, "slow": 0.3}},
    "eisschleim": {"name": "Eisschleim", "lvl": [12, 14], "family": "elementar", "model": "slime", "look": {"tint": "#a8d8ff"},
                   "hp_mult": 1.2, "dmg_mult": 0.9, "aggro": True, "respawn": 45, "radius": 0.7, "wander": 6,
                   "resist": {"frost": 0.6, "fire": -0.4}, "loot": [{"item": "frostkern", "chance": 0.3}], "world_drop": 0.05},
    "glazius": {"name": "Glazius", "title": "Herz des Sees", "lvl": [16, 16], "family": "elementar", "model": "ice_elemental",
                "scale": 2.0, "hp_mult": 3.0, "dmg_mult": 1.35, "aggro": True, "respawn": 900, "rare": True, "elite": True,
                "radius": 1.4, "resist": {"frost": 0.9, "fire": -0.5}, "bounty": True,
                "loot": [{"item": "frostfeuer_amulett", "chance": 0.35}, {"item": "runengewirkte_kapuze", "chance": 0.5},
                         {"item": "eiskern", "chance": 1.0}],
                "abilities": [{"id": "eisnova", "name": "Eisnova", "kind": "telegraph_circle_self", "cd": 14, "first": 6,
                               "radius": 8, "warn": 2.0, "mult": 2.0, "school": "frost",
                               "debuff": {"id": "eingefroren", "name": "Eingefroren", "debuff": True, "root": True, "dur": 3}},
                              {"id": "hagel", "name": "Hagelschauer", "kind": "telegraph_random", "cd": 11, "first": 3, "count": 6,
                               "radius": 3, "spread": 14, "warn": 1.6, "flat": 140, "school": "frost"}],
                "aggro_yell": "*Das Eis knirscht und bricht*"},
    # ---------------------------------------------------------------- Tiefenstollen (14–17)
    "frostkobold": {"name": "Frostkobold", "lvl": [14, 16], "family": "humanoid", "model": "humanoid", "scale": 0.8,
                    "look": {"kind": "kobold", "skin": "#8a9aa8", "top": "#4a5a6a", "bottom": "#3a3a4a", "hat": "mining", "held": "pick"},
                    "hp_mult": 1.0, "dmg_mult": 1.0, "aggro": True, "respawn": 45, "radius": 0.5, "wander": 6, "social": 8,
                    "copper": [20, 45], "cloth": "wollstoff",
                    "loot": [{"item": "verlorene_spitzhacke", "chance": 0.25}, {"item": "eisenerz", "chance": 0.2},
                             {"item": "grubenlaterne", "chance": 0.4}],
                    "world_drop": 0.07, "aggro_say": ["Du nicht nehmen Erz!", "Stollen gehört Kobold!", "Kalt! Kalt! Aber unser!"]},
    "kobold_sprengmeister": {"name": "Kobold-Sprengmeister", "lvl": [15, 16], "family": "humanoid", "model": "humanoid", "scale": 0.82,
                             "look": {"kind": "kobold", "skin": "#7a8a98", "top": "#8a3a1a", "bottom": "#3a3a4a", "hat": "mining", "held": "torch"},
                             "hp_mult": 0.85, "dmg_mult": 0.9, "aggro": True, "respawn": 50, "radius": 0.5, "social": 8, "copper": [25, 50],
                             "cloth": "wollstoff", "world_drop": 0.08,
                             "abilities": [{"id": "sprengladung", "name": "Sprengladung", "kind": "telegraph_circles_players", "cd": 10,
                                            "first": 3, "radius": 3.5, "warn": 1.8, "flat": 110, "school": "fire", "count": 1}],
                             "loot": [{"item": "grubenlaterne", "chance": 0.4}]},
    "stollengeist": {"name": "Stollengeist", "lvl": [16, 17], "family": "untot", "model": "ghost", "look": {"tint": "#b0c8e8"},
                     "hp_mult": 0.95, "dmg_mult": 1.05, "aggro": True, "respawn": 50, "radius": 0.5, "wander": 6,
                     "resist": {"shadow": 0.5, "holy": -0.5, "frost": 0.3}, "loot": [{"item": "geisteressenz", "chance": 0.4}],
                     "world_drop": 0.07,
                     "abilities": [{"id": "grubenkaelte", "name": "Grubenkälte", "kind": "strike", "cd": 9, "first": 3, "mult": 1.4,
                                    "debuff": {"id": "grubenkaelte", "name": "Grubenkälte", "debuff": True, "pct": {"haste": -25}, "dur": 8}}]},
    "knurrbart": {"name": "Knurrbart", "title": "Der ruhelose Vorarbeiter", "lvl": [17, 17], "family": "untot", "model": "humanoid",
                  "scale": 1.2, "look": {"kind": "dwarf", "skin": "#8aa0b8", "hair": "#c8d8e8", "beard": "#c8d8e8", "top": "#4a5a6a",
                                         "bottom": "#3a3a4a", "hat": "mining", "held": "pick", "eye_glow": "#a0d0ff", "ghost": True},
                  "hp_mult": 3.0, "dmg_mult": 1.3, "aggro": True, "respawn": 900, "rare": True, "elite": True, "radius": 0.7,
                  "copper": [300, 500], "bounty": True, "resist": {"shadow": 0.5, "holy": -0.5},
                  "loot": [{"item": "stollenkette", "chance": 0.5}, {"item": "zwergische_stiefel", "chance": 0.5}],
                  "abilities": [{"id": "einsturz", "name": "Einsturz", "kind": "telegraph_random", "cd": 10, "first": 4, "count": 5,
                                 "radius": 3, "spread": 12, "warn": 1.8, "flat": 150, "school": "physical"}],
                  "aggro_yell": "WER ... HAT ... FEIERABEND ... GESAGT?!"},
    # ---------------------------------------------------------------- Yetihöhlen (16–18)
    "yeti": {"name": "Zottelyeti", "lvl": [16, 18], "family": "tier", "model": "bear", "scale": 1.25,
             "look": {"tint": "#e8e8ec", "tint2": "#a8b0b8"}, "hp_mult": 1.3, "dmg_mult": 1.1, "aggro": True, "respawn": 50,
             "radius": 1.0, "wander": 8, "social": 10, "hide": "schweres_leder", "hide_chance": 0.5, "resist": {"frost": 0.5},
             "loot": [{"item": "yetifell", "chance": 0.55}, {"item": "gefrorene_zehe", "chance": 0.2}], "world_drop": 0.07,
             "abilities": [{"id": "brullen", "name": "Brüllen", "kind": "aura_self", "cd": 22, "first": 8,
                            "aura": {"id": "yetiwut", "name": "Yetiwut", "pct": {"dmg_done": 30}, "dur": 8}}]},
    "schneepranke": {"name": "Schneepranke", "title": "Mutter der Yetis", "lvl": [19, 19], "family": "tier", "model": "bear",
                     "scale": 1.9, "look": {"tint": "#f8f8fc", "tint2": "#b0c0d0"}, "hp_mult": 3.4, "dmg_mult": 1.4, "aggro": True,
                     "respawn": 900, "rare": True, "elite": True, "radius": 1.5, "hide": "schweres_leder", "hide_chance": 1.0,
                     "bounty": True, "loot": [{"item": "yetijaegerwams", "chance": 0.6}, {"item": "frostwolfumhang", "chance": 0.3},
                              {"item": "brogars_bart", "chance": 1.0}],
                     "abilities": [{"id": "lawine", "name": "Lawine", "kind": "telegraph_line", "cd": 13, "first": 5, "length": 18,
                                    "width": 4, "warn": 1.8, "mult": 2.4, "school": "frost"},
                                   {"id": "stampfen", "name": "Stampfen", "kind": "telegraph_circle_self", "cd": 16, "first": 9,
                                    "radius": 7, "warn": 1.8, "mult": 1.8}],
                     "aggro_yell": "*GRRRAAAAOOOH*"},
    # ---------------------------------------------------------------- Runenfeld (17–19)
    "runenwaechter": {"name": "Runenwächter", "lvl": [17, 19], "family": "mechanisch", "model": "golem", "look": {"tint": "#8a96a3", "glow": "#80c0ff"},
                      "hp_mult": 1.5, "dmg_mult": 1.0, "armor_mult": 1.6, "aggro": True, "respawn": 60, "radius": 1.0, "wander": 0,
                      "loot": [{"item": "runenstein_fragment", "chance": 0.6}], "world_drop": 0.07, "resist": {"physical": 0.15, "nature": 0.3},
                      "abilities": [{"id": "runenschlag", "name": "Runenschlag", "kind": "telegraph_cone", "cd": 12, "first": 5, "radius": 7,
                                     "angle": 80, "warn": 1.6, "mult": 2.0, "school": "arcane"}]},
    # ---------------------------------------------------------------- Eisriesenhorst (19–23)
    "eisriese": {"name": "Eisriese", "lvl": [19, 22], "family": "riese", "model": "humanoid", "scale": 2.1,
                 "look": {"kind": "giant", "skin": "#9ab8d8", "hair": "#e8f0ff", "beard": "#e8f0ff", "top": "#4a5a7a", "bottom": "#3a4a5a",
                          "held": "club", "bare_arms": True, "eye_glow": "#a0e0ff"},
                 "hp_mult": 2.0, "dmg_mult": 1.3, "aggro": True, "respawn": 70, "radius": 1.3, "wander": 6, "social": 14,
                 "copper": [40, 90], "resist": {"frost": 0.6, "fire": -0.3},
                 "loot": [{"item": "eisriesenzahn", "chance": 0.55}, {"item": "gefrorene_zehe", "chance": 0.4}, {"item": "eiskern", "chance": 0.12}],
                 "world_drop": 0.09,
                 "abilities": [{"id": "erdstoss", "name": "Erdstoß", "kind": "telegraph_circle_self", "cd": 14, "first": 6, "radius": 6,
                                "warn": 1.8, "mult": 1.9},
                               {"id": "felswurf", "name": "Felswurf", "kind": "telegraph_circles_players", "cd": 11, "first": 3,
                                "radius": 3, "warn": 1.8, "flat": 180, "school": "physical", "count": 1}]},
    "eisriesenschamane": {"name": "Eisriesen-Schamane", "lvl": [20, 22], "family": "riese", "model": "humanoid", "scale": 1.9,
                          "look": {"kind": "giant", "skin": "#8aa8c8", "hair": "#c8e0ff", "top": "#2a4a6a", "robe": True, "held": "staff",
                                   "eye_glow": "#a0e0ff"},
                          "hp_mult": 1.5, "dmg_mult": 1.0, "aggro": True, "respawn": 70, "radius": 1.2, "social": 14, "copper": [40, 90],
                          "resist": {"frost": 0.7, "fire": -0.3}, "world_drop": 0.09,
                          "ranged": {"range": 30, "name": "Eislanze", "school": "frost", "cd": 3.2, "cast": 2.5, "mult": 2.0, "slow": 0.4},
                          "abilities": [{"id": "frostheilung", "name": "Gletscherheilung", "kind": "heal", "cd": 14, "first": 6, "cast": 3.0,
                                         "heal": 0.3, "below": 0.6}],
                          "loot": [{"item": "eisriesenzahn", "chance": 0.5}, {"item": "eiskern", "chance": 0.2}]},
    "hrimgar": {
        "name": "Hrimgar", "title": "Der Frostkönig", "lvl": [24, 24], "family": "riese", "model": "humanoid", "scale": 3.4,
        "look": {"kind": "giant", "skin": "#a8c8e8", "hair": "#ffffff", "beard": "#ffffff", "beard_style": "long", "top": "#2a3a6a",
                 "bottom": "#1a2a4a", "armor": True, "crown": True, "held": "sword2h", "eye_glow": "#a0f0ff", "aura": "#a0e0ff"},
        "hp_mult": 30.0, "dmg_mult": 1.7, "aggro": False, "respawn": 3600, "radius": 3.0, "elite": True, "boss": True,
        "world_boss": True, "leash": 70, "copper": [3000, 5000], "resist": {"frost": 0.8, "fire": -0.4},
        "loot": [{"item": "hrimgars_krone", "chance": 1.0}],
        "boss_loot": {"pool": ["hrimgars_frostklinge", "krone_des_frostkoenigs", "eisriesengurt", "mantel_des_ewigen_winters",
                               "frostherz_stab", "eisriesenaxt", "frostkatana", "eisbrecher_schild"], "n": 2},
        "phases": [
            {"hp": 1.0, "abilities": [
                {"id": "gletscherhieb", "name": "Gletscherhieb", "kind": "telegraph_cone", "cd": 11, "first": 5, "radius": 14,
                 "angle": 90, "warn": 2.0, "mult": 2.8, "school": "frost"},
                {"id": "eissplitter", "name": "Eissplitterhagel", "kind": "telegraph_circles_players", "cd": 12, "first": 8,
                 "radius": 4, "warn": 2.0, "flat": 260, "school": "frost", "count": 3}]},
            {"hp": 0.5, "name": "Ewiger Winter", "yell": "SPÜRT DEN EWIGEN WINTER, WINZLINGE!",
             "on_enter": [{"kind": "summon", "summon": "eisriese", "count": 2}],
             "abilities": [
                 {"id": "gletscherhieb2", "name": "Gletscherhieb", "kind": "telegraph_cone", "cd": 10, "first": 4, "radius": 14,
                  "angle": 100, "warn": 1.8, "mult": 3.0, "school": "frost"},
                 {"id": "blizzard", "name": "Blizzard", "kind": "telegraph_ring", "cd": 16, "first": 8, "radius": 22, "inner": 8,
                  "warn": 2.5, "flat": 300, "school": "frost",
                  "debuff": {"id": "erfroren", "name": "Erfroren", "debuff": True, "slow": 0.6, "dur": 6}}]},
        ],
        "aggro_yell": "WER WAGT ES, DEN FROSTKÖNIG ZU WECKEN?",
        "death_yell": "Der Winter ... endet ... nie ...",
    },
    # ---------------------------------------------------------------- Schwarzeisen-Lager (20–23)
    "schwarzeisen_krieger": {"name": "Schwarzeisen-Krieger", "lvl": [20, 22], "family": "zwerg", "model": "humanoid",
                             "look": {"kind": "dwarf", "skin": "#5a4a48", "hair": "#1a1a1a", "beard": "#1a1a1a", "top": "#2a2224",
                                      "bottom": "#1a1a1a", "armor": True, "helm": True, "held": "axe", "shield": True, "eye_glow": "#ff8a30"},
                             "hp_mult": 1.2, "dmg_mult": 1.1, "armor_mult": 1.4, "aggro": True, "respawn": 55, "radius": 0.6,
                             "wander": 4, "social": 12, "copper": [40, 80], "cloth": "seidenstoff",
                             "loot": [{"item": "schwarzeisen_befehle", "chance": 0.15}, {"item": "eisenerz", "chance": 0.2}],
                             "world_drop": 0.08,
                             "abilities": [{"id": "schildstoss", "name": "Schildstoß", "kind": "strike", "cd": 12, "first": 4, "mult": 1.3,
                                            "debuff": {"id": "betaeubt", "name": "Betäubt", "debuff": True, "stun": True, "dur": 1.5}}]},
    "schwarzeisen_feuerrufer": {"name": "Schwarzeisen-Feuerrufer", "lvl": [21, 22], "family": "zwerg", "model": "humanoid",
                                "look": {"kind": "dwarf", "skin": "#5a4a48", "hair": "#2a1a1a", "beard": "#3a1a10", "top": "#5a1a10",
                                         "robe": True, "held": "staff", "eye_glow": "#ff8a30"},
                                "hp_mult": 0.95, "dmg_mult": 0.95, "aggro": True, "respawn": 55, "radius": 0.6, "social": 12,
                                "copper": [40, 80], "cloth": "seidenstoff", "world_drop": 0.08, "resist": {"fire": 0.5},
                                "ranged": {"range": 30, "name": "Feuerball", "school": "fire", "cd": 3.0, "cast": 2.5, "mult": 2.0},
                                "abilities": [{"id": "flammenwand", "name": "Flammenstoß", "kind": "telegraph_line", "cd": 13, "first": 6,
                                               "length": 14, "width": 3, "warn": 1.6, "mult": 2.0, "school": "fire"}],
                                "loot": [{"item": "schwarzeisen_befehle", "chance": 0.15}]},
    "glutbinder_varga": {"name": "Glutbinderin Varga", "title": "Vorhut der Schwarzen Schmiede", "lvl": [23, 23], "family": "zwerg",
                         "model": "humanoid", "scale": 1.25,
                         "look": {"kind": "dwarf", "body": "f", "skin": "#5a4a48", "hair": "#ff6a1a", "hair_style": "braid", "top": "#3a1a10",
                                  "bottom": "#1a1a1a", "armor": True, "held": "hammer", "eye_glow": "#ff8a30", "aura": "#ff6a1a"},
                         "hp_mult": 3.5, "dmg_mult": 1.4, "aggro": True, "respawn": 600, "elite": True, "rare": True, "radius": 0.8,
                         "copper": [400, 600], "bounty": True, "resist": {"fire": 0.5},
                         "loot": [{"item": "eisbrecher_schultern", "chance": 0.4}, {"item": "runenklinge_frostklamm", "chance": 0.3},
                                  {"item": "schwarzeisen_befehle", "chance": 1.0}],
                         "abilities": [{"id": "lavafontaene", "name": "Lavafontäne", "kind": "telegraph_random", "cd": 10, "first": 4,
                                        "count": 5, "radius": 3, "spread": 12, "warn": 1.6, "flat": 220, "school": "fire"},
                                       {"id": "glutschild", "name": "Glutschild", "kind": "aura_self", "cd": 25, "first": 10,
                                        "aura": {"id": "glutschild", "name": "Glutschild", "pct": {"dmg_taken": -40}, "dur": 6}}],
                         "aggro_yell": "Für Ambossherz! Für die Schwarze Schmiede!"},
}

SPAWNS = [
    {"mob": "frostwolf", "x": -120, "z": 140, "r": 30, "n": 9, "lvl": [10, 11]},
    {"mob": "frostwolf", "x": -160, "z": 80, "r": 30, "n": 8, "lvl": [11, 12]},
    {"mob": "schneeluchs", "x": -90, "z": 110, "r": 26, "n": 6},
    {"mob": "schneeluchs", "x": 70, "z": 160, "r": 26, "n": 5, "lvl": [11, 12]},
    {"mob": "weisszahn", "pos": [-176, 112], "r": E},
    {"mob": "eisschleim", "x": 90, "z": 130, "r": 16, "n": 5},
    {"mob": "frostgeist", "x": 70, "z": 100, "r": 20, "n": 8},
    {"mob": "glazius", "pos": [76, 104], "r": S},
    {"mob": "frostkobold", "x": 158, "z": 30, "r": 18, "n": 8},
    {"mob": "frostkobold", "x": 186, "z": 6, "r": 12, "n": 4},
    {"mob": "kobold_sprengmeister", "x": 166, "z": 40, "r": 12, "n": 3},
    {"mob": "stollengeist", "x": 190, "z": 30, "r": 14, "n": 6},
    {"mob": "knurrbart", "pos": [196, 26], "r": W},
    {"mob": "yeti", "x": -140, "z": -40, "r": 26, "n": 8},
    {"mob": "yeti", "x": -170, "z": -80, "r": 20, "n": 5},
    {"mob": "schneepranke", "pos": [-170, -50], "r": E},
    {"mob": "runenwaechter", "pos": [-48, -52]}, {"mob": "runenwaechter", "pos": [-72, -68]}, {"mob": "runenwaechter", "pos": [-60, -44]},
    {"mob": "runenwaechter", "pos": [-46, -72]}, {"mob": "runenwaechter", "pos": [-76, -54]},
    {"mob": "eisriese", "x": -100, "z": -140, "r": 26, "n": 7},
    {"mob": "eisriese", "x": -150, "z": -150, "r": 20, "n": 5, "lvl": [21, 22]},
    {"mob": "eisriesenschamane", "x": -120, "z": -150, "r": 20, "n": 4},
    {"mob": "hrimgar", "pos": [-120, -178], "r": S},
    {"mob": "schwarzeisen_krieger", "x": 138, "z": -132, "r": 18, "n": 8},
    {"mob": "schwarzeisen_feuerrufer", "x": 144, "z": -140, "r": 14, "n": 4},
    {"mob": "schwarzeisen_krieger", "x": 160, "z": -160, "r": 10, "n": 3, "lvl": [22, 22]},
    {"mob": "glutbinder_varga", "pos": [142, -146], "r": S},
    {"mob": "kaninchen", "x": -40, "z": 140, "r": 26, "n": 4},
]

OBJECTS = [
    *[{"kind": "node", "node": "eisen", "pos": p} for p in [
        [150, 20], [168, 44], [178, 10], [140, 46], [190, 36], [120, 60], [-80, -100], [60, -150], [90, -60], [-180, 20],
        [200, -40], [-30, 120], [110, 150]]],
    *[{"kind": "node", "node": "kupfer", "pos": p} for p in [[20, 150], [-50, 170], [40, 200], [-40, 80]]],
    *[{"kind": "node", "node": "mithril", "pos": p} for p in [[-140, -190], [-160, -160], [176, -110], [70, -200], [200, 80]]],
    *[{"kind": "node", "node": "frostmoos", "pos": p} for p in [
        [-100, 160], [-150, 60], [60, 140], [100, 90], [-40, 40], [40, -20], [-110, -10], [130, -60], [-20, -180], [20, 120]]],
    *[{"kind": "quest", "sub": "herb", "item": "verlorene_spitzhacke", "pos": p, "respawn": 40, "name": "Liegengebliebene Spitzhacke"}
      for p in [[150, 26], [170, 38], [184, 18], [160, 10]]],
    {"kind": "chest", "pos": [-196, -60], "tier": 2, "name": "Vereiste Truhe", "hidden": True},
    {"kind": "chest", "pos": [204, 30], "tier": 2, "name": "Kiste des Vorarbeiters", "hidden": True},
    {"kind": "chest", "pos": [60, -200], "tier": 2, "name": "Verschneite Truhe auf dem Grat", "hidden": True},
    {"kind": "mailbox", "pos": [-12, 192], "name": "Briefkasten"},
    {"kind": "mailbox", "pos": [-6, -66], "name": "Briefkasten"},
    {"kind": "board", "pos": [12, -66], "name": "Anschlagbrett: Kopfgelder"},
    {"kind": "forge", "pos": [24, -82], "name": "Schmiede"},
    {"kind": "alchemy", "pos": [-30, -96], "name": "Alchemietisch"},
]
