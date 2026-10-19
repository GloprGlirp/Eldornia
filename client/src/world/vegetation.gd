class_name Vegetation
extends RefCounted
## Bäume, Büsche, Felsen und Blumen im handgemalten Stil.
## Jede Art hat mehrere Varianten; verteilt wird per MultiMesh pro Gebietskachel mit LOD.

const CHUNK := 96.0
const VARIANTS := 2
const FAR_DIST := 110.0

static var _mesh_cache: Dictionary = {}


static func _rng(seed_v: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = seed_v
	return r


static func _theme_colors(theme: Dictionary, key: String) -> Array:
	var arr: Array = theme.get(key, ["#7fae32", "#2b5a1a", "#c6d45a"])
	return [Color.html(arr[0]), Color.html(arr[1]), Color.html(arr[2])]


static func _leaf_mats(theme: Dictionary, key := "leaf") -> Array:
	var c := _theme_colors(theme, key)
	var emis := Color.html(theme.get("leaf_emis", "#000000"))
	var solid := Mat.foliage(c[0], c[1], c[2], false, {"emis": emis})
	var cards := Mat.foliage(c[0].lightened(0.05), c[1], c[2], true, {"density": 5.0, "emis": emis})
	return [solid, cards]


static func _bark_mat(theme: Dictionary, kind := "") -> ShaderMaterial:
	var b: Array = theme.get("bark", ["#6e4a2e", "#3c2616"])
	if kind == "birch":
		return Mat.stylized(Color.html("#e8e2d4"), Mat.P.BARK, {"c2": Color.html("#3a3430"), "scale": 1.0})
	return Mat.stylized(Color.html(b[0]), Mat.P.BARK, {"c2": Color.html(b[1]), "scale": 1.2})


## Gebogener, sich verjüngender Stamm aus Segmenten. Gibt die Spitze zurück.
static func _trunk(mb: MeshBuilder, mat: Material, base: Vector3, height: float, r0: float, r1: float,
		lean: Vector3, segs: int, rng: RandomNumberGenerator, roots := true) -> Vector3:
	var p := base
	var dir := Vector3.UP
	for k in segs:
		var t0 := float(k) / segs
		var t1 := float(k + 1) / segs
		var ra := lerpf(r0, r1, t0)
		var rb := lerpf(r0, r1, t1)
		var seg_len := height / segs
		dir = (dir + lean * (0.35 / segs) + Vector3(rng.randf_range(-0.12, 0.12), 0, rng.randf_range(-0.12, 0.12))).normalized()
		var q := p + dir * seg_len
		var y := dir
		var x := Vector3.FORWARD.cross(y)
		if x.length() < 0.01:
			x = Vector3.RIGHT
		x = x.normalized()
		var z := x.cross(y).normalized()
		var xf := Transform3D(Basis(x, y, z), p - y * 0.05)
		mb.cylinder(mat, xf, ra, rb, seg_len + 0.1, 9, false)
		p = q
	if roots:
		for i in 5:
			var a := TAU * i / 5.0 + rng.randf_range(-0.3, 0.3)
			var d := Vector3(cos(a), 0, sin(a))
			var root_end := base + d * r0 * rng.randf_range(2.2, 3.2) + Vector3(0, -0.15, 0)
			var root_start := base + Vector3(0, r0 * 1.6, 0) + d * r0 * 0.5
			var y := (root_end - root_start).normalized()
			var x := Vector3.UP.cross(y).normalized()
			var z := x.cross(y).normalized()
			mb.cylinder(mat, Transform3D(Basis(x, y, z), root_start), r0 * 0.45, r0 * 0.12, root_start.distance_to(root_end), 6, false)
	return p


static func _branch(mb: MeshBuilder, mat: Material, from: Vector3, to: Vector3, r0: float, r1: float) -> void:
	var y := (to - from).normalized()
	var x := Vector3.UP.cross(y)
	if x.length() < 0.01:
		x = Vector3.RIGHT
	x = x.normalized()
	var z := x.cross(y).normalized()
	mb.cylinder(mat, Transform3D(Basis(x, y, z), from), r0, r1, from.distance_to(to), 6, false)


static func _leaf_cards(mb: MeshBuilder, mat: Material, center: Vector3, radii: Vector3, count: int,
		rng: RandomNumberGenerator, size := 1.3) -> void:
	for i in count:
		var a := rng.randf() * TAU
		var e := rng.randf_range(-0.35, 1.0)
		var d := Vector3(cos(a) * cos(e), sin(e), sin(a) * cos(e)).normalized()
		var p := center + Vector3(d.x * radii.x, d.y * radii.y, d.z * radii.z) * 0.92
		var z := d
		var x := Vector3.UP.cross(z)
		if x.length() < 0.01:
			x = Vector3.RIGHT
		x = x.normalized()
		var y := z.cross(x).normalized()
		var basis := Basis(x, y, z).rotated(d, rng.randf() * TAU)
		var s := size * rng.randf_range(0.75, 1.25)
		var xf := Transform3D(basis, p + y * s * 0.5)
		var col := Color(0.95, 1.0, 0, 1)
		mb.plane(mat, xf, s, s, col)


## Laubbaum (Eiche) – große, gemalte Blattwolken
static func _oak(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var bark := _bark_mat(theme)
	var leaves := _leaf_mats(theme)
	var h := rng.randf_range(3.6, 4.6)
	var lean := Vector3(rng.randf_range(-0.6, 0.6), 0, rng.randf_range(-0.6, 0.6))
	var top := _trunk(mb, bark, Vector3.ZERO, h, 0.42, 0.26, lean, 4 if lod == 0 else 2, rng, lod == 0)
	var canopy_c := top + Vector3(0, 1.6, 0)
	var blobs := []
	var nb := rng.randi_range(6, 8)
	blobs.append([canopy_c + Vector3(0, 0.9, 0), Vector3(2.2, 1.8, 2.2)])
	for i in nb:
		var a := TAU * i / nb + rng.randf_range(-0.3, 0.3)
		var dist := rng.randf_range(1.6, 2.4)
		var y := rng.randf_range(-0.6, 0.9)
		var r := rng.randf_range(1.4, 2.0)
		blobs.append([canopy_c + Vector3(cos(a) * dist, y, sin(a) * dist), Vector3(r, r * 0.82, r)])
	for b in blobs:
		var c: Vector3 = b[0]
		if lod == 0:
			_branch(mb, bark, top + Vector3(0, -0.4, 0), c.lerp(top, 0.25), 0.18, 0.07)
	for b in blobs:
		var c: Vector3 = b[0]
		var r: Vector3 = b[1]
		var su := 14 if lod == 0 else 7
		var sv := 9 if lod == 0 else 5
		var ao := clampf(0.55 + (c.y - canopy_c.y) * 0.25, 0.35, 1.0)
		mb.ellipsoid(leaves[0], MeshBuilder.at(c), r, su, sv, Color(ao, 1.0, 0, 1), 0.22 if lod == 0 else 0.15, 0.9, rng.randi(), -1.0, 1.0, 0.45)
	if lod == 0:
		for b in blobs:
			_leaf_cards(mb, leaves[1], b[0], b[1], 7, rng, 1.25)
	return mb.commit()


static func _birch(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var bark := _bark_mat(theme, "birch")
	var c := _theme_colors(theme, "leaf")
	var light: Color = c[0].lightened(0.15)
	var leaves_solid := Mat.foliage(light, c[1].lightened(0.1), Color.html("#e8e070"))
	var leaves_cards := Mat.foliage(light, c[1].lightened(0.1), Color.html("#e8e070"), true, {"density": 6.0})
	var h := rng.randf_range(5.0, 6.5)
	var top := _trunk(mb, bark, Vector3.ZERO, h, 0.2, 0.12, Vector3(rng.randf_range(-0.3, 0.3), 0, rng.randf_range(-0.3, 0.3)), 4 if lod == 0 else 2, rng, false)
	for i in 4:
		var y := h * (0.55 + 0.15 * i)
		var a := rng.randf() * TAU
		var cc := Vector3(cos(a) * 0.8, y + 0.6, sin(a) * 0.8)
		var r := 1.2 - i * 0.12
		mb.ellipsoid(leaves_solid, MeshBuilder.at(cc), Vector3(r, r * 1.2, r), 12 if lod == 0 else 6, 8 if lod == 0 else 4, Color(0.5 + 0.15 * i, 1, 0, 1), 0.2, 1.0, rng.randi(), -1, 1, 0.5)
		if lod == 0:
			_leaf_cards(mb, leaves_cards, cc, Vector3(r, r * 1.2, r), 5, rng, 0.9)
	mb.ellipsoid(leaves_solid, MeshBuilder.at(top + Vector3(0, 0.6, 0)), Vector3(0.9, 1.3, 0.9), 10, 7, Color(1, 1, 0, 1), 0.2, 1.0, rng.randi())
	return mb.commit()


static func _pine(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var bark := _bark_mat(theme)
	var c := _theme_colors(theme, "pine")
	var needles := Mat.foliage(c[0], c[1], c[2], false, {"wind": 0.6, "var": 0.15})
	var h := rng.randf_range(8.0, 10.5)
	mb.cylinder(bark, MeshBuilder.at(Vector3(0, -0.2, 0)), 0.32, 0.08, h, 8, false)
	var tiers := 6 if lod == 0 else 4
	for k in tiers:
		var t := float(k) / tiers
		var y := lerpf(1.8, h - 0.6, t)
		var r := lerpf(2.8, 0.7, t) * rng.randf_range(0.9, 1.1)
		var th := lerpf(2.4, 1.3, t)
		var seg := 12 if lod == 0 else 7
		# hängende Etage: Kegelstumpf mit gewelltem Rand
		var xf := MeshBuilder.at(Vector3(0, y, 0), rng.randf() * TAU)
		_pine_tier(mb, needles, xf, r, th, seg, rng, 0.4 + 0.6 * t)
	return mb.commit()


static func _pine_tier(mb: MeshBuilder, mat: Material, xf: Transform3D, r: float, h: float, seg: int,
		rng: RandomNumberGenerator, ao_top: float) -> void:
	var tip := xf * Vector3(0, h, 0)
	var rim := []
	for i in seg:
		var a := TAU * i / seg
		var rr := r * (1.0 + (0.12 if i % 2 == 0 else -0.08))
		var droop := -0.35 if i % 2 == 0 else 0.0
		rim.append(xf * Vector3(cos(a) * rr, droop, sin(a) * rr))
	var under := xf * Vector3(0, h * 0.25, 0)
	var basis := xf.basis
	for i in seg:
		var p0: Vector3 = rim[i]
		var p1: Vector3 = rim[(i + 1) % seg]
		var n0 := ((p0 - xf.origin).normalized() + basis.y * 0.9).normalized()
		var n1 := ((p1 - xf.origin).normalized() + basis.y * 0.9).normalized()
		var nt := basis.y
		var c_rim := Color(0.55, 1.0, 0, 1)
		var c_tip := Color(ao_top, 0.3, 0, 1)
		mb.tri(mat, p0, p1, tip, n0, n1, nt, Vector2(0, 0), Vector2(1, 0), Vector2(0.5, 1), c_rim, c_rim, c_tip)
		var nd := -basis.y
		var c_under := Color(0.25, 0.6, 0, 1)
		mb.tri(mat, p1, p0, under, nd, nd, nd, Vector2(0, 0), Vector2(1, 0), Vector2(0.5, 1), c_under, c_under, c_under)


static func _bush(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var leaves := _leaf_mats(theme)
	var n := rng.randi_range(2, 4)
	for i in n:
		var a := rng.randf() * TAU
		var d := rng.randf_range(0.0, 0.6)
		var r := rng.randf_range(0.6, 0.95)
		var c := Vector3(cos(a) * d, r * 0.55, sin(a) * d)
		mb.ellipsoid(leaves[0], MeshBuilder.at(c), Vector3(r, r * 0.8, r), 10 if lod == 0 else 6, 7 if lod == 0 else 4, Color(0.6, 0.7, 0, 1), 0.25, 1.2, rng.randi(), -0.6, 1.0, 0.4)
		if lod == 0:
			_leaf_cards(mb, leaves[1], c, Vector3(r, r * 0.8, r), 4, rng, 0.8)
	return mb.commit()


static func _deadtree(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var b: Array = theme.get("bark", ["#6e4a2e", "#3c2616"])
	var bark := Mat.stylized(Color.html(b[0]).darkened(0.25), Mat.P.BARK, {"c2": Color.html(b[1]).darkened(0.3)})
	var h := rng.randf_range(3.5, 5.0)
	var top := _trunk(mb, bark, Vector3.ZERO, h, 0.32, 0.12, Vector3(rng.randf_range(-0.8, 0.8), 0, rng.randf_range(-0.8, 0.8)), 4, rng, true)
	for i in 5:
		var y := rng.randf_range(h * 0.45, h * 0.95)
		var a := rng.randf() * TAU
		var from := Vector3(0, y, 0).lerp(top, y / h)
		var to := from + Vector3(cos(a) * rng.randf_range(1.2, 2.2), rng.randf_range(0.6, 1.6), sin(a) * rng.randf_range(1.2, 2.2))
		_branch(mb, bark, from, to, 0.1, 0.03)
		var to2 := to + Vector3(cos(a + 0.8) * 0.8, 0.5, sin(a + 0.8) * 0.8)
		_branch(mb, bark, to, to2, 0.035, 0.01)
	return mb.commit()


static func _rock(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var t: Dictionary = theme.get("terrain", {})
	var rock := Mat.stylized(Color.html(t.get("rock", "#8f877a")), Mat.P.ROCK, {"c2": Color.html(t.get("rock_dark", "#57514c")), "tri": true, "scale": 0.8})
	var r := Vector3(rng.randf_range(0.9, 1.3), rng.randf_range(0.55, 0.85), rng.randf_range(0.8, 1.2))
	mb.ellipsoid(rock, MeshBuilder.at(Vector3(0, r.y * 0.25, 0), rng.randf() * TAU), r, 12 if lod == 0 else 7, 8 if lod == 0 else 5, Color.WHITE, 0.35, 1.1, rng.randi(), -0.4, 1.0)
	if rng.randf() < 0.6:
		var r2 := r * 0.5
		mb.ellipsoid(rock, MeshBuilder.at(Vector3(r.x * 0.9, r2.y * 0.2, r.z * 0.3), rng.randf() * TAU), r2, 9, 6, Color.WHITE, 0.3, 1.3, rng.randi(), -0.4, 1.0)
	if theme.get("terrain", {}).get("snow_amount", 0.0) > 0.5:
		var snow := Mat.stylized(Color.html("#f2f7ff"), Mat.P.PLAIN, {"rough": 0.6})
		mb.ellipsoid(snow, MeshBuilder.at(Vector3(0, r.y * 0.62, 0)), Vector3(r.x * 0.85, r.y * 0.3, r.z * 0.85), 10, 4, Color.WHITE, 0.2, 1.2, rng.randi(), 0.0, 1.0)
	return mb.commit()


static func _flowers(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var t: Dictionary = theme.get("terrain", {})
	var stem := Mat.stylized(Color.html("#4a7a2a"))
	var colors := [Color.html(t.get("flower_a", "#f4dc5a")), Color.html(t.get("flower_b", "#d870c0")), Color.html("#ffffff"), Color.html("#e05040")]
	var petal := Mat.stylized(colors[seed_v % colors.size()], Mat.P.PLAIN, {"rim": 0.3, "emis": colors[seed_v % colors.size()] * 0.15})
	var center := Mat.stylized(Color.html("#f0c040"))
	for i in rng.randi_range(5, 9):
		var a := rng.randf() * TAU
		var d := rng.randf_range(0.0, 0.7)
		var p := Vector3(cos(a) * d, 0, sin(a) * d)
		var hgt := rng.randf_range(0.2, 0.42)
		mb.beam(stem, p, p + Vector3(0, hgt, 0), Vector2(0.025, 0.025))
		for k in 5:
			var pa := TAU * k / 5.0
			mb.ellipsoid(petal, MeshBuilder.at(p + Vector3(cos(pa) * 0.06, hgt, sin(pa) * 0.06)), Vector3(0.06, 0.02, 0.06), 5, 3)
		mb.ellipsoid(center, MeshBuilder.at(p + Vector3(0, hgt + 0.01, 0)), Vector3(0.035, 0.03, 0.035), 5, 3)
	return mb.commit()


## Riesenpilz (Mondhain)
static func _mushroom(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var stalk := Mat.stylized(Color.html("#e8e0d0"), Mat.P.PLAIN, {"rim": 0.25})
	var cap_col = [Color.html("#7a4ad0"), Color.html("#3ab0c0"), Color.html("#d04a8a")][seed_v % 3]
	var cap := Mat.stylized(cap_col, Mat.P.PLAIN, {"emis": cap_col * 0.35, "rim": 0.4})
	var dots := Mat.emissive(Color.html("#e8ffff"), 1.5)
	var h := rng.randf_range(2.5, 4.5)
	mb.cylinder(stalk, MeshBuilder.at(Vector3.ZERO), 0.35, 0.22, h, 10, false)
	var r := rng.randf_range(1.4, 2.2)
	mb.ellipsoid(cap, MeshBuilder.at(Vector3(0, h, 0)), Vector3(r, r * 0.55, r), 16, 8, Color.WHITE, 0.08, 1.0, rng.randi(), -0.15, 1.0)
	for i in 8:
		var a := rng.randf() * TAU
		var e := rng.randf_range(0.2, 0.8)
		var d := Vector3(cos(a) * cos(e) * r, sin(e) * r * 0.55, sin(a) * cos(e) * r)
		mb.ellipsoid(dots, MeshBuilder.at(Vector3(0, h, 0) + d), Vector3(0.14, 0.06, 0.14), 6, 3)
	return mb.commit()


## Kristallbaum (Mondhain / Himmelsbruch)
static func _crystal(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var col := Color.html("#7af0e0") if seed_v % 2 == 0 else Color.html("#b48aff")
	var cr := Mat.stylized(col, Mat.P.ICE, {"c2": col.darkened(0.5), "emis": col * 0.5, "rim": 0.5})
	for i in rng.randi_range(4, 7):
		var a := rng.randf() * TAU
		var tilt := rng.randf_range(0.0, 0.5)
		var len := rng.randf_range(1.2, 3.2)
		var xf := Transform3D(Basis(Vector3(cos(a + PI / 2), 0, sin(a + PI / 2)), tilt), Vector3(cos(a) * 0.3, 0, sin(a) * 0.3))
		mb.cylinder(cr, xf, 0.28, 0.0, len, 6, false, Color.WHITE, false)
	return mb.commit()


## Verkohlter Baum mit Glut (Aschenlande)
static func _ashtree(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var bark := Mat.stylized(Color.html("#2a2220"), Mat.P.LAVA, {"c2": Color.html("#100c0c"), "emis": Color.html("#ff4a10")})
	var h := rng.randf_range(3.0, 4.5)
	var top := _trunk(mb, bark, Vector3.ZERO, h, 0.3, 0.1, Vector3(rng.randf_range(-0.6, 0.6), 0, rng.randf_range(-0.6, 0.6)), 3, rng, true)
	for i in 4:
		var y := rng.randf_range(h * 0.5, h)
		var a := rng.randf() * TAU
		var from := Vector3(0, y, 0).lerp(top, y / h)
		var to := from + Vector3(cos(a) * 1.4, rng.randf_range(0.3, 1.2), sin(a) * 1.4)
		_branch(mb, bark, from, to, 0.08, 0.02)
	return mb.commit()


## Blütenweide (Himmelsbruch)
static func _skytree(theme: Dictionary, seed_v: int, lod: int) -> ArrayMesh:
	var rng := _rng(seed_v)
	var mb := MeshBuilder.new()
	var bark := Mat.stylized(Color.html("#a89080"), Mat.P.BARK, {"c2": Color.html("#5a4436")})
	var blossom_l := Color.html("#ffd0ec") if seed_v % 2 == 0 else Color.html("#fff2b0")
	var bl := Mat.foliage(blossom_l, blossom_l.darkened(0.45), Color.html("#ffffff"), false)
	var blc := Mat.foliage(blossom_l, blossom_l.darkened(0.45), Color.html("#ffffff"), true, {"density": 6.0})
	var h := rng.randf_range(3.5, 4.5)
	var top := _trunk(mb, bark, Vector3.ZERO, h, 0.3, 0.16, Vector3(rng.randf_range(-0.8, 0.8), 0, rng.randf_range(-0.8, 0.8)), 4, rng, true)
	var c := top + Vector3(0, 1.0, 0)
	for i in 5:
		var a := TAU * i / 5.0
		var p := c + Vector3(cos(a) * 1.5, rng.randf_range(-0.3, 0.5), sin(a) * 1.5)
		var r := rng.randf_range(1.2, 1.6)
		mb.ellipsoid(bl, MeshBuilder.at(p), Vector3(r, r * 0.75, r), 12 if lod == 0 else 6, 8 if lod == 0 else 4, Color(0.7, 1, 0, 1), 0.2, 1.0, rng.randi(), -1, 1, 0.5)
		if lod == 0:
			_leaf_cards(mb, blc, p, Vector3(r, r * 0.75, r), 5, rng, 1.0)
	mb.ellipsoid(bl, MeshBuilder.at(c + Vector3(0, 0.8, 0)), Vector3(1.6, 1.2, 1.6), 12, 8, Color(1, 1, 0, 1), 0.2, 1.0, rng.randi())
	return mb.commit()


const BUILDERS := {
	"tree": "_oak", "birch": "_birch", "pine": "_pine", "bush": "_bush", "deadtree": "_deadtree",
	"rock": "_rock", "flowers": "_flowers", "mushroom": "_mushroom", "crystal": "_crystal",
	"ashtree": "_ashtree", "skytree": "_skytree",
}


static func mesh_for(kind: String, theme_id: String, variant: int, lod: int) -> ArrayMesh:
	var key := "%s|%s|%d|%d" % [kind, theme_id, variant, lod]
	if _mesh_cache.has(key):
		return _mesh_cache[key]
	var theme := Themes.get_theme(theme_id)
	var sd := hash(kind) % 1000 + variant * 7919
	var mesh: ArrayMesh
	match kind:
		"tree": mesh = _oak(theme, sd, lod)
		"birch": mesh = _birch(theme, sd, lod)
		"pine": mesh = _pine(theme, sd, lod)
		"deadtree": mesh = _deadtree(theme, sd, lod)
		"rock": mesh = _rock(theme, sd, lod)
		"flowers": mesh = _flowers(theme, sd, lod)
		"mushroom": mesh = _mushroom(theme, sd, lod)
		"crystal": mesh = _crystal(theme, sd, lod)
		"ashtree": mesh = _ashtree(theme, sd, lod)
		"skytree": mesh = _skytree(theme, sd, lod)
		_: mesh = _bush(theme, sd, lod)
	_mesh_cache[key] = mesh
	return mesh


## Verteilt alle Vegetations-Requisiten einer Zone.
static func populate(parent: Node3D, props: Array, hf: Heightfield, theme_id: String) -> void:
	var groups := {}   # key -> Array[Transform3D]
	for p in props:
		var kind: String = p.get("t", "")
		if not BUILDERS.has(kind):
			continue
		var x := float(p["x"])
		var z := float(p["z"])
		var s := float(p.get("s", 1.0))
		var r := float(p.get("r", 0.0))
		var y := hf.height(x, z) if hf else 0.0
		if kind != "rock" and kind != "flowers":
			y -= 0.1
		var variant := int(abs(int(x * 13.0) ^ int(z * 7.0))) % VARIANTS
		var ck := Vector2i(int(floor(x / CHUNK)), int(floor(z / CHUNK)))
		var key := "%s|%d|%d|%d" % [kind, variant, ck.x, ck.y]
		if not groups.has(key):
			groups[key] = []
		var sc := Vector3(s, s, s)
		if kind == "rock":
			sc = Vector3(s, s * 0.9, s)
		groups[key].append([Transform3D(Basis(Vector3.UP, r) * Basis.from_scale(sc), Vector3(x, y, z)), hash(Vector2(x, z)) % 1000 / 1000.0])
	for key in groups:
		var parts: PackedStringArray = key.split("|")
		var kind := parts[0]
		var variant := int(parts[1])
		var items: Array = groups[key]
		var has_lod := kind in ["tree", "birch", "pine", "bush", "rock", "skytree"]
		for lod in (2 if has_lod else 1):
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_custom_data = true
			mm.mesh = mesh_for(kind, theme_id, variant, lod)
			mm.instance_count = items.size()
			for i in items.size():
				mm.set_instance_transform(i, items[i][0])
				mm.set_instance_custom_data(i, Color(items[i][1], fmod(items[i][1] * 7.31, 1.0), 0, 0))
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.name = "Veg_%s" % key
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if kind != "flowers" else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			if has_lod:
				if lod == 0:
					mmi.visibility_range_end = FAR_DIST
					mmi.visibility_range_end_margin = 10.0
					mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
				else:
					mmi.visibility_range_begin = FAR_DIST
					mmi.visibility_range_begin_margin = 10.0
					mmi.visibility_range_end = 420.0
					mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
			elif kind == "flowers":
				mmi.visibility_range_end = 70.0
			parent.add_child(mmi)
