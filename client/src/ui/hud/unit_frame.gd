class_name UnitFrame
extends Control
## Einheitenrahmen (Spieler, Ziel, Ziel des Ziels, Gruppenmitglied): Porträt, Name, Stufe, Balken, Auren, Zauberbalken.

signal clicked(button: int)

var world
var unit_id := 0
var compact := false
var is_player_frame := false
var portrait: TextureRect
var name_l: Label
var level_l: Label
var hp_bar: StatBar
var pw_bar: StatBar
var cast_bar: StatBar
var aura_box: HFlowContainer
var combo_box: HBoxContainer
var _elite := ""
var _last_auras := ""
var _last_portrait := ""


func _init(p_world, p_compact := false) -> void:
	world = p_world
	compact = p_compact
	custom_minimum_size = Vector2(240 if not compact else 160, 70 if not compact else 44)
	mouse_filter = Control.MOUSE_FILTER_STOP


func _ready() -> void:
	var bg := Panel.new()
	bg.add_theme_stylebox_override("panel", UiSkin.dark_box())
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var ps := 56 if not compact else 34
	portrait = TextureRect.new()
	portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	portrait.position = Vector2(6, 7)
	portrait.size = Vector2(ps, ps)
	portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(portrait)
	var x0 := ps + 12
	var w := custom_minimum_size.x - x0 - 8
	name_l = UiSkin.label("", 15 if not compact else 13, Color.WHITE, UiSkin.font_bold)
	name_l.position = Vector2(x0, 4)
	name_l.size = Vector2(w - 26, 20)
	name_l.clip_text = true
	name_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(name_l)
	level_l = UiSkin.label("", 14, Color(1, 0.85, 0.2), UiSkin.font_bold)
	level_l.position = Vector2(x0 + w - 26, 4)
	level_l.size = Vector2(28, 20)
	level_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	level_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(level_l)
	hp_bar = StatBar.new(Color("#1fa81f"), 18 if not compact else 12)
	hp_bar.position = Vector2(x0, 26 if not compact else 20)
	hp_bar.size = Vector2(w, 18 if not compact else 11)
	hp_bar.text_size = 13 if not compact else 10
	add_child(hp_bar)
	pw_bar = StatBar.new(Color("#2f6cff"), 12 if not compact else 7)
	pw_bar.position = Vector2(x0, 46 if not compact else 32)
	pw_bar.size = Vector2(w, 12 if not compact else 6)
	pw_bar.text_size = 11
	pw_bar.show_text = not compact
	add_child(pw_bar)
	if not compact:
		cast_bar = StatBar.new(Color("#e8a020"), 14)
		cast_bar.position = Vector2(x0, 72)
		cast_bar.size = Vector2(w, 14)
		cast_bar.visible = false
		cast_bar.spark = true
		add_child(cast_bar)
		aura_box = HFlowContainer.new()
		aura_box.position = Vector2(4, 90)
		aura_box.size = Vector2(custom_minimum_size.x, 60)
		aura_box.add_theme_constant_override("h_separation", 2)
		aura_box.add_theme_constant_override("v_separation", 2)
		aura_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(aura_box)
		combo_box = UiSkin.hbox(3)
		combo_box.position = Vector2(x0, 60)
		add_child(combo_box)


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed:
		clicked.emit(ev.button_index)
		accept_event()


func _process(_d: float) -> void:
	var e = world.ent(unit_id) if world and unit_id != 0 else null
	if e == null and not is_player_frame:
		visible = false
		return
	visible = true
	if e == null:
		return
	var nm: String = e.name_text
	name_l.text = nm
	var col: Color = e.reaction_color()
	if e.kind == "player":
		col = Content.class_color(str(e.info.get("cls", Game.me_cls if e.is_me else ""))) if not e.is_enemy() else col
	name_l.add_theme_color_override("font_color", col.lightened(0.15))
	var lvl := e.level if not e.is_me else Game.level
	level_l.text = "☠" if e.look.get("boss", false) else str(lvl)
	level_l.add_theme_color_override("font_color", HudOverlay._level_color(lvl))
	var hp: int = e.hp
	var mhp: int = e.mhp
	if e.is_me:
		hp = int(Game.stats.get("_hp", e.hp))
	hp_bar.color = Color("#1fa81f") if e.kind != "mob" or not e.is_enemy() else (Color("#c41f1f") if e.look.get("aggro", false) else Color("#c8b41f"))
	if e.kind == "mob" and e.fl.get("tap", false):
		hp_bar.color = Color("#7a7a7a")
	if e.dead:
		hp_bar.set_values(0, 1, "Tot")
	else:
		var pct := int(round(100.0 * hp / maxf(1, mhp)))
		hp_bar.set_values(hp, mhp, ("%d / %d" % [hp, mhp]) if (e.is_me or e.kind == "player" or compact) else ("%d %%" % pct))
	var pt: String = e.pt if e.pt != "" else (Game.power_type if e.is_me else "")
	if e.mpw > 0 and pt != "":
		pw_bar.visible = true
		pw_bar.color = Content.power_color(pt)
		pw_bar.set_values(e.pw, e.mpw, "%d / %d" % [e.pw, e.mpw])
	else:
		pw_bar.visible = false
	var key := str(e.info.get("cls", "")) + "|" + str(e.info.get("model", "")) + "|" + str(e.kind)
	if key != _last_portrait:
		_last_portrait = key
		portrait.texture = _portrait_for(e)
	_elite = "boss" if e.look.get("boss", false) else ("rare" if e.look.get("rare", false) else ("elite" if e.look.get("elite", false) else ""))
	queue_redraw()
	if cast_bar:
		if e.cast != null:
			var c: Dictionary = e.cast
			var total := maxf(0.05, float(c.get("dur", 1.0)))
			var left := float(c.get("left", 0.0)) - (Game.now() - e.cast_start)
			var f := clampf(1.0 - left / total, 0.0, 1.0)
			if c.get("ch", false):
				f = 1.0 - f
			cast_bar.visible = left > -0.1
			cast_bar.color = Color("#8a8a8a") if c.get("ni", false) else (Color("#40c040") if c.get("ch", false) else Color("#e8a020"))
			cast_bar.set_values(f, 1.0, str(c.get("name", "")))
			cast_bar.snap()
		else:
			cast_bar.visible = false
	if aura_box:
		var sig := str(e.auras.size()) + str(e.auras.map(func(a): return str(a[0]) + str(a[6]) if a is Array else ""))
		if sig != _last_auras:
			_last_auras = sig
			_build_auras(e)
	if combo_box:
		var n := Game.combo if Game.combo_target == unit_id and unit_id != 0 and not is_player_frame else 0
		while combo_box.get_child_count() < 5:
			var cr := ColorRect.new()
			cr.custom_minimum_size = Vector2(10, 10)
			combo_box.add_child(cr)
		for i in 5:
			combo_box.get_child(i).color = Color(1, 0.85, 0.2) if i < n else Color(0, 0, 0, 0.0)


func _portrait_for(e) -> Texture2D:
	if e.kind == "player":
		var c := Content.cls(str(e.info.get("cls", Game.me_cls if e.is_me else "")))
		return Content.icon(str(c.get("icon", "person")), Content.class_color(str(e.info.get("cls", Game.me_cls))).darkened(0.55), 64)
	var m := str(e.info.get("model", ""))
	var icon := {"wolf": "wolf-head", "boar": "boar", "bear": "bear-head", "spider": "spider-alt", "dragon": "dragon-head",
		"drake": "dragon-head", "golem": "golem-head", "treant": "oak", "ghost": "ghost", "chicken": "chicken", "rabbit": "rabbit",
		"fox": "fox-head", "dummy": "scarecrow"}.get(m, "")
	if icon == "":
		var kind := str(e.look.get("kind", "human"))
		icon = {"kobold": "goblin-head", "skeleton": "skull", "dwarf": "dwarf-face", "demon": "devil-mask", "giant": "troll"}.get(kind, "person")
	var bg := Color(0.35, 0.12, 0.1) if e.is_enemy() else Color(0.15, 0.3, 0.15)
	return Content.icon(icon, bg, 64)


func _build_auras(e) -> void:
	for c in aura_box.get_children():
		c.queue_free()
	var shown := 0
	var sorted: Array = e.auras.duplicate()
	sorted.sort_custom(func(a, b): return int(a[5]) > int(b[5]))
	for a in sorted:
		if not (a is Array) or shown >= 16:
			continue
		var s := AuraIcon.new(a, e.is_me)
		aura_box.add_child(s)
		shown += 1


func _draw() -> void:
	if _elite != "":
		var col := Color(1.0, 0.82, 0.3) if _elite != "rare" else Color(0.85, 0.85, 0.95)
		if _elite == "boss":
			col = Color(1.0, 0.45, 0.2)
		var p := Vector2(6 + 28, 7 + 28)
		for i in 3:
			draw_arc(p, 31 + i * 2, PI * 0.7, PI * 2.3, 24, Color(col, 0.9 - i * 0.25), 2.0)
		var pts := PackedVector2Array([p + Vector2(-34, -10), p + Vector2(-46, -26), p + Vector2(-30, -22), p + Vector2(-26, -36), p + Vector2(-18, -28)])
		draw_polyline(pts, col, 2.0)
