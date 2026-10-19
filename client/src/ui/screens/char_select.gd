class_name CharSelect
extends Control
## Charakterauswahl mit 3D-Vorschau.

signal enter_world(char_id: int)
signal create
signal logout

var menu: MenuScene
var list_box: VBoxContainer
var selected := 0
var chars: Array = []
var info: Label
var msg_label: Label
var enter_btn: Button
var _drag := false


func _init(p_menu: MenuScene) -> void:
	menu = p_menu


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var right := PanelContainer.new()
	right.set_anchors_preset(Control.PRESET_RIGHT_WIDE)
	right.offset_left = -360
	right.offset_right = -20
	right.offset_top = 40
	right.offset_bottom = -150
	add_child(right)
	var rv := UiSkin.vbox(8)
	right.add_child(rv)
	var t := UiSkin.title_label("Charaktere", 22)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	rv.add_child(t)
	var acc := UiSkin.label("Account: " + Game.username, 14, UiSkin.TEXT_DIM)
	acc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	rv.add_child(acc)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	rv.add_child(scroll)
	list_box = UiSkin.vbox(6)
	list_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(list_box)
	var new_btn := UiSkin.button("Neuen Charakter erstellen", func(): create.emit())
	rv.add_child(new_btn)
	var del_btn := UiSkin.button("Charakter löschen", _delete)
	rv.add_child(del_btn)
	enter_btn = UiSkin.button("Welt betreten", func():
		if selected > 0:
			Sfx.play("quest")
			enter_world.emit(selected)
	)
	enter_btn.add_theme_font_size_override("font_size", 24)
	enter_btn.add_theme_font_override("font", UiSkin.font_title)
	enter_btn.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	enter_btn.custom_minimum_size = Vector2(300, 56)
	enter_btn.position = Vector2(-150, -110)
	add_child(enter_btn)
	info = UiSkin.label("", 20, UiSkin.GOLD, UiSkin.font_title)
	info.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	info.position = Vector2(-300, -170)
	info.size = Vector2(600, 50)
	add_child(info)
	msg_label = UiSkin.label("", 16, Color("#ffb080"))
	msg_label.set_anchors_preset(Control.PRESET_CENTER_TOP)
	msg_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	msg_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	msg_label.position = Vector2(-350, 20)
	msg_label.size = Vector2(700, 60)
	add_child(msg_label)
	var back := UiSkin.button("Abmelden", func(): logout.emit())
	back.position = Vector2(20, 20)
	add_child(back)
	var srv := UiSkin.label("", 13, Color(1, 1, 1, 0.5))
	srv.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	srv.position = Vector2(20, -30)
	add_child(srv)
	Net.get_json("/api/status", func(ok: bool, _c: int, d):
		if ok and d is Dictionary:
			srv.text = "%s · %d Spieler online · Server %s" % [Settings.server, int(d.get("online", 0)), str(d.get("version", ""))]
	)


func show_message(t: String) -> void:
	if msg_label:
		msg_label.text = t


func refresh(select_id := 0) -> void:
	Net.get_json("/api/characters", func(ok: bool, code: int, data):
		if not ok:
			show_message(Net.error_text(code, data))
			return
		chars = data.get("characters", [])
		Game.characters = chars
		_build_list(select_id)
	)


func _build_list(select_id: int) -> void:
	for c in list_box.get_children():
		c.queue_free()
	if chars.is_empty():
		list_box.add_child(UiSkin.label("Noch kein Charakter.\nErstelle deinen ersten Helden!", 16, UiSkin.TEXT_DIM))
		selected = 0
		info.text = ""
		enter_btn.disabled = true
		menu.clear_model()
		return
	enter_btn.disabled = false
	var pick: int = select_id if select_id > 0 else int(chars[0]["id"])
	for c in chars:
		var b := Button.new()
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(0, 58)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.text = "%s\nStufe %d %s · %s" % [c["name"], int(c["level"]), c["cls_name"], c["zone"]]
		b.add_theme_font_size_override("font_size", 16)
		b.add_theme_color_override("font_color", Content.class_color(str(c["cls"])))
		b.icon = Content.icon(str(Content.cls(str(c["cls"])).get("icon", "person")), Content.class_color(str(c["cls"])).darkened(0.5), 40)
		b.expand_icon = false
		var cid := int(c["id"])
		b.pressed.connect(func(): _select(cid))
		b.gui_input.connect(func(ev):
			if ev is InputEventMouseButton and ev.double_click:
				enter_world.emit(cid)
		)
		list_box.add_child(b)
	_select(pick)


func _select(cid: int) -> void:
	selected = cid
	for i in list_box.get_child_count():
		var b = list_box.get_child(i)
		if b is Button and i < chars.size():
			b.button_pressed = int(chars[i]["id"]) == cid
	for c in chars:
		if int(c["id"]) == cid:
			var look: Dictionary = c.get("look", {}).duplicate()
			var gear: Dictionary = look.get("gear", {})
			look.erase("gear")
			menu.model_rot = PI
			menu.show_model(look, gear)
			info.text = "%s – Stufe %d %s" % [c["name"], int(c["level"]), c["cls_name"]]


func _delete() -> void:
	if selected <= 0:
		return
	var name := ""
	for c in chars:
		if int(c["id"]) == selected:
			name = str(c["name"])
	var dlg := ConfirmationDialog.new()
	dlg.title = "Charakter löschen"
	dlg.dialog_text = "Willst du %s wirklich für immer löschen?\nGib zur Bestätigung den Namen ein." % name
	var le := LineEdit.new()
	dlg.add_child(le)
	dlg.register_text_enter(le)
	dlg.ok_button_text = "Löschen"
	dlg.cancel_button_text = "Abbrechen"
	add_child(dlg)
	dlg.popup_centered(Vector2i(420, 160))
	dlg.confirmed.connect(func():
		if le.text.strip_edges().to_lower() != name.to_lower():
			show_message("Der Name stimmt nicht überein.")
			return
		Net.api(HTTPClient.METHOD_DELETE, "/api/characters/%d" % selected, null, func(ok: bool, code: int, d):
			if ok:
				refresh()
			else:
				show_message(Net.error_text(code, d))
		)
	)


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		_drag = ev.pressed
	elif ev is InputEventMouseMotion and _drag:
		menu.rotate_model(ev.relative.x)


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and ev.keycode == KEY_ENTER and selected > 0:
		enter_world.emit(selected)
