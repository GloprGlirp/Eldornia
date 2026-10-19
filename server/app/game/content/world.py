"""Weltaufbau von Eldornia.

Koordinaten: x = Osten, z = Süden (Meter). Blickrichtung r: 0 = Norden (-z), pi = Süden,
-pi/2 = Osten, pi/2 = Westen. Gebäude "schauen" mit ihrer Vorderseite (Tür) in Richtung r.

Die Zone Grünmark ist eine offene Welt (Stufe 1–10). Die vergessene Krypta ist eine instanzierte
Dungeon-Zone, die aus begehbaren Rechtecken (Räumen und Gängen) besteht.
"""
import math

N, S, E, W = 0.0, math.pi, -math.pi / 2, math.pi / 2
NE, NW, SE, SW = -math.pi / 4, math.pi / 4, -3 * math.pi / 4, 3 * math.pi / 4

WORLD_NAME = "Eldornia"

ZONES = {
    "gruenmark": {
        "name": "Grünmark", "type": "outdoor", "size": 480, "step": 2, "levels": [1, 10],
        "start": [2.0, 4.0, N], "graveyard": [-15.0, 48.0, S], "water_level": -0.8,
        "sky": {"top": "#4f8fd6", "bottom": "#cfe6f5", "fog": "#bcd6e6", "fog_near": 90, "fog_far": 320,
                "sun": "#fff2d6", "ambient": "#9fb6c9"},
    },
    "krypta": {
        "name": "Die vergessene Krypta", "type": "dungeon", "levels": [8, 10], "max_players": 5,
        "start": [0.0, 1.0, N], "graveyard": None, "exit": ["gruenmark", -122.0, 126.0, E],
        "sky": {"top": "#05060a", "bottom": "#0b0d14", "fog": "#07080d", "fog_near": 25, "fog_far": 85,
                "sun": "#6a7aa8", "ambient": "#2a3048"},
    },
}

# ----------------------------------------------------------------------------- Gelände Grünmark
# Bereiche, in denen das Gelände auf eine feste Höhe eingeebnet wird.
# h=None -> Höhe des natürlichen Geländes im Mittelpunkt
FLATTEN = [
    {"x": 8, "z": 16, "r": 48, "falloff": 22, "h": 0.0},          # Eichenau
    {"x": 0, "z": -110, "r": 52, "falloff": 26, "h": 8.0},        # Burghügel Eldenstein
    {"x": 88, "z": 32, "r": 44, "falloff": 22, "h": None},        # Kaspars Hof
    {"x": 124, "z": -95, "r": 30, "falloff": 16, "h": None},      # Rotdolch-Lager
    {"x": 124, "z": 106, "r": 18, "falloff": 12, "h": None},      # Vorplatz Kupferstollen
    {"x": -120, "z": 126, "r": 22, "falloff": 14, "h": None},     # Friedhof der Vergessenen
    {"x": -70, "z": 0, "r": 15, "falloff": 10, "h": -3.2},        # Spiegelsee (Senke)
]

# Hügel (Gauß-Glocken): x, z, Höhe, Breite
HILLS = [
    {"x": 172, "z": 152, "h": 30, "s": 30},   # Stollenberg
    {"x": -150, "z": -150, "h": 16, "s": 38},
    {"x": 170, "z": -160, "h": 18, "s": 34},
    {"x": -175, "z": 60, "h": 10, "s": 30},
]

WATER = [{"x": -70, "z": 0, "r": 25, "level": -0.8, "name": "Spiegelsee"}]

# Straßen (Polylinien, Breite in Metern)
ROADS = [
    {"w": 4.5, "pts": [[0, 6], [0, -8], [0, -30], [0, -58], [0, -80], [0, -100], [0, -112]]},          # Burgstraße
    {"w": 3.5, "pts": [[12, 18], [26, 19], [40, 20], [52, 22], [62, 24], [72, 26]]},                      # Hofweg
    {"w": 3.0, "pts": [[0, -45], [18, -50], [40, -56], [62, -64], [84, -76], [104, -88], [118, -94]]},   # Rotdolchpfad
    {"w": 3.0, "pts": [[24, 22], [30, 30], [40, 46], [50, 62], [68, 74], [86, 86], [104, 98], [120, 108], [130, 114]]},
    {"w": 3.0, "pts": [[0, 26], [-2, 34], [-5, 46], [-8, 60], [-22, 70], [-40, 80], [-60, 92], [-82, 104],
                       [-100, 116], [-114, 124]]},                                                            # Friedhofsweg
    {"w": 3.0, "pts": [[-4, 6], [-10, -4], [-16, -12], [-28, -14], [-40, -16], [-52, -24], [-64, -32],
                       [-80, -38], [-96, -42], [-116, -48], [-134, -56]]},                                   # Waldweg
]

PLAZA = {"x": 2, "z": 18, "r": 13}   # gepflasterter Dorfplatz

# Fixe Requisiten. Typen siehe Client (props.js). Kollision wird serverseitig abgeleitet.
PROPS = [
    # ---------------------------------------------------------------- Eichenau
    {"t": "well", "x": 0, "z": 20},
    {"t": "bench", "x": 5.3, "z": 21.5, "r": W},
    {"t": "inn", "x": -27, "z": 13, "r": E, "w": 12, "d": 10, "name": "Zum Schiefen Krug"},
    {"t": "smithy", "x": 30, "z": 13, "r": W, "w": 8, "d": 8},
    {"t": "anvil", "x": 21.4, "z": 14, "r": W},
    {"t": "chapel", "x": -15, "z": 35, "r": S, "w": 8, "d": 13},
    {"t": "house", "x": -22, "z": 0, "r": E, "w": 8, "d": 7, "v": 0},
    {"t": "house", "x": 20, "z": -2, "r": W, "w": 8, "d": 7, "v": 1},
    {"t": "house", "x": -36, "z": 31, "r": E, "w": 9, "d": 7, "v": 2},
    {"t": "house", "x": 24, "z": 41, "r": N, "w": 8, "d": 7, "v": 3},
    {"t": "house", "x": 36, "z": 3, "r": S, "w": 8, "d": 7, "v": 1},
    {"t": "house", "x": -31, "z": -22, "r": E, "w": 8, "d": 7, "v": 0},
    {"t": "house", "x": 12, "z": 48, "r": W, "w": 8, "d": 7, "v": 2},
    {"t": "house", "x": 12, "z": 36, "r": N, "w": 8, "d": 6, "v": 3},        # Miras Laden
    {"t": "stall", "x": 12, "z": 27.4, "r": N, "c": "#c9862f"},
    {"t": "stall", "x": 9, "z": 12, "r": S, "c": "#b83b3b"},
    {"t": "stall", "x": -5, "z": 12, "r": S, "c": "#3b6eb8"},
    {"t": "wagon", "x": -9.5, "z": 23.5, "r": S},
    {"t": "shed", "x": 45.5, "z": 27, "r": W, "w": 4, "d": 4},
    {"t": "gate", "x": 0, "z": -8, "r": N, "name": "Eichenau"},
    {"t": "sign", "x": 3, "z": -44, "r": N, "text": ["Burg Eldenstein ↑", "Rotdolch-Lager →", "Eichenau ↓"]},
    {"t": "sign", "x": 27, "z": 26, "r": E, "text": ["Kaspars Hof →", "Kupferstollen ↘"]},
    {"t": "sign", "x": -6, "z": 52, "r": S, "text": ["Friedhof ↙"]},
    {"t": "sign", "x": -14, "z": -6, "r": W, "text": ["Spiegelsee ←", "Wolfsforst ←"]},
    {"t": "graves", "x": -15, "z": 53, "w": 13, "d": 8},
    {"t": "barrel", "x": -18.5, "z": 20.5}, {"t": "barrel", "x": -19.2, "z": 21.6}, {"t": "crate", "x": -20.5, "z": 6},
    {"t": "crate", "x": 25.5, "z": 9.5}, {"t": "barrel", "x": 26, "z": 17.5}, {"t": "crate", "x": 43, "z": 29.6},
    {"t": "pier", "x": -50.5, "z": 4, "r": W, "len": 7},
    {"t": "hut", "x": -43, "z": -51, "r": SE, "w": 6, "d": 6},
    {"t": "cauldron", "x": -39.5, "z": -49},
    # ---------------------------------------------------------------- Burg Eldenstein
    {"t": "wall", "x1": -36, "z1": -80, "x2": -10, "z2": -80},
    {"t": "wall", "x1": 10, "z1": -80, "x2": 36, "z2": -80},
    {"t": "wall", "x1": -36, "z1": -80, "x2": -36, "z2": -152},
    {"t": "wall", "x1": 36, "z1": -80, "x2": 36, "z2": -152},
    {"t": "wall", "x1": -36, "z1": -152, "x2": 36, "z2": -152},
    {"t": "tower", "x": -36, "z": -80, "rad": 5, "h": 15},
    {"t": "tower", "x": 36, "z": -80, "rad": 5, "h": 15},
    {"t": "tower", "x": -36, "z": -152, "rad": 5, "h": 15},
    {"t": "tower", "x": 36, "z": -152, "rad": 5, "h": 15},
    {"t": "tower", "x": -8.5, "z": -80, "rad": 3.6, "h": 13},
    {"t": "tower", "x": 8.5, "z": -80, "rad": 3.6, "h": 13},
    {"t": "gatearch", "x": 0, "z": -80, "r": S, "w": 10},
    {"t": "keep", "x": 0, "z": -140, "r": S, "w": 34, "d": 18},
    {"t": "throne", "x": 0, "z": -120.2, "r": S},
    {"t": "fountain", "x": 0, "z": -100},
    {"t": "kitchen", "x": -29, "z": -104, "r": E, "w": 9, "d": 9},
    {"t": "house", "x": -27, "z": -138, "r": E, "w": 12, "d": 9, "v": 4},     # Kaserne
    {"t": "house", "x": 27, "z": -138, "r": W, "w": 12, "d": 9, "v": 4},      # Lagerhaus
    {"t": "rosegarden", "x": 29, "z": -104, "w": 10, "d": 16},
    {"t": "brazier", "x": -6, "z": -124}, {"t": "brazier", "x": 6, "z": -124},
    {"t": "brazier", "x": -5, "z": -86}, {"t": "brazier", "x": 5, "z": -86},
    {"t": "banner", "x": -12, "z": -130.5, "c": "#8f1d2c"}, {"t": "banner", "x": 12, "z": -130.5, "c": "#8f1d2c"},
    {"t": "weaponrack", "x": 14, "z": -72, "r": E},
    {"t": "fence", "x1": 11, "z1": -58, "x2": 31, "z2": -58},
    {"t": "fence", "x1": 31, "z1": -58, "x2": 31, "z2": -74},
    # ---------------------------------------------------------------- Kaspars Hof
    {"t": "house", "x": 63, "z": 18, "r": E, "w": 9, "d": 8, "v": 5},
    {"t": "barn", "x": 76, "z": 43, "r": W, "w": 10, "d": 14},
    {"t": "windmill", "x": 59, "z": 52, "r": E},
    {"t": "field", "x": 97, "z": 18, "w": 26, "d": 17, "crop": "wheat"},
    {"t": "field", "x": 97, "z": 42, "w": 26, "d": 17, "crop": "turnip"},
    {"t": "fence", "x1": 83, "z1": 8, "x2": 111, "z2": 8},
    {"t": "fence", "x1": 111, "z1": 8, "x2": 111, "z2": 52},
    {"t": "fence", "x1": 83, "z1": 52, "x2": 111, "z2": 52},
    {"t": "haystack", "x": 84, "z": 60}, {"t": "haystack", "x": 88.5, "z": 61.5}, {"t": "haystack", "x": 70, "z": 56},
    {"t": "scarecrow", "x": 97, "z": 30, "r": S},
    {"t": "cart", "x": 70, "z": 12, "r": E},
    # ---------------------------------------------------------------- Rotdolch-Lager
    {"t": "tent", "x": 113, "z": -101, "r": NE, "c": "#8a2a2a"},
    {"t": "tent", "x": 127, "z": -83, "r": S, "c": "#7a3a2a"},
    {"t": "tent", "x": 136, "z": -95, "r": W, "c": "#8a2a2a"},
    {"t": "bigtent", "x": 141, "z": -111, "r": NW, "c": "#9a1f1f"},
    {"t": "campfire", "x": 124, "z": -95},
    {"t": "watchtower", "x": 106, "z": -113},
    {"t": "palisade", "x1": 100, "z1": -78, "x2": 116, "z2": -70},
    {"t": "palisade", "x1": 130, "z1": -70, "x2": 148, "z2": -80},
    {"t": "palisade", "x1": 148, "z1": -80, "x2": 152, "z2": -104},
    {"t": "palisade", "x1": 152, "z1": -104, "x2": 140, "z2": -124},
    {"t": "palisade", "x1": 126, "z1": -124, "x2": 104, "z2": -120},
    {"t": "crate", "x": 131, "z": -104}, {"t": "crate", "x": 132.2, "z": -105.4}, {"t": "barrel", "x": 118, "z": -88},
    {"t": "weaponrack", "x": 120, "z": -105, "r": N},
    # ---------------------------------------------------------------- Kupferstollen
    {"t": "mine", "x": 136, "z": 120, "r": NW},
    {"t": "rails", "x1": 133, "z1": 117, "x2": 120, "z2": 104},
    {"t": "minecart", "x": 124, "z": 108, "r": NW},
    {"t": "lantern", "x": 131, "z": 120}, {"t": "lantern", "x": 138, "z": 114},
    {"t": "crate", "x": 118, "z": 112}, {"t": "crate", "x": 119, "z": 113.4}, {"t": "orepile", "x": 128, "z": 101},
    # ---------------------------------------------------------------- Friedhof der Vergessenen
    {"t": "mausoleum", "x": -132.5, "z": 126, "r": E, "w": 10, "d": 12},
    {"t": "graves", "x": -112, "z": 117, "w": 12, "d": 9},
    {"t": "graves", "x": -112, "z": 137, "w": 12, "d": 8},
    {"t": "ironfence", "x1": -138, "z1": 110, "x2": -100, "z2": 110},
    {"t": "ironfence", "x1": -138, "z1": 142, "x2": -100, "z2": 142},
    {"t": "ironfence", "x1": -100, "z1": 110, "x2": -100, "z2": 120},
    {"t": "ironfence", "x1": -100, "z1": 132, "x2": -100, "z2": 142},
    {"t": "lantern", "x": -124, "z": 122}, {"t": "lantern", "x": -124, "z": 130},
    {"t": "deadtree", "x": -106, "z": 128}, {"t": "deadtree", "x": -133, "z": 114}, {"t": "deadtree", "x": -131, "z": 139},
]

# Eingänge zu anderen Zonen
PORTALS = {
    "gruenmark": [{"x": -126.4, "z": 126, "r": 2.2, "to": "krypta", "name": "Die vergessene Krypta"}],
    "krypta": [{"x": 0, "z": 5.2, "r": 1.8, "to": "gruenmark", "name": "Ausgang"}],
}

# Gebiete (Anzeige des Ortsnamens)
SUBZONES = [
    {"name": "Eichenau", "x": 6, "z": 18, "r": 46},
    {"name": "Burg Eldenstein", "x": 0, "z": -114, "r": 50},
    {"name": "Kaspars Hof", "x": 88, "z": 32, "r": 40},
    {"name": "Rotdolch-Lager", "x": 126, "z": -96, "r": 36},
    {"name": "Kupferstollen", "x": 130, "z": 112, "r": 32},
    {"name": "Friedhof der Vergessenen", "x": -120, "z": 126, "r": 28},
    {"name": "Spiegelsee", "x": -70, "z": 0, "r": 30},
    {"name": "Wolfsforst", "x": -130, "z": -60, "r": 80},
]

# ----------------------------------------------------------------------------- Gegner
# Entweder feste Position (pos) oder Gebiet (x, z, r, n). lvl überschreibt die Stufenspanne.
SPAWNS = {
    "gruenmark": [
        {"mob": "waldwolf", "x": -62, "z": -58, "r": 26, "n": 7, "lvl": [1, 2]},
        {"mob": "waldwolf", "x": -112, "z": -28, "r": 34, "n": 9, "lvl": [2, 3]},
        {"mob": "waldwolf", "x": -150, "z": -82, "r": 26, "n": 6, "lvl": [3, 3]},
        {"mob": "graumaehne", "pos": [-160, -104], "r": SE},
        {"mob": "wildschwein", "x": 97, "z": 30, "r": 24, "n": 8},
        {"mob": "wildschwein", "x": 134, "z": 46, "r": 20, "n": 6},
        {"mob": "wildschwein", "x": 66, "z": 84, "r": 16, "n": 4, "lvl": [2, 3]},
        {"mob": "kaninchen", "x": -30, "z": -44, "r": 26, "n": 6},
        {"mob": "kaninchen", "x": 42, "z": -32, "r": 22, "n": 4},
        {"mob": "kaninchen", "x": 52, "z": 70, "r": 18, "n": 3},
        {"mob": "huhn", "x": -2, "z": 30, "r": 8, "n": 3},
        {"mob": "huhn", "x": 68, "z": 32, "r": 8, "n": 4},
        {"mob": "uebungspuppe", "pos": [15, -64], "r": N},
        {"mob": "uebungspuppe", "pos": [20.5, -62], "r": N},
        {"mob": "uebungspuppe", "pos": [26, -64], "r": N},
        # Rotdolch-Lager
        {"mob": "bandit", "pos": [118, -91]}, {"mob": "bandit", "pos": [121, -100]}, {"mob": "bandit", "pos": [130, -90]},
        {"mob": "bandit", "pos": [128, -102]}, {"mob": "bandit", "pos": [111, -88]}, {"mob": "bandit", "pos": [134, -80]},
        {"mob": "bandit", "pos": [116, -108]}, {"mob": "bandit", "pos": [141, -98]}, {"mob": "bandit", "pos": [102, -84]},
        {"mob": "bandit", "pos": [97, -96]},
        {"mob": "armbrustschuetze", "pos": [108, -110]}, {"mob": "armbrustschuetze", "pos": [133, -76]},
        {"mob": "armbrustschuetze", "pos": [146, -103]}, {"mob": "armbrustschuetze", "pos": [100, -104]},
        {"mob": "armbrustschuetze", "pos": [123, -116]}, {"mob": "armbrustschuetze", "pos": [145, -88]},
        {"mob": "grimbart", "pos": [141, -106], "r": W},
        # Kupferstollen
        {"mob": "tunnelkobold", "x": 124, "z": 102, "r": 18, "n": 8},
        {"mob": "tunnelkobold", "x": 146, "z": 96, "r": 12, "n": 3},
        {"mob": "kobold_geomant", "x": 130, "z": 110, "r": 12, "n": 3},
        {"mob": "kobold_geomant", "pos": [110, 96]},
    ],
    "krypta": [
        {"mob": "skelett", "pos": [-6, -40], "r": S}, {"mob": "skelett", "pos": [-3, -43], "r": S},
        {"mob": "skelett", "pos": [6, -48], "r": S}, {"mob": "skelett", "pos": [9, -45], "r": S},
        {"mob": "knochenmagier", "pos": [0, -53], "r": S},
        {"mob": "skelett", "pos": [28, -44], "r": W},
        {"mob": "skelett", "pos": [48, -36], "r": W}, {"mob": "skelett", "pos": [51, -33], "r": W},
        {"mob": "knochenmagier", "pos": [60, -40], "r": W}, {"mob": "knochenmagier", "pos": [58, -50], "r": W},
        {"mob": "grabwaechter", "pos": [54, -56], "r": S}, {"mob": "skelett", "pos": [46, -56], "r": S},
        {"mob": "skelett", "pos": [54, -77], "r": S},
        {"mob": "grabwaechter", "pos": [54, -108], "r": N},
        {"mob": "skelett", "pos": [44, -100], "r": N}, {"mob": "skelett", "pos": [47, -97], "r": N},
        {"mob": "knochenmagier", "pos": [64, -110], "r": W}, {"mob": "knochenmagier", "pos": [62, -98], "r": W},
        {"mob": "skelett", "pos": [44, -113], "r": E},
        {"mob": "skelett", "pos": [22, -105], "r": E},
        {"mob": "morgrath", "pos": [-16, -106], "r": E},
    ],
}

# ----------------------------------------------------------------------------- Sammelobjekte
OBJECTS = {
    "gruenmark": [
        # Wiesenkraut auf den Wiesen zwischen Burg und Dorf
        *[{"kind": "herb", "item": "wiesenkraut", "pos": p} for p in [
            [-22, -36], [-30, -48], [-16, -52], [-40, -34], [-12, -40], [22, -38], [30, -46], [16, -48],
            [38, -36], [-26, -60], [12, -34], [28, -28], [-34, -28], [44, -44]]],
        # Kupfererz am Stollen
        *[{"kind": "ore", "item": "kupfererz", "pos": p} for p in [
            [117, 99], [128, 95], [141, 104], [147, 113], [111, 111], [124, 121], [151, 99], [115, 92],
            [134, 92], [142, 122]]],
        {"kind": "gackerle", "item": "gackerle", "pos": [63.5, 55.5], "respawn": 10},
    ],
    "krypta": [],
}

# ----------------------------------------------------------------------------- Vergessene Krypta
# Begehbare Rechtecke: x1, z1, x2, z2
KRYPTA_RECTS = [
    [-6, -6, 6, 6],          # Eingangshalle
    [-3, -32, 3, -6],        # Gang 1
    [-14, -56, 14, -32],     # Halle der Ruhelosen
    [14, -47, 42, -41],      # Gang 2
    [42, -62, 66, -26],      # Kammer der Knochenmagier
    [51, -92, 57, -62],      # Gang 3
    [38, -118, 70, -92],     # Beinhaus
    [6, -108, 38, -102],     # Gang 4
    [-30, -132, 6, -80],     # Morgraths Gruft
]
KRYPTA_ROOMS = [
    {"name": "Eingangshalle", "rect": 0}, {"name": "Halle der Ruhelosen", "rect": 2},
    {"name": "Kammer der Knochenmagier", "rect": 4}, {"name": "Beinhaus", "rect": 6},
    {"name": "Morgraths Gruft", "rect": 8},
]
KRYPTA_PROPS = [
    {"t": "stairs", "x": 0, "z": 6, "r": S},
    *[{"t": "pillar", "x": x, "z": z} for x, z in [(-9, -37), (9, -37), (-9, -51), (9, -51),
                                                  (46, -30), (62, -30), (46, -58), (62, -58),
                                                  (42, -96), (66, -96), (42, -114), (66, -114)]],
    *[{"t": "pillar", "x": -12 + 11 * math.cos(a), "z": -106 + 13 * math.sin(a), "big": True}
      for a in [i * math.pi / 3 + math.pi / 6 for i in range(6)]],
    {"t": "sarcophagus", "x": -10, "z": -44, "r": E}, {"t": "sarcophagus", "x": 10, "z": -40, "r": W},
    {"t": "sarcophagus", "x": 54, "z": -44, "r": S}, {"t": "sarcophagus", "x": 48, "z": -104, "r": E},
    {"t": "sarcophagus", "x": 60, "z": -104, "r": W},
    {"t": "bones", "x": -4, "z": -36}, {"t": "bones", "x": 4, "z": -54}, {"t": "bones", "x": 50, "z": -48},
    {"t": "bones", "x": 64, "z": -100}, {"t": "bones", "x": 40, "z": -116}, {"t": "bones", "x": -2, "z": -94},
    {"t": "bonepile", "x": 66, "z": -116}, {"t": "bonepile", "x": 40, "z": -94}, {"t": "bonepile", "x": -26, "z": -84},
    {"t": "altar", "x": -24, "z": -106, "r": E},
    {"t": "brazier", "x": -20, "z": -94}, {"t": "brazier", "x": -20, "z": -118},
    {"t": "brazier", "x": 4, "z": -84}, {"t": "brazier", "x": 4, "z": -128},
    {"t": "candles", "x": 0, "z": -2}, {"t": "candles", "x": 12, "z": -34}, {"t": "candles", "x": 64, "z": -28},
    {"t": "candles", "x": 68, "z": -94},
]
