class_name GrassField
extends Node3D
## Grasbüschel rund um den Spieler (wird beim Laufen nachgeladen).

const CELL := 24.0
const RADIUS := 2          # 5x5 Zellen
const PER_CELL := 900

var hf: Heightfield
var terrain: TerrainBuilder
var theme: Dictionary
var focus := Vector3.ZERO
var _cells: Dictionary = {}   # Vector2i -> MultiMeshInstance3D
var _mesh: ArrayMesh
var _mat: ShaderMaterial
var _last_center := Vector2i(999999, 999999)
var enabled := true


func setup(p_hf: Heightfield, p_terrain: TerrainBuilder, p_theme: Dictionary) -> void:
	hf = p_hf
	terrain = p_terrain
	theme = p_theme
	var g: Array = theme.get("grass", ["#5f9a2c", "#3b7322", "#c9d060"])
	_mat = Mat.grass(Color.html(g[0]), Color.html(g[1]), Color.html(g[2]))
	_mesh = _tuft_mesh()


func _tuft_mesh() -> ArrayMesh:
	var mb := MeshBuilder.new()
	for i in 3:
		var a := PI * i / 3.0
		var dir := Vector3(cos(a), 0, sin(a))
		var w := 0.55
		var h := 0.36
		var p0 := -dir * w * 0.5
		var p1 := dir * w * 0.5
		var n := Vector3.UP
		mb.tri(_mat, p0, p1, p1 + Vector3(0, h, 0), n, n, n, Vector2(0, 0), Vector2(1, 0), Vector2(1, 1))
		mb.tri(_mat, p0, p1 + Vector3(0, h, 0), p0 + Vector3(0, h, 0), n, n, n, Vector2(0, 0), Vector2(1, 1), Vector2(0, 1))
	return mb.commit()


func _process(_delta: float) -> void:
	if not enabled or hf == null:
		return
	var center := Vector2i(int(floor(focus.x / CELL)), int(floor(focus.z / CELL)))
	if center == _last_center:
		return
	_last_center = center
	var wanted := {}
	for dz in range(-RADIUS, RADIUS + 1):
		for dx in range(-RADIUS, RADIUS + 1):
			wanted[Vector2i(center.x + dx, center.y + dz)] = true
	for key in _cells.keys():
		if not wanted.has(key):
			(_cells[key] as Node).queue_free()
			_cells.erase(key)
	for key in wanted:
		if not _cells.has(key):
			_cells[key] = _build_cell(key)


func _build_cell(key: Vector2i) -> MultiMeshInstance3D:
	var rng := RandomNumberGenerator.new()
	rng.seed = key.x * 92821 + key.y * 68917
	var xforms: Array[Transform3D] = []
	var x0 := key.x * CELL
	var z0 := key.y * CELL
	var snow: float = float(theme.get("terrain", {}).get("snow_amount", 0.0))
	for i in PER_CELL:
		var x := x0 + rng.randf() * CELL
		var z := z0 + rng.randf() * CELL
		if absf(x) > hf.half - 2.0 or absf(z) > hf.half - 2.0:
			continue
		var w := terrain.weight_at(x, z)
		if w.r > 0.3 or w.g > 0.25 or w.b > 0.4:
			continue
		var y := hf.height(x, z)
		if y <= hf.void_level + 2.0:
			continue
		var n := hf.normal(x, z)
		if n.y < 0.8:
			continue
		if snow > 0.5 and rng.randf() < 0.75:
			continue
		var s := rng.randf_range(0.7, 1.35)
		xforms.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU) * Basis.from_scale(Vector3(s, s * rng.randf_range(0.8, 1.3), s)), Vector3(x, y - 0.03, z)))
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = _mesh
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mmi)
	return mmi
