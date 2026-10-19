extends Node
## Einstiegspunkt: Anmeldung → Charakterwahl → Charaktererstellung → Spielwelt.

var ui_layer: CanvasLayer
var ui: Control
var menu: MenuScene
var screen: Control
var world: Node3D
var hud: Control
var loading: Control


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	for a in args:
		if a.begins_with("--visual-test"):
			var vt = load("res://src/dev/visual_test.gd").new()
			add_child(vt)
			return
		if a.begins_with("--check"):
			var ck = load("res://src/dev/check.gd").new()
			add_child(ck)
			return
	UiSkin.init()
	get_tree().root.theme = UiSkin.theme
	get_tree().set_auto_accept_quit(false)
	ui_layer = CanvasLayer.new()
	ui_layer.layer = 10
	add_child(ui_layer)
	ui = Control.new()
	ui.name = "UI"
	ui.theme = UiSkin.theme
	ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_layer.add_child(ui)
	Net.disconnected.connect(_on_disconnected)
	Game.msg.connect(_on_game_msg)
	for a in args:
		if a.begins_with("--server="):
			Settings.server = a.substr(9)
	show_login()
	Sfx.play_music("menu")
	for a in args:
		if a.begins_with("--auto="):
			add_child(load("res://src/dev/auto_play.gd").new(self))


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		Settings.save_settings()
		Net.close_world("Spiel beendet.")
		get_tree().quit()


func _ensure_menu() -> void:
	if menu == null:
		menu = MenuScene.new()
		add_child(menu)


func _set_screen(c: Control) -> void:
	if screen:
		screen.queue_free()
	screen = c
	if c:
		ui.add_child(c)


func show_login(msg := "") -> void:
	_leave_world()
	_ensure_menu()
	menu.set_mode("login")
	menu.clear_model()
	var s := LoginScreen.new()
	s.logged_in.connect(_on_logged_in)
	_set_screen(s)
	if msg != "":
		s.show_error(msg)


func _on_logged_in() -> void:
	if not Content.ready_ok:
		Content.fetch(func(ok: bool, code: int, _d):
			if ok:
				show_select()
			else:
				show_login("Spielinhalte konnten nicht geladen werden: " + Net.error_text(code, _d))
		)
	else:
		show_select()


func show_select(select_id := 0) -> void:
	_leave_world()
	_ensure_menu()
	menu.set_mode("select")
	var s := CharSelect.new(menu)
	s.enter_world.connect(_enter_world)
	s.create.connect(show_create)
	s.logout.connect(func():
		Net.token = ""
		show_login()
	)
	_set_screen(s)
	s.refresh(select_id)
	Sfx.play_music("menu")


func show_create() -> void:
	_ensure_menu()
	menu.set_mode("create")
	var s := CharCreate.new(menu)
	s.created.connect(func(cid: int): show_select(cid))
	s.cancelled.connect(func(): show_select())
	_set_screen(s)


func _enter_world(char_id: int) -> void:
	Game.char_id = char_id
	Game.reset_world()
	_set_screen(null)
	loading = LoadingScreen.new()
	ui.add_child(loading)
	loading.set_text("Verbinde mit Eldornia ...")
	Net.connect_world(char_id)


func _on_game_msg(t: String, m: Dictionary) -> void:
	match t:
		"welcome":
			_build_world(m)
		"zone":
			if world:
				if loading == null:
					loading = LoadingScreen.new()
					ui.add_child(loading)
				loading.set_text("Betrete %s ..." % str(m.get("name", "")))
				loading.set_zone(str(m.get("zone", "")))
				world.change_zone(m, func(): _hide_loading())
		"kick":
			Net.close_world(str(m.get("text", "Verbindung getrennt.")))


func _build_world(m: Dictionary) -> void:
	if loading == null:
		loading = LoadingScreen.new()
		ui.add_child(loading)
	loading.set_text("Lade %s ..." % str(m.get("zone_name", "")))
	loading.set_zone(str(m.get("zone", "")))
	if world == null:
		if menu:
			menu.queue_free()
			menu = null
		world = WorldView.new()
		add_child(world)
		hud = Hud.new(world)
		ui.add_child(hud)
		ui.move_child(hud, 0)
		world.hud = hud
		world.leave_requested.connect(func(): show_select(Game.char_id))
	world.start(m, func(): _hide_loading())


func _hide_loading() -> void:
	if loading:
		loading.fade_out()
		loading = null


func _leave_world() -> void:
	if world:
		Net.close_world("")
		world.queue_free()
		world = null
	if hud:
		hud.queue_free()
		hud = null
	if loading:
		loading.queue_free()
		loading = null
	Game.reset_world()


func _on_disconnected(reason: String) -> void:
	if reason == "":
		return
	if world or loading:
		_leave_world()
		if Net.token != "":
			show_select(Game.char_id)
			if screen is CharSelect:
				screen.show_message(reason)
		else:
			show_login(reason)
