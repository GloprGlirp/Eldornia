"""Quests der Grünmark (Stufe 1–10) und der Vergessenen Krypta.

objectives:
  {"type": "kill",    "mob": <mob_id>,  "count": n}
  {"type": "collect", "item": <item_id>, "count": n}   (Questgegenstände droppen nur, solange benötigt)
Ohne objectives ist es eine Botenquest (Abgabe beim "ender").

rewards: xp, copper, items [(item_id, anzahl)], choice [item_id, ...] (Spieler wählt einen)
"""

QUESTS = {
    # ------------------------------------------------------------------ Eichenau
    "wolfsplage": {
        "title": "Wölfe vor den Toren", "giver": "roderich", "ender": "roderich", "level": 1, "min_level": 1,
        "text": "Ihr seid neu hier, was? Dann kommt Ihr gerade recht. Westlich von Eichenau treiben sich "
                "Waldwölfe herum. Gestern haben sie Mutter Hildes Wäsche gefressen. Die WÄSCHE!\n\n"
                "Erlegt 6 Waldwölfe im Westen des Dorfes, dann reden wir weiter.",
        "objective": "Erlegt 6 Waldwölfe.",
        "progress": "Die Wölfe heulen immer noch. Ich höre sie. Ihr nicht?",
        "complete": "Gut gemacht! Hilde wird sich freuen. Ihre neue Wäsche ist allerdings schon wieder schmutzig. "
                    "Nehmt das hier, Ihr habt es Euch verdient.",
        "objectives": [{"type": "kill", "mob": "waldwolf", "count": 6}],
        "rewards": {"xp": 170, "copper": 25, "choice": ["rekrutenhandschuhe", "gewebte_handschuhe"]},
    },
    "audienz_beim_herrscher": {
        "title": "Audienz beim Herrscher", "giver": "roderich", "ender": "simon", "level": 1, "min_level": 1,
        "text": "Jeder Neuankömmling in Eldornia muss sich beim Herrscher vorstellen. So will es das Gesetz. "
                "Na gut, eigentlich will es nur Simon so. Aber er ist der Herrscher, also ist es Gesetz.\n\n"
                "Folgt der Straße nach Norden zur Burg Eldenstein und meldet Euch bei Simon, dem zweiäugigen Herrscher.",
        "objective": "Sprecht mit Simon auf Burg Eldenstein nördlich von Eichenau.",
        "complete": "Ah! Ein neues Gesicht! Ich sehe es ganz deutlich – mit BEIDEN Augen. Wisst Ihr, in Eldornia gibt es "
                    "Herrscher mit einem Auge, Herrscher mit drei Augen ... aber nur einen mit genau zwei. Mich.\n\n"
                    "Willkommen in meinem Reich, Abenteurer.",
        "objectives": [],
        "rewards": {"xp": 90, "copper": 10},
    },
    "graumaehne": {
        "title": "Der Rudelführer", "giver": "roderich", "ender": "roderich", "level": 4, "min_level": 3,
        "prev": "wolfsplage",
        "text": "Die Wölfe kommen zurück. Immer wieder. Meine Späher sagen, dass ein riesiger grauer Wolf das Rudel "
                "anführt: Graumähne. Solange er lebt, hören die Angriffe nicht auf.\n\n"
                "Ihr findet ihn tief im Wolfsforst im Nordwesten. Seid vorsichtig, er ist stärker als die anderen.",
        "objective": "Tötet Graumähne im Wolfsforst.",
        "progress": "Lebt Graumähne noch?",
        "complete": "Graumähne ist tot? Bei Simons beiden Augen! Ihr seid wirklich ein Held. Nehmt diese Tränke.",
        "objectives": [{"type": "kill", "mob": "graumaehne", "count": 1}],
        "rewards": {"xp": 420, "copper": 110, "items": [("heiltrank", 3)]},
    },
    "wildschweinbraten": {
        "title": "Braten für den Schiefen Krug", "giver": "hilde", "ender": "hilde", "level": 3, "min_level": 2,
        "text": "Kind, du bist ja nur Haut und Knochen! Aber wenn du schon hier bist: Mir sind die Wildschweinkeulen "
                "ausgegangen, und ohne Braten trinken die Leute nur und singen. Fidelius singt dann auch. Das will keiner.\n\n"
                "Bring mir 6 Wildschweinkeulen von den Wildschweinen östlich des Dorfes.",
        "objective": "Bringt Mutter Hilde 6 Wildschweinkeulen.",
        "progress": "Ohne Keulen kein Braten. Ohne Braten singt Fidelius. Beeil dich!",
        "complete": "Prachtvolle Keulen! Jetzt gibt's endlich wieder Braten. Hier, nimm ein paar Portionen mit – "
                    "und iss sie auch!",
        "objectives": [{"type": "collect", "item": "wildschweinkeule", "count": 6}],
        "rewards": {"xp": 310, "copper": 40, "items": [("wildschweinbraten", 5)]},
    },
    "ein_brief_fuer_kathi": {
        "title": "Ein Brief für Kathi", "giver": "fidelius", "ender": "kathi", "level": 2, "min_level": 1,
        "text": "Ihr habt ein ehrliches Gesicht! Und zwei Beine! Perfekt. Ich habe einen Brief für Kathi, die holde "
                "Burgmaid. Ein Liebesgedicht. Zweiunddreißig Strophen.\n\n"
                "Bringt ihn zu ihr auf die Burg Eldenstein. Und lest ihn nicht! ... Na gut, nur die erste Strophe.",
        "objective": "Bringt Fidelius' Brief zu Kathi auf Burg Eldenstein.",
        "complete": "Ein Brief? Von Fidelius? *liest* ... \"Deine Augen sind wie zwei Suppenteller\" ... \"so rund und "
                    "voller Brühe\" ... Oh je.\n\nSagt ihm, ich denke darüber nach. Und dass er Gedichte schreiben lernen soll.",
        "objectives": [],
        "start_item": "liebesbrief",
        "rewards": {"xp": 160, "copper": 50},
    },
    "baelle_fuer_den_gaukler": {
        "title": "Bälle für den Gaukler", "giver": "gaukelkobold", "ender": "gaukelkobold", "level": 3, "min_level": 2,
        "text": "Großfuß! Großfuß, hör zu! Gaukelkobold hatte sieben Bälle. Dann sechs. Dann ... drei. "
                "Ein Wildschwein hat vier gefressen. Lange Geschichte.\n\nAber! Schweineblasen hüpfen wie Bälle! "
                "Bring 5 Schweineblasen von den Wildschweinen, dann jongliert Gaukelkobold wieder wie früher!",
        "objective": "Bringt dem Gaukelkobold 5 aufgeblasene Schweineblasen.",
        "progress": "Hopp, hopp! Wo sind die Bälle? Gaukelkobold jongliert solange mit Luft.",
        "complete": "JA! JA! Fünf Bälle! *jongliert* Eins, zwei, drei, vier, fü... *plopp* ... vier Bälle. Egal! "
                    "Hier, Gaukelkobolds alte Handschuhe. Glück bringen sie nicht, aber warm sind sie.",
        "objectives": [{"type": "collect", "item": "schweineblase", "count": 5}],
        "rewards": {"xp": 300, "copper": 30, "items": [("gauklerhandschuhe", 1)]},
    },
    "plage_auf_dem_feld": {
        "title": "Plage auf dem Feld", "giver": "kaspar", "ender": "kaspar", "level": 3, "min_level": 2,
        "text": "Seht Ihr das? Meine Rüben! Angefressen! Alle! Die Wildschweine kommen jede Nacht und fressen "
                "sich durch meine Felder.\n\nErlegt 10 Wildschweine rund um meinen Hof, bevor sie auch noch die "
                "Mühle fressen.",
        "objective": "Erlegt 10 Wildschweine rund um Kaspars Hof.",
        "progress": "Ich höre sie schmatzen. Hört Ihr sie auch schmatzen?",
        "complete": "Endlich Ruhe auf dem Feld! Nehmt das als Dank. Meine Frau hat's gemacht. Oder gefunden.",
        "objectives": [{"type": "kill", "mob": "wildschwein", "count": 10}],
        "rewards": {"xp": 340, "copper": 60, "choice": ["bauernstiefel", "eichenstab"]},
    },
    "gackerle_ist_weg": {
        "title": "Gackerle ist weg!", "giver": "dorftrottel", "ender": "dorftrottel", "level": 2, "min_level": 1,
        "text": "Gackerle ist weg! GACKERLE IST WEG! Gackerle ist mein Huhn. Ein goldenes Huhn! Na ja, gelb. "
                "Sehr gelb.\n\nGestern hat es gesagt, dass es Bauer Kaspars Mühle sehen will. Also, es hat \"Gack\" "
                "gesagt. Aber ich hab's verstanden! Bitte bring Gackerle zurück!",
        "objective": "Findet Gackerle bei Bauer Kaspars Windmühle östlich des Dorfes und bringt es zurück.",
        "progress": "Gackerle? Gackerleee?",
        "complete": "GACKERLE! Da bist du ja! *drückt das Huhn* Es sagt danke! Also, es sagt \"Gack\". "
                    "Das heißt danke. Hier, meine Glücksfeder. Die hat Gackerle verloren. Oder ein anderer Vogel.",
        "objectives": [{"type": "collect", "item": "gackerle", "count": 1}],
        "rewards": {"xp": 220, "copper": 5, "items": [("glueckfeder", 1)]},
    },
    # ------------------------------------------------------------------ Burg Eldenstein
    "kraeuter_fuer_die_suppe": {
        "title": "Kräuter für die Suppe", "giver": "kathi", "ender": "kathi", "level": 2, "min_level": 1,
        "text": "Oh, gut, dass Ihr da seid! Der Herrscher will Suppe, aber ich habe keine Kräuter mehr. Und eine Suppe "
                "ohne Kräuter ist nur heißes Wasser. Das merkt sogar Simon. Mit beiden Augen.\n\n"
                "Auf den Wiesen zwischen Burg und Dorf wächst Wiesenkraut. Bringt mir 6 Stück, bitte!",
        "objective": "Sammelt 6 Wiesenkraut auf den Wiesen zwischen Burg und Eichenau.",
        "progress": "Das Wasser kocht schon. Seit zwei Stunden.",
        "complete": "Wunderbar! Das duftet herrlich! Jetzt wird es eine richtige Suppe. Nehmt diesen Umhang, ich habe "
                    "ihn aus Kräuterresten genäht. Er riecht ein bisschen nach Suppe.",
        "objectives": [{"type": "collect", "item": "wiesenkraut", "count": 6}],
        "rewards": {"xp": 260, "copper": 20, "items": [("kraeuterumhang", 1), ("brot", 5)]},
    },
    "das_verlorene_medaillon": {
        "title": "Das verlorene Medaillon", "giver": "leonine", "ender": "leonine", "level": 5, "min_level": 4,
        "text": "Bitte, könnt Ihr mir helfen? Als ich Rosen am Waldrand gepflückt habe, haben mich Banditen der "
                "Rotdolch-Bande überfallen. Sie haben mein Medaillon gestohlen. Es war ein Geschenk meiner Mutter.\n\n"
                "Ihr Lager liegt nordöstlich der Burg. Einer von ihnen muss es haben.",
        "objective": "Holt Leonines Medaillon von den Rotdolch-Banditen zurück.",
        "progress": "Habt Ihr es gefunden? Silber, mit einer Rose darauf ...",
        "complete": "Mein Medaillon! Ihr habt es wirklich gefunden! Ich danke Euch von ganzem Herzen. "
                    "Nehmt einen dieser Ringe – sie gehörten meinem Vater.",
        "objectives": [{"type": "collect", "item": "leonines_medaillon", "count": 1}],
        "rewards": {"xp": 520, "copper": 80, "choice": ["ring_standhaftigkeit", "ring_klarheit"]},
    },
    "die_rotdolche": {
        "title": "Die Rotdolch-Bande", "giver": "jonas", "ender": "jonas", "level": 5, "min_level": 4,
        "text": "Seid gegrüßt, Abenteurer. Ein Ritter dient dem Volk – und das Volk leidet unter der Rotdolch-Bande. "
                "Sie überfallen Händler, Bauern und Burgmaiden.\n\nIhr Lager liegt nordöstlich von hier. "
                "Zeigt ihnen, was Gerechtigkeit bedeutet: Besiegt 8 Rotdolch-Schläger und 5 Rotdolch-Armbrustschützen.",
        "objective": "Besiegt 8 Rotdolch-Schläger und 5 Rotdolch-Armbrustschützen.",
        "progress": "Für Ehre und für Eldornia! Kehrt zurück, wenn Eure Aufgabe erfüllt ist.",
        "complete": "Ausgezeichnet! Die Bande ist geschwächt. Ihr kämpft wie ein wahrer Ritter. "
                    "Nehmt dies als Zeichen meines Respekts.",
        "objectives": [{"type": "kill", "mob": "bandit", "count": 8}, {"type": "kill", "mob": "armbrustschuetze", "count": 5}],
        "rewards": {"xp": 560, "copper": 120, "choice": ["banditenweste", "schimmernde_robe"]},
    },
    "grimbart_rotdolch": {
        "title": "Grimbart Rotdolch", "giver": "jonas", "ender": "jonas", "level": 7, "min_level": 5,
        "prev": "die_rotdolche",
        "text": "Die Bande ist geschwächt, aber ihr Anführer lebt noch: Grimbart Rotdolch. Er versteckt sich in seinem "
                "großen Zelt im Lager.\n\nGrimbart ist gefährlich – nehmt einen Gefährten mit, wenn Ihr könnt. "
                "Und achtet auf seinen Wirbelwind: Wenn er die Klingen kreisen lässt, geht ihm aus dem Weg!",
        "objective": "Besiegt Grimbart Rotdolch im Lager der Rotdolch-Bande. (Elite – Gruppe empfohlen)",
        "progress": "Grimbart lebt noch? Dann ist Eldornia nicht sicher.",
        "complete": "Grimbart ist gefallen! Ihr habt Eldornia einen großen Dienst erwiesen. Simon wird davon erfahren "
                    "– er hat es vermutlich ohnehin schon gesehen.",
        "objectives": [{"type": "kill", "mob": "grimbart", "count": 1}],
        "rewards": {"xp": 820, "copper": 300, "choice": ["wachmannsschultern", "lehrlingsschultertuch"]},
    },
    "ein_auge_auf_den_einaeugigen": {
        "title": "Ein Auge auf den Einäugigen", "giver": "simon", "ender": "einaeugiger_kobold", "level": 4,
        "min_level": 3, "prev": "audienz_beim_herrscher",
        "text": "Ich habe zwei Augen, Abenteurer. Und ich setze beide gut ein. Aber selbst zwei Augen können nicht "
                "überall sein.\n\nIn Eichenau treibt sich ein Kobold mit nur einem Auge herum. Er verkauft Dinge, "
                "die ... irgendwo herkommen. Geht hin und behaltet ihn im Auge. In einem Eurer beiden.",
        "objective": "Sprecht mit dem einäugigen Kobold am Ostrand von Eichenau.",
        "complete": "Psst! Was? Der Zweiäugige schickt dich? Hah! Einauge sieht mit einem Auge mehr als der mit zwei! "
                    "... Aber gut. Du siehst ehrlich aus. Ehrlich genug. Einauge hat Arbeit für dich.",
        "objectives": [],
        "rewards": {"xp": 210, "copper": 15},
    },
    "kerzen_der_tiefe": {
        "title": "Kerzen der Tiefe", "giver": "einaeugiger_kobold", "ender": "einaeugiger_kobold", "level": 6,
        "min_level": 5, "prev": "ein_auge_auf_den_einaeugigen",
        "text": "Die Tunnelkobolde im Kupferstollen haben Kerzen. Viele Kerzen! Schöne Kerzen! Einauge will Kerzen. "
                "Warum? Geht dich nichts an. ... Na gut: Kerzen verkaufen sich gut. Sehr gut.\n\n"
                "Bring Einauge 8 Kobold-Kerzen aus dem Stollen im Südosten.",
        "objective": "Bringt dem einäugigen Kobold 8 Kobold-Kerzen von den Tunnelkobolden im Südosten.",
        "progress": "Kerzen? Hast du Kerzen? Einauge sieht keine Kerzen.",
        "complete": "Kerzen! So viele Kerzen! Einauge ist reich! Fast. Hier, nimm das Monokel. Einauge braucht es nicht "
                    "– du weißt schon, warum.",
        "objectives": [{"type": "collect", "item": "kobold_kerze", "count": 8}],
        "rewards": {"xp": 620, "copper": 150, "items": [("monokel", 1)]},
    },
    "erz_fuer_die_schmiede": {
        "title": "Erz für die Schmiede", "giver": "gundolf", "ender": "gundolf", "level": 6, "min_level": 5,
        "text": "*Klong* Erz. Ich brauche Erz. Die Kobolde sitzen auf dem besten Kupfer der ganzen Grünmark.\n\n"
                "Geht zum Kupferstollen im Südosten und baut 6 Brocken Kupfererz ab. Dann schmiede ich Euch was Ordentliches.",
        "objective": "Baut 6 Kupfererz am Kupferstollen im Südosten ab.",
        "progress": "*Klong* Kein Erz, keine Waffe.",
        "complete": "*Klong* Gutes Erz. Sehr gut. Hier, frisch geschmiedet. Sucht Euch eins aus.",
        "objectives": [{"type": "collect", "item": "kupfererz", "count": 6}],
        "rewards": {"xp": 620, "copper": 60, "choice": ["gundolfs_breitschwert", "gluehender_kupferstab"]},
    },
    # ------------------------------------------------------------------ Krypta
    "was_der_blinde_sieht": {
        "title": "Was der Blinde sieht", "giver": "blinde", "ender": "wache_krypta", "level": 8, "min_level": 7,
        "text": "Setz dich, Wanderer. Ich sehe nichts ... und doch sehe ich Dunkelheit. Sie kriecht unter dem alten "
                "Friedhof im Südwesten hervor. Die Toten der vergessenen Krypta schlafen nicht mehr.\n\n"
                "Geh zu Totenwächterin Elsbeth am Friedhof. Sie bewacht das Tor. Sag ihr, dass der Blinde dich schickt.",
        "objective": "Sprecht mit Totenwächterin Elsbeth am Friedhof der Vergessenen im Südwesten.",
        "complete": "Der Blinde schickt Euch? Dann ist es schlimmer, als ich dachte. Er irrt sich nie. Nie.",
        "objectives": [],
        "rewards": {"xp": 260, "copper": 20},
    },
    "die_vergessene_krypta": {
        "title": "Die vergessene Krypta", "giver": "wache_krypta", "ender": "jonas", "level": 10, "min_level": 7,
        "prev": "was_der_blinde_sieht",
        "text": "Vor langer Zeit war Sir Morgrath der edelste Ritter Eldornias. Er war der Lehrmeister von Jonas. "
                "Als er starb, wurde er in der Krypta beigesetzt. Doch etwas hat ihn wieder erweckt.\n\n"
                "Steigt hinab in die vergessene Krypta, besiegt Sir Morgrath und bringt sein Siegel zu Jonas. "
                "Er sollte es als Erster erfahren. (Dungeon – 1 bis 2 Spieler empfohlen)",
        "objective": "Besiegt Sir Morgrath in der vergessenen Krypta und bringt Morgraths Siegel zu Jonas.",
        "progress": "Ist es wahr? Ist mein alter Meister zurückgekehrt?",
        "complete": "Morgraths Siegel ... Also ist es wahr. Mein Meister hat endlich seine Ruhe gefunden. Danke. "
                    "Er hat mir alles beigebracht, was ich weiß: Ehre, Mut ... und wie man ein Schwert poliert.",
        "objectives": [{"type": "collect", "item": "morgraths_siegel", "count": 1}],
        "rewards": {"xp": 1100, "copper": 400},
    },
    "ruhe_fuer_die_toten": {
        "title": "Ruhe für die Toten", "giver": "anselm", "ender": "anselm", "level": 9, "min_level": 7,
        "text": "Möge das Licht Euch leiten. Unter dem Friedhof erheben sich die Toten. Ich spüre ihre Unruhe bis hierher.\n\n"
                "Steigt in die vergessene Krypta hinab und erlöst 10 ruhelose Skelette und 4 Knochenmagier.",
        "objective": "Erlöst 10 ruhelose Skelette und 4 Knochenmagier in der vergessenen Krypta.",
        "progress": "Die Toten verdienen Ruhe. Alle.",
        "complete": "Ich spüre es – die Unruhe lässt nach. Das Licht ist mit Euch. Nehmt diese gesegneten Handschuhe.",
        "objectives": [{"type": "kill", "mob": "skelett", "count": 10}, {"type": "kill", "mob": "knochenmagier", "count": 4}],
        "rewards": {"xp": 900, "copper": 200, "choice": ["gesegnete_handschuhe", "handschuhe_der_andacht"]},
    },
    "der_herrscher_muss_es_wissen": {
        "title": "Der Herrscher muss es wissen", "giver": "jonas", "ender": "simon", "level": 10, "min_level": 7,
        "prev": "die_vergessene_krypta",
        "text": "Simon muss erfahren, was in der Krypta geschehen ist. Geht zu ihm und berichtet. Er wird Euch belohnen, "
                "wie es einem Helden Eldornias gebührt.",
        "objective": "Berichtet Simon auf Burg Eldenstein von Morgraths Fall.",
        "complete": "Morgrath ist gefallen? Das habe ich kommen sehen. Mit beiden Augen. Natürlich.\n\n"
                    "Ihr habt Eldornia gerettet, Abenteurer. Ab heute seid Ihr ein Held des Reiches. Wählt Eure Belohnung "
                    "aus meiner persönlichen Waffenkammer.",
        "objectives": [],
        "rewards": {"xp": 1000, "copper": 500, "choice": ["klinge_des_herrschers", "simons_zepter"]},
    },
}

for _id, _q in QUESTS.items():
    _q["id"] = _id
    _q.setdefault("prev", None)
    _q.setdefault("progress", "")
    _q.setdefault("start_item", None)
    _q["rewards"].setdefault("items", [])
    _q["rewards"].setdefault("choice", [])
    _q["rewards"].setdefault("copper", 0)


def quests_given_by(npc_id: str):
    return [q for q in QUESTS.values() if q["giver"] == npc_id]


def quests_ended_by(npc_id: str):
    return [q for q in QUESTS.values() if q["ender"] == npc_id]


# Welche Quest benötigt welchen Questgegenstand (für Drops und Sammelobjekte)
ITEM_QUESTS: dict[str, list[str]] = {}
for _q in QUESTS.values():
    for _o in _q["objectives"]:
        if _o["type"] == "collect":
            ITEM_QUESTS.setdefault(_o["item"], []).append(_q["id"])
