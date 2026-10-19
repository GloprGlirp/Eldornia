class_name Hud
extends Control
## Spieloberfläche im Stil von World of Warcraft (GDD 11): Einheitenrahmen, Aktionsleisten, Zauberbalken,
## Minikarte, Questverfolgung, Chat, Erfahrungsleiste, Mikromenü, Meldungen, Dialoge und alle Fenster.

var world
var overlay: HudOverlay
var player_frame: UnitFrame
var target_frame: UnitFrame
var tot_frame: UnitFrame
var party: PartyFrames
var bars: ActionBars
var cast_bar: StatBar
var xp_bar: StatBar
var minimap: Minimap
var tracker: QuestTracker
var chat: ChatBox
var micro: HBoxContainer
var money_label: RichTextLabel
var perf_label: Label
var err_box: VBoxContainer
var zone_title: Label
var zone_sub: Label
var warn_box: VBoxContainer
var toast_box: VBoxContainer
var popup_box: VBoxContainer
var win_layer: Control
var windows: Dictionary = {}
var popups: Dictionary = {}
var ui_hidden := false
var _drag_data = null
var _perf_t := 0.0
var _was_dead := false
var _duel_count: Dictionary = {}

const MICRO := [
	["charakter", "person", "Charakter"], ["zauberbuch", "spell-book", "Zauberbuch"], ["talente", "skills", "Talente"],
	["erfolge", "trophy", "Erfolge"], ["questlog", "scroll-unfurled", "Questlog"], ["gilde", "family-tree", "Gilde"],
	["gruppensuche", "eye-target", "Gruppenfinder"], ["sammlung", "horse-head", "Sammlung"], ["berufe", "anvil", "Berufe"],
	["soziales", "two-shadows", "Soziales"], ["karte", "treasure-map", "Weltkarte"], ["menue", "cog", "Spielmenü"],
	["inventar", "swap-bag", "Taschen"],
]
const KEY_WINDOWS := {
	"inventar": "inventar", "charakter": "charakter", "zauberbuch": "zauberbuch", "talente": "talente", "questlog": "questlog",
	"karte": "karte", "gilde": "gilde", "berufe": "berufe", "erfolge": "erfolge", "sammlung": "sammlung",
	"gruppensuche": "gruppensuche", "soziales": "soziales",
}
const OPEN_MAP := {
	"professions": "berufe", "market": "markt", "guild": "gilde", "guild_create": "gilde", "collections": "sammlung",
	"transmog": "sammlung", "finder": "gruppensuche", "arena": "gruppensuche",
}


func _init(p_world) -> void:
	world = p_world
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	theme = UiSkin.theme


func _ready() -> void:
	overlay = HudOverlay.new(world)
	add_child(overlay)
	# Einheitenrahmen
	player_frame = UnitFrame.new(world)
	player_frame.is_player_frame = true
	player_frame.position = Vector2(16, 14)
	player_frame.clicked.connect(func(b):
		if b == MOUSE_BUTTON_LEFT:
			world.set_target(Game.me_id)
		elif b == MOUSE_BUTTON_RIGHT:
			_unit_menu(Game.me_id)
	)
	add_child(player_frame)
	target_frame = UnitFrame.new(world)
	target_frame.position = Vector2(290, 14)
	target_frame.clicked.connect(func(b):
		if b == MOUSE_BUTTON_RIGHT:
			_unit_menu(world.target)
	)
	add_child(target_frame)
	tot_frame = UnitFrame.new(world, true)
	tot_frame.position = Vector2(540, 30)
	tot_frame.clicked.connect(func(b):
		var e = world.ent(world.target)
		if e and e.target_id != 0 and b == MOUSE_BUTTON_LEFT:
			world.set_target(e.target_id)
	)
	add_child(tot_frame)
	party = PartyFrames.new(self)
	party.position = Vector2(16, 190)
	add_child(party)
	# Aktionsleisten, Zauber- und Erfahrungsbalken
	bars = ActionBars.new(world)
	add_child(bars)
	cast_bar = StatBar.new(Color("#e8a020"), 22)
	cast_bar.size = Vector2(300, 22)
	cast_bar.spark = true
	cast_bar.visible = false
	cast_bar.text_size = 14
	add_child(cast_bar)
	xp_bar = StatBar.new(Color("#9a3ad8"), 10)
	xp_bar.text_size = 11
	xp_bar.tooltip_text = " "
	add_child(xp_bar)
	# Minikarte, Questverfolgung, Chat
	minimap = Minimap.new(world)
	add_child(minimap)
	tracker = QuestTracker.new(self)
	add_child(tracker)
	chat = ChatBox.new(self)
	add_child(chat)
	# Mikromenü
	micro = UiSkin.hbox(2)
	add_child(micro)
	for m in MICRO:
		var s := IconSlot.new(30)
		s.drag_enabled = false
		var key_lbl := ""
		if Settings.keys.has(m[0]):
			key_lbl = " (%s)" % Settings.key_label(m[0])
		s.set_icon(Content.icon(m[1], Color(0.45, 0.18, 0.12), 48), "%s%s" % [m[2], key_lbl])
		var wid: String = m[0]
		s.clicked.connect(func(_s, _b): toggle_window(wid))
		micro.add_child(s)
	money_label = UiSkin.rich("")
	money_label.custom_minimum_size = Vector2(240, 22)
	money_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	money_label.add_theme_font_size_override("normal_font_size", 15)
	add_child(money_label)
	perf_label = UiSkin.label("", 11, Color(0.75, 0.75, 0.7))
	perf_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(perf_label)
	# Meldungen
	err_box = UiSkin.vbox(0)
	err_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(err_box)
	warn_box = UiSkin.vbox(4)
	warn_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(warn_box)
	zone_title = UiSkin.label("", 46, Color("#ffd870"), UiSkin.font_deco)
	zone_title.add_theme_color_override("font_outline_color", Color(0.1, 0.05, 0.0))
	zone_title.add_theme_constant_override("outline_size", 8)
	zone_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	zone_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zone_title.modulate.a = 0.0
	add_child(zone_title)
	zone_sub = UiSkin.label("", 22, Color("#f0e0b0"), UiSkin.font_title)
	zone_sub.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	zone_sub.add_theme_constant_override("outline_size", 5)
	zone_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	zone_sub.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zone_sub.modulate.a = 0.0
	add_child(zone_sub)
	toast_box = UiSkin.vbox(6)
	toast_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(toast_box)
	# Fenster und Dialoge
	win_layer = Control.new()
	win_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	win_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(win_layer)
	popup_box = UiSkin.vbox(8)
	popup_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(popup_box)
	Game.msg.connect(_on_msg)
	Game.system_text.connect(_on_system_text)
	Game.state_changed.connect(_on_state)
	world.target_changed.connect(_on_target_changed)
	get_viewport().size_changed.connect(_layout)
	_layout()
	_refresh_money()


# ============================================================================== Anordnung
func _layout() -> void:
	var vp := get_viewport_rect().size
	bars.layout(vp)
	var w1 := 12 * 49
	xp_bar.position = Vector2((vp.x - w1) * 0.5, vp.y - 15)
	xp_bar.size = Vector2(w1 - 3, 10)
	cast_bar.position = Vector2((vp.x - 300) * 0.5, vp.y - 175)
	minimap.position = Vector2(vp.x - 228, 6)
	tracker.position = Vector2(vp.x - 300, 268)
	tracker.size = Vector2(250, vp.y * 0.45)
	chat.position = Vector2(10, vp.y - 300)
	chat.size = Vector2(minf(470, vp.x * 0.32), 240)
	micro.position = Vector2(vp.x - MICRO.size() * 32 - 10, vp.y - 40)
	money_label.position = Vector2(vp.x - 260, vp.y - 66)
	perf_label.position = Vector2(vp.x - 150, vp.y - 18)
	err_box.position = Vector2(vp.x * 0.5 - 300, 110)
	err_box.size = Vector2(600, 80)
	warn_box.position = Vector2(vp.x * 0.5 - 400, 180)
	warn_box.size = Vector2(800, 100)
	zone_title.position = Vector2(0, vp.y * 0.22)
	zone_title.size = Vector2(vp.x, 60)
	zone_sub.position = Vector2(0, vp.y * 0.22 + 60)
	zone_sub.size = Vector2(vp.x, 30)
	toast_box.position = Vector2(vp.x * 0.5 - 190, vp.y - 330)
	popup_box.position = Vector2(vp.x * 0.5 - 220, 90)


# ============================================================================== Laufend
func _process(delta: float) -> void:
	var me = world.me
	if me == null:
		return
	player_frame.unit_id = Game.me_id
	target_frame.unit_id = world.target
	var te = world.ent(world.target)
	tot_frame.unit_id = te.target_id if te and te.target_id != 0 and te.target_id != world.target else 0
	# eigener Zauberbalken
	if me.cast != null:
		var c: Dictionary = me.cast
		var total := maxf(0.05, float(c.get("dur", 1.0)))
		var left = float(c.get("left", 0.0)) - (Game.now() - me.cast_start)
		var f := clampf(1.0 - left / total, 0.0, 1.0)
		if c.get("ch", false):
			f = 1.0 - f
		cast_bar.visible = left > -0.05
		cast_bar.color = Color("#40c040") if c.get("ch", false) else Color("#e8a020")
		cast_bar.set_values(f, 1.0, "%s   %.1f" % [str(c.get("name", "")), maxf(0.0, left)])
		cast_bar.snap()
	else:
		cast_bar.visible = false
	xp_bar.set_values(Game.xp, maxf(1, Game.xp_next), ("EP %d / %d" % [Game.xp, Game.xp_next]) if Game.level < 50 else "Höchststufe")
	# Tod
	if me.dead != _was_dead:
		_was_dead = me.dead
		if me.dead:
			_show_death()
		else:
			close_popup("death")
	_perf_t -= delta
	if _perf_t <= 0:
		_perf_t = 0.5
		perf_label.text = "%d FPS   %d ms" % [Engine.get_frames_per_second(), int(Net.ping_ms)]


func _notification(what: int) -> void:
	if what == NOTIFICATION_DRAG_BEGIN:
		_drag_data = get_viewport().gui_get_drag_data()
	elif what == NOTIFICATION_DRAG_END:
		var d = _drag_data
		_drag_data = null
		if d is Dictionary and not get_viewport().gui_is_drag_successful():
			if str(d.get("from", "")) == "bar":
				bars.remove_from(int(d.get("index", -1)))
			elif str(d.get("from", "")) == "bag" and d.get("item"):
				var slot := int(d.get("index", -1))
				var it := Content.item(str(d["item"]))
				confirm("destroy", "%s zerstören?" % it.get("name", "Gegenstand"), func(): Game.send({"t": "destroy", "slot": slot}))


# ============================================================================== Fenster
func window(id: String) -> Win:
	if windows.has(id):
		return windows[id]
	var w: Win = _make_window(id)
	if w == null:
		return null
	windows[id] = w
	win_layer.add_child(w)
	return w


func _make_window(id: String) -> Win:
	match id:
		"inventar": return InventoryWin.new(self)
		"charakter": return CharacterWin.new(self)
		"zauberbuch": return SpellbookWin.new(self)
		"talente": return TalentWin.new(self)
		"questlog": return QuestLogWin.new(self)
		"karte": return MapWin.new(self)
		"gilde": return GuildWin.new(self)
		"berufe": return ProfessionWin.new(self)
		"erfolge": return AchievementWin.new(self)
		"sammlung": return CollectionWin.new(self)
		"gruppensuche": return FinderWin.new(self)
		"soziales": return SocialWin.new(self)
		"markt": return MarketWin.new(self)
		"post": return MailWin.new(self)
		"haendler": return VendorWin.new(self)
		"gespraech": return GossipWin.new(self)
		"beute": return LootWin.new(self)
		"berufslehrer": return ProfTrainerWin.new(self)
		"handel": return TradeWin.new(self)
		"einstellungen": return SettingsWin.new(self)
		"menue": return GameMenuWin.new(self)
		"steine": return StonesWin.new(self)
		"dungeon": return DungeonWin.new(self)
		"inspektion": return InspectWin.new(self)
		"hilfe": return HelpWin.new(self)
	return null


func toggle_window(id: String) -> void:
	var w := window(id)
	if w:
		w.toggle()


func open_window(id: String) -> Win:
	var w := window(id)
	if w:
		w.open()
	return w


func close_window(id: String) -> void:
	if windows.has(id):
		windows[id].close_win()


func is_open(id: String) -> bool:
	return windows.has(id) and windows[id].visible


func close_top_window() -> bool:
	var kids := win_layer.get_children()
	for i in range(kids.size() - 1, -1, -1):
		var w = kids[i]
		if w is Win and w.visible:
			w.close_win()
			return true
	return false


func toggle_game_menu() -> void:
	toggle_window("menue")


func handle_key(ev: InputEventKey) -> void:
	if Settings.is_action(ev, "ui_umschalten"):
		ui_hidden = not ui_hidden
		for c in get_children():
			if c != overlay and c != win_layer and c != popup_box:
				c.visible = not ui_hidden
		return
	if Settings.is_action(ev, "chat"):
		chat.focus_input()
		return
	if Settings.is_action(ev, "chat_befehl"):
		chat.focus_input("/")
		return
	if Settings.is_action(ev, "screenshot"):
		_screenshot()
		return
	if bars.handle_key(ev):
		return
	for a in KEY_WINDOWS:
		if Settings.is_action(ev, a):
			toggle_window(KEY_WINDOWS[a])
			return


func _screenshot() -> void:
	var img := get_viewport().get_texture().get_image()
	var dir := OS.get_user_data_dir() + "/screenshots"
	DirAccess.make_dir_recursive_absolute(dir)
	var path := dir + "/eldornia_%s.png" % Time.get_datetime_string_from_system().replace(":", "-")
	img.save_png(path)
	chat.add_line("sys", "", "Bildschirmfoto gespeichert: " + path)


# ============================================================================== Schnittstelle für WorldView
func on_zone(data: Dictionary) -> void:
	minimap.set_zone(data)
	show_zone_text(str(data.get("name", Game.zone_name)), ("%s" % Game.zone_mode) if Game.zone_mode != "" else _zone_levels(data))
	if is_open("karte"):
		windows["karte"].refresh()
	close_window("beute")
	close_window("haendler")
	close_window("gespraech")


func _zone_levels(data: Dictionary) -> String:
	var lv = data.get("levels")
	if lv is Array and lv.size() >= 2:
		return "Stufe %d – %d" % [int(lv[0]), int(lv[1])]
	return ""


func on_me_update(_d: Dictionary) -> void:
	pass


func combat_text(ev: Dictionary, src, dst) -> void:
	overlay.add_combat(ev, src, dst)


func bubble(e, text: String) -> void:
	overlay.bubble(e, text)


func error_text(t: String) -> void:
	_flash_line(err_box, t, Color(1.0, 0.18, 0.12), 20, 2.5)
	Sfx.play("error", -10.0)


func info_text(t: String, col := Color(1.0, 0.85, 0.2)) -> void:
	_flash_line(err_box, t, col, 20, 3.0)


func raid_warning(t: String, col := Color(1.0, 0.35, 0.15)) -> void:
	_flash_line(warn_box, t, col, 30, 5.0, UiSkin.font_title)
	Sfx.play("warning", -4.0)


func _flash_line(box: VBoxContainer, t: String, col: Color, fs: int, life: float, font: Font = null) -> void:
	for c in box.get_children():
		if c is Label and c.text == t:
			c.queue_free()
	var l := UiSkin.label(t, fs, col, font if font else UiSkin.font_bold)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	l.add_theme_constant_override("outline_size", 5)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(l)
	while box.get_child_count() > 3:
		box.get_child(0).free()
	var tw := l.create_tween()
	tw.tween_interval(life)
	tw.tween_property(l, "modulate:a", 0.0, 0.8)
	tw.tween_callback(l.queue_free)


func show_zone_text(title: String, sub := "", col := Color("#ffd870")) -> void:
	zone_title.text = title
	zone_title.add_theme_color_override("font_color", col)
	zone_sub.text = sub
	for l in [zone_title, zone_sub]:
		var tw: Tween = l.create_tween()
		l.modulate.a = 0.0
		tw.tween_property(l, "modulate:a", 1.0, 0.6)
		tw.tween_interval(2.8)
		tw.tween_property(l, "modulate:a", 0.0, 1.4)


func toast(title: String, text: String, icon := "star-medal", col := Color("#ffd870")) -> void:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UiSkin.dark_box())
	p.custom_minimum_size = Vector2(380, 70)
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var h := UiSkin.hbox(10)
	p.add_child(h)
	var ic := TextureRect.new()
	ic.texture = Content.icon(icon, Color(0.5, 0.35, 0.12), 64)
	ic.custom_minimum_size = Vector2(52, 52)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	h.add_child(ic)
	var v := UiSkin.vbox(2)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	v.add_child(UiSkin.label(title, 18, col, UiSkin.font_title))
	var tl := UiSkin.label(text, 16, UiSkin.TEXT)
	tl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(tl)
	toast_box.add_child(p)
	while toast_box.get_child_count() > 3:
		toast_box.get_child(0).free()
	p.modulate.a = 0.0
	var tw := p.create_tween()
	tw.tween_property(p, "modulate:a", 1.0, 0.3)
	tw.tween_interval(5.0)
	tw.tween_property(p, "modulate:a", 0.0, 1.0)
	tw.tween_callback(p.queue_free)


# ============================================================================== Dialoge
## Zeigt einen Dialog oben in der Bildschirmmitte. buttons: [[Text, Callable], ...]
func popup(key: String, text: String, buttons: Array, timeout := 0.0) -> PanelContainer:
	close_popup(key)
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(440, 0)
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	var v := UiSkin.vbox(10)
	p.add_child(v)
	var r := UiSkin.rich("[center]%s[/center]" % text)
	r.custom_minimum_size.x = 400
	v.add_child(r)
	var h := UiSkin.hbox(12)
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(h)
	for b in buttons:
		var cb: Callable = b[1]
		var bt := UiSkin.button(str(b[0]), func():
			close_popup(key)
			if cb.is_valid():
				cb.call()
		, 110)
		h.add_child(bt)
	popup_box.add_child(p)
	popups[key] = p
	if timeout > 0:
		get_tree().create_timer(timeout).timeout.connect(func():
			if popups.get(key) == p:
				close_popup(key)
		)
	Sfx.play("popup", -8.0)
	return p


func close_popup(key: String) -> void:
	var p = popups.get(key)
	if p and is_instance_valid(p):
		p.queue_free()
	popups.erase(key)


func confirm(key: String, text: String, yes: Callable, yes_text := "Ja", no_text := "Nein") -> void:
	popup(key, text, [[yes_text, yes], [no_text, Callable()]])


## Dialog mit Eingabefeld (z. B. Stapel teilen, Gold einzahlen).
func ask_text(key: String, text: String, initial: String, cb: Callable) -> void:
	var p := popup(key, text, [])
	var v: VBoxContainer = p.get_child(0)
	var le := LineEdit.new()
	le.text = initial
	le.custom_minimum_size = Vector2(240, 34)
	le.select_all_on_focus = true
	v.add_child(le)
	v.move_child(le, 1)
	var h: HBoxContainer = v.get_child(2)
	var ok := func():
		var t := le.text
		close_popup(key)
		cb.call(t)
	le.text_submitted.connect(func(_t): ok.call())
	h.add_child(UiSkin.button("OK", ok, 100))
	h.add_child(UiSkin.button("Abbrechen", func(): close_popup(key), 100))
	le.grab_focus.call_deferred()


func _show_death() -> void:
	var in_arena := false
	if Game.zone_id.begins_with("arena"):
		in_arena = true
	if in_arena:
		popup("death", "[font_size=22][color=#ff6040]Ihr seid besiegt.[/color][/font_size]\nWartet auf das Ende des Kampfes.", [])
	else:
		popup("death", "[font_size=22][color=#ff6040]Ihr seid gestorben.[/color][/font_size]\nEure Ausrüstung verliert 10 % Haltbarkeit.",
			[["Geist freilassen", func(): Game.send({"t": "release"})]])


func _unit_menu(id: int) -> void:
	var e = world.ent(id)
	if e == null:
		return
	var pm := PopupMenu.new()
	pm.add_theme_font_size_override("font_size", 16)
	var acts: Array = []
	if e.is_me:
		if not Game.party.get("members", []).is_empty():
			pm.add_item("Gruppe verlassen")
			acts.append(func(): Game.send({"t": "party_leave"}))
		pm.add_item("Rolle: Tank")
		acts.append(func(): Game.send({"t": "role", "role": "tank"}))
		pm.add_item("Rolle: Heiler")
		acts.append(func(): Game.send({"t": "role", "role": "heiler"}))
		pm.add_item("Rolle: Schaden")
		acts.append(func(): Game.send({"t": "role", "role": "dps"}))
	elif e.kind == "player":
		pm.add_item("Flüstern")
		acts.append(func(): chat.start_whisper(e.name_text))
		pm.add_item("In Gruppe einladen")
		acts.append(func(): Game.send({"t": "invite", "name": e.name_text}))
		pm.add_item("Handeln")
		acts.append(func(): Game.send({"t": "trade_request", "id": e.id}))
		pm.add_item("Betrachten")
		acts.append(func(): Game.send({"t": "interact", "id": e.id}))
		pm.add_item("Zum Duell herausfordern")
		acts.append(func(): Game.send({"t": "duel", "id": e.id}))
		pm.add_item("Freund hinzufügen")
		acts.append(func(): Game.send({"t": "friend_add", "name": e.name_text}))
		pm.add_item("In Gilde einladen")
		acts.append(func(): Game.send({"t": "guild_invite", "name": e.name_text}))
		if _is_leader():
			pm.add_item("Aus Gruppe entfernen")
			acts.append(func(): Game.send({"t": "party_kick", "id": e.id}))
			pm.add_item("Zum Anführer machen")
			acts.append(func(): Game.send({"t": "party_lead", "id": e.id}))
		pm.add_item("Ignorieren")
		acts.append(func(): Game.send({"t": "friend_add", "name": e.name_text, "ignore": true}))
	else:
		return
	pm.id_pressed.connect(func(i): acts[i].call())
	pm.popup_hide.connect(pm.queue_free)
	add_child(pm)
	pm.position = Vector2i(get_global_mouse_position())
	pm.popup()


func _is_leader() -> bool:
	return int(Game.party.get("leader", 0) if Game.party.get("leader") != null else 0) == Game.me_id


# ============================================================================== Nachrichten
func _on_target_changed(_id: int) -> void:
	pass


func _on_state(what: String) -> void:
	if what in ["inventory", "stats"]:
		_refresh_money()


func _refresh_money() -> void:
	money_label.text = "[right]%s[/right]" % Content.money_bb(Game.copper)


func _on_system_text(text: String, kind: String) -> void:
	if kind == "err":
		error_text(text)
	chat.add_line(kind, "", text)


func _on_msg(t: String, m: Dictionary) -> void:
	match t:
		"gossip":
			var w: GossipWin = open_window("gespraech")
			w.show_gossip(m)
		"quest_detail":
			var w2: GossipWin = open_window("gespraech")
			w2.show_quest(m)
		"quest_accepted":
			Sfx.play("quest_accept", -6.0)
			if is_open("gespraech"):
				windows["gespraech"].after_quest_action()
		"quest_done":
			Sfx.play("quest_done", -4.0)
			info_text("%s abgeschlossen." % str(m.get("title", "")), Color(1, 0.85, 0.2))
			if is_open("gespraech"):
				windows["gespraech"].after_quest_action()
		"qprog":
			info_text(str(m.get("text", "")), Color(1, 0.85, 0.2) if not m.get("done", false) else Color(0.4, 1.0, 0.4))
		"vendor":
			var vw: VendorWin = open_window("haendler")
			vw.show_vendor(m)
			open_window("inventar")
		"loot":
			var lw: LootWin = window("beute")
			lw.show_loot(m)
			if not lw.visible:
				lw.open()
				lw.position = (get_global_mouse_position() + Vector2(20, -40)).clamp(Vector2.ZERO, get_viewport_rect().size - Vector2(280, 300))
		"loot_close":
			close_window("beute")
		"trainer":
			if m.get("mine", false):
				var tw2: TalentWin = open_window("talente")
				tw2.trainer_npc = int(m.get("npc", 0))
				tw2.refresh()
				open_window("zauberbuch")
			else:
				error_text("%s unterrichtet Eure Klasse nicht." % str(m.get("name", "")))
		"prof_trainer":
			var pw: ProfTrainerWin = open_window("berufslehrer")
			pw.show_trainer(m)
		"open":
			var wid := str(m.get("w", ""))
			if OPEN_MAP.has(wid):
				var ow := open_window(OPEN_MAP[wid])
				if ow.has_method("open_mode"):
					ow.open_mode(wid, m)
		"mail":
			var mw: MailWin = open_window("post")
			mw.show_mail(m)
		"trade_request":
			popup("trade", "%s möchte mit Euch handeln." % str(m.get("from", "")),
				[["Annehmen", func(): Game.send({"t": "trade_answer", "ok": true})], ["Ablehnen", func(): Game.send({"t": "trade_answer", "ok": false})]], 30.0)
		"trade":
			var trw: TradeWin = open_window("handel")
			trw.show_trade(m)
			open_window("inventar")
		"trade_done":
			if windows.has("handel"):
				windows["handel"].data = {}
			close_window("handel")
			info_text("Handel abgeschlossen.", Color(0.4, 1.0, 0.4))
		"trade_cancel":
			if windows.has("handel"):
				windows["handel"].visible = false
			error_text(str(m.get("reason", "Handel abgebrochen.")))
		"party_invite":
			popup("party", "%s lädt Euch in eine Gruppe ein." % str(m.get("from", "")),
				[["Annehmen", func(): Game.send({"t": "party_accept"})], ["Ablehnen", func(): Game.send({"t": "party_decline"})]], 60.0)
		"guild_invite":
			popup("guild", "%s lädt Euch in die Gilde <%s> ein." % [str(m.get("from", "")), str(m.get("guild", ""))],
				[["Beitreten", func(): Game.send({"t": "guild_accept"})], ["Ablehnen", func(): Game.send({"t": "guild_decline"})]], 60.0)
		"duel_request":
			popup("duel", "%s fordert Euch zum Duell heraus." % str(m.get("from", "")),
				[["Annehmen", func(): Game.send({"t": "duel_answer", "ok": true})], ["Ablehnen", func(): Game.send({"t": "duel_answer", "ok": false})]], 30.0)
		"duel_start":
			_countdown(int(m.get("in", 3)), "Duell!")
		"duel_end":
			raid_warning(str(m.get("text", "Das Duell ist vorbei.")), Color(1, 0.85, 0.3))
		"queue":
			if str(m.get("state")) == "found":
				raid_warning("Gruppe gefunden: %s" % str(m.get("name", "")), Color(0.5, 0.85, 1.0))
				Sfx.play("ready", -2.0)
			if is_open("gruppensuche"):
				windows["gruppensuche"].refresh_queue()
		"arena_queue":
			if str(m.get("state")) == "found":
				raid_warning("Arenakampf gefunden!", Color(0.5, 0.85, 1.0))
			if windows.has("gruppensuche"):
				windows["gruppensuche"].on_arena_queue(m)
		"arena_start":
			_countdown(int(m.get("in", 10)), "Kämpft!")
		"arena_end":
			var won: bool = m.get("won", false)
			show_zone_text("Sieg!" if won else "Niederlage", "Wertung %d (%s%d)" % [int(m.get("rating", 1500)), "+" if int(m.get("delta", 0)) >= 0 else "", int(m.get("delta", 0))],
				Color("#ffd870") if won else Color("#ff6050"))
		"stones":
			var sw: StonesWin = open_window("steine")
			sw.show_stones(m)
		"dungeon_select":
			var dw: DungeonWin = open_window("dungeon")
			dw.show_select(m)
		"inspect":
			var iw: InspectWin = open_window("inspektion")
			iw.show_inspect(m)
		"who":
			var so: SocialWin = open_window("soziales")
			so.show_who(m)
		"map":
			if windows.has("karte"):
				windows["karte"].on_map(m)
		"finder":
			if windows.has("gruppensuche"):
				windows["gruppensuche"].on_finder(m)
		"market", "market_mine", "market_price":
			if windows.has("markt"):
				windows["markt"].on_msg(t, m)
		"toast":
			toast(str(m.get("title", "")), str(m.get("text", "")), str(m.get("icon", "")) if m.get("icon") else _toast_icon(str(m.get("kind", ""))))
		"achievement":
			toast("Erfolg errungen!", "%s  (%d Punkte)" % [str(m.get("name", "")), int(m.get("points", 0))], str(m.get("icon", "trophy")))
			Sfx.play("achievement", -2.0)
		"levelup":
			show_zone_text("Stufe %d" % int(m.get("lvl", Game.level)), "Ihr seid aufgestiegen!", Color("#ffe080"))
			Sfx.play("levelup", 0.0)
			var news: Array = m.get("new", [])
			for n in news:
				chat.add_line("sys", "", "Neue Fähigkeit erlernt: %s" % str(n))
			if int(m.get("lvl", 0)) == 10:
				toast("Talente", "Ihr könnt jetzt Talentpunkte verteilen (Taste N).", "skills")
		"discover":
			show_zone_text(str(m.get("name", "")), "Entdeckt%s" % ((" – %d EP" % int(m.get("xp", 0))) if int(m.get("xp", 0)) > 0 else ""), Color("#f0e0b0"))
			Sfx.play("discover", -6.0)
		"subzone":
			var sub := str(m.get("name", ""))
			if sub != "":
				_flash_line(warn_box, sub + (" (PvP-Gebiet)" if m.get("pvp", false) else ""), Color("#f0e0b0") if not m.get("pvp", false) else Color("#ff6050"), 24, 2.0, UiSkin.font_title)
		"zone":
			close_popup("death")
		"phase":
			raid_warning("%s – %s" % [str(m.get("boss", "")), str(m.get("name", "Phase %d" % int(m.get("phase", 2))))])
		"xp":
			if int(m.get("a", 0)) > 0:
				var src = m.get("src")
				chat.add_line("xp", "", ("%s stirbt, Ihr erhaltet %d Erfahrung." % [src, int(m["a"])]) if src else ("Ihr erhaltet %d Erfahrung." % int(m["a"])))
		"died":
			pass
		"revived":
			close_popup("death")
		"chat":
			if str(m.get("ch")) == "yell" and m.get("fid"):
				pass


func _toast_icon(kind: String) -> String:
	return {"rep": "laurels", "title": "scroll-quill", "collection": "horse-head", "stone": "stone-tablet", "loot": "open-treasure-chest"}.get(kind, "star-medal")


func _countdown(n: int, final_text: String) -> void:
	for i in range(n, 0, -1):
		get_tree().create_timer(float(n - i)).timeout.connect(func():
			_flash_line(warn_box, str(i), Color(1, 0.85, 0.2), 48, 0.6, UiSkin.font_deco)
			Sfx.play("click", -2.0)
		)
	get_tree().create_timer(float(n)).timeout.connect(func():
		_flash_line(warn_box, final_text, Color(1, 0.4, 0.2), 48, 1.2, UiSkin.font_deco)
		Sfx.play("warning", 0.0)
	)
