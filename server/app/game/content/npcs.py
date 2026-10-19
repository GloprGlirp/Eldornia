"""Freundliche NPCs von Eldornia.

Blickrichtung (rot): 0 = Norden (-z), pi = Süden (+z), -pi/2 = Osten (+x), pi/2 = Westen (-x)
look: Aussehen für den Client (Farben als Hex, Frisur, Kleidung, Besonderheiten)
"""
import math

N, S, E, W = 0.0, math.pi, -math.pi / 2, math.pi / 2
NE, NW, SE, SW = -math.pi / 4, math.pi / 4, -3 * math.pi / 4, 3 * math.pi / 4

NPCS = {
    "simon": {
        "name": "Simon", "title": "Der zweiäugige Herrscher", "lvl": 30, "pos": [0, -119], "rot": S,
        "model": "human", "scale": 1.12,
        "look": {"skin": "#e8b89a", "hair": "#4a2c17", "hair_style": "short", "beard": "#4a2c17", "top": "#6b1d3a",
                 "bottom": "#2b1a2f", "cape": "#8f1d2c", "crown": True, "eyes": "big", "anim": "throne"},
        "greeting": "Seid gegrüßt auf Burg Eldenstein. Ich bin Simon, Herrscher über Eldornia. "
                    "Man nennt mich den zweiäugigen Herrscher – denn ich sehe alles. Mit beiden Augen. Gleichzeitig.",
        "barks": ["Mit beiden Augen wache ich über Eldornia.",
                  "Ein guter Herrscher sieht alles. Ich sehe sogar doppelt so viel wie ein einäugiger.",
                  "Kathi! Ist die Suppe schon fertig?"],
    },
    "kathi": {
        "name": "Kathi", "title": "Die holde Burgmaid", "lvl": 12, "pos": [-21, -104], "rot": E,
        "model": "human", "scale": 0.95,
        "look": {"skin": "#f2c9a8", "hair": "#e3c06a", "hair_style": "long", "top": "#e88fb0", "bottom": "#e88fb0",
                 "dress": True, "apron": "#f4f0e6", "anim": "idle"},
        "greeting": "Oh, ein Besucher! Willkommen auf der Burg. Möchtet Ihr etwas Suppe? Sie ist noch nicht fertig. "
                    "Eigentlich ist sie noch nicht mal angefangen.",
        "barks": ["Ach, wo bleiben nur meine Kräuter? Die Suppe schmeckt sonst nach gar nichts!",
                  "Leonine, hast du den großen Kochlöffel gesehen?",
                  "Ein bisschen Thymian, ein bisschen Liebe ... und viel Salz."],
    },
    "leonine": {
        "name": "Leonine", "title": "Burgmaid", "lvl": 12, "pos": [21, -104], "rot": W,
        "model": "human", "scale": 0.95,
        "look": {"skin": "#d9a582", "hair": "#2a1a12", "hair_style": "braid", "top": "#7fb3d9", "bottom": "#7fb3d9",
                 "dress": True, "apron": "#f4f0e6", "anim": "idle"},
        "greeting": "Willkommen auf Eldenstein. Ich bin Leonine. Ich kümmere mich um den Rosengarten ... "
                    "und um alles andere, was Kathi vergisst.",
        "barks": ["Mein Medaillon ... es war ein Geschenk meiner Mutter.",
                  "Die Rosen blühen dieses Jahr besonders schön.",
                  "Kathi, die Suppe kocht über!"],
    },
    "jonas": {
        "name": "Jonas", "title": "Der edle Ritter", "lvl": 20, "pos": [20, -72], "rot": S,
        "model": "human", "scale": 1.08,
        "look": {"skin": "#e0ae8c", "hair": "#c98a3a", "hair_style": "short", "top": "#c9ccd6", "bottom": "#8b8f99",
                 "armor": True, "cape": "#2d5aa8", "held": "sword", "shield": True, "anim": "idle"},
        "greeting": "Seid gegrüßt! Ich bin Jonas, Ritter von Eldenstein. Ein Ritter dient nicht sich selbst, "
                    "sondern dem Volk. Wie kann ich Euch helfen – oder besser: Wie könnt Ihr Eldornia helfen?",
        "barks": ["Für Ehre und für Eldornia!",
                  "Das Schwert ist nur so edel wie die Hand, die es führt.",
                  "Haltung! Schild hoch! ... Ach, ich rede schon wieder mit den Übungspuppen."],
    },
    "roderich": {
        "name": "Roderich", "title": "Hauptmann der Wache", "lvl": 20, "pos": [-5, -5], "rot": SE,
        "model": "human", "scale": 1.05,
        "look": {"skin": "#d49a7a", "hair": "#6b6b6b", "hair_style": "short", "beard": "#6b6b6b", "top": "#3a5b8c",
                 "bottom": "#4a4a52", "armor": True, "held": "spear", "helm": True, "anim": "idle"},
        "greeting": "Halt! Wer da? ... Ach, ein Abenteurer. Willkommen in Eichenau. Benehmt Euch, dann gibt es keinen Ärger.",
        "barks": ["Haltet die Augen offen. Die Rotdolche werden immer frecher.",
                  "Ruhe bewahren, Bürger. Die Wache ist wachsam.",
                  "Hat jemand den Dorftrottel gesehen? Er wollte wieder den Brunnen umarmen."],
    },
    "dorftrottel": {
        "name": "Der Dorftrottel", "title": "Er meint es gut", "lvl": 1, "pos": [9, 9], "rot": S,
        "model": "human", "scale": 0.98, "wander": 7,
        "look": {"skin": "#f0c4a0", "hair": "#c4632f", "hair_style": "wild", "top": "#9a8a3a", "bottom": "#6a4a2a",
                 "patches": True, "anim": "goofy"},
        "greeting": "Hallo! Hallo! Ich hab heute schon dreimal bis zehn gezählt. Fast ohne Fehler! Willst du mal sehen? Eins, zwei, ... Kartoffel ...",
        "barks": ["Wenn ich ganz fest an Käse denke, wird er dann zu Käse?",
                  "Gackerle? Gackerleee?!",
                  "Der Himmel ist heute wieder sehr ... oben.",
                  "Warum heißt es Brunnen, wenn er gar nicht brennt?",
                  "Ich bin nicht dumm. Ich hab nur sehr viel Platz im Kopf.",
                  "Der Blinde hat gesagt, ich sehe mehr als alle anderen. Ich glaub, er hat mich verwechselt."],
    },
    "blinde": {
        "name": "Der Blinde", "title": "Seher von Eichenau", "lvl": 25, "pos": [4.5, 21.5], "rot": W,
        "model": "human", "scale": 1.0,
        "look": {"skin": "#c9a084", "hair": "#e0e0e0", "hair_style": "long", "beard": "#e0e0e0", "top": "#5a4a6a",
                 "bottom": "#3a3040", "robe": True, "blindfold": True, "held": "staff", "anim": "sit"},
        "greeting": "Ich höre Schritte. Leichte Schritte, schwere Gedanken. Setz dich zu mir, Wanderer. "
                    "Ich sehe nichts ... und doch sehe ich genug.",
        "barks": ["Ich sehe ... nichts. Und doch sehe ich mehr als ihr.",
                  "Unter der Erde regt sich etwas Altes ...",
                  "Die Toten der Krypta schlafen unruhig.",
                  "Der Dorftrottel ist klüger, als ihr alle glaubt. Nicht viel klüger. Aber klüger."],
    },
    "gaukelkobold": {
        "name": "Der Gaukelkobold", "title": "Gaukler & Krimskrams", "lvl": 8, "pos": [-7, 27], "rot": S,
        "model": "kobold", "scale": 0.8,
        "look": {"skin": "#9c6b3c", "top": "#d43c8f", "bottom": "#2fb5a8", "hat": "jester", "anim": "juggle"},
        "greeting": "Hoho! Großfuß! Komm, komm! Gaukelkobold jongliert für dich! Drei Bälle! Früher sieben. Lange Geschichte.",
        "barks": ["Hereinspaziert! Drei Bälle, zwei Hände, ein Kobold!",
                  "Gaukelkobold jongliert alles! Außer Fackeln. Fackeln nicht mehr.",
                  "Klimper-klimper, glitzer-glitzer, kaufen, kaufen!",
                  "Hopp! Hopp! ... Hoppla."],
        "vendor": ["heiltrank", "manatrank", "brot", "quellwasser"],
    },
    "einaeugiger_kobold": {
        "name": "Der einäugige Kobold", "title": "Hehler", "lvl": 9, "pos": [41, 26], "rot": W,
        "model": "kobold", "scale": 0.85,
        "look": {"skin": "#7d6a4a", "top": "#3a3a3a", "bottom": "#5a4a3a", "eyepatch": True, "hood": True,
                 "anim": "shifty"},
        "greeting": "Psst! Du! Ja, du. Willst du was kaufen? Nichts gestohlen. Alles nur ... gefunden. Vor dem Besitzer.",
        "barks": ["Einauge sieht alles. Na gut, die Hälfte.",
                  "Psst ... gute Ware, fast nicht verflucht!",
                  "Gaukelkobold ist Einauges Cousin. Oder Onkel. Kobolde zählen nicht so genau."],
        "vendor": ["zauberfoliant", "beschlagener_schild", "wolfsfellumhang", "jaegerhandschuhe"],
    },
    "hilde": {
        "name": "Mutter Hilde", "title": "Wirtin des Schiefen Krugs", "lvl": 15, "pos": [-19, 11], "rot": E,
        "model": "human", "scale": 1.0,
        "look": {"skin": "#f0b896", "hair": "#8a8a8a", "hair_style": "bun", "top": "#8a5a3a", "bottom": "#5a3a2a",
                 "dress": True, "apron": "#f4f0e6", "anim": "idle"},
        "greeting": "Willkommen im Schiefen Krug! Setzt Euch, esst was – Ihr seht ja aus wie ein Gerippe aus der Krypta!",
        "barks": ["Frisches Brot! Und Braten, wenn mir endlich jemand Keulen bringt!",
                  "Fidelius, sing was Fröhliches! ... Nicht das Lied über Käse.",
                  "Wer nicht isst, kann auch nicht kämpfen!"],
        "vendor": ["brot", "quellwasser", "wildschweinbraten", "melonensaft"],
    },
    "fidelius": {
        "name": "Fidelius", "title": "Barde", "lvl": 10, "pos": [-17, 19], "rot": E,
        "model": "human", "scale": 0.97,
        "look": {"skin": "#f2c9a8", "hair": "#2a1a12", "hair_style": "short", "top": "#2f8a4a", "bottom": "#c9a43a",
                 "hat": "feather", "held": "lute", "anim": "lute"},
        "greeting": "Ein Zuhörer! Endlich! Ich bin Fidelius, Barde, Poet und – ganz unter uns – hoffnungslos verliebt.",
        "barks": ["♪ Oh Kathi, holde Maid der Burg, dein Lächeln strahlt wie ... äh ... die Burg! ♪",
                  "♪ Simon hat zwei Augen, zwei Augen hat er gar, und jedes sieht das Reich so klar! ♪",
                  "♪ Der Gaukelkobold, klein und flink, jongliert mit allem, was er find'! ♪",
                  "♪ Ein Ritter namens Jonas, so edel und so rein, der putzt sein Schwert im Mondenschein! ♪"],
    },
    "gundolf": {
        "name": "Gundolf", "title": "Schmied", "lvl": 15, "pos": [23, 14], "rot": W,
        "model": "human", "scale": 1.12,
        "look": {"skin": "#c98a6a", "hair": "#1a1a1a", "hair_style": "bald", "beard": "#3a2a1a", "top": "#5a3a2a",
                 "bottom": "#3a3a3a", "apron": "#4a3020", "held": "hammer", "anim": "anvil"},
        "greeting": "*Klong* Hm? Ein Kunde. Gut. Ich schmiede, Ihr kauft. So einfach ist das.",
        "barks": ["*Klong* *Klong* ... Erz! Ich brauche mehr Erz!",
                  "Heißes Eisen, kühler Kopf. So schmiedet man.",
                  "Jonas bringt sein Schwert jede Woche zum Polieren. Jede. Woche."],
        "vendor": ["rostiges_langschwert", "holzschild", "lehrlingsstab", "rekrutenweste", "rekrutenhose", "abgetragene_stiefel"],
    },
    "mira": {
        "name": "Mira", "title": "Gemischtwaren", "lvl": 10, "pos": [12, 29], "rot": N,
        "model": "human", "scale": 0.96,
        "look": {"skin": "#a9785a", "hair": "#1a1a1a", "hair_style": "bun", "top": "#c9862f", "bottom": "#6a3a5a",
                 "dress": True, "anim": "idle"},
        "greeting": "Gemischtwaren! Brot, Wasser, Tränke – alles, was ein Abenteurer zum Überleben braucht. Und ein bisschen mehr.",
        "barks": ["Frisches Brot, klares Wasser!", "Heiltränke! Wer heute einen kauft, stirbt morgen nicht!"],
        "vendor": ["brot", "quellwasser", "heiltrank", "manatrank"],
    },
    "anselm": {
        "name": "Bruder Anselm", "title": "Geistheiler", "lvl": 20, "pos": [-15, 44], "rot": S,
        "model": "human", "scale": 1.0,
        "look": {"skin": "#e8c0a0", "hair": "#a0a0a0", "hair_style": "tonsure", "top": "#e8e0c8", "bottom": "#e8e0c8",
                 "robe": True, "held": "book", "glow": "#fff3b0", "anim": "idle"},
        "greeting": "Möge das Licht Euch leiten, Wanderer. Wer in Grünmark fällt, erwacht hier bei mir wieder.",
        "barks": ["Möge das Licht mit Euch sein.", "Die Toten verdienen Ruhe. Alle."],
    },
    "kaspar": {
        "name": "Bauer Kaspar", "title": "", "lvl": 8, "pos": [70, 27], "rot": E,
        "model": "human", "scale": 1.02,
        "look": {"skin": "#d4a07a", "hair": "#7a5a2a", "hair_style": "short", "beard": "#7a5a2a", "top": "#a85a3a",
                 "bottom": "#5a6a3a", "hat": "straw", "held": "pitchfork", "anim": "idle"},
        "greeting": "Tach. Ich bin Kaspar. Das ist mein Hof. Das sind meine Felder. Und das da sind NICHT meine Wildschweine!",
        "barks": ["Diese verflixten Wildschweine fressen mir die Rüben weg!",
                  "Hat jemand ein goldenes Huhn gesehen? Das ist nicht meins. Das gehört dem Dorftrottel."],
    },
    "ewald": {
        "name": "Ewald", "title": "Ausrufer", "lvl": 5, "pos": [16, 20], "rot": W,
        "model": "human", "scale": 1.0,
        "look": {"skin": "#ecbc98", "hair": "#b0b0b0", "hair_style": "short", "top": "#c9302c", "bottom": "#e8d8a0",
                 "hat": "feather", "held": "bell", "anim": "idle"},
        "greeting": "Hört, hört! Ewald, Ausrufer von Eichenau, zu Euren Diensten! Wer etwas verkünden will, "
                    "zahlt einen Kupfer. Wer nichts hören will, zahlt zwei.",
        "barks": ["Hört, hört! Der zweiäugige Herrscher Simon verkündet: Alle Augen auf die Wölfe im Westen!",
                  "Hört, hört! Die Rotdolch-Bande wurde nordöstlich gesichtet! Haltet eure Taschen fest!",
                  "Hört, hört! Der Dorftrottel hat sein Huhn verloren! Schon wieder!",
                  "Hört, hört! Im Kupferstollen klauen Kobolde Kerzen! Niemand weiß, warum!",
                  "Hört, hört! Es gibt nichts zu hören! ... Hört trotzdem!"],
    },
    "bodo": {
        "name": "Bodo", "title": "Angler", "lvl": 6, "pos": [-46, 4], "rot": W,
        "model": "human", "scale": 1.05,
        "look": {"skin": "#d9a07a", "hair": "#5a3a1a", "hair_style": "short", "beard": "#5a3a1a", "top": "#4a6a3a",
                 "bottom": "#4a3a2a", "hat": "straw", "held": "rod", "anim": "sit"},
        "greeting": "Psst! Nicht so laut, sonst beißen die Fische nicht. ... Die beißen sowieso nicht. Seit elf Jahren nicht.",
        "barks": ["Heute beißt bestimmt einer an. Bestimmt.",
                  "Im Spiegelsee lebt ein Hecht, so groß wie ein Pferd! Hab ihn nie gesehen, aber gehört.",
                  "Der Blinde sagt, der See sieht mich auch an. Gruselig."],
    },
    "walburga": {
        "name": "Kräuterweib Walburga", "title": "Tränke & Kräuter", "lvl": 14, "pos": [-38, -46], "rot": SE,
        "model": "human", "scale": 0.94,
        "look": {"skin": "#e0b494", "hair": "#d8d8d8", "hair_style": "long", "top": "#5a6a3a", "bottom": "#3a2a2a",
                 "robe": True, "hood": True, "held": "staff", "anim": "idle"},
        "greeting": "Ah, ein junges Ding mit schmutzigen Stiefeln. Brauchst du Tränke? Walburgas Tränke helfen gegen "
                    "alles. Außer gegen Dummheit. Frag den Dorftrottel.",
        "barks": ["Wiesenkraut, Wolfsmilch, Mondblatt ... alles da.",
                  "Die Wölfe werden frecher. Liegt am Mond. Oder an den Wölfen."],
        "vendor": ["heiltrank", "manatrank", "quellwasser"],
    },
    "wache_tor_w": {"name": "Burgwache", "title": "", "lvl": 25, "pos": [-5, -76], "rot": S, "model": "human",
                    "scale": 1.05, "guard": True,
                    "look": {"skin": "#d9a88a", "hair": "#3a2a1a", "top": "#8f1d2c", "bottom": "#4a4a52",
                             "armor": True, "helm": True, "held": "spear", "anim": "guard"},
                    "greeting": "Die Burg steht Euch offen, Bürger. Simon empfängt Euch im Hof."},
    "wache_tor_e": {"name": "Burgwache", "title": "", "lvl": 25, "pos": [5, -76], "rot": S, "model": "human",
                    "scale": 1.05, "guard": True,
                    "look": {"skin": "#c49070", "hair": "#1a1a1a", "top": "#8f1d2c", "bottom": "#4a4a52",
                             "armor": True, "helm": True, "held": "spear", "anim": "guard"},
                    "greeting": "Keine Waffen im Thronsaal. Ach, es gibt keinen Thronsaal. Dann eben im Hof."},
    "wache_dorf": {"name": "Wache von Eichenau", "title": "", "lvl": 20, "pos": [6, -8], "rot": N, "model": "human",
                   "scale": 1.03, "guard": True,
                   "look": {"skin": "#e0b090", "hair": "#8a5a2a", "top": "#3a5b8c", "bottom": "#4a4a52",
                            "armor": True, "helm": True, "held": "spear", "anim": "guard"},
                   "greeting": "Alles ruhig in Eichenau. Na ja, bis auf den Dorftrottel."},
    "wache_krypta": {"name": "Totenwächterin Elsbeth", "title": "Wacht der Krypta", "lvl": 20, "pos": [-118, 129],
                     "rot": E, "model": "human", "scale": 1.0, "guard": True,
                     "look": {"skin": "#e8c0a0", "hair": "#d8d8d8", "hair_style": "braid", "top": "#3a3a4a",
                              "bottom": "#2a2a3a", "armor": True, "held": "lantern", "anim": "idle"},
                     "greeting": "Hinter diesem Tor liegt die vergessene Krypta. Geht nur hinein, wenn Ihr mindestens "
                                 "Stufe 6 seid – und am besten nicht allein. Dort unten wartet Sir Morgrath.",
                     "barks": ["Hört Ihr das? Knochen. Immer diese Knochen."]},
}

for _id, _n in NPCS.items():
    _n["id"] = _id
    _n.setdefault("zone", "gruenmark")
    _n.setdefault("barks", [])
    _n.setdefault("vendor", None)
    _n.setdefault("wander", 0)
    _n.setdefault("title", "")
    _n.setdefault("guard", False)
