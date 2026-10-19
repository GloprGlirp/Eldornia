class_name GuildWin
extends Win
## Gildenfenster (GDD 10): Mitglieder & Ränge, Nachricht des Tages, Wochenziel, Gildenstufe, Protokoll,
## Gildenbank (Gegenstände + Gold). Ohne Gilde: Gründung beim Gildenmeister.

var hud
var tabs: TabContainer
var head: RichTextLabel
var members: VBoxContainer
var info: VBoxContainer
var bank_grid: GridContainer
var bank_money: RichTextLabel
var create_box: VBoxContainer
var show_offline := true

const RANKS := ["rekrut", "mitglied", "offizier", "leiter"]


func _init(p_hud) -> void:
	super("Gilde", "gilde", Vector2(640, 560))
	hud = p_hud


func _ready() -> void:
	head = UiSkin.rich("")
	body.add_child(head)
	create_box = UiSkin.vbox(8)
	body.add_child(create_box)
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(620, 440)
	body.add_child(tabs)
	var ms := ScrollContainer.new()
	ms.name = "Mitglieder"
	tabs.add_child(ms)
	members = UiSkin.vbox(2)
	members.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ms.add_child(members)
	var isc := ScrollContainer.new()
	isc.name = "Info"
	tabs.add_child(isc)
	info = UiSkin.vbox(8)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	isc.add_child(info)
	var bv := UiSkin.vbox(8)
	bv.name = "Gildenbank"
	tabs.add_child(bv)
	bv.add_child(UiSkin.label("Rechtsklick auf einen Gegenstand in Euren Taschen lagert ihn ein (am Gildenmeister oder Briefkasten).", 13, UiSkin.TEXT_DIM))
	bank_grid = GridContainer.new()
	bank_grid.columns = 12
	bank_grid.add_theme_constant_override("h_separation", 3)
	bank_grid.add_theme_constant_override("v_separation", 3)
	bv.add_child(bank_grid)
	var mh := UiSkin.hbox(8)
	bv.add_child(mh)
	bank_money = UiSkin.rich("")
	bank_money.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mh.add_child(bank_money)
	mh.add_child(UiSkin.button("Einzahlen", func():
		hud.ask_text("gdep", "Wie viel Gold einzahlen?", "1", func(t):
			if t.is_valid_float():
				Game.send({"t": "guild_money", "amount": int(float(t) * 10000)})
		)
	))
	mh.add_child(UiSkin.button("Abheben", func():
		hud.ask_text("gwd", "Wie viel Gold abheben?", "1", func(t):
			if t.is_valid_float():
				Game.send({"t": "guild_money", "amount": -int(float(t) * 10000)})
		)
	))
	Game.state_changed.connect(func(w):
		if w == "guild" and visible:
			refresh()
	)
	position = Vector2(140, 100)


func _on_open() -> void:
	Game.send({"t": "get", "w": "guild"})
	refresh()


func open_mode(_w: String, _m: Dictionary) -> void:
	refresh()


func accept_bag_item(slot: int) -> bool:
	if Game.guild is Dictionary and tabs.current_tab == 2:
		Game.send({"t": "guild_deposit", "slot": slot})
		return true
	return false


func _my_rank() -> int:
	var g = Game.guild
	return RANKS.find(str(g.get("my_rank", "rekrut"))) if g is Dictionary else 0


func refresh() -> void:
	var g = Game.guild
	for c in create_box.get_children():
		c.queue_free()
	if not (g is Dictionary):
		tabs.visible = false
		head.text = "[center][font_size=20]Ihr seid in keiner Gilde.[/font_size]\nGilden bieten Gildenchat, eine gemeinsame Bank, Wochenziele und Gildenstufen.\nEine Gilde wird bei einem Gildenmeister gegründet (Kosten: 10 Gold).[/center]"
		var name_e := LineEdit.new()
		name_e.placeholder_text = "Gildenname (3–24 Buchstaben)"
		name_e.custom_minimum_size = Vector2(320, 34)
		var tag_e := LineEdit.new()
		tag_e.placeholder_text = "Kürzel (bis 5)"
		tag_e.max_length = 5
		tag_e.custom_minimum_size = Vector2(120, 34)
		var h := UiSkin.hbox(8)
		h.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_child(name_e)
		h.add_child(tag_e)
		create_box.add_child(h)
		var b := UiSkin.button("Gilde gründen", func(): Game.send({"t": "guild_create", "name": name_e.text, "tag": tag_e.text}))
		b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		create_box.add_child(b)
		return
	tabs.visible = true
	head.text = "[center][font_size=24][color=#ffd870]<%s>[/color][/font_size]  [color=#aaa][%s][/color]\nGildenstufe %d  ·  %d Mitglieder  ·  %d online[/center]" % [
		g.get("name", ""), g.get("tag", ""), int(g.get("level", 1)), g.get("members", []).size(),
		g.get("members", []).filter(func(x): return x.get("online", false)).size()]
	_members(g)
	_info(g)
	_bank(g)


func _members(g: Dictionary) -> void:
	for c in members.get_children():
		c.queue_free()
	var top := UiSkin.hbox(8)
	members.add_child(top)
	var inv := LineEdit.new()
	inv.placeholder_text = "Spielername"
	inv.custom_minimum_size = Vector2(200, 32)
	top.add_child(inv)
	var ib := UiSkin.button("Einladen", func():
		Game.send({"t": "guild_invite", "name": inv.text})
		inv.text = ""
	)
	ib.disabled = _my_rank() < 2
	top.add_child(ib)
	var off := CheckBox.new()
	off.text = "Offline zeigen"
	off.button_pressed = show_offline
	off.toggled.connect(func(v):
		show_offline = v
		_members(g)
	)
	top.add_child(off)
	top.add_child(UiSkin.spacer())
	top.add_child(UiSkin.button("Verlassen", func():
		hud.confirm("gleave", "Die Gilde wirklich verlassen?", func(): Game.send({"t": "guild_leave"}))
	))
	var my := _my_rank()
	for m in g.get("members", []):
		if not m.get("online", false) and not show_offline:
			continue
		var h := UiSkin.hbox(8)
		var on: bool = m.get("online", false)
		var nl := UiSkin.label(str(m.get("name", "")), 15, Content.class_color(str(m.get("cls", ""))) if on else Color(0.55, 0.55, 0.55), UiSkin.font_bold)
		nl.custom_minimum_size.x = 140
		h.add_child(nl)
		var ll := UiSkin.label(str(m.get("lvl", "")), 15, UiSkin.TEXT if on else Color(0.55, 0.55, 0.55))
		ll.custom_minimum_size.x = 30
		h.add_child(ll)
		var rl := UiSkin.label(str(m.get("rank_name", "")), 15, UiSkin.GOLD if on else Color(0.55, 0.5, 0.4))
		rl.custom_minimum_size.x = 120
		h.add_child(rl)
		var zl := UiSkin.label(str(m.get("zone", "")) if on else "Offline", 14, UiSkin.TEXT_DIM)
		zl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(zl)
		var r := RANKS.find(str(m.get("rank", "rekrut")))
		var cid = m.get("id")
		if str(m.get("name", "")) != Game.me_name and my >= 2 and r < my:
			var up := UiSkin.button("▲", func(): Game.send({"t": "guild_rank", "id": cid, "up": true}))
			up.tooltip_text = "Befördern"
			h.add_child(up)
			var dn := UiSkin.button("▼", func(): Game.send({"t": "guild_rank", "id": cid, "up": false}))
			dn.tooltip_text = "Degradieren"
			h.add_child(dn)
			var nm := str(m.get("name", ""))
			var k := UiSkin.button("✕", func(): hud.confirm("gkick", "%s aus der Gilde entfernen?" % nm, func(): Game.send({"t": "guild_kick", "id": cid})))
			k.tooltip_text = "Entfernen"
			h.add_child(k)
		members.add_child(h)


func _info(g: Dictionary) -> void:
	for c in info.get_children():
		c.queue_free()
	info.add_child(UiSkin.title_label("Nachricht des Tages", 18))
	var motd := TextEdit.new()
	motd.text = str(g.get("motd", ""))
	motd.custom_minimum_size = Vector2(580, 70)
	motd.editable = _my_rank() >= 2
	motd.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	info.add_child(motd)
	if _my_rank() >= 2:
		var sb := UiSkin.button("Speichern", func(): Game.send({"t": "guild_motd", "text": motd.text}))
		sb.size_flags_horizontal = Control.SIZE_SHRINK_END
		info.add_child(sb)
	info.add_child(UiSkin.title_label("Gildenstufe %d" % int(g.get("level", 1)), 18))
	var xb := StatBar.new(Color("#c08a2a"), 16)
	xb.custom_minimum_size = Vector2(580, 16)
	xb.set_values(int(g.get("xp", 0)), 5000, "%d / 5000 Gilden-EP" % int(g.get("xp", 0)))
	info.add_child(xb)
	var goal: Dictionary = g.get("goal", {})
	if not goal.is_empty():
		info.add_child(UiSkin.title_label("Wochenziel: %s" % goal.get("name", ""), 18))
		info.add_child(UiSkin.label(str(goal.get("desc", "")), 15))
		var gb := StatBar.new(Color("#3aa83a") if not goal.get("done", false) else Color("#e8c374"), 16)
		gb.custom_minimum_size = Vector2(580, 16)
		gb.set_values(int(goal.get("progress", 0)), maxf(1, int(goal.get("n", 1))), "%d / %d%s" % [int(goal.get("progress", 0)), int(goal.get("n", 1)), "  ✔ Erreicht" if goal.get("done", false) else ""])
		info.add_child(gb)
	info.add_child(UiSkin.title_label("Protokoll", 18))
	for e in g.get("log", []):
		var l := UiSkin.label("• " + str(e if not (e is Dictionary) else e.get("text", "")), 14, UiSkin.TEXT_DIM)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		info.add_child(l)


func _bank(g: Dictionary) -> void:
	for c in bank_grid.get_children():
		c.queue_free()
	var bank: Array = g.get("bank", [])
	for i in bank.size():
		var s := IconSlot.new(44)
		s.kind = "gbank"
		s.index = i
		var inst = bank[i]
		if inst is Dictionary:
			s.set_item(str(inst["i"]), int(inst.get("n", 1)), inst)
		var idx := i
		s.clicked.connect(func(_s, b):
			if b == MOUSE_BUTTON_RIGHT and bank[idx] is Dictionary:
				Game.send({"t": "guild_withdraw", "slot": idx})
		)
		s.accepts_drop = true
		s.dropped.connect(func(_s, d):
			if str(d.get("from", "")) == "bag":
				Game.send({"t": "guild_deposit", "slot": int(d.get("index", -1))})
		)
		bank_grid.add_child(s)
	bank_money.text = "Gildenkasse: " + Content.money_bb(int(g.get("copper", 0)))
