class_name InventoryWin
extends Win
## Taschen (GDD 6): Rucksack + Zusatztaschen, Geld, Währungen. Rechtsklick benutzt/legt an/verkauft,
## Ziehen & Ablegen verschiebt, Umschalt+Rechtsklick teilt Stapel, Umschalt+Linksklick verlinkt im Chat.

var hud
var grid: GridContainer
var slots: Array = []
var money: RichTextLabel
var cur_box: HFlowContainer
var bag_row: HBoxContainer
var cap_label: Label
var junk_btn: Button


func _init(p_hud) -> void:
	super("Taschen", "inventar", Vector2(420, 360))
	hud = p_hud


func _ready() -> void:
	bag_row = UiSkin.hbox(4)
	body.add_child(bag_row)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(396, 300)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(scroll)
	grid = GridContainer.new()
	grid.columns = 8
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	scroll.add_child(grid)
	cap_label = UiSkin.label("", 14, UiSkin.TEXT_DIM)
	body.add_child(cap_label)
	cur_box = HFlowContainer.new()
	cur_box.add_theme_constant_override("h_separation", 12)
	body.add_child(cur_box)
	var h := UiSkin.hbox(6)
	body.add_child(h)
	money = UiSkin.rich("")
	money.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(money)
	junk_btn = UiSkin.button("Schrott verkaufen", func():
		var v = hud.windows.get("haendler")
		if v and v.visible:
			Game.send({"t": "sell_junk", "npc": v.npc_id})
	)
	h.add_child(junk_btn)
	h.add_child(UiSkin.button("Sortieren", func(): Game.send({"t": "sort"})))
	Game.state_changed.connect(func(w):
		if w == "inventory" and visible:
			refresh()
	)
	position = get_viewport_rect().size - Vector2(460, 560)
	refresh()


func _on_open() -> void:
	refresh()


func refresh() -> void:
	var cap := maxi(Game.capacity, Game.bags.size())
	while slots.size() < cap:
		var s := IconSlot.new(44)
		s.kind = "bag"
		s.index = slots.size()
		s.accepts_drop = true
		s.clicked.connect(_on_click)
		s.dropped.connect(_on_drop)
		grid.add_child(s)
		slots.append(s)
	while slots.size() > cap:
		var s2: IconSlot = slots.pop_back()
		s2.queue_free()
	var used := 0
	for i in slots.size():
		var s: IconSlot = slots[i]
		var inst = Game.bags[i] if i < Game.bags.size() else null
		if inst is Dictionary:
			s.set_item(str(inst["i"]), int(inst.get("n", 1)), inst)
			s.dim = false
			used += 1
			var d := int(inst.get("d", 100))
			s.red = inst.has("d") and d <= 0
		else:
			s.clear()
			s.payload = {}
	cap_label.text = "%d / %d Plätze belegt" % [used, cap]
	money.text = Content.money_bb(Game.copper)
	for c in cur_box.get_children():
		c.queue_free()
	var curdefs: Dictionary = Content.defs.get("currencies", {})
	for k in Game.currencies:
		var n := int(Game.currencies[k])
		if n <= 0:
			continue
		var cd: Dictionary = curdefs.get(k, {})
		var hb := UiSkin.hbox(3)
		var t := TextureRect.new()
		t.texture = Content.icon(str(cd.get("icon", "two-coins")), Color(0.35, 0.3, 0.15), 32)
		t.custom_minimum_size = Vector2(18, 18)
		t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		hb.add_child(t)
		var l := UiSkin.label(str(n), 14)
		hb.add_child(l)
		hb.tooltip_text = "%s\n%s" % [cd.get("name", k), cd.get("desc", "")]
		cur_box.add_child(hb)
	for c in bag_row.get_children():
		c.queue_free()
	var back := IconSlot.new(34)
	back.drag_enabled = false
	back.set_icon(Content.icon("knapsack", Color(0.4, 0.28, 0.16), 48), "[b]Rucksack[/b]\n24 Plätze")
	bag_row.add_child(back)
	for b in Game.bagslots:
		var bs := IconSlot.new(34)
		bs.drag_enabled = false
		if b:
			bs.set_item(str(b), 1)
		bag_row.add_child(bs)
	for i in range(Game.bagslots.size(), 4):
		var es := IconSlot.new(34)
		es.drag_enabled = false
		es.set_icon(null, "Leerer Taschenplatz – benutzt eine Tasche, um sie anzulegen.")
		bag_row.add_child(es)
	var v = hud.windows.get("haendler")
	junk_btn.visible = v != null and v.visible


func _vendor():
	var v = hud.windows.get("haendler")
	return v if v and v.visible else null


func _on_click(s: IconSlot, button: int) -> void:
	var inst = Game.bags[s.index] if s.index < Game.bags.size() else null
	if not (inst is Dictionary):
		return
	var iid := str(inst["i"])
	var it := Content.item(iid)
	if button == MOUSE_BUTTON_LEFT:
		if Input.is_key_pressed(KEY_SHIFT):
			hud.chat.focus_input(hud.chat.input.text + "[%s] " % it.get("name", iid))
		return
	# Rechtsklick
	if Input.is_key_pressed(KEY_SHIFT) and int(inst.get("n", 1)) > 1:
		var slot := s.index
		hud.ask_text("split", "Wie viele abteilen?", str(int(inst["n"]) / 2), func(t):
			if t.is_valid_int() and int(t) > 0:
				Game.send({"t": "split", "slot": slot, "n": int(t)})
		)
		return
	var v = _vendor()
	if v:
		Game.send({"t": "sell", "npc": v.npc_id, "slot": s.index})
		Sfx.play("sell", -8.0)
		return
	for wid in ["handel", "post", "markt", "gilde", "berufe"]:
		var w = hud.windows.get(wid)
		if w and w.visible and w.has_method("accept_bag_item") and w.accept_bag_item(s.index):
			return
	var t := str(it.get("type", ""))
	if t in ["weapon", "armor", "jewelry"]:
		Game.send({"t": "equip", "slot": s.index})
		Sfx.play("loot", -10.0)
	else:
		Game.send({"t": "use", "slot": s.index, "tid": hud.world.target if hud.world.target != 0 else null})


func _on_drop(s: IconSlot, data: Dictionary) -> void:
	var from := str(data.get("from", ""))
	if from == "bag":
		var a := int(data.get("index", -1))
		if a >= 0 and a != s.index:
			if Input.is_key_pressed(KEY_SHIFT):
				Game.send({"t": "split", "slot": a, "n": 1})
			else:
				Game.send({"t": "swap", "a": a, "b": s.index})
	elif from == "equip":
		Game.send({"t": "unequip", "s": str(data.get("key", "")), "to": s.index})
	elif from == "gbank":
		Game.send({"t": "guild_withdraw", "slot": int(data.get("index", -1))})
	elif from == "vendor":
		var v = _vendor()
		if v:
			Game.send({"t": "buy", "npc": v.npc_id, "i": data.get("item"), "n": 1})
