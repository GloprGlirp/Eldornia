class_name CharacterWin
extends Win
## Charakterfenster (GDD 6): Ausrüstungsplätze inkl. Klassenslot, 3D-Vorschau, Werte, Ruf und Titel.

var hud
var tabs: TabContainer
var preview: ModelPreview
var eq_slots: Dictionary = {}
var stats_box: RichTextLabel
var head_l: Label
var rep_list: VBoxContainer
var title_list: VBoxContainer
var dur_label: RichTextLabel

const LEFT := ["head", "neck", "shoulders", "back", "chest"]
const RIGHT := ["hands", "legs", "feet", "ring1", "ring2"]
const BOTTOM := ["main_hand", "off_hand", "class"]
const PLACEHOLDER := {"head": "visored-helm", "neck": "gem-pendant", "shoulders": "shoulder-armor", "back": "cape",
	"chest": "chest-armor", "hands": "gauntlet", "legs": "leg-armor", "feet": "boots", "ring1": "ring", "ring2": "ring",
	"main_hand": "broadsword", "off_hand": "shield", "class": "star-swirl"}


func _init(p_hud) -> void:
	super("Charakter", "charakter", Vector2(560, 560))
	hud = p_hud


func _ready() -> void:
	head_l = UiSkin.label("", 16, UiSkin.TEXT, UiSkin.font_bold)
	head_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(head_l)
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(540, 480)
	body.add_child(tabs)
	# --- Charakter
	var page := UiSkin.vbox(6)
	page.name = "Ausrüstung"
	tabs.add_child(page)
	var row := UiSkin.hbox(8)
	page.add_child(row)
	var lcol := UiSkin.vbox(4)
	row.add_child(lcol)
	for s in LEFT:
		lcol.add_child(_slot(s))
	preview = ModelPreview.new(Vector2(250, 260))
	row.add_child(preview)
	var rcol := UiSkin.vbox(4)
	row.add_child(rcol)
	for s in RIGHT:
		rcol.add_child(_slot(s))
	var brow := UiSkin.hbox(6)
	brow.alignment = BoxContainer.ALIGNMENT_CENTER
	page.add_child(brow)
	for s in BOTTOM:
		brow.add_child(_slot(s))
	dur_label = UiSkin.rich("")
	page.add_child(dur_label)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(520, 120)
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page.add_child(sc)
	stats_box = UiSkin.rich("")
	stats_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stats_box.add_theme_font_size_override("normal_font_size", 15)
	sc.add_child(stats_box)
	# --- Ruf
	var rs := ScrollContainer.new()
	rs.name = "Ruf"
	tabs.add_child(rs)
	rep_list = UiSkin.vbox(6)
	rep_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rs.add_child(rep_list)
	# --- Titel
	var ts := ScrollContainer.new()
	ts.name = "Titel"
	tabs.add_child(ts)
	title_list = UiSkin.vbox(4)
	title_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ts.add_child(title_list)
	tabs.tab_changed.connect(func(i):
		if i == 1:
			Game.send({"t": "get", "w": "reputation"})
		elif i == 2:
			Game.send({"t": "get", "w": "collections"})
	)
	Game.state_changed.connect(func(w):
		if not visible:
			return
		if w in ["inventory", "stats", "level"]:
			refresh()
		elif w == "reputation":
			_rep()
		elif w == "collections":
			_titles()
	)
	position = Vector2(40, 120)


func _slot(s: String) -> IconSlot:
	var sl := IconSlot.new(46)
	sl.kind = "equip"
	sl.key = s
	sl.accepts_drop = true
	sl.placeholder = Content.icon(PLACEHOLDER.get(s, "swap-bag"), Color(0.15, 0.13, 0.11), 48, Color(0.6, 0.55, 0.45))
	sl.clicked.connect(func(slot, b):
		if b == MOUSE_BUTTON_RIGHT and Game.equipment.get(s):
			Game.send({"t": "unequip", "s": s})
		elif b == MOUSE_BUTTON_LEFT and Input.is_key_pressed(KEY_SHIFT) and Game.equipment.get(s):
			hud.chat.focus_input("[%s] " % Content.item(str(Game.equipment[s]["i"])).get("name", ""))
	)
	sl.dropped.connect(func(_slot, data):
		if str(data.get("from", "")) == "bag":
			Game.send({"t": "equip", "slot": int(data.get("index", -1)), "to": s})
	)
	eq_slots[s] = sl
	return sl


func _on_open() -> void:
	Game.send({"t": "get", "w": "stats"})
	refresh()


func refresh() -> void:
	var c := Content.cls(Game.me_cls)
	head_l.text = "%s%s – Stufe %d %s%s" % [Game.title + " " if Game.title != "" else "", Game.me_name, Game.level,
		Content.class_name_of(Game.me_cls), (" (%s)" % Game.spec) if Game.spec != "" else ""]
	head_l.add_theme_color_override("font_color", Content.class_color(Game.me_cls))
	var low_dur := 0
	for s in eq_slots:
		var sl: IconSlot = eq_slots[s]
		var inst = Game.equipment.get(s)
		if inst is Dictionary:
			sl.set_item(str(inst["i"]), 1, inst)
			sl.red = int(inst.get("d", 100)) <= 0
			if int(inst.get("d", 100)) < 25:
				low_dur += 1
		else:
			sl.clear()
			var nm: String = Tips.SLOT_TXT.get(s.trim_suffix("1").trim_suffix("2"), s)
			if s == "class":
				nm = str(c.get("class_slot_name", "Klassenslot"))
			sl.set_icon(null, "[b]%s[/b]\nLeer" % nm)
	dur_label.text = ("[center][color=#ff8040]%d Gegenstände sind stark beschädigt. Reparaturkosten: %s[/color][/center]" % [low_dur, Content.money_bb(Game.repair_cost)]) if low_dur > 0 else ""
	if hud.world.me:
		var look: Dictionary = hud.world.me.look
		preview.show_humanoid(look, look.get("gear", {}))
	_stats()


func _stats() -> void:
	var st := Game.stats
	if st.is_empty():
		return
	var pn: String = Content.POWER_NAMES.get(Game.power_type, "")
	var me = hud.world.me
	var s := "[table=4]"
	var rows := [
		["Stärke", st.get("str", 0), "Rüstung", st.get("armor", 0)],
		["Beweglichkeit", st.get("agi", 0), "Ausweichen", "%s %%" % str(st.get("dodge", 0))],
		["Ausdauer", st.get("sta", 0), "Parieren", "%s %%" % str(st.get("parry", 0))],
		["Intelligenz", st.get("int", 0), "Blocken", "%s %%" % str(st.get("block", 0))],
		["Willenskraft", st.get("spi", 0), "Tempo", "%s %%" % str(st.get("haste", 0))],
		["Angriffskraft", st.get("ap", 0), "Krit. (Nahk.)", "%s %%" % str(st.get("crit", 0))],
		["Zaubermacht", st.get("sp", 0), "Krit. (Zauber)", "%s %%" % str(st.get("spell_crit", 0))],
		["Heilkraft", st.get("heal", 0), "Waffenschaden", "%s – %s" % [str(st.get("dmg_min", 0)), str(st.get("dmg_max", 0))]],
		["Gesundheit", "%d" % (me.mhp if me else 0), pn, "%d" % (me.mpw if me else 0)],
		["Feuerwid.", st.get("fire_res", 0), "Frostwid.", st.get("frost_res", 0)],
		["Naturwid.", st.get("nature_res", 0), "Schattenwid.", st.get("shadow_res", 0)],
		["Arkanwid.", st.get("arcane_res", 0), "Angriffstempo", "%s" % str(st.get("speed", 0))],
	]
	for r in rows:
		s += "[cell][color=#e8c374]%s[/color]  [/cell][cell]%s      [/cell][cell][color=#e8c374]%s[/color]  [/cell][cell]%s[/cell]" % [r[0], str(r[1]), r[2], str(r[3])]
	s += "[/table]"
	stats_box.text = s


func _rep() -> void:
	for c in rep_list.get_children():
		c.queue_free()
	for f in Game.reputation:
		var box := UiSkin.vbox(1)
		var h := UiSkin.hbox(6)
		box.add_child(h)
		var ic := TextureRect.new()
		ic.texture = Content.icon(str(f.get("icon", "flag-objective")), Color(0.3, 0.25, 0.15), 32)
		ic.custom_minimum_size = Vector2(22, 22)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		h.add_child(ic)
		var nl := UiSkin.label(str(f.get("name", "")), 16, UiSkin.GOLD, UiSkin.font_bold)
		nl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		nl.tooltip_text = str(f.get("desc", ""))
		nl.mouse_filter = Control.MOUSE_FILTER_PASS
		h.add_child(nl)
		h.add_child(UiSkin.label(str(f.get("st", "")), 15, _standing_color(str(f.get("st", "")))))
		var bar := StatBar.new(_standing_color(str(f.get("st", ""))), 14)
		bar.custom_minimum_size = Vector2(480, 14)
		var lo := int(f.get("lo", 0))
		var hi := int(f.get("hi", 1))
		var v := int(f.get("v", 0))
		bar.set_values(v - lo, maxf(1, hi - lo), "%d / %d" % [v - lo, hi - lo])
		bar.text_size = 11
		box.add_child(bar)
		rep_list.add_child(box)


func _standing_color(st: String) -> Color:
	return {"Hasserfüllt": Color(0.8, 0.1, 0.1), "Feindselig": Color(0.9, 0.25, 0.1), "Unfreundlich": Color(0.9, 0.5, 0.1),
		"Neutral": Color(0.9, 0.85, 0.2), "Freundlich": Color(0.3, 0.8, 0.2), "Wohlwollend": Color(0.2, 0.8, 0.5),
		"Respektvoll": Color(0.2, 0.7, 0.8), "Ehrfürchtig": Color(0.5, 0.4, 1.0)}.get(st, Color(0.3, 0.7, 0.3))


func _titles() -> void:
	for c in title_list.get_children():
		c.queue_free()
	var col: Dictionary = Game.collections
	var cur = col.get("title")
	title_list.add_child(UiSkin.button("Kein Titel" + (" ✓" if cur == null else ""), func(): Game.send({"t": "title", "id": null})))
	for t in col.get("titles", []):
		var tid := str(t["id"])
		title_list.add_child(UiSkin.button(str(t["name"]) + (" ✓" if str(cur) == tid else ""), func(): Game.send({"t": "title", "id": tid})))
	if col.get("titles", []).is_empty():
		title_list.add_child(UiSkin.label("Ihr habt noch keine Titel errungen. Titel erhaltet Ihr durch Erfolge, Quests und Ruf.", 15, UiSkin.TEXT_DIM))
