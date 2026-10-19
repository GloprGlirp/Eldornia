class_name StonesWin
extends Win
## Teleportationssteine (Schnellreise zwischen aktivierten Steinen gegen Gebühr).

var hud
var list: VBoxContainer


func _init(p_hud) -> void:
	super("Teleportationsstein", "steine", Vector2(420, 300))
	hud = p_hud


func _ready() -> void:
	body.add_child(UiSkin.label("Wohin soll Euch der Stein tragen?", 16, UiSkin.TEXT))
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(400, 260)
	body.add_child(sc)
	list = UiSkin.vbox(4)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(list)


func show_stones(m: Dictionary) -> void:
	center()
	for c in list.get_children():
		c.queue_free()
	var lst: Array = m.get("list", [])
	if lst.is_empty():
		list.add_child(UiSkin.label("Ihr habt noch keine anderen Steine aktiviert. Berührt Teleportationssteine in der Welt, um sie freizuschalten.", 14, UiSkin.TEXT_DIM))
	for s in lst:
		var h := UiSkin.hbox(8)
		var v := UiSkin.vbox(0)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		v.add_child(UiSkin.label(str(s.get("name", "")), 16, UiSkin.GOLD, UiSkin.font_bold))
		v.add_child(UiSkin.label("%s (ab Stufe %d)" % [s.get("zone", ""), int(s.get("lvl", 1))], 13, UiSkin.TEXT_DIM))
		h.add_child(v)
		h.add_child(UiSkin.rich(Content.money_bb(int(s.get("cost", 0)))))
		var sid := str(s.get("id", ""))
		var b := UiSkin.button("Reisen", func():
			Game.send({"t": "travel", "stone": sid})
			close_win()
		)
		b.disabled = Game.copper < int(s.get("cost", 0))
		h.add_child(b)
		list.add_child(h)
