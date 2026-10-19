class_name LoginScreen
extends Control
## Anmeldebildschirm: Anmelden oder Account erstellen (GDD 14).

signal logged_in

var user_edit: LineEdit
var pass_edit: LineEdit
var pass2_edit: LineEdit
var mail_edit: LineEdit
var server_edit: LineEdit
var remember: CheckBox
var status: Label
var btn_main: Button
var btn_switch: Button
var reg_box: VBoxContainer
var server_box: HBoxContainer
var verify_box: HBoxContainer
var code_edit: LineEdit
var register_mode := false
var busy := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Logo
	var logo := Label.new()
	logo.text = "ELDORNIA"
	logo.add_theme_font_override("font", UiSkin.font_deco)
	logo.add_theme_font_size_override("font_size", 96)
	logo.add_theme_color_override("font_color", Color("#ffd27a"))
	logo.add_theme_color_override("font_outline_color", Color("#2a1406"))
	logo.add_theme_constant_override("outline_size", 14)
	logo.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.7))
	logo.add_theme_constant_override("shadow_offset_y", 6)
	logo.set_anchors_preset(Control.PRESET_CENTER_TOP)
	logo.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	logo.position = Vector2(-400, 40)
	logo.size = Vector2(800, 120)
	add_child(logo)
	var sub := UiSkin.label("Ein Reich voller Abenteuer", 22, Color("#f0e0c0"), UiSkin.font_italic)
	sub.set_anchors_preset(Control.PRESET_CENTER_TOP)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.position = Vector2(-300, 160)
	sub.size = Vector2(600, 30)
	add_child(sub)
	# Formular
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.custom_minimum_size = Vector2(400, 0)
	panel.position = Vector2(-200, -60)
	add_child(panel)
	var v := UiSkin.vbox(8)
	panel.add_child(v)
	var head := UiSkin.title_label("Anmeldung", 24)
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(head)
	v.add_child(UiSkin.label("Benutzername", 15, UiSkin.TEXT_DIM))
	user_edit = LineEdit.new()
	user_edit.text = Settings.username
	user_edit.placeholder_text = "Accountname"
	user_edit.max_length = 20
	v.add_child(user_edit)
	v.add_child(UiSkin.label("Passwort", 15, UiSkin.TEXT_DIM))
	pass_edit = LineEdit.new()
	pass_edit.secret = true
	pass_edit.placeholder_text = "Passwort"
	pass_edit.text_submitted.connect(func(_t): _submit())
	v.add_child(pass_edit)
	reg_box = UiSkin.vbox(6)
	reg_box.visible = false
	v.add_child(reg_box)
	reg_box.add_child(UiSkin.label("Passwort wiederholen", 15, UiSkin.TEXT_DIM))
	pass2_edit = LineEdit.new()
	pass2_edit.secret = true
	reg_box.add_child(pass2_edit)
	reg_box.add_child(UiSkin.label("E-Mail-Adresse (zur Bestätigung)", 15, UiSkin.TEXT_DIM))
	mail_edit = LineEdit.new()
	mail_edit.placeholder_text = "name@beispiel.de"
	reg_box.add_child(mail_edit)
	remember = CheckBox.new()
	remember.text = "Benutzernamen merken"
	remember.button_pressed = Settings.remember
	v.add_child(remember)
	verify_box = UiSkin.hbox(6)
	verify_box.visible = false
	v.add_child(verify_box)
	code_edit = LineEdit.new()
	code_edit.placeholder_text = "Bestätigungscode aus der E-Mail"
	code_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	verify_box.add_child(code_edit)
	verify_box.add_child(UiSkin.button("Bestätigen", _verify))
	btn_main = UiSkin.button("Anmelden", _submit)
	btn_main.custom_minimum_size.y = 40
	v.add_child(btn_main)
	btn_switch = UiSkin.button("Neuen Account erstellen", _toggle_mode)
	v.add_child(btn_switch)
	status = UiSkin.label("", 15, Color("#ff8a6a"))
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.custom_minimum_size.x = 360
	v.add_child(status)
	var srv_toggle := LinkButton.new()
	srv_toggle.text = "Server: " + Settings.server
	srv_toggle.add_theme_color_override("font_color", Color("#b8a888"))
	srv_toggle.add_theme_font_size_override("font_size", 13)
	v.add_child(srv_toggle)
	server_box = UiSkin.hbox(6)
	server_box.visible = false
	v.add_child(server_box)
	server_edit = LineEdit.new()
	server_edit.text = Settings.server
	server_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	server_box.add_child(server_edit)
	server_box.add_child(UiSkin.button("OK", func():
		Settings.server = server_edit.text.strip_edges()
		srv_toggle.text = "Server: " + Settings.server
		server_box.visible = false
		Settings.save_settings()
	))
	srv_toggle.pressed.connect(func(): server_box.visible = not server_box.visible)
	if OS.has_feature("web"):
		srv_toggle.visible = false
	# Fußzeile
	var ver := UiSkin.label("Eldornia %s · Godot %s" % [ProjectSettings.get_setting("application/config/version", "0.3"),
		Engine.get_version_info().get("string", "")], 13, Color(1, 1, 1, 0.55))
	ver.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	ver.position = Vector2(14, -30)
	add_child(ver)
	var credits := UiSkin.label("Symbole: game-icons.net (CC BY 3.0) · Schriften: Cinzel, Alegreya Sans (OFL)", 12, Color(1, 1, 1, 0.4))
	credits.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	credits.position = Vector2(-260, -28)
	add_child(credits)
	if not OS.has_feature("web"):
		var quit := UiSkin.button("Beenden", func(): get_tree().quit())
		quit.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
		quit.position = Vector2(-130, -54)
		add_child(quit)
	await get_tree().process_frame
	if user_edit.text == "":
		user_edit.grab_focus()
	else:
		pass_edit.grab_focus()


func show_error(t: String) -> void:
	status.add_theme_color_override("font_color", Color("#ff8a6a"))
	status.text = t


func show_info(t: String) -> void:
	status.add_theme_color_override("font_color", Color("#a0e0a0"))
	status.text = t


func _toggle_mode() -> void:
	register_mode = not register_mode
	reg_box.visible = register_mode
	btn_main.text = "Account erstellen" if register_mode else "Anmelden"
	btn_switch.text = "Zurück zur Anmeldung" if register_mode else "Neuen Account erstellen"
	status.text = ""


func _submit() -> void:
	if busy:
		return
	var u := user_edit.text.strip_edges()
	var p := pass_edit.text
	if u.length() < 3 or p.length() < 6:
		show_error("Benutzername (mind. 3 Zeichen) und Passwort (mind. 6 Zeichen) eingeben.")
		return
	if register_mode and p != pass2_edit.text:
		show_error("Die Passwörter stimmen nicht überein.")
		return
	busy = true
	btn_main.disabled = true
	show_info("Verbinde ...")
	var body := {"username": u, "password": p}
	if register_mode:
		body["email"] = mail_edit.text.strip_edges()
	Net.post_json("/api/register" if register_mode else "/api/login", body, func(ok: bool, code: int, data):
		busy = false
		btn_main.disabled = false
		if not ok:
			show_error(Net.error_text(code, data))
			Sfx.play("error")
			return
		Net.token = str(data["token"])
		Game.username = str(data["username"])
		Settings.remember = remember.button_pressed
		Settings.username = u
		Settings.save_settings()
		if data.get("verify", false) and register_mode:
			verify_box.visible = true
			show_info("Wir haben dir einen Bestätigungscode geschickt. Du kannst auch später bestätigen.")
		logged_in.emit()
	)


func _verify() -> void:
	Net.post_json("/api/verify", {"code": code_edit.text.strip_edges()}, func(ok: bool, code: int, data):
		if ok:
			show_info("E-Mail bestätigt. Willkommen!")
			verify_box.visible = false
		else:
			show_error(Net.error_text(code, data))
	)


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and ev.keycode == KEY_ENTER:
		_submit()
