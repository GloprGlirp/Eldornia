"""Quests der Grünmark (Stufe 1–10), der vergessenen Krypta und der geheimen Höhle."""
from .. import items as I

# Questgegenstände dieser Region
I.QUEST("grimbarts_kassenbuch", "Grimbarts Kassenbuch", "book-cover", "Voller Zahlen. Die meisten davon falsch addiert.", 1)
I.QUEST("reine_tauperle", "Reine Tauperle", "water-drop", "Ein Tautropfen, der nicht verdunstet.", 10)
I.QUEST("zerknitterte_karte", "Zerknitterte Schatzkarte", "treasure-map", "Ein Kreuz, ein Hügel und ein schlecht gezeichnetes Auge.", 1)
I.QUEST("krummnases_schluessel", "Krummnases Schlüssel", "key", "Passt bestimmt in eine große Truhe.", 1)
I.QUEST("trottels_liste", "Trottels Einkaufsliste", "scroll-unfurled", "\"1. Käse 2. mehr Käse 3. Gackerle füttern 4. Käse\"", 1)
I.QUEST("goldener_kaese", "Goldener Käse", "cheese-wedge", "Er riecht ... golden?", 1)
I.QUEST("eldenstein_depesche", "Versiegelte Depesche", "envelope", "Das Siegel zeigt zwei wachsame Augen.", 1)
I.ITEMS["zerknitterte_karte"]["starts_quest"] = "die_geheime_hoehle"

QUESTS = {
    # ================================================================== Hauptgeschichte
    "audienz_beim_herrscher": {
        "type": "main", "title": "Audienz beim Herrscher", "giver": "roderich", "ender": "simon", "level": 1, "min_level": 1,
        "text": "Ihr seid neu hier, was? Jeder Neuankömmling in Eldornia muss sich beim Herrscher vorstellen. So will es das "
                "Gesetz. Na gut, eigentlich will es nur Simon so. Aber er ist der Herrscher, also ist es Gesetz.\n\n"
                "Folgt der Straße nach Norden zur Burg Eldenstein und meldet Euch bei Simon, dem zweiäugigen Herrscher.",
        "objective": "Sprecht mit Simon auf Burg Eldenstein nördlich von Eichenau.",
        "complete": "Ah! Ein neues Gesicht! Ich sehe es ganz deutlich – mit BEIDEN Augen. Wisst Ihr, in Eldornia gibt es "
                    "Herrscher mit einem Auge, Herrscher mit drei Augen ... aber nur einen mit genau zwei. Mich.\n\n"
                    "Willkommen in meinem Reich, Abenteurer.",
        "rewards": {"xp": 90, "copper": 10, "rep": {"krone": 75}},
    },
    "ein_auge_auf_den_einaeugigen": {
        "type": "main", "title": "Ein Auge auf den Einäugigen", "giver": "simon", "ender": "einaeugiger_kobold", "level": 4,
        "min_level": 3, "prev": "audienz_beim_herrscher",
        "text": "Ich habe zwei Augen, Abenteurer. Und ich setze beide gut ein. Aber selbst zwei Augen können nicht "
                "überall sein.\n\nIn Eichenau treibt sich ein Kobold mit nur einem Auge herum. Er verkauft Dinge, "
                "die ... irgendwo herkommen. Geht hin und behaltet ihn im Auge. In einem Eurer beiden.",
        "objective": "Sprecht mit dem einäugigen Kobold am Ostrand von Eichenau.",
        "complete": "Psst! Was? Der Zweiäugige schickt dich? Hah! Einauge sieht mit einem Auge mehr als der mit zwei! "
                    "... Aber gut. Du siehst ehrlich aus. Ehrlich genug. Einauge hat Arbeit für dich.",
        "rewards": {"xp": 210, "copper": 15, "rep": {"krone": 75}},
    },
    "was_der_blinde_sieht": {
        "type": "main", "title": "Was der Blinde sieht", "giver": "blinde", "ender": "wache_krypta", "level": 8, "min_level": 7,
        "text": "Setz dich, Wanderer. Ich sehe nichts ... und doch sehe ich Dunkelheit. Sie kriecht unter dem alten "
                "Friedhof im Südwesten hervor. Die Toten der vergessenen Krypta schlafen nicht mehr.\n\n"
                "Geh zu Totenwächterin Elsbeth am Friedhof. Sie bewacht das Tor. Sag ihr, dass der Blinde dich schickt.",
        "objective": "Sprecht mit Totenwächterin Elsbeth am Friedhof der Vergessenen im Südwesten.",
        "complete": "Der Blinde schickt Euch? Dann ist es schlimmer, als ich dachte. Er irrt sich nie. Nie.",
        "rewards": {"xp": 260, "copper": 20},
    },
    "die_vergessene_krypta": {
        "type": "main", "title": "Die vergessene Krypta", "giver": "wache_krypta", "ender": "jonas", "level": 10, "min_level": 7,
        "prev": "was_der_blinde_sieht", "dungeon": "krypta",
        "text": "Vor langer Zeit war Sir Morgrath der edelste Ritter Eldornias. Er war der Lehrmeister von Jonas. "
                "Als er starb, wurde er in der Krypta beigesetzt. Doch etwas hat ihn wieder erweckt.\n\n"
                "Steigt hinab in die vergessene Krypta, besiegt Sir Morgrath und bringt sein Siegel zu Jonas. "
                "Er sollte es als Erster erfahren. (Dungeon – allein oder zu zweit)",
        "objective": "Besiegt Sir Morgrath in der vergessenen Krypta und bringt Morgraths Siegel zu Jonas.",
        "progress": "Ist es wahr? Ist mein alter Meister zurückgekehrt?",
        "complete": "Morgraths Siegel ... Also ist es wahr. Mein Meister hat endlich seine Ruhe gefunden. Danke. "
                    "Er hat mir alles beigebracht, was ich weiß: Ehre, Mut ... und wie man ein Schwert poliert.",
        "objectives": [{"type": "collect", "item": "morgraths_siegel", "count": 1}],
        "rewards": {"xp": 1100, "copper": 400, "rep": {"krone": 250}, "currency": {"dungeonmarken": 5}},
    },
    "der_herrscher_muss_es_wissen": {
        "type": "main", "title": "Der Herrscher muss es wissen", "giver": "jonas", "ender": "simon", "level": 10, "min_level": 7,
        "prev": "die_vergessene_krypta",
        "text": "Simon muss erfahren, was in der Krypta geschehen ist. Geht zu ihm und berichtet. Er wird Euch belohnen, "
                "wie es einem Helden Eldornias gebührt.",
        "objective": "Berichtet Simon auf Burg Eldenstein von Morgraths Fall.",
        "complete": "Morgrath ist gefallen? Das habe ich kommen sehen. Mit beiden Augen. Natürlich.\n\n"
                    "Ihr habt Eldornia gerettet, Abenteurer. Ab heute seid Ihr ein Held des Reiches. Wählt Eure Belohnung "
                    "aus meiner persönlichen Waffenkammer.",
        "rewards": {"xp": 1000, "copper": 500, "rep": {"krone": 500}, "title": "held_eldornias",
                    "choice": ["klinge_des_herrschers", "simons_zepter", "simons_jagdbogen", "simons_zweihaender",
                               "simons_katana", "simons_dolche"]},
    },
    "der_weg_nach_frostklamm": {
        "type": "main", "title": "Der Weg nach Frostklamm", "giver": "simon", "ender": "brogar", "level": 11, "min_level": 10,
        "prev": "der_herrscher_muss_es_wissen", "start_item": "eldenstein_depesche",
        "text": "Held, ich habe noch eine Bitte. Mit beiden Augen beobachte ich die Berge im Nordosten – und ich sehe "
                "Rauch über Frostklamm. Die Zwerge des Eisenbart-Klans bitten um Hilfe gegen die Eisriesen.\n\n"
                "Bringt diese Depesche zu König Brogar Eisenbart in der Zwergenfestung Hammerfeste. Der Pass beginnt "
                "nordöstlich des Rotdolch-Lagers. Kleidet Euch warm.",
        "objective": "Bringt Simons Depesche zu König Brogar Eisenbart in Hammerfeste (Frostklamm).",
        "complete": "Ein Brief vom zweiäugigen Simon? Hah! Sieht er immer noch alles doppelt? ... Ihr seid also der Held, "
                    "von dem hier alle reden. Gut. Wir können jede Axt gebrauchen. Willkommen in Frostklamm!",
        "rewards": {"xp": 1400, "copper": 300, "rep": {"krone": 250, "eisenbart": 500}},
    },
    # ================================================================== Eichenau
    "wolfsplage": {
        "type": "side", "title": "Wölfe vor den Toren", "giver": "roderich", "ender": "roderich", "level": 1, "min_level": 1,
        "text": "Westlich von Eichenau treiben sich Waldwölfe herum. Gestern haben sie Mutter Hildes Wäsche gefressen. "
                "Die WÄSCHE!\n\nErlegt 6 Waldwölfe im Westen des Dorfes, dann reden wir weiter.",
        "objective": "Erlegt 6 Waldwölfe.",
        "progress": "Die Wölfe heulen immer noch. Ich höre sie. Ihr nicht?",
        "complete": "Gut gemacht! Hilde wird sich freuen. Ihre neue Wäsche ist allerdings schon wieder schmutzig. "
                    "Nehmt das hier, Ihr habt es Euch verdient.",
        "objectives": [{"type": "kill", "mob": "waldwolf", "count": 6}],
        "rewards": {"xp": 170, "copper": 25, "rep": {"krone": 50},
                    "choice": ["rekrutenhandschuhe", "gewebte_handschuhe", "geschmeidige_handschuhe"]},
    },
    "graumaehne": {
        "type": "side", "title": "Der Rudelführer", "giver": "roderich", "ender": "roderich", "level": 4, "min_level": 3,
        "prev": "wolfsplage",
        "text": "Die Wölfe kommen zurück. Immer wieder. Meine Späher sagen, dass ein riesiger grauer Wolf das Rudel "
                "anführt: Graumähne. Solange er lebt, hören die Angriffe nicht auf.\n\n"
                "Ihr findet ihn tief im Wolfsforst im Nordwesten. Seid vorsichtig, er ist stärker als die anderen.",
        "objective": "Tötet Graumähne im Wolfsforst. (Elite)",
        "progress": "Lebt Graumähne noch?",
        "complete": "Graumähne ist tot? Bei Simons beiden Augen! Ihr seid wirklich ein Held. Nehmt diese Tränke.",
        "objectives": [{"type": "kill", "mob": "graumaehne", "count": 1}],
        "rewards": {"xp": 420, "copper": 110, "items": [("heiltrank", 3)], "rep": {"krone": 100}},
    },
    "schatten_im_forst": {
        "type": "side", "title": "Schatten im Forst", "giver": "roderich", "ender": "roderich", "level": 7, "min_level": 6,
        "prev": "graumaehne",
        "text": "Seit Graumähne tot ist, streifen schwarze Wölfe durch den tiefen Wolfsforst. Schattenwölfe. Sie jagen "
                "im Rudel und heulen so laut, dass sogar der Dorftrottel nicht mehr schlafen kann.\n\n"
                "Erlegt 8 Schattenwölfe im Westen des Wolfsforsts.",
        "objective": "Erlegt 8 Schattenwölfe im Westen des Wolfsforsts.",
        "progress": "Hört Ihr das Heulen?",
        "complete": "Endlich Ruhe. Der Dorftrottel schläft wieder. Er schnarcht zwar, aber das ist besser als Heulen.",
        "objectives": [{"type": "kill", "mob": "schattenwolf", "count": 8}],
        "rewards": {"xp": 650, "copper": 140, "rep": {"krone": 150}, "choice": ["wolfsfellumhang", "jaegerhandschuhe"]},
    },
    "wildschweinbraten": {
        "type": "side", "title": "Braten für den Schiefen Krug", "giver": "hilde", "ender": "hilde", "level": 3, "min_level": 2,
        "text": "Kind, du bist ja nur Haut und Knochen! Aber wenn du schon hier bist: Mir sind die Wildschweinkeulen "
                "ausgegangen, und ohne Braten trinken die Leute nur und singen. Fidelius singt dann auch. Das will keiner.\n\n"
                "Bring mir 6 Wildschweinkeulen von den Wildschweinen östlich des Dorfes.",
        "objective": "Bringt Mutter Hilde 6 Wildschweinkeulen.",
        "progress": "Ohne Keulen kein Braten. Ohne Braten singt Fidelius. Beeil dich!",
        "complete": "Prachtvolle Keulen! Jetzt gibt's endlich wieder Braten. Hier, nimm ein paar Portionen mit – und iss sie auch!",
        "objectives": [{"type": "collect", "item": "wildschweinkeule", "count": 6}],
        "rewards": {"xp": 310, "copper": 40, "items": [("wildschweinbraten", 5)]},
    },
    "ein_brief_fuer_kathi": {
        "type": "side", "title": "Ein Brief für Kathi", "giver": "fidelius", "ender": "kathi", "level": 2, "min_level": 1,
        "text": "Ihr habt ein ehrliches Gesicht! Und zwei Beine! Perfekt. Ich habe einen Brief für Kathi, die holde "
                "Burgmaid. Ein Liebesgedicht. Zweiunddreißig Strophen.\n\n"
                "Bringt ihn zu ihr auf die Burg Eldenstein. Und lest ihn nicht! ... Na gut, nur die erste Strophe.",
        "objective": "Bringt Fidelius' Brief zu Kathi auf Burg Eldenstein.",
        "complete": "Ein Brief? Von Fidelius? *liest* ... \"Deine Augen sind wie zwei Suppenteller\" ... \"so rund und "
                    "voller Brühe\" ... Oh je.\n\nSagt ihm, ich denke darüber nach. Und dass er Gedichte schreiben lernen soll.",
        "start_item": "liebesbrief",
        "rewards": {"xp": 160, "copper": 50},
    },
    "kathis_antwort": {
        "type": "side", "title": "Kathis Antwort", "giver": "kathi", "ender": "fidelius", "level": 3, "min_level": 2,
        "prev": "ein_brief_fuer_kathi",
        "text": "Bitte richtet Fidelius aus ... ach, wie sage ich das am besten ... dass ich seine Gedichte sehr ... laut "
                "finde. Und dass ich mich über eine Suppe mehr freuen würde als über zweiunddreißig Strophen.",
        "objective": "Überbringt Fidelius im Schiefen Krug Kathis Antwort.",
        "complete": "Eine Suppe? SIE WILL EINE SUPPE? Das ist ... das ist die romantischste Antwort aller Zeiten! "
                    "♪ Oh Kathi, holde Maid der Burg ... ♪ Danke, mein Freund!",
        "rewards": {"xp": 200, "copper": 40},
    },
    "baelle_fuer_den_gaukler": {
        "type": "side", "title": "Bälle für den Gaukler", "giver": "gaukelkobold", "ender": "gaukelkobold", "level": 3, "min_level": 2,
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
    "der_grosse_auftritt": {
        "type": "side", "title": "Der große Auftritt", "giver": "gaukelkobold", "ender": "gaukelkobold", "level": 4, "min_level": 3,
        "prev": "baelle_fuer_den_gaukler",
        "text": "Gaukelkobold plant großen Auftritt! Für ganz Eichenau! Aber Publikum muss kommen. Und Publikum kommt nur, "
                "wenn jemand jubelt.\n\nGeh zu Mutter Hilde, zum Blinden und zu Ewald und jubel für sie (/jubeln), "
                "damit sie gute Laune bekommen. Gute Laune = Publikum!",
        "objective": "Jubelt Mutter Hilde, dem Blinden und Ewald zu (Emote /jubeln in ihrer Nähe).",
        "progress": "Publikum? Gaukelkobold sieht kein Publikum!",
        "complete": "Sie kommen! Sie kommen alle! Sogar der Blinde! Er sagt, er sieht den Auftritt nicht, aber er hört "
                    "ihn sehr deutlich. Danke, Großfuß!",
        "objectives": [{"type": "emote", "emote": "jubeln", "npc": "hilde", "count": 1, "text": "Mutter Hilde zugejubelt"},
                       {"type": "emote", "emote": "jubeln", "npc": "blinde", "count": 1, "text": "Dem Blinden zugejubelt"},
                       {"type": "emote", "emote": "jubeln", "npc": "ewald", "count": 1, "text": "Ewald zugejubelt"}],
        "rewards": {"xp": 380, "copper": 60, "items": [("haustier_kerzenkobold", 1)]},
    },
    "plage_auf_dem_feld": {
        "type": "side", "title": "Plage auf dem Feld", "giver": "kaspar", "ender": "kaspar", "level": 3, "min_level": 2,
        "text": "Seht Ihr das? Meine Rüben! Angefressen! Alle! Die Wildschweine kommen jede Nacht und fressen "
                "sich durch meine Felder.\n\nErlegt 10 Wildschweine rund um meinen Hof, bevor sie auch noch die Mühle fressen.",
        "objective": "Erlegt 10 Wildschweine rund um Kaspars Hof.",
        "progress": "Ich höre sie schmatzen. Hört Ihr sie auch schmatzen?",
        "complete": "Endlich Ruhe auf dem Feld! Nehmt das als Dank. Meine Frau hat's gemacht. Oder gefunden.",
        "objectives": [{"type": "kill", "mob": "wildschwein", "count": 10}],
        "rewards": {"xp": 340, "copper": 60, "choice": ["bauernstiefel", "eichenstab", "wolfszahnaxt"]},
    },
    "gackerle_ist_weg": {
        "type": "side", "title": "Gackerle ist weg!", "giver": "dorftrottel", "ender": "dorftrottel", "level": 2, "min_level": 1,
        "text": "Gackerle ist weg! GACKERLE IST WEG! Gackerle ist mein Huhn. Ein goldenes Huhn! Na ja, gelb. Sehr gelb.\n\n"
                "Gestern hat es gesagt, dass es Bauer Kaspars Mühle sehen will. Also, es hat \"Gack\" gesagt. Aber ich "
                "hab's verstanden! Bitte bring Gackerle zurück!",
        "objective": "Findet Gackerle bei Bauer Kaspars Windmühle östlich des Dorfes und bringt es zurück.",
        "progress": "Gackerle? Gackerleee?",
        "complete": "GACKERLE! Da bist du ja! *drückt das Huhn* Es sagt danke! Also, es sagt \"Gack\". "
                    "Das heißt danke. Hier, meine Glücksfeder. Die hat Gackerle verloren. Oder ein anderer Vogel.",
        "objectives": [{"type": "collect", "item": "gackerle", "count": 1}],
        "rewards": {"xp": 220, "copper": 5, "items": [("glueckfeder", 1)]},
    },
    "trottels_grosser_tag": {
        "type": "hidden", "title": "Trottels großer Tag", "giver": "dorftrottel", "ender": "dorftrottel", "level": 6, "min_level": 5,
        "prev": "gackerle_ist_weg", "requires": ["der_grosse_auftritt"], "start_item": "trottels_liste",
        "text": "Psst. Heute ist mein großer Tag. Ich hab Geburtstag! Glaub ich. Oder Gackerle. Einer von uns.\n\n"
                "Ich hab eine Liste gemacht. Kannst du mir helfen? Der Gaukelkobold soll für mich jonglieren, Mutter Hilde "
                "soll mir einen goldenen Käse geben – und der Blinde soll mir sagen, was er sieht. Er sieht nie was. Das "
                "ist sein Trick!",
        "objective": "Bittet den Gaukelkobold um eine Vorstellung, holt bei Mutter Hilde den goldenen Käse und lasst Euch "
                     "vom Blinden die Zukunft deuten.",
        "progress": "Ist es schon mein Geburtstag? Oder noch?",
        "complete": "Ein goldener Käse! Ein Kunststück! Und der Blinde hat gesagt, ich werde eines Tages ein großer Held. "
                    "Oder ein großer Käse. Er hat genuschelt.\n\nDu bist mein bester Freund! Hier – Gackerles Küken. "
                    "Es mag dich lieber als mich. Das ist okay.",
        "objectives": [{"type": "talk", "npc": "gaukelkobold", "count": 1, "text": "Vorstellung des Gaukelkobolds gesehen",
                        "say": "Für den Trottel? Hoho! Gaukelkobold jongliert mit VIER Bällen! *plopp* ... drei Bällen!"},
                       {"type": "talk", "npc": "hilde", "count": 1, "text": "Goldenen Käse bei Mutter Hilde abgeholt",
                        "give": "goldener_kaese", "say": "Goldener Käse? Für den Trottel? Ach, warum nicht. Hier."},
                       {"type": "talk", "npc": "blinde", "count": 1, "text": "Zukunft vom Blinden gedeutet",
                        "say": "Ich sehe ... einen Helden. Oder einen Käse. Die Visionen sind heute etwas ... käsig."}],
        "rewards": {"xp": 600, "copper": 77, "items": [("haustier_gackerkueken", 1)], "title": "freund_des_trottels"},
        "remove_items": ["goldener_kaese"],
    },
    # ================================================================== Burg Eldenstein
    "kraeuter_fuer_die_suppe": {
        "type": "side", "title": "Kräuter für die Suppe", "giver": "kathi", "ender": "kathi", "level": 2, "min_level": 1,
        "text": "Oh, gut, dass Ihr da seid! Der Herrscher will Suppe, aber ich habe keine Kräuter mehr. Und eine Suppe "
                "ohne Kräuter ist nur heißes Wasser. Das merkt sogar Simon. Mit beiden Augen.\n\n"
                "Auf den Wiesen zwischen Burg und Dorf wächst Wiesenkraut. Bringt mir 6 Stück, bitte!",
        "objective": "Sammelt 6 Wiesenkraut auf den Wiesen zwischen Burg und Eichenau.",
        "progress": "Das Wasser kocht schon. Seit zwei Stunden.",
        "complete": "Wunderbar! Das duftet herrlich! Jetzt wird es eine richtige Suppe. Nehmt diesen Umhang, ich habe "
                    "ihn aus Kräuterresten genäht. Er riecht ein bisschen nach Suppe.",
        "objectives": [{"type": "collect", "item": "wiesenkraut", "count": 6}],
        "rewards": {"xp": 260, "copper": 20, "items": [("kraeuterumhang", 1), ("frisches_brot", 5)], "rep": {"krone": 75}},
    },
    "das_verlorene_medaillon": {
        "type": "side", "title": "Das verlorene Medaillon", "giver": "leonine", "ender": "leonine", "level": 5, "min_level": 4,
        "text": "Bitte, könnt Ihr mir helfen? Als ich Rosen am Waldrand gepflückt habe, haben mich Banditen der "
                "Rotdolch-Bande überfallen. Sie haben mein Medaillon gestohlen. Es war ein Geschenk meiner Mutter.\n\n"
                "Ihr Lager liegt nordöstlich der Burg. Einer von ihnen muss es haben.",
        "objective": "Holt Leonines Medaillon von den Rotdolch-Banditen zurück.",
        "progress": "Habt Ihr es gefunden? Silber, mit einer Rose darauf ...",
        "complete": "Mein Medaillon! Ihr habt es wirklich gefunden! Ich danke Euch von ganzem Herzen. "
                    "Nehmt einen dieser Ringe – sie gehörten meinem Vater.",
        "objectives": [{"type": "collect", "item": "leonines_medaillon", "count": 1}],
        "rewards": {"xp": 520, "copper": 80, "rep": {"krone": 150},
                    "choice": ["ring_standhaftigkeit", "ring_klarheit", "ring_der_schnelligkeit"]},
    },
    "rosen_fuer_leonine": {
        "type": "side", "title": "Rosen für den Garten", "giver": "leonine", "ender": "leonine", "level": 6, "min_level": 5,
        "prev": "das_verlorene_medaillon",
        "text": "Seit dem Überfall traue ich mich nicht mehr allein zum Waldrand. Aber die Rosen im Burggarten brauchen "
                "Tau, sonst welken sie. Am Ufer des Spiegelsees im Westen glitzern Tauperlen, die niemals verdunsten.\n\n"
                "Bringt mir bitte 5 reine Tauperlen.",
        "objective": "Sammelt 5 reine Tauperlen am Ufer des Spiegelsees.",
        "progress": "Die Rosen lassen schon die Köpfe hängen ...",
        "complete": "Seht nur, wie sie leuchten! Kathi sagt, Ihr seid ein Held. Ich sage, Ihr seid ein Freund.",
        "objectives": [{"type": "collect", "item": "reine_tauperle", "count": 5}],
        "rewards": {"xp": 480, "copper": 70, "rep": {"krone": 150}, "items": [("melonensaft", 5)]},
    },
    "die_rotdolche": {
        "type": "side", "title": "Die Rotdolch-Bande", "giver": "jonas", "ender": "jonas", "level": 5, "min_level": 4,
        "text": "Seid gegrüßt, Abenteurer. Ein Ritter dient dem Volk – und das Volk leidet unter der Rotdolch-Bande. "
                "Sie überfallen Händler, Bauern und Burgmaiden.\n\nIhr Lager liegt nordöstlich von hier. "
                "Zeigt ihnen, was Gerechtigkeit bedeutet: Besiegt 8 Rotdolch-Schläger und 5 Rotdolch-Armbrustschützen.",
        "objective": "Besiegt 8 Rotdolch-Schläger und 5 Rotdolch-Armbrustschützen.",
        "progress": "Für Ehre und für Eldornia! Kehrt zurück, wenn Eure Aufgabe erfüllt ist.",
        "complete": "Ausgezeichnet! Die Bande ist geschwächt. Ihr kämpft wie ein wahrer Ritter. Nehmt dies als Zeichen meines Respekts.",
        "objectives": [{"type": "kill", "mob": "bandit", "count": 8}, {"type": "kill", "mob": "armbrustschuetze", "count": 5}],
        "rewards": {"xp": 560, "copper": 120, "rep": {"krone": 200}, "choice": ["banditenweste", "schimmernde_robe", "rotdolch_kopftuch"]},
    },
    "grimbart_rotdolch": {
        "type": "side", "title": "Grimbart Rotdolch", "giver": "jonas", "ender": "jonas", "level": 7, "min_level": 5,
        "prev": "die_rotdolche",
        "text": "Die Bande ist geschwächt, aber ihr Anführer lebt noch: Grimbart Rotdolch. Er versteckt sich in seinem "
                "großen Zelt im Lager.\n\nGrimbart ist gefährlich – nehmt einen Gefährten mit, wenn Ihr könnt. "
                "Und achtet auf seinen Wirbelwind: Wenn er die Klingen kreisen lässt, geht ihm aus dem Weg!",
        "objective": "Besiegt Grimbart Rotdolch im Lager der Rotdolch-Bande. (Elite – Gruppe empfohlen)",
        "progress": "Grimbart lebt noch? Dann ist Eldornia nicht sicher.",
        "complete": "Grimbart ist gefallen! Ihr habt Eldornia einen großen Dienst erwiesen. Simon wird davon erfahren "
                    "– er hat es vermutlich ohnehin schon gesehen.",
        "objectives": [{"type": "kill", "mob": "grimbart", "count": 1}],
        "rewards": {"xp": 820, "copper": 300, "rep": {"krone": 350},
                    "choice": ["wachmannsschultern", "lehrlingsschultertuch", "lederschultern_spaeher"]},
    },
    # ================================================================== Kupferstollen
    "kerzen_der_tiefe": {
        "type": "side", "title": "Kerzen der Tiefe", "giver": "einaeugiger_kobold", "ender": "einaeugiger_kobold", "level": 6,
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
    "der_koboldkoenig": {
        "type": "side", "title": "Der Koboldkönig", "giver": "einaeugiger_kobold", "ender": "einaeugiger_kobold", "level": 8,
        "min_level": 6, "prev": "kerzen_der_tiefe",
        "text": "Psst! Ganz hinten im Stollen sitzt Goldbart. Koboldkönig! Hat eine Krone aus echtem Gold. Na ja, fast "
                "echtem. Einauge will die Krone. Für ... Studienzwecke.\n\nGoldbart erscheint nur selten. Wenn du ihn "
                "siehst – hau drauf! Und bring die Krone mit.",
        "objective": "Besiegt Goldbart, den Koboldkönig, im hinteren Kupferstollen (seltener Elitegegner).",
        "progress": "Goldbart lebt noch? Einauge wartet. Einauge ist geduldig. Nicht sehr.",
        "complete": "Goldbart besiegt? Und die Krone ...? Ach, du behältst sie? Na gut. Einauge gibt dir trotzdem Gold. "
                    "Gold für Goldbart. Hehehe.",
        "objectives": [{"type": "kill", "mob": "goldbart", "count": 1}],
        "rewards": {"xp": 900, "copper": 450},
    },
    "erz_fuer_die_schmiede": {
        "type": "side", "title": "Erz für die Schmiede", "giver": "gundolf", "ender": "gundolf", "level": 6, "min_level": 5,
        "text": "*Klong* Erz. Ich brauche Erz. Die Kobolde sitzen auf dem besten Kupfer der ganzen Grünmark.\n\n"
                "Geht zum Kupferstollen im Südosten und baut 6 Brocken Kupfererz ab. Dann schmiede ich Euch was Ordentliches. "
                "(Bergbau lernt Ihr bei Bergfried am Stollen.)",
        "objective": "Baut 6 Kupfererz am Kupferstollen im Südosten ab.",
        "progress": "*Klong* Kein Erz, keine Waffe.",
        "complete": "*Klong* Gutes Erz. Sehr gut. Hier, frisch geschmiedet. Sucht Euch eins aus.",
        "objectives": [{"type": "collect", "item": "kupfererz", "count": 6}],
        "rewards": {"xp": 620, "copper": 60,
                    "choice": ["gundolfs_breitschwert", "gluehender_kupferstab", "gundolfs_kurzbogen", "gundolfs_streitaxt",
                               "gundolfs_katana", "gundolfs_dolch", "stollenhammer"]},
    },
    "spinnen_im_suedwald": {
        "type": "side", "title": "Achtbeinige Plage", "giver": "gerbert", "ender": "gerbert", "level": 6, "min_level": 5,
        "text": "Für feines Leder braucht man feinen Faden. Und den feinsten Faden machen die Waldspinnen im Süden des "
                "Wolfsforsts. Leider beißen sie.\n\nBringt mir 6 Spinnenseide. Und wenn Ihr schon dabei seid: Erlegt ein "
                "paar mehr, damit meine Lehrlinge sich wieder in den Wald trauen.",
        "objective": "Bringt Gerbert 6 Spinnenseide und erlegt 8 Waldspinnen.",
        "progress": "Achtung, die beißen wirklich.",
        "complete": "Schöne Seide! Daraus mache ich etwas Feines. Für Euch habe ich auch etwas.",
        "objectives": [{"type": "collect", "item": "spinnenseide", "count": 6}, {"type": "kill", "mob": "waldspinne", "count": 8}],
        "rewards": {"xp": 640, "copper": 90, "items": [("lederbeutel", 1)]},
    },
    "ruhelose_geister": {
        "type": "side", "title": "Ruhelose Geister", "giver": "anselm", "ender": "anselm", "level": 8, "min_level": 7,
        "text": "Auf dem Friedhof der Vergessenen im Südwesten wandeln Geister. Sie suchen etwas – oder jemanden. "
                "Bevor wir ihnen Frieden schenken können, müssen wir sie aufhalten.\n\nErlöst 6 ruhelose Geister.",
        "objective": "Erlöst 6 ruhelose Geister auf dem Friedhof der Vergessenen.",
        "progress": "Das Licht ist mit Euch. Auch auf dem Friedhof.",
        "complete": "Ich spüre, wie die Unruhe nachlässt. Doch die Quelle liegt tiefer – in der Krypta selbst.",
        "objectives": [{"type": "kill", "mob": "ruheloser_geist", "count": 6}],
        "rewards": {"xp": 720, "copper": 110, "rep": {"krone": 100}},
    },
    "ruhe_fuer_die_toten": {
        "type": "side", "title": "Ruhe für die Toten", "giver": "anselm", "ender": "anselm", "level": 9, "min_level": 7,
        "prev": "ruhelose_geister", "dungeon": "krypta",
        "text": "Unter dem Friedhof erheben sich die Toten. Ich spüre ihre Unruhe bis hierher.\n\n"
                "Steigt in die vergessene Krypta hinab und erlöst 10 ruhelose Skelette und 4 Knochenmagier.",
        "objective": "Erlöst 10 ruhelose Skelette und 4 Knochenmagier in der vergessenen Krypta.",
        "progress": "Die Toten verdienen Ruhe. Alle.",
        "complete": "Ich spüre es – die Unruhe lässt nach. Das Licht ist mit Euch. Nehmt diese gesegneten Handschuhe.",
        "objectives": [{"type": "kill", "mob": "skelett", "count": 10}, {"type": "kill", "mob": "knochenmagier", "count": 4}],
        "rewards": {"xp": 900, "copper": 200, "choice": ["gesegnete_handschuhe", "handschuhe_der_andacht", "handschuhe_des_pilgers"]},
    },
    "jonas_uebungsstunde": {
        "type": "side", "title": "Die Übungsstunde", "giver": "jonas", "ender": "jonas", "level": 1, "min_level": 1,
        "text": "Ihr wollt kämpfen lernen? Gut. Jeder fängt bei den Übungspuppen an – auch ich habe das getan. Damals "
                "waren die Puppen noch aus Stroh. Heute sind sie aus Eiche. Und sie schlagen nicht zurück. Meistens.\n\n"
                "Trefft die Übungspuppen im Burghof 8-mal mit Euren Fähigkeiten.",
        "objective": "Trefft eine Übungspuppe im Burghof 8-mal mit Fähigkeiten.",
        "progress": "Haltung! Und dann zuschlagen!",
        "complete": "Nicht schlecht für den Anfang. Ihr habt Talent. Viel Talent? Das wird sich zeigen.",
        "objectives": [{"type": "event", "event": "dummy_ability", "count": 8, "text": "Übungspuppe getroffen"}],
        "rewards": {"xp": 120, "copper": 10, "items": [("schwacher_heiltrank", 3)]},
    },
    "der_kreislauf_des_handels": {
        "type": "side", "title": "Der Kreislauf des Handels", "giver": "ludwig", "ender": "ludwig", "level": 5, "min_level": 5,
        "text": "Ah, ein neuer Kunde! Wisst Ihr, wie der Marktplatz funktioniert? Ihr bietet Waren an, andere kaufen sie, "
                "ich nehme eine kleine Gebühr. Ein wunderbares System. Vor allem für mich.\n\n"
                "Stellt irgendeinen Gegenstand auf dem Marktplatz ein und sprecht dann wieder mit mir.",
        "objective": "Stellt einen Gegenstand auf dem Marktplatz ein.",
        "progress": "Na, schon etwas eingestellt?",
        "complete": "Sehr schön! Und denkt daran: Auf dem Marktplatz bestimmt Ihr den Preis. Fast immer.",
        "objectives": [{"type": "event", "event": "market_post", "count": 1, "text": "Angebot eingestellt"}],
        "rewards": {"xp": 250, "copper": 100},
    },
    # ================================================================== Tägliche Aufträge (Ruf: Krone von Eldenstein)
    "taeglich_wolfsjagd": {
        "type": "daily", "title": "Täglich: Wolfsjagd", "giver": "roderich", "ender": "roderich", "level": 8, "min_level": 8,
        "prev": "schatten_im_forst",
        "text": "Die Wölfe hören nie auf. Jeden Tag kommen neue. Jeden Tag braucht es neue Jäger.\n\n"
                "Erlegt 10 Wald- oder Schattenwölfe.",
        "objective": "Erlegt 10 Wald- oder Schattenwölfe. (Täglich)",
        "progress": "Morgen wieder?",
        "complete": "Danke. Bis morgen.",
        "objectives": [{"type": "kill", "mob": ["waldwolf", "schattenwolf"], "count": 10, "text": "Wölfe erlegt"}],
        "rewards": {"xp": 700, "copper": 300, "rep": {"krone": 250}, "currency": {"muenzen_krone": 2}},
    },
    "taeglich_suppe": {
        "type": "daily", "title": "Täglich: Suppe des Tages", "giver": "kathi", "ender": "kathi", "level": 5, "min_level": 5,
        "prev": "kraeuter_fuer_die_suppe",
        "text": "Simon will jeden Tag Suppe. JEDEN TAG. Bringt mir bitte 8 Wiesenkraut.",
        "objective": "Sammelt 8 Wiesenkraut. (Täglich)",
        "progress": "Das Wasser kocht schon wieder.",
        "complete": "Danke! Morgen dann wieder, ja?",
        "objectives": [{"type": "collect", "item": "wiesenkraut", "count": 8}],
        "rewards": {"xp": 500, "copper": 200, "rep": {"krone": 250}, "currency": {"muenzen_krone": 2}},
    },
    "taeglich_rotdolch": {
        "type": "daily", "title": "Täglich: Patrouille gegen die Rotdolche", "giver": "jonas", "ender": "jonas", "level": 8,
        "min_level": 8, "prev": "grimbart_rotdolch",
        "text": "Die Rotdolche haben einen neuen Anführer gewählt. Er ist genauso schlimm wie der alte. Patrouilliert "
                "durch ihr Lager und besiegt 10 Banditen.",
        "objective": "Besiegt 10 Rotdolch-Banditen. (Täglich)",
        "progress": "Für Ehre und für Eldornia!",
        "complete": "Gute Arbeit, wie immer.",
        "objectives": [{"type": "kill", "mob": ["bandit", "armbrustschuetze", "rotdolch_heiler"], "count": 10, "text": "Rotdolche besiegt"}],
        "rewards": {"xp": 750, "copper": 350, "rep": {"krone": 350}, "currency": {"muenzen_krone": 3}},
    },
    # ================================================================== Wöchentliche Herausforderungen
    "woechentlich_krypta": {
        "type": "weekly", "title": "Wöchentlich: Die ewige Wacht", "giver": "wache_krypta", "ender": "wache_krypta", "level": 10,
        "min_level": 10, "prev": "die_vergessene_krypta", "dungeon": "krypta",
        "text": "Morgrath erhebt sich immer wieder. Jede Woche. Ich weiß nicht, wer ihn ruft – aber jemand muss ihn "
                "zurück ins Grab schicken.\n\nBesiegt Sir Morgrath (beliebiger Schwierigkeitsgrad).",
        "objective": "Besiegt Sir Morgrath in der vergessenen Krypta. (Wöchentlich)",
        "progress": "Er wacht noch.",
        "complete": "Wieder eine Woche Ruhe. Danke.",
        "objectives": [{"type": "kill", "mob": "morgrath", "count": 1}],
        "rewards": {"xp": 1500, "copper": 800, "currency": {"dungeonmarken": 10}, "rep": {"krone": 500}},
    },
    "woechentlich_mutterborke": {
        "type": "weekly", "title": "Wöchentlich: Die Uralte Eiche", "giver": "ewald", "ender": "ewald", "level": 11, "min_level": 10,
        "text": "Hört, hört! Im Hain der Uralten Eiche im Nordwesten erwacht Mutterborke! Sie ist so groß wie die Burg "
                "und doppelt so schlecht gelaunt. Sammelt Eure Freunde und besiegt sie!",
        "objective": "Besiegt den Weltboss Mutterborke im Hain der Uralten Eiche. (Wöchentlich, Gruppe)",
        "progress": "Hört, hört! Sie lebt noch!",
        "complete": "Hört, hört! Mutterborke ist gefallen! Ganz Eichenau jubelt! Na ja, der Dorftrottel jubelt.",
        "objectives": [{"type": "kill", "mob": "mutterborke", "count": 1}],
        "rewards": {"xp": 2000, "copper": 1000, "currency": {"dungeonmarken": 15}, "rep": {"krone": 750}},
    },
    # ================================================================== Kopfgelder (Anschlagbrett)
    "kopfgeld_einohr": {
        "type": "bounty", "title": "Kopfgeld: Einohr", "giver": "board:gruenmark", "ender": "board:gruenmark", "level": 7, "min_level": 6,
        "repeat": "daily",
        "text": "GESUCHT: EINOHR, der alte Wilderer.\nZuletzt gesehen im westlichen Wolfsforst. Bewaffnet mit Bogen und "
                "schlechter Laune. Belohnung: 2 Silber.\n– Hauptmann Roderich",
        "objective": "Besiegt Einohr im westlichen Wolfsforst und kehrt zum Anschlagbrett zurück.",
        "complete": "Ihr reißt das Plakat ab. In der Kassette darunter liegt die Belohnung.",
        "objectives": [{"type": "kill", "mob": "einohr", "count": 1}],
        "rewards": {"xp": 600, "copper": 200, "rep": {"krone": 150}},
    },
    "kopfgeld_goldbart": {
        "type": "bounty", "title": "Kopfgeld: Goldbart", "giver": "board:gruenmark", "ender": "board:gruenmark", "level": 8, "min_level": 7,
        "repeat": "daily",
        "text": "GESUCHT: GOLDBART, selbsternannter Koboldkönig.\nWegen Diebstahls von 412 Kerzen. Belohnung: 3 Silber.\n– Gundolf",
        "objective": "Besiegt Goldbart im Kupferstollen und kehrt zum Anschlagbrett zurück.",
        "complete": "Ihr reißt das Plakat ab. In der Kassette darunter liegt die Belohnung.",
        "objectives": [{"type": "kill", "mob": "goldbart", "count": 1}],
        "rewards": {"xp": 700, "copper": 300, "rep": {"krone": 150}},
    },
    "kopfgeld_grimbart": {
        "type": "bounty", "title": "Kopfgeld: Grimbart Rotdolch", "giver": "board:gruenmark", "ender": "board:gruenmark", "level": 7,
        "min_level": 6, "repeat": "daily",
        "text": "GESUCHT: GRIMBART ROTDOLCH, Anführer der Rotdolch-Bande.\nTot oder lebendig. Lieber tot. Belohnung: 2 Silber 50 Kupfer.\n– Jonas",
        "objective": "Besiegt Grimbart Rotdolch und kehrt zum Anschlagbrett zurück.",
        "complete": "Ihr reißt das Plakat ab. In der Kassette darunter liegt die Belohnung.",
        "objectives": [{"type": "kill", "mob": "grimbart", "count": 1}],
        "rewards": {"xp": 650, "copper": 250, "rep": {"krone": 150}},
    },
    # ================================================================== Versteckte Quest: Die geheime Höhle
    "die_geheime_hoehle": {
        "type": "hidden", "title": "Die geheime Höhle", "giver": "item", "ender": "einaeugiger_kobold", "level": 9, "min_level": 7,
        "text": "Die zerknitterte Karte zeigt die Grünmark. Ein Kreuz markiert einen Hügel im äußersten Südosten, hinter "
                "dem Kupferstollen. Daneben ist ein Auge gezeichnet – nur eins. Darunter steht in krakeliger Schrift: "
                "\"Einauges Versteck. NICHT FÜR GOLDBART.\"",
        "objective": "Findet die geheime Höhle auf dem Hügel im Südosten, besiegt ihren Wächter und öffnet die Schatztruhe. "
                     "Sprecht dann mit dem einäugigen Kobold.",
        "progress": "Was? Welche Karte? Einauge kennt keine Karte. Einauge hat nie eine Karte gezeichnet.",
        "complete": "Du ... du hast Einauges Versteck gefunden?! Und Krummnase besiegt? ... Na gut. NA GUT. Behalte, was "
                    "du gefunden hast. Aber sag es niemandem! Vor allem nicht dem Zweiäugigen!",
        "objectives": [{"type": "explore", "zone": "hoehle_einauge", "count": 1, "text": "Geheime Höhle gefunden"},
                       {"type": "kill", "mob": "krummnase", "count": 1},
                       {"type": "event", "event": "chest_hoehle", "count": 1, "text": "Schatztruhe geöffnet"}],
        "rewards": {"xp": 1200, "copper": 777, "choice": ["einauges_glasauge", "einauges_umhang"], "title": None},
    },
    # ================================================================== Klassenquests (Stufe 10)
    "klasse_ritter": {
        "type": "class", "cls": "ritter", "title": "Der Schwur des Schildträgers", "giver": "jonas", "ender": "jonas", "level": 10,
        "min_level": 10,
        "text": "Ihr tragt das Schwert eines Ritters. Doch ein Ritter wird erst durch seinen Schwur geboren. Wer andere "
                "schützen will, muss standhalten.\n\nBlockt oder pariert 15 Angriffe und besiegt 10 Rotdolche, die "
                "unschuldige Bürger bedrohen. Dann sprecht den Schwur mit mir.",
        "objective": "Blockt oder pariert 15 Angriffe und besiegt 10 Rotdolch-Banditen.",
        "progress": "Ein Ritter weicht nicht zurück.",
        "complete": "Kniet nieder. ... Ich, Jonas, Ritter von Eldenstein, nehme Euren Schwur an. Von nun an seid Ihr ein "
                    "Schildträger. Tragt dieses Wappen mit Ehre.",
        "objectives": [{"type": "event", "event": ["block", "parry"], "count": 15, "text": "Angriffe abgewehrt"},
                       {"type": "kill", "mob": ["bandit", "armbrustschuetze", "rotdolch_heiler"], "count": 10, "text": "Rotdolche besiegt"}],
        "rewards": {"xp": 900, "copper": 200, "title": "schildtraeger", "items": [("skin_ritter", 1)]},
    },
    "klasse_magier": {
        "type": "class", "cls": "magier", "title": "Das Feuer zähmen", "giver": "isolde", "ender": "isolde", "level": 10,
        "min_level": 10,
        "text": "Jeder Lehrling kann einen Feuerball werfen. Doch nur ein Magier weiß, wann er es NICHT tun sollte. "
                "Beweist mir Kontrolle: Unterbrecht 5 Zauber Eurer Gegner und besiegt 8 Waldspinnen – sie fürchten das Feuer.",
        "objective": "Unterbrecht 5 gegnerische Zauber und besiegt 8 Waldspinnen.",
        "progress": "Kontrolle, Schüler. Kontrolle.",
        "complete": "Ausgezeichnet. Ihr seid nun ein Flammenweber. Diese Robe wird Euch an diesen Tag erinnern.",
        "objectives": [{"type": "event", "event": "interrupts", "count": 5, "text": "Zauber unterbrochen"},
                       {"type": "kill", "mob": "waldspinne", "count": 8}],
        "rewards": {"xp": 900, "copper": 200, "title": "flammenweber", "items": [("skin_magier", 1)]},
    },
    "klasse_raeuber": {
        "type": "class", "cls": "raeuber", "title": "Ein Schatten unter Schatten", "giver": "schattenfinger", "ender": "schattenfinger",
        "level": 10, "min_level": 10,
        "text": "Grimbart Rotdolch führt Buch über alles, was er stiehlt. Ein Dieb, der Buch führt! Lächerlich. Bringt mir "
                "sein Kassenbuch – und wenn Ihr schon dabei seid, greift 5 Gegner aus der Tarnung heraus an.",
        "objective": "Bringt Grimbarts Kassenbuch und eröffnet 5 Kämpfe aus der Tarnung.",
        "progress": "Wer gesehen wird, hat schon verloren.",
        "complete": "Hm. Nicht schlecht. Ihr seid jetzt eine Schattenhand. Tragt diese Kapuze – oder lasst es. Niemand wird es merken.",
        "objectives": [{"type": "collect", "item": "grimbarts_kassenbuch", "count": 1},
                       {"type": "event", "event": "stealth_opener", "count": 5, "text": "Angriffe aus der Tarnung"}],
        "rewards": {"xp": 900, "copper": 250, "title": "schattenhand", "items": [("skin_raeuber", 1)]},
    },
    "klasse_samurai": {
        "type": "class", "cls": "samurai", "title": "Der Weg der Klinge", "giver": "kenjiro", "ender": "kenjiro", "level": 10,
        "min_level": 10,
        "text": "Die Klinge folgt dem Atem. Und der Atem folgt dem Gegner. Pariert 12 Angriffe und besiegt dann den "
                "Rudelführer Graumähne – allein, wenn Ihr den Weg ehrt.",
        "objective": "Pariert 12 Angriffe und besiegt Graumähne.",
        "progress": "Atme.",
        "complete": "Ihr habt den Weg gesehen. Von heute an nennt man Euch Klingenweiser. Dieser Helm gehörte meinem Meister.",
        "objectives": [{"type": "event", "event": "parry", "count": 12, "text": "Angriffe pariert"},
                       {"type": "kill", "mob": "graumaehne", "count": 1}],
        "rewards": {"xp": 900, "copper": 200, "title": "klingenweiser", "items": [("skin_samurai", 1)]},
    },
    "klasse_bogenschuetze": {
        "type": "class", "cls": "bogenschuetze", "title": "Das Auge des Falken", "giver": "wilma", "ender": "wilma", "level": 10,
        "min_level": 10,
        "text": "Einohr ist der beste Schütze der Grünmark. Oder war es, bis Ihr kamt? Besiegt ihn – und trefft dabei "
                "10 Gegner aus mehr als 25 Metern Entfernung.",
        "objective": "Trefft 10 Gegner aus über 25 m Entfernung und besiegt Einohr.",
        "progress": "Ruhig atmen. Wind beachten.",
        "complete": "Einohrs Bogen hat ausgedient. Ihr habt das Auge des Falken. Nehmt diesen Federumhang.",
        "objectives": [{"type": "event", "event": "long_shot", "count": 10, "text": "Weitschüsse"},
                       {"type": "kill", "mob": "einohr", "count": 1}],
        "rewards": {"xp": 900, "copper": 200, "title": "falkenauge", "items": [("skin_bogenschuetze", 1)]},
    },
    "klasse_barbar": {
        "type": "class", "cls": "barbar", "title": "Blut und Zorn", "giver": "thorgrim", "ender": "thorgrim", "level": 10,
        "min_level": 10,
        "text": "HA! Du willst wissen, was Zorn ist? Zorn ist, wenn ein Rudel Schattenwölfe dich umzingelt und du LACHST! "
                "Erschlag 15 Schattenwölfe und sammle 100 Wut in einem einzigen Kampf!",
        "objective": "Erschlagt 15 Schattenwölfe und erreicht im Kampf 100 Wut.",
        "progress": "MEHR ZORN!",
        "complete": "HAHA! Das war Zorn! Ab heute bist du eine Zornesfaust! Nimm diese Schädel – trag sie mit Stolz!",
        "objectives": [{"type": "kill", "mob": "schattenwolf", "count": 15},
                       {"type": "event", "event": "rage_full", "count": 1, "text": "Volle Wut erreicht"}],
        "rewards": {"xp": 900, "copper": 200, "title": "zornesfaust", "items": [("skin_barbar", 1)]},
    },
    "klasse_druide": {
        "type": "class", "cls": "druide", "title": "Hüter des Waldes", "giver": "eibenhain", "ender": "eibenhain", "level": 10,
        "min_level": 10,
        "text": "Der Spiegelsee ist das Herz der Grünmark. Seine Tauperlen tragen das Leben des Waldes. Sammelt 5 davon "
                "und heilt andere Abenteurer – denn ein Druide hütet nicht nur Bäume.",
        "objective": "Sammelt 5 reine Tauperlen und wirkt 10 Heilzauber auf andere Spieler.",
        "progress": "Höre, wie der Wald atmet.",
        "complete": "Der Wald hat Euch angenommen. Tragt diese Geweihkrone, Waldhüter.",
        "objectives": [{"type": "collect", "item": "reine_tauperle", "count": 5},
                       {"type": "event", "event": "heal_other", "count": 10, "text": "Andere geheilt"}],
        "rewards": {"xp": 900, "copper": 200, "title": "waldhueter", "items": [("skin_druide", 1)]},
    },
    "klasse_totenbeschwoerer": {
        "type": "class", "cls": "totenbeschwoerer", "title": "Herr der Knochen", "giver": "morwen", "ender": "morwen", "level": 10,
        "min_level": 10,
        "text": "Die Geister des Friedhofs tragen Essenzen in sich, rein und kalt. Bringt mir 6 davon. Und lasst Eure "
                "Diener 20 Gegner erschlagen – ein Meister kämpft nicht selbst.",
        "objective": "Bringt Morwen 6 ruhelose Geisteressenzen und lasst Eure Diener 20 Gegner besiegen.",
        "progress": "Die Toten sind geduldig. Ich nicht.",
        "complete": "Gut. Sehr gut. Die Knochen gehorchen Euch, Knochenfürst. Diese Krone ist aus den Gebeinen eines alten Königs.",
        "objectives": [{"type": "collect", "item": "geisteressenz", "count": 6},
                       {"type": "event", "event": "pet_kill", "count": 20, "text": "Gegner durch Diener besiegt"}],
        "rewards": {"xp": 900, "copper": 200, "title": "knochenfuerst", "items": [("skin_totenbeschwoerer", 1)]},
    },
}
