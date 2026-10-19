class_name MapWin
extends Win
## Weltkarte (GDD 11): gemalte Zonenkarte mit Spieler, Gruppe, NPCs (Dienste/Quests), Questgebieten, Portalen,
## Teleportsteinen und entdeckten Gebieten sowie eine Übersicht über ganz Eldornia.

var hud
var tabs: TabContainer
var canvas: _ZoneMap
var world_canvas: _WorldMap
var data: Dictionary = {}


func _init(p_hud) -> void:
	super("Weltkarte", "karte", Vector2(700, 720))
	hud = p_hud


func _ready() -> void:
	tabs = TabContainer.new()
	body.add_child(tabs)
	canvas = _ZoneMap.new(self)
	canvas.name = "Zone"
	tabs.add_child(canvas)
	world_canvas = _WorldMap.new(self)
	world_canvas.name = "Eldornia"
	tabs.add_child(world_canvas)


func _on_open() -> void:
	center()
	refresh()


func refresh() -> void:
	Game.send({"t": "get", "w": "map"})
	title_label.text = Game.zone_name
	canvas.queue_redraw()


func on_map(m: Dictionary) -> void:
	data = m
	canvas.queue_redraw()
	world_canvas.queue_redraw()


class _ZoneMap extends Control:
	var win
	var hover_text := ""
	var _t := 0.0

	func _init(p_win) -> void:
		win = p_win
		custom_minimum_size = Vector2(660, 640)
		mouse_filter = Control.MOUSE_FILTER_STOP

	func _process(d: float) -> void:
		_t += d
		if _t > 0.25 and is_visible_in_tree():
			_t = 0.0
			queue_redraw()

	func _rect() -> Rect2:
		var s := minf(size.x, size.y)
		return Rect2(Vector2((size.x - s) * 0.5, 0), Vector2(s, s))

	func _w2m(x: float, z: float) -> Vector2:
		var mp: Dictionary = win.hud.minimap.map
		if mp.is_empty():
			return Vector2.ZERO
		var r := _rect()
		var o: Vector2 = mp["origin"]
		var sz: float = mp["size"]
		return r.position + Vector2((x - o.x) / sz, (z - o.y) / sz) * r.size.x

	func _m2w(p: Vector2) -> Vector2:
		var mp: Dictionary = win.hud.minimap.map
		var r := _rect()
		var o: Vector2 = mp["origin"]
		var sz: float = mp["size"]
		return o + (p - r.position) / r.size.x * sz

	func _gui_input(ev: InputEvent) -> void:
		if ev is InputEventMouseMotion:
			hover_text = ""
			for n in win.data.get("npcs", []):
				if _w2m(float(n["x"]), float(n["z"])).distance_to(ev.position) < 8:
					hover_text = str(n["name"]) + ((" <%s>" % n["title"]) if n.get("title") else "")
			for s in win.hud.world.zone.get("stones", []):
				if _w2m(float(s["pos"][0]), float(s["pos"][1])).distance_to(ev.position) < 9:
					hover_text = "Teleportationsstein: %s" % s["name"]
			for p in win.hud.world.zone.get("portals", []):
				if _w2m(float(p["x"]), float(p["z"])).distance_to(ev.position) < 10:
					hover_text = str(p.get("name", "Portal"))
			queue_redraw()

	func _draw() -> void:
		var mp: Dictionary = win.hud.minimap.map
		if mp.is_empty():
			return
		var r := _rect()
		draw_style_box(UiSkin.parchment_box(), r.grow(6))
		draw_texture_rect(mp["tex"], r, false, Color(1, 1, 1, 0.95))
		var f := UiSkin.font_title
		var disc: Array = win.data.get("discovered", [])
		for sz in win.hud.world.zone.get("subzones", []):
			var p := _w2m(float(sz["x"]), float(sz["z"]))
			var known: bool = str(sz["name"]) in disc
			var txt := str(sz["name"])
			var w := f.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x
			draw_string_outline(f, p - Vector2(w * 0.5, 0), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, 4, Color(0, 0, 0, 0.8))
			draw_string(f, p - Vector2(w * 0.5, 0), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(1, 0.92, 0.7) if known else Color(0.7, 0.7, 0.7, 0.7))
		# Questgebiete
		for q in Game.quests:
			if q.get("done", false):
				continue
			for h in q.get("targets", []):
				var hp := _w2m(float(h[0]), float(h[1]))
				var hr := float(h[2]) / float(mp["size"]) * r.size.x
				draw_circle(hp, maxf(hr, 6), Color(1, 0.85, 0.2, 0.16))
				draw_arc(hp, maxf(hr, 6), 0, TAU, 36, Color(1, 0.85, 0.2, 0.6), 1.5)
		for p in win.hud.world.zone.get("portals", []):
			var pp := _w2m(float(p["x"]), float(p["z"]))
			draw_circle(pp, 7, Color(0.65, 0.35, 1.0, 0.9))
			draw_arc(pp, 9, 0, TAU, 24, Color(1, 1, 1, 0.8), 1.5)
		for s in win.hud.world.zone.get("stones", []):
			var sp := _w2m(float(s["pos"][0]), float(s["pos"][1]))
			var active: bool = str(s["id"]) in win.data.get("stones", [])
			draw_colored_polygon(PackedVector2Array([sp + Vector2(0, -8), sp + Vector2(6, 0), sp + Vector2(0, 8), sp + Vector2(-6, 0)]),
				Color(0.4, 0.8, 1.0) if active else Color(0.5, 0.5, 0.6))
		for n in win.data.get("npcs", []):
			var np := _w2m(float(n["x"]), float(n["z"]))
			var q = n.get("q")
			if q:
				var ch := str(q).substr(0, 1)
				var col := Color(1, 0.85, 0.1) if not str(q).ends_with("b") else Color(0.4, 0.7, 1.0)
				draw_string_outline(UiSkin.font_deco, np + Vector2(-5, 7), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, 4, Color.BLACK)
				draw_string(UiSkin.font_deco, np + Vector2(-5, 7), ch, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, col)
			elif not (n.get("svc", []) as Array).is_empty():
				draw_circle(np, 3.5, Color(1, 0.95, 0.4))
		for pm in win.data.get("party", []):
			draw_circle(_w2m(float(pm["x"]), float(pm["z"])), 5, Color(0.3, 0.6, 1.0))
		var me = win.hud.world.me
		if me:
			var c := _w2m(me.global_position.x, me.global_position.z)
			var yaw: float = me.rotation.y
			var fwd := Vector2(-sin(yaw), -cos(yaw))
			var right := Vector2(fwd.y, -fwd.x)
			var tri := PackedVector2Array([c + fwd * 12, c - fwd * 8 + right * 8, c - fwd * 4, c - fwd * 8 - right * 8])
			draw_colored_polygon(tri, Color(1, 0.9, 0.3))
			draw_polyline(tri + PackedVector2Array([tri[0]]), Color(0.2, 0.1, 0.0), 2.0)
		if hover_text != "":
			var mpos := get_local_mouse_position() + Vector2(14, -8)
			var fb := UiSkin.font_bold
			var w2 := fb.get_string_size(hover_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x
			draw_style_box(UiSkin.tooltip_box(), Rect2(mpos - Vector2(6, 16), Vector2(w2 + 14, 24)))
			draw_string(fb, mpos, hover_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color.WHITE)


class _WorldMap extends Control:
	var win
	const LAYOUT := {
		"gruenmark": [Vector2(0.48, 0.62), Color("#6a9a3a")], "frostklamm": [Vector2(0.62, 0.2), Color("#c8dcef")],
		"mondhain": [Vector2(0.2, 0.5), Color("#4a3a7a")], "aschenlande": [Vector2(0.8, 0.6), Color("#7a3a20")],
		"himmelsbruch": [Vector2(0.5, 0.12), Color("#8ab0e0")],
	}

	func _init(p_win) -> void:
		win = p_win
		custom_minimum_size = Vector2(660, 640)

	func _draw() -> void:
		var r := Rect2(Vector2(10, 10), size - Vector2(20, 20))
		draw_style_box(UiSkin.parchment_box(), r)
		var f := UiSkin.font_title
		var tt := "Eldornia"
		var tw := UiSkin.font_deco.get_string_size(tt, HORIZONTAL_ALIGNMENT_LEFT, -1, 34).x
		draw_string(UiSkin.font_deco, Vector2(r.position.x + (r.size.x - tw) * 0.5, r.position.y + 50), tt, HORIZONTAL_ALIGNMENT_LEFT, -1, 34, Color("#5a3010"))
		# Meer & Küsten
		var rng := RandomNumberGenerator.new()
		rng.seed = 7
		var regions: Array = win.data.get("regions", [])
		if regions.is_empty():
			for k in LAYOUT:
				regions.append({"id": k, "name": Content.defs.get("zones", {}).get(k, {}).get("name", k), "levels": Content.defs.get("zones", {}).get(k, {}).get("levels"), "known": k == Game.zone_id})
		for reg in regions:
			var lay = LAYOUT.get(str(reg["id"]))
			if lay == null:
				continue
			var c: Vector2 = r.position + lay[0] * r.size
			var col: Color = lay[1]
			var pts := PackedVector2Array()
			for i in 18:
				var a := TAU * i / 18.0
				var rad := 78.0 + rng.randf_range(-14, 16)
				pts.append(c + Vector2(cos(a) * rad * 1.25, sin(a) * rad * 0.9))
			var known: bool = reg.get("known", false) or str(reg["id"]) == Game.zone_id
			draw_colored_polygon(pts, col if known else col.lerp(Color(0.6, 0.55, 0.45), 0.7))
			draw_polyline(pts + PackedVector2Array([pts[0]]), Color("#5a3a1a"), 2.5)
			var name := str(reg.get("name", reg["id"]))
			var w := f.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, 18).x
			draw_string_outline(f, c - Vector2(w * 0.5, 0), name, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, 4, Color(1, 0.95, 0.8, 0.8))
			draw_string(f, c - Vector2(w * 0.5, 0), name, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color("#2a1408"))
			var lv = reg.get("levels")
			if lv is Array and lv.size() >= 2:
				var lt := "Stufe %d–%d" % [int(lv[0]), int(lv[1])]
				var w2 := UiSkin.font_bold.get_string_size(lt, HORIZONTAL_ALIGNMENT_LEFT, -1, 14).x
				draw_string(UiSkin.font_bold, c + Vector2(-w2 * 0.5, 20), lt, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color("#3a2410"))
			if str(reg["id"]) == Game.zone_id:
				draw_circle(c + Vector2(0, 38), 7, Color(1, 0.85, 0.2))
				draw_arc(c + Vector2(0, 38), 9, 0, TAU, 20, Color(0.3, 0.15, 0.0), 2.0)
