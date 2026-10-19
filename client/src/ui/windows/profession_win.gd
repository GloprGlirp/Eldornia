class_name ProfessionWin
extends Win
## Berufe (GDD 9): Schmiedekunst, Alchemie, Kräuterkunde, Bergbau, Lederverarbeitung, Verzauberung.
## Rezeptliste mit Farbstufen, Materialanzeige, Herstellen (einzeln/mehrfach), Entzaubern.

var hud
var tabs: TabBar
var list: VBoxContainer
var detail: VBoxContainer
var skill_bar: StatBar
var rank_l: Label
var cur := ""
var sel := ""
var count_spin: SpinBox
var disenchant_mode := false
var de_btn: Button
var empty_l: RichTextLabel

const COLORS := {"red": "#ff3030", "orange": "#ff8040", "yellow": "#ffff00", "green": "#40c040", "grey": "#808080"}


func _init(p_hud) -> void:
	super("Berufe", "berufe", Vector2(760, 540))
	hud = p_hud


func _ready() -> void:
	tabs = TabBar.new()
	tabs.tab_changed.connect(func(i):
		var keys := Game.professions.keys()
		if i < keys.size():
			cur = str(keys[i])
			sel = ""
			_render()
	)
	body.add_child(tabs)
	var top := UiSkin.hbox(10)
	body.add_child(top)
	rank_l = UiSkin.label("", 16, UiSkin.GOLD, UiSkin.font_bold)
	top.add_child(rank_l)
	skill_bar = StatBar.new(Color("#3a7ad8"), 16)
	skill_bar.custom_minimum_size = Vector2(300, 16)
	skill_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	top.add_child(skill_bar)
	top.add_child(UiSkin.spacer())
	de_btn = UiSkin.button("Entzaubern", func():
		disenchant_mode = not disenchant_mode
		de_btn.text = "Entzaubern: Gegenstand rechtsklicken …" if disenchant_mode else "Entzaubern"
		if disenchant_mode:
			hud.open_window("inventar")
	)
	top.add_child(de_btn)
	var unl := UiSkin.button("Verlernen", func():
		if cur == "":
			return
		var pid := cur
		hud.confirm("unlearn", "Wollt Ihr %s wirklich verlernen? Fertigkeit und Rezepte gehen verloren." % Game.professions[pid].get("name", pid),
			func(): Game.send({"t": "prof_unlearn", "prof": pid}))
	)
	top.add_child(unl)
	empty_l = UiSkin.rich("")
	body.add_child(empty_l)
	var h := UiSkin.hbox(10)
	h.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(h)
	var ls := ScrollContainer.new()
	ls.custom_minimum_size = Vector2(320, 400)
	h.add_child(ls)
	list = UiSkin.vbox(1)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ls.add_child(list)
	var dp := PanelContainer.new()
	dp.add_theme_stylebox_override("panel", UiSkin.inner_box())
	dp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(dp)
	detail = UiSkin.vbox(8)
	dp.add_child(detail)
	Game.state_changed.connect(func(w):
		if visible and w in ["professions", "inventory"]:
			refresh()
	)
	position = Vector2(100, 100)


func _on_open() -> void:
	Game.send({"t": "get", "w": "professions"})
	refresh()


func _on_close() -> void:
	disenchant_mode = false
	de_btn.text = "Entzaubern"


func accept_bag_item(slot: int) -> bool:
	if disenchant_mode:
		Game.send({"t": "disenchant", "slot": slot})
		return true
	return false


func refresh() -> void:
	var keys := Game.professions.keys()
	while tabs.tab_count > 0:
		tabs.remove_tab(0)
	for k in keys:
		tabs.add_tab(str(Game.professions[k].get("name", k)))
	if keys.is_empty():
		cur = ""
		empty_l.text = "[center]Ihr habt noch keinen Beruf erlernt. Berufslehrer findet Ihr in Eichenau (Schmied, Alchemist, Gerber, Kräuterkundige, Bergmann, Verzauberer).[/center]"
	else:
		empty_l.text = ""
		if not cur in keys:
			cur = str(keys[0])
		tabs.set_block_signals(true)
		tabs.current_tab = keys.find(cur)
		tabs.set_block_signals(false)
	de_btn.visible = Game.professions.has("verzauberung")
	_render()


func _render() -> void:
	for c in list.get_children():
		c.queue_free()
	for c in detail.get_children():
		c.queue_free()
	var pr: Dictionary = Game.professions.get(cur, {})
	if pr.is_empty():
		rank_l.text = ""
		skill_bar.visible = false
		return
	skill_bar.visible = true
	rank_l.text = "%s (%s)" % [pr.get("name", cur), pr.get("rank", "")]
	skill_bar.set_values(int(pr.get("skill", 1)), int(pr.get("max", 75)), "%d / %d" % [int(pr.get("skill", 1)), int(pr.get("max", 75))])
	if str(pr.get("kind", "")) != "craft":
		var l := UiSkin.rich("[b]Sammelberuf[/b]\n\nSammelt Vorkommen in der Welt (auf der Minikarte markiert). Jedes Sammeln kann Eure Fertigkeit erhöhen. Höherwertige Vorkommen erfordern mehr Fertigkeit.")
		l.custom_minimum_size.x = 380
		detail.add_child(l)
		return
	var recs: Array = pr.get("recipes", [])
	if sel == "" and not recs.is_empty():
		sel = str(recs[0]["id"])
	for r in recs:
		var b := Button.new()
		b.flat = str(r["id"]) != sel
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.add_theme_font_size_override("font_size", 15)
		b.add_theme_font_override("font", UiSkin.font_body)
		var col := Color.html(COLORS.get(str(r.get("color", "grey")), "#808080"))
		b.add_theme_color_override("font_color", col)
		b.add_theme_color_override("font_hover_color", col.lightened(0.3))
		var can := int(r.get("can", 0))
		b.text = "%s%s" % [r.get("name", ""), (" [%d]" % can) if can > 0 else ""]
		var rid := str(r["id"])
		b.pressed.connect(func():
			sel = rid
			_render()
		)
		list.add_child(b)
		if rid == sel:
			_detail(r)


func _detail(r: Dictionary) -> void:
	var h := UiSkin.hbox(8)
	detail.add_child(h)
	var s := IconSlot.new(52)
	s.set_item(str(r.get("result", "")), int(r.get("n", 1)))
	h.add_child(s)
	var v := UiSkin.vbox(0)
	h.add_child(v)
	var it := Content.item(str(r.get("result", "")))
	v.add_child(UiSkin.label(str(r.get("name", "")), 19, Content.rarity_color(int(it.get("q", 1))), UiSkin.font_bold))
	var st = {"forge": "Benötigt: Schmiede", "anvil": "Benötigt: Amboss", "alchemy": "Benötigt: Alchemietisch"}.get(str(r.get("station", "")), "")
	if st != "":
		v.add_child(UiSkin.label(st, 14, UiSkin.TEXT_DIM))
	v.add_child(UiSkin.label("Fertigkeit %d · %.1f Sek." % [int(r.get("skill", 0)), float(r.get("cast", 2.0))], 14, UiSkin.TEXT_DIM))
	detail.add_child(UiSkin.label("Materialien", 16, UiSkin.GOLD, UiSkin.font_title))
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 10)
	detail.add_child(g)
	for m in r.get("mats", []):
		var mh := UiSkin.hbox(6)
		var ms := IconSlot.new(38)
		ms.set_item(str(m[0]), 1)
		mh.add_child(ms)
		var have := Game.count_item(str(m[0]))
		var need := int(m[1])
		var ml := UiSkin.label("%s\n%d / %d" % [Content.item(str(m[0])).get("name", m[0]), have, need], 14, UiSkin.TEXT if have >= need else Color(1, 0.35, 0.3))
		ml.custom_minimum_size.x = 120
		mh.add_child(ml)
		g.add_child(mh)
	var bh := UiSkin.hbox(8)
	detail.add_child(UiSkin.spacer(0, 10))
	detail.add_child(bh)
	count_spin = SpinBox.new()
	count_spin.min_value = 1
	count_spin.max_value = maxi(1, int(r.get("can", 1)))
	count_spin.value = 1
	bh.add_child(count_spin)
	var rid := str(r["id"])
	var mk := UiSkin.button("Herstellen", func(): Game.send({"t": "craft", "r": rid, "n": int(count_spin.value)}))
	mk.disabled = int(r.get("can", 0)) <= 0
	bh.add_child(mk)
	var all := UiSkin.button("Alle", func(): Game.send({"t": "craft", "r": rid, "n": int(r.get("can", 1))}))
	all.disabled = int(r.get("can", 0)) <= 0
	bh.add_child(all)
	if r.get("enchant"):
		detail.add_child(UiSkin.label("Erzeugt eine Verzauberungsrolle. Benutzt sie, um passende Ausrüstung zu verzaubern.", 13, UiSkin.TEXT_DIM))
