class_name DungeonBuilder
extends RefCounted
## Baut einen Dungeon aus begehbaren Rechtecken (Räume und Gänge): Boden, Wände, Decke,
## Fackeln und Requisiten. Stil je nach Dungeon (Krypta, Schmiede, Kathedrale, Thron).

const WALL_H := 7.5
const CELL := 1.0

var rects: Array = []
var minx := 0.0
var minz := 0.0
var w := 0
var h := 0
var grid := PackedByteArray()
var style := "krypta"

const STYLES := {
	"krypta": {"floor": "#6e6a64", "floor2": "#34312d", "wall": "#7a766e", "wall2": "#3a3631", "torch": "#7ab0ff", "ceil": "#2a2826", "trim": "#5a5650"},
	"schmiede": {"floor": "#3e3634", "floor2": "#1a1414", "wall": "#4a403a", "wall2": "#1e1814", "torch": "#ff7a20", "ceil": "#1a1412", "trim": "#8a5a30"},
	"kathedrale": {"floor": "#c8c2b8", "floor2": "#6a6058", "wall": "#9a90a0", "wall2": "#4a4050", "torch": "#c070ff", "ceil": "#2a2030", "trim": "#d0b060"},
	"thron": {"floor": "#d8d4e8", "floor2": "#8a84a8", "wall": "#a8a0c8", "wall2": "#5a5078", "torch": "#80e0ff", "ceil": "#14102a", "trim": "#e0c070"},
	"hoehle": {"floor": "#6a5a4a", "floor2": "#2a2018", "wall": "#7a6a58", "wall2": "#3a2e22", "torch": "#ffb060", "ceil": "#2a2018", "trim": "#5a4a3a"},
	"arena": {"floor": "#b8a888", "floor2": "#6a5a40", "wall": "#9a8a70", "wall2": "#4a3e2e", "torch": "#ffb060", "ceil": "#000000", "trim": "#c8a050"},
}


func build(root: Node3D, zone: Dictionary, theme: Dictionary) -> void:
	rects = zone["rects"]
	style = str(zone.get("style", "krypta"))
	var st: Dictionary = STYLES.get(style, STYLES["krypta"])
	_rasterize()
	var floor_mat := Mat.stylized(Color.html(st.floor), Mat.P.FLAGSTONE, {"c2": Color.html(st.floor2), "tri": true, "scale": 0.7})
	var wall_mat := Mat.stylized(Color.html(st.wall), Mat.P.STONE, {"c2": Color.html(st.wall2), "tri": true, "scale": 1.0})
	var trim_mat := Mat.stylized(Color.html(st.trim), Mat.P.STONE if style != "kathedrale" else Mat.P.GOLD, {"c2": Color.html(st.wall2), "tri": true})
	var ceil_mat := Mat.stylized(Color.html(st.ceil), Mat.P.STONE, {"c2": Color.html("#000000"), "tri": true, "scale": 0.6})
	var open_sky: bool = zone.get("open_sky", false)
	var mb := MeshBuilder.new()
	for r in rects:
		var x1 := float(r[0])
		var z1 := float(r[1])
		var x2 := float(r[2])
		var z2 := float(r[3])
		mb.box(floor_mat, MeshBuilder.at(Vector3((x1 + x2) * 0.5, -0.25, (z1 + z2) * 0.5)), Vector3(x2 - x1 + 0.02, 0.5, z2 - z1 + 0.02))
		if not open_sky:
			mb.box(ceil_mat, MeshBuilder.at(Vector3((x1 + x2) * 0.5, WALL_H + 0.25, (z1 + z2) * 0.5)), Vector3(x2 - x1 + 2.0, 0.5, z2 - z1 + 2.0))
	var mi := MeshInstance3D.new()
	mi.mesh = mb.commit()
	root.add_child(mi)
	# Wände entlang der Ränder
	var walls := _boundary_segments()
	mb = MeshBuilder.new()
	var torch_positions := []
	for seg in walls:
		var a: Vector2 = seg[0]
		var b: Vector2 = seg[1]
		var n: Vector2 = seg[2]
		var center := (a + b) * 0.5
		var len := a.distance_to(b)
		var horiz := absf(a.y - b.y) < 0.01
		var size := Vector3(len + 1.0, WALL_H if not open_sky else 1.6, 1.0) if horiz else Vector3(1.0, WALL_H if not open_sky else 1.6, len + 1.0)
		var off := Vector3(-n.x * 0.5, 0, -n.y * 0.5)
		var hh := size.y
		mb.box(wall_mat, MeshBuilder.at(Vector3(center.x, hh * 0.5, center.y) + off), size)
		# Sockelleiste und Gesims
		var trim := Vector3(size.x + (0.0 if horiz else 0.3), 0.5, size.z + (0.3 if horiz else 0.0))
		mb.box(trim_mat, MeshBuilder.at(Vector3(center.x, 0.25, center.y) + off * 0.7), trim)
		if not open_sky:
			mb.box(trim_mat, MeshBuilder.at(Vector3(center.x, WALL_H - 0.6, center.y) + off * 0.7), trim)
		# Wandpfeiler und Fackeln
		var count := int(len / 6.0)
		for k in count:
			var t := (k + 0.5) / count
			var p := a.lerp(b, t)
			var pp := Vector3(p.x, 0, p.y) + Vector3(n.x * 0.15, 0, n.y * 0.15)
			var psize := Vector3(0.9, hh, 0.5) if horiz else Vector3(0.5, hh, 0.9)
			mb.box(wall_mat, MeshBuilder.at(pp + Vector3(0, hh * 0.5, 0)), psize)
			if k % 2 == 0:
				torch_positions.append([pp + Vector3(n.x * 0.35, 3.2, n.y * 0.35), n])
	mi = MeshInstance3D.new()
	mi.mesh = mb.commit()
	root.add_child(mi)
	var torch_col := Color.html(st.torch)
	var used := 0
	for tp in torch_positions:
		if used > 40:
			break
		used += 1
		var pos: Vector3 = tp[0]
		var n: Vector2 = tp[1]
		var tmb := MeshBuilder.new()
		var iron := Mat.stylized(Color.html("#2a2a2e"), Mat.P.METAL)
		tmb.beam(iron, pos - Vector3(n.x, 0, n.y) * 0.3 + Vector3(0, -0.2, 0), pos + Vector3(0, 0.1, 0), Vector2(0.06, 0.06))
		tmb.cylinder(iron, MeshBuilder.at(pos + Vector3(0, 0.05, 0)), 0.12, 0.2, 0.25, 8)
		var tmi := MeshInstance3D.new()
		tmi.mesh = tmb.commit()
		root.add_child(tmi)
		var f := FxLib.fire(0.35, torch_col.lerp(Color(1, 0.6, 0.2), 0.3), true)
		f.position = pos + Vector3(0, 0.3, 0)
		root.add_child(f)
	# Requisiten
	PropFactory.hf_ref = null
	var props := Node3D.new()
	root.add_child(props)
	PropFactory.populate(props, zone.get("props", []), null, "dungeon")
	# Lavakanäle / magische Becken
	for pool in zone.get("pools", []):
		var pmb := MeshBuilder.new()
		var lava: bool = pool.get("lava", style == "schmiede")
		var m := Mat.water(Color.html("#ff7a20") if lava else Color.html("#5a8ad8"), Color.html("#3a0a04") if lava else Color.html("#1a2a5e"), lava)
		pmb.box(m, MeshBuilder.at(Vector3(float(pool["x"]), 0.02, float(pool["z"]))), Vector3(float(pool["w"]), 0.05, float(pool["d"])))
		var pmi := MeshInstance3D.new()
		pmi.mesh = pmb.commit()
		root.add_child(pmi)
		if lava:
			var l := FxLib.light(Color.html("#ff6a20"), 2.5, 10.0)
			l.position = Vector3(float(pool["x"]), 1.5, float(pool["z"]))
			root.add_child(l)
	# Grundlicht in jedem Raum
	for r in rects:
		var cx := (float(r[0]) + float(r[2])) * 0.5
		var cz := (float(r[1]) + float(r[3])) * 0.5
		var area := (float(r[2]) - float(r[0])) * (float(r[3]) - float(r[1]))
		if area > 150.0:
			var l := FxLib.light(torch_col.lerp(Color.WHITE, 0.4), 0.8, sqrt(area) * 1.1)
			l.position = Vector3(cx, WALL_H - 1.5, cz)
			root.add_child(l)


func _rasterize() -> void:
	minx = 1e9
	minz = 1e9
	var maxx := -1e9
	var maxz := -1e9
	for r in rects:
		minx = min(minx, float(r[0]))
		minz = min(minz, float(r[1]))
		maxx = max(maxx, float(r[2]))
		maxz = max(maxz, float(r[3]))
	minx -= 2.0
	minz -= 2.0
	w = int(ceil((maxx - minx) / CELL)) + 3
	h = int(ceil((maxz - minz) / CELL)) + 3
	grid.resize(w * h)
	grid.fill(0)
	for r in rects:
		var i0 := int(round((float(r[0]) - minx) / CELL))
		var i1 := int(round((float(r[2]) - minx) / CELL))
		var j0 := int(round((float(r[1]) - minz) / CELL))
		var j1 := int(round((float(r[3]) - minz) / CELL))
		for j in range(j0, j1):
			for i in range(i0, i1):
				grid[j * w + i] = 1


func _cell(i: int, j: int) -> int:
	if i < 0 or j < 0 or i >= w or j >= h:
		return 0
	return grid[j * w + i]


## Randkanten als zusammengefasste Segmente: [a, b, normal_ins_Innere]
func _boundary_segments() -> Array:
	var segs := []
	# horizontale Kanten (zwischen Zeile j-1 und j)
	for j in range(0, h + 1):
		var run_start := -1
		var run_n := 0
		for i in range(0, w + 1):
			var above := _cell(i, j - 1)
			var below := _cell(i, j)
			var n := 0
			if i < w and above != below:
				n = 1 if below == 1 else -1
			if n != run_n:
				if run_n != 0:
					var z := minz + j * CELL
					segs.append([Vector2(minx + run_start * CELL, z), Vector2(minx + i * CELL, z), Vector2(0, run_n)])
				run_start = i
				run_n = n
	# vertikale Kanten
	for i in range(0, w + 1):
		var run_start := -1
		var run_n := 0
		for j in range(0, h + 1):
			var left := _cell(i - 1, j)
			var right := _cell(i, j)
			var n := 0
			if j < h and left != right:
				n = 1 if right == 1 else -1
			if n != run_n:
				if run_n != 0:
					var x := minx + i * CELL
					segs.append([Vector2(x, minz + run_start * CELL), Vector2(x, minz + j * CELL), Vector2(run_n, 0)])
				run_start = j
				run_n = n
	return segs


func walkable(x: float, z: float) -> bool:
	var i := int(floor((x - minx) / CELL))
	var j := int(floor((z - minz) / CELL))
	return _cell(i, j) == 1
