class_name GameMenuWin
extends Win
## Spielmenü (Esc): Einstellungen, Hilfe, Instanz verlassen, Charakterwahl, Beenden.

var hud
var leave_btn: Button


func _init(p_hud) -> void:
	super("Spielmenü", "menue", Vector2(300, 380))
	hud = p_hud


func _ready() -> void:
	for e in [["Einstellungen", func(): _go("einstellungen")], ["Hilfe & Steuerung", func(): _go("hilfe")],
			["Sammlung", func(): _go("sammlung")], ["Erfolge", func(): _go("erfolge")]]:
		var b := UiSkin.button(e[0], e[1])
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		body.add_child(b)
	leave_btn = UiSkin.button("Instanz verlassen", func():
		Game.send({"t": "leave_instance"})
		close_win()
	)
	leave_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(leave_btn)
	var hs := UiSkin.button("Ruhestein benutzen", func():
		Game.send({"t": "hearth"})
		close_win()
	)
	hs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(hs)
	body.add_child(UiSkin.spacer(0, 8))
	var cs := UiSkin.button("Zur Charakterauswahl", func():
		close_win()
		hud.world.leave_requested.emit()
	)
	cs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(cs)
	if not OS.has_feature("web"):
		var q := UiSkin.button("Spiel beenden", func():
			Settings.save_settings()
			Net.close_world("Spiel beendet.")
			get_tree().quit()
		)
		q.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		body.add_child(q)
	var back := UiSkin.button("Zurück zum Spiel", close_win)
	back.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(back)


func _go(w: String) -> void:
	close_win()
	hud.open_window(w)


func _on_open() -> void:
	center()
	leave_btn.visible = Game.zone_inst
