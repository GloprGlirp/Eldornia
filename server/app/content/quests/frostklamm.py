"""Quests der Frostklamm (Stufe 10–25) und der Schwarzen Schmiede."""
from .. import items as I

I.QUEST("ambossherz_kern", "Ambossherz' Glutkern", "fire-gem", "Pulsiert wie ein Herz aus flüssigem Stahl.", 1)
I.QUEST("humpen_fuer_die_wache", "Humpen Frostbräu", "beer-stein", "Schäumt. Und friert dabei nicht ein. Zwergenmagie.", 3)
I.QUEST("mondzirkel_brief", "Brief des Mondzirkels", "envelope", "Riecht nach Nachtblumen. Das Siegel zeigt eine Mondsichel.", 1)

_T = "g_"   # Präfix generierter Ausrüstung


def _choice(tier: int, q: int = 2, slot: str = "chest") -> list[str]:
    """Eine Belohnungsauswahl für Platte, Kette, Leder und Stoff derselben Stufe."""
    return [f"g_platte_{slot}_{tier}_{q}_baer", f"g_kette_{slot}_{tier}_{q}_falke" if q == 2 else f"g_kette_{slot}_{tier}_{q}_tiger",
            f"g_leder_{slot}_{tier}_{q}_affe", f"g_stoff_{slot}_{tier}_{q}_eule"]


QUESTS = {
    # ================================================================== Hauptgeschichte
    "der_koenig_unter_dem_berg": {
        "type": "main", "title": "Der König unter dem Berg", "giver": "brogar", "ender": "kragg", "level": 11, "min_level": 10,
        "prev": "der_weg_nach_frostklamm",
        "text": "Simon schreibt, Ihr hättet Sir Morgrath besiegt? Mit nur zwei Augen und ohne Bart? Respekt, Großling.\n\n"
                "Wir Zwerge vom Eisenbart-Klan halten die Frostklamm seit tausend Jahren. Doch die Eisriesen werden "
                "dreister, die Kobolde haben unseren alten Stollen besetzt, und die Schwarzeisenzwerge – Schande über "
                "ihre rußigen Bärte – rüsten in der Schwarzen Schmiede zum Krieg.\n\nMeldet Euch bei Hauptmann Kragg am Tor.",
        "objective": "Sprecht mit Hauptmann Kragg Steinfaust am Tor der Hammerfeste.",
        "complete": "Der König schickt Euch? Gut. Ich habe eine Liste. Sie ist lang. Fangen wir unten an.",
        "rewards": {"xp": 600, "copper": 120, "rep": {"eisenbart": 150}},
    },
    "woelfe_vor_den_toren": {
        "type": "main", "title": "Wölfe vor den Toren", "giver": "kragg", "ender": "kragg", "level": 11, "min_level": 10,
        "prev": "der_koenig_unter_dem_berg",
        "text": "Die Frostwölfe im Westen jagen unsere Händler. Sie sind hungrig, sie sind viele, und sie haben sehr "
                "viele Zähne.\n\nDünnt das Rudel im Frostwolftal aus. Zehn sollten reichen, damit die anderen nachdenken.",
        "objective": "Besiegt 10 Frostwölfe im Frostwolftal westlich der Hammerfeste.",
        "objectives": [{"type": "kill", "mob": "frostwolf", "count": 10}],
        "progress": "Hört Ihr noch Heulen? Dann seid Ihr nicht fertig.",
        "complete": "Ruhe im Westen. Sehr gut. Die Händler werden es Euch danken. Mit Rabatt. Vielleicht.",
        "rewards": {"xp": 1150, "copper": 260, "rep": {"eisenbart": 250}, "choice": _choice(2, 2, "feet")},
    },
    "der_verlassene_stollen": {
        "type": "main", "title": "Der verlassene Stollen", "giver": "kragg", "ender": "durin", "level": 14, "min_level": 12,
        "prev": "woelfe_vor_den_toren",
        "text": "Der Tiefenstollen im Osten war einst unsere reichste Mine. Dann kamen Kobolde – und etwas, das "
                "nicht atmet. Durin Kieselbart, der letzte Bergmann, hockt vor dem Eingang und weigert sich zu gehen.\n\n"
                "Geht zu ihm. Hört Euch an, was er gesehen hat. Und bringt ihm um Himmels willen eine Decke mit.",
        "objective": "Sprecht mit Durin Kieselbart vor dem Tiefenstollen im Osten.",
        "complete": "Endlich! Hilfe! Habt Ihr eine Decke? ... Nein? Na gut. Hört zu, da unten ist es schlimm.",
        "rewards": {"xp": 700, "copper": 100, "rep": {"eisenbart": 100}},
    },
    "kobolde_raus": {
        "type": "main", "title": "Kobolde raus!", "giver": "durin", "ender": "durin", "level": 15, "min_level": 13,
        "prev": "der_verlassene_stollen",
        "text": "Die Frostkobolde haben sich im Stollen breitgemacht. Sie klauen Erz, Laternen und meine Pausenbrote. "
                "Die Sprengmeister sprengen Gänge, die seit 300 Jahren stehen!\n\nWerft sie raus. Alle. Bitte.",
        "objective": "Besiegt 10 Frostkobolde und 4 Kobold-Sprengmeister im Tiefenstollen.",
        "objectives": [{"type": "kill", "mob": "frostkobold", "count": 10},
                       {"type": "kill", "mob": "kobold_sprengmeister", "count": 4}],
        "progress": "Ich höre sie immer noch kichern.",
        "complete": "Stille. Herrliche Stille. Nur ... das Singen ist noch da. Von ganz tief unten.",
        "rewards": {"xp": 1650, "copper": 420, "rep": {"eisenbart": 250}, "choice": _choice(3, 2, "hands")},
    },
    "das_lied_aus_der_tiefe": {
        "type": "main", "title": "Das Lied aus der Tiefe", "giver": "durin", "ender": "edda", "level": 17, "min_level": 15,
        "prev": "kobolde_raus",
        "text": "Das Singen kommt vom alten Vorarbeiter Knurrbart. Er starb beim großen Einsturz – und er will einfach "
                "keinen Feierabend machen. Seine Geister halten die Schicht.\n\nBesiegt Knurrbart und bringt Runenpriesterin "
                "Edda im Lager Frosthauch Nachricht. Sie weiß, wie man ruhelose Zwerge zur Ruhe bettet.",
        "objective": "Besiegt Knurrbart im Tiefenstollen und berichtet Runenpriesterin Edda im Lager Frosthauch.",
        "objectives": [{"type": "kill", "mob": "knurrbart", "count": 1}, {"type": "kill", "mob": "stollengeist", "count": 6}],
        "progress": "Die Runen sind unruhig. Ist es vollbracht?",
        "complete": "Knurrbart hat seinen Feierabend gefunden. Ich spüre es in den Runen. Gut gemacht. Doch die Runen "
                    "erzählen noch mehr – von einem Feld im Nordwesten, wo alte Wächter erwacht sind.",
        "rewards": {"xp": 2000, "copper": 600, "rep": {"eisenbart": 350},
                    "choice": ["stollenkette", "zwergische_stiefel", "runengewirkte_kapuze", "kuerschnerhandschuhe"]},
    },
    "die_runen_der_ahnen": {
        "type": "main", "title": "Die Runen der Ahnen", "giver": "edda", "ender": "edda", "level": 18, "min_level": 16,
        "prev": "das_lied_aus_der_tiefe",
        "text": "Auf dem Runenfeld haben unsere Ahnen Steinwächter aufgestellt, die das Tal vor den Riesen schützen sollten. "
                "Jetzt greifen sie jeden an. Jemand hat ihre Runen verdreht.\n\nZerschlagt die Wächter und bringt mir ihre "
                "Runensteinfragmente. Ich will lesen, wer sie verändert hat.",
        "objective": "Sammelt 8 Runensteinfragmente von den Runenwächtern auf dem Runenfeld.",
        "objectives": [{"type": "collect", "item": "runenstein_fragment", "count": 8}],
        "progress": "Ohne die Fragmente kann ich die Runen nicht lesen.",
        "complete": "Eisrunen ... die Schrift der Riesen. Hrimgar selbst hat die Wächter verdreht! Der Frostkönig ist erwacht.",
        "rewards": {"xp": 2200, "copper": 700, "rep": {"eisenbart": 350}, "choice": _choice(4, 2, "shoulders")},
    },
    "der_frostkoenig_erwacht": {
        "type": "main", "title": "Der Frostkönig erwacht", "giver": "edda", "ender": "brogar", "level": 21, "min_level": 19,
        "prev": "die_runen_der_ahnen",
        "text": "Wenn Hrimgar erwacht ist, werden die Eisriesen über die Täler herfallen. Geht zum Eisriesenhorst im "
                "Nordwesten und schwächt ihr Heer, bevor es marschiert. Bringt König Brogar ihre Zähne als Beweis.\n\n"
                "Hrimgar selbst ... den greift nur mit vielen Freunden an.",
        "objective": "Besiegt 8 Eisriesen und sammelt 6 Eisriesenzähne. Bringt sie König Brogar.",
        "objectives": [{"type": "kill", "mob": ["eisriese", "eisriesenschamane"], "count": 8, "text": "Eisriesen besiegt"},
                       {"type": "collect", "item": "eisriesenzahn", "count": 6}],
        "progress": "Riesenzähne! Ich will Riesenzähne sehen!",
        "complete": "BEI MEINEM BART! Sechs Zähne! Daraus lasse ich mir ein Halsband machen. Der Klan steht in Eurer Schuld.",
        "rewards": {"xp": 2700, "copper": 900, "rep": {"eisenbart": 500}, "choice": _choice(5, 2, "chest")},
    },
    "rauch_im_nordosten": {
        "type": "main", "title": "Rauch im Nordosten", "giver": "brogar", "ender": "brogar", "level": 22, "min_level": 20,
        "prev": "der_frostkoenig_erwacht",
        "text": "Die Schwarzeisenzwerge haben ein Lager vor der Schwarzen Schmiede aufgeschlagen. Ihre Feuerrufer "
                "verbrennen alles, was nicht aus Stein ist – und ihre Krieger alles, was aus Stein ist.\n\nGreift das "
                "Lager an und erbeutet ihre Befehle. Ich will wissen, was dieser Ambossherz plant.",
        "objective": "Besiegt 10 Schwarzeisenzwerge und erbeutet die Schwarzeisen-Befehle.",
        "objectives": [{"type": "kill", "mob": ["schwarzeisen_krieger", "schwarzeisen_feuerrufer"], "count": 10, "text": "Schwarzeisenzwerge besiegt"},
                       {"type": "collect", "item": "schwarzeisen_befehle", "count": 1}],
        "progress": "Und? Was steht in den Befehlen?",
        "complete": "\"... Ambossherz erweckt die Großen Golems. Wenn die Esse brennt, fällt Hammerfeste.\" Pah! Nicht, "
                    "solange ich einen Bart habe.",
        "rewards": {"xp": 2800, "copper": 1000, "rep": {"eisenbart": 500},
                    "choice": ["runenklinge_frostklamm", "eiszapfenstab", "bergbogen", "frostkatana", "eisdolch", "eisriesenaxt",
                               "brogars_hammer", "eisbrecher_schild"]},
    },
    "die_schwarze_schmiede": {
        "type": "main", "title": "Die Schwarze Schmiede", "giver": "brogar", "ender": "brogar", "level": 25, "min_level": 20,
        "prev": "rauch_im_nordosten", "dungeon": "schmiede",
        "text": "Es reicht. Ihr geht in die Schwarze Schmiede und löscht Ambossherz' Esse. Für immer.\n\nNehmt Freunde mit – "
                "drei bis fünf, wenn Ihr klug seid. Die Golems dort unten sind größer als mein Ego. Und das ist groß.\n\n"
                "Bringt mir Ambossherz' Glutkern. (Dungeon – 3 bis 5 Spieler)",
        "objective": "Besiegt Glutmeister Ambossherz in der Schwarzen Schmiede und bringt seinen Glutkern zu König Brogar.",
        "objectives": [{"type": "collect", "item": "ambossherz_kern", "count": 1}],
        "progress": "Brennt die Esse noch?",
        "complete": "Der Glutkern! Die Esse ist erloschen! Hammerfeste ist gerettet! Ab heute seid Ihr Ehrenzwerg des "
                    "Eisenbart-Klans. Ihr bekommt sogar einen Bart. ... Einen falschen. Aber einen sehr schönen.",
        "rewards": {"xp": 4200, "copper": 2500, "rep": {"eisenbart": 1000}, "title": "freund_der_zwerge",
                    "currency": {"dungeonmarken": 10}},
    },
    # ================================================================== Lager Frosthauch
    "kaltes_willkommen": {
        "type": "side", "title": "Ein kaltes Willkommen", "giver": "sigrun", "ender": "sigrun", "level": 11, "min_level": 10,
        "text": "Ihr friert. Ich sehe es an Euren blauen Lippen. Bringt mir sechs makellose Frostwolfpelze, dann nähe ich "
                "Euch etwas Warmes. Für mich bleibt auch was übrig – das ist der Deal.",
        "objective": "Sammelt 6 makellose Frostwolfpelze.",
        "objectives": [{"type": "collect", "item": "frostwolfpelz", "count": 6}],
        "progress": "Noch nicht genug Pelze? Dann zittert weiter.",
        "complete": "Schöne Pelze! Hier, Euer Umhang. Ab jetzt sind Eure Lippen wieder rot.",
        "rewards": {"xp": 1100, "copper": 220, "rep": {"eisenbart": 150}, "items": [("frostwolfumhang", 1)]},
    },
    "luchse_im_unterholz": {
        "type": "side", "title": "Luchse im Unterholz", "giver": "sigrun", "ender": "sigrun", "level": 12, "min_level": 10,
        "text": "Schneeluchse schleichen ums Lager. Gestern hat einer meinen Proviant gestohlen. Mitsamt Rucksack. "
                "Und meinem zweiten Stiefel.\n\nErledigt acht von ihnen.",
        "objective": "Besiegt 8 Schneeluchse.",
        "objectives": [{"type": "kill", "mob": "schneeluchs", "count": 8}],
        "complete": "Gut. Jetzt fehlt mir nur noch der Stiefel.",
        "rewards": {"xp": 1200, "copper": 250, "rep": {"eisenbart": 150}, "choice": _choice(2, 2, "legs")},
    },
    "das_leuchten_im_see": {
        "type": "side", "title": "Das Leuchten im See", "giver": "ingrid", "ender": "ingrid", "level": 14, "min_level": 12,
        "text": "Seit einigen Wochen leuchtet der See nachts blau, und aus den Löchern im Eis steigen Frostgeister. "
                "Die Fische sind weg. Mein Mann sagt, das Eis ist verflucht. Mein Mann sagt viel.\n\nBesiegt die "
                "Frostgeister und bringt mir ihre Kerne. Ich will wissen, was da unten pocht.",
        "objective": "Besiegt 8 Frostgeister und sammelt 5 pulsierende Frostkerne am Gefrorenen See.",
        "objectives": [{"type": "kill", "mob": "frostgeist", "count": 8}, {"type": "collect", "item": "frostkern", "count": 5}],
        "complete": "Sie pulsieren alle im selben Takt ... wie ein Herz. Unter dem Eis schlägt ein Herz!",
        "rewards": {"xp": 1500, "copper": 380, "rep": {"eisenbart": 200}, "choice": _choice(3, 2, "head")},
    },
    "das_herz_des_sees": {
        "type": "side", "title": "Das Herz des Sees", "giver": "ingrid", "ender": "ingrid", "level": 16, "min_level": 14,
        "prev": "das_leuchten_im_see",
        "text": "Das Herz des Sees – ein riesiger Eiselementar namens Glazius. Er ist aus dem Eis gestiegen und will "
                "nicht zurück. Er ist stark. Nehmt Freunde mit.",
        "objective": "Besiegt Glazius, das Herz des Sees (Elite).",
        "objectives": [{"type": "kill", "mob": "glazius", "count": 1}],
        "complete": "Das Leuchten ist fort. Und ... ein Fisch! Da, ein Fisch! Die Fische kommen zurück!",
        "rewards": {"xp": 2200, "copper": 600, "rep": {"eisenbart": 300}, "items": [("grosser_heiltrank", 3)],
                    "choice": ["frostfeuer_amulett", "ring_des_eisenbarts"]},
    },
    "durins_spitzhacke": {
        "type": "side", "title": "Durins Spitzhacke", "giver": "durin", "ender": "durin", "level": 14, "min_level": 13,
        "text": "Meine Spitzhacke! Ein Erbstück! Mein Ur-ur-ur-Großvater hat damit den ersten Stollen gegraben. "
                "Ich hab sie fallen lassen, als die Kobolde kamen. Sie liegt irgendwo vor dem Eingang.",
        "objective": "Findet Durins verlorene Zwergenspitzhacke vor dem Tiefenstollen.",
        "objectives": [{"type": "collect", "item": "verlorene_spitzhacke", "count": 1}],
        "complete": "MEINE SPITZHACKE! *küsst sie* ... Entschuldigung. Hier, für Euch. Familienrezept.",
        "rewards": {"xp": 900, "copper": 300, "items": [("zwergenbrot", 10)]},
    },
    "laternen_der_grube": {
        "type": "side", "title": "Laternen der Grube", "giver": "durin", "ender": "durin", "level": 16, "min_level": 14,
        "text": "Die Kobolde haben alle Grubenlaternen geklaut. Ohne Licht kann kein Zwerg in den Stollen zurück. "
                "Bringt mir sechs Laternen. Die Kobolde halten sie für Schätze. Kobolde halten alles für Schätze.",
        "objective": "Sammelt 6 alte Grubenlaternen von den Kobolden im Tiefenstollen.",
        "objectives": [{"type": "collect", "item": "grubenlaterne", "count": 6}],
        "complete": "Licht! Wunderbares Licht! Der Stollen lebt wieder!",
        "rewards": {"xp": 1500, "copper": 450, "rep": {"eisenbart": 200}, "choice": _choice(3, 2, "legs")},
    },
    "yetifelle_fuer_frode": {
        "type": "side", "title": "Yetifelle für Frode", "giver": "frode", "ender": "frode", "level": 17, "min_level": 15,
        "text": "Yetifell ist das wärmste Leder der Welt. Und das stinkendste. Bringt mir acht Felle aus den Yetihöhlen, "
                "dann mache ich Euch daraus etwas, das Euch durch jeden Schneesturm bringt.",
        "objective": "Sammelt 8 zottelige Yetifelle in den Yetihöhlen nordwestlich der Hammerfeste.",
        "objectives": [{"type": "collect", "item": "yetifell", "count": 8}],
        "complete": "Puh! Die riechen ja noch schlimmer als erwartet. Perfekt.",
        "rewards": {"xp": 1900, "copper": 550, "rep": {"eisenbart": 200}, "choice": _choice(4, 2, "chest")},
    },
    "brogars_bartspange": {
        "type": "hidden", "title": "Brogars Bartspange", "giver": "olaf", "ender": "brogar", "level": 19, "min_level": 17,
        "text": "Psst, Großling. Unter uns: Der König sucht seit Wochen seine Bartspange. Ich weiß, wo sie ist. Er war "
                "betrunken auf Yetijagd und ... na ja. Schneepranke, die Yetimutter, hat sie verschluckt.\n\nWenn Ihr sie "
                "zurückholt, sagt ihm bloß nicht, woher Ihr es wisst.",
        "objective": "Holt Brogars Bartspange von Schneepranke zurück und bringt sie dem König.",
        "objectives": [{"type": "collect", "item": "brogars_bart", "count": 1}],
        "complete": "MEINE BARTSPANGE! Wo habt Ihr ... nein, sagt nichts. Ich will es nicht wissen. Sie ist ... feucht.",
        "rewards": {"xp": 2100, "copper": 1200, "rep": {"eisenbart": 600}, "items": [("ring_des_eisenbarts", 1)]},
    },
    "frostbraeu_fuer_die_wache": {
        "type": "side", "title": "Frostbräu für die Wache", "giver": "olaf", "ender": "olaf", "level": 12, "min_level": 10,
        "start_item": "humpen_fuer_die_wache",
        "text": "Die Wachen am Tor frieren sich die Bärte ab. Bringt ihnen je einen Humpen Frostbräu. Und Hauptmann Kragg "
                "auch einen – der trinkt zwar \"im Dienst nie\", aber er trinkt.",
        "objective": "Bringt den beiden Bergwachen und Hauptmann Kragg je einen Humpen Frostbräu.",
        "objectives": [{"type": "talk", "npc": "wache_hf_1", "count": 1, "text": "Bergwache (links) versorgt",
                        "say": "Bei allen Ahnen! Frostbräu! Ihr seid ein Held!"},
                       {"type": "talk", "npc": "wache_hf_2", "count": 1, "text": "Bergwache (rechts) versorgt",
                        "say": "*schlürf* ... Ahhh. Jetzt spüre ich meine Zehen wieder."},
                       {"type": "talk", "npc": "kragg", "count": 1, "text": "Hauptmann Kragg versorgt",
                        "say": "Ich trinke im Dienst nie. *trinkt* ... Das war kein Dienst. Das war eine Pause."}],
        "complete": "Zufriedene Wachen sind wachsame Wachen. Sagt man. Hier, nehmt das.",
        "rewards": {"xp": 800, "copper": 150, "rep": {"eisenbart": 150}, "items": [("zwergenbrot", 5), ("bergquellwasser", 5)]},
    },
    "erz_fuer_die_esse": {
        "type": "side", "title": "Erz für die Esse", "giver": "grimhild", "ender": "grimhild", "level": 15, "min_level": 13,
        "text": "Die Esse hungert. Bringt mir Eisenerz – egal, ob Ihr es selbst abbaut oder den Kobolden abnehmt. "
                "Zehn Brocken. Dann schmiede ich Euch etwas, das den Namen Rüstung verdient.",
        "objective": "Bringt Grimhild 10 Eisenerz.",
        "objectives": [{"type": "collect", "item": "eisenerz", "count": 10}],
        "complete": "Gutes Erz. Es singt. Hört Ihr es? ... Nein? Ihr müsst lauter zuhören.",
        "rewards": {"xp": 1500, "copper": 500, "rep": {"eisenbart": 250}, "choice": _choice(3, 2, "chest")},
    },
    # ================================================================== Täglich & wöchentlich
    "taegliche_riesenjagd": {
        "type": "daily", "title": "Tägliche Riesenjagd", "giver": "thrain", "ender": "thrain", "level": 22, "min_level": 20,
        "text": "Jeden Tag kommen neue Riesen von den Gipfeln. Jeden Tag schicken wir sie zurück. Heute seid Ihr dran.",
        "objective": "Besiegt 8 Eisriesen am Eisriesenhorst.",
        "objectives": [{"type": "kill", "mob": ["eisriese", "eisriesenschamane"], "count": 8, "text": "Eisriesen besiegt"}],
        "complete": "Gute Arbeit. Morgen wieder.",
        "rewards": {"xp": 2000, "copper": 800, "rep": {"eisenbart": 350}, "currency": {"muenzen_eisenbart": 3}},
    },
    "taegliche_bergwacht": {
        "type": "daily", "title": "Patrouille der Bergwacht", "giver": "kragg", "ender": "kragg", "level": 16, "min_level": 14,
        "text": "Die tägliche Patrouille. Yetis, Wölfe, Luchse – irgendwas versucht immer, die Straße zu fressen.",
        "objective": "Besiegt 10 Yetis, Frostwölfe oder Schneeluchse.",
        "objectives": [{"type": "kill", "mob": ["yeti", "frostwolf", "schneeluchs"], "count": 10, "text": "Raubtiere vertrieben"}],
        "complete": "Die Straße ist frei. Für heute.",
        "rewards": {"xp": 1400, "copper": 500, "rep": {"eisenbart": 250}, "currency": {"muenzen_eisenbart": 2}},
    },
    "der_frostkoenig_muss_fallen": {
        "type": "weekly", "title": "Der Frostkönig muss fallen", "giver": "brogar", "ender": "brogar", "level": 24, "min_level": 22,
        "text": "Hrimgar erhebt sich jede Woche aufs Neue aus seinem Eisthron. Sammelt Eure Freunde und schickt ihn "
                "zurück in seinen Schlummer. (Weltboss – Gruppe empfohlen)",
        "objective": "Besiegt Hrimgar, den Frostkönig, am Eisriesenhorst und bringt seine Eiskrone.",
        "objectives": [{"type": "collect", "item": "hrimgars_krone", "count": 1}],
        "complete": "Die Krone des Frostkönigs! Die Riesen werden eine Woche lang Ruhe geben.",
        "rewards": {"xp": 5000, "copper": 3000, "rep": {"eisenbart": 1000}, "currency": {"muenzen_eisenbart": 10, "dungeonmarken": 5}},
    },
    # ================================================================== Kopfgelder (Anschlagbrett)
    "kopfgeld_weisszahn": {
        "type": "bounty", "title": "Kopfgeld: Weißzahn", "giver": "board:frostklamm", "ender": "board:frostklamm",
        "level": 13, "min_level": 11,
        "text": "GESUCHT: Weißzahn, Leitwolf des Frostwolftals. Hat drei Schlitten und einen Postboten gefressen. "
                "Der Postbote wird nicht vermisst, die Schlitten schon.",
        "objective": "Besiegt Weißzahn im Frostwolftal.",
        "objectives": [{"type": "kill", "mob": "weisszahn", "count": 1}],
        "complete": "Kopfgeld ausgezahlt.",
        "rewards": {"xp": 1600, "copper": 900, "rep": {"eisenbart": 200}},
    },
    "kopfgeld_knurrbart": {
        "type": "bounty", "title": "Kopfgeld: Knurrbart", "giver": "board:frostklamm", "ender": "board:frostklamm",
        "level": 17, "min_level": 15,
        "text": "GESUCHT: Knurrbart, ehemaliger Vorarbeiter. Verweigert seit 80 Jahren den Feierabend. Gefährlich.",
        "objective": "Besiegt Knurrbart im Tiefenstollen.",
        "objectives": [{"type": "kill", "mob": "knurrbart", "count": 1}],
        "complete": "Kopfgeld ausgezahlt.",
        "rewards": {"xp": 2000, "copper": 1100, "rep": {"eisenbart": 250}},
    },
    "kopfgeld_schneepranke": {
        "type": "bounty", "title": "Kopfgeld: Schneepranke", "giver": "board:frostklamm", "ender": "board:frostklamm",
        "level": 19, "min_level": 17,
        "text": "GESUCHT: Schneepranke, Mutter der Yetis. Löst Lawinen aus, wenn sie niest. Und sie ist erkältet.",
        "objective": "Besiegt Schneepranke an den Yetihöhlen.",
        "objectives": [{"type": "kill", "mob": "schneepranke", "count": 1}],
        "complete": "Kopfgeld ausgezahlt.",
        "rewards": {"xp": 2300, "copper": 1300, "rep": {"eisenbart": 300}},
    },
    "kopfgeld_varga": {
        "type": "bounty", "title": "Kopfgeld: Glutbinderin Varga", "giver": "board:frostklamm", "ender": "board:frostklamm",
        "level": 23, "min_level": 21,
        "text": "GESUCHT: Glutbinderin Varga, Vorhut der Schwarzen Schmiede. Hat die Brücke am Weißen Grat geschmolzen.",
        "objective": "Besiegt Glutbinderin Varga im Schwarzeisen-Lager.",
        "objectives": [{"type": "kill", "mob": "glutbinder_varga", "count": 1}],
        "complete": "Kopfgeld ausgezahlt.",
        "rewards": {"xp": 2900, "copper": 1600, "rep": {"eisenbart": 400}},
    },
}
