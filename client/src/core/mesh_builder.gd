class_name MeshBuilder
extends RefCounted
## Baut prozedurale Meshes aus Grundformen zusammen.
## Pro Material entsteht eine Oberfläche; alle Formen werden über eine Transform platziert.
## UVs sind in Metern angelegt, damit die prozeduralen Muster überall gleich groß wirken.

var _tools: Dictionary = {}   # Material -> SurfaceTool
var _order: Array = []
var _aabb_valid := false


func _st(mat: Material) -> SurfaceTool:
	var st: SurfaceTool = _tools.get(mat)
	if st == null:
		st = SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		_tools[mat] = st
		_order.append(mat)
	return st


func is_empty() -> bool:
	return _order.is_empty()


## Ein Dreieck mit Normalen. Die Reihenfolge wird automatisch so gedreht, dass die Vorderseite
## in Richtung der (gemittelten) Normale zeigt (Godot: Vorderseite im Uhrzeigersinn).
func tri(mat: Material, a: Vector3, b: Vector3, c: Vector3, na: Vector3, nb: Vector3, nc: Vector3,
		uva := Vector2.ZERO, uvb := Vector2.ZERO, uvc := Vector2.ZERO,
		ca := Color.WHITE, cb := Color.WHITE, cc := Color.WHITE) -> void:
	var st := _st(mat)
	var face := (b - a).cross(c - a)
	if face.dot(na + nb + nc) > 0.0:
		# gegen den Uhrzeigersinn von der Normalen aus gesehen -> umdrehen
		var t := b; b = c; c = t
		var tn := nb; nb = nc; nc = tn
		var tu := uvb; uvb = uvc; uvc = tu
		var tc := cb; cb = cc; cc = tc
	st.set_normal(na); st.set_uv(uva); st.set_color(ca); st.add_vertex(a)
	st.set_normal(nb); st.set_uv(uvb); st.set_color(cb); st.add_vertex(b)
	st.set_normal(nc); st.set_uv(uvc); st.set_color(cc); st.add_vertex(c)


func quad(mat: Material, a: Vector3, b: Vector3, c: Vector3, d: Vector3, n: Vector3,
		uva := Vector2(0, 0), uvb := Vector2(1, 0), uvc := Vector2(1, 1), uvd := Vector2(0, 1),
		col := Color.WHITE) -> void:
	# a-b-c-d im Kreis
	tri(mat, a, b, c, n, n, n, uva, uvb, uvc, col, col, col)
	tri(mat, a, c, d, n, n, n, uva, uvc, uvd, col, col, col)


## Quader (zentriert) mit UVs in Metern.
func box(mat: Material, xf: Transform3D, size: Vector3, uv_scale := 1.0, col := Color.WHITE) -> void:
	var h := size * 0.5
	var corners := [
		Vector3(-h.x, -h.y, -h.z), Vector3(h.x, -h.y, -h.z), Vector3(h.x, h.y, -h.z), Vector3(-h.x, h.y, -h.z),
		Vector3(-h.x, -h.y, h.z), Vector3(h.x, -h.y, h.z), Vector3(h.x, h.y, h.z), Vector3(-h.x, h.y, h.z)]
	var faces := [
		[[4, 5, 6, 7], Vector3(0, 0, 1), Vector2(size.x, size.y)],
		[[1, 0, 3, 2], Vector3(0, 0, -1), Vector2(size.x, size.y)],
		[[5, 1, 2, 6], Vector3(1, 0, 0), Vector2(size.z, size.y)],
		[[0, 4, 7, 3], Vector3(-1, 0, 0), Vector2(size.z, size.y)],
		[[7, 6, 2, 3], Vector3(0, 1, 0), Vector2(size.x, size.z)],
		[[0, 1, 5, 4], Vector3(0, -1, 0), Vector2(size.x, size.z)]]
	var basis := xf.basis
	for f in faces:
		var idx: Array = f[0]
		var n: Vector3 = (basis * (f[1] as Vector3)).normalized()
		var uvs: Vector2 = f[2] * uv_scale
		var p0: Vector3 = xf * (corners[idx[0]] as Vector3)
		var p1: Vector3 = xf * (corners[idx[1]] as Vector3)
		var p2: Vector3 = xf * (corners[idx[2]] as Vector3)
		var p3: Vector3 = xf * (corners[idx[3]] as Vector3)
		quad(mat, p0, p1, p2, p3, n, Vector2(0, uvs.y), Vector2(uvs.x, uvs.y), Vector2(uvs.x, 0), Vector2(0, 0), col)


## Quader zwischen zwei Punkten (für Balken, Zaunlatten, Knochen ...).
func beam(mat: Material, from: Vector3, to: Vector3, thickness: Vector2, up_hint := Vector3.UP, col := Color.WHITE) -> void:
	var dir := to - from
	var length := dir.length()
	if length < 0.0001:
		return
	var y := dir / length
	var x := up_hint.cross(y)
	if x.length() < 0.01:
		x = Vector3.RIGHT.cross(y)
	x = x.normalized()
	var z := x.cross(y).normalized()
	var xf := Transform3D(Basis(x, y, z), (from + to) * 0.5)
	box(mat, xf, Vector3(thickness.x, length, thickness.y), 1.0, col)


## Ellipsoid bzw. Kugel mit optionaler Verbeulung (für Laub, Felsen, Körperteile).
## y_min/y_max (-1..1) schneiden die Kugel ab (Halbkugeln, Kuppeln).
func ellipsoid(mat: Material, xf: Transform3D, radii: Vector3, seg_u := 16, seg_v := 10,
		col := Color.WHITE, lump := 0.0, lump_freq := 1.5, lump_seed := 0, y_min := -1.0, y_max := 1.0,
		ao_bottom := 1.0) -> void:
	var noise: FastNoiseLite = null
	if lump > 0.0:
		noise = FastNoiseLite.new()
		noise.seed = lump_seed
		noise.frequency = lump_freq
		noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	var v_from := asin(clamp(y_min, -1.0, 1.0))
	var v_to := asin(clamp(y_max, -1.0, 1.0))
	var rows := seg_v + 1
	var cols := seg_u + 1
	var pos := PackedVector3Array()
	pos.resize(rows * cols)
	var dirs := PackedVector3Array()
	dirs.resize(rows * cols)
	for j in rows:
		var phi := lerpf(v_from, v_to, float(j) / seg_v)
		for i in cols:
			var th := TAU * float(i % seg_u) / seg_u
			var d := Vector3(cos(phi) * cos(th), sin(phi), cos(phi) * sin(th))
			var p := Vector3(d.x * radii.x, d.y * radii.y, d.z * radii.z)
			if noise:
				var nn := noise.get_noise_3dv(d * 2.0)
				p += d * nn * lump * radii.length() * 0.577
			pos[j * cols + i] = p
			dirs[j * cols + i] = d
	# Normalen aus dem Gitter
	var nrm := PackedVector3Array()
	nrm.resize(rows * cols)
	for j in rows:
		for i in cols:
			var p: Vector3 = pos[j * cols + i]
			var pu: Vector3 = pos[j * cols + (i + 1) % seg_u] if i < seg_u else pos[j * cols + 1]
			var pd: Vector3 = pos[j * cols + (i - 1 + seg_u) % seg_u]
			var pn: Vector3 = pos[min(j + 1, rows - 1) * cols + i]
			var ps: Vector3 = pos[max(j - 1, 0) * cols + i]
			var n := (pu - pd).cross(pn - ps)
			if n.length() < 0.000001 or j == 0 or j == rows - 1:
				var d: Vector3 = dirs[j * cols + i]
				n = Vector3(d.x / max(radii.x, 0.001), d.y / max(radii.y, 0.001), d.z / max(radii.z, 0.001))
			n = n.normalized()
			if n.dot(dirs[j * cols + i]) < 0.0:
				n = -n
			nrm[j * cols + i] = n
	var basis := xf.basis
	var circ := TAU * (radii.x + radii.z) * 0.5
	var height := PI * radii.y
	for j in seg_v:
		for i in seg_u:
			var i0 := j * cols + i
			var i1 := j * cols + i + 1
			var i2 := (j + 1) * cols + i + 1
			var i3 := (j + 1) * cols + i
			var ids := [i0, i1, i2, i3]
			var pts := []
			var ns := []
			var uvs := []
			var cs := []
			for k in ids:
				pts.append(xf * pos[k])
				ns.append((basis * nrm[k]).normalized())
				var u := float(k % cols) / seg_u
				var v := float(k / cols) / seg_v
				uvs.append(Vector2(u * circ, (1.0 - v) * height))
				var ao := lerpf(ao_bottom, 1.0, clamp(dirs[k].y * 0.5 + 0.5, 0.0, 1.0))
				cs.append(Color(col.r * ao, col.g, col.b, col.a) if ao_bottom != 1.0 else col)
			tri(mat, pts[0], pts[1], pts[2], ns[0], ns[1], ns[2], uvs[0], uvs[1], uvs[2], cs[0], cs[1], cs[2])
			tri(mat, pts[0], pts[2], pts[3], ns[0], ns[2], ns[3], uvs[0], uvs[2], uvs[3], cs[0], cs[2], cs[3])


## Zylinder/Kegelstumpf entlang +Y (Fuß bei y=0).
func cylinder(mat: Material, xf: Transform3D, r_bottom: float, r_top: float, height: float, seg := 12,
		caps := true, col := Color.WHITE, smooth := true, col_top := Color(-1, 0, 0)) -> void:
	var basis := xf.basis
	var slope = (r_bottom - r_top) / max(height, 0.0001)
	var circ = TAU * max(r_bottom, r_top)
	var ctop := col if col_top.r < 0.0 else col_top
	for i in seg:
		var a0 := TAU * i / seg
		var a1 := TAU * (i + 1) / seg
		var d0 := Vector3(cos(a0), 0, sin(a0))
		var d1 := Vector3(cos(a1), 0, sin(a1))
		var b0 := xf * (d0 * r_bottom)
		var b1 := xf * (d1 * r_bottom)
		var t0 := xf * (d0 * r_top + Vector3(0, height, 0))
		var t1 := xf * (d1 * r_top + Vector3(0, height, 0))
		var n0: Vector3
		var n1: Vector3
		if smooth:
			n0 = (basis * (d0 + Vector3(0, slope, 0))).normalized()
			n1 = (basis * (d1 + Vector3(0, slope, 0))).normalized()
		else:
			var dm := (d0 + d1).normalized()
			n0 = (basis * (dm + Vector3(0, slope, 0))).normalized()
			n1 = n0
		var u0 = circ * i / seg
		var u1 = circ * (i + 1) / seg
		tri(mat, b0, b1, t1, n0, n1, n1, Vector2(u0, height), Vector2(u1, height), Vector2(u1, 0), col, col, ctop)
		tri(mat, b0, t1, t0, n0, n1, n0, Vector2(u0, height), Vector2(u1, 0), Vector2(u0, 0), col, ctop, ctop)
		if caps:
			var up := (basis * Vector3.UP).normalized()
			if r_top > 0.0001:
				var ct := xf * Vector3(0, height, 0)
				tri(mat, ct, t0, t1, up, up, up, Vector2.ZERO, Vector2(d0.x, d0.z) * r_top, Vector2(d1.x, d1.z) * r_top, ctop, ctop, ctop)
			if r_bottom > 0.0001:
				var cb := xf * Vector3.ZERO
				tri(mat, cb, b1, b0, -up, -up, -up, Vector2.ZERO, Vector2(d1.x, d1.z) * r_bottom, Vector2(d0.x, d0.z) * r_bottom, col, col, col)


## Gliedmaße: Kapsel mit zwei Radien entlang -Y (vom Gelenk nach unten), abgerundete Enden.
func limb(mat: Material, xf: Transform3D, r_top: float, r_bottom: float, length: float, seg := 10, col := Color.WHITE) -> void:
	var rings := 6
	var basis := xf.basis
	var profile := []   # [y, r, normal_y]
	# obere Halbkugel
	for k in range(rings, -1, -1):
		var a := PI * 0.5 * float(k) / rings
		profile.append([sin(a) * r_top, cos(a) * r_top, sin(a)])
	# Schaft
	profile.append([-length, r_bottom, 0.0])
	for k in range(1, rings + 1):
		var a := PI * 0.5 * float(k) / rings
		profile.append([-length - sin(a) * r_bottom, cos(a) * r_bottom, -sin(a)])
	var circ = TAU * max(r_top, r_bottom)
	for j in profile.size() - 1:
		var p0: Array = profile[j]
		var p1: Array = profile[j + 1]
		for i in seg:
			var a0 := TAU * i / seg
			var a1 := TAU * (i + 1) / seg
			var d0 := Vector3(cos(a0), 0, sin(a0))
			var d1 := Vector3(cos(a1), 0, sin(a1))
			var q00 = xf * (d0 * p0[1] + Vector3(0, p0[0], 0))
			var q10 = xf * (d1 * p0[1] + Vector3(0, p0[0], 0))
			var q01 = xf * (d0 * p1[1] + Vector3(0, p1[0], 0))
			var q11 = xf * (d1 * p1[1] + Vector3(0, p1[0], 0))
			var cy0: float = sqrt(max(0.0, 1.0 - p0[2] * p0[2]))
			var cy1: float = sqrt(max(0.0, 1.0 - p1[2] * p1[2]))
			var n00 := (basis * (d0 * cy0 + Vector3(0, p0[2], 0))).normalized()
			var n10 := (basis * (d1 * cy0 + Vector3(0, p0[2], 0))).normalized()
			var n01 := (basis * (d0 * cy1 + Vector3(0, p1[2], 0))).normalized()
			var n11 := (basis * (d1 * cy1 + Vector3(0, p1[2], 0))).normalized()
			if (q00 - q10).length_squared() < 1e-10 and (q01 - q11).length_squared() < 1e-10:
				continue
			var u0 = circ * i / seg
			var u1 = circ * (i + 1) / seg
			var v0: float = -p0[0]
			var v1: float = -p1[0]
			if (q00 - q10).length_squared() > 1e-10:
				tri(mat, q00, q10, q11, n00, n10, n11, Vector2(u0, v0), Vector2(u1, v0), Vector2(u1, v1), col, col, col)
			if (q01 - q11).length_squared() > 1e-10:
				tri(mat, q00, q11, q01, n00, n11, n01, Vector2(u0, v0), Vector2(u1, v1), Vector2(u0, v1), col, col, col)


## Torus (Ringe, Gürtel, Kronen) in der XZ-Ebene.
func torus(mat: Material, xf: Transform3D, radius: float, tube: float, seg := 16, seg_t := 6, col := Color.WHITE) -> void:
	var basis := xf.basis
	for i in seg:
		var a0 := TAU * i / seg
		var a1 := TAU * (i + 1) / seg
		for j in seg_t:
			var b0 := TAU * j / seg_t
			var b1 := TAU * (j + 1) / seg_t
			var pts := []
			var ns := []
			for ab in [[a0, b0], [a1, b0], [a1, b1], [a0, b1]]:
				var a: float = ab[0]
				var b: float = ab[1]
				var c := Vector3(cos(a), 0, sin(a))
				var n := c * cos(b) + Vector3(0, sin(b), 0)
				pts.append(xf * (c * radius + n * tube))
				ns.append((basis * n).normalized())
			tri(mat, pts[0], pts[1], pts[2], ns[0], ns[1], ns[2], Vector2(a0 * radius, b0 * tube), Vector2(a1 * radius, b0 * tube), Vector2(a1 * radius, b1 * tube), col, col, col)
			tri(mat, pts[0], pts[2], pts[3], ns[0], ns[2], ns[3], Vector2(a0 * radius, b0 * tube), Vector2(a1 * radius, b1 * tube), Vector2(a0 * radius, b1 * tube), col, col, col)


## Satteldach (Prisma) über einer Grundfläche w x d, First entlang X. Ursprung = Traufmitte unten.
func gable_roof(mat: Material, xf: Transform3D, w: float, d: float, h: float, overhang := 0.4,
		thickness := 0.18, gable_mat: Material = null, col := Color.WHITE) -> void:
	var hw := w * 0.5 + overhang
	var hd := d * 0.5 + overhang
	var basis := xf.basis
	var ridge_l := Vector3(-hw, h + overhang * h / (d * 0.5), 0)
	var ridge_r := Vector3(hw, h + overhang * h / (d * 0.5), 0)
	var eave_fl := Vector3(-hw, 0, hd)
	var eave_fr := Vector3(hw, 0, hd)
	var eave_bl := Vector3(-hw, 0, -hd)
	var eave_br := Vector3(hw, 0, -hd)
	var slope_len := Vector2(hd, ridge_l.y).length()
	var nf := (basis * Vector3(0, hd, ridge_l.y).normalized()).normalized()
	var nb := (basis * Vector3(0, hd, -ridge_l.y).normalized()).normalized()
	quad(mat, xf * eave_fl, xf * eave_fr, xf * ridge_r, xf * ridge_l, nf,
		Vector2(0, slope_len), Vector2(hw * 2, slope_len), Vector2(hw * 2, 0), Vector2(0, 0), col)
	quad(mat, xf * eave_br, xf * eave_bl, xf * ridge_l, xf * ridge_r, nb,
		Vector2(0, slope_len), Vector2(hw * 2, slope_len), Vector2(hw * 2, 0), Vector2(0, 0), col)
	# Unterseite (Dachstärke)
	var t := Vector3(0, -thickness, 0)
	var nfd := -nf
	var nbd := -nb
	quad(mat, xf * (eave_fl + t), xf * (ridge_l + t), xf * (ridge_r + t), xf * (eave_fr + t), nfd)
	quad(mat, xf * (eave_br + t), xf * (ridge_r + t), xf * (ridge_l + t), xf * (eave_bl + t), nbd)
	# Traufkanten
	var ndown := (basis * Vector3(0, 0, 1)).normalized()
	quad(mat, xf * eave_fl, xf * (eave_fl + t), xf * (eave_fr + t), xf * eave_fr, ndown)
	quad(mat, xf * eave_bl, xf * eave_br, xf * (eave_br + t), xf * (eave_bl + t), -ndown)
	# Giebeldreiecke (Wand)
	if gable_mat:
		var gw := w * 0.5
		var gd := d * 0.5
		for sx in [-1.0, 1.0]:
			var n := (basis * Vector3(sx, 0, 0)).normalized()
			var a := xf * Vector3(sx * gw, 0, gd)
			var b := xf * Vector3(sx * gw, 0, -gd)
			var c := xf * Vector3(sx * gw, h, 0)
			tri(gable_mat, a, b, c, n, n, n, Vector2(0, h), Vector2(d, h), Vector2(d * 0.5, 0))


## Kegeldach (Türme) – Ursprung unten Mitte.
func cone_roof(mat: Material, xf: Transform3D, radius: float, h: float, seg := 16, col := Color.WHITE) -> void:
	cylinder(mat, xf, radius, 0.0, h, seg, true, col, true)


## Flache Scheibe in XZ (Bodenplatten, Teiche, Untersetzer)
func disc(mat: Material, xf: Transform3D, radius: float, seg := 24, col := Color.WHITE) -> void:
	var up := (xf.basis * Vector3.UP).normalized()
	var c := xf * Vector3.ZERO
	for i in seg:
		var a0 := TAU * i / seg
		var a1 := TAU * (i + 1) / seg
		var p0 := xf * Vector3(cos(a0) * radius, 0, sin(a0) * radius)
		var p1 := xf * Vector3(cos(a1) * radius, 0, sin(a1) * radius)
		tri(mat, c, p0, p1, up, up, up, Vector2.ZERO, Vector2(cos(a0), sin(a0)) * radius, Vector2(cos(a1), sin(a1)) * radius, col, col, col)


## Doppelseitige Fläche (Banner, Umhang, Blattkarte) in der XY-Ebene, oben y=0 bis y=-h.
func plane(mat: Material, xf: Transform3D, w: float, h: float, col := Color.WHITE, segs_y := 1, curve := 0.0) -> void:
	var basis := xf.basis
	var n := (basis * Vector3(0, 0, 1)).normalized()
	for k in segs_y:
		var y0 := -h * float(k) / segs_y
		var y1 := -h * float(k + 1) / segs_y
		var z0 := curve * pow(float(k) / segs_y, 2.0)
		var z1 := curve * pow(float(k + 1) / segs_y, 2.0)
		var a := xf * Vector3(-w * 0.5, y0, z0)
		var b := xf * Vector3(w * 0.5, y0, z0)
		var c := xf * Vector3(w * 0.5, y1, z1)
		var d := xf * Vector3(-w * 0.5, y1, z1)
		var v0 := float(k) / segs_y
		var v1 := float(k + 1) / segs_y
		quad(mat, a, b, c, d, n, Vector2(0, v0), Vector2(1, v0), Vector2(1, v1), Vector2(0, v1), col)
		quad(mat, b, a, d, c, -n, Vector2(1, v0), Vector2(0, v0), Vector2(0, v1), Vector2(1, v1), col)


## Beliebiges Prisma aus einem 2D-Umriss (XZ) mit Höhe h (Schwerter, Äxte, Abzeichen ...)
func extrude(mat: Material, xf: Transform3D, outline: PackedVector2Array, depth: float, col := Color.WHITE) -> void:
	var basis := xf.basis
	var hz := depth * 0.5
	var n_front := (basis * Vector3(0, 0, 1)).normalized()
	var center := Vector2.ZERO
	for p in outline:
		center += p
	center /= max(1, outline.size())
	var cf := xf * Vector3(center.x, center.y, hz)
	var cb := xf * Vector3(center.x, center.y, -hz)
	var cnt := outline.size()
	for i in cnt:
		var p0 := outline[i]
		var p1 := outline[(i + 1) % cnt]
		var f0 := xf * Vector3(p0.x, p0.y, hz)
		var f1 := xf * Vector3(p1.x, p1.y, hz)
		var b0 := xf * Vector3(p0.x, p0.y, -hz)
		var b1 := xf * Vector3(p1.x, p1.y, -hz)
		tri(mat, cf, f0, f1, n_front, n_front, n_front, center, p0, p1, col, col, col)
		tri(mat, cb, b1, b0, -n_front, -n_front, -n_front, center, p1, p0, col, col, col)
		var e := p1 - p0
		var side := (basis * Vector3(e.y, -e.x, 0)).normalized()
		if side.dot(xf * Vector3((p0.x + p1.x) * 0.5, (p0.y + p1.y) * 0.5, 0) - xf * Vector3(center.x, center.y, 0)) < 0:
			side = -side
		quad(mat, f0, f1, b1, b0, side, Vector2(0, 0), Vector2(e.length(), 0), Vector2(e.length(), depth), Vector2(0, depth), col)


## Fertiges Mesh erzeugen.
func commit(existing: ArrayMesh = null) -> ArrayMesh:
	var mesh := existing if existing else ArrayMesh.new()
	for mat in _order:
		var st: SurfaceTool = _tools[mat]
		var before := mesh.get_surface_count()
		st.commit(mesh)
		if mesh.get_surface_count() > before:
			mesh.surface_set_material(mesh.get_surface_count() - 1, mat)
	_tools.clear()
	_order.clear()
	return mesh


## Hilfen für Transforms
static func at(pos: Vector3, rot_y := 0.0, scale := Vector3.ONE) -> Transform3D:
	return Transform3D(Basis(Vector3.UP, rot_y) * Basis.from_scale(scale), pos)


static func at_euler(pos: Vector3, euler: Vector3, scale := Vector3.ONE) -> Transform3D:
	return Transform3D(Basis.from_euler(euler) * Basis.from_scale(scale), pos)
