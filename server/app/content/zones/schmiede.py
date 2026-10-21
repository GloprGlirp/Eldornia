"""Die Schwarze Schmiede – Dungeon (Stufe 20–30, 3–5 Spieler).

Die Schwarzeisenzwerge erwecken in ihrer Lavaschmiede gewaltige Golems. Endboss: Glutmeister Ambossherz,
ein lebender Schmiedegolem mit glühendem Kern.
"""
import math

from .. import items as I

N, S, E, W = 0.0, math.pi, -math.pi / 2, math.pi / 2
SW = 3 * math.pi / 4

_V = I.V
I.W("schlackenbrecher", "Schlackenbrecher", 3, "kriegshammer", 26, (62, 94), 3.6, {"str": 13, "sta": 10}, bind="bop",
    vis=_V(m="#5a4a48", a="#ff7a20", g="#ff6a1a"))
I.W("glutklinge", "Glutklinge der Esse", 3, "schwert", 26, (40, 72), 2.6, {"str": 10, "agi": 6, "sta": 8}, bind="bop",
    vis=_V(m="#6a4a40", g="#ff8a30"))
I.W("essenstab", "Stab der Essenhüterin", 3, "stab", 26, (40, 68), 3.0, {"int": 12, "spi": 8, "sp": 18}, bind="bop",
    vis=_V(w="#3a2a26", g="#ff8a30"))
I.W("funkenbogen", "Funkenschleuder", 3, "bogen", 26, (42, 74), 2.8, {"agi": 12, "sta": 7}, bind="bop", vis=_V(w="#3a2a26", g="#ff8a30"))
I.W("russdolch", "Rußdolch", 3, "dolch", 26, (24, 44), 1.8, {"agi": 10, "sta": 7}, bind="bop", vis=_V(m="#3a3436", g="#ff6a1a"))
I.W("glutkatana", "Glutgehärtetes Katana", 3, "katana", 26, (58, 90), 2.9, {"agi": 9, "str": 8}, bind="bop", vis=_V(m="#6a4a40", g="#ff8a30"))
I.W("schmiedeaxt", "Große Schmiedeaxt", 3, "zweihandaxt", 26, (66, 100), 3.5, {"str": 14, "sta": 9}, bind="bop", vis=_V(m="#5a4a48"))
I.AR("russgeschwaerzte_robe", "Rußgeschwärzte Robe", 3, "chest", "stoff", 26, {"int": 12, "spi": 8, "sp": 14, "fire_res": 10}, bind="bop",
     vis=_V(c="#2a2224", g="#ff6a1a"))
I.AR("schlackenwams", "Schlackenwams", 3, "chest", "leder", 26, {"agi": 12, "sta": 10, "fire_res": 10}, bind="bop", vis=_V(c="#3a2a26"))
I.AR("ambossschild", "Amboss-Schild", 3, "off_hand", "schild", 26, {"sta": 11, "str": 5, "fire_res": 10}, bind="bop",
     vis=_V(c="#3a3436", m="#6a5a58", a="#ff7a20"))
I.AR("glutring", "Ring der Glut", 3, "ring", "schmuck", 26, {"str": 6, "agi": 6, "sta": 6})
I.AR("funkenamulett", "Funkenamulett", 3, "neck", "schmuck", 26, {"int": 7, "sp": 10, "fire_res": 8})
I.AR("hitzeschutzhandschuhe", "Hitzeschutzhandschuhe", 3, "hands", "stoff", 26, {"int": 8, "sp": 9, "fire_res": 12}, bind="bop")
# Endboss (episch)
I.W("ambossherz_hammer", "Ambossherz", 4, "kriegshammer", 28, (80, 120), 3.6, {"str": 18, "sta": 14}, bind="bop",
    desc="Der Kern pocht noch immer im Takt eines Schmiedehammers.", vis=_V(m="#3a3436", a="#ff7a20", g="#ff6a1a"),
    proc={"chance": 0.08, "dmg": {"school": "fire", "base": (60, 8, 90, 10)}, "name": "Schmiedeschlag"})
I.W("flammenzunge", "Flammenzunge", 4, "schwert", 28, (52, 90), 2.6, {"str": 13, "agi": 8, "sta": 10}, bind="bop",
    vis=_V(m="#6a3a20", a="#ff9a40", g="#ff6a1a"))
I.W("stab_der_ewigen_glut", "Stab der ewigen Glut", 4, "stab", 28, (50, 84), 3.0, {"int": 16, "spi": 10, "sp": 28}, bind="bop",
    vis=_V(w="#2a1a14", g="#ff6a1a"))
I.W("ambossherz_bogen", "Kern-Langbogen", 4, "bogen", 28, (54, 94), 2.8, {"agi": 16, "sta": 10}, bind="bop", vis=_V(w="#2a1a14", g="#ff6a1a"))

ZONE = {
    "id": "schmiede", "name": "Die Schwarze Schmiede", "type": "dungeon", "theme": "dungeon", "style": "schmiede",
    "levels": [20, 30], "max_players": 5, "players_text": "3 bis 5 Spieler", "recommended": 25,
    "start": [0.0, 2.0, N], "exit": ["frostklamm", 170.0, -170.0, SW],
    "modes": ["normal", "heroisch", "mythisch"], "music": "dungeon",
    "rects": [
        [-8, -8, 8, 8],            # Torhalle
        [-3, -34, 3, -8],          # Rampe
        [-22, -70, 22, -34],       # Gießerei
        [22, -58, 50, -50],        # Erzgang
        [50, -86, 86, -40],        # Schlackengrube
        [64, -118, 72, -86],       # Kettenbrücke
        [40, -160, 96, -118],      # Golemwerkstatt
        [10, -144, 40, -136],      # Gang zur Esse
        [-40, -176, 10, -110],     # Große Esse
    ],
    "rooms": [
        {"name": "Torhalle", "rect": 0}, {"name": "Gießerei", "rect": 2}, {"name": "Schlackengrube", "rect": 4},
        {"name": "Golemwerkstatt", "rect": 6}, {"name": "Die Große Esse", "rect": 8},
    ],
    "pools": [
        {"x": 0, "z": -52, "r": 6, "lava": True}, {"x": 68, "z": -63, "r": 7, "lava": True},
        {"x": -15, "z": -143, "r": 5, "lava": True}, {"x": 58, "z": -150, "r": 4, "lava": True},
        {"x": 82, "z": -128, "r": 4, "lava": True},
    ],
    "props": [
        {"t": "stairs", "x": 0, "z": 8, "r": S},
        {"t": "anvil", "x": -14, "z": -40, "r": E}, {"t": "anvil", "x": 14, "z": -40, "r": W},
        {"t": "anvil", "x": -14, "z": -64, "r": E}, {"t": "anvil", "x": 14, "z": -64, "r": W},
        {"t": "brazier", "x": -6, "z": -4}, {"t": "brazier", "x": 6, "z": -4},
        {"t": "brazier", "x": -18, "z": -52}, {"t": "brazier", "x": 18, "z": -52},
        {"t": "orepile", "x": 30, "z": -55}, {"t": "orepile", "x": 44, "z": -53}, {"t": "minecart", "x": 36, "z": -54, "r": E},
        {"t": "rails", "x1": 24, "z1": -54, "x2": 50, "z2": -54},
        *[{"t": "pillar", "x": x, "z": z, "dark": True} for x, z in [(54, -44), (82, -44), (54, -82), (82, -82),
                                                                     (44, -122), (92, -122), (44, -156), (92, -156)]],
        {"t": "weaponrack", "x": 94, "z": -138, "r": W}, {"t": "weaponrack", "x": 94, "z": -146, "r": W},
        {"t": "anvil", "x": 60, "z": -140, "r": S}, {"t": "anvil", "x": 76, "z": -140, "r": S},
        {"t": "orepile", "x": 48, "z": -126}, {"t": "orepile", "x": 88, "z": -152},
        *[{"t": "pillar", "x": round(-15 + 18 * math.cos(a), 1), "z": round(-143 + 22 * math.sin(a), 1), "big": True, "dark": True}
          for a in [i * math.pi / 3 + math.pi / 6 for i in range(6)]],
        {"t": "anvil", "x": -15, "z": -128, "r": S, "scale": 2.5},
        {"t": "brazier", "x": -34, "z": -116}, {"t": "brazier", "x": 4, "z": -116},
        {"t": "brazier", "x": -34, "z": -170}, {"t": "brazier", "x": 4, "z": -170},
    ],
    "traps": [
        {"x": 0, "z": -18, "r": 1.8, "name": "Funkenfalle", "flat": 140, "school": "fire", "fx": "fire", "cd": 5},
        {"x": 0, "z": -28, "r": 1.8, "name": "Funkenfalle", "flat": 140, "school": "fire", "fx": "fire", "cd": 5},
        {"x": 68, "z": -96, "r": 1.8, "name": "Dampfventil", "flat": 160, "school": "fire", "fx": "fire", "cd": 6},
        {"x": 68, "z": -108, "r": 1.8, "name": "Dampfventil", "flat": 160, "school": "fire", "fx": "fire", "cd": 6},
        {"x": 25, "z": -140, "r": 1.8, "name": "Funkenfalle", "flat": 170, "school": "fire", "fx": "fire", "cd": 5},
    ],
    "boss_order": ["schlackenschlund", "essenmeisterin_brenna", "ambossherz"],
}

NPCS = {}

_DW = {"kind": "dwarf", "skin": "#5a4a48", "hair": "#1a1a1a", "beard": "#1a1a1a", "eye_glow": "#ff8a30"}

MOBS = {
    "schwarzeisen_waechter": {"name": "Schwarzeisen-Wächter", "lvl": [24, 26], "family": "zwerg", "model": "humanoid",
                              "look": {**_DW, "top": "#2a2224", "bottom": "#1a1a1a", "armor": True, "helm": True, "held": "axe2h"},
                              "hp_mult": 1.6, "dmg_mult": 1.15, "armor_mult": 1.5, "aggro": True, "radius": 0.6, "social": 14,
                              "copper": [60, 110], "cloth": "seidenstoff", "world_drop": 0.12,
                              "abilities": [{"id": "spalten", "name": "Spalten", "kind": "telegraph_cone", "cd": 12, "first": 5,
                                             "radius": 6, "angle": 70, "warn": 1.5, "mult": 2.0}]},
    "schwarzeisen_schmied": {"name": "Schwarzeisen-Schmied", "lvl": [24, 26], "family": "zwerg", "model": "humanoid",
                             "look": {**_DW, "top": "#3a2a26", "bottom": "#1a1a1a", "apron": "#2a1a10", "held": "hammer", "bare_arms": True},
                             "hp_mult": 1.3, "dmg_mult": 1.1, "aggro": True, "radius": 0.6, "social": 14, "copper": [60, 110],
                             "cloth": "seidenstoff", "world_drop": 0.12,
                             "abilities": [{"id": "glutschlag", "name": "Glühender Hammer", "kind": "strike", "cd": 9, "first": 3, "mult": 1.6,
                                            "school": "fire",
                                            "debuff": {"id": "verbrannt", "name": "Verbrannt", "debuff": True, "dur": 6,
                                                       "dot": {"school": "fire", "interval": 2, "mult": 0.2}}}]},
    "schwarzeisen_feuerweber": {"name": "Schwarzeisen-Feuerweber", "lvl": [25, 26], "family": "zwerg", "model": "humanoid",
                                "look": {**_DW, "top": "#5a1a10", "robe": True, "held": "staff"},
                                "hp_mult": 1.0, "dmg_mult": 1.0, "aggro": True, "radius": 0.6, "social": 14, "copper": [60, 110],
                                "cloth": "seidenstoff", "world_drop": 0.12, "resist": {"fire": 0.6},
                                "ranged": {"range": 30, "name": "Glutblitz", "school": "fire", "cd": 3.0, "cast": 2.2, "mult": 2.1},
                                "abilities": [{"id": "feuerwelle", "name": "Feuerwelle", "kind": "cast", "cd": 15, "first": 6, "cast": 3.0,
                                               "range": 30, "school": "fire", "mult": 3.0, "aoe": 10, "icon": "fire"}]},
    "glutwichtel": {"name": "Glutwichtel", "lvl": [23, 24], "family": "elementar", "model": "fire_elemental", "scale": 0.5,
                    "hp_mult": 0.45, "dmg_mult": 0.7, "aggro": True, "radius": 0.4, "social": 10, "resist": {"fire": 0.9, "frost": -0.5},
                    "loot": []},
    "schmiedegolem": {"name": "Schmiedegolem", "lvl": [25, 26], "family": "mechanisch", "model": "forge_golem", "scale": 1.2,
                      "hp_mult": 2.6, "dmg_mult": 1.25, "armor_mult": 1.8, "aggro": True, "radius": 1.2, "elite": True, "social": 14,
                      "resist": {"fire": 0.7, "frost": -0.3, "physical": 0.15},
                      "loot": [{"item": "schmiedekern", "chance": 0.25}, {"item": "eisenbarren", "chance": 0.4}],
                      "abilities": [{"id": "dampfstoss", "name": "Dampfstoß", "kind": "telegraph_circle_self", "cd": 13, "first": 5,
                                     "radius": 6, "warn": 1.8, "mult": 2.0, "school": "fire"}]},
    # ---------------------------------------------------------------- Boss 1
    "schlackenschlund": {
        "name": "Schlackenschlund", "title": "Der Unersättliche", "lvl": [26, 26], "family": "elementar", "model": "slime", "scale": 3.0,
        "look": {"tint": "#3a2a26", "glow": "#ff6a1a"}, "hp_mult": 5.5, "dmg_mult": 1.3, "aggro": True, "radius": 2.4,
        "elite": True, "boss": True, "mini_boss": True, "copper": [600, 900], "aggro_radius": 16, "resist": {"fire": 0.9, "frost": -0.5},
        "boss_loot": {"pool": ["schlackenwams", "russgeschwaerzte_robe", "glutring", "sf_handschuhe", "hitzeschutzhandschuhe", "russdolch"], "n": 1},
        "abilities": [
            {"id": "schlackenspritzer", "name": "Schlackenspritzer", "kind": "telegraph_random", "cd": 9, "first": 4, "count": 6,
             "radius": 3.5, "spread": 14, "warn": 1.8, "flat": 260, "school": "fire"},
            {"id": "verschlingen", "name": "Verschlingen", "kind": "telegraph_cone", "cd": 14, "first": 8, "radius": 9, "angle": 80,
             "warn": 1.8, "mult": 3.0, "school": "fire"},
            {"id": "schlackenkinder", "name": "Schlacke spalten", "kind": "summon", "cd": 25, "first": 14, "summon": "glutwichtel",
             "count": 3, "yell": "*Blubb* ... *BLUBB*"},
        ],
        "aggro_yell": "*Die Schlacke wölbt sich hungrig auf*",
    },
    # ---------------------------------------------------------------- Boss 2
    "essenmeisterin_brenna": {
        "name": "Brenna Rußhand", "title": "Essenmeisterin", "lvl": [27, 27], "family": "zwerg", "model": "humanoid", "scale": 1.35,
        "look": {**_DW, "body": "f", "hair": "#ff6a1a", "hair_style": "braid", "beard": None, "top": "#3a1a10", "bottom": "#1a1a1a",
                 "armor": True, "held": "hammer", "shield": True, "aura": "#ff6a1a"},
        "hp_mult": 5.0, "dmg_mult": 1.35, "aggro": True, "radius": 0.9, "elite": True, "boss": True, "mini_boss": True,
        "copper": [600, 900], "aggro_radius": 18, "resist": {"fire": 0.5}, "power": True,
        "boss_loot": {"pool": ["glutklinge", "essenstab", "funkenbogen", "glutkatana", "schmiedeaxt", "ambossschild", "funkenamulett",
                               "sf_helm", "sf_beine"], "n": 1},
        "abilities": [
            {"id": "geschmolzener_stahl", "name": "Geschmolzener Stahl", "kind": "cast", "cd": 15, "first": 7, "cast": 3.0, "range": 40,
             "school": "fire", "mult": 4.5, "aoe": 40, "icon": "fire"},
            {"id": "hammerwurf", "name": "Hammerwurf", "kind": "telegraph_line", "cd": 11, "first": 4, "length": 22, "width": 3,
             "warn": 1.5, "mult": 2.6},
            {"id": "golem_erwecken", "name": "Golem erwecken", "kind": "summon", "cd": 40, "first": 20, "summon": "schmiedegolem",
             "count": 1, "yell": "Erhebe dich, mein Werk! Zermalme sie!"},
        ],
        "aggro_yell": "Wer stört meine Esse? Ihr werdet hervorragende Schlacke abgeben!",
        "death_yell": "Mein Meister ... wird ... euch ... einschmelzen ...",
    },
    # ---------------------------------------------------------------- Endboss
    "ambossherz": {
        "name": "Glutmeister Ambossherz", "title": "Herz der Schwarzen Schmiede", "lvl": [28, 28], "family": "mechanisch",
        "model": "forge_golem", "scale": 2.6, "hp_mult": 9.0, "dmg_mult": 1.45, "armor_mult": 1.6, "aggro": True, "radius": 2.6,
        "elite": True, "boss": True, "final_boss": True, "copper": [1500, 2200], "leash": 999, "aggro_radius": 20,
        "resist": {"fire": 0.9, "frost": -0.35},
        "loot": [{"item": "ambossherz_kern", "chance": 1.0}, {"item": "schmiedekern", "chance": 1.0}],
        "boss_loot": {"pool": ["ambossherz_hammer", "flammenzunge", "stab_der_ewigen_glut", "ambossherz_bogen", "sf_brust", "sf_helm",
                               "sf_beine", "sf_handschuhe", "schlackenbrecher"], "n": 2},
        "phases": [
            {"hp": 1.0, "abilities": [
                {"id": "ambossschlag", "name": "Ambossschlag", "kind": "telegraph_cone", "cd": 11, "first": 6, "radius": 12, "angle": 90,
                 "warn": 1.8, "mult": 3.0},
                {"id": "funkenregen", "name": "Funkenregen", "kind": "telegraph_circles_players", "cd": 12, "first": 3, "radius": 4,
                 "warn": 2.0, "flat": 320, "school": "fire", "count": 3}]},
            {"hp": 0.65, "name": "Die Esse brennt", "yell": "DIE ESSE BRENNT! SCHÜRT DAS FEUER, MEINE KINDER!",
             "on_enter": [{"kind": "summon", "summon": "glutwichtel", "count": 4},
                          {"kind": "hazards", "name": "Glühende Schlacke", "radius": 4, "flat": 140, "school": "fire", "fx": "fire",
                           "points": [[-14, 14], [14, -14], [-14, -14], [14, 14]]}],
             "abilities": [
                 {"id": "ambossschlag2", "name": "Ambossschlag", "kind": "telegraph_cone", "cd": 10, "first": 5, "radius": 12, "angle": 100,
                  "warn": 1.7, "mult": 3.2},
                 {"id": "glutring", "name": "Glutring", "kind": "telegraph_ring", "cd": 15, "first": 8, "radius": 20, "inner": 7,
                  "warn": 2.2, "flat": 380, "school": "fire"}]},
            {"hp": 0.3, "name": "Kernschmelze", "yell": "MEIN KERN ... SCHMILZT ... DANN SCHMELZT IHR MIT MIR!",
             "aura": {"id": "kernschmelze", "name": "Kernschmelze", "pct": {"dmg_done": 35, "haste": 20}, "dur": 3600},
             "abilities": [
                 {"id": "ambossschlag3", "name": "Ambossschlag", "kind": "telegraph_cone", "cd": 8, "first": 4, "radius": 13, "angle": 110,
                  "warn": 1.5, "mult": 3.4},
                 {"id": "funkenregen3", "name": "Funkenregen", "kind": "telegraph_circles_players", "cd": 8, "first": 2, "radius": 4,
                  "warn": 1.8, "flat": 360, "school": "fire", "count": 5},
                 {"id": "kernexplosion", "name": "Kernexplosion", "kind": "telegraph_circle_self", "cd": 20, "first": 10, "radius": 10,
                  "warn": 3.0, "mult": 4.0, "school": "fire"}]},
        ],
        "aggro_yell": "EINDRINGLINGE IN MEINER ESSE. IHR WERDET ... UMGESCHMIEDET.",
        "death_yell": "Das ... Feuer ... erlischt ...",
        "evade_yell": "Die Esse ruht ... für jetzt.",
    },
}

SPAWNS = [
    {"mob": "schwarzeisen_waechter", "pos": [-4, -4], "r": S}, {"mob": "schwarzeisen_waechter", "pos": [4, -4], "r": S},
    # Gießerei
    {"mob": "schwarzeisen_schmied", "pos": [-12, -42], "r": S}, {"mob": "schwarzeisen_schmied", "pos": [12, -42], "r": S},
    {"mob": "schwarzeisen_feuerweber", "pos": [-16, -60], "r": S}, {"mob": "schwarzeisen_feuerweber", "pos": [16, -60], "r": S},
    {"mob": "schwarzeisen_waechter", "pos": [0, -64], "r": S}, {"mob": "glutwichtel", "pos": [-6, -48]}, {"mob": "glutwichtel", "pos": [6, -48]},
    # Erzgang & Schlackengrube
    {"mob": "schwarzeisen_waechter", "pos": [36, -54], "r": W},
    {"mob": "glutwichtel", "pos": [56, -46]}, {"mob": "glutwichtel", "pos": [60, -50]}, {"mob": "glutwichtel", "pos": [78, -46]},
    {"mob": "schwarzeisen_feuerweber", "pos": [80, -78], "r": W}, {"mob": "schwarzeisen_schmied", "pos": [56, -78], "r": E},
    {"mob": "schlackenschlund", "pos": [68, -66], "r": N},
    # Golemwerkstatt
    {"mob": "schmiedegolem", "pos": [56, -130], "r": N}, {"mob": "schmiedegolem", "pos": [80, -130], "r": N},
    {"mob": "schwarzeisen_schmied", "pos": [50, -146], "r": E}, {"mob": "schwarzeisen_schmied", "pos": [86, -146], "r": W},
    {"mob": "schwarzeisen_feuerweber", "pos": [60, -154], "r": N}, {"mob": "schwarzeisen_feuerweber", "pos": [76, -154], "r": N},
    {"mob": "essenmeisterin_brenna", "pos": [68, -150], "r": N},
    # Große Esse
    {"mob": "schwarzeisen_waechter", "pos": [28, -140], "r": W}, {"mob": "schwarzeisen_waechter", "pos": [16, -140], "r": W},
    {"mob": "ambossherz", "pos": [-15, -150], "r": E},
]

OBJECTS = [
    {"kind": "chest", "pos": [-34, -164], "tier": 3, "name": "Truhe des Glutmeisters", "boss_chest": "ambossherz"},
]
