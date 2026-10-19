class_name TerrainBuilder
extends RefCounted
## Erzeugt das Gelände einer Außenzone als Kacheln (Chunks) mit Vertexfarben für
## Wege (R), Pflaster (G), Äcker (B) und die Akzentschicht der Zone (A).

const CHUNK_CELLS := 32

var hf: Heightfield
var zone: Dictionary
var theme: Dictionary
var weights := PackedColorArray()   # pro Gitterpunkt
var material: ShaderMaterial


func _init(p_hf: Heightfield, p_zone: Dictionary, p_theme: Dictionary) -> void:
	hf = p_hf
	zone = p_zone
	theme = p_theme


func build(parent: Node3D) -> void:
	_compute_weights()
	material = _make_material()
	var n := hf.n
	var cells := n - 1
	var chunks := int(ceil(float(cells) / CHUNK_CELLS))
	for cj in chunks:
		for ci in chunks:
			var mi := MeshInstance3D.new()
			mi.name = "Terrain_%d_%d" % [ci, cj]
			mi.mesh = _build_chunk(ci * CHUNK_CELLS, cj * CHUNK_CELLS, min(CHUNK_CELLS, cells - ci * CHUNK_CELLS), min(CHUNK_CELLS, cells - cj * CHUNK_CELLS))
			if mi.mesh == null:
				mi.queue_free()
				continue
			mi.material_override = material
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			parent.add_child(mi)


func _make_material() -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/terrain.gdshader")
	var t: Dictionary = theme.get("terrain", {})
	for k in ["grass_a", "grass_b", "grass_c", "flower_a", "flower_b", "dirt", "dirt_dark", "rock", "rock_dark",
			"cobble", "cobble_dark", "farmland", "sand", "snow", "accent"]:
		if t.has(k):
			m.set_shader_parameter(k, Color.html(t[k]))
	m.set_shader_parameter("accent_glow", Color.html(t.get("accent_glow", "#000000")))
	m.set_shader_parameter("snow_amount", float(t.get("snow_amount", 0.0)))
	m.set_shader_parameter("snow_height", float(t.get("snow_height", 9999.0)))
	m.set_shader_parameter("flower_density", float(t.get("flower_density", 1.0)))
	var wl := -100.0
	for w in zone.get("water", []):
		wl = max(wl, float(w.get("level", -0.8)))
	m.set_shader_parameter("water_level", wl)
	return m


func _idx(i: int, j: int) -> int:
	return j * hf.n + i


func _world_to_grid(x: float, z: float) -> Vector2:
	return Vector2((x + hf.half) / hf.step, (z + hf.half) / hf.step)


func _compute_weights() -> void:
	var n := hf.n
	weights.resize(n * n)
	weights.fill(Color(0, 0, 0, 0))
	# Wege
	for road in zone.get("roads", []):
		var w: float = float(road.get("w", 3.0))
		var pts: Array = road["pts"]
		var kind: String = road.get("k", "dirt")
		for k in pts.size() - 1:
			var a := Vector2(pts[k][0], pts[k][1])
			var b := Vector2(pts[k + 1][0], pts[k + 1][1])
			_paint_segment(a, b, w, 0 if kind == "dirt" else 1)
	# Plätze und gepflasterte Flächen
	var paved: Array = zone.get("paved", []).duplicate()
	if zone.has("plaza"):
		paved.append(zone["plaza"])
	for p in paved:
		if p.has("r"):
			_paint_circle(Vector2(p["x"], p["z"]), float(p["r"]), 1, 2.5)
		else:
			_paint_rect(Vector2(p["x"], p["z"]), float(p["w"]), float(p["d"]), float(p.get("rot", 0.0)), 1)
	# Äcker
	for p in zone.get("props", []):
		if p.get("t") == "field":
			_paint_rect(Vector2(p["x"], p["z"]), float(p["w"]), float(p["d"]), 0.0, 2)
	# Akzentflächen
	for a in zone.get("accent", []):
		_paint_circle(Vector2(a["x"], a["z"]), float(a["r"]), 3, float(a.get("soft", 6.0)))


func _set_channel(i: int, j: int, ch: int, v: float) -> void:
	var id := _idx(i, j)
	var c: Color = weights[id]
	match ch:
		0: c.r = max(c.r, v)
		1: c.g = max(c.g, v)
		2: c.b = max(c.b, v)
		3: c.a = max(c.a, v)
	weights[id] = c


func _paint_segment(a: Vector2, b: Vector2, width: float, ch: int) -> void:
	var half_w := width * 0.5
	var reach := half_w + 1.6
	var mn := Vector2(min(a.x, b.x), min(a.y, b.y)) - Vector2(reach, reach)
	var mx := Vector2(max(a.x, b.x), max(a.y, b.y)) + Vector2(reach, reach)
	var g0 := _world_to_grid(mn.x, mn.y)
	var g1 := _world_to_grid(mx.x, mx.y)
	var ab := b - a
	var l2 := ab.length_squared()
	for j in range(max(0, int(floor(g0.y))), min(hf.n, int(ceil(g1.y)) + 1)):
		for i in range(max(0, int(floor(g0.x))), min(hf.n, int(ceil(g1.x)) + 1)):
			var p := Vector2(-hf.half + i * hf.step, -hf.half + j * hf.step)
			var t := 0.0 if l2 == 0.0 else clampf((p - a).dot(ab) / l2, 0.0, 1.0)
			var d := p.distance_to(a + ab * t)
			if d < reach:
				var v := 1.0 - smoothstep(half_w - 0.6, half_w + 1.4, d)
				_set_channel(i, j, ch, v)


func _paint_circle(c: Vector2, r: float, ch: int, soft: float) -> void:
	var reach := r + soft
	var g0 := _world_to_grid(c.x - reach, c.y - reach)
	var g1 := _world_to_grid(c.x + reach, c.y + reach)
	for j in range(max(0, int(floor(g0.y))), min(hf.n, int(ceil(g1.y)) + 1)):
		for i in range(max(0, int(floor(g0.x))), min(hf.n, int(ceil(g1.x)) + 1)):
			var p := Vector2(-hf.half + i * hf.step, -hf.half + j * hf.step)
			var d := p.distance_to(c)
			if d < reach:
				_set_channel(i, j, ch, 1.0 - smoothstep(r - soft * 0.3, reach, d))


func _paint_rect(c: Vector2, w: float, d: float, rot: float, ch: int) -> void:
	var reach := Vector2(w, d).length() * 0.5 + 2.0
	var g0 := _world_to_grid(c.x - reach, c.y - reach)
	var g1 := _world_to_grid(c.x + reach, c.y + reach)
	var cs := cos(-rot)
	var sn := sin(-rot)
	for j in range(max(0, int(floor(g0.y))), min(hf.n, int(ceil(g1.y)) + 1)):
		for i in range(max(0, int(floor(g0.x))), min(hf.n, int(ceil(g1.x)) + 1)):
			var p := Vector2(-hf.half + i * hf.step, -hf.half + j * hf.step) - c
			var q := Vector2(p.x * cs - p.y * sn, p.x * sn + p.y * cs)
			var dx := absf(q.x) - w * 0.5
			var dz := absf(q.y) - d * 0.5
			var dist: float = max(dx, dz)
			if dist < 1.5:
				_set_channel(i, j, ch, 1.0 - smoothstep(-0.8, 1.5, dist))


func _build_chunk(i0: int, j0: int, ci: int, cj: int) -> ArrayMesh:
	if ci <= 0 or cj <= 0:
		return null
	var n := hf.n
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var cols := PackedColorArray()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()
	var w := ci + 1
	var all_void := true
	for j in range(j0, j0 + cj + 1):
		for i in range(i0, i0 + ci + 1):
			var x := -hf.half + i * hf.step
			var z := -hf.half + j * hf.step
			var y := hf.at_index(i, j)
			if y > hf.void_level + 1.0:
				all_void = false
			verts.append(Vector3(x, y, z))
			var hl := hf.at_index(i - 1, j)
			var hr := hf.at_index(i + 1, j)
			var hd := hf.at_index(i, j - 1)
			var hu := hf.at_index(i, j + 1)
			norms.append(Vector3(hl - hr, 2.0 * hf.step, hd - hu).normalized())
			cols.append(weights[_idx(i, j)])
			uvs.append(Vector2(x, z))
	if all_void:
		return null
	for j in cj:
		for i in ci:
			var a := j * w + i
			var b := a + 1
			var c := a + w
			var e := c + 1
			# gleiche Diagonale wie der Server (b–c); Vorderseite im Uhrzeigersinn von oben
			var ya := verts[a].y
			var yb := verts[b].y
			var yc := verts[c].y
			var ye := verts[e].y
			if min(ya, min(yb, yc)) > hf.void_level + 1.0:
				idx.append_array([a, b, c])
			if min(yb, min(ye, yc)) > hf.void_level + 1.0:
				idx.append_array([b, e, c])
	if idx.is_empty():
		return null
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = norms
	arrays[Mesh.ARRAY_COLOR] = cols
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


## Gewicht an einer Weltposition (für Grasverteilung: kein Gras auf Wegen/Pflaster/Äckern)
func weight_at(x: float, z: float) -> Color:
	var g := _world_to_grid(x, z)
	var i := clampi(int(round(g.x)), 0, hf.n - 1)
	var j := clampi(int(round(g.y)), 0, hf.n - 1)
	return weights[_idx(i, j)]
