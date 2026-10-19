class_name LootWin
extends Win
## Beutefenster (persönliche Beute, GDD 6). Klick nimmt einen Gegenstand, „Alles nehmen“ nimmt alles.

var hud
var src_id := 0
var list: VBoxContainer


func _init(p_hud) -> void:
	super("Beute", "beute", Vector2(280, 120))
	hud = p_hud


func _ready() -> void:
	list = UiSkin.vbox(4)
	body.add_child(list)
	body.add_child(UiSkin.button("Alles nehmen", func(): Game.send({"t": "loot_all", "id": src_id})))


func _on_close() -> void:
	Game.send({"t": "loot_close"})
	src_id = 0


func show_loot(m: Dictionary) -> void:
	src_id = int(m.get("id", 0))
	title_label.text = str(m.get("name", "Beute"))
	for c in list.get_children():
		c.queue_free()
	var copper := int(m.get("copper", 0))
	if copper > 0:
		list.add_child(_row(Content.icon("two-coins", Color(0.55, 0.45, 0.1), 48), Content.money_bb(copper), func():
			Game.send({"t": "loot_take", "id": src_id, "i": "c"})
			Sfx.play("coin", -6.0)
		))
	var items: Array = m.get("items", [])
	for i in items.size():
		var e: Array = items[i]
		var iid := str(e[0])
		var n := int(e[1]) if e.size() > 1 else 1
		var it := Content.item(iid)
		var idx := i
		var col: String = Content.RARITY_COLORS[clampi(int(it.get("q", 1)), 0, 6)]
		var r := _row(Content.item_icon(it), "[color=%s]%s[/color]%s" % [col, it.get("name", iid), (" ×%d" % n) if n > 1 else ""], func():
			Game.send({"t": "loot_take", "id": src_id, "i": idx})
			Sfx.play("loot", -8.0)
		, iid)
		list.add_child(r)
	if copper == 0 and items.is_empty():
		close_win()
	reset_size()


func _row(tex: Texture2D, bb: String, cb: Callable, iid := "") -> Control:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UiSkin.inner_box())
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	p.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var h := UiSkin.hbox(8)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(h)
	var s := IconSlot.new(40)
	s.drag_enabled = false
	if iid != "":
		s.set_item(iid, 1)
	else:
		s.set_icon(tex, "")
	s.clicked.connect(func(_s, _b): cb.call())
	h.add_child(s)
	var l := UiSkin.rich(bb)
	l.custom_minimum_size.x = 190
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(l)
	p.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed:
			cb.call()
	)
	return p
