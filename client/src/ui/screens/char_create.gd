class_name CharCreate
extends Control
## Charaktererstellung: Klasse wählen (8 spielbar, weitere geplant), Aussehen anpassen, Namen vergeben.

signal created(char_id: int)
signal cancelled

const SKINS := ["#f2c9a8", "#e8b896", "#e0ae8c", "#c98a6a", "#a9785a", "#7a5238", "#5a3a28", "#d8c0a8"]
const HAIRS := ["#1a1410", "#3a2414", "#6a4422", "#a86a32", "#d8b060", "#e8e0d0", "#8a2a1a", "#4a4a52", "#3a5a8a", "#6a3a6a"]
const STYLES := [["short", "Kurz"], ["long", "Lang"], ["braid", "Zopf"], ["bun", "Dutt"], ["ponytail", "Pferdeschwanz"],
	["wild", "Wild"], ["mohawk", "Irokese"], ["tonsure", "Tonsur"], ["bald", "Glatze"]]
const KINDS := [["human", "Mensch"], ["dwarf", "Zwerg"], ["elf", "Elf"]]

var menu: MenuScene
var cls := "ritter"
var look := {"body": "m", "skin": "#e0ae8c", "hair": "#3a2414", "hair_style": "short", "kind": "human", "beard": ""}
var desc: RichTextLabel
var name_edit: LineEdit
var status: Label
var class_buttons: Dictionary = {}
var _drag := false


func _init(p_menu: MenuScene) -> void:
	menu = p_menu


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	# --- links: Klassen
	var left := PanelContainer.new()
	left.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	left.offset_left = 20
	left.offset_right = 420
	left.offset_top = 20
	left.offset_bottom = -20
	add_child(left)
	var lv := UiSkin.vbox(8)
	left.add_child(lv)
	var t := UiSkin.title_label("Wähle deine Klasse", 22)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	lv.add_child(t)
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	lv.add_child(grid)
	var classes: Dictionary = Content.defs.get("classes", {})
	for cid in classes:
		var c: Dictionary = classes[cid]
		var b := Button.new()
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(86, 86)
		b.icon = Content.icon(str(c.get("icon", "person")), Content.class_color(cid).darkened(0.45), 56)
		b.expand_icon = true
		b.tooltip_text = "%s – %s" % [c["name"], c["role"]]
		b.pressed.connect(_pick_class.bind(cid))
		grid.add_child(b)
		class_buttons[cid] = b
	for pc in Content.defs.get("planned", []):
		var b := Button.new()
		b.disabled = true
		b.custom_minimum_size = Vector2(86, 86)
		b.icon = Content.icon("padlock", Color(0.25, 0.22, 0.2), 48)
		b.expand_icon = true
		b.tooltip_text = "%s – %s\n(Kommt in einem späteren Update)" % [pc["name"], pc["role"]]
		grid.add_child(b)
	var dscroll := ScrollContainer.new()
	dscroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	lv.add_child(dscroll)
	desc = UiSkin.rich("")
	desc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	dscroll.add_child(desc)
	# --- rechts: Aussehen
	var right := PanelContainer.new()
	right.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	right.offset_left = -400
	right.offset_right = -20
	right.offset_top = 20
	right.offset_bottom = -20
	add_child(right)
	var rv := UiSkin.vbox(8)
	right.add_child(rv)
	var t2 := UiSkin.title_label("Aussehen", 22)
	t2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	rv.add_child(t2)
	rv.add_child(UiSkin.label("Volk", 15, UiSkin.TEXT_DIM))
	rv.add_child(_options(KINDS, "kind"))
	rv.add_child(UiSkin.label("Körper", 15, UiSkin.TEXT_DIM))
	rv.add_child(_options([["m", "Männlich"], ["f", "Weiblich"]], "body"))
	rv.add_child(UiSkin.label("Hautfarbe", 15, UiSkin.TEXT_DIM))
	rv.add_child(_swatches(SKINS, "skin"))
	rv.add_child(UiSkin.label("Frisur", 15, UiSkin.TEXT_DIM))
	var ob := OptionButton.new()
	for s in STYLES:
		ob.add_item(s[1])
	ob.item_selected.connect(func(i): _set_look("hair_style", STYLES[i][0]))
	rv.add_child(ob)
	rv.add_child(UiSkin.label("Haarfarbe", 15, UiSkin.TEXT_DIM))
	rv.add_child(_swatches(HAIRS, "hair"))
	rv.add_child(UiSkin.label("Bart", 15, UiSkin.TEXT_DIM))
	var beard := OptionButton.new()
	for s in ["Kein Bart", "Kurzer Bart", "Langer Bart"]:
		beard.add_item(s)
	beard.item_selected.connect(func(i):
		look["beard"] = "" if i == 0 else look.get("hair", "#3a2414")
		look["beard_style"] = "long" if i == 2 else "short"
		_update_model()
	)
	rv.add_child(beard)
	rv.add_child(UiSkin.button("Zufällig", _randomize))
	rv.add_child(UiSkin.spacer())
	rv.add_child(UiSkin.label("Name", 15, UiSkin.TEXT_DIM))
	name_edit = LineEdit.new()
	name_edit.max_length = 16
	name_edit.placeholder_text = "3–16 Buchstaben"
	name_edit.text_submitted.connect(func(_t): _create())
	rv.add_child(name_edit)
	status = UiSkin.label("", 15, Color("#ff8a6a"))
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.custom_minimum_size.x = 340
	rv.add_child(status)
	var cb := UiSkin.button("Charakter erstellen", _create)
	cb.custom_minimum_size.y = 46
	cb.add_theme_font_override("font", UiSkin.font_title)
	rv.add_child(cb)
	rv.add_child(UiSkin.button("Zurück", func(): cancelled.emit()))
	_pick_class("ritter")


func _options(opts: Array, key: String) -> HBoxContainer:
	var h := UiSkin.hbox(6)
	var group := ButtonGroup.new()
	for o in opts:
		var b := Button.new()
		b.text = o[1]
		b.toggle_mode = true
		b.button_group = group
		b.button_pressed = str(look.get(key, "")) == o[0]
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(func(): _set_look(key, o[0]))
		h.add_child(b)
	return h


func _swatches(cols: Array, key: String) -> HFlowContainer:
	var h := HFlowContainer.new()
	h.add_theme_constant_override("h_separation", 4)
	h.add_theme_constant_override("v_separation", 4)
	for c in cols:
		var b := Button.new()
		b.custom_minimum_size = Vector2(30, 30)
		var sb := UiSkin.flat(Color.html(c), Color("#e8c374"), 2, 4)
		b.add_theme_stylebox_override("normal", sb)
		var sbh := UiSkin.flat(Color.html(c).lightened(0.2), Color.WHITE, 2, 4)
		b.add_theme_stylebox_override("hover", sbh)
		b.add_theme_stylebox_override("pressed", sbh)
		b.pressed.connect(func(): _set_look(key, c))
		h.add_child(b)
	return h


func _set_look(key: String, v) -> void:
	look[key] = v
	if key == "hair" and str(look.get("beard", "")) != "":
		look["beard"] = v
	_update_model()


func _pick_class(cid: String) -> void:
	cls = cid
	for k in class_buttons:
		class_buttons[k].button_pressed = k == cid
	var c := Content.cls(cid)
	var res: String = Content.POWER_NAMES.get(str(c.get("resource", "")), "")
	var s := "[font_size=26][color=%s]%s[/color][/font_size]\n" % [Content.CLASS_COLORS.get(cid, "#fff"), c.get("name", "")]
	s += "[color=#e8c374]%s[/color]   ·   %s\n\n" % [c.get("role", ""), c.get("difficulty", "")]
	s += "%s\n\n" % c.get("desc", "")
	s += "[color=#e8c374]Ressource:[/color] %s\n" % res
	s += "[color=#e8c374]Rüstung:[/color] %s\n" % ", ".join(c.get("armor", []))
	s += "[color=#e8c374]Waffen:[/color] %s\n\n" % ", ".join(c.get("weapons", []))
	s += "[color=#e8c374]Spezialisierungen:[/color]\n"
	for sp in c.get("specs", []):
		s += "  • [b]%s[/b] – %s\n" % [sp["name"], sp["role"]]
	s += "\n[color=#e8c374]Erste Fähigkeiten:[/color]\n"
	var shown := 0
	for ab in c.get("abilities", []):
		if ab.get("talent") or shown >= 6:
			continue
		s += "  • %s (Stufe %d)\n" % [ab["name"], int(ab["level"])]
		shown += 1
	desc.text = s
	_update_model()


func _update_model() -> void:
	var c := Content.cls(cls)
	var gear := {}
	var start: Dictionary = c.get("start", {}).get("equip", {})
	for slot in start:
		var it := Content.item(str(start[slot]))
		if not it.is_empty():
			gear[slot] = {"sub": it.get("sub"), "q": it.get("q", 1), "vis": it.get("vis", {}), "id": start[slot], "two": it.get("two_hand", false)}
	var l := look.duplicate()
	if str(l.get("beard", "")) == "":
		l.erase("beard")
	menu.model_rot = PI
	menu.show_model(l, gear)


func _randomize() -> void:
	look["body"] = ["m", "f"][randi() % 2]
	look["skin"] = SKINS[randi() % SKINS.size()]
	look["hair"] = HAIRS[randi() % HAIRS.size()]
	look["hair_style"] = STYLES[randi() % STYLES.size()][0]
	look["kind"] = KINDS[randi() % KINDS.size()][0]
	look["beard"] = look["hair"] if randf() < 0.4 and look["body"] == "m" else ""
	_update_model()


func _create() -> void:
	var n := name_edit.text.strip_edges()
	if n.length() < 3:
		status.text = "Bitte gib einen Namen ein (3–16 Buchstaben)."
		return
	var l := look.duplicate()
	if str(l.get("beard", "")) == "":
		l.erase("beard")
	Net.post_json("/api/characters", {"name": n, "cls": cls, "look": l}, func(ok: bool, code: int, data):
		if ok:
			Sfx.play("levelup")
			created.emit(int(data["id"]))
		else:
			status.text = Net.error_text(code, data)
			Sfx.play("error")
	)


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		_drag = ev.pressed
	elif ev is InputEventMouseMotion and _drag:
		menu.rotate_model(ev.relative.x)
