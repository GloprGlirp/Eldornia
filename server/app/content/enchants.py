"""Verzauberungen (Beruf Verzauberkunst): dauerhafte Runen auf Waffen und Rüstungen."""

ENCHANTS = {
    # Waffen
    "w_kraft_1": {"name": "Rune der Kraft I", "slots": ["main_hand"], "stats": {"str": 3}, "skill": 20},
    "w_flinkheit_1": {"name": "Rune der Flinkheit I", "slots": ["main_hand"], "stats": {"agi": 3}, "skill": 25},
    "w_zauber_1": {"name": "Rune der Zaubermacht I", "slots": ["main_hand"], "stats": {"sp": 5}, "skill": 30},
    "w_kraft_2": {"name": "Rune der Kraft II", "slots": ["main_hand"], "stats": {"str": 8}, "skill": 110},
    "w_flinkheit_2": {"name": "Rune der Flinkheit II", "slots": ["main_hand"], "stats": {"agi": 8}, "skill": 115},
    "w_zauber_2": {"name": "Rune der Zaubermacht II", "slots": ["main_hand"], "stats": {"sp": 14}, "skill": 120},
    "w_kraft_3": {"name": "Rune der Kraft III", "slots": ["main_hand"], "stats": {"str": 16}, "skill": 200},
    "w_flinkheit_3": {"name": "Rune der Flinkheit III", "slots": ["main_hand"], "stats": {"agi": 16}, "skill": 205},
    "w_zauber_3": {"name": "Rune der Zaubermacht III", "slots": ["main_hand"], "stats": {"sp": 28}, "skill": 210},
    "w_feuerzunge": {"name": "Rune der Feuerzunge", "slots": ["main_hand"], "stats": {"ap": 30, "sp": 15}, "skill": 260},
    # Brust
    "c_leben_1": {"name": "Rune des Lebens I", "slots": ["chest"], "stats": {"sta": 4}, "skill": 15},
    "c_leben_2": {"name": "Rune des Lebens II", "slots": ["chest"], "stats": {"sta": 10}, "skill": 100},
    "c_leben_3": {"name": "Rune des Lebens III", "slots": ["chest"], "stats": {"sta": 20}, "skill": 190},
    "c_alle_3": {"name": "Rune der Werte", "slots": ["chest"], "stats": {"str": 6, "agi": 6, "sta": 6, "int": 6, "spi": 6}, "skill": 240},
    # Umhang
    "b_schutz_1": {"name": "Rune des Schutzes I", "slots": ["back"], "stats": {"armor": 40}, "skill": 35},
    "b_schutz_2": {"name": "Rune des Schutzes II", "slots": ["back"], "stats": {"armor": 120, "fire_res": 10}, "skill": 140},
    "b_feuer": {"name": "Rune des Feuerschutzes", "slots": ["back"], "stats": {"fire_res": 25}, "skill": 210},
    # Handschuhe / Stiefel
    "h_kraft_1": {"name": "Rune der Hände I", "slots": ["hands"], "stats": {"str": 3, "agi": 3}, "skill": 50},
    "h_kraft_2": {"name": "Rune der Hände II", "slots": ["hands"], "stats": {"str": 7, "agi": 7}, "skill": 160},
    "f_tempo_1": {"name": "Rune der Schritte I", "slots": ["feet"], "stats": {"sta": 4, "agi": 2}, "skill": 60},
    "f_tempo_2": {"name": "Rune der Schritte II", "slots": ["feet"], "stats": {"sta": 10, "agi": 5}, "skill": 170},
    # Schild
    "s_block_1": {"name": "Rune des Blockens", "slots": ["off_hand"], "stats": {"block": 2, "sta": 4}, "skill": 80},
}
