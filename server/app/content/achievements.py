"""Erfolge (GDD 7): belohnen Erkundung, Bosskills und besondere Herausforderungen.

cond:
  {"counter": <zähler>, "n": n}          – Zähler des Charakters (kills, quests, deaths, gold_looted ...)
  {"kill": <mob_id>}                    – bestimmten Gegner besiegt
  {"kill_any": [ids], "n": n}            – n verschiedene der genannten Gegner besiegt
  {"explore": <zone_id>}                – alle Unterzonen einer Region entdeckt
  {"level": n}                          – Charakterstufe erreicht
  {"quest": <quest_id>}                  – Quest abgeschlossen
  {"prof": <beruf>, "n": n}              – Berufsfertigkeit erreicht
  {"rep": <fraktion>, "standing": <Name>}
  {"collect": "mounts"|"pets"|"titles"|"skins", "n": n}
  {"dungeon": <boss_id>, "mode": "heroic"|"mythic"}
"""

A = []


def ach(aid, name, desc, cond, points=10, icon="trophy", cat="Allgemein", title=None, item=None, hidden=False):
    A.append({"id": aid, "name": name, "desc": desc, "cond": cond, "points": points, "icon": icon, "cat": cat,
              "title": title, "item": item, "hidden": hidden})


# ------------------------------------------------------------------ Stufen
for _n in (10, 20, 30, 40, 50):
    ach(f"stufe_{_n}", f"Stufe {_n}", f"Erreicht Stufe {_n}.", {"level": _n}, 10 if _n < 50 else 25, "level-three", "Charakter")
# ------------------------------------------------------------------ Kampf
ach("erster_sieg", "Der erste Schritt", "Besiegt Euren ersten Gegner.", {"counter": "kills", "n": 1}, 5, "sword-wound", "Kampf")
ach("kills_100", "Monsterjäger", "Besiegt 100 Gegner.", {"counter": "kills", "n": 100}, 10, "crossed-swords", "Kampf")
ach("kills_1000", "Monsterschlächter", "Besiegt 1000 Gegner.", {"counter": "kills", "n": 1000}, 20, "crossed-swords", "Kampf")
ach("kills_10000", "Geißel der Monster", "Besiegt 10.000 Gegner.", {"counter": "kills", "n": 10000}, 50, "crossed-swords", "Kampf")
ach("wolfsjaeger", "Wolfsjäger", "Besiegt 50 Wölfe in der Grünmark.", {"counter": "kills_wolf", "n": 50}, 10, "wolf-head", "Kampf",
    title="wolfsjaeger")
ach("interrupts_50", "Halt den Mund!", "Unterbrecht 50 gegnerische Zauber.", {"counter": "interrupts", "n": 50}, 10, "silenced", "Kampf")
ach("tod_10", "Stammgast bei Bruder Anselm", "Sterbt 10-mal.", {"counter": "deaths", "n": 10}, 5, "dead-head", "Kampf", hidden=True)
ach("kopfgeld_10", "Kopfgeldjäger", "Erfüllt 10 Kopfgeldaufträge.", {"counter": "bounties", "n": 10}, 15, "wanted-reward", "Kampf",
    title="kopfgeldjaeger")
ach("rare_5", "Seltene Beute", "Besiegt 5 verschiedene seltene Gegner.",
    {"kill_any": ["graumaehne", "einohr", "goldbart", "eisbart_der_alte", "frostkralle", "silbergeweih", "dornenkoenigin",
                  "glutschuppe", "schattenkrallen", "sturmfeder", "himmelsleviathan"], "n": 5}, 20, "trophy-cup", "Kampf")
# ------------------------------------------------------------------ Dungeons & Bosse
ach("krypta", "Ruhe für Morgrath", "Besiegt Sir Morgrath in der vergessenen Krypta.", {"kill": "morgrath"}, 10, "crypt", "Dungeons",
    title="kryptenwaechter")
ach("krypta_hero", "Ruhe für Morgrath (Heroisch)", "Besiegt Sir Morgrath auf heroischem Schwierigkeitsgrad.",
    {"dungeon": "morgrath", "mode": "heroic"}, 15, "crypt", "Dungeons")
ach("schmiede", "Kalte Esse", "Besiegt den Schmiedegolem Ambossherz in der Schwarzen Schmiede.", {"kill": "ambossherz"}, 15,
    "anvil-impact", "Dungeons", title="schmiedebezwinger")
ach("schmiede_mythic", "Kalte Esse (Mythisch)", "Besiegt Ambossherz auf mythischem Schwierigkeitsgrad.",
    {"dungeon": "ambossherz", "mode": "mythic"}, 25, "anvil-impact", "Dungeons")
ach("kathedrale", "Erlösung", "Besiegt die Verdammte Äbtissin Seraphine in der Kathedrale der Verdammten.", {"kill": "seraphine"}, 20,
    "church", "Dungeons", title="erloeser")
ach("kathedrale_mythic", "Erlösung (Mythisch)", "Besiegt Seraphine auf mythischem Schwierigkeitsgrad.",
    {"dungeon": "seraphine", "mode": "mythic"}, 30, "church", "Dungeons")
ach("weltenbrecher", "Der Thron fällt", "Besiegt Kael'thar, den Weltenbrecher.", {"kill": "weltenbrecher"}, 50, "crowned-skull",
    "Raids", title="weltenbrecher")
ach("weltenbrecher_mythic", "Der Thron fällt (Mythisch)", "Besiegt den Weltenbrecher auf mythischem Schwierigkeitsgrad.",
    {"dungeon": "weltenbrecher", "mode": "mythic"}, 100, "crowned-skull", "Raids", item="reittier_weltenbrecher_ross")
ach("varkor", "Drachentöter", "Besiegt Varkor, den Aschendrachen.", {"kill": "varkor"}, 25, "dragon-head", "Weltbosse",
    title="drachentoeter")
ach("mutterborke", "Holzfäller", "Besiegt Mutterborke, die Uralte Eiche.", {"kill": "mutterborke"}, 10, "oak", "Weltbosse")
ach("eisbart", "Kalt erwischt", "Besiegt Hrimgar den Eisriesenkönig.", {"kill": "hrimgar"}, 15, "frozen-orb", "Weltbosse")
ach("weltbosse_alle", "Weltenbummler mit Schwert", "Besiegt alle Weltbosse Eldornias.",
    {"kill_any": ["mutterborke", "hrimgar", "dornenkoenigin", "varkor", "sturmfuerst"], "n": 5}, 50, "world", "Weltbosse")
# ------------------------------------------------------------------ Erkundung
for _z, _n in (("gruenmark", "Grünmark"), ("frostklamm", "Frostklamm"), ("mondhain", "Mondhain"), ("aschenlande", "Aschenlande"),
               ("himmelsbruch", "Himmelsbruch")):
    ach(f"erkunde_{_z}", f"Erkundet: {_n}", f"Entdeckt alle Gebiete der Region {_n}.", {"explore": _z}, 10, "compass", "Erkundung")
ach("entdecker", "Entdecker Eldornias", "Erkundet alle Regionen Eldornias.",
    {"all": ["erkunde_gruenmark", "erkunde_frostklamm", "erkunde_mondhain", "erkunde_aschenlande", "erkunde_himmelsbruch"]}, 30,
    "world", "Erkundung", title="entdecker")
ach("schatz_5", "Schatzsucher", "Öffnet 5 versteckte Schatztruhen.", {"counter": "chests", "n": 5}, 10, "open-treasure-chest", "Erkundung")
ach("schatz_25", "Schatzjäger", "Öffnet 25 versteckte Schatztruhen.", {"counter": "chests", "n": 25}, 20, "open-treasure-chest", "Erkundung")
ach("hoehle_einauge", "Was der Einäugige verbirgt", "Findet die geheime Höhle in der Grünmark.", {"counter": "secret_gruenmark", "n": 1},
    10, "cave-entrance", "Erkundung", hidden=True)
ach("teleport_alle", "Steinreich", "Aktiviert alle Teleportationssteine.", {"counter": "stones", "n": 14}, 15, "portal", "Erkundung")
# ------------------------------------------------------------------ Quests
for _n, _pts in ((10, 5), (50, 10), (150, 20), (300, 30)):
    ach(f"quests_{_n}", f"{_n} Quests", f"Schließt {_n} Quests ab.", {"counter": "quests", "n": _n}, _pts, "scroll-quill", "Quests")
ach("dailies_30", "Pflichtbewusst", "Schließt 30 tägliche Aufträge ab.", {"counter": "dailies", "n": 30}, 15, "calendar", "Quests")
ach("held_eldornias", "Held Eldornias", "Schließt die Hauptgeschichte der Grünmark ab.", {"quest": "der_herrscher_muss_es_wissen"}, 15,
    "laurel-crown", "Quests", title="held_eldornias")
ach("trottel", "Ein Herz für Trottel", "Helft dem Dorftrottel bei all seinen Sorgen.", {"quest": "trottels_grosser_tag"}, 10, "jester-hat",
    "Quests", title="freund_des_trottels", hidden=True)
# ------------------------------------------------------------------ Berufe
for _p, _pn in (("bergbau", "Bergbau"), ("kraeuterkunde", "Kräuterkunde"), ("schmiedekunst", "Schmiedekunst"),
                ("alchemie", "Alchemie"), ("lederverarbeitung", "Lederverarbeitung"), ("verzauberung", "Verzauberung")):
    ach(f"prof_{_p}_150", f"Geselle: {_pn}", f"Erreicht 150 Punkte in {_pn}.", {"prof": _p, "n": 150}, 10, "upgrade", "Berufe")
    ach(f"prof_{_p}_300", f"Meister: {_pn}", f"Erreicht 300 Punkte in {_pn}.", {"prof": _p, "n": 300}, 20, "upgrade", "Berufe")
ach("berufe_meister", "Meister der Berufe", "Erreicht 300 Punkte in allen sechs Berufen.",
    {"all": [f"prof_{p}_300" for p in ("bergbau", "kraeuterkunde", "schmiedekunst", "alchemie", "lederverarbeitung", "verzauberung")]},
    50, "trophy", "Berufe", title="meister_der_berufe")
ach("crafts_100", "Fleißige Hände", "Stellt 100 Gegenstände her.", {"counter": "crafts", "n": 100}, 10, "hammer-nails", "Berufe")
# ------------------------------------------------------------------ Wirtschaft & Soziales
ach("gold_100", "Wohlhabend", "Besitzt 100 Gold.", {"counter": "max_gold", "n": 100}, 10, "two-coins", "Wirtschaft")
ach("gold_10000", "Der Reiche", "Besitzt 10.000 Gold.", {"counter": "max_gold", "n": 10000}, 30, "gold-bar", "Wirtschaft", title="der_reiche")
ach("markt_10", "Händlerseele", "Verkauft 10 Gegenstände auf dem Marktplatz.", {"counter": "market_sales", "n": 10}, 10, "shop", "Wirtschaft")
ach("markt_100", "Marktbaron", "Verkauft 100 Gegenstände auf dem Marktplatz.", {"counter": "market_sales", "n": 100}, 20, "shop", "Wirtschaft")
ach("handel_1", "Handschlag", "Handelt mit einem anderen Spieler.", {"counter": "trades", "n": 1}, 5, "shaking-hands", "Soziales")
ach("gilde", "Gemeinsam stark", "Tretet einer Gilde bei.", {"counter": "guild_joined", "n": 1}, 5, "barbarian", "Soziales")
ach("gruppe_dungeon", "Teamgeist", "Schließt einen Dungeon über den Gruppenfinder ab.", {"counter": "finder_dungeons", "n": 1}, 10,
    "team-idea", "Soziales")
# ------------------------------------------------------------------ Ruf
for _f, _fn in (("krone", "Krone von Eldenstein"), ("eisenbart", "Eisenbart-Klan"), ("mondzirkel", "Zirkel des Mondes"),
                ("aschenwacht", "Die Aschenwacht"), ("himmelswaechter", "Wächter des Himmelsbruchs")):
    ach(f"ruf_{_f}", f"Ehrfürchtig: {_fn}", f"Erreicht den Ruf Ehrfürchtig bei {_fn}.", {"rep": _f, "standing": "Ehrfürchtig"}, 20,
        "laurels", "Ruf", title={"krone": "ritter_der_krone", "eisenbart": "freund_der_zwerge", "mondzirkel": "huter_des_hains",
                                 "aschenwacht": "aschenwacht", "himmelswaechter": "himmelswanderer"}[_f])
# ------------------------------------------------------------------ Sammlungen
ach("mount_1", "Hoch zu Ross", "Lernt Euer erstes Reittier.", {"collect": "mounts", "n": 1}, 10, "horse-head", "Sammlungen")
ach("mount_5", "Stallmeister", "Sammelt 5 Reittiere.", {"collect": "mounts", "n": 5}, 20, "horse-head", "Sammlungen")
ach("pets_5", "Tierfreund", "Sammelt 5 Haustiere.", {"collect": "pets", "n": 5}, 10, "paw", "Sammlungen")
ach("sammler", "Sammler", "Sammelt 10 Reittiere und 8 Haustiere.", {"all": ["mount_10", "pets_8"]}, 30, "chest", "Sammlungen", title="sammler")
ach("mount_10", "Herr der Ställe", "Sammelt 10 Reittiere.", {"collect": "mounts", "n": 10}, 25, "horse-head", "Sammlungen")
ach("pets_8", "Zoo-Direktor", "Sammelt 8 Haustiere.", {"collect": "pets", "n": 8}, 20, "paw", "Sammlungen")
# ------------------------------------------------------------------ PvP
ach("duell_1", "Fehdehandschuh", "Gewinnt ein Duell.", {"counter": "duels_won", "n": 1}, 5, "gauntlet", "PvP")
ach("duell_50", "Duellant", "Gewinnt 50 Duelle.", {"counter": "duels_won", "n": 50}, 15, "gauntlet", "PvP", title="duellant")
ach("arena_10", "Arenakämpfer", "Gewinnt 10 Arenakämpfe.", {"counter": "arena_wins", "n": 10}, 10, "crossed-swords", "PvP")
ach("arena_1800", "Gladiator", "Erreicht eine Arenawertung von 1800.", {"counter": "arena_rating", "n": 1800}, 30, "crossed-swords", "PvP",
    title="gladiator")
ach("pvp_kills_100", "Blutfeld-Veteran", "Besiegt 100 Spieler im offenen PvP-Gebiet.", {"counter": "pvp_kills", "n": 100}, 20,
    "skull-crossed-bones", "PvP")

ACHIEVEMENTS = {a["id"]: a for a in A}
CATEGORIES = []
for _a in A:
    if _a["cat"] not in CATEGORIES:
        CATEGORIES.append(_a["cat"])
