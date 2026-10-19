class_name HelpWin
extends Win
## Hilfe: Steuerung, Kampfsystem, Chatbefehle.

var hud


func _init(p_hud) -> void:
	super("Hilfe", "hilfe", Vector2(620, 560))
	hud = p_hud


func _ready() -> void:
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(600, 500)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(sc)
	var r := UiSkin.rich("")
	r.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(r)
	var k := func(a): return "[color=#ffd870]%s[/color]" % Settings.key_label(a)
	r.text = """[font_size=20][color=#e8c374]Steuerung[/color][/font_size]
%s %s %s %s – Bewegen (A/D drehen; mit gedrückter rechter Maustaste seitwärts)
%s / %s – Seitwärts gehen   ·   %s – Springen / Ausweichen   ·   %s – Sprinten
Rechte Maustaste halten – Kamera und Blickrichtung drehen   ·   Linke Maustaste halten – Kamera umsehen
Beide Maustasten – Vorwärts laufen   ·   Mausrad – Zoom
Linksklick – Ziel auswählen   ·   Rechtsklick – Angreifen / Sprechen / Plündern
%s – Interagieren   ·   %s – Nächster Gegner   ·   %s – Sich selbst anvisieren   ·   Esc – Ziel löschen / Menü
1–0, ß, ´ – Aktionsleiste 1   ·   Z X C V T – Aktionsleiste 2

[font_size=20][color=#e8c374]Fenster[/color][/font_size]
%s Taschen · %s Charakter · %s Zauberbuch · %s Talente · %s Questlog · %s Weltkarte · %s Gilde
%s Berufe · %s Erfolge · %s Sammlung · %s Gruppenfinder · %s Chat

[font_size=20][color=#e8c374]Kampf[/color][/font_size]
Jede Klasse nutzt eine eigene Ressource (Mana, Wut, Energie, Fokus, Entschlossenheit, Konzentration).
Fähigkeiten teilen sich eine globale Abklingzeit von 1,5 Sekunden; starke Fähigkeiten haben eigene Abklingzeiten.
Rote Bodenmarkierungen kündigen Bossangriffe an – verlasst sie rechtzeitig!
Unterbrecht Zauber mit orangefarbenem Zauberbalken. Graue Balken sind nicht unterbrechbar.
Angriffe von hinten können nicht pariert oder geblockt werden. Achtet auf Reichweite (rote Symbole = zu weit).

[font_size=20][color=#e8c374]Chatbefehle[/color][/font_size]
/s Sagen · /y Rufen · /p Gruppe · /ra Schlachtzug · /g Gilde · /1 Welt · /2 Handel · /4 Gruppensuche
/w Name Text – Flüstern · /r – Antworten · /einladen Name · /verlassen · /wer · /duell · /würfeln
/tanzen /winken /verbeugen /lachen /jubeln /weinen /sitzen /schlafen /knien /salutieren /klatschen /zeigen
/freund Name · /ignorieren Name · /ruhestein · /schlachtzug · /abmelden
""" % [k.call("vor"), k.call("links"), k.call("zurueck"), k.call("rechts"), k.call("links_seit"), k.call("rechts_seit"),
		k.call("springen"), k.call("sprinten"), k.call("interagieren"), k.call("ziel_naechstes"), k.call("ziel_selbst"),
		k.call("inventar"), k.call("charakter"), k.call("zauberbuch"), k.call("talente"), k.call("questlog"), k.call("karte"),
		k.call("gilde"), k.call("berufe"), k.call("erfolge"), k.call("sammlung"), k.call("gruppensuche"), k.call("chat")]


func _on_open() -> void:
	center()
