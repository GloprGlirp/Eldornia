class_name SpellbookWin
extends Win
## Zauberbuch: alle erlernten Fähigkeiten (in die Aktionsleisten ziehbar), künftige Fähigkeiten, Emotes.

var hud
var tabs: TabContainer
var list: GridContainer
var future: VBoxContainer
var general: GridContainer

const EMOTES := [["winken", "hand"], ["tanzen", "music-spell"], ["verbeugen", "person"], ["lachen", "drama-masks"],
	["jubeln", "trophy-cup"], ["weinen", "drop"], ["sitzen", "camp-cooking-pot"], ["schlafen", "night-sleep"],
	["knien", "kneeling"], ["salutieren", "flag-objective"], ["klatschen", "hand"], ["zeigen", "pointing"]]


func _init(p_hud) -> void:
	super("Zauberbuch", "zauberbuch", Vector2(560, 520))
	hud = p_hud


func _ready() -> void:
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(540, 470)
	body.add_child(tabs)
	var sc := ScrollContainer.new()
	sc.name = Content.class_name_of(Game.me_cls)
	tabs.add_child(sc)
	var v := UiSkin.vbox(10)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(v)
	list = GridContainer.new()
	list.columns = 2
	list.add_theme_constant_override("h_separation", 12)
	list.add_theme_constant_override("v_separation", 8)
	v.add_child(list)
	v.add_child(UiSkin.title_label("Noch zu erlernen", 17))
	future = UiSkin.vbox(4)
	v.add_child(future)
	var gs := ScrollContainer.new()
	gs.name = "Allgemein"
	tabs.add_child(gs)
	general = GridContainer.new()
	general.columns = 2
	general.add_theme_constant_override("h_separation", 12)
	general.add_theme_constant_override("v_separation", 8)
	gs.add_child(general)
	Game.state_changed.connect(func(w):
		if w == "abilities" and visible:
			refresh()
	)
	position = Vector2(120, 110)


func _on_open() -> void:
	refresh()


func refresh() -> void:
	for c in list.get_children():
		c.queue_free()
	for c in future.get_children():
		c.queue_free()
	for c in general.get_children():
		c.queue_free()
	for id in Game.ability_order:
		var ab: Dictionary = Game.abilities[id]
		list.add_child(_entry_ability(ab))
	for f in Game.future_abilities:
		var h := UiSkin.hbox(8)
		var t := TextureRect.new()
		t.texture = Content.icon(str(f.get("icon", "sword-wound")), Color(0.25, 0.25, 0.25), 48)
		t.custom_minimum_size = Vector2(30, 30)
		t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		t.modulate = Color(0.6, 0.6, 0.6)
		h.add_child(t)
		h.add_child(UiSkin.label("%s  –  ab Stufe %d" % [str(f.get("name", "")), int(f.get("level", 1))], 15, UiSkin.TEXT_DIM))
		future.add_child(h)
	for e in EMOTES:
		var h2 := UiSkin.hbox(8)
		var s := IconSlot.new(40)
		s.set_icon(Content.icon(e[1], Color(0.3, 0.3, 0.42), 48), "Emote: /%s" % e[0])
		s.payload = {"emote": e[0]}
		var em: String = e[0]
		s.clicked.connect(func(_s, _b): Game.send({"t": "emote", "e": em}))
		h2.add_child(s)
		h2.add_child(UiSkin.label("/" + e[0], 15))
		general.add_child(h2)
	var hs := IconSlot.new(40)
	hs.set_item("ruhestein", 1)
	hs.clicked.connect(func(_s, _b): Game.send({"t": "hearth"}))
	var hh := UiSkin.hbox(8)
	hh.add_child(hs)
	hh.add_child(UiSkin.label("Ruhestein", 15))
	general.add_child(hh)


func _entry_ability(ab: Dictionary) -> Control:
	var h := UiSkin.hbox(8)
	h.custom_minimum_size = Vector2(250, 44)
	var s := IconSlot.new(42)
	s.kind = "ab"
	s.set_ability(ab)
	var id := str(ab["id"])
	s.clicked.connect(func(_s, b):
		if b == MOUSE_BUTTON_LEFT and Input.is_key_pressed(KEY_SHIFT):
			hud.chat.focus_input(hud.chat.input.text + "[%s] " % ab.get("name", ""))
		else:
			hud.world.use_ability(id)
	)
	h.add_child(s)
	var v := UiSkin.vbox(0)
	v.add_child(UiSkin.label(str(ab.get("name", "")), 16, UiSkin.TEXT, UiSkin.font_bold))
	var sub := "Passiv" if ab.get("passive", false) else ("Talent" if ab.get("talent", false) else "Stufe %d" % int(ab.get("level", 1)))
	v.add_child(UiSkin.label(sub, 13, UiSkin.TEXT_DIM))
	h.add_child(v)
	return h
