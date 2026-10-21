class_name CreatureModel
extends Node3D
## Prozedurale Kreaturen: Vierbeiner (Wolf, Eber, Bär, Pferd, Hase ...), Spinnen, Vögel,
## Drachen, Golems, Elementare, Baumwesen, Geister und mehr. Gleiche Animations-Schnittstelle
## wie HumanoidModel (speed, combat, casting, attack(), set_dead() ...).

var species := "wolf"
var look: Dictionary = {}
var speed := 0.0
var move_dir := Vector2(0, -1)
var airborne := false
var combat := false
var casting := false
var channeling := false
var cast_color := Color(1, 0.5, 0.2)
var dead := false
var sitting := false
var mounted := false
var emote := ""
var phase := 0.0
var _t := 0.0
var _attack_t := -1.0
var _hit_t := -1.0
var _death_t := 0.0
var _height := 1.0

# Gelenke (je nach Bauplan)
var root_body: Node3D
var head: Node3D
var jaw: Node3D
var neck_segs: Array = []
var tail_segs: Array = []
var legs: Array = []          # [hip, knee, phase_offset, side]
var wings: Array = []
var arms: Array = []          # [shoulder, elbow, side]
var extra: Array = []
var _base_y := 0.0
var _fx_mouth: Node3D


func _init(p_species := "wolf", p_look: Dictionary = {}) -> void:
	species = p_species
	look = p_look


func _ready() -> void:
	if root_body == null:
		build()


func _c(key: String, def: String) -> Color:
	var v = look.get(key)
	if v == null or str(v) == "":
		return Color.html(def)
	return Color.html(str(v))


func _n(n: String, parent: Node3D, pos: Vector3) -> Node3D:
	var x := Node3D.new()
	x.name = n
	x.position = pos
	parent.add_child(x)
	return x


func _add(parent: Node3D, mb: MeshBuilder, shadow := true) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mb.commit()
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	return mi


func build() -> void:
	for c in get_children():
		c.queue_free()
	legs.clear()
	wings.clear()
	arms.clear()
	neck_segs.clear()
	tail_segs.clear()
	var alias := {"wolf_mount": "worg", "moth": "bird", "gryphon": "bird", "lizard": "drake", "yeti": "bear", "salamander": "drake"}
	if alias.has(species):
		if species == "wolf_mount":
			scale = Vector3.ONE * 1.35
		elif species == "gryphon":
			scale = Vector3.ONE * 2.2
		species = alias[species]
	match species:
		"wolf", "hellhound", "worg", "fox":
			_quadruped({"len": 1.15, "h": 0.78, "leg_r": 0.07, "head": 0.24, "snout": 0.3, "ears": "pointy", "tail": "bushy",
				"fur": _c("tint", "#8a8a8a" if species != "hellhound" else "#2a1a18").to_html(), "fur2": _c("tint2", "#d8d0c4" if species != "hellhound" else "#ff5a10").to_html(),
				"eyes": "#ffd040" if species != "hellhound" else "#ff6010", "fire": species == "hellhound"})
		"boar":
			_quadruped({"len": 1.0, "h": 0.62, "leg_r": 0.07, "head": 0.27, "snout": 0.22, "ears": "small", "tail": "thin",
				"fur": _c("tint", "#6a4a32").to_html(), "fur2": _c("tint2", "#3a2618").to_html(), "eyes": "#1a0a0a", "tusks": true, "bristle": true, "girth": 1.35})
		"bear":
			_quadruped({"len": 1.6, "h": 1.05, "leg_r": 0.13, "head": 0.32, "snout": 0.2, "ears": "round", "tail": "stub",
				"fur": _c("tint", "#5a3e2a").to_html(), "fur2": _c("tint2", "#3a2416").to_html(), "eyes": "#1a0a0a", "girth": 1.4})
		"horse", "mount_horse":
			_quadruped({"len": 1.7, "h": 1.45, "leg_r": 0.07, "head": 0.25, "snout": 0.42, "ears": "pointy", "tail": "long", "neck": 0.7,
				"fur": _c("tint", "#8a5a32").to_html(), "fur2": _c("tint2", "#2a1a10").to_html(), "eyes": "#1a0a0a", "mane": true, "saddle": look.get("saddle", false)})
		"stag", "ram":
			_quadruped({"len": 1.2, "h": 1.05, "leg_r": 0.055, "head": 0.2, "snout": 0.24, "ears": "pointy", "tail": "stub", "neck": 0.4,
				"fur": _c("tint", "#a07040" if species == "stag" else "#d8d0c0").to_html(), "fur2": _c("tint2", "#f0e8d8").to_html(),
				"eyes": "#1a0a0a", "antlers": species == "stag", "horns": species == "ram", "glow": look.get("glow")})
		"rabbit":
			_quadruped({"len": 0.32, "h": 0.22, "leg_r": 0.03, "head": 0.1, "snout": 0.05, "ears": "rabbit", "tail": "puff",
				"fur": _c("tint", "#a08a70").to_html(), "fur2": _c("tint2", "#f0e8e0").to_html(), "eyes": "#1a0a0a", "hop": true})
		"cat", "lynx", "panther":
			_quadruped({"len": 1.1, "h": 0.65, "leg_r": 0.06, "head": 0.2, "snout": 0.1, "ears": "pointy", "tail": "long_thin",
				"fur": _c("tint", "#3a3040").to_html(), "fur2": _c("tint2", "#6a6070").to_html(), "eyes": "#a0ff60"})
		"spider":
			_spider()
		"chicken", "owl", "vulture", "bird":
			_bird()
		"dragon", "drake", "whelp":
			_dragon()
		"golem", "forge_golem", "ice_golem", "crystal_golem", "mech":
			_golem()
		"fire_elemental", "ice_elemental", "earth_elemental", "air_elemental", "wisp", "arcane_elemental":
			_elemental()
		"treant":
			_treant()
		"ghost", "wraith":
			_ghost()
		"slime":
			_slime()
		"dummy":
			_dummy()
		_:
			_quadruped({"len": 1.0, "h": 0.7, "leg_r": 0.07, "head": 0.22, "snout": 0.2, "ears": "pointy", "tail": "thin",
				"fur": "#7a6a5a", "fur2": "#b0a090", "eyes": "#ffd040"})


# =============================================================================== Vierbeiner
func _quadruped(o: Dictionary) -> void:
	var fur := Mat.stylized(Color.html(o.fur), Mat.P.FUR, {"c2": Color.html(o.fur).darkened(0.45), "rim": 0.22})
	var fur2 := Mat.stylized(Color.html(o.fur2), Mat.P.FUR, {"c2": Color.html(o.fur2).darkened(0.3)})
	var dark := Mat.stylized(Color.html("#141010"), Mat.P.PLAIN)
	var eye = Mat.emissive(Color.html(o.eyes), 1.5) if o.eyes != "#1a0a0a" else Mat.stylized(Color.html("#100808"), Mat.P.PLAIN, {"rough": 0.2, "rim": 0.6})
	var L: float = o.len
	var H: float = o.h
	var girth: float = o.get("girth", 1.0)
	_height = H * 1.3
	var leg_len := H * 0.72
	var leg_r: float = o.leg_r
	root_body = _n("Body", self, Vector3(0, H * 0.82, 0))
	_base_y = root_body.position.y
	var mb := MeshBuilder.new()
	# Rumpf: Brustpartie vorn kräftiger
	mb.ellipsoid(fur, MeshBuilder.at(Vector3(0, 0, -L * 0.18)), Vector3(H * 0.26 * girth, H * 0.3 * girth, L * 0.36), 14, 9, Color.WHITE, 0.06, 2.0, 1)
	mb.ellipsoid(fur, MeshBuilder.at(Vector3(0, -H * 0.02, L * 0.22)), Vector3(H * 0.23 * girth, H * 0.25 * girth, L * 0.32), 14, 9, Color.WHITE, 0.06, 2.0, 2)
	mb.ellipsoid(fur2, MeshBuilder.at(Vector3(0, -H * 0.16 * girth, -L * 0.1)), Vector3(H * 0.18 * girth, H * 0.14, L * 0.36), 10, 6)
	if o.get("bristle", false):
		for k in 7:
			mb.cylinder(Mat.stylized(Color.html(o.fur2), Mat.P.FUR), MeshBuilder.at_euler(Vector3(0, H * 0.27 * girth, -L * 0.35 + k * L * 0.1), Vector3(0.3, 0, 0)), 0.05, 0.0, 0.16, 4)
	if o.get("mane", false):
		pass
	if o.get("saddle", false):
		var leather := Mat.stylized(Color.html("#5a3218"), Mat.P.LEATHER)
		mb.ellipsoid(leather, MeshBuilder.at(Vector3(0, H * 0.27, -0.05)), Vector3(H * 0.27, 0.08, L * 0.22), 12, 6, Color.WHITE, 0, 1, 0, -0.2, 1.0)
		var cloth := Mat.stylized(Color.html(str(look.get("blanket", "#8f1d2c"))), Mat.P.CLOTH)
		mb.ellipsoid(cloth, MeshBuilder.at(Vector3(0, H * 0.22, -0.05)), Vector3(H * 0.29, 0.1, L * 0.26), 12, 6, Color.WHITE, 0, 1, 0, -0.4, 0.6)
	_add(root_body, mb)
	# Hals & Kopf
	var neck_len: float = o.get("neck", 0.25)
	var neck_n := _n("Neck", root_body, Vector3(0, H * 0.12, -L * 0.45))
	neck_n.rotation.x = -0.5 if neck_len > 0.5 else -0.2
	mb = MeshBuilder.new()
	mb.limb(fur, MeshBuilder.at_euler(Vector3.ZERO, Vector3(PI * 0.5 + 0.0, 0, 0)), H * 0.16 * girth, H * 0.13 * girth, neck_len, 10)
	if o.get("mane", false):
		var mane := Mat.stylized(Color.html(o.fur2), Mat.P.FUR)
		for k in 6:
			mb.ellipsoid(mane, MeshBuilder.at(Vector3(0, H * 0.12, -neck_len * k / 6.0)), Vector3(0.05, 0.14, 0.1), 6, 4)
	_add(neck_n, mb)
	head = _n("Head", neck_n, Vector3(0, 0, -neck_len))
	head.rotation.x = 0.5 if neck_len > 0.5 else 0.2
	neck_segs = [neck_n]
	var hr: float = o.head
	var sn: float = o.snout
	mb = MeshBuilder.new()
	mb.ellipsoid(fur, MeshBuilder.at(Vector3(0, 0, -hr * 0.3)), Vector3(hr * 0.85, hr * 0.8, hr), 12, 8)
	mb.ellipsoid(fur, MeshBuilder.at(Vector3(0, -hr * 0.2, -hr - sn * 0.4)), Vector3(hr * 0.48, hr * 0.42, sn * 0.9 + 0.02), 10, 7)
	mb.ellipsoid(dark, MeshBuilder.at(Vector3(0, -hr * 0.05, -hr - sn * 1.2)), Vector3(hr * 0.2, hr * 0.15, hr * 0.12), 6, 4)
	for sx in [-1.0, 1.0]:
		mb.ellipsoid(eye, MeshBuilder.at(Vector3(sx * hr * 0.42, hr * 0.15, -hr * 0.95)), Vector3(hr * 0.12, hr * 0.12, hr * 0.08), 6, 5)
		match str(o.ears):
			"pointy":
				mb.cylinder(fur, MeshBuilder.at_euler(Vector3(sx * hr * 0.45, hr * 0.6, -hr * 0.25), Vector3(-0.2, 0, sx * -0.3)), hr * 0.22, 0.0, hr * 0.6, 6)
			"round":
				mb.ellipsoid(fur, MeshBuilder.at(Vector3(sx * hr * 0.55, hr * 0.62, -hr * 0.15)), Vector3(hr * 0.2, hr * 0.2, hr * 0.1), 8, 5)
			"small":
				mb.ellipsoid(fur, MeshBuilder.at_euler(Vector3(sx * hr * 0.55, hr * 0.5, -hr * 0.1), Vector3(0, 0, sx * -0.8)), Vector3(hr * 0.2, hr * 0.08, hr * 0.15), 8, 5)
			"rabbit":
				mb.ellipsoid(fur, MeshBuilder.at_euler(Vector3(sx * hr * 0.3, hr * 1.3, hr * 0.0), Vector3(0.2, 0, sx * -0.2)), Vector3(hr * 0.22, hr * 0.9, hr * 0.12), 8, 6)
		if o.get("tusks", false):
			mb.cylinder(Mat.stylized(Color.html("#f0e6d0"), Mat.P.BONE), MeshBuilder.at_euler(Vector3(sx * hr * 0.35, -hr * 0.35, -hr - sn * 0.6), Vector3(-0.4, 0, sx * -0.5)), hr * 0.08, 0.0, hr * 0.5, 5)
		if o.get("antlers", false):
			var bone := Mat.stylized(Color.html("#d8c8a8"), Mat.P.BONE)
			var base := Vector3(sx * hr * 0.35, hr * 0.7, -hr * 0.3)
			var tip := base + Vector3(sx * 0.35, 0.55, 0.1)
			mb.beam(bone, base, tip, Vector2(0.035, 0.035))
			mb.beam(bone, base.lerp(tip, 0.4), base.lerp(tip, 0.4) + Vector3(sx * 0.05, 0.25, -0.15), Vector2(0.025, 0.025))
			mb.beam(bone, base.lerp(tip, 0.75), base.lerp(tip, 0.75) + Vector3(sx * 0.2, 0.15, 0.0), Vector2(0.025, 0.025))
		if o.get("horns", false):
			var horn := Mat.stylized(Color.html("#b0a080"), Mat.P.BONE)
			mb.torus(horn, MeshBuilder.at_euler(Vector3(sx * hr * 0.6, hr * 0.35, -hr * 0.2), Vector3(0, 0, PI * 0.5)), hr * 0.35, hr * 0.12, 10, 5)
	if o.get("glow") != null:
		var gm := Mat.emissive(Color.html(str(o.glow)), 2.0)
		mb.ellipsoid(gm, MeshBuilder.at(Vector3(0, hr * 0.6, -hr * 0.6)), Vector3(hr * 0.12, hr * 0.12, hr * 0.12), 6, 4)
	_add(head, mb)
	jaw = _n("Jaw", head, Vector3(0, -hr * 0.4, -hr))
	mb = MeshBuilder.new()
	mb.ellipsoid(fur, MeshBuilder.at(Vector3(0, 0, -sn * 0.4)), Vector3(hr * 0.38, hr * 0.12, sn * 0.75 + 0.01), 8, 5)
	_add(jaw, mb)
	if o.get("fire", false):
		var f := FxLib.fire(0.25, Color(1.0, 0.45, 0.1), false)
		f.position = Vector3(0, -hr * 0.3, -hr - sn)
		head.add_child(f)
		var f2 := FxLib.fire(0.4, Color(1.0, 0.45, 0.1), false)
		f2.position = Vector3(0, H * 0.25, 0)
		root_body.add_child(f2)
	# Beine
	var offs := [[-1, -1, 0.0], [1, -1, PI], [-1, 1, PI], [1, 1, 0.0]]
	for o2 in offs:
		var sx: float = o2[0]
		var sz: float = o2[1]
		var hip := _n("Leg", root_body, Vector3(sx * H * 0.17 * girth, -H * 0.08, sz * L * 0.38))
		mb = MeshBuilder.new()
		mb.limb(fur, MeshBuilder.at(Vector3.ZERO), leg_r * 1.6 * (1.2 if sz > 0 else 1.0), leg_r * 1.1, leg_len * 0.5, 8)
		_add(hip, mb)
		var knee := _n("Knee", hip, Vector3(0, -leg_len * 0.5, 0))
		mb = MeshBuilder.new()
		mb.limb(fur, MeshBuilder.at(Vector3.ZERO), leg_r * 1.05, leg_r * 0.85, leg_len * 0.5 - 0.02, 8)
		mb.ellipsoid(fur2 if species != "hellhound" else dark, MeshBuilder.at(Vector3(0, -leg_len * 0.5 + 0.01, -leg_r * 0.4)), Vector3(leg_r * 1.15, leg_r * 0.7, leg_r * 1.5), 8, 5)
		_add(knee, mb)
		legs.append([hip, knee, o2[2], sx, sz])
	# Schwanz
	var tail_n := _n("Tail", root_body, Vector3(0, H * 0.08, L * 0.52))
	mb = MeshBuilder.new()
	match str(o.tail):
		"bushy":
			mb.ellipsoid(fur, MeshBuilder.at_euler(Vector3(0, -0.12, 0.25), Vector3(-0.9, 0, 0)), Vector3(0.09, 0.3, 0.09), 8, 6, Color.WHITE, 0.15, 2.0, 3)
		"long":
			mb.ellipsoid(Mat.stylized(Color.html(o.fur2), Mat.P.FUR), MeshBuilder.at_euler(Vector3(0, -0.35, 0.18), Vector3(-0.35, 0, 0)), Vector3(0.08, 0.45, 0.08), 8, 6)
		"long_thin":
			mb.limb(fur, MeshBuilder.at_euler(Vector3.ZERO, Vector3(-1.9, 0, 0)), 0.04, 0.03, 0.7, 6)
		"puff":
			mb.ellipsoid(fur2, MeshBuilder.at(Vector3(0, 0, 0.03)), Vector3(0.05, 0.05, 0.05), 6, 4)
		"stub":
			mb.ellipsoid(fur, MeshBuilder.at(Vector3(0, 0, 0.04)), Vector3(0.06, 0.06, 0.08), 6, 4)
		_:
			mb.limb(fur, MeshBuilder.at_euler(Vector3.ZERO, Vector3(-2.2, 0, 0)), 0.03, 0.015, 0.3, 6)
	_add(tail_n, mb)
	tail_segs = [tail_n]
	if o.get("hop", false):
		extra.append("hop")


# =============================================================================== Spinne
func _spider() -> void:
	var col := _c("tint", "#3a2a26")
	var s := Mat.stylized(col, Mat.P.FUR, {"c2": col.darkened(0.6), "rim": 0.3})
	var mark := Mat.stylized(_c("tint2", "#a02020"), Mat.P.PLAIN, {"rim": 0.4})
	var eye := Mat.emissive(_c("eyes", "#ff3020"), 2.0)
	_height = 0.9
	root_body = _n("Body", self, Vector3(0, 0.55, 0))
	_base_y = 0.55
	var mb := MeshBuilder.new()
	mb.ellipsoid(s, MeshBuilder.at(Vector3(0, 0.12, 0.45)), Vector3(0.48, 0.42, 0.55), 14, 9, Color.WHITE, 0.08, 2.0, 1)
	mb.ellipsoid(mark, MeshBuilder.at(Vector3(0, 0.45, 0.45)), Vector3(0.18, 0.12, 0.28), 8, 5)
	mb.ellipsoid(s, MeshBuilder.at(Vector3(0, 0, -0.15)), Vector3(0.3, 0.24, 0.32), 12, 8)
	_add(root_body, mb)
	head = _n("Head", root_body, Vector3(0, 0.02, -0.42))
	mb = MeshBuilder.new()
	mb.ellipsoid(s, MeshBuilder.at(Vector3.ZERO), Vector3(0.18, 0.15, 0.16), 10, 7)
	for i in 4:
		var x := -0.09 + i * 0.06
		mb.ellipsoid(eye, MeshBuilder.at(Vector3(x, 0.06 + (0.03 if i % 3 == 0 else 0.0), -0.14)), Vector3(0.025, 0.025, 0.02), 5, 4)
	for sx in [-1.0, 1.0]:
		mb.cylinder(Mat.stylized(Color.html("#1a1010"), Mat.P.BONE), MeshBuilder.at_euler(Vector3(sx * 0.06, -0.08, -0.12), Vector3(PI * 0.85, 0, sx * 0.2)), 0.03, 0.0, 0.16, 5)
	_add(head, mb)
	for i in 8:
		var side := -1.0 if i < 4 else 1.0
		var k := i % 4
		var hip := _n("Leg", root_body, Vector3(side * 0.22, 0.0, -0.28 + k * 0.14))
		hip.rotation = Vector3(0, side * (0.9 - k * 0.55), side * 1.0)
		mb = MeshBuilder.new()
		mb.limb(s, MeshBuilder.at(Vector3.ZERO), 0.04, 0.035, 0.45, 6)
		_add(hip, mb)
		var knee := _n("Knee", hip, Vector3(0, -0.45, 0))
		knee.rotation.z = side * -1.9
		mb = MeshBuilder.new()
		mb.limb(s, MeshBuilder.at(Vector3.ZERO), 0.035, 0.015, 0.6, 6)
		_add(knee, mb)
		legs.append([hip, knee, (PI if (k % 2 == 0) == (side > 0) else 0.0), side, k])
	extra.append("spider")


# =============================================================================== Vögel
func _bird() -> void:
	var col := _c("tint", "#f4f0e8" if species == "chicken" else "#8a6a4a")
	var feather := Mat.stylized(col, Mat.P.FUR, {"c2": col.darkened(0.3), "rim": 0.25})
	var beak := Mat.stylized(Color.html("#f0b030"), Mat.P.PLAIN)
	var dark := Mat.stylized(Color.html("#100808"), Mat.P.PLAIN, {"rim": 0.5})
	var s := 0.32 if species == "chicken" else 0.55
	_height = s * 1.5
	root_body = _n("Body", self, Vector3(0, s * 0.7, 0))
	_base_y = root_body.position.y
	var mb := MeshBuilder.new()
	mb.ellipsoid(feather, MeshBuilder.at_euler(Vector3.ZERO, Vector3(0.3, 0, 0)), Vector3(s * 0.45, s * 0.5, s * 0.62), 12, 8)
	mb.ellipsoid(feather, MeshBuilder.at_euler(Vector3(0, s * 0.15, s * 0.55), Vector3(-0.8, 0, 0)), Vector3(s * 0.18, s * 0.4, s * 0.12), 8, 5)
	_add(root_body, mb)
	head = _n("Head", root_body, Vector3(0, s * 0.45, -s * 0.42))
	mb = MeshBuilder.new()
	mb.ellipsoid(feather, MeshBuilder.at(Vector3.ZERO), Vector3(s * 0.22, s * 0.26, s * 0.24), 10, 7)
	mb.cylinder(beak, MeshBuilder.at_euler(Vector3(0, -s * 0.02, -s * 0.2), Vector3(-PI * 0.5, 0, 0)), s * 0.07, 0.0, s * 0.18, 6)
	for sx in [-1.0, 1.0]:
		mb.ellipsoid(dark, MeshBuilder.at(Vector3(sx * s * 0.13, s * 0.06, -s * 0.13)), Vector3(s * 0.04, s * 0.04, s * 0.03), 5, 4)
	if species == "chicken":
		var red := Mat.stylized(Color.html("#e02020"), Mat.P.PLAIN)
		mb.ellipsoid(red, MeshBuilder.at(Vector3(0, s * 0.28, -s * 0.05)), Vector3(s * 0.04, s * 0.1, s * 0.12), 6, 4)
		mb.ellipsoid(red, MeshBuilder.at(Vector3(0, -s * 0.12, -s * 0.18)), Vector3(s * 0.04, s * 0.07, s * 0.04), 6, 4)
	if species == "owl":
		for sx in [-1.0, 1.0]:
			mb.ellipsoid(Mat.emissive(Color.html("#ffc020"), 1.2), MeshBuilder.at(Vector3(sx * s * 0.09, s * 0.06, -s * 0.2)), Vector3(s * 0.07, s * 0.07, s * 0.03), 6, 4)
	_add(head, mb)
	for sx in [-1.0, 1.0]:
		var w := _n("Wing", root_body, Vector3(sx * s * 0.38, s * 0.12, 0))
		mb = MeshBuilder.new()
		mb.ellipsoid(feather, MeshBuilder.at(Vector3(sx * s * 0.05, -s * 0.05, s * 0.05)), Vector3(s * 0.12, s * 0.32, s * 0.45), 8, 6)
		_add(w, mb)
		wings.append([w, sx])
		var hip := _n("Leg", root_body, Vector3(sx * s * 0.15, -s * 0.35, 0.05))
		mb = MeshBuilder.new()
		mb.limb(beak, MeshBuilder.at(Vector3.ZERO), s * 0.03, s * 0.025, s * 0.3, 5)
		mb.box(beak, MeshBuilder.at(Vector3(0, -s * 0.33, -s * 0.06)), Vector3(s * 0.12, s * 0.02, s * 0.16))
		_add(hip, mb)
		legs.append([hip, null, PI if sx > 0 else 0.0, sx, 0])
	extra.append("bird")


# =============================================================================== Drache
func _dragon() -> void:
	var col := _c("tint", "#3a3436")
	var col2 := _c("tint2", "#ff6a1a")
	var big := species == "dragon"
	var s := 1.0
	var scale_mat := Mat.stylized(col, Mat.P.SCALES, {"c2": col.darkened(0.6), "rim": 0.25, "emis": col2 * 0.05})
	var belly := Mat.stylized(col2.darkened(0.3) if big else col.lightened(0.3), Mat.P.LAVA if big else Mat.P.SCALES, {"c2": col.darkened(0.5), "emis": col2})
	var horn := Mat.stylized(Color.html("#1a1414"), Mat.P.BONE, {"c2": Color.html("#000000")})
	var wing_mat := Mat.stylized(col.darkened(0.2), Mat.P.LEATHER, {"c2": col2.darkened(0.6), "emis": col2 * 0.12})
	var eye := Mat.emissive(col2.lightened(0.3), 4.0)
	_height = 2.2
	root_body = _n("Body", self, Vector3(0, 1.3, 0))
	_base_y = 1.3
	var mb := MeshBuilder.new()
	mb.ellipsoid(scale_mat, MeshBuilder.at(Vector3(0, 0, -0.2)), Vector3(0.65, 0.7, 1.1), 16, 10, Color.WHITE, 0.05, 1.5, 4)
	mb.ellipsoid(belly, MeshBuilder.at(Vector3(0, -0.35, -0.2)), Vector3(0.5, 0.4, 1.0), 14, 8)
	for k in 7:
		mb.cylinder(horn, MeshBuilder.at_euler(Vector3(0, 0.62, -0.9 + k * 0.3), Vector3(0.4, 0, 0)), 0.08, 0.0, 0.32, 5)
	_add(root_body, mb)
	# Hals aus Segmenten
	var parent: Node3D = root_body
	var pos := Vector3(0, 0.25, -1.1)
	for i in 4:
		var seg := _n("Neck%d" % i, parent, pos)
		seg.rotation.x = -0.35 if i == 0 else -0.15
		mb = MeshBuilder.new()
		var r := 0.38 - i * 0.05
		mb.ellipsoid(scale_mat, MeshBuilder.at(Vector3(0, 0, -0.2)), Vector3(r, r, 0.38), 10, 7)
		mb.ellipsoid(belly, MeshBuilder.at(Vector3(0, -r * 0.5, -0.2)), Vector3(r * 0.7, r * 0.5, 0.34), 8, 5)
		mb.cylinder(horn, MeshBuilder.at_euler(Vector3(0, r * 0.9, -0.2), Vector3(0.5, 0, 0)), 0.06, 0.0, 0.25, 5)
		_add(seg, mb)
		neck_segs.append(seg)
		parent = seg
		pos = Vector3(0, 0, -0.4)
	head = _n("Head", parent, Vector3(0, 0.05, -0.45))
	head.rotation.x = 0.6
	mb = MeshBuilder.new()
	mb.ellipsoid(scale_mat, MeshBuilder.at(Vector3(0, 0.05, -0.15)), Vector3(0.32, 0.28, 0.4), 12, 8)
	mb.ellipsoid(scale_mat, MeshBuilder.at(Vector3(0, -0.02, -0.55)), Vector3(0.22, 0.16, 0.38), 10, 7)
	for sx in [-1.0, 1.0]:
		mb.ellipsoid(eye, MeshBuilder.at(Vector3(sx * 0.2, 0.15, -0.35)), Vector3(0.06, 0.04, 0.05), 6, 4)
		mb.cylinder(horn, MeshBuilder.at_euler(Vector3(sx * 0.18, 0.22, 0.05), Vector3(-1.1, 0, sx * -0.35)), 0.09, 0.0, 0.6, 6)
		mb.cylinder(horn, MeshBuilder.at_euler(Vector3(sx * 0.25, 0.0, 0.1), Vector3(-1.4, 0, sx * -0.9)), 0.05, 0.0, 0.35, 5)
		for k in 3:
			mb.cylinder(Mat.stylized(Color.html("#f0e6d0"), Mat.P.BONE), MeshBuilder.at_euler(Vector3(sx * 0.12, -0.14, -0.55 - k * 0.1), Vector3(PI, 0, 0)), 0.025, 0.0, 0.1, 4)
	_add(head, mb)
	jaw = _n("Jaw", head, Vector3(0, -0.12, -0.2))
	mb = MeshBuilder.new()
	mb.ellipsoid(scale_mat, MeshBuilder.at(Vector3(0, -0.04, -0.35)), Vector3(0.18, 0.08, 0.38), 10, 5)
	_add(jaw, mb)
	_fx_mouth = Node3D.new()
	_fx_mouth.position = Vector3(0, -0.05, -0.85)
	head.add_child(_fx_mouth)
	# Schwanz
	parent = root_body
	pos = Vector3(0, 0.05, 0.85)
	for i in 6:
		var seg := _n("Tail%d" % i, parent, pos)
		seg.rotation.x = 0.12
		mb = MeshBuilder.new()
		var r := 0.42 - i * 0.065
		mb.ellipsoid(scale_mat, MeshBuilder.at(Vector3(0, 0, 0.25)), Vector3(r, r * 0.9, 0.42), 10, 6)
		mb.cylinder(horn, MeshBuilder.at_euler(Vector3(0, r * 0.85, 0.25), Vector3(-0.4, 0, 0)), 0.05, 0.0, 0.2, 4)
		if i == 5:
			var outline := PackedVector2Array([Vector2(0, 0.3), Vector2(0.35, 0.65), Vector2(0, 1.1), Vector2(-0.35, 0.65)])
			mb.extrude(horn, MeshBuilder.at_euler(Vector3(0, 0, 0.1), Vector3(PI * 0.5, 0, 0)), outline, 0.06)
		_add(seg, mb)
		tail_segs.append(seg)
		parent = seg
		pos = Vector3(0, 0, 0.5)
	# Beine
	var offs := [[-1, -1, 0.0], [1, -1, PI], [-1, 1, PI], [1, 1, 0.0]]
	for o2 in offs:
		var sx: float = o2[0]
		var sz: float = o2[1]
		var hip := _n("Leg", root_body, Vector3(sx * 0.5, -0.2, sz * 0.62 - 0.2))
		mb = MeshBuilder.new()
		mb.ellipsoid(scale_mat, MeshBuilder.at(Vector3(0, -0.15, 0)), Vector3(0.26, 0.35, 0.3), 10, 7)
		mb.limb(scale_mat, MeshBuilder.at(Vector3.ZERO), 0.2, 0.15, 0.55, 8)
		_add(hip, mb)
		var knee := _n("Knee", hip, Vector3(0, -0.55, 0))
		mb = MeshBuilder.new()
		mb.limb(scale_mat, MeshBuilder.at(Vector3.ZERO), 0.14, 0.11, 0.45, 8)
		mb.ellipsoid(scale_mat, MeshBuilder.at(Vector3(0, -0.5, -0.1)), Vector3(0.18, 0.1, 0.25), 8, 5)
		for k in 3:
			mb.cylinder(horn, MeshBuilder.at_euler(Vector3(-0.1 + k * 0.1, -0.52, -0.32), Vector3(-PI * 0.5, 0, 0)), 0.035, 0.0, 0.14, 4)
		_add(knee, mb)
		legs.append([hip, knee, o2[2], sx, sz])
	# Flügel
	for sx in [-1.0, 1.0]:
		var w := _n("Wing", root_body, Vector3(sx * 0.45, 0.45, -0.5))
		mb = MeshBuilder.new()
		var span := 2.6 if big else 1.6
		mb.beam(horn, Vector3.ZERO, Vector3(sx * span * 0.45, 0.5, 0.2), Vector2(0.09, 0.09))
		mb.beam(horn, Vector3(sx * span * 0.45, 0.5, 0.2), Vector3(sx * span, 0.25, 0.6), Vector2(0.07, 0.07))
		var outline := PackedVector2Array([Vector2(0, 0), Vector2(sx * span * 0.45, 0.5), Vector2(sx * span, 0.25), Vector2(sx * span * 0.85, -0.6), Vector2(sx * span * 0.55, -0.35), Vector2(sx * span * 0.35, -0.8), Vector2(sx * span * 0.15, -0.5)])
		mb.extrude(wing_mat, MeshBuilder.at_euler(Vector3(0, 0, 0.3), Vector3(PI * 0.5 - 0.2, 0, 0)), outline, 0.03)
		_add(w, mb)
		w.rotation.z = sx * -0.25
		wings.append([w, sx])
	if big:
		var cracks := FxLib.sparkles(col2, 1.2, 24)
		root_body.add_child(cracks)
	extra.append("dragon")


# =============================================================================== Golem
func _golem() -> void:
	var stone_c := _c("tint", "#8a8278")
	var glow_c := _c("glow", "#ff7a20" if species == "forge_golem" else ("#60c0ff" if species in ["ice_golem", "crystal_golem"] else "#90ff60"))
	var pattern := Mat.P.ROCK
	if species in ["forge_golem", "mech"]:
		pattern = Mat.P.METAL
	if species in ["ice_golem", "crystal_golem"]:
		pattern = Mat.P.ICE
	var st := Mat.stylized(stone_c, pattern, {"c2": stone_c.darkened(0.5), "tri": true, "rim": 0.25})
	var gm := Mat.emissive(glow_c, 3.0)
	_height = 2.6
	root_body = _n("Body", self, Vector3(0, 1.45, 0))
	_base_y = 1.45
	var mb := MeshBuilder.new()
	mb.ellipsoid(st, MeshBuilder.at(Vector3(0, 0.25, 0)), Vector3(0.75, 0.6, 0.5), 10, 7, Color.WHITE, 0.25, 1.2, 3)
	mb.ellipsoid(st, MeshBuilder.at(Vector3(0, -0.3, 0.05)), Vector3(0.5, 0.35, 0.38), 8, 6, Color.WHITE, 0.25, 1.2, 5)
	mb.ellipsoid(gm, MeshBuilder.at(Vector3(0, 0.2, -0.42)), Vector3(0.16, 0.16, 0.1), 8, 6)
	if species == "forge_golem":
		mb.cylinder(st, MeshBuilder.at(Vector3(0.3, 0.6, 0.25)), 0.12, 0.1, 0.7, 8)
		mb.cylinder(st, MeshBuilder.at(Vector3(-0.3, 0.6, 0.25)), 0.12, 0.1, 0.7, 8)
	_add(root_body, mb)
	if species == "forge_golem":
		for sx in [-0.3, 0.3]:
			var sm := FxLib.fire(0.3, Color(1, 0.5, 0.1), false)
			sm.position = Vector3(sx, 1.35, 0.25)
			root_body.add_child(sm)
	head = _n("Head", root_body, Vector3(0, 0.85, -0.05))
	mb = MeshBuilder.new()
	mb.ellipsoid(st, MeshBuilder.at(Vector3.ZERO), Vector3(0.3, 0.26, 0.28), 8, 6, Color.WHITE, 0.2, 1.5, 7)
	for sx in [-1.0, 1.0]:
		mb.box(gm, MeshBuilder.at(Vector3(sx * 0.11, 0.03, -0.25)), Vector3(0.09, 0.05, 0.04))
	_add(head, mb)
	for sx in [-1.0, 1.0]:
		var sh := _n("Arm", root_body, Vector3(sx * 0.85, 0.45, 0))
		mb = MeshBuilder.new()
		mb.ellipsoid(st, MeshBuilder.at(Vector3(0, 0, 0)), Vector3(0.35, 0.32, 0.35), 8, 6, Color.WHITE, 0.25, 1.4, 11)
		mb.ellipsoid(st, MeshBuilder.at(Vector3(0, -0.45, 0)), Vector3(0.24, 0.35, 0.24), 8, 6, Color.WHITE, 0.2, 1.4, 12)
		_add(sh, mb)
		var el := _n("Elbow", sh, Vector3(0, -0.75, 0))
		mb = MeshBuilder.new()
		mb.ellipsoid(st, MeshBuilder.at(Vector3(0, -0.3, 0)), Vector3(0.26, 0.36, 0.26), 8, 6, Color.WHITE, 0.2, 1.4, 13)
		mb.ellipsoid(st, MeshBuilder.at(Vector3(0, -0.72, -0.05)), Vector3(0.36, 0.3, 0.36), 8, 6, Color.WHITE, 0.25, 1.4, 14)
		mb.ellipsoid(gm, MeshBuilder.at(Vector3(0, -0.3, -0.24)), Vector3(0.06, 0.12, 0.03), 6, 4)
		_add(el, mb)
		arms.append([sh, el, sx])
	for sx in [-1.0, 1.0]:
		var hip := _n("Leg", root_body, Vector3(sx * 0.32, -0.55, 0.05))
		mb = MeshBuilder.new()
		mb.ellipsoid(st, MeshBuilder.at(Vector3(0, -0.2, 0)), Vector3(0.24, 0.3, 0.24), 8, 6, Color.WHITE, 0.2, 1.4, 21)
		_add(hip, mb)
		var knee := _n("Knee", hip, Vector3(0, -0.45, 0))
		mb = MeshBuilder.new()
		mb.ellipsoid(st, MeshBuilder.at(Vector3(0, -0.2, 0)), Vector3(0.22, 0.28, 0.22), 8, 6, Color.WHITE, 0.2, 1.4, 22)
		mb.ellipsoid(st, MeshBuilder.at(Vector3(0, -0.42, -0.1)), Vector3(0.28, 0.12, 0.36), 8, 5, Color.WHITE, 0.15, 1.4, 23)
		_add(knee, mb)
		legs.append([hip, knee, 0.0 if sx < 0 else PI, sx, 0])
	var l := FxLib.light(glow_c, 1.4, 6.0)
	l.position = Vector3(0, 0.3, -0.8)
	root_body.add_child(l)
	extra.append("biped")


# =============================================================================== Elementare
func _elemental() -> void:
	var col := _c("tint", {"fire_elemental": "#ff6a1a", "ice_elemental": "#8ad8ff", "earth_elemental": "#8a7a5a",
		"air_elemental": "#d0e8ff", "wisp": "#a0ffe0", "arcane_elemental": "#c080ff"}.get(species, "#ffffff"))
	_height = 2.2 if species != "wisp" else 1.0
	root_body = _n("Body", self, Vector3(0, 1.2 if species != "wisp" else 1.0, 0))
	_base_y = root_body.position.y
	var core := Mat.stylized(col, Mat.P.ICE if species != "earth_elemental" else Mat.P.ROCK, {"emis": col * (0.9 if species != "earth_elemental" else 0.15), "rim": 0.6, "tri": true})
	var mb := MeshBuilder.new()
	if species == "wisp":
		mb.ellipsoid(Mat.emissive(col, 3.0), MeshBuilder.at(Vector3.ZERO), Vector3(0.18, 0.18, 0.18), 10, 8)
		_add(root_body, mb, false)
		var g := FxLib.glow_sprite(Color(col.r, col.g, col.b, 0.8), 1.4)
		root_body.add_child(g)
		root_body.add_child(FxLib.sparkles(col, 0.4, 14))
		root_body.add_child(FxLib.light(col, 1.5, 6.0))
		head = root_body
		extra.append("float")
		return
	mb.ellipsoid(core, MeshBuilder.at(Vector3(0, 0.1, 0)), Vector3(0.45, 0.6, 0.4), 10, 8, Color.WHITE, 0.25, 1.2, 9)
	_add(root_body, mb)
	head = _n("Head", root_body, Vector3(0, 0.85, 0))
	mb = MeshBuilder.new()
	mb.ellipsoid(core, MeshBuilder.at(Vector3.ZERO), Vector3(0.26, 0.28, 0.25), 8, 6, Color.WHITE, 0.25, 1.5, 3)
	for sx in [-1.0, 1.0]:
		mb.ellipsoid(Mat.emissive(Color(1, 1, 1), 4.0), MeshBuilder.at(Vector3(sx * 0.09, 0.03, -0.22)), Vector3(0.05, 0.03, 0.02), 5, 4)
	_add(head, mb)
	# schwebende Brocken
	for i in 6:
		var orb := AnimNode3D.new()
		orb.mode = "bob"
		orb.speed = 1.5 + i * 0.3
		orb.amount = 0.15
		var a := TAU * i / 6.0
		orb.position = Vector3(cos(a) * 0.75, -0.2 + (i % 3) * 0.35, sin(a) * 0.75)
		var omb := MeshBuilder.new()
		omb.ellipsoid(core, MeshBuilder.at(Vector3.ZERO), Vector3(0.14, 0.16, 0.14), 6, 4, Color.WHITE, 0.3, 2.0, i)
		var mi := MeshInstance3D.new()
		mi.mesh = omb.commit()
		orb.add_child(mi)
		root_body.add_child(orb)
	for sx in [-1.0, 1.0]:
		var sh := _n("Arm", root_body, Vector3(sx * 0.55, 0.45, 0))
		mb = MeshBuilder.new()
		mb.ellipsoid(core, MeshBuilder.at(Vector3(0, -0.3, 0)), Vector3(0.16, 0.38, 0.16), 8, 6, Color.WHITE, 0.25, 1.5, 5)
		_add(sh, mb)
		var el := _n("Elbow", sh, Vector3(0, -0.6, 0))
		mb = MeshBuilder.new()
		mb.ellipsoid(core, MeshBuilder.at(Vector3(0, -0.25, 0)), Vector3(0.18, 0.3, 0.18), 8, 6, Color.WHITE, 0.25, 1.5, 6)
		_add(el, mb)
		arms.append([sh, el, sx])
	if species == "fire_elemental":
		var f := FxLib.fire(1.4, col, true)
		f.position.y = -0.4
		root_body.add_child(f)
	else:
		root_body.add_child(FxLib.sparkles(col, 1.0, 24))
		root_body.add_child(FxLib.light(col, 1.4, 7.0))
	extra.append("float")


# =============================================================================== Baumwesen
func _treant() -> void:
	var bark := Mat.stylized(_c("tint", "#5a4430"), Mat.P.BARK, {"c2": Color.html("#2a1a10")})
	var leaf := Mat.foliage(_c("leaf", "#5aa040"), Color.html("#1a3a14"), Color.html("#c8e070"))
	var glow := Mat.emissive(_c("glow", "#c0ff60"), 2.5)
	_height = 3.4
	root_body = _n("Body", self, Vector3(0, 1.6, 0))
	_base_y = 1.6
	var mb := MeshBuilder.new()
	mb.cylinder(bark, MeshBuilder.at(Vector3(0, -0.5, 0)), 0.55, 0.42, 1.7, 10)
	mb.ellipsoid(leaf, MeshBuilder.at(Vector3(0, 1.6, 0.1)), Vector3(1.0, 0.8, 0.9), 12, 8, Color(0.7, 1, 0, 1), 0.3, 1.0, 3, -1, 1, 0.5)
	mb.ellipsoid(leaf, MeshBuilder.at(Vector3(0.6, 1.3, 0.2)), Vector3(0.6, 0.5, 0.6), 10, 6, Color(0.6, 1, 0, 1), 0.3, 1.0, 4, -1, 1, 0.5)
	mb.ellipsoid(leaf, MeshBuilder.at(Vector3(-0.6, 1.35, 0.1)), Vector3(0.6, 0.5, 0.6), 10, 6, Color(0.6, 1, 0, 1), 0.3, 1.0, 5, -1, 1, 0.5)
	_add(root_body, mb)
	head = _n("Head", root_body, Vector3(0, 0.9, -0.38))
	mb = MeshBuilder.new()
	for sx in [-1.0, 1.0]:
		mb.ellipsoid(glow, MeshBuilder.at(Vector3(sx * 0.15, 0, 0)), Vector3(0.07, 0.05, 0.03), 6, 4)
	mb.box(Mat.stylized(Color.html("#1a1008")), MeshBuilder.at(Vector3(0, -0.25, 0.02)), Vector3(0.3, 0.06, 0.04))
	_add(head, mb)
	for sx in [-1.0, 1.0]:
		var sh := _n("Arm", root_body, Vector3(sx * 0.5, 0.8, 0))
		mb = MeshBuilder.new()
		mb.limb(bark, MeshBuilder.at(Vector3.ZERO), 0.16, 0.12, 0.8, 8)
		_add(sh, mb)
		var el := _n("Elbow", sh, Vector3(0, -0.85, 0))
		mb = MeshBuilder.new()
		mb.limb(bark, MeshBuilder.at(Vector3.ZERO), 0.12, 0.08, 0.7, 8)
		for k in 3:
			mb.beam(bark, Vector3(0, -0.7, 0), Vector3((k - 1) * 0.15, -1.0, -0.1), Vector2(0.05, 0.05))
		mb.ellipsoid(leaf, MeshBuilder.at(Vector3(0, -0.3, 0.05)), Vector3(0.2, 0.18, 0.2), 6, 4, Color(0.8, 1, 0, 1))
		_add(el, mb)
		arms.append([sh, el, sx])
	for sx in [-1.0, 1.0]:
		var hip := _n("Leg", root_body, Vector3(sx * 0.28, -0.4, 0))
		mb = MeshBuilder.new()
		mb.limb(bark, MeshBuilder.at(Vector3.ZERO), 0.22, 0.16, 0.6, 8)
		_add(hip, mb)
		var knee := _n("Knee", hip, Vector3(0, -0.6, 0))
		mb = MeshBuilder.new()
		mb.limb(bark, MeshBuilder.at(Vector3.ZERO), 0.16, 0.22, 0.5, 8)
		for k in 3:
			mb.beam(bark, Vector3(0, -0.5, 0), Vector3((k - 1) * 0.3, -0.62, -0.25), Vector2(0.08, 0.08))
		_add(knee, mb)
		legs.append([hip, knee, 0.0 if sx < 0 else PI, sx, 0])
	extra.append("biped")


# =============================================================================== Geist
func _ghost() -> void:
	var col := _c("tint", "#9ad0ff")
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(col.r, col.g, col.b, 0.45)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.emission_enabled = true
	m.emission = col
	m.emission_energy_multiplier = 0.8
	m.rim_enabled = true
	m.rim = 1.0
	_height = 2.0
	root_body = _n("Body", self, Vector3(0, 1.1, 0))
	_base_y = 1.1
	var mb := MeshBuilder.new()
	mb.ellipsoid(m, MeshBuilder.at(Vector3(0, 0.2, 0)), Vector3(0.32, 0.4, 0.24), 12, 8)
	mb.cylinder(m, MeshBuilder.at(Vector3(0, -0.9, 0)), 0.05, 0.3, 1.0, 12, false)
	_add(root_body, mb, false)
	head = _n("Head", root_body, Vector3(0, 0.75, 0))
	mb = MeshBuilder.new()
	mb.ellipsoid(m, MeshBuilder.at(Vector3.ZERO), Vector3(0.17, 0.2, 0.18), 10, 8)
	mb.ellipsoid(m, MeshBuilder.at(Vector3(0, 0.05, 0.05)), Vector3(0.22, 0.25, 0.22), 10, 8, Color.WHITE, 0.1, 2.0, 1, -0.4, 1.0)
	for sx in [-1.0, 1.0]:
		mb.ellipsoid(Mat.emissive(Color(1, 1, 1), 4.0), MeshBuilder.at(Vector3(sx * 0.06, 0.02, -0.16)), Vector3(0.03, 0.04, 0.02), 5, 4)
	_add(head, mb, false)
	for sx in [-1.0, 1.0]:
		var sh := _n("Arm", root_body, Vector3(sx * 0.32, 0.45, 0))
		mb = MeshBuilder.new()
		mb.limb(m, MeshBuilder.at(Vector3.ZERO), 0.07, 0.05, 0.45, 8)
		_add(sh, mb, false)
		var el := _n("Elbow", sh, Vector3(0, -0.45, 0))
		mb = MeshBuilder.new()
		mb.limb(m, MeshBuilder.at(Vector3.ZERO), 0.05, 0.03, 0.4, 8)
		_add(el, mb, false)
		arms.append([sh, el, sx])
	root_body.add_child(FxLib.sparkles(col, 0.5, 10))
	extra.append("float")


func _slime() -> void:
	var col := _c("tint", "#60d040")
	var m := Mat.stylized(col, Mat.P.ICE, {"emis": col * 0.3, "rim": 0.6})
	_height = 1.0
	root_body = _n("Body", self, Vector3(0, 0.0, 0))
	var mb := MeshBuilder.new()
	mb.ellipsoid(m, MeshBuilder.at(Vector3(0, 0.45, 0)), Vector3(0.6, 0.5, 0.6), 14, 9, Color.WHITE, 0.08, 1.5, 2, -0.3, 1.0)
	for sx in [-1.0, 1.0]:
		mb.ellipsoid(Mat.stylized(Color.html("#101010")), MeshBuilder.at(Vector3(sx * 0.15, 0.62, -0.5)), Vector3(0.06, 0.08, 0.04), 6, 4)
	_add(root_body, mb)
	head = root_body
	extra.append("slime")


func _dummy() -> void:
	var straw := Mat.stylized(Color.html("#d8b868"), Mat.P.THATCH, {"c2": Color.html("#8a6a28"), "scale": 3.0})
	var wood := Mat.stylized(Color.html("#7a5232"), Mat.P.WOOD)
	var cloth := Mat.stylized(Color.html("#9a3a2a"), Mat.P.CLOTH)
	_height = 2.0
	root_body = _n("Body", self, Vector3.ZERO)
	var mb := MeshBuilder.new()
	mb.cylinder(wood, MeshBuilder.at(Vector3(0, -0.2, 0)), 0.08, 0.07, 2.1, 8)
	mb.ellipsoid(straw, MeshBuilder.at(Vector3(0, 1.25, 0)), Vector3(0.32, 0.45, 0.25), 10, 8)
	mb.ellipsoid(cloth, MeshBuilder.at(Vector3(0, 1.25, -0.08)), Vector3(0.33, 0.3, 0.2), 10, 6, Color.WHITE, 0, 1, 0, -0.6, 0.6)
	mb.beam(wood, Vector3(-0.6, 1.45, 0), Vector3(0.6, 1.45, 0), Vector2(0.06, 0.06))
	mb.ellipsoid(straw, MeshBuilder.at(Vector3(0, 1.85, 0)), Vector3(0.2, 0.22, 0.2), 10, 8)
	mb.disc(Mat.stylized(Color.html("#c02020")), MeshBuilder.at_euler(Vector3(0, 1.3, -0.29), Vector3(PI * 0.5, 0, 0)), 0.12, 12)
	_add(root_body, mb)
	head = root_body
	extra.append("static")


# =============================================================================== Animation
func attack(_k := "") -> void:
	_attack_t = 0.0


func cast_release() -> void:
	_attack_t = 0.0


func hit_react() -> void:
	if _hit_t < 0:
		_hit_t = 0.0


func set_dead(v: bool) -> void:
	if v and not dead:
		_death_t = 0.0
	dead = v


func top_height() -> float:
	return _height * scale.y


func mouth_node() -> Node3D:
	return _fx_mouth if _fx_mouth else head


func _process(delta: float) -> void:
	if root_body == null:
		return
	_t += delta
	var k := clampf(delta * 10.0, 0.0, 1.0)
	if "static" in extra:
		if _hit_t >= 0.0:
			_hit_t += delta
			root_body.rotation.z = sin(_hit_t * 30.0) * 0.12 * max(0.0, 1.0 - _hit_t * 2.5)
			if _hit_t > 0.5:
				_hit_t = -1.0
		return
	if dead:
		_death_t += delta
		var d := clampf(_death_t / 0.7, 0.0, 1.0)
		var e := d * d * (3.0 - 2.0 * d)
		if "float" in extra:
			root_body.position.y = lerpf(_base_y, 0.3, e)
			root_body.scale = Vector3.ONE * (1.0 - e * 0.7)
		else:
			root_body.rotation.z = lerpf(0.0, PI * 0.5, e)
			root_body.position.y = lerpf(_base_y, _base_y * 0.45, e)
		for l in legs:
			(l[0] as Node3D).rotation.x = lerpf((l[0] as Node3D).rotation.x, 0.4, k)
		return
	var moving := speed > 0.2
	var run := clampf(speed / 7.0, 0.0, 1.5)
	phase += delta * (2.0 + speed * 1.6) if moving else delta * 0.8
	var s := sin(phase)
	var c := cos(phase)
	var atk := 0.0
	if _attack_t >= 0.0:
		_attack_t += delta
		atk = sin(clampf(_attack_t / 0.5, 0.0, 1.0) * PI)
		if _attack_t > 0.5:
			_attack_t = -1.0
	var hit := 0.0
	if _hit_t >= 0.0:
		_hit_t += delta
		hit = sin(clampf(_hit_t / 0.25, 0.0, 1.0) * PI)
		if _hit_t > 0.25:
			_hit_t = -1.0
	# Beine
	for l in legs:
		var hip: Node3D = l[0]
		var knee = l[1]
		var off: float = l[2]
		if "spider" in extra:
			var ls := sin(phase * 1.5 + off)
			hip.rotation.x = ls * 0.35 * (1.0 if moving else 0.08)
			continue
		if moving:
			var amp := 0.45 + run * 0.35
			hip.rotation.x = sin(phase + off) * amp
			if knee:
				(knee as Node3D).rotation.x = -max(0.0, cos(phase + off)) * (0.6 + run * 0.6) * (1.0 if l[4] > 0 or "biped" in extra else -0.7)
		else:
			hip.rotation.x = lerpf(hip.rotation.x, 0.0, k)
			if knee:
				(knee as Node3D).rotation.x = lerpf((knee as Node3D).rotation.x, 0.0, k)
	# Körper
	var by := _base_y
	if moving:
		by += absf(c) * 0.04 * (1.0 + run)
	if "hop" in extra and moving:
		by += absf(sin(phase * 1.2)) * 0.12
	if "float" in extra:
		by += sin(_t * 1.8) * 0.12
	if "slime" in extra:
		var sq := 1.0 + sin(_t * (3.0 + speed)) * 0.08
		root_body.scale = Vector3(1.0 / sqrt(sq), sq, 1.0 / sqrt(sq))
	root_body.position.y = lerpf(root_body.position.y, by, k)
	root_body.rotation.x = lerpf(root_body.rotation.x, (-0.12 * atk) + hit * 0.12 + (0.05 * run if moving else 0.0), k)
	# Kopf / Kiefer
	if head and head != root_body:
		var look_down := 0.0
		if species == "chicken" and not moving:
			look_down = max(0.0, sin(_t * 1.3)) * 0.9
		head.rotation.x = lerpf(head.rotation.x, (0.6 if "dragon" in extra else 0.0) + look_down + atk * (0.3 if "dragon" in extra else -0.25), k)
	if jaw:
		jaw.rotation.x = lerpf(jaw.rotation.x, atk * 0.6 + (0.45 if casting or channeling else 0.0), k * 1.5)
	for i in neck_segs.size():
		var nseg: Node3D = neck_segs[i]
		nseg.rotation.y = sin(_t * 0.8 + i * 0.5) * 0.06
	for i in tail_segs.size():
		var tseg: Node3D = tail_segs[i]
		tseg.rotation.y = sin(_t * (1.5 + speed * 0.4) - i * 0.6) * (0.25 if "dragon" in extra else 0.5)
	# Flügel
	for w in wings:
		var wn: Node3D = w[0]
		var sx: float = w[1]
		if "dragon" in extra:
			var flap := sin(_t * (2.5 if airborne or moving else 1.2)) * (0.5 if airborne or moving else 0.12)
			wn.rotation.z = sx * (-0.25 + flap)
		elif "bird" in extra:
			var flap := sin(_t * 20.0) * 0.6 if airborne or (species != "chicken" and moving) else sin(_t * 2.0) * 0.05
			if species == "chicken" and moving:
				flap = sin(_t * 18.0) * 0.4
			wn.rotation.z = sx * flap
	# Arme (Golems, Elementare, Baumwesen, Geister)
	for a in arms:
		var sh: Node3D = a[0]
		var el: Node3D = a[1]
		var sx: float = a[2]
		var swing := (-s * sx * 0.4 * (1.0 if moving else 0.1))
		var ax := swing
		if combat:
			ax += 0.35
		if casting or channeling:
			ax = 1.0 + sin(_t * 6.0) * 0.08
		ax += atk * (1.8 if sx > 0 else 0.6)
		sh.rotation.x = lerpf(sh.rotation.x, ax, k)
		sh.rotation.z = lerpf(sh.rotation.z, sx * (0.15 + (0.3 if casting else 0.0)), k)
		el.rotation.x = lerpf(el.rotation.x, 0.3 + atk * -0.2 + (0.2 if combat else 0.0), k)
	if _fx_mouth and (casting or channeling) and _fx_mouth.get_child_count() == 0:
		var f := FxLib.fire(0.6, cast_color, true)
		_fx_mouth.add_child(f)
	elif _fx_mouth and not (casting or channeling) and _fx_mouth.get_child_count() > 0:
		for ch in _fx_mouth.get_children():
			ch.queue_free()
