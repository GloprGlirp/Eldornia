class_name VendorWin
extends Win
## Händlerfenster: Kaufen (auch gegen Marken/Ruf), Rückkauf, Reparieren. Gegenstände aus den Taschen
## per Rechtsklick oder Ziehen verkaufen.

var hud
var npc_id := 0
var data: Dictionary = {}
var tabs: TabContainer
var grid: GridContainer
var bb_grid: GridContainer
var repair_btn: Button
var money: RichTextLabel


func _init(p_hud) -> void:
	super("Händler", "haendler", Vector2(560, 520))
	hud = p_hud


func _ready() -> void:
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(540, 420)
	body.add_child(tabs)
	var sc := ScrollContainer.new()
	sc.name = "Waren"
	tabs.add_child(sc)
	grid = GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 6)
	sc.add_child(grid)
	var sc2 := ScrollContainer.new()
	sc2.name = "Rückkauf"
	tabs.add_child(sc2)
	bb_grid = GridContainer.new()
	bb_grid.columns = 2
	bb_grid.add_theme_constant_override("h_separation", 8)
	bb_grid.add_theme_constant_override("v_separation", 6)
	sc2.add_child(bb_grid)
	var h := UiSkin.hbox(8)
	body.add_child(h)
	money = UiSkin.rich("")
	money.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(money)
	repair_btn = UiSkin.button("Alles reparieren", func(): Game.send({"t": "repair", "npc": npc_id}))
	h.add_child(repair_btn)
	Game.state_changed.connect(func(w):
		if w == "inventory" and visible:
			_footer()
	)
	position = Vector2(60, 120)


func _on_close() -> void:
	npc_id = 0
	if hud.windows.has("inventar"):
		hud.windows["inventar"].refresh()


func show_vendor(m: Dictionary) -> void:
	data = m
	npc_id = int(m.get("npc", 0))
	title = str(m.get("name", "Händler"))
	title_label.text = title
	for c in grid.get_children():
		c.queue_free()
	for c in bb_grid.get_children():
		c.queue_free()
	for e in m.get("stock", []):
		grid.add_child(_entry(e, false, -1))
	var bb: Array = m.get("buyback", [])
	for i in bb.size():
		bb_grid.add_child(_entry(bb[i], true, i))
	if bb.is_empty():
		bb_grid.add_child(UiSkin.label("Hier erscheinen verkaufte Gegenstände.", 15, UiSkin.TEXT_DIM))
	_footer()


func _footer() -> void:
	repair_btn.visible = data.get("repair", false)
	repair_btn.disabled = Game.repair_cost <= 0
	repair_btn.tooltip_text = "Kosten: %s" % Content.money(Game.repair_cost)
	money.text = Content.money_bb(Game.copper) + ("    Reparatur: %s" % Content.money_bb(Game.repair_cost) if data.get("repair", false) and Game.repair_cost > 0 else "")
	if hud.windows.has("inventar"):
		hud.windows["inventar"].refresh()


func _entry(e: Dictionary, buyback: bool, idx: int) -> Control:
	var iid := str(e.get("i", ""))
	var it := Content.item(iid)
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UiSkin.inner_box())
	p.custom_minimum_size = Vector2(262, 56)
	var h := UiSkin.hbox(8)
	p.add_child(h)
	var s := IconSlot.new(44)
	s.kind = "vendor"
	s.set_item(iid, int(e.get("n", it.get("vendor_n", 1))))
	h.add_child(s)
	var v := UiSkin.vbox(0)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var nl := UiSkin.label(str(it.get("name", iid)), 15, Content.rarity_color(int(it.get("q", 1))), UiSkin.font_bold)
	nl.clip_text = true
	nl.custom_minimum_size.x = 190
	v.add_child(nl)
	var price := int(e.get("price", 0))
	var ptxt := Content.money_bb(price) if price > 0 else ""
	if e.get("cur") is Dictionary:
		var curdefs: Dictionary = Content.defs.get("currencies", {})
		for c in e["cur"]:
			ptxt += "  [color=#c0e0ff]%d %s[/color]" % [int(e["cur"][c]), curdefs.get(c, {}).get("name", c)]
	var pr := UiSkin.rich(ptxt)
	pr.add_theme_font_size_override("normal_font_size", 14)
	v.add_child(pr)
	var locked := false
	if e.get("rep") is Array:
		var rr: Array = e["rep"]
		var fac: Dictionary = Content.defs.get("factions", {})
		var rl := UiSkin.label("Benötigt %s: %s" % [fac.get(rr[0], {}).get("name", rr[0]), rr[1]], 12, Color(1, 0.55, 0.3))
		v.add_child(rl)
	if int(it.get("lvl", 1)) > Game.level or (it.get("cls") is Array and not Game.me_cls in it["cls"]):
		locked = true
	if price > Game.copper:
		locked = true
	s.red = locked
	var buy := func():
		if buyback:
			Game.send({"t": "buyback", "npc": npc_id, "i": idx})
			return
		if Input.is_key_pressed(KEY_SHIFT) and int(it.get("stack", 1)) > 1:
			hud.ask_text("buy_n", "Wie viele kaufen?", str(int(it.get("stack", 1))), func(t):
				if t.is_valid_int():
					Game.send({"t": "buy", "npc": npc_id, "i": iid, "n": int(t)})
			)
		else:
			Game.send({"t": "buy", "npc": npc_id, "i": iid, "n": 1})
		Sfx.play("coin", -8.0)
	s.clicked.connect(func(_s, b):
		if b == MOUSE_BUTTON_RIGHT or Input.is_key_pressed(KEY_SHIFT):
			buy.call()
	)
	p.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_RIGHT:
			buy.call()
	)
	p.tooltip_text = ""
	return p


func _can_drop_data(_at: Vector2, d: Variant) -> bool:
	return d is Dictionary and str(d.get("from", "")) == "bag"


func _drop_data(_at: Vector2, d: Variant) -> void:
	Game.send({"t": "sell", "npc": npc_id, "slot": int(d.get("index", -1))})
	Sfx.play("sell", -8.0)
