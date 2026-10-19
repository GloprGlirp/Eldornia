class_name HumanoidModel
extends Node3D
## Prozeduraler, stilisierter Humanoide (Menschen, Zwerge, Kobolde, Skelette, Dämonen ...).
## Kräftige Proportionen wie in klassischen Fantasy-MMOs: breite Schultern, große Hände,
## wuchtige Schulterstücke. Animiert wird prozedural (Laufen, Kämpfen, Zaubern, Emotes).

signal anim_event(name: String)

var look: Dictionary = {}
var gear: Dictionary = {}          # slot -> item dict (mit "vis")
var kind := "human"
var female := false
var P: Dictionary = {}

# Gelenke
var body: Node3D
var hips: Node3D
var spine: Node3D
var chest: Node3D
var neck: Node3D
var head: Node3D
var sh_l: Node3D
var sh_r: Node3D
var el_l: Node3D
var el_r: Node3D
var hand_l: Node3D
var hand_r: Node3D
var th_l: Node3D
var th_r: Node3D
var kn_l: Node3D
var kn_r: Node3D
var ft_l: Node3D
var ft_r: Node3D
var back_attach: Node3D
var tail: Node3D

var _parts: Array = []        # alle erzeugten MeshInstances (für Neuaufbau)
var _weapon_r: Node3D
var _weapon_l: Node3D
var _cape: MeshInstance3D
var _cast_glow_l: MeshInstance3D
var _cast_glow_r: MeshInstance3D

# Animationszustand
var phase := 0.0
var speed := 0.0
var move_dir := Vector2(0, -1)    # lokal: x = rechts, y = vorwärts(-z)
var airborne := false
var combat := false
var casting := false
var channeling := false
var cast_color := Color(1, 0.7, 0.3)
var dead := false
var sitting := false
var mounted := false
var emote := ""
var idle_anim := "idle"
var weapon_style := "unarmed"     # unarmed, 1h, 2h, dual, bow, staff, shield
var _attack_t := -1.0
var _attack_kind := ""
var _attack_dur := 0.5
var _release_t := -1.0
var _hit_t := -1.0
var _death_t := 0.0
var _t := 0.0
var _pose: Dictionary = {}

const SKINS := ["#f2c9a8", "#e0ae8c", "#c98a6a", "#a9785a", "#7a5238", "#5a3a28"]
const HAIRS := ["#1a1410", "#3a2414", "#6a4422", "#a86a32", "#d8b060", "#e8e0d0", "#8a2a1a", "#4a4a52"]


func _init(p_look: Dictionary = {}, p_gear: Dictionary = {}) -> void:
	look = p_look
	gear = p_gear


func _ready() -> void:
	if body == null:
		build()


func build() -> void:
	for c in get_children():
		c.queue_free()
	_parts.clear()
	kind = str(look.get("kind", "human"))
	female = str(look.get("body", "m")) in ["f", "w", "female"]
	_setup_proportions()
	_build_rig()
	_build_body()
	_build_head()
	_apply_gear()
	idle_anim = str(look.get("anim", "idle"))
	_update_weapon_style()


# =============================================================================== Proportionen
func _setup_proportions() -> void:
	P = {
		"hip_h": 0.98, "hip_w": 0.105, "thigh": 0.45, "shin": 0.44,
		"spine": 0.2, "chest_h": 0.34, "sh_w": 0.25, "ua": 0.3, "fa": 0.27, "neck": 0.1, "head_r": 0.135,
		"chest_r": Vector3(0.235, 0.21, 0.15), "pelvis_r": Vector3(0.17, 0.12, 0.125), "belly_r": Vector3(0.17, 0.14, 0.13),
		"ua_r": [0.072, 0.058], "fa_r": [0.06, 0.046], "th_r": [0.095, 0.07], "sh_r": [0.068, 0.05],
		"hand": 1.15, "foot": 1.15, "head_s": 1.0, "hunch": 0.0,
	}
	if female:
		P.merge({"sh_w": 0.2, "chest_r": Vector3(0.19, 0.19, 0.13), "pelvis_r": Vector3(0.18, 0.13, 0.135),
			"belly_r": Vector3(0.14, 0.13, 0.11), "ua_r": [0.055, 0.045], "fa_r": [0.046, 0.036],
			"th_r": [0.088, 0.062], "sh_r": [0.058, 0.042], "hand": 0.95, "foot": 0.95, "hip_w": 0.1,
			"hip_h": 0.94, "thigh": 0.43, "shin": 0.42, "head_r": 0.125}, true)
	match kind:
		"dwarf":
			P.merge({"hip_h": 0.62, "thigh": 0.28, "shin": 0.27, "spine": 0.17, "chest_h": 0.32, "sh_w": 0.27,
				"chest_r": Vector3(0.28, 0.24, 0.21), "belly_r": Vector3(0.23, 0.18, 0.2), "pelvis_r": Vector3(0.2, 0.12, 0.15),
				"ua": 0.25, "fa": 0.23, "ua_r": [0.085, 0.07], "fa_r": [0.072, 0.056], "th_r": [0.11, 0.085], "sh_r": [0.08, 0.062],
				"hand": 1.35, "foot": 1.25, "head_r": 0.14, "hip_w": 0.12}, true)
		"kobold":
			P.merge({"hip_h": 0.55, "thigh": 0.27, "shin": 0.27, "spine": 0.16, "chest_h": 0.26, "sh_w": 0.17,
				"chest_r": Vector3(0.17, 0.17, 0.14), "belly_r": Vector3(0.16, 0.15, 0.15), "pelvis_r": Vector3(0.14, 0.1, 0.12),
				"ua": 0.22, "fa": 0.2, "ua_r": [0.045, 0.038], "fa_r": [0.04, 0.032], "th_r": [0.065, 0.05], "sh_r": [0.05, 0.036],
				"hand": 1.1, "foot": 1.2, "head_r": 0.16, "hunch": 0.35, "hip_w": 0.08}, true)
		"skeleton", "undead":
			P.merge({"ua_r": [0.035, 0.03], "fa_r": [0.03, 0.025], "th_r": [0.04, 0.035], "sh_r": [0.035, 0.03],
				"chest_r": Vector3(0.18, 0.2, 0.13), "belly_r": Vector3(0.05, 0.12, 0.05), "pelvis_r": Vector3(0.15, 0.08, 0.1)}, true)
		"demon":
			P.merge({"sh_w": 0.3, "chest_r": Vector3(0.29, 0.25, 0.19), "ua_r": [0.09, 0.075], "fa_r": [0.075, 0.06],
				"hand": 1.4, "foot": 1.3, "head_r": 0.14}, true)
		"giant":
			P.merge({"sh_w": 0.3, "chest_r": Vector3(0.3, 0.26, 0.2), "belly_r": Vector3(0.24, 0.2, 0.2),
				"ua_r": [0.1, 0.085], "fa_r": [0.09, 0.07], "th_r": [0.12, 0.09], "sh_r": [0.09, 0.07], "hand": 1.5, "foot": 1.4,
				"head_r": 0.13, "hunch": 0.15}, true)
		"fairy":
			P.merge({"sh_w": 0.15, "chest_r": Vector3(0.13, 0.14, 0.1), "pelvis_r": Vector3(0.12, 0.09, 0.1),
				"belly_r": Vector3(0.1, 0.1, 0.09), "ua_r": [0.035, 0.03], "fa_r": [0.03, 0.025], "th_r": [0.05, 0.035],
				"sh_r": [0.035, 0.026], "hand": 0.8, "foot": 0.7, "head_r": 0.13}, true)


# =============================================================================== Materialien
func _skin_color() -> Color:
	var s = look.get("skin")
	if s == null:
		return Color.html(SKINS[int(look.get("skin_i", 1)) % SKINS.size()])
	if s is int or (str(s).is_valid_int() and not str(s).begins_with("#")):
		return Color.html(SKINS[int(s) % SKINS.size()])
	return Color.html(str(s))


func _hair_color() -> Color:
	var h = look.get("hair")
	if h == null:
		return Color.html(HAIRS[2])
	if h is int or (str(h).is_valid_int() and not str(h).begins_with("#")):
		return Color.html(HAIRS[int(h) % HAIRS.size()])
	return Color.html(str(h))


func _mat_skin() -> Material:
	var c := _skin_color()
	if kind in ["skeleton", "undead"]:
		return Mat.stylized(Color.html("#e6dcc0"), Mat.P.BONE, {"c2": Color.html("#8a7a5a")})
	if kind == "kobold" or kind == "demon" or kind == "giant":
		return Mat.stylized(c, Mat.P.FUR if kind == "kobold" else Mat.P.SKIN, {"c2": c.darkened(0.35), "rim": 0.2})
	return Mat.stylized(c, Mat.P.SKIN, {"c2": Color(0.85, 0.35, 0.35), "rim": 0.18, "rim_tint": 0.7})


func _cloth(hex, pattern := Mat.P.CLOTH) -> Material:
	var c := Mat.col(hex)
	return Mat.stylized(c, pattern, {"c2": c.darkened(0.45), "rim": 0.12})


func _gear_mat(slot: String, fallback_hex, fallback_pattern := Mat.P.CLOTH) -> Material:
	var it: Dictionary = gear.get(slot, {})
	if it.is_empty():
		return _cloth(fallback_hex, fallback_pattern)
	var vis: Dictionary = it.get("vis", {})
	var typ: String = str(it.get("sub", "stoff"))
	var c := Color.html(str(vis.get("c", "#6a5a7a")))
	var c2 := Color.html(str(vis.get("c2", c.darkened(0.4).to_html())))
	var mcol := Color.html(str(vis.get("m", "#b8bcc6")))
	var q := int(it.get("q", 1))
	var glow = vis.get("g")
	var emis := Color(0, 0, 0)
	if glow != null and str(glow) != "" and q >= 4:
		emis = Color.html(str(glow)) * 0.12
	match typ:
		"platte":
			if q >= 4 and vis.get("gold", false):
				return Mat.stylized(mcol, Mat.P.GOLD, {"c2": mcol.darkened(0.5), "emis": emis, "wear": 0.8, "rim": 0.25})
			return Mat.stylized(mcol, Mat.P.METAL, {"c2": c, "emis": emis, "wear": 0.7, "rim": 0.25})
		"kette":
			return Mat.stylized(mcol, Mat.P.CHAIN, {"c2": mcol.darkened(0.6), "emis": emis})
		"leder":
			return Mat.stylized(c, Mat.P.LEATHER, {"c2": c2, "emis": emis})
	return Mat.stylized(c, Mat.P.CLOTH, {"c2": c2, "emis": emis})


func _gear_type(slot: String) -> String:
	var it: Dictionary = gear.get(slot, {})
	return str(it.get("sub", "")) if not it.is_empty() else ""


func _gear_vis(slot: String) -> Dictionary:
	var it: Dictionary = gear.get(slot, {})
	var v: Dictionary = it.get("vis", {}).duplicate()
	v["q"] = int(it.get("q", 1))
	return v


# =============================================================================== Skelett
func _node(n: String, parent: Node3D, pos: Vector3) -> Node3D:
	var x := Node3D.new()
	x.name = n
	x.position = pos
	parent.add_child(x)
	return x


func _build_rig() -> void:
	body = _node("Body", self, Vector3.ZERO)
	hips = _node("Hips", body, Vector3(0, P.hip_h, 0))
	spine = _node("Spine", hips, Vector3(0, 0.02, 0))
	chest = _node("Chest", spine, Vector3(0, P.spine, 0))
	neck = _node("Neck", chest, Vector3(0, P.chest_h, 0.01))
	head = _node("Head", neck, Vector3(0, P.neck + P.head_r * 0.85, -0.01))
	sh_l = _node("ShL", chest, Vector3(-P.sh_w, P.chest_h * 0.78, 0))
	sh_r = _node("ShR", chest, Vector3(P.sh_w, P.chest_h * 0.78, 0))
	el_l = _node("ElL", sh_l, Vector3(0, -P.ua, 0))
	el_r = _node("ElR", sh_r, Vector3(0, -P.ua, 0))
	hand_l = _node("HandL", el_l, Vector3(0, -P.fa, 0))
	hand_r = _node("HandR", el_r, Vector3(0, -P.fa, 0))
	th_l = _node("ThL", hips, Vector3(-P.hip_w, -0.04, 0))
	th_r = _node("ThR", hips, Vector3(P.hip_w, -0.04, 0))
	kn_l = _node("KnL", th_l, Vector3(0, -P.thigh, 0))
	kn_r = _node("KnR", th_r, Vector3(0, -P.thigh, 0))
	ft_l = _node("FtL", kn_l, Vector3(0, -P.shin, 0))
	ft_r = _node("FtR", kn_r, Vector3(0, -P.shin, 0))
	back_attach = _node("Back", chest, Vector3(0, P.chest_h * 0.7, P.chest_r.z * 0.9))
	sh_l.rotation.z = -0.12
	sh_r.rotation.z = 0.12


func _add(parent: Node3D, mesh: Mesh, shadow := true) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadow else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	_parts.append(mi)
	return mi


static var _mcache: Dictionary = {}


func _cached(key: String, fn: Callable) -> ArrayMesh:
	if _mcache.has(key):
		return _mcache[key]
	var m: ArrayMesh = fn.call()
	_mcache[key] = m
	return m


# =============================================================================== Körper
func _outfit_hex(key: String, default: String) -> String:
	return str(look.get(key, default))


func _build_body() -> void:
	var skin := _mat_skin()
	var skel := kind in ["skeleton", "undead"]
	var robe: bool = look.get("robe", false) or _gear_type("chest") == "stoff" and not look.get("no_robe", false)
	var dress: bool = look.get("dress", false)
	var top_hex := _outfit_hex("top", "#7a5a3a")
	var bottom_hex := _outfit_hex("bottom", "#4a3a2a")
	var top := _gear_mat("chest", top_hex)
	var legs := _gear_mat("legs", bottom_hex)
	var boots := _gear_mat("feet", "#4a3020", Mat.P.LEATHER)
	var gloves: Material = skin if not gear.has("hands") else _gear_mat("hands", "#5a3a22", Mat.P.LEATHER)
	var sleeves := top if not look.get("bare_arms", false) else skin
	if skel:
		top = skin
		legs = skin
		boots = skin
		gloves = skin
		sleeves = skin
		if look.get("armor", false) or not gear.is_empty():
			top = _gear_mat("chest", "#3a3a44", Mat.P.METAL)
	var key := "%s|%s|%s" % [kind, female, str(P)]
	# --- Becken & Bauch
	var mb := MeshBuilder.new()
	mb.ellipsoid(legs, MeshBuilder.at(Vector3(0, -0.02, 0)), P.pelvis_r, 14, 8)
	if not skel:
		mb.ellipsoid(top, MeshBuilder.at(Vector3(0, P.spine * 0.55, 0.005)), P.belly_r, 14, 8)
	else:
		mb.cylinder(skin, MeshBuilder.at(Vector3(0, 0, 0.04)), 0.03, 0.03, P.spine + 0.05, 6)
	_add(hips, mb.commit())
	# --- Brustkorb
	mb = MeshBuilder.new()
	var cr: Vector3 = P.chest_r
	if skel:
		for i in 5:
			var y = P.chest_h * (0.25 + i * 0.13)
			var w := cr.x * (0.75 + 0.25 * sin(PI * (i + 1) / 6.0))
			mb.torus(skin, Transform3D(Basis.from_scale(Vector3(1.0, 1.0, cr.z / cr.x)), Vector3(0, y, 0)), w, 0.018, 14, 4)
		mb.cylinder(skin, MeshBuilder.at(Vector3(0, -0.02, 0.06)), 0.03, 0.03, P.chest_h + 0.05, 6)
		mb.beam(skin, Vector3(-P.sh_w, P.chest_h * 0.8, 0), Vector3(P.sh_w, P.chest_h * 0.8, 0), Vector2(0.03, 0.03))
		if look.get("armor", false) or gear.has("chest"):
			mb.ellipsoid(top, MeshBuilder.at(Vector3(0, P.chest_h * 0.5, 0)), cr * 1.02, 14, 9, Color.WHITE, 0.0, 1.0, 0, -0.9, 0.95)
	else:
		mb.ellipsoid(top, MeshBuilder.at(Vector3(0, P.chest_h * 0.48, 0)), Vector3(cr.x, cr.y, cr.z), 16, 10)
		mb.ellipsoid(top, MeshBuilder.at(Vector3(0, P.chest_h * 0.72, 0.01)), Vector3(cr.x * 1.05, cr.y * 0.55, cr.z * 0.95), 16, 8)
		if female:
			mb.ellipsoid(top, MeshBuilder.at(Vector3(0, P.chest_h * 0.55, -cr.z * 0.35)), Vector3(cr.x * 0.8, cr.y * 0.55, cr.z * 0.8), 12, 7)
		# Kragen
		mb.torus(top, MeshBuilder.at(Vector3(0, P.chest_h * 0.95, 0.0)), 0.075, 0.03, 12, 5)
	_add(chest, mb.commit())
	# --- Hals
	mb = MeshBuilder.new()
	mb.cylinder(skin, MeshBuilder.at(Vector3(0, P.chest_h * 0.85, 0.0)), 0.055 if not skel else 0.025, 0.05 if not skel else 0.025, P.neck + 0.08, 10)
	_add(chest, mb.commit())
	# --- Arme
	for side in [-1, 1]:
		var sh: Node3D = sh_l if side < 0 else sh_r
		var el: Node3D = el_l if side < 0 else el_r
		var hd: Node3D = hand_l if side < 0 else hand_r
		mb = MeshBuilder.new()
		mb.ellipsoid(sleeves, MeshBuilder.at(Vector3(0, -0.01, 0)), Vector3(P.ua_r[0] * 1.35, P.ua_r[0] * 1.25, P.ua_r[0] * 1.3), 12, 8)
		mb.limb(sleeves, MeshBuilder.at(Vector3.ZERO), P.ua_r[0], P.ua_r[1], P.ua - 0.02, 10)
		_add(sh, mb.commit())
		mb = MeshBuilder.new()
		var fore_mat: Material = gloves if gear.has("hands") and _gear_type("hands") in ["platte", "kette"] else sleeves
		if look.get("bare_arms", false):
			fore_mat = skin
		mb.limb(fore_mat, MeshBuilder.at(Vector3.ZERO), P.fa_r[0], P.fa_r[1], P.fa - 0.03, 10)
		_add(el, mb.commit())
		mb = MeshBuilder.new()
		var hs: float = P.hand
		if skel:
			mb.ellipsoid(skin, MeshBuilder.at(Vector3(0, -0.04, 0)), Vector3(0.035, 0.04, 0.02), 6, 4)
			for k in 4:
				mb.beam(skin, Vector3(-0.03 + k * 0.02, -0.07, 0), Vector3(-0.03 + k * 0.02, -0.12, -0.02), Vector2(0.01, 0.01))
		else:
			mb.ellipsoid(gloves, MeshBuilder.at(Vector3(0, -0.045 * hs, 0)), Vector3(0.048, 0.055, 0.03) * hs, 10, 7)
			mb.ellipsoid(gloves, MeshBuilder.at_euler(Vector3(0, -0.1 * hs, -0.012 * hs), Vector3(0.6, 0, 0)), Vector3(0.045, 0.04, 0.028) * hs, 10, 6)
			mb.ellipsoid(gloves, MeshBuilder.at_euler(Vector3(-side * 0.04 * hs, -0.05 * hs, -0.025 * hs), Vector3(0.4, 0, side * 0.6)), Vector3(0.018, 0.035, 0.018) * hs, 6, 4)
			if gear.has("hands"):
				var gt := _gear_type("hands")
				var cuff := 0.07 if gt == "platte" else 0.058
				mb.cylinder(gloves, MeshBuilder.at(Vector3(0, 0.0, 0)), cuff * hs, cuff * 0.85 * hs, 0.1, 10)
		_add(hd, mb.commit())
	# --- Beine
	for side in [-1, 1]:
		var th: Node3D = th_l if side < 0 else th_r
		var kn: Node3D = kn_l if side < 0 else kn_r
		var ft: Node3D = ft_l if side < 0 else ft_r
		mb = MeshBuilder.new()
		mb.limb(legs, MeshBuilder.at(Vector3.ZERO), P.th_r[0], P.th_r[1], P.thigh - 0.02, 10)
		_add(th, mb.commit())
		mb = MeshBuilder.new()
		mb.ellipsoid(legs, MeshBuilder.at(Vector3(0, 0, -0.01)), Vector3(P.sh_r[0] * 1.15, P.sh_r[0] * 1.1, P.sh_r[0] * 1.15), 10, 7)
		mb.limb(legs, MeshBuilder.at(Vector3.ZERO), P.sh_r[0], P.sh_r[1], P.shin * 0.55, 10)
		mb.limb(boots, MeshBuilder.at(Vector3(0, -P.shin * 0.45, 0)), P.sh_r[1] * 1.25, P.sh_r[1] * 1.12, P.shin * 0.5, 10)
		var bt := _gear_type("feet")
		if bt == "platte" or bt == "kette" or look.get("boots_cuff", false):
			mb.cylinder(boots, MeshBuilder.at(Vector3(0, -P.shin * 0.5, 0)), P.sh_r[1] * 1.55, P.sh_r[1] * 1.45, 0.07, 12)
		if _gear_type("legs") == "platte":
			mb.ellipsoid(legs, MeshBuilder.at(Vector3(0, 0.0, -P.sh_r[0] * 0.9)), Vector3(0.06, 0.07, 0.04), 8, 6)
		_add(kn, mb.commit())
		mb = MeshBuilder.new()
		var fs: float = P.foot
		if skel:
			mb.ellipsoid(skin, MeshBuilder.at(Vector3(0, -0.03, -0.05)), Vector3(0.04, 0.03, 0.1), 6, 4)
		else:
			mb.ellipsoid(boots, MeshBuilder.at(Vector3(0, -0.035, -0.045 * fs)), Vector3(0.062, 0.055, 0.13) * fs, 12, 7, Color.WHITE, 0.0, 1.0, 0, -0.6, 1.0)
			mb.ellipsoid(boots, MeshBuilder.at(Vector3(0, -0.055, -0.13 * fs)), Vector3(0.058, 0.04, 0.07) * fs, 10, 6, Color.WHITE, 0.0, 1.0, 0, -0.6, 1.0)
		_add(ft, mb.commit())
	# --- Gürtel
	if not skel:
		mb = MeshBuilder.new()
		var belt := Mat.stylized(Color.html(str(look.get("belt", "#3a2416"))), Mat.P.LEATHER)
		mb.torus(belt, Transform3D(Basis.from_scale(Vector3(1.0, 1.0, P.belly_r.z / P.belly_r.x)), Vector3(0, P.spine * 0.12, 0)), P.belly_r.x * 0.98, 0.028, 16, 4)
		mb.box(Mat.stylized(Color.html("#d0a840"), Mat.P.GOLD), MeshBuilder.at(Vector3(0, P.spine * 0.12, -P.belly_r.z - 0.02)), Vector3(0.07, 0.06, 0.02))
		_add(spine, mb.commit())
	# --- Robe / Kleid / Schürze / Wappenrock
	if (robe or dress) and not skel:
		mb = MeshBuilder.new()
		var rmat := top if robe else _cloth(top_hex)
		var len: float = P.hip_h - 0.08
		mb.cylinder(rmat, MeshBuilder.at(Vector3(0, -len + 0.06, 0)), P.pelvis_r.x * (2.1 if robe else 2.3), P.pelvis_r.x * 1.05, len, 16, false)
		_add(hips, mb.commit())
	if look.has("apron"):
		mb = MeshBuilder.new()
		var ap := _cloth(look["apron"])
		mb.plane(ap, MeshBuilder.at(Vector3(0, 0.05, -P.belly_r.z - 0.04)), 0.3, 0.55, Color.WHITE, 1, -0.06)
		_add(hips, mb.commit())
	var tabard_hex = look.get("tabard")
	if tabard_hex == null and gear.has("chest") and _gear_type("chest") in ["platte", "kette"]:
		tabard_hex = _gear_vis("chest").get("c", null)
	if tabard_hex != null and not robe and not skel:
		mb = MeshBuilder.new()
		var tb := Mat.stylized(Color.html(str(tabard_hex)), Mat.P.CLOTH, {"wind": 0.25})
		mb.plane(tb, MeshBuilder.at(Vector3(0, 0.02, -P.pelvis_r.z - 0.02)), 0.26, 0.45, Color.WHITE, 3, -0.03)
		mb.plane(tb, MeshBuilder.at(Vector3(0, 0.02, P.pelvis_r.z + 0.02)), 0.26, 0.45, Color.WHITE, 3, 0.03)
		_add(hips, mb.commit(), false)
	# Plattenrock (Beintaschen)
	if _gear_type("chest") == "platte" or _gear_type("legs") == "platte":
		mb = MeshBuilder.new()
		var pm := _gear_mat("chest" if gear.has("chest") else "legs", "#9a9aa2")
		for sx in [-1.0, 1.0]:
			mb.ellipsoid(pm, MeshBuilder.at_euler(Vector3(sx * 0.13, -0.08, -0.02), Vector3(0, 0, sx * 0.25)), Vector3(0.1, 0.12, 0.13), 10, 6, Color.WHITE, 0, 1, 0, -0.2, 1.0)
		_add(hips, mb.commit())
	# --- Schultern
	_build_shoulders()
	# --- Umhang
	var cape_hex = look.get("cape")
	if gear.has("back"):
		cape_hex = _gear_vis("back").get("c", "#6a2a2a")
	if cape_hex != null and not skel:
		mb = MeshBuilder.new()
		var cm := Mat.stylized(Color.html(str(cape_hex)), Mat.P.CLOTH, {"c2": Color.html(str(cape_hex)).darkened(0.5), "wind": 0.6})
		var clen: float = P.hip_h + P.spine + 0.15
		mb.plane(cm, MeshBuilder.at(Vector3(0, 0, 0.02)), P.sh_w * 2.0, clen, Color.WHITE, 6, 0.25)
		_cape = _add(back_attach, mb.commit(), false)
	# --- Schwanz (Kobolde, Dämonen)
	if kind == "kobold" or kind == "demon":
		tail = _node("Tail", hips, Vector3(0, -0.02, P.pelvis_r.z * 0.9))
		mb = MeshBuilder.new()
		mb.beam(skin, Vector3.ZERO, Vector3(0, -0.15, 0.3), Vector2(0.05, 0.05))
		mb.beam(skin, Vector3(0, -0.15, 0.3), Vector3(0, -0.12, 0.55), Vector2(0.035, 0.035))
		if kind == "demon":
			mb.cylinder(skin, MeshBuilder.at_euler(Vector3(0, -0.12, 0.55), Vector3(PI * 0.5, 0, 0)), 0.06, 0.0, 0.12, 4)
		_add(tail, mb.commit())
	# --- Flügel (Feen, Dämonen)
	if kind == "fairy" or look.get("wings", false):
		var wing_c := Color.html(str(look.get("wing", "#c8f0ff")))
		var wm := Mat.transparent(Color(wing_c.r, wing_c.g, wing_c.b, 0.45))
		for sx in [-1.0, 1.0]:
			var w := _node("Wing", back_attach, Vector3(sx * 0.05, 0, 0.02))
			var wmb := MeshBuilder.new()
			wmb.ellipsoid(wm, MeshBuilder.at_euler(Vector3(sx * 0.28, 0.1, 0.05), Vector3(0, 0, sx * 0.5)), Vector3(0.3, 0.14, 0.01), 10, 4)
			wmb.ellipsoid(wm, MeshBuilder.at_euler(Vector3(sx * 0.2, -0.12, 0.05), Vector3(0, 0, -sx * 0.4)), Vector3(0.2, 0.09, 0.01), 10, 4)
			_add(w, wmb.commit(), false)
			var anim := AnimNode3D.new()
			anim.mode = "sway"
			anim.speed = 18.0
			anim.amount = 0.35
			w.get_parent().remove_child(w)
			anim.add_child(w)
			back_attach.add_child(anim)
	if look.get("demon_wings", false):
		var dm := Mat.stylized(Color.html(str(look.get("wing", "#4a1010"))), Mat.P.LEATHER, {"c2": Color.html("#1a0505")})
		for sx in [-1.0, 1.0]:
			var wmb := MeshBuilder.new()
			var outline := PackedVector2Array([Vector2(0, 0), Vector2(sx * 0.9, 0.5), Vector2(sx * 1.3, 0.2), Vector2(sx * 1.1, -0.3), Vector2(sx * 0.8, -0.15), Vector2(sx * 0.6, -0.5), Vector2(sx * 0.3, -0.2)])
			wmb.extrude(dm, MeshBuilder.at(Vector3(sx * 0.05, 0.05, 0.05)), outline, 0.02)
			_add(back_attach, wmb.commit())
	# Leuchtende Hände beim Zaubern
	_cast_glow_l = FxLib.glow_sprite(Color(1, 0.7, 0.3, 0.0), 0.32)
	_cast_glow_r = FxLib.glow_sprite(Color(1, 0.7, 0.3, 0.0), 0.32)
	_cast_glow_l.position = Vector3(0, -0.08, 0)
	_cast_glow_r.position = Vector3(0, -0.08, 0)
	hand_l.add_child(_cast_glow_l)
	hand_r.add_child(_cast_glow_r)
	_cast_glow_l.visible = false
	_cast_glow_r.visible = false


func _build_shoulders() -> void:
	var typ := _gear_type("shoulders")
	var npc_armor: bool = look.get("armor", false) and typ == ""
	if typ == "" and not npc_armor:
		return
	var vis := _gear_vis("shoulders") if typ != "" else {"q": 2}
	var q := int(vis.get("q", 2))
	var mat: Material = _gear_mat("shoulders", "#9a9aa2") if typ != "" else Mat.stylized(Color.html("#b8bcc6"), Mat.P.METAL, {"c2": Color.html(str(look.get("top", "#5a5a6a")))})
	var trim: Material = Mat.stylized(Color.html(str(vis.get("a", "#c9a040"))), Mat.P.GOLD, {"c2": Color.html("#6a4a10")})
	var glow = vis.get("g")
	var size = 1.0 + max(0, q - 2) * 0.18
	if typ == "" or typ == "platte":
		size *= 1.15
	for side in [-1, 1]:
		var sh: Node3D = sh_l if side < 0 else sh_r
		var mb := MeshBuilder.new()
		var r = Vector3(0.13, 0.1, 0.13) * size
		if typ == "stoff":
			r = Vector3(0.1, 0.07, 0.11) * size
		mb.ellipsoid(mat, MeshBuilder.at_euler(Vector3(side * 0.03, 0.02, 0), Vector3(0, 0, -side * 0.35)), r, 14, 8, Color.WHITE, 0.0, 1.0, 0, -0.25, 1.0)
		if typ == "platte" or typ == "":
			mb.ellipsoid(mat, MeshBuilder.at_euler(Vector3(side * 0.07, -0.06, 0), Vector3(0, 0, -side * 0.6)), r * Vector3(0.85, 0.7, 0.95), 12, 6, Color.WHITE, 0.0, 1.0, 0, -0.2, 1.0)
			if q >= 3:
				mb.torus(trim, MeshBuilder.at_euler(Vector3(side * 0.03, 0.0, 0), Vector3(0, 0, -side * 0.35)), r.x * 0.98, 0.012 * size, 16, 4)
			if q >= 4:
				for k in 3:
					var a := -0.5 + k * 0.5
					mb.cylinder(trim, MeshBuilder.at_euler(Vector3(side * 0.04, 0.06 * size, a * 0.08), Vector3(a * 0.6, 0, -side * 0.5)), 0.025 * size, 0.0, 0.16 * size, 5)
		elif typ == "kette" or typ == "leder":
			mb.ellipsoid(mat, MeshBuilder.at_euler(Vector3(side * 0.06, -0.05, 0), Vector3(0, 0, -side * 0.6)), r * Vector3(0.8, 0.5, 0.9), 10, 5, Color.WHITE, 0.0, 1.0, 0, -0.2, 1.0)
		if glow != null and str(glow) != "":
			mb.ellipsoid(Mat.emissive(Color.html(str(glow)), 3.0), MeshBuilder.at(Vector3(side * 0.08, 0.04, -0.09) * size), Vector3(0.025, 0.025, 0.02) * size, 6, 4)
		_add(sh, mb.commit())


# =============================================================================== Kopf
func _build_head() -> void:
	var skin := _mat_skin()
	var hr: float = P.head_r
	var mb := MeshBuilder.new()
	var skel := kind in ["skeleton", "undead"]
	var dark := Mat.stylized(Color.html("#120c0a"), Mat.P.PLAIN, {"rim": 0.0})
	var white := Mat.stylized(Color.html("#f4f0ea"), Mat.P.PLAIN, {"rough": 0.3})
	var eye_c := Color.html(str(look.get("eye_color", "#3a5a8a")))
	var iris := Mat.stylized(eye_c, Mat.P.PLAIN, {"rough": 0.2, "emis": eye_c * 0.15})
	var big_eyes: bool = str(look.get("eyes", "")) == "big"
	if skel:
		mb.ellipsoid(skin, MeshBuilder.at(Vector3(0, 0.02, 0)), Vector3(hr * 0.88, hr * 0.95, hr), 14, 10)
		mb.box(skin, MeshBuilder.at(Vector3(0, -hr * 0.62, -hr * 0.35)), Vector3(hr * 1.1, hr * 0.3, hr * 0.9))
		var eg := Color.html(str(look.get("eye_glow", "#60c0ff")))
		var em := Mat.emissive(eg, 4.0)
		for sx in [-1.0, 1.0]:
			mb.ellipsoid(dark, MeshBuilder.at(Vector3(sx * hr * 0.36, 0.0, -hr * 0.78)), Vector3(hr * 0.24, hr * 0.26, hr * 0.12), 8, 6)
			mb.ellipsoid(em, MeshBuilder.at(Vector3(sx * hr * 0.36, 0.0, -hr * 0.86)), Vector3(hr * 0.09, hr * 0.09, hr * 0.05), 6, 4)
		mb.box(dark, MeshBuilder.at(Vector3(0, -hr * 0.3, -hr * 0.9)), Vector3(hr * 0.15, hr * 0.15, hr * 0.06))
		for k in 6:
			mb.box(white, MeshBuilder.at(Vector3(-hr * 0.38 + k * hr * 0.15, -hr * 0.55, -hr * 0.82)), Vector3(hr * 0.1, hr * 0.12, hr * 0.06))
		_add(head, mb.commit())
		_build_headgear()
		return
	if kind == "kobold":
		mb.ellipsoid(skin, MeshBuilder.at(Vector3(0, 0.02, 0.02)), Vector3(hr * 0.95, hr * 0.85, hr * 0.95), 14, 10)
		mb.ellipsoid(skin, MeshBuilder.at(Vector3(0, -hr * 0.25, -hr * 0.85)), Vector3(hr * 0.5, hr * 0.38, hr * 0.6), 12, 8)
		mb.ellipsoid(dark, MeshBuilder.at(Vector3(0, -hr * 0.12, -hr * 1.42)), Vector3(hr * 0.16, hr * 0.12, hr * 0.12), 8, 6)
		for sx in [-1.0, 1.0]:
			mb.ellipsoid(skin, MeshBuilder.at_euler(Vector3(sx * hr * 0.95, hr * 0.25, 0.0), Vector3(0, 0, sx * -0.6)), Vector3(hr * 0.55, hr * 0.12, hr * 0.38), 10, 6)
			var pink := Mat.stylized(Color.html("#d89090"), Mat.P.SKIN)
			mb.ellipsoid(pink, MeshBuilder.at_euler(Vector3(sx * hr * 1.0, hr * 0.27, -hr * 0.06), Vector3(0, 0, sx * -0.6)), Vector3(hr * 0.42, hr * 0.06, hr * 0.26), 8, 4)
			if not (look.get("eyepatch", false) and sx > 0):
				mb.ellipsoid(dark, MeshBuilder.at(Vector3(sx * hr * 0.38, hr * 0.12, -hr * 0.78)), Vector3(hr * 0.13, hr * 0.15, hr * 0.08), 8, 6)
				mb.ellipsoid(white, MeshBuilder.at(Vector3(sx * hr * 0.35, hr * 0.17, -hr * 0.84)), Vector3(hr * 0.04, hr * 0.04, hr * 0.02), 4, 3)
		for sx in [-1.0, 1.0]:
			mb.cylinder(white, MeshBuilder.at_euler(Vector3(sx * hr * 0.2, -hr * 0.55, -hr * 1.15), Vector3(PI, 0, 0)), hr * 0.05, 0.0, hr * 0.18, 4)
		_add(head, mb.commit())
		_build_face_extras()
		_build_headgear()
		return
	# --- Mensch, Zwerg, Dämon, Riese, Fee
	var hs: float = P.head_s
	mb.ellipsoid(skin, MeshBuilder.at(Vector3(0, 0.0, 0.0)), Vector3(hr * 0.9, hr, hr * 0.95) * hs, 16, 12)
	# Kiefer / Kinn
	var jaw := Vector3(hr * 0.7, hr * 0.42, hr * 0.72) if not female else Vector3(hr * 0.6, hr * 0.38, hr * 0.64)
	mb.ellipsoid(skin, MeshBuilder.at(Vector3(0, -hr * 0.42, -hr * 0.14)), jaw, 14, 8)
	# Wangen
	for sx in [-1.0, 1.0]:
		mb.ellipsoid(skin, MeshBuilder.at(Vector3(sx * hr * 0.4, -hr * 0.2, -hr * 0.62)), Vector3(hr * 0.28, hr * 0.24, hr * 0.26), 8, 6)
	# Nase
	mb.ellipsoid(skin, MeshBuilder.at_euler(Vector3(0, -hr * 0.1, -hr * 0.95), Vector3(-0.3, 0, 0)), Vector3(hr * 0.15, hr * 0.3, hr * 0.22) * (0.8 if female else 1.0), 8, 6)
	mb.ellipsoid(skin, MeshBuilder.at(Vector3(0, -hr * 0.3, -hr * 1.0)), Vector3(hr * 0.17, hr * 0.12, hr * 0.13) * (0.8 if female else 1.0), 8, 5)
	# Ohren
	var elf_ears: bool = look.get("pointy_ears", false) or kind == "fairy" or kind == "elf"
	for sx in [-1.0, 1.0]:
		if elf_ears:
			mb.cylinder(skin, MeshBuilder.at_euler(Vector3(sx * hr * 0.85, 0.0, 0.0), Vector3(0, 0, sx * -1.2)), hr * 0.14, 0.0, hr * 0.7, 6)
		else:
			mb.ellipsoid(skin, MeshBuilder.at(Vector3(sx * hr * 0.88, -hr * 0.05, 0.02)), Vector3(hr * 0.12, hr * 0.22, hr * 0.14), 8, 6)
	# Augen (mandelförmig, deutlich sichtbar)
	var er := hr * (0.2 if big_eyes else 0.16)
	var brow := Mat.stylized(_hair_color().darkened(0.2), Mat.P.FUR)
	for sx in [-1.0, 1.0]:
		var blind: bool = look.get("blindfold", false)
		var patched: bool = look.get("eyepatch", false) and sx > 0
		var ep := Vector3(sx * hr * 0.34, hr * 0.08, -hr * 0.8)
		if not (blind or patched):
			mb.ellipsoid(dark, MeshBuilder.at(ep + Vector3(0, 0, 0.004)), Vector3(er * 1.22, er * 0.82, er * 0.5), 10, 6)
			mb.ellipsoid(white, MeshBuilder.at(ep + Vector3(0, 0, -0.002)), Vector3(er * 1.12, er * 0.72, er * 0.5), 10, 7)
			mb.ellipsoid(iris, MeshBuilder.at(ep + Vector3(0, 0, -er * 0.32)), Vector3(er * 0.55, er * 0.6, er * 0.25), 8, 6)
			mb.ellipsoid(dark, MeshBuilder.at(ep + Vector3(0, 0, -er * 0.46)), Vector3(er * 0.28, er * 0.32, er * 0.1), 6, 4)
			mb.ellipsoid(white, MeshBuilder.at(ep + Vector3(er * 0.15, er * 0.18, -er * 0.52)), Vector3(er * 0.1, er * 0.1, er * 0.05), 4, 3)
		# Brauen (kräftig)
		mb.box(brow, MeshBuilder.at_euler(ep + Vector3(0, er * 1.25, -er * 0.25), Vector3(-0.2, 0, sx * (0.22 if not female else 0.08))), Vector3(er * 2.6, er * (0.55 if not female else 0.35), er * 0.7))
	# Mund
	var lip := Mat.stylized(Color.html("#8a3a34") if not female else Color.html("#b0464e"), Mat.P.PLAIN)
	mb.box(Mat.stylized(Color.html("#3a1410"), Mat.P.PLAIN), MeshBuilder.at(Vector3(0, -hr * 0.5, -hr * 0.84)), Vector3(hr * 0.46, hr * 0.05, hr * 0.06))
	mb.ellipsoid(lip, MeshBuilder.at(Vector3(0, -hr * 0.56, -hr * 0.8)), Vector3(hr * 0.2, hr * 0.06, hr * 0.06), 8, 4)
	if kind == "demon" or look.get("horns", false):
		var horn := Mat.stylized(Color.html(str(look.get("horn_color", "#2a2420"))), Mat.P.BONE, {"c2": Color.html("#0a0808")})
		for sx in [-1.0, 1.0]:
			mb.cylinder(horn, MeshBuilder.at_euler(Vector3(sx * hr * 0.5, hr * 0.7, -hr * 0.1), Vector3(-0.5, 0, sx * -0.5)), hr * 0.22, 0.0, hr * 1.4, 8)
	if kind == "giant":
		var ice := Mat.stylized(Color.html("#a8e0ff"), Mat.P.ICE, {"emis": Color.html("#4080c0")})
		for k in 5:
			var a := -0.8 + k * 0.4
			mb.cylinder(ice, MeshBuilder.at_euler(Vector3(sin(a) * hr * 0.6, hr * 0.75, cos(a) * hr * 0.2), Vector3(-0.3, 0, -a)), hr * 0.15, 0.0, hr * 0.8, 5)
	_add(head, mb.commit())
	_build_hair()
	_build_face_extras()
	_build_headgear()


func _build_hair() -> void:
	var style: String = str(look.get("hair_style", "short"))
	if gear.has("head") and _gear_type("head") in ["platte", "kette"]:
		style = "none"
	var hc := _hair_color()
	var hair := Mat.stylized(hc, Mat.P.FUR, {"c2": hc.darkened(0.45), "rim": 0.2})
	var hr: float = P.head_r
	var mb := MeshBuilder.new()
	match style:
		"short":
			mb.ellipsoid(hair, _cap_xf(hr), Vector3(hr * 1.0, hr * 1.0, hr * 1.02), 14, 9, Color.WHITE, 0.12, 2.5, 3, -0.12, 1.0)
			mb.ellipsoid(hair, MeshBuilder.at_euler(Vector3(hr * 0.2, hr * 0.68, -hr * 0.5), Vector3(0.7, 0, -0.35)), Vector3(hr * 0.55, hr * 0.2, hr * 0.32), 8, 5)
		"long", "wild":
			var lump := 0.3 if style == "wild" else 0.12
			mb.ellipsoid(hair, _cap_xf(hr), Vector3(hr, hr, hr * 1.02) * (1.12 if style == "wild" else 1.03), 14, 9, Color.WHITE, lump, 2.0, 7, -0.25, 1.0)
			mb.ellipsoid(hair, MeshBuilder.at(Vector3(0, -hr * 0.7, hr * 0.55)), Vector3(hr * 0.88, hr * 1.35, hr * 0.42), 12, 8, Color.WHITE, lump, 2.0, 9)
			for sx in [-1.0, 1.0]:
				mb.ellipsoid(hair, MeshBuilder.at(Vector3(sx * hr * 0.82, -hr * 0.6, hr * 0.25)), Vector3(hr * 0.24, hr * 1.0, hr * 0.38), 8, 6, Color.WHITE, lump, 2.0, 11)
		"ponytail", "braid":
			mb.ellipsoid(hair, _cap_xf(hr), Vector3(hr, hr, hr * 1.02), 14, 9, Color.WHITE, 0.08, 2.0, 5, -0.15, 1.0)
			for k in 6:
				var t := float(k)
				var rr := hr * (0.24 - t * 0.02)
				mb.ellipsoid(hair, MeshBuilder.at(Vector3(0, hr * (0.1 - t * 0.38), hr * (1.05 + t * 0.05))), Vector3(rr, rr * 1.4, rr), 8, 6)
		"bun":
			mb.ellipsoid(hair, _cap_xf(hr), Vector3(hr, hr, hr * 1.02), 14, 9, Color.WHITE, 0.06, 2.0, 5, -0.15, 1.0)
			mb.ellipsoid(hair, MeshBuilder.at(Vector3(0, hr * 0.7, hr * 0.7)), Vector3(hr * 0.45, hr * 0.42, hr * 0.42), 10, 8, Color.WHITE, 0.1, 3.0, 6)
		"mohawk":
			for k in 7:
				var a := -0.9 + k * 0.3
				mb.cylinder(hair, MeshBuilder.at_euler(Vector3(0, sin(PI * 0.5 + a) * hr * 0.9, cos(PI * 0.5 + a) * hr * -0.9), Vector3(-a, 0, 0)), hr * 0.18, 0.0, hr * 0.7, 5)
		"tonsure":
			mb.torus(hair, MeshBuilder.at(Vector3(0, hr * 0.15, 0.0)), hr * 0.9, hr * 0.16, 16, 5)
		"bald", "none":
			pass
		_:
			mb.ellipsoid(hair, _cap_xf(hr), Vector3(hr * 1.0, hr * 1.0, hr * 1.02), 14, 9, Color.WHITE, 0.12, 2.5, 3, -0.12, 1.0)
	# Bart
	var beard = look.get("beard")
	if kind == "dwarf" and beard == null:
		beard = hc.to_html()
	if beard != null and str(beard) != "" and not female:
		var bc := Color.html(str(beard)) if str(beard).begins_with("#") else hc
		var bm := Mat.stylized(bc, Mat.P.FUR, {"c2": bc.darkened(0.45)})
		var long_beard: bool = kind == "dwarf" or str(look.get("beard_style", "")) == "long"
		if long_beard:
			mb.ellipsoid(bm, MeshBuilder.at(Vector3(0, -hr * 1.05, -hr * 0.55)), Vector3(hr * 0.75, hr * 1.25, hr * 0.5), 12, 8, Color.WHITE, 0.2, 2.5, 4)
			mb.torus(Mat.stylized(Color.html("#c8a040"), Mat.P.GOLD), MeshBuilder.at(Vector3(0, -hr * 1.7, -hr * 0.55)), hr * 0.2, hr * 0.05, 10, 4)
		else:
			mb.ellipsoid(bm, MeshBuilder.at(Vector3(0, -hr * 0.62, -hr * 0.42)), Vector3(hr * 0.78, hr * 0.55, hr * 0.55), 12, 8, Color.WHITE, 0.18, 3.0, 4)
		for sx in [-1.0, 1.0]:
			mb.ellipsoid(bm, MeshBuilder.at_euler(Vector3(sx * hr * 0.18, -hr * 0.32, -hr * 0.9), Vector3(0, 0, sx * 0.5)), Vector3(hr * 0.22, hr * 0.07, hr * 0.09), 8, 5)
	if not mb.is_empty():
		_add(head, mb.commit())


## Haarkappe: nach hinten gekippt, damit Stirn und Augen frei bleiben
func _cap_xf(hr: float) -> Transform3D:
	return MeshBuilder.at_euler(Vector3(0, hr * 0.1, hr * 0.12), Vector3(0.62, 0, 0))


func _build_face_extras() -> void:
	var hr: float = P.head_r
	var mb := MeshBuilder.new()
	var dark := Mat.stylized(Color.html("#141010"), Mat.P.LEATHER)
	if look.get("eyepatch", false):
		mb.ellipsoid(dark, MeshBuilder.at(Vector3(hr * 0.36, hr * 0.06, -hr * 0.86)), Vector3(hr * 0.22, hr * 0.2, hr * 0.06), 8, 6)
		mb.torus(dark, MeshBuilder.at_euler(Vector3(0, hr * 0.15, 0), Vector3(0.35, 0, 0.15)), hr * 0.98, hr * 0.03, 16, 3)
	if look.get("blindfold", false):
		var cloth := Mat.stylized(Color.html(str(look.get("blindfold_color", "#3a3050"))), Mat.P.CLOTH)
		mb.torus(cloth, Transform3D(Basis.from_scale(Vector3(1, 1, 1.05)), Vector3(0, hr * 0.06, 0.0)), hr * 0.95, hr * 0.1, 16, 5)
	if look.get("monocle", false):
		mb.torus(Mat.stylized(Color.html("#d0a840"), Mat.P.GOLD), MeshBuilder.at_euler(Vector3(-hr * 0.36, hr * 0.06, -hr * 0.92), Vector3(PI * 0.5, 0, 0)), hr * 0.18, hr * 0.025, 12, 4)
	if not mb.is_empty():
		_add(head, mb.commit())


func _build_headgear() -> void:
	var hr: float = P.head_r
	var mb := MeshBuilder.new()
	var hat: String = str(look.get("hat", ""))
	if look.get("crown", false):
		hat = "crown"
	if look.get("hood", false):
		hat = "hood"
	if look.get("helm", false):
		hat = "helm"
	var gtyp := _gear_type("head")
	if gtyp != "":
		hat = {"platte": "greathelm", "kette": "helm", "leder": "leathercap", "stoff": "circlet"}.get(gtyp, "circlet")
	var gm: Material = _gear_mat("head", "#8a8a94") if gtyp != "" else Mat.stylized(Color.html("#9aa0aa"), Mat.P.METAL, {"c2": Color.html("#3a3a44")})
	var gold := Mat.stylized(Color.html("#e0b648"), Mat.P.GOLD, {"c2": Color.html("#7a5a18")})
	var vis := _gear_vis("head")
	var q := int(vis.get("q", 1))
	match hat:
		"crown":
			mb.torus(gold, MeshBuilder.at(Vector3(0, hr * 0.62, 0.0)), hr * 0.78, hr * 0.08, 16, 4)
			mb.cylinder(gold, MeshBuilder.at(Vector3(0, hr * 0.55, 0)), hr * 0.8, hr * 0.84, hr * 0.28, 16, false)
			for k in 8:
				var a := TAU * k / 8.0
				mb.cylinder(gold, MeshBuilder.at(Vector3(cos(a) * hr * 0.82, hr * 0.8, sin(a) * hr * 0.82)), hr * 0.09, 0.0, hr * 0.32, 4)
				mb.ellipsoid(Mat.stylized(Color.html(["#e02040", "#2060e0", "#20c060"][k % 3]), Mat.P.ICE), MeshBuilder.at(Vector3(cos(a) * hr * 0.86, hr * 0.68, sin(a) * hr * 0.86)), Vector3(hr * 0.06, hr * 0.06, hr * 0.06), 6, 4)
		"jester":
			var c1 := Mat.stylized(Color.html(str(look.get("top", "#d43c8f"))), Mat.P.CLOTH)
			var c2 := Mat.stylized(Color.html(str(look.get("bottom", "#2fb5a8"))), Mat.P.CLOTH)
			mb.ellipsoid(c1, MeshBuilder.at(Vector3(0, hr * 0.25, 0.02)), Vector3(hr * 1.02, hr * 0.85, hr * 1.02), 12, 8, Color.WHITE, 0, 1, 0, -0.1, 1.0)
			for sx in [-1.0, 1.0]:
				var cm := c1 if sx < 0 else c2
				mb.beam(cm, Vector3(sx * hr * 0.4, hr * 0.8, 0), Vector3(sx * hr * 1.4, hr * 1.5, hr * 0.2), Vector2(hr * 0.35, hr * 0.35))
				mb.beam(cm, Vector3(sx * hr * 1.4, hr * 1.5, hr * 0.2), Vector3(sx * hr * 1.8, hr * 0.9, hr * 0.3), Vector2(hr * 0.2, hr * 0.2))
				mb.ellipsoid(gold, MeshBuilder.at(Vector3(sx * hr * 1.82, hr * 0.85, hr * 0.3)), Vector3(hr * 0.15, hr * 0.15, hr * 0.15), 6, 4)
		"straw":
			var straw := Mat.stylized(Color.html("#e0c070"), Mat.P.THATCH, {"c2": Color.html("#9a7a30"), "scale": 3.0})
			mb.cylinder(straw, MeshBuilder.at(Vector3(0, hr * 0.5, 0)), hr * 2.0, hr * 2.0, hr * 0.06, 18)
			mb.cylinder(straw, MeshBuilder.at(Vector3(0, hr * 0.5, 0)), hr * 0.92, hr * 0.7, hr * 0.7, 14)
			mb.torus(Mat.stylized(Color.html("#8a2a1a"), Mat.P.CLOTH), MeshBuilder.at(Vector3(0, hr * 0.65, 0)), hr * 0.85, hr * 0.06, 14, 4)
		"feather":
			var fm := Mat.stylized(Color.html(str(look.get("top", "#2f8a4a"))), Mat.P.CLOTH)
			mb.ellipsoid(fm, MeshBuilder.at_euler(Vector3(0, hr * 0.55, 0.0), Vector3(0, 0, 0.15)), Vector3(hr * 1.05, hr * 0.42, hr * 1.1), 12, 7, Color.WHITE, 0, 1, 0, -0.3, 1.0)
			var feather := Mat.stylized(Color.html("#e04030"), Mat.P.PLAIN, {"rim": 0.3})
			mb.ellipsoid(feather, MeshBuilder.at_euler(Vector3(hr * 0.6, hr * 1.0, hr * 0.4), Vector3(-0.8, 0, -0.5)), Vector3(hr * 0.12, hr * 0.8, hr * 0.06), 8, 6)
		"hood":
			var hm := Mat.stylized(Color.html(str(look.get("hood_color", look.get("top", "#4a3a2a")))), Mat.P.CLOTH)
			mb.ellipsoid(hm, MeshBuilder.at(Vector3(0, hr * 0.12, hr * 0.12)), Vector3(hr * 1.12, hr * 1.12, hr * 1.12), 14, 10, Color.WHITE, 0.05, 2.0, 2, -0.55, 1.0)
			mb.cylinder(hm, MeshBuilder.at_euler(Vector3(0, hr * 0.5, hr * 0.7), Vector3(0.8, 0, 0)), hr * 0.5, 0.0, hr * 0.9, 8)
		"helm", "greathelm":
			var great := hat == "greathelm"
			mb.ellipsoid(gm, MeshBuilder.at(Vector3(0, hr * 0.1, 0.0)), Vector3(hr * 1.08, hr * 1.08, hr * 1.1), 14, 10, Color.WHITE, 0, 1, 0, -0.35 if not great else -0.95, 1.0)
			mb.torus(gm, MeshBuilder.at(Vector3(0, -hr * 0.18, 0)), hr * 1.08, hr * 0.06, 16, 4)
			if great:
				mb.box(Mat.stylized(Color.html("#0c0a0a"), Mat.P.PLAIN), MeshBuilder.at(Vector3(0, hr * 0.05, -hr * 1.06)), Vector3(hr * 1.1, hr * 0.12, hr * 0.06))
				mb.box(gm, MeshBuilder.at(Vector3(0, -hr * 0.4, -hr * 1.0)), Vector3(hr * 0.12, hr * 0.6, hr * 0.12))
				if q >= 3:
					mb.box(gold, MeshBuilder.at(Vector3(0, hr * 1.05, 0.0)), Vector3(hr * 0.12, hr * 0.35, hr * 1.4))
				if q >= 4:
					for sx in [-1.0, 1.0]:
						mb.cylinder(gold, MeshBuilder.at_euler(Vector3(sx * hr * 0.9, hr * 0.5, 0), Vector3(0, 0, sx * -1.0)), hr * 0.16, 0.0, hr * 0.9, 6)
			else:
				mb.box(gm, MeshBuilder.at(Vector3(0, -hr * 0.2, -hr * 1.08)), Vector3(hr * 0.12, hr * 0.5, hr * 0.06))
				mb.cylinder(gm, MeshBuilder.at(Vector3(0, hr * 1.05, 0)), hr * 0.12, 0.0, hr * 0.35, 6)
		"leathercap":
			mb.ellipsoid(gm, MeshBuilder.at(Vector3(0, hr * 0.15, 0.03)), Vector3(hr * 1.06, hr * 0.98, hr * 1.06), 14, 9, Color.WHITE, 0, 1, 0, -0.2, 1.0)
			mb.torus(gm, MeshBuilder.at(Vector3(0, hr * 0.05, 0.0)), hr * 1.04, hr * 0.05, 16, 4)
		"circlet":
			mb.torus(gold, MeshBuilder.at_euler(Vector3(0, hr * 0.35, 0.0), Vector3(-0.2, 0, 0)), hr * 0.92, hr * 0.04, 16, 4)
			var gem := Color.html(str(vis.get("g", "#60a0ff")))
			mb.ellipsoid(Mat.emissive(gem, 2.0), MeshBuilder.at(Vector3(0, hr * 0.48, -hr * 0.9)), Vector3(hr * 0.08, hr * 0.1, hr * 0.05), 6, 4)
		"mining":
			var hm := Mat.stylized(Color.html("#8a6a30"), Mat.P.METAL)
			mb.ellipsoid(hm, MeshBuilder.at(Vector3(0, hr * 0.3, 0.0)), Vector3(hr * 1.05, hr * 0.8, hr * 1.05), 12, 8, Color.WHITE, 0, 1, 0, 0.0, 1.0)
			mb.cylinder(hm, MeshBuilder.at(Vector3(0, hr * 0.3, 0)), hr * 1.25, hr * 1.25, hr * 0.06, 16)
			mb.cylinder(Mat.stylized(Color.html("#f0e6c8")), MeshBuilder.at(Vector3(0, hr * 1.05, 0)), hr * 0.12, hr * 0.12, hr * 0.4, 8)
	if not mb.is_empty():
		_add(head, mb.commit())
	if hat == "mining":
		var f := FxLib.fire(0.12, Color(1, 0.75, 0.3), true)
		f.position = Vector3(0, hr * 1.5, 0)
		head.add_child(f)


# =============================================================================== Ausrüstung
func _apply_gear() -> void:
	if _weapon_r:
		_weapon_r.queue_free()
		_weapon_r = null
	if _weapon_l:
		_weapon_l.queue_free()
		_weapon_l = null
	var main_kind := ""
	var main_vis := {}
	if gear.has("main_hand"):
		main_kind = WeaponModels.kind_for_item(gear["main_hand"])
		main_vis = _gear_vis("main_hand")
	elif look.has("held"):
		main_kind = str(look["held"])
	if main_kind != "":
		_weapon_r = WeaponModels.make(main_kind, main_vis)
		if main_kind == "bow":
			hand_l.add_child(_weapon_r)
			_weapon_r.position = Vector3(0, -0.07, -0.02)
			_weapon_r.rotation = Vector3(0, 0, 0)
		else:
			hand_r.add_child(_weapon_r)
			_weapon_r.position = Vector3(0, -0.075, -0.015)
			_weapon_r.rotation = Vector3(-PI * 0.5, 0, 0)
			if main_kind in ["staff", "spear", "pitchfork", "rod", "torch", "lute", "bell", "lantern"]:
				_weapon_r.rotation = Vector3(-PI * 0.5 + 0.3, 0, 0)
			if main_kind == "lantern":
				_weapon_r.rotation = Vector3.ZERO
			if main_kind == "lute":
				_weapon_r.rotation = Vector3(-0.3, 0.2, 1.2)
	var off_kind := ""
	var off_vis := {}
	if gear.has("off_hand"):
		off_kind = WeaponModels.kind_for_item(gear["off_hand"])
		off_vis = _gear_vis("off_hand")
	elif look.get("shield", false):
		off_kind = "shield"
		off_vis = {"c": look.get("shield_color", look.get("cape", "#2d4f9a")), "q": 2}
	elif look.has("offhand"):
		off_kind = str(look["offhand"])
	if off_kind != "":
		_weapon_l = WeaponModels.make(off_kind, off_vis)
		if off_kind.begins_with("shield"):
			el_l.add_child(_weapon_l)
			_weapon_l.position = Vector3(-0.09, -P.fa * 0.55, -0.02)
			_weapon_l.rotation = Vector3(0, -PI * 0.5, 0)
		else:
			hand_l.add_child(_weapon_l)
			_weapon_l.position = Vector3(0, -0.08, -0.02)
			_weapon_l.rotation = Vector3(-PI * 0.5, 0, 0)
			if off_kind == "book":
				_weapon_l.rotation = Vector3(-0.4, 0.3, 0)
	# Köcher für Bogenschützen
	if main_kind == "bow":
		var mb := MeshBuilder.new()
		var lm := Mat.stylized(Color.html("#6a4422"), Mat.P.LEATHER)
		mb.cylinder(lm, MeshBuilder.at_euler(Vector3(0.05, -0.35, 0.05), Vector3(0, 0, 0.4)), 0.07, 0.08, 0.6, 10)
		var fl := Mat.stylized(Color.html("#e8e0d0"), Mat.P.PLAIN)
		for k in 5:
			mb.beam(fl, Vector3(-0.08 + k * 0.03, 0.15, 0.06), Vector3(-0.12 + k * 0.035, 0.3, 0.06), Vector2(0.025, 0.006))
		_add(back_attach, mb.commit())
	_update_weapon_style()


func _update_weapon_style() -> void:
	var main := ""
	if gear.has("main_hand"):
		main = WeaponModels.kind_for_item(gear["main_hand"])
	elif look.has("held"):
		main = str(look["held"])
	var off := ""
	if gear.has("off_hand"):
		off = WeaponModels.kind_for_item(gear["off_hand"])
	elif look.get("shield", false):
		off = "shield"
	if main in ["sword2h", "axe2h", "hammer2h"]:
		weapon_style = "2h"
	elif main == "bow":
		weapon_style = "bow"
	elif main == "staff":
		weapon_style = "staff"
	elif main == "katana":
		weapon_style = "katana"
	elif main in ["sword", "axe", "mace", "dagger", "wand"] and off in ["sword", "axe", "mace", "dagger"]:
		weapon_style = "dual"
	elif off.begins_with("shield"):
		weapon_style = "shield"
	elif main != "":
		weapon_style = "1h"
	else:
		weapon_style = "unarmed"


func set_gear(new_gear: Dictionary) -> void:
	gear = new_gear
	build()


# =============================================================================== Animation
func attack(kind_override := "") -> void:
	_attack_kind = kind_override if kind_override != "" else weapon_style
	_attack_dur = 0.55 if _attack_kind != "2h" else 0.7
	_attack_t = 0.0


func cast_release() -> void:
	_release_t = 0.0


func hit_react() -> void:
	if _hit_t < 0.0:
		_hit_t = 0.0


func set_dead(v: bool) -> void:
	if v and not dead:
		_death_t = 0.0
	dead = v


func _lerp_rot(n: Node3D, target: Vector3, k: float) -> void:
	n.rotation = n.rotation.lerp(target, k)


func _process(delta: float) -> void:
	if body == null:
		return
	_t += delta
	var k := clampf(delta * 12.0, 0.0, 1.0)
	var pose := {}
	# Grundhaltung
	var hunch: float = P.hunch
	pose["hips_y"] = 0.0
	pose["spine"] = Vector3(hunch * 0.5, 0, 0)
	pose["chest"] = Vector3(hunch * 0.5, 0, 0)
	pose["neck"] = Vector3(-hunch * 0.8, 0, 0)
	pose["sh_l"] = Vector3(0.05, 0, -0.12)
	pose["sh_r"] = Vector3(0.05, 0, 0.12)
	pose["el_l"] = Vector3(0.25, 0, 0)
	pose["el_r"] = Vector3(0.25, 0, 0)
	pose["th_l"] = Vector3(0, 0, -0.03)
	pose["th_r"] = Vector3(0, 0, 0.03)
	pose["kn_l"] = Vector3(0, 0, 0)
	pose["kn_r"] = Vector3(0, 0, 0)
	pose["ft_l"] = Vector3(0, 0, 0)
	pose["ft_r"] = Vector3(0, 0, 0)
	pose["body_rot"] = Vector3.ZERO
	pose["body_y"] = 0.0
	# Atmen
	var breath := sin(_t * 1.6) * 0.012
	pose["chest"].x += breath
	pose["sh_l"].z -= breath
	pose["sh_r"].z += breath
	if dead:
		_death_t += delta
		var d := clampf(_death_t / 0.6, 0.0, 1.0)
		var e := d * d * (3.0 - 2.0 * d)
		pose["body_rot"] = Vector3(-PI * 0.5 * e, 0, 0.1 * e)
		pose["body_y"] = 0.12 * e
		pose["sh_l"] = Vector3(-2.6 * e, 0, -0.5)
		pose["sh_r"] = Vector3(-2.4 * e, 0, 0.6)
		pose["kn_l"] = Vector3(-0.6 * e, 0, 0)
		pose["th_l"] = Vector3(0.3 * e, 0, -0.1)
		pose["neck"] = Vector3(-0.3 * e, 0.3, 0)
		_apply_pose(pose, k)
		_set_cast_glow(false)
		return
	if sitting or mounted:
		pose["hips_y"] = -P.hip_h + 0.42 if sitting else -0.05
		pose["th_l"] = Vector3(1.5, 0, -0.15 if sitting else -0.5)
		pose["th_r"] = Vector3(1.5, 0, 0.15 if sitting else 0.5)
		pose["kn_l"] = Vector3(-1.5, 0, 0)
		pose["kn_r"] = Vector3(-1.5, 0, 0)
		pose["sh_l"] = Vector3(0.4, 0, -0.15)
		pose["sh_r"] = Vector3(0.4, 0, 0.15)
		pose["el_l"] = Vector3(0.9, 0, 0)
		pose["el_r"] = Vector3(0.9, 0, 0)
		if mounted:
			pose["hips_y"] = 0.0
			pose["th_l"] = Vector3(0.9, 0, -0.55)
			pose["th_r"] = Vector3(0.9, 0, 0.55)
			pose["kn_l"] = Vector3(-1.4, 0, 0)
			pose["kn_r"] = Vector3(-1.4, 0, 0)
	elif airborne:
		pose["th_l"] = Vector3(0.7, 0, -0.05)
		pose["th_r"] = Vector3(0.2, 0, 0.05)
		pose["kn_l"] = Vector3(-1.2, 0, 0)
		pose["kn_r"] = Vector3(-0.6, 0, 0)
		pose["sh_l"] = Vector3(0.5, 0, -0.6)
		pose["sh_r"] = Vector3(0.5, 0, 0.6)
		pose["el_l"] = Vector3(0.6, 0, 0)
		pose["el_r"] = Vector3(0.6, 0, 0)
	elif speed > 0.3:
		var run := clampf((speed - 3.0) / 4.0, 0.0, 1.0)
		var dirsign := -1.0 if move_dir.y < -0.2 else 1.0
		phase += delta * speed * (1.55 - run * 0.25) * dirsign * (1.0 / max(0.6, P.hip_h))
		var s := sin(phase)
		var c := cos(phase)
		var a := lerpf(0.45, 0.85, run)
		var kb := lerpf(0.6, 1.4, run)
		var strafe := absf(move_dir.x) > 0.5 and absf(move_dir.y) < 0.3
		if strafe:
			a *= 0.5
		pose["th_l"] = Vector3(s * a, 0, -0.03)
		pose["th_r"] = Vector3(-s * a, 0, 0.03)
		pose["kn_l"] = Vector3(-kb * max(0.0, c * dirsign) - 0.08, 0, 0)
		pose["kn_r"] = Vector3(-kb * max(0.0, -c * dirsign) - 0.08, 0, 0)
		pose["ft_l"] = Vector3(-s * 0.2, 0, 0)
		pose["ft_r"] = Vector3(s * 0.2, 0, 0)
		var arm := lerpf(0.4, 0.85, run)
		pose["sh_l"] = Vector3(-s * arm + run * 0.2, 0, -0.14)
		pose["sh_r"] = Vector3(s * arm + run * 0.2, 0, 0.14)
		pose["el_l"] = Vector3(0.35 + run * 0.9, 0, 0)
		pose["el_r"] = Vector3(0.35 + run * 0.9, 0, 0)
		pose["hips_y"] = -absf(c) * 0.04 * (0.5 + run) + 0.02
		pose["spine"].x += run * 0.18 * dirsign
		pose["spine"].y = s * 0.08
		pose["chest"].y = -s * 0.1
		if strafe:
			pose["body_rot"] = Vector3(0, -sign(move_dir.x) * 0.35, 0)
	else:
		_idle_variant(pose)
	# Kampfhaltung / Waffen
	if combat and not casting and not channeling and speed < 0.3:
		pose["th_l"] = Vector3(0.25, 0, -0.08)
		pose["th_r"] = Vector3(-0.2, 0, 0.08)
		pose["kn_l"] = Vector3(-0.35, 0, 0)
		pose["kn_r"] = Vector3(-0.25, 0, 0)
		pose["hips_y"] = -0.05
	if (combat or weapon_style != "unarmed") and not casting:
		_weapon_hold(pose)
	if casting or channeling:
		var w := sin(_t * 5.0) * 0.05
		pose["sh_l"] = Vector3(0.9 + w, 0.0, -0.35)
		pose["sh_r"] = Vector3(0.9 - w, 0.0, 0.35)
		pose["el_l"] = Vector3(0.7, 0, 0)
		pose["el_r"] = Vector3(0.7, 0, 0)
		if channeling:
			pose["sh_l"] = Vector3(1.3, 0.0, -0.15)
			pose["sh_r"] = Vector3(1.3, 0.0, 0.15)
			pose["el_l"] = Vector3(0.15, 0, 0)
			pose["el_r"] = Vector3(0.15, 0, 0)
	_set_cast_glow(casting or channeling)
	# Einmalige Aktionen
	if _attack_t >= 0.0:
		_attack_t += delta
		var t := _attack_t / _attack_dur
		if t >= 1.0:
			_attack_t = -1.0
		else:
			_attack_pose(pose, t)
	if _release_t >= 0.0:
		_release_t += delta
		var t := _release_t / 0.35
		if t >= 1.0:
			_release_t = -1.0
		else:
			var e := sin(t * PI)
			pose["sh_r"] = Vector3(1.4 * e + 0.2, 0, 0.1)
			pose["el_r"] = Vector3(0.1, 0, 0)
			pose["sh_l"] = Vector3(1.2 * e + 0.1, 0, -0.1)
			pose["spine"].x += 0.15 * e
	if _hit_t >= 0.0:
		_hit_t += delta
		var t := _hit_t / 0.25
		if t >= 1.0:
			_hit_t = -1.0
		else:
			pose["spine"].x -= sin(t * PI) * 0.2
			pose["neck"].x -= sin(t * PI) * 0.2
	_apply_pose(pose, k)


func _idle_variant(pose: Dictionary) -> void:
	var anim := idle_anim
	if emote != "":
		anim = emote
	var t := _t
	match anim:
		"dance":
			var s := sin(t * 6.0)
			pose["hips_y"] = absf(sin(t * 6.0)) * 0.05
			pose["spine"].z = s * 0.15
			pose["sh_l"] = Vector3(0.3, 0, -1.8 - s * 0.5)
			pose["sh_r"] = Vector3(0.3, 0, 1.8 - s * 0.5)
			pose["el_l"] = Vector3(0.9, 0, 0)
			pose["el_r"] = Vector3(0.9, 0, 0)
			pose["th_l"] = Vector3(max(0.0, s) * 0.5, 0, -0.1)
			pose["th_r"] = Vector3(max(0.0, -s) * 0.5, 0, 0.1)
			pose["kn_l"] = Vector3(-max(0.0, s) * 0.8, 0, 0)
			pose["kn_r"] = Vector3(-max(0.0, -s) * 0.8, 0, 0)
		"wave":
			pose["sh_r"] = Vector3(0.2, 0, 2.6)
			pose["el_r"] = Vector3(0.3 + sin(t * 9.0) * 0.4, 0, 0)
		"bow":
			pose["spine"].x = 0.7
			pose["neck"].x = 0.2
			pose["sh_r"] = Vector3(0.8, 0, 0.1)
			pose["el_r"] = Vector3(1.6, 0, 0)
		"cheer":
			pose["sh_l"] = Vector3(0.0, 0, -2.8)
			pose["sh_r"] = Vector3(0.0, 0, 2.8)
			pose["hips_y"] = absf(sin(t * 7.0)) * 0.08
		"laugh":
			pose["spine"].x = -0.15 + sin(t * 14.0) * 0.06
			pose["neck"].x = -0.3
			pose["sh_l"] = Vector3(0.6, 0, -0.3)
			pose["el_l"] = Vector3(1.4, 0, 0)
			pose["sh_r"] = Vector3(0.6, 0, 0.3)
			pose["el_r"] = Vector3(1.4, 0, 0)
		"cry":
			pose["spine"].x = 0.25
			pose["neck"].x = 0.4
			pose["sh_l"] = Vector3(1.8, 0, -0.1)
			pose["sh_r"] = Vector3(1.8, 0, 0.1)
			pose["el_l"] = Vector3(2.3, 0, 0)
			pose["el_r"] = Vector3(2.3, 0, 0)
		"point":
			pose["sh_r"] = Vector3(1.55, 0, 0.05)
			pose["el_r"] = Vector3(0.05, 0, 0)
		"salute":
			pose["sh_r"] = Vector3(1.0, 0, 1.3)
			pose["el_r"] = Vector3(2.2, 0, 0)
		"throne", "sit":
			pose["hips_y"] = -P.hip_h + 0.5
			pose["th_l"] = Vector3(1.45, 0, -0.12)
			pose["th_r"] = Vector3(1.45, 0, 0.12)
			pose["kn_l"] = Vector3(-1.45, 0, 0)
			pose["kn_r"] = Vector3(-1.45, 0, 0)
			pose["sh_l"] = Vector3(0.45, 0, -0.25)
			pose["sh_r"] = Vector3(0.45, 0, 0.25)
			pose["el_l"] = Vector3(0.8, 0, 0)
			pose["el_r"] = Vector3(0.8, 0, 0)
		"goofy":
			pose["spine"].z = sin(t * 1.3) * 0.12
			pose["neck"].z = sin(t * 1.7 + 1.0) * 0.25
			pose["neck"].y = sin(t * 0.9) * 0.4
			pose["sh_l"] = Vector3(sin(t * 2.0) * 0.3, 0, -0.5 - sin(t * 2.3) * 0.3)
			pose["sh_r"] = Vector3(-sin(t * 2.1) * 0.3, 0, 0.5 + sin(t * 1.9) * 0.3)
		"juggle":
			var a := sin(t * 8.0)
			pose["sh_l"] = Vector3(1.0 + a * 0.35, 0, -0.25)
			pose["sh_r"] = Vector3(1.0 - a * 0.35, 0, 0.25)
			pose["el_l"] = Vector3(1.0, 0, 0)
			pose["el_r"] = Vector3(1.0, 0, 0)
			pose["neck"].x = -0.35
		"shifty":
			pose["neck"].y = sin(t * 1.2) * 0.7
			pose["spine"].x = 0.2
			pose["sh_l"] = Vector3(0.5, 0, -0.2)
			pose["el_l"] = Vector3(1.5, 0, 0)
			pose["sh_r"] = Vector3(0.5, 0, 0.2)
			pose["el_r"] = Vector3(1.5, 0, 0)
		"lute":
			pose["sh_l"] = Vector3(0.9, 0.2, -0.1)
			pose["el_l"] = Vector3(1.5, 0, 0)
			pose["sh_r"] = Vector3(0.6, 0, 0.3)
			pose["el_r"] = Vector3(1.1 + sin(t * 10.0) * 0.12, 0, 0)
			pose["neck"].z = sin(t * 2.0) * 0.1
		"anvil":
			var h := absf(sin(t * 3.0))
			pose["sh_r"] = Vector3(0.6 + h * 1.6, 0, 0.2)
			pose["el_r"] = Vector3(0.6 + h * 0.6, 0, 0)
			pose["spine"].x = 0.2
			pose["sh_l"] = Vector3(0.8, 0, -0.1)
			pose["el_l"] = Vector3(0.6, 0, 0)
		"guard":
			pose["sh_r"] = Vector3(0.2, 0, 0.2)
			pose["el_r"] = Vector3(1.4, 0, 0)
		"hunched":
			pose["spine"].x = 0.4
			pose["neck"].x = -0.4
		_:
			var w := sin(t * 0.7) * 0.03
			pose["hips_y"] = w * 0.3
			pose["spine"].z = w


func _weapon_hold(pose: Dictionary) -> void:
	if speed > 0.3 and not combat:
		return
	match weapon_style:
		"1h", "shield":
			pose["sh_r"] = Vector3(0.45, 0, 0.2)
			pose["el_r"] = Vector3(1.0, 0, 0)
			if weapon_style == "shield":
				pose["sh_l"] = Vector3(0.6, 0.0, -0.35)
				pose["el_l"] = Vector3(1.3, 0, 0)
		"2h":
			pose["sh_r"] = Vector3(0.7, 0, 0.0)
			pose["el_r"] = Vector3(1.1, 0, 0)
			pose["sh_l"] = Vector3(0.9, 0, 0.35)
			pose["el_l"] = Vector3(1.2, 0, 0)
		"katana":
			pose["sh_r"] = Vector3(0.8, 0, -0.05)
			pose["el_r"] = Vector3(1.0, 0, 0)
			pose["sh_l"] = Vector3(0.85, 0, 0.3)
			pose["el_l"] = Vector3(1.1, 0, 0)
		"dual":
			pose["sh_r"] = Vector3(0.5, 0, 0.25)
			pose["el_r"] = Vector3(1.2, 0, 0)
			pose["sh_l"] = Vector3(0.5, 0, -0.25)
			pose["el_l"] = Vector3(1.2, 0, 0)
		"bow":
			pose["sh_l"] = Vector3(0.5, 0, -0.15)
			pose["el_l"] = Vector3(0.4, 0, 0)
		"staff":
			pose["sh_r"] = Vector3(0.35, 0, 0.18)
			pose["el_r"] = Vector3(0.9, 0, 0)


func _attack_pose(pose: Dictionary, t: float) -> void:
	var wind := clampf(t / 0.4, 0.0, 1.0)
	var strike := clampf((t - 0.4) / 0.25, 0.0, 1.0)
	var back := clampf((t - 0.65) / 0.35, 0.0, 1.0)
	var e_w := wind * wind * (3.0 - 2.0 * wind)
	var e_s := 1.0 - pow(1.0 - strike, 3.0)
	var e_b := back * back * (3.0 - 2.0 * back)
	match _attack_kind:
		"2h":
			var up := lerpf(0.0, 2.9, e_w)
			var down := lerpf(up, 0.6, e_s)
			var v := lerpf(down, 0.7, e_b)
			pose["sh_r"] = Vector3(v, 0, 0.05)
			pose["sh_l"] = Vector3(v + 0.15, 0, 0.3)
			pose["el_r"] = Vector3(lerpf(0.6, 0.2, e_s), 0, 0)
			pose["el_l"] = Vector3(lerpf(0.8, 0.4, e_s), 0, 0)
			pose["spine"].x += lerpf(-0.2 * e_w, 0.35, e_s) * (1.0 - e_b)
		"dual":
			var tt := fmod(t * 2.0, 1.0)
			var e := sin(tt * PI)
			if t < 0.5:
				pose["sh_r"] = Vector3(0.5 + e * 1.0, 0, 0.1)
				pose["el_r"] = Vector3(1.2 - e * 1.1, 0, 0)
			else:
				pose["sh_l"] = Vector3(0.5 + e * 1.0, 0, -0.1)
				pose["el_l"] = Vector3(1.2 - e * 1.1, 0, 0)
			pose["chest"].y = (0.3 if t < 0.5 else -0.3) * e
		"bow":
			var draw := clampf(t / 0.6, 0.0, 1.0)
			pose["sh_l"] = Vector3(1.55, 0, -0.05)
			pose["el_l"] = Vector3(0.05, 0, 0)
			pose["sh_r"] = Vector3(1.45, 0, 0.3)
			pose["el_r"] = Vector3(lerpf(0.4, 2.3, draw) if t < 0.75 else 0.3, 0, 0)
			pose["chest"].y = -0.4
		"unarmed":
			var e := sin(t * PI)
			pose["sh_r"] = Vector3(0.4 + e * 1.1, 0, 0.1)
			pose["el_r"] = Vector3(1.6 - e * 1.4, 0, 0)
			pose["chest"].y = -0.4 * e
		"staff", "cast":
			var e := sin(t * PI)
			pose["sh_r"] = Vector3(0.6 + e * 1.2, 0, 0.2)
			pose["el_r"] = Vector3(0.6 - e * 0.4, 0, 0)
			pose["spine"].x += 0.1 * e
		_:
			# Einhändig: von rechts oben diagonal nach links unten
			var up := lerpf(0.4, 2.5, e_w)
			var sx := lerpf(0.2, 0.9, e_w)
			var v := lerpf(up, 0.5, e_s)
			var z := lerpf(sx, -0.45, e_s)
			v = lerpf(v, 0.45, e_b)
			z = lerpf(z, 0.2, e_b)
			pose["sh_r"] = Vector3(v, 0, z)
			pose["el_r"] = Vector3(lerpf(1.2, 0.3, e_s), 0, 0)
			pose["chest"].y = lerpf(0.35 * e_w, -0.45, e_s) * (1.0 - e_b)
			pose["spine"].x += 0.12 * e_s * (1.0 - e_b)


func _apply_pose(pose: Dictionary, k: float) -> void:
	hips.position.y = lerpf(hips.position.y, P.hip_h + pose["hips_y"], k)
	body.rotation = body.rotation.lerp(pose["body_rot"], k * 0.8)
	body.position.y = lerpf(body.position.y, pose["body_y"], k)
	_lerp_rot(spine, pose["spine"], k)
	_lerp_rot(chest, pose["chest"], k)
	_lerp_rot(neck, pose["neck"], k)
	_lerp_rot(sh_l, pose["sh_l"], k)
	_lerp_rot(sh_r, pose["sh_r"], k)
	_lerp_rot(el_l, pose["el_l"], k)
	_lerp_rot(el_r, pose["el_r"], k)
	_lerp_rot(th_l, pose["th_l"], k)
	_lerp_rot(th_r, pose["th_r"], k)
	_lerp_rot(kn_l, pose["kn_l"], k)
	_lerp_rot(kn_r, pose["kn_r"], k)
	_lerp_rot(ft_l, pose["ft_l"], k)
	_lerp_rot(ft_r, pose["ft_r"], k)
	if tail:
		tail.rotation.y = sin(_t * 2.0) * 0.4
	if _cape:
		var target := 0.05 + clampf(speed / 7.0, 0.0, 1.0) * 0.6
		back_attach.rotation.x = lerpf(back_attach.rotation.x, target if not airborne else 0.9, k * 0.5)


func _set_cast_glow(on: bool) -> void:
	if _cast_glow_l == null:
		return
	_cast_glow_l.visible = on
	_cast_glow_r.visible = on
	if on:
		var a := 0.4 + 0.2 * sin(_t * 9.0)
		var c := Color(cast_color.r, cast_color.g, cast_color.b, a)
		(_cast_glow_l.mesh.material as StandardMaterial3D).albedo_color = c
		(_cast_glow_r.mesh.material as StandardMaterial3D).albedo_color = c


## Höhe für Namensschild und Zielmarkierung
func top_height() -> float:
	return (P.hip_h + P.spine + P.chest_h + P.neck + P.head_r * 2.2) * scale.y
