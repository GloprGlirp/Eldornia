class_name ProfTrainerWin
extends Win
## Berufslehrer (GDD 9): Beruf erlernen, nächsten Rang kaufen, Rezepte lernen.

var hud
var npc_id := 0
var list: VBoxContainer


func _init(p_hud) -> void:
	super("Berufslehrer", "berufslehrer", Vector2(560, 520))
	hud = p_hud


func _ready() -> void:
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(540, 470)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(sc)
	list = UiSkin.vbox(10)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(list)
	position = Vector2(70, 110)


func show_trainer(m: Dictionary) -> void:
	npc_id = int(m.get("npc", 0))
	title_label.text = str(m.get("name", "Berufslehrer"))
	for c in list.get_children():
		c.queue_free()
	for e in m.get("list", []):
		var pid := str(e.get("id", ""))
		var box := PanelContainer.new()
		box.add_theme_stylebox_override("panel", UiSkin.inner_box())
		list.add_child(box)
		var v := UiSkin.vbox(6)
		box.add_child(v)
		var h := UiSkin.hbox(8)
		v.add_child(h)
		var pd: Dictionary = Content.defs.get("professions", {}).get(pid, {})
		var ic := TextureRect.new()
		ic.texture = Content.icon(str(pd.get("icon", "anvil")), Color(0.4, 0.3, 0.15), 48)
		ic.custom_minimum_size = Vector2(40, 40)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		h.add_child(ic)
		var tv := UiSkin.vbox(0)
		tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(tv)
		tv.add_child(UiSkin.label(str(e.get("name", pid)), 19, UiSkin.GOLD, UiSkin.font_title))
		var dl := UiSkin.label(str(e.get("desc", "")), 14, UiSkin.TEXT_DIM)
		dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		dl.custom_minimum_size.x = 380
		tv.add_child(dl)
		if not e.get("known", false):
			h.add_child(UiSkin.button("Erlernen (%s)" % Content.money(int(e.get("cost", 0)), true), func():
				Game.send({"t": "prof_learn", "npc": npc_id, "prof": pid})
			))
			continue
		var sk := UiSkin.label("Fertigkeit: %d / %d" % [int(e.get("skill", 1)), int(e.get("max", 75))], 15)
		v.add_child(sk)
		var nr = e.get("next_rank")
		if nr is Dictionary:
			var ok := int(e.get("skill", 0)) >= int(nr.get("need", 0)) and Game.level >= int(nr.get("level", 1))
			var b := UiSkin.button("Rang „%s“ lernen (bis %d) – %s" % [nr.get("name", ""), int(nr.get("max", 0)), Content.money(int(nr.get("cost", 0)), true)], func():
				Game.send({"t": "prof_rank", "npc": npc_id, "prof": pid})
			)
			b.disabled = not ok
			b.tooltip_text = "Benötigt Fertigkeit %d und Stufe %d." % [int(nr.get("need", 0)), int(nr.get("level", 1))]
			v.add_child(b)
		var recs: Array = e.get("recipes", []) + e.get("faction_recipes", [])
		if not recs.is_empty():
			v.add_child(UiSkin.label("Rezepte", 16, UiSkin.GOLD, UiSkin.font_bold))
		for r in recs:
			var rh := UiSkin.hbox(6)
			var s := IconSlot.new(34)
			s.set_item(str(r.get("result", "")), 1)
			rh.add_child(s)
			var can := int(e.get("skill", 0)) >= int(r.get("skill", 0))
			var nm := UiSkin.label("%s  (%d)" % [str(r.get("name", "")), int(r.get("skill", 0))], 15, UiSkin.TEXT if can else Color(0.9, 0.3, 0.3))
			nm.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			var mats := []
			for mm in r.get("mats", []):
				mats.append("%d× %s" % [int(mm[1]), Content.item(str(mm[0])).get("name", mm[0])])
			nm.tooltip_text = "Materialien: " + ", ".join(mats)
			nm.mouse_filter = Control.MOUSE_FILTER_PASS
			rh.add_child(nm)
			var rid := str(r.get("id", ""))
			var cost_txt := Content.money(int(r.get("cost", 0)), true)
			if r.get("rep") is Array:
				cost_txt += " · Ruf: %s" % str(r["rep"][1])
			var lb := UiSkin.button("Lernen (%s)" % cost_txt, func(): Game.send({"t": "prof_recipe", "npc": npc_id, "r": rid}))
			lb.disabled = not can or (r.has("ok") and not r["ok"])
			rh.add_child(lb)
			v.add_child(rh)
