class_name Minimap
extends Control
## Runde Minikarte (GDD 11) mit Spielerpfeil, Questzielen, NPCs, Gruppenmitgliedern, Gegnern und Rohstoffen.

var world
var map: Dictionary = {}
var zoom := 1.0              # Meter pro Pixel
var radius := 92.0
var zone_label: Label
var coord_label: Label
var _t := 0.0


func _init(p_world) -> void:
	world = p_world
	custom_minimum_size = Vector2(220, 250)
	mouse_filter = Control.MOUSE_FILTER_PASS


func _ready() -> void:
	zone_label = UiSkin.label("", 15, UiSkin.GOLD, UiSkin.font_title)
	zone_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	zone_label.position = Vector2(0, 0)
	zone_label.size = Vector2(220, 22)
	zone_label.clip_text = true
	add_child(zone_label)
	coord_label = UiSkin.label("", 12, Color(0.9, 0.9, 0.85))
	coord_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	coord_label.position = Vector2(0, 228)
	coord_label.size = Vector2(220, 18)
	add_child(coord_label)
	var plus := Button.new()
	plus.text = "+"
	plus.position = Vector2(190, 176)
	plus.custom_minimum_size = Vector2(26, 26)
	plus.pressed.connect(func(): zoom = clampf(zoom * 0.75, 0.25, 3.0))
	add_child(plus)
	var minus := Button.new()
	minus.text = "−"
	minus.position = Vector2(190, 204)
	minus.custom_minimum_size = Vector2(26, 26)
	minus.pressed.connect(func(): zoom = clampf(zoom / 0.75, 0.25, 3.0))
	add_child(minus)


func set_zone(z: Dictionary) -> void:
	map = MapRender.texture(z, world.hf)
	zoom = 1.0 if world.hf else 0.4


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed:
		if ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom = clampf(zoom * 0.85, 0.25, 3.0)
			accept_event()
		elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom = clampf(zoom / 0.85, 0.25, 3.0)
			accept_event()
		elif ev.button_index == MOUSE_BUTTON_LEFT and world.hud:
			world.hud.toggle_window("karte")


func _process(delta: float) -> void:
	_t += delta
	if _t > 0.08:
		_t = 0.0
		queue_redraw()
		var me = world.me
		if me:
			var sub := Game.subzone if Game.subzone != "" else Game.zone_name
			zone_label.text = sub
			coord_label.text = "%d, %d    %s" % [int(me.global_position.x), int(me.global_position.z), Time.get_time_string_from_system().substr(0, 5)]


func _w2m(c: Vector2, me_pos: Vector3, x: float, z: float) -> Vector2:
	return c + Vector2(x - me_pos.x, z - me_pos.z) / zoom


func _draw() -> void:
	var me = world.me
	if me == null or map.is_empty():
		return
	var c := Vector2(110, 120)
	var mp: Vector3 = me.global_position
	# Kartenausschnitt (kreisförmig per Polygon mit UV)
	var tex: Texture2D = map["tex"]
	var size: float = map["size"]
	var origin: Vector2 = map["origin"]
	var pts := PackedVector2Array()
	var uvs := PackedVector2Array()
	var cols := PackedColorArray()
	for i in 48:
		var a := TAU * i / 48.0
		var p := c + Vector2(cos(a), sin(a)) * radius
		pts.append(p)
		var wx := mp.x + (p.x - c.x) * zoom
		var wz := mp.z + (p.y - c.y) * zoom
		uvs.append(Vector2((wx - origin.x) / size, (wz - origin.y) / size))
		cols.append(Color.WHITE)
	draw_circle(c, radius + 1, Color(0.05, 0.05, 0.08))
	draw_polygon(pts, cols, uvs, tex)
	# Questziele
	for q in Game.quests:
		if q.get("done", false):
			if q.get("ender_pos") is Array:
				var ep := _w2m(c, mp, float(q["ender_pos"][0]), float(q["ender_pos"][1]))
				_marker(c, ep, "?", Color(1, 0.85, 0.1))
			continue
		for h in q.get("targets", []):
			var hp := _w2m(c, mp, float(h[0]), float(h[1]))
			var hr := maxf(4.0, float(h[2]) / zoom)
			if hp.distance_to(c) - hr < radius:
				draw_circle(hp, minf(hr, radius), Color(1, 0.85, 0.2, 0.18))
				draw_arc(hp, minf(hr, radius), 0, TAU, 32, Color(1, 0.85, 0.2, 0.5), 1.0)
	# Einheiten
	for e in world.entities.values():
		if not is_instance_valid(e):
			continue
		var ep2 := _w2m(c, mp, e.global_position.x, e.global_position.z)
		if ep2.distance_to(c) > radius - 3:
			if e.kind == "npc" and e.quest_mark in ["!", "?", "!b", "?b"]:
				var dirv := (ep2 - c).normalized()
				_marker(c, c + dirv * (radius - 6), e.quest_mark.substr(0, 1), Color(1, 0.85, 0.1) if not e.quest_mark.ends_with("b") else Color(0.4, 0.7, 1.0), 12)
			continue
		match e.kind:
			"npc":
				if e.quest_mark in ["!", "?", "!b", "?b"]:
					_marker(c, ep2, e.quest_mark.substr(0, 1), Color(1, 0.85, 0.1) if not e.quest_mark.ends_with("b") else Color(0.4, 0.7, 1.0))
				else:
					draw_circle(ep2, 2.5, Color(1.0, 0.95, 0.3))
			"mob":
				if not e.dead and e.is_attackable() and not e.look.get("critter", false):
					draw_circle(ep2, 2.2 if not e.look.get("elite", false) else 3.2, Color(0.95, 0.15, 0.1) if e.look.get("aggro", false) else Color(0.95, 0.85, 0.2))
			"player":
				var in_party: bool = e.fl.get("pt", false)
				draw_circle(ep2, 3.0, Color(0.3, 0.6, 1.0) if in_party else Color(0.9, 0.9, 0.9))
			"obj":
				if e.fl.get("u", false):
					var ob := str(e.info.get("obj", ""))
					var oc := Color(0.9, 0.9, 0.9)
					if ob == "node":
						oc = Color(1.0, 0.6, 0.2) if str(e.info.get("model", "")).begins_with("ore") else Color(0.4, 1.0, 0.4)
					elif ob == "quest":
						oc = Color(1.0, 0.85, 0.2)
					elif ob == "stone":
						oc = Color(0.5, 0.8, 1.0)
					draw_rect(Rect2(ep2 - Vector2(2.5, 2.5), Vector2(5, 5)), oc)
	# Portale
	for p in world.zone.get("portals", []):
		var pp := _w2m(c, mp, float(p["x"]), float(p["z"]))
		if pp.distance_to(c) < radius:
			draw_circle(pp, 4.0, Color(0.7, 0.4, 1.0))
	# Rahmen
	draw_arc(c, radius + 2, 0, TAU, 64, Color("#2a1a0a"), 5.0)
	draw_arc(c, radius + 5, 0, TAU, 64, Color("#e8c374"), 3.0)
	draw_arc(c, radius + 7.5, 0, TAU, 64, Color("#5a3a14"), 2.0)
	var f := UiSkin.font_title
	draw_string_outline(f, c + Vector2(-6, -radius - 2), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, 4, Color.BLACK)
	draw_string(f, c + Vector2(-6, -radius - 2), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(1, 0.9, 0.6))
	# Spielerpfeil
	var yaw: float = me.rotation.y
	var fwd := Vector2(-sin(yaw), -cos(yaw))
	var right := Vector2(fwd.y, -fwd.x)
	var tri := PackedVector2Array([c + fwd * 9, c - fwd * 6 + right * 6, c - fwd * 3, c - fwd * 6 - right * 6])
	draw_colored_polygon(tri, Color(1, 0.9, 0.3))
	draw_polyline(tri + PackedVector2Array([tri[0]]), Color(0.2, 0.1, 0.0), 1.5)
	# Post- / Gruppensuche-Symbole
	if Game.mail_unread > 0:
		draw_string_outline(f, Vector2(18, 210), "✉", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, 4, Color.BLACK)
		draw_string(f, Vector2(18, 210), "✉", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(1, 0.95, 0.7))
	if Game.queue_state != null:
		var a2 := 0.5 + 0.5 * sin(Game.now() * 4.0)
		draw_string_outline(f, Vector2(14, 48), "⚔", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, 4, Color.BLACK)
		draw_string(f, Vector2(14, 48), "⚔", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(0.5, 0.8, 1.0, 0.5 + a2 * 0.5))


func _marker(_c: Vector2, p: Vector2, ch: String, col: Color, fs := 16) -> void:
	var f := UiSkin.font_deco
	draw_string_outline(f, p + Vector2(-4, 6), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 4, Color(0.1, 0.05, 0))
	draw_string(f, p + Vector2(-4, 6), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, col)
