"""Die vergessene Krypta – Dungeon (Stufe 8–15, solo oder 2 Spieler).

Skelette, Fallen und ein untoter Ritter als Endboss: Sir Morgrath, der Lehrmeister von Jonas.
"""
import math

N, S, E, W = 0.0, math.pi, -math.pi / 2, math.pi / 2

ZONE = {
    "id": "krypta", "name": "Die vergessene Krypta", "type": "dungeon", "theme": "dungeon", "style": "krypta",
    "levels": [8, 15], "max_players": 2, "players_text": "Solo oder 2 Spieler", "recommended": 10,
    "start": [0.0, 1.0, N], "exit": ["gruenmark", -122.0, 126.0, E],
    "modes": ["normal", "heroisch", "mythisch"],
    "rects": [
        [-6, -6, 6, 6],          # Eingangshalle
        [-3, -32, 3, -6],        # Gang 1 (Fallen)
        [-14, -56, 14, -32],     # Halle der Ruhelosen
        [14, -47, 42, -41],      # Gang 2
        [42, -62, 66, -26],      # Kammer der Knochenmagier
        [51, -92, 57, -62],      # Gang 3 (Fallen)
        [38, -118, 70, -92],     # Beinhaus
        [6, -108, 38, -102],     # Gang 4
        [-30, -132, 6, -80],     # Morgraths Gruft
    ],
    "rooms": [
        {"name": "Eingangshalle", "rect": 0}, {"name": "Halle der Ruhelosen", "rect": 2},
        {"name": "Kammer der Knochenmagier", "rect": 4}, {"name": "Beinhaus", "rect": 6},
        {"name": "Morgraths Gruft", "rect": 8},
    ],
    "props": [
        {"t": "stairs", "x": 0, "z": 6, "r": S},
        *[{"t": "pillar", "x": x, "z": z} for x, z in [(-9, -37), (9, -37), (-9, -51), (9, -51),
                                                      (46, -30), (62, -30), (46, -58), (62, -58),
                                                      (42, -96), (66, -96), (42, -114), (66, -114)]],
        *[{"t": "pillar", "x": round(-12 + 11 * math.cos(a), 2), "z": round(-106 + 13 * math.sin(a), 2), "big": True}
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
    ],
    # Fallen (GDD: "Skelette, Fallen ..."): Bodenplatten, die beim Betreten Klingen/Gift auslösen
    "traps": [
        {"x": 0, "z": -14, "r": 1.6, "name": "Klingenfalle", "flat": 45, "school": "physical", "fx": "blades", "cd": 4},
        {"x": 0, "z": -24, "r": 1.6, "name": "Klingenfalle", "flat": 45, "school": "physical", "fx": "blades", "cd": 4},
        {"x": 54, "z": -70, "r": 1.8, "name": "Giftgasfalle", "flat": 30, "school": "nature", "fx": "poison", "cd": 6,
         "debuff": {"id": "gruftgas", "name": "Gruftgas", "debuff": True, "dur": 8, "dot": {"school": "nature", "interval": 2, "flat": 12}}},
        {"x": 54, "z": -84, "r": 1.8, "name": "Giftgasfalle", "flat": 30, "school": "nature", "fx": "poison", "cd": 6,
         "debuff": {"id": "gruftgas", "name": "Gruftgas", "debuff": True, "dur": 8, "dot": {"school": "nature", "interval": 2, "flat": 12}}},
        {"x": 22, "z": -105, "r": 1.6, "name": "Klingenfalle", "flat": 55, "school": "physical", "fx": "blades", "cd": 4},
    ],
    "boss_order": ["grabwaechter_boss", "knochenfuerstin_vexa", "morgrath"],
}

NPCS = {}

MOBS = {
    "skelett": {"name": "Ruheloses Skelett", "lvl": [8, 9], "family": "untot", "model": "humanoid",
                "look": {"kind": "skeleton", "held": "sword", "eye_glow": "#7ab0ff"},
                "hp_mult": 1.1, "dmg_mult": 1.0, "aggro": True, "radius": 0.5, "social": 12, "copper": [10, 25],
                "resist": {"shadow": 0.25, "holy": -0.5},
                "loot": [{"item": "knochensplitter", "chance": 0.5}, {"item": "vergilbter_schaedel", "chance": 0.2}],
                "world_drop": 0.1},
    "skelett_schildtraeger": {"name": "Skelett-Schildträger", "lvl": [9, 9], "family": "untot", "model": "humanoid",
                              "look": {"kind": "skeleton", "held": "axe", "shield": True, "eye_glow": "#7ab0ff"},
                              "hp_mult": 1.4, "dmg_mult": 0.9, "armor_mult": 1.6, "aggro": True, "radius": 0.55, "social": 12,
                              "copper": [12, 26], "resist": {"shadow": 0.25, "holy": -0.5},
                              "abilities": [{"id": "schildhieb", "name": "Schildhieb", "kind": "strike", "cd": 12, "first": 4, "mult": 1.2,
                                             "debuff": {"id": "benommen", "name": "Benommen", "debuff": True, "slow": 0.5, "dur": 3}}],
                              "loot": [{"item": "knochensplitter", "chance": 0.5}], "world_drop": 0.1},
    "knochenmagier": {"name": "Knochenmagier", "lvl": [9, 9], "family": "untot", "model": "humanoid",
                      "look": {"kind": "skeleton", "held": "staff", "hood": True, "hood_color": "#2a2a3a", "eye_glow": "#c080ff"},
                      "hp_mult": 0.9, "dmg_mult": 0.9, "aggro": True, "radius": 0.5, "social": 12, "copper": [12, 28],
                      "resist": {"shadow": 0.5, "holy": -0.5},
                      "ranged": {"range": 28, "name": "Schattenblitz", "school": "shadow", "cd": 3.0, "cast": 2.5, "mult": 1.9},
                      "abilities": [{"id": "knochenschild", "name": "Knochenschild", "kind": "aura_self", "cd": 25, "first": 2,
                                     "aura": {"id": "knochenschild", "name": "Knochenschild", "pct": {"dmg_taken": -40}, "dur": 8}}],
                      "loot": [{"item": "knochensplitter", "chance": 0.5}, {"item": "knochenmagier_kappe", "chance": 0.08}],
                      "world_drop": 0.1},
    "gruftratte": {"name": "Gruftratte", "lvl": [8, 8], "family": "tier", "model": "fox", "scale": 0.5, "look": {"tint": "#5a5048", "tint2": "#8a7a70"},
                   "hp_mult": 0.4, "dmg_mult": 0.6, "aggro": True, "radius": 0.4, "social": 6, "loot": [],
                   "abilities": [{"id": "pestbiss", "name": "Pestbiss", "kind": "strike", "cd": 9, "first": 2, "mult": 0.8,
                                  "debuff": {"id": "pest", "name": "Gruftpest", "debuff": True, "dispel": "disease", "dur": 9,
                                             "dot": {"school": "nature", "interval": 3, "mult": 0.15}}}]},
    "grabwaechter": {"name": "Grabwächter", "lvl": [9, 9], "family": "untot", "model": "humanoid", "scale": 1.45,
                     "look": {"kind": "skeleton", "held": "axe2h", "armor": True, "helm": True, "eye_glow": "#7ab0ff"},
                     "hp_mult": 2.6, "dmg_mult": 1.3, "aggro": True, "radius": 0.9, "elite": True, "social": 12, "copper": [60, 90],
                     "resist": {"shadow": 0.25, "holy": -0.5},
                     "loot": [{"item": "grabwaechter_schultern", "chance": 0.3}, {"item": "umhang_grabesruhe", "chance": 0.3},
                              {"item": "wiedergaenger_stiefel", "chance": 0.25}, {"item": "ring_der_vergessenen", "chance": 0.15}],
                     "abilities": [{"id": "zerschmettern", "name": "Zerschmettern", "kind": "strike", "cd": 11, "first": 5, "mult": 2.0}]},
    # ---------------------------------------------------------------- Boss 1
    "grabwaechter_boss": {
        "name": "Knochenbrecher", "title": "Wächter der Halle", "lvl": [10, 10], "family": "untot", "model": "golem", "scale": 1.3,
        "look": {"tint": "#e6dcc0", "glow": "#7ab0ff"}, "hp_mult": 4.5, "dmg_mult": 1.2, "aggro": True, "radius": 1.4,
        "elite": True, "boss": True, "mini_boss": True, "copper": [200, 300], "aggro_radius": 14, "resist": {"holy": -0.5},
        "boss_loot": {"pool": ["grabwaechter_schultern", "wiedergaenger_stiefel", "gruftkettenhemd", "gruftschleicher_wams",
                               "kw_schultern"], "n": 1},
        "abilities": [
            {"id": "knochensturm", "name": "Knochensturm", "kind": "telegraph_circle_self", "cd": 15, "first": 8, "radius": 8,
             "warn": 2.0, "mult": 2.0, "school": "physical"},
            {"id": "beben", "name": "Beben", "kind": "telegraph_random", "cd": 11, "first": 4, "count": 5, "radius": 3.5,
             "spread": 12, "warn": 1.8, "flat": 70, "school": "physical"},
        ],
        "aggro_yell": "KNOCHEN ... ZU ... KNOCHEN!",
        "death_yell": "Zerfalle ... zu ... Staub ...",
    },
    # ---------------------------------------------------------------- Boss 2
    "knochenfuerstin_vexa": {
        "name": "Vexa", "title": "Knochenfürstin", "lvl": [10, 10], "family": "untot", "model": "humanoid", "scale": 1.15,
        "look": {"kind": "skeleton", "held": "staff", "hood": True, "hood_color": "#3a1a4a", "eye_glow": "#c080ff", "crown": True},
        "hp_mult": 4.0, "dmg_mult": 1.1, "aggro": True, "radius": 0.8, "elite": True, "boss": True, "mini_boss": True,
        "copper": [200, 300], "aggro_radius": 16, "resist": {"shadow": 0.6, "holy": -0.5}, "power": True,
        "ranged": {"range": 30, "name": "Schattenblitz", "school": "shadow", "cd": 2.5, "cast": 2.0, "mult": 1.6},
        "boss_loot": {"pool": ["knochenmagier_kappe", "leichentuchrobe", "robe_der_wachsamkeit", "ring_der_vergessenen",
                               "kw_helm"], "n": 1},
        "abilities": [
            # unterbrechbar! – Interrupts sind die Lösung
            {"id": "seelensog", "name": "Seelensog", "kind": "cast", "cd": 14, "first": 6, "cast": 3.0, "range": 40,
             "school": "shadow", "mult": 4.0, "aoe": 40, "icon": "skull"},
            {"id": "vexa_diener", "name": "Ruf der Gruft", "kind": "summon", "cd": 25, "first": 12, "summon": "erweckter", "count": 2,
             "yell": "Steht auf, meine Kinder!"},
            {"id": "schattennova", "name": "Schattennova", "kind": "telegraph_circle_self", "cd": 18, "first": 9, "radius": 9,
             "warn": 2.2, "mult": 2.2, "school": "shadow"},
        ],
        "aggro_yell": "Lebende? In meiner Kammer? Wie ... erfrischend.",
        "death_yell": "Morgrath ... wird ... mich ... rächen ...",
    },
    "erweckter": {"name": "Erweckter Diener", "lvl": [8, 8], "family": "untot", "model": "humanoid", "scale": 0.9,
                  "look": {"kind": "skeleton", "held": "sword", "eye_glow": "#7affc8"},
                  "hp_mult": 0.6, "dmg_mult": 0.7, "aggro": True, "radius": 0.5, "loot": [], "summoned": True},
    # ---------------------------------------------------------------- Endboss
    "morgrath": {
        "name": "Sir Morgrath", "title": "Der Gefallene", "lvl": [11, 11], "family": "untot", "model": "humanoid", "scale": 1.9,
        "look": {"kind": "human", "skin": "#8a9aa8", "hair": "#d8d8e0", "top": "#2a2a34", "bottom": "#1a1a22", "armor": True, "helm": True,
                 "cape": "#1a1a2a", "held": "sword2h", "eye_glow": "#7ab0ff", "aura": "#4a8aff"},
        "hp_mult": 7.0, "dmg_mult": 1.25, "aggro": True, "radius": 1.6, "elite": True, "boss": True, "final_boss": True,
        "copper": [500, 800], "leash": 999, "aggro_radius": 18, "resist": {"shadow": 0.4, "holy": -0.4},
        "loot": [{"item": "morgraths_siegel", "chance": 1.0}],
        "boss_loot": {"pool": ["morgraths_seelenklinge", "schild_des_gefallenen", "stab_verlorener_seelen", "morgraths_zweihaender",
                               "morgraths_bogen", "kapuze_der_grabesstille", "morgraths_helm", "maske_des_grabraeubers",
                               "kw_brust", "kw_helm"],
                      "n": 2, "legendary": "eldornias_traene", "legendary_chance": 0.02},
        "phases": [
            {"hp": 1.0, "abilities": [
                {"id": "grabesschlag", "name": "Grabesschlag", "kind": "telegraph_cone", "cd": 12, "first": 7, "radius": 10,
                 "angle": 100, "warn": 1.6, "mult": 3.0},
                {"id": "todesgriff", "name": "Todesgriff", "kind": "teleport", "cd": 20, "first": 15}]},
            {"hp": 0.6, "name": "Die treuen Diener", "yell": "Erhebt euch, meine treuen Diener! Verteidigt euren Herrn!",
             "on_enter": [{"kind": "summon", "summon": "erweckter", "count": 3}],
             "abilities": [
                 {"id": "grabesschlag2", "name": "Grabesschlag", "kind": "telegraph_cone", "cd": 11, "first": 5, "radius": 10,
                  "angle": 100, "warn": 1.5, "mult": 3.0},
                 {"id": "seelenfeuer", "name": "Seelenfeuer", "kind": "telegraph_circles_players", "cd": 9, "first": 2, "radius": 4,
                  "warn": 2.0, "flat": 110, "school": "shadow", "count": 2}]},
            {"hp": 0.3, "name": "Ewiger Zorn", "yell": "Ich habe diesen Ort tausend Jahre bewacht ... ich werde nicht fallen!",
             "aura": {"id": "ewiger_zorn", "name": "Ewiger Zorn", "pct": {"dmg_done": 40, "haste": 25}, "dur": 3600},
             "on_enter": [{"kind": "hazards", "name": "Seelenfeuer", "radius": 4, "flat": 60, "school": "shadow", "fx": "shadowfire",
                           "points": [[-12, 12], [12, -12], [-12, -12], [12, 12]]}],
             "abilities": [
                 {"id": "grabesschlag3", "name": "Grabesschlag", "kind": "telegraph_cone", "cd": 9, "first": 4, "radius": 11,
                  "angle": 110, "warn": 1.4, "mult": 3.2},
                 {"id": "seelenfeuer3", "name": "Seelenfeuer", "kind": "telegraph_circles_players", "cd": 7, "first": 2, "radius": 4,
                  "warn": 1.8, "flat": 130, "school": "shadow", "count": 3}]},
        ],
        "aggro_yell": "Wer stört meine ewige Wacht? Ihr werdet hier neben mir ruhen!",
        "death_yell": "Jonas ... mein Schüler ... vergib ... mir ...",
        "evade_yell": "Ruht in Frieden ... in meiner Krypta.",
    },
}

SPAWNS = [
    # Eingangshalle & Gang 1
    {"mob": "gruftratte", "pos": [-3, -2]}, {"mob": "gruftratte", "pos": [3, -3]},
    # Halle der Ruhelosen
    {"mob": "skelett", "pos": [-6, -38], "r": S}, {"mob": "skelett", "pos": [6, -38], "r": S},
    {"mob": "skelett_schildtraeger", "pos": [0, -42], "r": S},
    {"mob": "skelett", "pos": [-8, -48], "r": S}, {"mob": "knochenmagier", "pos": [8, -48], "r": S},
    {"mob": "grabwaechter_boss", "pos": [0, -52], "r": S},
    # Gang 2 & Kammer der Knochenmagier
    {"mob": "gruftratte", "pos": [22, -44]}, {"mob": "gruftratte", "pos": [28, -43]}, {"mob": "gruftratte", "pos": [34, -45]},
    {"mob": "knochenmagier", "pos": [48, -34], "r": W}, {"mob": "skelett", "pos": [50, -38], "r": W},
    {"mob": "knochenmagier", "pos": [60, -34], "r": W}, {"mob": "skelett_schildtraeger", "pos": [58, -40], "r": W},
    {"mob": "skelett", "pos": [48, -52], "r": N}, {"mob": "knochenmagier", "pos": [60, -52], "r": N},
    {"mob": "knochenfuerstin_vexa", "pos": [54, -58], "r": N},
    # Beinhaus
    {"mob": "grabwaechter", "pos": [54, -98], "r": N},
    {"mob": "skelett", "pos": [44, -106], "r": E}, {"mob": "skelett_schildtraeger", "pos": [64, -106], "r": W},
    {"mob": "knochenmagier", "pos": [46, -114], "r": N}, {"mob": "knochenmagier", "pos": [62, -114], "r": N},
    {"mob": "grabwaechter", "pos": [40, -104], "r": W},
    # Gang 4 & Gruft
    {"mob": "skelett", "pos": [30, -105], "r": W}, {"mob": "skelett", "pos": [14, -105], "r": W},
    {"mob": "morgrath", "pos": [-12, -106], "r": E},
]

OBJECTS = [
    {"kind": "chest", "pos": [-24, -126], "tier": 2, "name": "Morgraths Truhe", "boss_chest": "morgrath"},
]
