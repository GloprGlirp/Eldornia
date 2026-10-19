"""Die geheime Höhle des einäugigen Kobolds (versteckter Mini-Dungeon in der Grünmark, Stufe 8–11).

Der Eingang liegt hinter einem Wasserfall am Fuß des Nordost-Hügels. Wer die zerknitterte Schatzkarte
findet, erfährt davon. Hier haust Krummnase, der Rivale des einäugigen Kobolds.
"""
import math

from .. import items as I

N, S, E, W = 0.0, math.pi, -math.pi / 2, math.pi / 2

I.AR("einauges_glasauge", "Einauges Ersatzglasauge", 3, "neck", "schmuck", 10, {"agi": 4, "int": 4, "sta": 3, "crit": 0.5},
     icon="eye-target", desc="Es blinzelt manchmal. Von allein.", bind="bop")
I.AR("einauges_umhang", "Einauges Schmugglerumhang", 3, "back", "umhang", 10, {"agi": 5, "sta": 4, "dodge": 0.5},
     icon="cape", desc="Hat erstaunlich viele Innentaschen.", bind="bop", vis=I.V(c="#3a3a3a", a="#8a6a2a"))
I.W("krummnases_nasenbrecher", "Krummnases Nasenbrecher", 3, "streitkolben", 10, (14, 27), 2.7, {"str": 5, "sta": 3},
    desc="Die Delle stammt von Krummnases eigener Nase.", bind="bop", vis=I.V(m="#8a7a5a", a="#c9a040"))

ZONE = {
    "id": "hoehle_einauge", "name": "Krummnases Schmugglerhöhle", "type": "dungeon", "theme": "dungeon", "style": "hoehle",
    "levels": [8, 11], "max_players": 3, "players_text": "1–3 Spieler", "recommended": 9, "hidden": True,
    "start": [0.0, 1.0, N], "exit": ["gruenmark", 166.0, 148.0, S],
    "modes": ["normal"],
    "rects": [
        [-5, -5, 5, 5],
        [-2.5, -26, 2.5, -5],
        [-14, -46, 14, -26],
        [14, -40, 30, -34],
        [30, -54, 50, -24],
    ],
    "rooms": [{"name": "Wasserfallgrotte", "rect": 0}, {"name": "Schmugglerlager", "rect": 2}, {"name": "Krummnases Schatzkammer", "rect": 4}],
    "props": [
        {"t": "stairs", "x": 0, "z": 5, "r": S},
        {"t": "crate", "x": -10, "z": -30}, {"t": "crate", "x": -11.2, "z": -31.3}, {"t": "barrel", "x": 10, "z": -30},
        {"t": "barrel", "x": 11, "z": -31.5}, {"t": "campfire", "x": 0, "z": -36}, {"t": "candles", "x": -12, "z": -44},
        {"t": "candles", "x": 12, "z": -44}, {"t": "lantern", "x": 0, "z": -6},
        {"t": "orepile", "x": 46, "z": -28}, {"t": "orepile", "x": 34, "z": -50}, {"t": "candles", "x": 48, "z": -50},
        {"t": "crate", "x": 33, "z": -27}, {"t": "brazier", "x": 32, "z": -40}, {"t": "brazier", "x": 48, "z": -40},
    ],
    "boss_order": ["krummnase"],
}

NPCS = {}

MOBS = {
    "schmugglerkobold": {"name": "Schmugglerkobold", "lvl": [8, 9], "family": "humanoid", "model": "humanoid", "scale": 0.8,
                         "look": {"kind": "kobold", "skin": "#7a6a4a", "top": "#3a3a3a", "bottom": "#5a4a3a", "hood": True,
                                  "held": "dagger"},
                         "hp_mult": 1.0, "dmg_mult": 1.0, "aggro": True, "radius": 0.5, "social": 12, "copper": [10, 22],
                         "loot": [{"item": "kobold_kerze", "chance": 0.3}, {"item": "verbogener_loeffel", "chance": 0.4}],
                         "world_drop": 0.1, "aggro_say": ["Krummnase sagt: Keiner kommt rein!", "Das ist UNSER Gold!"]},
    "kobold_bombenwerfer": {"name": "Kobold-Bombenwerfer", "lvl": [9, 9], "family": "humanoid", "model": "humanoid", "scale": 0.82,
                            "look": {"kind": "kobold", "skin": "#8a6a3a", "top": "#6a3a2a", "bottom": "#4a3a2a", "hat": "mining"},
                            "hp_mult": 0.8, "dmg_mult": 0.8, "aggro": True, "radius": 0.5, "social": 12, "copper": [10, 22],
                            "abilities": [{"id": "pulverfass", "name": "Pulverfass", "kind": "telegraph_circles_players", "cd": 9,
                                           "first": 3, "radius": 3.0, "warn": 1.6, "flat": 55, "school": "fire", "count": 1}],
                            "loot": [{"item": "verbogener_loeffel", "chance": 0.4}], "world_drop": 0.1},
    "krummnase": {"name": "Krummnase", "title": "Schmugglerkönig", "lvl": [10, 10], "family": "humanoid", "model": "humanoid",
                  "scale": 1.15,
                  "look": {"kind": "kobold", "skin": "#9a7a4a", "top": "#8a2a5a", "bottom": "#3a2a3a", "crown": True, "held": "hammer",
                           "big_nose": True},
                  "hp_mult": 4.0, "dmg_mult": 1.2, "aggro": True, "radius": 0.8, "elite": True, "boss": True, "final_boss": True,
                  "copper": [400, 700], "aggro_radius": 14,
                  "loot": [{"item": "krummnases_schluessel", "chance": 1.0}],
                  "boss_loot": {"pool": ["krummnases_nasenbrecher", "einauges_umhang", "stollenhandschuhe", "kerzenwachshose"], "n": 1},
                  "phases": [
                      {"hp": 1.0, "abilities": [
                          {"id": "nasenstoss", "name": "Nasenstoß", "kind": "telegraph_line", "cd": 10, "first": 5, "radius": 14, "width": 3,
                           "warn": 1.4, "mult": 2.4, "knockback": 6}]},
                      {"hp": 0.5, "name": "Alle Mann an die Fässer!", "yell": "Jungs! Die Fässer! ALLE Fässer!",
                       "abilities": [
                           {"id": "fassregen", "name": "Fassregen", "kind": "telegraph_random", "cd": 8, "first": 2, "count": 6,
                            "radius": 3.0, "spread": 12, "warn": 1.6, "flat": 60, "school": "fire"},
                           {"id": "nasenstoss2", "name": "Nasenstoß", "kind": "telegraph_line", "cd": 9, "first": 5, "radius": 14,
                            "width": 3, "warn": 1.3, "mult": 2.6, "knockback": 6}]}],
                  "aggro_yell": "Einauge schickt dich, ja? Krummnase riecht Verrat! Mit seiner großen Nase!",
                  "death_yell": "Nicht ... die ... Nase ..."},
}

SPAWNS = [
    {"mob": "schmugglerkobold", "pos": [-6, -32], "r": S}, {"mob": "schmugglerkobold", "pos": [6, -32], "r": S},
    {"mob": "kobold_bombenwerfer", "pos": [0, -42], "r": S}, {"mob": "schmugglerkobold", "pos": [-9, -40], "r": E},
    {"mob": "schmugglerkobold", "pos": [20, -37], "r": E}, {"mob": "kobold_bombenwerfer", "pos": [26, -37], "r": E},
    {"mob": "schmugglerkobold", "pos": [34, -30], "r": E}, {"mob": "schmugglerkobold", "pos": [34, -48], "r": E},
    {"mob": "krummnase", "pos": [42, -39], "r": W},
]

OBJECTS = [
    {"kind": "chest", "pos": [47, -39], "tier": 2, "name": "Krummnases Schatztruhe", "needs_item": "krummnases_schluessel",
     "event": "chest_hoehle", "loot": [("kupferbarren", 4), ("rohquarz", 1)], "copper": 1500},
]
