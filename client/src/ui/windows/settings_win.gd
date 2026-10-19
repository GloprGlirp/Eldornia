class_name SettingsWin
extends Win
## Einstellungen: Grafik, Audio, Steuerung/Anzeige und frei belegbare Tasten (GDD 4: konfigurierbare Steuerung).

var hud
var tabs: TabContainer
var key_list: VBoxContainer
var _rebind := ""
var _rebind_btn: Button


func _init(p_hud) -> void:
	super("Einstellungen", "einstellungen", Vector2(620, 560))
	hud = p_hud


func _ready() -> void:
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(600, 470)
	body.add_child(tabs)
	var g := _page("Grafik")
	_option(g, "Grafikqualität", ["Niedrig", "Mittel", "Hoch", "Ultra"], Settings.quality, func(i): Settings.quality = i)
	_slider(g, "Sichtweite", 0.0, 2.0, Settings.view_distance, func(v): Settings.view_distance = v)
	_check(g, "Schatten", Settings.shadows, func(v): Settings.shadows = v)
	_check(g, "Umgebungsverdeckung (SSAO)", Settings.ssao, func(v): Settings.ssao = v)
	_check(g, "Gras und Bodenbewuchs", Settings.grass, func(v): Settings.grass = v)
	_check(g, "Vertikale Synchronisation", Settings.vsync, func(v): Settings.vsync = v)
	if not OS.has_feature("web"):
		_check(g, "Vollbild", Settings.fullscreen, func(v): Settings.fullscreen = v)
	_slider(g, "Oberflächengröße", 0.75, 1.5, Settings.ui_scale, func(v): Settings.ui_scale = v)
	var a := _page("Audio")
	_slider(a, "Gesamtlautstärke", 0.0, 1.0, Settings.vol_master, func(v): Settings.vol_master = v)
	_slider(a, "Musik", 0.0, 1.0, Settings.vol_music, func(v):
		Settings.vol_music = v
		Sfx.set_music_volume()
	)
	_slider(a, "Effekte", 0.0, 1.0, Settings.vol_sfx, func(v): Settings.vol_sfx = v)
	var c := _page("Steuerung")
	_slider(c, "Mausempfindlichkeit", 0.2, 3.0, Settings.mouse_sens, func(v): Settings.mouse_sens = v)
	_check(c, "Maus-Y invertieren", Settings.invert_y, func(v): Settings.invert_y = v)
	_check(c, "Zielhilfe (automatisch nächsten Gegner anvisieren)", Settings.target_assist, func(v): Settings.target_assist = v)
	_check(c, "Schwebender Kampftext", Settings.show_fct, func(v): Settings.show_fct = v)
	_check(c, "Namensplaketten", Settings.show_nameplates, func(v): Settings.show_nameplates = v)
	_check(c, "Freundliche Namensplaketten", Settings.show_friendly_plates, func(v): Settings.show_friendly_plates = v)
	var ksc := ScrollContainer.new()
	ksc.name = "Tastenbelegung"
	tabs.add_child(ksc)
	key_list = UiSkin.vbox(3)
	key_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ksc.add_child(key_list)
	_keys()
	var bh := UiSkin.hbox(8)
	bh.alignment = BoxContainer.ALIGNMENT_END
	body.add_child(bh)
	bh.add_child(UiSkin.button("Standard", func():
		Settings.keys = Settings.DEFAULT_KEYS.duplicate(true)
		_keys()
	))
	bh.add_child(UiSkin.button("Übernehmen", _apply, 140))


func _on_open() -> void:
	center()


func _on_close() -> void:
	_apply()


func _apply() -> void:
	Settings.apply()
	Settings.save_settings()
	if hud.world:
		hud.world._apply_graphics()
	for s in hud.bars.slots:
		if s.index < 12:
			s.keybind = Settings.short_key_label(ActionBars.KEYS1[s.index])
		elif s.index < 18:
			s.keybind = Settings.short_key_label(ActionBars.KEYS2[s.index - 12])
		s.queue_redraw()


func _page(n: String) -> VBoxContainer:
	var v := UiSkin.vbox(10)
	v.name = n
	tabs.add_child(v)
	return v


func _row(parent: Control, label: String) -> HBoxContainer:
	var h := UiSkin.hbox(10)
	var l := UiSkin.label(label, 16)
	l.custom_minimum_size.x = 260
	h.add_child(l)
	parent.add_child(h)
	return h


func _option(parent: Control, label: String, items: Array, cur: int, cb: Callable) -> void:
	var h := _row(parent, label)
	var o := OptionButton.new()
	for it in items:
		o.add_item(it)
	o.selected = cur
	o.item_selected.connect(func(i): cb.call(i))
	h.add_child(o)


func _slider(parent: Control, label: String, mn: float, mx: float, cur: float, cb: Callable) -> void:
	var h := _row(parent, label)
	var s := HSlider.new()
	s.min_value = mn
	s.max_value = mx
	s.step = 0.05
	s.value = cur
	s.custom_minimum_size = Vector2(220, 24)
	var vl := UiSkin.label("%d %%" % int(cur * 100), 14, UiSkin.TEXT_DIM)
	s.value_changed.connect(func(v):
		cb.call(v)
		vl.text = "%d %%" % int(v * 100)
	)
	h.add_child(s)
	h.add_child(vl)


func _check(parent: Control, label: String, cur: bool, cb: Callable) -> void:
	var c := CheckBox.new()
	c.text = label
	c.button_pressed = cur
	c.add_theme_font_size_override("font_size", 16)
	c.toggled.connect(func(v): cb.call(v))
	parent.add_child(c)


func _keys() -> void:
	for c in key_list.get_children():
		c.queue_free()
	key_list.add_child(UiSkin.label("Klickt eine Belegung an und drückt die neue Taste (Esc bricht ab, Entf löscht).", 14, UiSkin.TEXT_DIM))
	var names: Dictionary = Settings.ACTION_NAMES.duplicate()
	for i in 12:
		names["aktion_%d" % (i + 1)] = "Aktionsleiste 1 – Platz %d" % (i + 1)
	for i in 6:
		names["leiste2_%d" % (i + 1)] = "Aktionsleiste 2 – Platz %d" % (i + 1)
	for k in Settings.DEFAULT_KEYS:
		var h := _row(key_list, str(names.get(k, k)))
		var codes: Array = Settings.keys.get(k, [])
		var txt := " / ".join(codes.map(func(c): return OS.get_keycode_string(int(c)))) if not codes.is_empty() else "—"
		var b := UiSkin.button(txt, Callable(), 200)
		var action: String = k
		b.pressed.connect(func():
			_rebind = action
			_rebind_btn = b
			b.text = "Taste drücken …"
		)
		h.add_child(b)


func _input(ev: InputEvent) -> void:
	if _rebind == "" or not visible:
		return
	if ev is InputEventKey and ev.pressed and not ev.echo:
		get_viewport().set_input_as_handled()
		if ev.keycode == KEY_ESCAPE:
			_rebind = ""
			_keys()
			return
		if ev.keycode == KEY_DELETE:
			Settings.keys[_rebind] = []
		else:
			var code: int = ev.keycode if ev.keycode != 0 else ev.physical_keycode
			for k in Settings.keys:
				var arr: Array = Settings.keys[k]
				if code in arr and k != _rebind:
					arr.erase(code)
			Settings.keys[_rebind] = [code]
		_rebind = ""
		_keys()
