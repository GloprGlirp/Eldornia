class_name PropFactory
extends RefCounted
## Gebäude und Requisiten im Stil klassischer Fantasy-MMOs: Fachwerk, wuchtige Steinmauern,
## blaue Spitzdächer, warm leuchtende Fenster. Vorderseite (Tür) zeigt lokal nach -Z,
## die Drehung r des Servers wird direkt als rotation.y verwendet.

static var M := {}


static func mats() -> Dictionary:
	if M.is_empty():
		M = {
			"wood": Mat.stylized(Color.html("#86603c"), Mat.P.WOOD, {"c2": Color.html("#4e331d")}),
			"wood_dark": Mat.stylized(Color.html("#4f3220"), Mat.P.WOOD, {"c2": Color.html("#2c1a0e")}),
			"wood_light": Mat.stylized(Color.html("#b08a5a"), Mat.P.WOOD, {"c2": Color.html("#6a4c2c")}),
			"beam": Mat.stylized(Color.html("#4a2d1a"), Mat.P.WOOD, {"c2": Color.html("#26160c"), "scale": 2.0}),
			"plaster": Mat.stylized(Color.html("#ecdfc2"), Mat.P.PLASTER, {"c2": Color.html("#b4a07a")}),
			"stone": Mat.stylized(Color.html("#a39d92"), Mat.P.STONE, {"c2": Color.html("#5a554e")}),
			"stone_dark": Mat.stylized(Color.html("#77726b"), Mat.P.STONE, {"c2": Color.html("#3a3631")}),
			"stone_castle": Mat.stylized(Color.html("#b5aea2"), Mat.P.STONE, {"c2": Color.html("#625c54"), "scale": 0.7}),
			"flag": Mat.stylized(Color.html("#9a948a"), Mat.P.FLAGSTONE, {"c2": Color.html("#4c4741"), "tri": true}),
			"roof_blue": Mat.stylized(Color.html("#3f62a8"), Mat.P.ROOF, {"c2": Color.html("#1e2c4e")}),
			"roof_red": Mat.stylized(Color.html("#a8462c"), Mat.P.ROOF, {"c2": Color.html("#4e1c10")}),
			"roof_slate": Mat.stylized(Color.html("#5a6070"), Mat.P.ROOF, {"c2": Color.html("#262a34")}),
			"roof_green": Mat.stylized(Color.html("#4a7a5a"), Mat.P.ROOF, {"c2": Color.html("#1e3626")}),
			"thatch": Mat.stylized(Color.html("#d0ae62"), Mat.P.THATCH, {"c2": Color.html("#7a5a28")}),
			"iron": Mat.stylized(Color.html("#4a4a52"), Mat.P.METAL, {"c2": Color.html("#1e1e22"), "wear": 0.6}),
			"gold": Mat.stylized(Color.html("#e0b648"), Mat.P.GOLD, {"c2": Color.html("#7a5a18"), "wear": 0.8}),
			"glass": Mat.stylized(Color.html("#2a2f3a"), Mat.P.PLAIN, {"emis": Color.html("#ffb860"), "emis_e": 0.9, "rough": 0.2}),
			"glass_color": Mat.stylized(Color.html("#4a3a8a"), Mat.P.PLAIN, {"emis": Color.html("#a070ff"), "emis_e": 1.2}),
			"dark": Mat.stylized(Color.html("#0e0c0c"), Mat.P.PLAIN, {"rough": 1.0, "rim": 0.0}),
			"cloth_red": Mat.stylized(Color.html("#8f1d2c"), Mat.P.CLOTH, {"wind": 1.0}),
			"cloth_blue": Mat.stylized(Color.html("#2d4f9a"), Mat.P.CLOTH, {"wind": 1.0}),
			"straw": Mat.stylized(Color.html("#e0c070"), Mat.P.THATCH, {"c2": Color.html("#9a7a30"), "scale": 2.0}),
			"bone": Mat.stylized(Color.html("#e6dcc0"), Mat.P.BONE, {"c2": Color.html("#8a7a5a")}),
			"water": Mat.water(Color.html("#3aa6b0"), Color.html("#0e3f5e")),
			"rope": Mat.stylized(Color.html("#b09060"), Mat.P.PLAIN),
			"hedge": Mat.foliage(Color.html("#4a8a2a"), Color.html("#1a3a10"), Color.html("#8ab040")),
			"rose": Mat.stylized(Color.html("#d02040"), Mat.P.PLAIN, {"emis": Color.html("#400008")}),
			"ore": Mat.stylized(Color.html("#d07a3a"), Mat.P.METAL, {"emis": Color.html("#3a1a08")}),
			"candle": Mat.stylized(Color.html("#f0e6c8"), Mat.P.PLAIN),
			"red_cushion": Mat.stylized(Color.html("#a01828"), Mat.P.CLOTH),
			"grave": Mat.stylized(Color.html("#8a8a88"), Mat.P.STONE, {"c2": Color.html("#4a4a48"), "scale": 1.6}),
			"soil": Mat.stylized(Color.html("#4a3424"), Mat.P.PLAIN),
			"marble": Mat.stylized(Color.html("#e8e4dc"), Mat.P.FLAGSTONE, {"c2": Color.html("#a8a49c"), "tri": true}),
		}
	return M


static func m(key: String) -> Material:
	return mats()[key]


static var _mesh_cache: Dictionary = {}


## Baut alle Requisiten einer Zone.
static func populate(parent: Node3D, props: Array, hf: Heightfield, theme_id: String) -> void:
	hf_ref = hf
	for p in props:
		var t: String = p.get("t", "")
		if Vegetation.BUILDERS.has(t):
			continue
		var node := create(p, theme_id)
		if node == null:
			continue
		if p.has("x1"):
			# Segment-Requisiten bringen ihre Lage selbst mit
			parent.add_child(node)
			continue
		var x := float(p.get("x", 0.0))
		var z := float(p.get("z", 0.0))
		var y := hf.height(x, z) if hf else 0.0
		if p.has("y"):
			y = float(p["y"])
		node.position = Vector3(x, y, z)
		node.rotation.y = float(p.get("r", 0.0))
		parent.add_child(node)


static func _mi(mesh: Mesh, shadows := true) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi


static func _cached(key: String, fn: Callable) -> ArrayMesh:
	if _mesh_cache.has(key):
		return _mesh_cache[key]
	var mesh: ArrayMesh = fn.call()
	_mesh_cache[key] = mesh
	return mesh


static func create(p: Dictionary, theme_id: String) -> Node3D:
	var t: String = p.get("t", "")
	match t:
		"house": return house(p)
		"inn": return inn(p)
		"kitchen": return house(p.merged({"v": 3, "floors": 1}))
		"smithy": return smithy(p)
		"chapel": return chapel(p)
		"keep": return keep(p)
		"tower": return tower(p)
		"wall": return wall(p)
		"gatearch": return gatearch(p)
		"gate": return village_gate(p)
		"fountain": return fountain(p)
		"well": return well(p)
		"windmill": return windmill(p)
		"barn": return barn(p)
		"field": return field(p)
		"fence": return fence(p, false)
		"ironfence": return fence(p, true)
		"palisade": return palisade(p)
		"haystack": return haystack(p)
		"tent": return tent(p)
		"bigtent": return bigtent(p)
		"campfire": return campfire(p)
		"watchtower": return watchtower(p)
		"mine": return mine(p)
		"rails": return rails(p)
		"minecart": return minecart(p)
		"lantern": return lantern(p)
		"graves": return graves(p)
		"mausoleum": return mausoleum(p)
		"pier": return pier(p)
		"hut": return hut(p)
		"cauldron": return cauldron(p)
		"stall": return stall(p)
		"wagon", "cart": return cart(p)
		"sign": return signpost(p)
		"bench": return bench(p)
		"barrel": return barrel(p)
		"crate": return crate(p)
		"banner": return banner(p)
		"weaponrack": return weaponrack(p)
		"anvil": return anvil(p)
		"throne": return throne(p)
		"rosegarden": return rosegarden(p)
		"brazier": return brazier(p)
		"shed": return shed(p)
		"scarecrow": return scarecrow(p)
		"orepile": return orepile(p)
		"stairs": return stairs(p)
		"pillar": return pillar(p)
		"sarcophagus": return sarcophagus(p)
		"bones": return bones(p, false)
		"bonepile": return bones(p, true)
		"altar": return altar(p)
		"candles": return candles(p)
	return null


# =============================================================================== Fachwerkhaus
static func _timber_walls(mb: MeshBuilder, w: float, d: float, y0: float, h: float, door_side := true, rng: RandomNumberGenerator = null) -> void:
	var plaster := m("plaster")
	var beam := m("beam")
	mb.box(plaster, MeshBuilder.at(Vector3(0, y0 + h * 0.5, 0)), Vector3(w, h, d))
	var bt := Vector2(0.2, 0.2)
	var hw := w * 0.5 + 0.04
	var hd := d * 0.5 + 0.04
	# Eckpfosten
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			mb.beam(beam, Vector3(sx * hw, y0, sz * hd), Vector3(sx * hw, y0 + h, sz * hd), bt)
	# Schwellen und Rähme
	for yy in [y0 + 0.1, y0 + h - 0.1]:
		mb.beam(beam, Vector3(-hw, yy, -hd), Vector3(hw, yy, -hd), bt, Vector3.BACK)
		mb.beam(beam, Vector3(-hw, yy, hd), Vector3(hw, yy, hd), bt, Vector3.BACK)
		mb.beam(beam, Vector3(-hw, yy, -hd), Vector3(-hw, yy, hd), bt, Vector3.RIGHT)
		mb.beam(beam, Vector3(hw, yy, -hd), Vector3(hw, yy, hd), bt, Vector3.RIGHT)
	# Ständer und Streben
	var nx := int(max(1, round(w / 1.7)))
	for i in range(1, nx):
		var x := -hw + w * i / nx
		for sz in [-1.0, 1.0]:
			if door_side and sz < 0 and abs(x) < 0.9:
				continue
			mb.beam(beam, Vector3(x, y0, sz * hd), Vector3(x, y0 + h, sz * hd), Vector2(0.16, 0.16))
	var nz := int(max(1, round(d / 1.7)))
	for i in range(1, nz):
		var z := -hd + d * i / nz
		for sx in [-1.0, 1.0]:
			mb.beam(beam, Vector3(sx * hw, y0, z), Vector3(sx * hw, y0 + h, z), Vector2(0.16, 0.16))
	# Diagonalstreben an den Ecken
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			var x0 = sx * hw
			var x1 = sx * (hw - min(1.2, w * 0.25))
			mb.beam(beam, Vector3(x0, y0 + 0.2, sz * hd), Vector3(x1, y0 + h - 0.2, sz * hd), Vector2(0.14, 0.14))
			var z1 = sz * (hd - min(1.2, d * 0.25))
			mb.beam(beam, Vector3(sx * hw, y0 + 0.2, sz * hd), Vector3(sx * hw, y0 + h - 0.2, z1), Vector2(0.14, 0.14))


static func _window(mb: MeshBuilder, pos: Vector3, normal: Vector3, w := 0.9, h := 1.0, shutters := true, shutter_mat: Material = null) -> void:
	var rot := atan2(normal.x, normal.z)
	var basis := Basis(Vector3.UP, rot)
	var xf := Transform3D(basis, pos + normal * 0.06)
	mb.box(m("glass"), xf, Vector3(w, h, 0.05))
	var fr := m("beam")
	mb.box(fr, xf * Transform3D(Basis(), Vector3(0, h * 0.5, 0.04)), Vector3(w + 0.2, 0.12, 0.14))
	mb.box(fr, xf * Transform3D(Basis(), Vector3(0, -h * 0.5, 0.06)), Vector3(w + 0.3, 0.14, 0.24))
	mb.box(fr, xf * Transform3D(Basis(), Vector3(-w * 0.5, 0, 0.04)), Vector3(0.1, h, 0.12))
	mb.box(fr, xf * Transform3D(Basis(), Vector3(w * 0.5, 0, 0.04)), Vector3(0.1, h, 0.12))
	mb.box(fr, xf * Transform3D(Basis(), Vector3(0, 0, 0.04)), Vector3(0.06, h, 0.08))
	mb.box(fr, xf * Transform3D(Basis(), Vector3(0, 0, 0.04)), Vector3(w, 0.06, 0.08))
	if shutters:
		var sm: Material = shutter_mat if shutter_mat else m("wood")
		for sx in [-1.0, 1.0]:
			mb.box(sm, xf * Transform3D(Basis(Vector3.UP, sx * 0.5), Vector3(sx * (w * 0.5 + 0.28), 0, 0.12)), Vector3(0.48, h + 0.05, 0.06))


static func _door(mb: MeshBuilder, pos: Vector3, normal: Vector3, w := 1.2, h := 2.1) -> void:
	var rot := atan2(normal.x, normal.z)
	var xf := Transform3D(Basis(Vector3.UP, rot), pos + normal * 0.05)
	mb.box(m("wood_dark"), xf * Transform3D(Basis(), Vector3(0, h * 0.5, 0)), Vector3(w, h, 0.1))
	mb.box(m("beam"), xf * Transform3D(Basis(), Vector3(0, h + 0.08, 0.04)), Vector3(w + 0.35, 0.18, 0.2))
	mb.box(m("beam"), xf * Transform3D(Basis(), Vector3(-w * 0.5 - 0.08, h * 0.5, 0.04)), Vector3(0.16, h, 0.18))
	mb.box(m("beam"), xf * Transform3D(Basis(), Vector3(w * 0.5 + 0.08, h * 0.5, 0.04)), Vector3(0.16, h, 0.18))
	for yy in [0.4, h - 0.5]:
		mb.box(m("iron"), xf * Transform3D(Basis(), Vector3(0, yy, 0.07)), Vector3(w * 0.9, 0.08, 0.03))
	mb.ellipsoid(m("iron"), xf * Transform3D(Basis(), Vector3(w * 0.3, h * 0.48, 0.1)), Vector3(0.05, 0.05, 0.05), 6, 4)


const ROOFS := ["roof_blue", "roof_red", "thatch", "roof_slate", "roof_slate", "thatch"]
const SHUTTERS := ["#3a5a8a", "#2f6a3a", "#8a3a2a", "#6a4a2a", "#4a4a5a", "#3a6a6a"]


static func house(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 8.0))
	var d := float(p.get("d", 7.0))
	var v := int(p.get("v", 0))
	var floors := int(p.get("floors", 2 if w >= 7.5 else 1))
	var key := "house|%s|%s|%d|%d" % [w, d, v, floors]
	var mesh := _cached(key, func(): return _house_mesh(w, d, v, floors))
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var light := FxLib.light(Color.html("#ffb060"), 0.8, 6.0)
	light.position = Vector3(0, 1.6, -d * 0.5 - 0.8)
	root.add_child(light)
	return root


static func _house_mesh(w: float, d: float, v: int, floors: int) -> ArrayMesh:
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = int(w * 100 + d * 10 + v)
	var shutter := Mat.stylized(Color.html(SHUTTERS[v % SHUTTERS.size()]), Mat.P.WOOD)
	var stone := m("stone")
	# Sockel
	mb.box(stone, MeshBuilder.at(Vector3(0, 0.15, 0)), Vector3(w + 0.4, 0.9, d + 0.4))
	var y := 0.6
	var h1 := 2.9
	_timber_walls(mb, w, d, y, h1, true, rng)
	_door(mb, Vector3(0, y, -d * 0.5), Vector3(0, 0, -1))
	# Türvordach
	mb.gable_roof(m(ROOFS[v % ROOFS.size()]), MeshBuilder.at(Vector3(0, y + 2.45, -d * 0.5 - 0.55)), 1.8, 1.0, 0.55, 0.15, 0.08)
	for sx in [-1.0, 1.0]:
		mb.beam(m("beam"), Vector3(sx * 0.95, y + 2.45, -d * 0.5 - 1.0), Vector3(sx * 0.95, y + 1.9, -d * 0.5 - 0.05), Vector2(0.1, 0.1))
	# Fenster Erdgeschoss
	for sx in [-1.0, 1.0]:
		if w > 5.5:
			_window(mb, Vector3(sx * w * 0.3, y + 1.5, -d * 0.5), Vector3(0, 0, -1), 0.9, 1.0, true, shutter)
		_window(mb, Vector3(sx * w * 0.5, y + 1.5, 0), Vector3(sx, 0, 0), 0.9, 1.0, true, shutter)
	_window(mb, Vector3(0, y + 1.5, d * 0.5), Vector3(0, 0, 1), 0.9, 1.0, true, shutter)
	y += h1
	var top_w := w
	var top_d := d
	if floors >= 2:
		var h2 := 2.3
		top_w = w + 0.6
		top_d = d + 0.6
		# Auskragung mit Balkenköpfen
		for i in int(top_w / 0.9) + 1:
			var x := -top_w * 0.5 + i * 0.9
			mb.box(m("beam"), MeshBuilder.at(Vector3(x, y - 0.05, -d * 0.5 - 0.2)), Vector3(0.16, 0.18, 0.5))
			mb.box(m("beam"), MeshBuilder.at(Vector3(x, y - 0.05, d * 0.5 + 0.2)), Vector3(0.16, 0.18, 0.5))
		_timber_walls(mb, top_w, top_d, y, h2, false, rng)
		for sx in [-1.0, 1.0]:
			_window(mb, Vector3(sx * top_w * 0.28, y + 1.2, -top_d * 0.5), Vector3(0, 0, -1), 0.8, 0.9, true, shutter)
			_window(mb, Vector3(sx * top_w * 0.28, y + 1.2, top_d * 0.5), Vector3(0, 0, 1), 0.8, 0.9, true, shutter)
		y += h2
	# Dach (First entlang X)
	var roof_mat := m(ROOFS[v % ROOFS.size()])
	var rh := top_d * 0.72
	mb.gable_roof(roof_mat, MeshBuilder.at(Vector3(0, y, 0)), top_w, top_d, rh, 0.55, 0.22, m("plaster"))
	# Giebelbalken
	for sx in [-1.0, 1.0]:
		var gx = sx * (top_w * 0.5 + 0.03)
		mb.beam(m("beam"), Vector3(gx, y, -top_d * 0.5), Vector3(gx, y + rh, 0), Vector2(0.16, 0.16))
		mb.beam(m("beam"), Vector3(gx, y, top_d * 0.5), Vector3(gx, y + rh, 0), Vector2(0.16, 0.16))
		mb.beam(m("beam"), Vector3(gx, y, 0), Vector3(gx, y + rh, 0), Vector2(0.14, 0.14))
		_window(mb, Vector3(sx * (top_w * 0.5), y + rh * 0.35, 0), Vector3(sx, 0, 0), 0.6, 0.7, false)
	# Firstbalken
	mb.box(m("beam"), MeshBuilder.at(Vector3(0, y + rh + 0.42, 0)), Vector3(top_w + 1.2, 0.2, 0.25))
	# Schornstein
	var cx := top_w * 0.28 * (1.0 if v % 2 == 0 else -1.0)
	mb.box(m("stone_dark"), MeshBuilder.at(Vector3(cx, y + rh * 0.6, top_d * 0.18)), Vector3(0.9, rh * 1.3, 0.9))
	mb.box(m("stone_dark"), MeshBuilder.at(Vector3(cx, y + rh * 1.25 + 0.1, top_d * 0.18)), Vector3(1.1, 0.25, 1.1))
	# Blumenkästen
	var flower := Mat.stylized(Color.html(["#e04060", "#f0d040", "#c060e0", "#ff8040"][v % 4]), Mat.P.PLAIN, {"rim": 0.3})
	for sx in [-1.0, 1.0]:
		if w > 5.5:
			mb.box(m("wood"), MeshBuilder.at(Vector3(sx * w * 0.3, 0.6 + 0.85, -d * 0.5 - 0.25)), Vector3(1.0, 0.22, 0.25))
			for k in 4:
				mb.ellipsoid(flower, MeshBuilder.at(Vector3(sx * w * 0.3 - 0.36 + k * 0.24, 0.6 + 1.02, -d * 0.5 - 0.25)), Vector3(0.12, 0.1, 0.12), 6, 4)
	return mb.commit()


static func inn(p: Dictionary) -> Node3D:
	var root := house(p.merged({"floors": 2, "v": int(p.get("v", 1))}))
	var d := float(p.get("d", 10.0))
	var mb := MeshBuilder.new()
	# Wirtshausschild mit Krug
	mb.beam(m("beam"), Vector3(-1.6, 3.4, -d * 0.5 - 0.1), Vector3(-1.6, 3.4, -d * 0.5 - 1.6), Vector2(0.12, 0.12))
	mb.box(m("wood_light"), MeshBuilder.at(Vector3(-1.6, 2.85, -d * 0.5 - 1.3)), Vector3(0.08, 0.9, 1.1))
	mb.cylinder(m("gold"), MeshBuilder.at_euler(Vector3(-1.66, 2.6, -d * 0.5 - 1.3), Vector3(0, 0, 0)), 0.18, 0.2, 0.42, 10)
	mb.box(m("rope"), MeshBuilder.at(Vector3(-1.6, 3.32, -d * 0.5 - 1.0)), Vector3(0.03, 0.12, 0.03))
	mb.box(m("rope"), MeshBuilder.at(Vector3(-1.6, 3.32, -d * 0.5 - 1.6)), Vector3(0.03, 0.12, 0.03))
	# Fässer neben dem Eingang
	for i in 3:
		mb.cylinder(m("wood"), MeshBuilder.at(Vector3(2.2 + i * 0.7, 0.6, -d * 0.5 - 0.9)), 0.33, 0.33, 0.9, 10)
		mb.torus(m("iron"), MeshBuilder.at(Vector3(2.2 + i * 0.7, 0.85, -d * 0.5 - 0.9)), 0.34, 0.03, 12, 4)
	root.add_child(_mi(mb.commit()))
	if p.has("name"):
		var l := _label(str(p["name"]), 0.3)
		l.position = Vector3(-1.6, 2.85, -d * 0.5 - 1.36)
		l.rotation.y = PI * 0.5
		root.add_child(l)
	return root


static func _label(text: String, size := 0.4, color := Color.html("#f4e6c0")) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.font = load("res://assets/fonts/Cinzel-Bold.woff2")
	l.font_size = 64
	l.pixel_size = size / 64.0 * 1.4
	l.modulate = color
	l.outline_size = 10
	l.outline_modulate = Color(0.1, 0.06, 0.03, 1)
	l.double_sided = true
	return l


static func smithy(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 8.0))
	var d := float(p.get("d", 8.0))
	var mesh := _cached("smithy|%s|%s" % [w, d], func():
		var mb := MeshBuilder.new()
		mb.box(m("flag"), MeshBuilder.at(Vector3(0, 0.1, 0)), Vector3(w + 0.4, 0.3, d + 0.4))
		# Rückwand aus Stein, Seitenwände halbhoch
		mb.box(m("stone"), MeshBuilder.at(Vector3(0, 1.8, d * 0.5 - 0.3)), Vector3(w, 3.4, 0.6))
		for sx in [-1.0, 1.0]:
			mb.box(m("stone"), MeshBuilder.at(Vector3(sx * (w * 0.5 - 0.3), 0.8, d * 0.25)), Vector3(0.6, 1.4, d * 0.5))
			mb.beam(m("beam"), Vector3(sx * (w * 0.5 - 0.3), 0.2, -d * 0.5 + 0.3), Vector3(sx * (w * 0.5 - 0.3), 3.6, -d * 0.5 + 0.3), Vector2(0.3, 0.3))
		mb.gable_roof(m("roof_red"), MeshBuilder.at(Vector3(0, 3.6, 0)), w, d, d * 0.45, 0.5, 0.2, m("wood"))
		# Esse
		mb.box(m("stone_dark"), MeshBuilder.at(Vector3(w * 0.25, 0.7, d * 0.25)), Vector3(2.0, 1.2, 1.8))
		mb.box(m("stone_dark"), MeshBuilder.at(Vector3(w * 0.25, 4.0, d * 0.35)), Vector3(1.2, 5.6, 1.0))
		mb.box(Mat.emissive(Color.html("#ff5a10"), 3.0), MeshBuilder.at(Vector3(w * 0.25, 1.32, d * 0.22)), Vector3(1.5, 0.08, 1.3))
		# Werkbank und Wassertrog
		mb.box(m("wood"), MeshBuilder.at(Vector3(-w * 0.25, 0.85, d * 0.3)), Vector3(2.2, 0.15, 0.9))
		for sx in [-1.0, 1.0]:
			mb.box(m("wood_dark"), MeshBuilder.at(Vector3(-w * 0.25 + sx * 0.9, 0.45, d * 0.3)), Vector3(0.12, 0.8, 0.8))
		mb.box(m("wood_dark"), MeshBuilder.at(Vector3(-w * 0.3, 0.35, -d * 0.1)), Vector3(1.6, 0.6, 0.7))
		mb.box(m("water"), MeshBuilder.at(Vector3(-w * 0.3, 0.62, -d * 0.1)), Vector3(1.45, 0.05, 0.55))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var fire := FxLib.fire(0.7)
	fire.position = Vector3(w * 0.25, 1.35, d * 0.22)
	root.add_child(fire)
	return root


static func chapel(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 8.0))
	var d := float(p.get("d", 13.0))
	var mesh := _cached("chapel|%s|%s" % [w, d], func():
		var mb := MeshBuilder.new()
		var st := m("stone_castle")
		mb.box(st, MeshBuilder.at(Vector3(0, 0.1, 0)), Vector3(w + 0.6, 0.6, d + 0.6))
		mb.box(st, MeshBuilder.at(Vector3(0, 3.0, 0)), Vector3(w, 5.4, d))
		# Strebepfeiler
		for i in 4:
			var z := -d * 0.5 + d * (i + 0.5) / 4.0
			for sx in [-1.0, 1.0]:
				mb.box(st, MeshBuilder.at(Vector3(sx * (w * 0.5 + 0.35), 2.2, z)), Vector3(0.7, 4.4, 0.8))
				_window(mb, Vector3(sx * w * 0.5, 3.4, z + d / 8.0), Vector3(sx, 0, 0), 0.7, 2.0, false)
		mb.gable_roof(m("roof_slate"), Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(0, 5.7, 0)), d, w, w * 0.85, 0.5, 0.25, st)
		# Glockenturm vorne
		var tz := -d * 0.5 - 1.2
		mb.box(st, MeshBuilder.at(Vector3(0, 4.5, tz)), Vector3(3.2, 9.0, 3.2))
		mb.box(m("dark"), MeshBuilder.at(Vector3(0, 7.6, tz)), Vector3(3.3, 1.6, 2.2))
		mb.box(m("dark"), MeshBuilder.at(Vector3(0, 7.6, tz)), Vector3(2.2, 1.6, 3.3))
		mb.cone_roof(m("roof_slate"), MeshBuilder.at(Vector3(0, 9.0, tz), PI * 0.25), 2.6, 4.5, 4)
		mb.cylinder(m("gold"), MeshBuilder.at(Vector3(0, 13.4, tz)), 0.06, 0.06, 1.0, 6)
		mb.box(m("gold"), MeshBuilder.at(Vector3(0, 14.1, tz)), Vector3(0.6, 0.08, 0.08))
		# Portal und Rosettenfenster
		_door(mb, Vector3(0, 0.4, tz - 1.6), Vector3(0, 0, -1), 1.4, 2.5)
		mb.cylinder(m("glass_color"), MeshBuilder.at_euler(Vector3(0, 5.2, tz - 1.62), Vector3(PI * 0.5, 0, 0)), 0.75, 0.75, 0.05, 16)
		mb.torus(st, MeshBuilder.at_euler(Vector3(0, 5.2, tz - 1.64), Vector3(PI * 0.5, 0, 0)), 0.8, 0.12, 16, 6)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var l := FxLib.light(Color.html("#ffd890"), 1.2, 8.0)
	l.position = Vector3(0, 2.5, -d * 0.5 - 4.0)
	root.add_child(l)
	return root


# =============================================================================== Burg
static func _crenellations(mb: MeshBuilder, mat: Material, from: Vector3, to: Vector3, thick: float) -> void:
	var dir := to - from
	var len := dir.length()
	var count := int(len / 1.2)
	for i in count:
		if i % 2 == 0:
			var a := from + dir * (float(i) + 0.5) / count
			var rot := atan2(dir.x, dir.z)
			mb.box(mat, Transform3D(Basis(Vector3.UP, rot), a + Vector3(0, 0.45, 0)), Vector3(thick, 0.9, len / count * 0.95))


static func wall(p: Dictionary) -> Node3D:
	var a := Vector3(float(p["x1"]), 0, float(p["z1"]))
	var b := Vector3(float(p["x2"]), 0, float(p["z2"]))
	var h := float(p.get("h", 7.5))
	var th := float(p.get("th", 2.6))
	var mb := MeshBuilder.new()
	var st := m("stone_castle")
	var dir := b - a
	var rot := atan2(dir.x, dir.z)
	var mid := (a + b) * 0.5
	var y0 := float(p.get("y", _ground(mid.x, mid.z)))
	var ground := y0 - 3.0
	var top := y0 + h
	mb.box(st, Transform3D(Basis(Vector3.UP, rot), mid + Vector3(0, (ground + top) * 0.5, 0)), Vector3(th, top - ground, dir.length()))
	# Sockelvorsprung
	mb.box(m("stone_dark"), Transform3D(Basis(Vector3.UP, rot), mid + Vector3(0, y0 + 0.2, 0)), Vector3(th + 0.6, 1.6, dir.length()))
	var side := Vector3(cos(rot), 0, -sin(rot)) * (th * 0.5 - 0.25)
	_crenellations(mb, st, a + side + Vector3(0, top, 0), b + side + Vector3(0, top, 0), 0.5)
	_crenellations(mb, st, a - side + Vector3(0, top, 0), b - side + Vector3(0, top, 0), 0.5)
	var node := Node3D.new()
	node.add_child(_mi(mb.commit()))
	return node


static func tower(p: Dictionary) -> Node3D:
	var rad := float(p.get("rad", 4.0))
	var h := float(p.get("h", 14.0))
	var mesh := _cached("tower|%s|%s" % [rad, h], func():
		var mb := MeshBuilder.new()
		var st := m("stone_castle")
		mb.cylinder(st, MeshBuilder.at(Vector3(0, -3, 0)), rad * 1.08, rad, h + 3, 18)
		mb.cylinder(m("stone_dark"), MeshBuilder.at(Vector3(0, h - 0.4, 0)), rad * 1.15, rad * 1.18, 0.6, 18)
		for i in 10:
			var a := TAU * i / 10.0
			mb.box(st, MeshBuilder.at(Vector3(cos(a) * rad * 1.1, h + 0.6, sin(a) * rad * 1.1), -a), Vector3(0.5, 1.2, rad * 0.45))
		mb.cylinder(st, MeshBuilder.at(Vector3(0, h, 0)), rad * 0.85, rad * 0.85, 2.2, 14)
		mb.cone_roof(m("roof_blue"), MeshBuilder.at(Vector3(0, h + 2.2, 0)), rad * 1.05, rad * 2.2, 18)
		mb.cylinder(m("gold"), MeshBuilder.at(Vector3(0, h + 2.2 + rad * 2.2 - 0.2, 0)), 0.08, 0.04, 1.6, 6)
		# Schießscharten
		for i in 4:
			var a := TAU * i / 4.0 + 0.4
			_window(mb, Vector3(cos(a) * rad, h * 0.6, sin(a) * rad), Vector3(cos(a), 0, sin(a)), 0.35, 1.2, false)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var fl := _flagpole(Color.html("#8f1d2c"))
	fl.position = Vector3(0, h + 2.2 + rad * 2.2 + 1.2, 0)
	root.add_child(fl)
	return root


static func _flagpole(color: Color) -> Node3D:
	var mb := MeshBuilder.new()
	var cloth := Mat.stylized(color, Mat.P.CLOTH, {"wind": 1.6})
	mb.plane(cloth, Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(0.0, 0.0, 0.8)), 1.6, 0.9, Color.WHITE, 4)
	var n := Node3D.new()
	n.add_child(_mi(mb.commit(), false))
	return n


static func gatearch(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 10.0))
	var mesh := _cached("gatearch|%s" % w, func():
		var mb := MeshBuilder.new()
		var st := m("stone_castle")
		var h := 9.0
		for sx in [-1.0, 1.0]:
			mb.box(st, MeshBuilder.at(Vector3(sx * (w * 0.5 - 1.0), h * 0.5 - 1.5, 0)), Vector3(2.0, h + 3, 4.0))
		mb.box(st, MeshBuilder.at(Vector3(0, h - 1.0, 0)), Vector3(w, 3.2, 4.0))
		_crenellations(mb, st, Vector3(-w * 0.5, h + 0.6, -1.75), Vector3(w * 0.5, h + 0.6, -1.75), 0.5)
		_crenellations(mb, st, Vector3(-w * 0.5, h + 0.6, 1.75), Vector3(w * 0.5, h + 0.6, 1.75), 0.5)
		# Bogen
		for i in 9:
			var a := PI * i / 8.0
			var x := cos(a) * (w * 0.5 - 2.0)
			var y := 5.0 + sin(a) * 1.4
			mb.box(m("stone_dark"), MeshBuilder.at_euler(Vector3(x, y, -2.05), Vector3(0, 0, a - PI * 0.5)), Vector3(0.6, 0.9, 0.4))
		# Fallgitter (hochgezogen)
		for i in 7:
			var x := -w * 0.5 + 2.2 + i * (w - 4.4) / 6.0
			mb.box(m("iron"), MeshBuilder.at(Vector3(x, 6.0, 0)), Vector3(0.1, 2.0, 0.1))
		mb.box(m("iron"), MeshBuilder.at(Vector3(0, 5.2, 0)), Vector3(w - 4.0, 0.12, 0.12))
		# Wappen
		mb.box(m("cloth_red"), MeshBuilder.at(Vector3(0, 7.8, -2.06)), Vector3(1.6, 2.0, 0.05))
		mb.box(m("gold"), MeshBuilder.at(Vector3(0, 7.9, -2.1)), Vector3(0.7, 0.7, 0.05))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	for sx in [-1.0, 1.0]:
		var f := FxLib.fire(0.35)
		f.position = Vector3(sx * (w * 0.5 - 1.0), 4.0, -2.4)
		root.add_child(f)
	return root


static func keep(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 34.0))
	var d := float(p.get("d", 18.0))
	var mesh := _cached("keep|%s|%s" % [w, d], func():
		var mb := MeshBuilder.new()
		var st := m("stone_castle")
		var h := 13.0
		mb.box(m("stone_dark"), MeshBuilder.at(Vector3(0, 0.3, 0)), Vector3(w + 1.0, 1.6, d + 1.0))
		mb.box(st, MeshBuilder.at(Vector3(0, h * 0.5, 0)), Vector3(w, h, d))
		_crenellations(mb, st, Vector3(-w * 0.5, h, -d * 0.5 + 0.25), Vector3(w * 0.5, h, -d * 0.5 + 0.25), 0.5)
		_crenellations(mb, st, Vector3(-w * 0.5, h, d * 0.5 - 0.25), Vector3(w * 0.5, h, d * 0.5 - 0.25), 0.5)
		_crenellations(mb, st, Vector3(-w * 0.5 + 0.25, h, -d * 0.5), Vector3(-w * 0.5 + 0.25, h, d * 0.5), 0.5)
		_crenellations(mb, st, Vector3(w * 0.5 - 0.25, h, -d * 0.5), Vector3(w * 0.5 - 0.25, h, d * 0.5), 0.5)
		# Mittelbau (Halle) mit hohem Dach
		mb.box(st, MeshBuilder.at(Vector3(0, h + 3.0, 0)), Vector3(w * 0.5, 6.0, d * 0.7))
		mb.gable_roof(m("roof_blue"), MeshBuilder.at(Vector3(0, h + 6.0, 0)), w * 0.5, d * 0.7, d * 0.55, 0.6, 0.3, st)
		# Ecktürme
		for sx in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				var c := Vector3(sx * w * 0.5, 0, sz * d * 0.5)
				mb.cylinder(st, MeshBuilder.at(c), 3.2, 3.0, h + 5, 16)
				for i in 8:
					var a := TAU * i / 8.0
					mb.box(st, MeshBuilder.at(c + Vector3(cos(a) * 3.1, h + 5.5, sin(a) * 3.1), -a), Vector3(0.5, 1.0, 1.2))
				mb.cone_roof(m("roof_blue"), MeshBuilder.at(c + Vector3(0, h + 5.0, 0)), 3.4, 7.5, 16)
				mb.cylinder(m("gold"), MeshBuilder.at(c + Vector3(0, h + 12.3, 0)), 0.08, 0.03, 1.6, 6)
		# Großes Portal
		var fz := -d * 0.5
		mb.box(m("stone_dark"), MeshBuilder.at(Vector3(0, 3.4, fz - 0.4)), Vector3(7.0, 6.8, 1.2))
		mb.box(m("wood_dark"), MeshBuilder.at(Vector3(0, 2.6, fz - 1.02)), Vector3(4.2, 5.2, 0.1))
		for yy in [1.0, 2.4, 3.8]:
			mb.box(m("iron"), MeshBuilder.at(Vector3(0, yy, fz - 1.1)), Vector3(4.0, 0.12, 0.05))
		mb.box(m("stone_dark"), MeshBuilder.at(Vector3(0, 5.6, fz - 1.1)), Vector3(4.8, 0.6, 0.3))
		# Fensterreihen
		for i in 6:
			var x := -w * 0.5 + w * (i + 0.5) / 6.0
			if absf(x) < 4.0:
				continue
			_window(mb, Vector3(x, 8.5, fz), Vector3(0, 0, -1), 0.9, 1.8, false)
			_window(mb, Vector3(x, 3.5, fz), Vector3(0, 0, -1), 0.7, 1.4, false)
		# Banner an der Front
		for sx in [-1.0, 1.0]:
			mb.plane(m("cloth_red"), MeshBuilder.at(Vector3(sx * 5.5, 11.5, fz - 0.08)), 2.0, 6.0, Color.WHITE, 4)
			mb.box(m("gold"), MeshBuilder.at(Vector3(sx * 5.5, 9.4, fz - 0.12)), Vector3(0.9, 0.9, 0.05))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	for sx in [-1.0, 1.0]:
		var f := FxLib.fire(0.4)
		f.position = Vector3(sx * 4.0, 4.2, -d * 0.5 - 1.4)
		root.add_child(f)
		var fl := _flagpole(Color.html("#2d4f9a"))
		fl.position = Vector3(sx * w * 0.5, 13.0 + 13.2, -d * 0.5)
		root.add_child(fl)
	return root


static func village_gate(p: Dictionary) -> Node3D:
	var root := Node3D.new()
	var mb := MeshBuilder.new()
	for sx in [-1.0, 1.0]:
		mb.cylinder(m("wood"), MeshBuilder.at(Vector3(sx * 3.2, -0.3, 0)), 0.32, 0.28, 5.2, 10)
		mb.cone_roof(m("roof_red"), MeshBuilder.at(Vector3(sx * 3.2, 4.9, 0)), 0.55, 0.9, 8)
	mb.box(m("beam"), MeshBuilder.at(Vector3(0, 4.3, 0)), Vector3(7.2, 0.35, 0.4))
	mb.box(m("wood_light"), MeshBuilder.at(Vector3(0, 3.6, -0.05)), Vector3(3.6, 0.9, 0.12))
	for sx in [-1.0, 1.0]:
		mb.beam(m("beam"), Vector3(sx * 3.2, 3.2, 0), Vector3(sx * 2.0, 4.2, 0), Vector2(0.15, 0.15), Vector3.BACK)
	root.add_child(_mi(mb.commit()))
	if p.has("name"):
		var l := _label(str(p["name"]), 0.55, Color.html("#3a2412"))
		l.outline_modulate = Color(0.95, 0.85, 0.6, 1)
		l.outline_size = 4
		l.position = Vector3(0, 3.6, -0.13)
		l.rotation.y = PI
		root.add_child(l)
	return root


# =============================================================================== Dorfrequisiten
static func fountain(p: Dictionary) -> Node3D:
	var mesh := _cached("fountain", func():
		var mb := MeshBuilder.new()
		mb.cylinder(m("stone"), MeshBuilder.at(Vector3(0, -0.2, 0)), 3.0, 3.0, 0.9, 20)
		mb.torus(m("stone_castle"), MeshBuilder.at(Vector3(0, 0.72, 0)), 2.9, 0.22, 22, 6)
		mb.cylinder(m("water"), MeshBuilder.at(Vector3(0, 0.58, 0)), 2.75, 2.75, 0.02, 20, true)
		mb.cylinder(m("stone_castle"), MeshBuilder.at(Vector3(0, 0.5, 0)), 0.45, 0.35, 2.2, 10)
		mb.cylinder(m("stone"), MeshBuilder.at(Vector3(0, 2.6, 0)), 1.1, 0.4, 0.4, 14)
		mb.ellipsoid(m("stone_castle"), MeshBuilder.at(Vector3(0, 3.1, 0)), Vector3(0.35, 0.5, 0.35), 8, 6)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var spray := FxLib.particles(40, 1.2, 0.18, FxLib._ramp(Color(0.8, 0.9, 1.0, 0.0), Color(0.85, 0.95, 1.0, 0.6), Color(0.8, 0.9, 1.0, 0.0)),
		Vector3(0, 2.2, 0), 25.0, 0.1, Vector3(0, -5.5, 0), false)
	spray.position.y = 3.3
	root.add_child(spray)
	return root


static func well(p: Dictionary) -> Node3D:
	var mesh := _cached("well", func():
		var mb := MeshBuilder.new()
		mb.cylinder(m("stone"), MeshBuilder.at(Vector3(0, -0.2, 0)), 1.2, 1.2, 1.1, 14)
		mb.cylinder(m("dark"), MeshBuilder.at(Vector3(0, 0.9, 0)), 0.95, 0.95, 0.02, 14)
		mb.torus(m("stone_dark"), MeshBuilder.at(Vector3(0, 0.92, 0)), 1.12, 0.14, 16, 5)
		for sx in [-1.0, 1.0]:
			mb.box(m("wood"), MeshBuilder.at(Vector3(sx * 1.05, 1.9, 0)), Vector3(0.18, 2.2, 0.18))
		mb.box(m("wood_dark"), MeshBuilder.at(Vector3(0, 2.6, 0)), Vector3(2.3, 0.14, 0.14))
		mb.gable_roof(m("roof_red"), Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(0, 2.9, 0)), 1.6, 2.4, 0.9, 0.2, 0.1)
		mb.cylinder(m("wood"), MeshBuilder.at(Vector3(0.0, 1.6, 0)), 0.22, 0.2, 0.32, 10)
		mb.box(m("rope"), MeshBuilder.at(Vector3(0, 2.15, 0)), Vector3(0.03, 0.9, 0.03))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func windmill(p: Dictionary) -> Node3D:
	var mesh := _cached("windmill", func():
		var mb := MeshBuilder.new()
		mb.cylinder(m("stone"), MeshBuilder.at(Vector3(0, -0.5, 0)), 3.6, 2.6, 4.5, 16)
		mb.cylinder(m("plaster"), MeshBuilder.at(Vector3(0, 4.0, 0)), 2.7, 2.1, 5.0, 16)
		for i in 8:
			var a := TAU * i / 8.0
			mb.beam(m("beam"), Vector3(cos(a) * 2.68, 4.0, sin(a) * 2.68), Vector3(cos(a) * 2.12, 9.0, sin(a) * 2.12), Vector2(0.16, 0.16))
		mb.cone_roof(m("thatch"), MeshBuilder.at(Vector3(0, 8.9, 0)), 2.8, 3.2, 16)
		_door(mb, Vector3(0, 0.0, -3.4), Vector3(0, 0, -1), 1.2, 2.2)
		_window(mb, Vector3(0, 6.2, -2.4), Vector3(0, 0, -1), 0.7, 0.8, true)
		mb.cylinder(m("wood_dark"), MeshBuilder.at_euler(Vector3(0, 8.2, -2.0), Vector3(PI * 0.5, 0, 0)), 0.3, 0.3, 1.2, 8)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var blades := AnimNode3D.new()
	blades.mode = "spin"
	blades.axis = Vector3(0, 0, 1)
	blades.speed = 0.5
	blades.position = Vector3(0, 8.2, -3.3)
	var bm := _cached("windmill_blades", func():
		var mb := MeshBuilder.new()
		mb.cylinder(m("wood_dark"), MeshBuilder.at_euler(Vector3(0, 0, -0.3), Vector3(PI * 0.5, 0, 0)), 0.35, 0.35, 0.5, 8)
		for i in 4:
			var a := TAU * i / 4.0
			var dir := Vector3(cos(a), sin(a), 0)
			mb.beam(m("wood"), Vector3.ZERO, dir * 6.5, Vector2(0.18, 0.12), Vector3.BACK)
			var perp := Vector3(-dir.y, dir.x, 0)
			var center := dir * 4.0 + perp * 0.55
			mb.box(m("plaster"), Transform3D(Basis(Vector3.BACK, a), center + Vector3(0, 0, 0.08)), Vector3(4.6, 0.95, 0.04))
			for k in 6:
				mb.beam(m("beam"), dir * (1.8 + k * 0.85) + perp * 0.05, dir * (1.8 + k * 0.85) + perp * 1.05, Vector2(0.05, 0.05), Vector3.BACK)
		return mb.commit())
	blades.add_child(_mi(bm))
	root.add_child(blades)
	return root


static func barn(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 10.0))
	var d := float(p.get("d", 14.0))
	var mesh := _cached("barn|%s|%s" % [w, d], func():
		var mb := MeshBuilder.new()
		var red := Mat.stylized(Color.html("#9a3424"), Mat.P.WOOD, {"c2": Color.html("#4e1810")})
		var trim := Mat.stylized(Color.html("#ece4d0"), Mat.P.WOOD, {"c2": Color.html("#a89a80")})
		mb.box(m("stone"), MeshBuilder.at(Vector3(0, 0.1, 0)), Vector3(w + 0.3, 0.6, d + 0.3))
		mb.box(red, MeshBuilder.at(Vector3(0, 2.6, 0)), Vector3(w, 4.6, d))
		mb.gable_roof(m("roof_slate"), Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(0, 4.9, 0)), d, w, w * 0.55, 0.5, 0.2, red)
		# großes Tor vorne (Front -Z liegt hier auf der Längsseite)
		for sz in [-1.0, 1.0]:
			var fz = sz * d * 0.5
			mb.box(m("wood_dark"), MeshBuilder.at(Vector3(0, 2.0, fz + sz * 0.05)), Vector3(4.0, 3.6, 0.1))
			mb.beam(trim, Vector3(-2.0, 0.3, fz + sz * 0.12), Vector3(2.0, 3.7, fz + sz * 0.12), Vector2(0.2, 0.1), Vector3.BACK)
			mb.beam(trim, Vector3(2.0, 0.3, fz + sz * 0.12), Vector3(-2.0, 3.7, fz + sz * 0.12), Vector2(0.2, 0.1), Vector3.BACK)
			mb.box(trim, MeshBuilder.at(Vector3(0, 3.85, fz + sz * 0.12)), Vector3(4.4, 0.22, 0.12))
			mb.box(trim, MeshBuilder.at(Vector3(-2.1, 2.0, fz + sz * 0.12)), Vector3(0.22, 3.8, 0.12))
			mb.box(trim, MeshBuilder.at(Vector3(2.1, 2.0, fz + sz * 0.12)), Vector3(0.22, 3.8, 0.12))
			mb.box(m("wood_dark"), MeshBuilder.at(Vector3(0, 6.2, fz + sz * 0.05)), Vector3(1.4, 1.2, 0.1))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func field(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 20.0))
	var d := float(p.get("d", 14.0))
	var crop: String = p.get("crop", "wheat")
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var plant := _cached("crop|" + crop, func():
		var mb := MeshBuilder.new()
		if crop == "wheat":
			var straw := m("straw")
			for i in 5:
				var a := TAU * i / 5.0
				var base := Vector3(cos(a) * 0.12, 0, sin(a) * 0.12)
				var top := base * 1.6 + Vector3(0, 1.0, 0)
				mb.beam(straw, base, top, Vector2(0.025, 0.025))
				mb.ellipsoid(straw, MeshBuilder.at(top + Vector3(0, 0.08, 0)), Vector3(0.04, 0.12, 0.04), 5, 4)
		else:
			var leaf := Mat.stylized(Color.html("#4a8a2a"), Mat.P.PLAIN, {"rim": 0.25})
			var bulb := Mat.stylized(Color.html("#d8c8e8"), Mat.P.PLAIN)
			mb.ellipsoid(bulb, MeshBuilder.at(Vector3(0, 0.05, 0)), Vector3(0.16, 0.14, 0.16), 8, 5)
			for i in 4:
				var a := TAU * i / 4.0
				mb.ellipsoid(leaf, MeshBuilder.at_euler(Vector3(cos(a) * 0.1, 0.3, sin(a) * 0.1), Vector3(cos(a) * 0.5, 0, sin(a) * 0.5)), Vector3(0.08, 0.3, 0.05), 6, 4)
		return mb.commit())
	mm.mesh = plant
	var spacing := 0.9
	var nx := int(w / spacing)
	var nz := int(d / 0.7)
	mm.instance_count = nx * nz
	var k := 0
	var rng := RandomNumberGenerator.new()
	rng.seed = int(w * d)
	for i in nx:
		for j in nz:
			var x := -w * 0.5 + (i + 0.5) * spacing + rng.randf_range(-0.12, 0.12)
			var z := -d * 0.5 + (j + 0.5) * 0.7
			mm.set_instance_transform(k, Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.85, 1.15)), Vector3(x, 0, z)))
			k += 1
	var mmi := MultiMeshInstance3D.new()
	mmi.multimesh = mm
	mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mmi.visibility_range_end = 140.0
	var root := Node3D.new()
	root.add_child(mmi)
	return root


static func _segment_node(p: Dictionary) -> Array:
	var a := Vector3(float(p["x1"]), 0, float(p["z1"]))
	var b := Vector3(float(p["x2"]), 0, float(p["z2"]))
	return [a, b]


static var hf_ref: Heightfield


static func _ground(x: float, z: float) -> float:
	return hf_ref.height(x, z) if hf_ref else 0.0


static func fence(p: Dictionary, iron: bool) -> Node3D:
	var ab := _segment_node(p)
	var a: Vector3 = ab[0]
	var b: Vector3 = ab[1]
	var mb := MeshBuilder.new()
	var len := a.distance_to(b)
	var count := int(max(1, round(len / (2.0 if not iron else 1.6))))
	var post_mat := m("iron") if iron else m("wood")
	var prev := Vector3.ZERO
	for i in count + 1:
		var q := a.lerp(b, float(i) / count)
		q.y = _ground(q.x, q.z)
		if iron:
			mb.box(post_mat, MeshBuilder.at(q + Vector3(0, 0.9, 0)), Vector3(0.12, 1.8, 0.12))
			mb.cylinder(m("gold"), MeshBuilder.at(q + Vector3(0, 1.8, 0)), 0.08, 0.0, 0.2, 5)
		else:
			mb.cylinder(post_mat, MeshBuilder.at(q + Vector3(0, -0.2, 0)), 0.1, 0.09, 1.4, 6)
		if i > 0:
			for hh in ([0.5, 1.0] if not iron else [0.3, 1.5]):
				mb.beam(m("wood_light") if not iron else post_mat, prev + Vector3(0, hh, 0), q + Vector3(0, hh, 0), Vector2(0.07, 0.1) if not iron else Vector2(0.05, 0.05))
			if iron:
				for k in 6:
					var t := (k + 0.5) / 6.0
					var c := prev.lerp(q, t)
					mb.box(post_mat, MeshBuilder.at(c + Vector3(0, 0.9, 0)), Vector3(0.04, 1.4, 0.04))
		prev = q
	var n := Node3D.new()
	n.add_child(_mi(mb.commit()))
	return n


static func palisade(p: Dictionary) -> Node3D:
	var ab := _segment_node(p)
	var a: Vector3 = ab[0]
	var b: Vector3 = ab[1]
	var mb := MeshBuilder.new()
	var len := a.distance_to(b)
	var count := int(len / 0.42)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(len * 100)
	for i in count:
		var q := a.lerp(b, (i + 0.5) / count)
		q.y = _ground(q.x, q.z)
		var h := rng.randf_range(3.0, 3.6)
		mb.cylinder(m("wood"), MeshBuilder.at(q + Vector3(0, -0.4, 0), rng.randf() * TAU), 0.2, 0.2, h, 7)
		mb.cylinder(m("wood_light"), MeshBuilder.at(q + Vector3(0, h - 0.4, 0)), 0.2, 0.0, 0.6, 7)
	var dir := b - a
	for hh in [1.0, 2.2]:
		mb.beam(m("rope"), a + Vector3(0, _ground(a.x, a.z) + hh, 0), b + Vector3(0, _ground(b.x, b.z) + hh, 0), Vector2(0.06, 0.06))
	var n := Node3D.new()
	n.add_child(_mi(mb.commit()))
	return n


static func haystack(p: Dictionary) -> Node3D:
	var mesh := _cached("haystack", func():
		var mb := MeshBuilder.new()
		mb.ellipsoid(m("straw"), MeshBuilder.at(Vector3(0, 0.2, 0)), Vector3(1.6, 1.5, 1.6), 14, 8, Color.WHITE, 0.12, 1.2, 3, -0.2, 1.0)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func tent(p: Dictionary) -> Node3D:
	var c := Mat.col(p.get("c", "#8a2a2a"))
	var mesh := _cached("tent|" + c.to_html(), func():
		var mb := MeshBuilder.new()
		var cloth := Mat.stylized(c, Mat.P.CLOTH, {"c2": c.darkened(0.4)})
		mb.gable_roof(cloth, Transform3D(Basis(Vector3.UP, PI * 0.5), Vector3(0, 0.0, 0)), 4.2, 3.6, 2.4, 0.1, 0.05, cloth)
		mb.cylinder(m("wood"), MeshBuilder.at(Vector3(0, 0, -2.0)), 0.06, 0.06, 2.7, 6)
		mb.cylinder(m("wood"), MeshBuilder.at(Vector3(0, 0, 2.0)), 0.06, 0.06, 2.7, 6)
		mb.box(m("dark"), MeshBuilder.at(Vector3(0, 0.6, -2.12)), Vector3(1.0, 1.2, 0.02))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func bigtent(p: Dictionary) -> Node3D:
	var c := Mat.col(p.get("c", "#9a1f1f"))
	var mesh := _cached("bigtent|" + c.to_html(), func():
		var mb := MeshBuilder.new()
		var cloth := Mat.stylized(c, Mat.P.CLOTH, {"c2": c.darkened(0.4)})
		var stripe := Mat.stylized(Color.html("#e8d8b0"), Mat.P.CLOTH)
		mb.cylinder(cloth, MeshBuilder.at(Vector3(0, 0, 0)), 3.6, 3.6, 2.2, 16, false)
		mb.cylinder(cloth, MeshBuilder.at(Vector3(0, 2.2, 0)), 4.0, 0.2, 2.8, 16)
		for i in 8:
			var a := TAU * i / 8.0
			mb.beam(stripe, Vector3(cos(a) * 4.0, 2.2, sin(a) * 4.0), Vector3(cos(a) * 0.2, 5.0, sin(a) * 0.2), Vector2(0.25, 0.04))
		mb.cylinder(m("wood"), MeshBuilder.at(Vector3(0, 4.9, 0)), 0.08, 0.05, 1.2, 6)
		mb.box(m("dark"), MeshBuilder.at(Vector3(0, 1.0, -3.6)), Vector3(1.4, 2.0, 0.05))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var fl := _flagpole(c)
	fl.position = Vector3(0, 6.0, 0)
	root.add_child(fl)
	return root


static func campfire(p: Dictionary) -> Node3D:
	var mesh := _cached("campfire", func():
		var mb := MeshBuilder.new()
		for i in 9:
			var a := TAU * i / 9.0
			mb.ellipsoid(m("stone"), MeshBuilder.at(Vector3(cos(a) * 0.75, 0.05, sin(a) * 0.75)), Vector3(0.22, 0.16, 0.2), 6, 4, Color.WHITE, 0.2, 2.0, i)
		for i in 4:
			var a := TAU * i / 4.0 + 0.3
			mb.beam(m("wood_dark"), Vector3(cos(a) * 0.55, 0.05, sin(a) * 0.55), Vector3(cos(a) * 0.05, 0.4, sin(a) * 0.05), Vector2(0.12, 0.12))
		mb.disc(Mat.emissive(Color.html("#ff6a20"), 2.5), MeshBuilder.at(Vector3(0, 0.06, 0)), 0.45, 10)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var f := FxLib.fire(1.0)
	f.position.y = 0.15
	root.add_child(f)
	return root


static func watchtower(p: Dictionary) -> Node3D:
	var mesh := _cached("watchtower", func():
		var mb := MeshBuilder.new()
		for sx in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				mb.beam(m("wood"), Vector3(sx * 1.6, -0.5, sz * 1.6), Vector3(sx * 1.1, 6.0, sz * 1.1), Vector2(0.28, 0.28))
		for yy in [2.0, 4.0]:
			mb.beam(m("wood_dark"), Vector3(-1.5, yy, -1.5), Vector3(1.5, yy - 1.4, -1.5), Vector2(0.12, 0.12), Vector3.BACK)
			mb.beam(m("wood_dark"), Vector3(-1.5, yy, 1.5), Vector3(1.5, yy - 1.4, 1.5), Vector2(0.12, 0.12), Vector3.BACK)
		mb.box(m("wood_light"), MeshBuilder.at(Vector3(0, 6.0, 0)), Vector3(3.4, 0.2, 3.4))
		for s in [[0, -1.7], [0, 1.7], [-1.7, 0], [1.7, 0]]:
			var rot := 0.0 if s[0] == 0 else PI * 0.5
			mb.box(m("wood"), MeshBuilder.at(Vector3(s[0], 6.55, s[1]), rot), Vector3(3.4, 0.9, 0.12))
		for sx in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				mb.beam(m("wood"), Vector3(sx * 1.6, 6.0, sz * 1.6), Vector3(sx * 1.6, 8.2, sz * 1.6), Vector2(0.14, 0.14))
		mb.cone_roof(m("thatch"), MeshBuilder.at(Vector3(0, 8.2, 0), PI * 0.25), 2.8, 1.8, 4)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var f := FxLib.fire(0.3)
	f.position = Vector3(1.2, 7.0, -1.2)
	root.add_child(f)
	return root


static func mine(p: Dictionary) -> Node3D:
	var mesh := _cached("mine", func():
		var mb := MeshBuilder.new()
		var rng := RandomNumberGenerator.new()
		rng.seed = 77
		var rock := Mat.stylized(Color.html("#8a8070"), Mat.P.ROCK, {"c2": Color.html("#4a443c"), "tri": true})
		for i in 9:
			var a := PI * (0.05 + 0.9 * i / 8.0)
			mb.ellipsoid(rock, MeshBuilder.at(Vector3(cos(a) * 4.2, sin(a) * 3.8, 1.5 + rng.randf_range(-0.5, 0.5))), Vector3(2.2, 2.0, 2.4), 9, 6, Color.WHITE, 0.3, 1.0, i)
		mb.ellipsoid(rock, MeshBuilder.at(Vector3(0, 5.0, 3.0)), Vector3(5.5, 2.8, 4.0), 12, 7, Color.WHITE, 0.3, 0.8, 99)
		mb.box(m("dark"), MeshBuilder.at(Vector3(0, 1.6, 0.6)), Vector3(3.6, 3.6, 0.4))
		for sx in [-1.0, 1.0]:
			mb.box(m("wood"), MeshBuilder.at(Vector3(sx * 1.9, 1.6, 0.0)), Vector3(0.35, 3.6, 0.35))
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 3.5, 0.0)), Vector3(4.5, 0.4, 0.45))
		mb.beam(m("wood_dark"), Vector3(-1.9, 2.8, -0.2), Vector3(-1.0, 3.4, -0.2), Vector2(0.15, 0.15), Vector3.BACK)
		mb.beam(m("wood_dark"), Vector3(1.9, 2.8, -0.2), Vector3(1.0, 3.4, -0.2), Vector2(0.15, 0.15), Vector3.BACK)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func rails(p: Dictionary) -> Node3D:
	var ab := _segment_node(p)
	var a: Vector3 = ab[0]
	var b: Vector3 = ab[1]
	var mb := MeshBuilder.new()
	var dir := (b - a).normalized()
	var side := Vector3(-dir.z, 0, dir.x)
	var len := a.distance_to(b)
	for i in int(len / 0.8):
		var q := a + dir * (i * 0.8 + 0.4)
		q.y = _ground(q.x, q.z) + 0.05
		mb.beam(m("wood_dark"), q - side * 0.75, q + side * 0.75, Vector2(0.18, 0.1))
	for s in [-0.5, 0.5]:
		var pa = a + side * s
		var pb = b + side * s
		pa.y = _ground(pa.x, pa.z) + 0.15
		pb.y = _ground(pb.x, pb.z) + 0.15
		mb.beam(m("iron"), pa, pb, Vector2(0.06, 0.08))
	var n := Node3D.new()
	n.add_child(_mi(mb.commit()))
	return n


static func minecart(p: Dictionary) -> Node3D:
	var mesh := _cached("minecart", func():
		var mb := MeshBuilder.new()
		mb.box(m("iron"), MeshBuilder.at(Vector3(0, 0.75, 0)), Vector3(1.0, 0.7, 1.5))
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 0.75, 0)), Vector3(1.05, 0.5, 1.55))
		for sx in [-1.0, 1.0]:
			for sz in [-0.5, 0.5]:
				mb.cylinder(m("iron"), MeshBuilder.at_euler(Vector3(sx * 0.55, 0.3, sz), Vector3(0, 0, PI * 0.5)), 0.25, 0.25, 0.1, 10)
		for i in 5:
			mb.ellipsoid(m("ore"), MeshBuilder.at(Vector3(randf_range(-0.3, 0.3), 1.12, randf_range(-0.5, 0.5))), Vector3(0.25, 0.18, 0.22), 6, 4, Color.WHITE, 0.3, 2.0, i)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func lantern(p: Dictionary) -> Node3D:
	var mesh := _cached("lantern", func():
		var mb := MeshBuilder.new()
		mb.cylinder(m("iron"), MeshBuilder.at(Vector3(0, -0.2, 0)), 0.1, 0.07, 3.0, 8)
		mb.beam(m("iron"), Vector3(0, 2.7, 0), Vector3(0.6, 2.7, 0), Vector2(0.06, 0.06))
		mb.box(m("iron"), MeshBuilder.at(Vector3(0.6, 2.35, 0)), Vector3(0.36, 0.06, 0.36))
		mb.box(Mat.emissive(Color.html("#ffc060"), 3.0), MeshBuilder.at(Vector3(0.6, 2.2, 0)), Vector3(0.24, 0.32, 0.24))
		mb.cone_roof(m("iron"), MeshBuilder.at(Vector3(0.6, 2.38, 0)), 0.24, 0.25, 4)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var l := FxLib.light(Color.html("#ffb860"), 1.6, 9.0)
	l.position = Vector3(0.6, 2.1, 0)
	root.add_child(l)
	var g := FxLib.glow_sprite(Color(1, 0.7, 0.3, 0.5), 1.4)
	g.position = Vector3(0.6, 2.2, 0)
	root.add_child(g)
	return root


static func graves(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 12.0))
	var d := float(p.get("d", 8.0))
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = int(float(p.get("x", 0)) * 31 + float(p.get("z", 0)))
	var nx := int(w / 2.2)
	var nz := int(d / 2.6)
	for i in nx:
		for j in nz:
			var x := -w * 0.5 + (i + 0.5) * w / nx + rng.randf_range(-0.3, 0.3)
			var z := -d * 0.5 + (j + 0.5) * d / nz
			var kind := rng.randi() % 3
			var tilt := rng.randf_range(-0.15, 0.15)
			var xf := MeshBuilder.at_euler(Vector3(x, 0, z), Vector3(tilt, rng.randf_range(-0.2, 0.2), tilt * 0.5))
			if kind == 0:
				mb.box(m("grave"), xf * Transform3D(Basis(), Vector3(0, 0.55, 0)), Vector3(0.75, 1.1, 0.18))
				mb.cylinder(m("grave"), xf * Transform3D(Basis(Vector3.RIGHT, PI * 0.5), Vector3(0, 1.1, -0.09)), 0.375, 0.375, 0.18, 10, true)
			elif kind == 1:
				mb.box(m("grave"), xf * Transform3D(Basis(), Vector3(0, 0.7, 0)), Vector3(0.16, 1.4, 0.16))
				mb.box(m("grave"), xf * Transform3D(Basis(), Vector3(0, 1.05, 0)), Vector3(0.75, 0.16, 0.16))
			else:
				mb.box(m("grave"), xf * Transform3D(Basis(), Vector3(0, 0.4, 0)), Vector3(0.9, 0.8, 0.22))
			mb.ellipsoid(m("soil"), MeshBuilder.at(Vector3(x, 0.0, z + 1.0)), Vector3(0.5, 0.18, 0.95), 8, 4, Color.WHITE, 0.1, 1.0, i * 7 + j, 0.0, 1.0)
	var n := Node3D.new()
	n.add_child(_mi(mb.commit()))
	return n


static func mausoleum(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 10.0))
	var d := float(p.get("d", 12.0))
	var mesh := _cached("mausoleum|%s|%s" % [w, d], func():
		var mb := MeshBuilder.new()
		var st := Mat.stylized(Color.html("#8a8a92"), Mat.P.STONE, {"c2": Color.html("#3e3e46")})
		mb.box(st, MeshBuilder.at(Vector3(0, 0.3, 0)), Vector3(w + 1.0, 0.8, d + 1.0))
		mb.box(st, MeshBuilder.at(Vector3(0, 3.0, 0.8)), Vector3(w, 5.0, d - 1.6))
		mb.gable_roof(m("roof_slate"), MeshBuilder.at(Vector3(0, 5.5, 0)), w, d, 2.4, 0.5, 0.3, st)
		for i in 4:
			var x := -w * 0.5 + 1.0 + i * (w - 2.0) / 3.0
			mb.cylinder(m("marble"), MeshBuilder.at(Vector3(x, 0.7, -d * 0.5 + 0.6)), 0.4, 0.35, 4.8, 12)
		mb.box(st, MeshBuilder.at(Vector3(0, 5.3, -d * 0.5 + 0.6)), Vector3(w, 0.6, 1.4))
		mb.box(m("dark"), MeshBuilder.at(Vector3(0, 2.0, -d * 0.5 + 1.62)), Vector3(2.4, 3.2, 0.1))
		mb.box(m("iron"), MeshBuilder.at(Vector3(0, 2.0, -d * 0.5 + 1.55)), Vector3(2.5, 3.3, 0.05))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var l := FxLib.light(Color.html("#7a9aff"), 1.4, 6.0)
	l.position = Vector3(0, 2.0, -d * 0.5)
	root.add_child(l)
	return root


static func pier(p: Dictionary) -> Node3D:
	var len := float(p.get("len", 7.0))
	var mb := MeshBuilder.new()
	for i in int(len / 0.45):
		mb.box(m("wood_light"), MeshBuilder.at(Vector3(0, 0.0, -0.225 - i * 0.45)), Vector3(2.2, 0.1, 0.4))
	for i in int(len / 2.0) + 1:
		for sx in [-1.0, 1.0]:
			mb.cylinder(m("wood_dark"), MeshBuilder.at(Vector3(sx * 1.0, -1.6, -i * 2.0)), 0.12, 0.12, 2.1, 6)
	var n := Node3D.new()
	n.add_child(_mi(mb.commit()))
	return n


static func hut(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 6.0))
	var d := float(p.get("d", 6.0))
	var mesh := _cached("hut|%s|%s" % [w, d], func():
		var mb := MeshBuilder.new()
		mb.box(m("stone"), MeshBuilder.at(Vector3(0, 0.0, 0)), Vector3(w + 0.2, 0.6, d + 0.2))
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 1.5, 0)), Vector3(w, 2.6, d))
		_door(mb, Vector3(0, 0.25, -d * 0.5), Vector3(0, 0, -1), 1.0, 1.9)
		_window(mb, Vector3(w * 0.5, 1.6, 0), Vector3(1, 0, 0), 0.7, 0.7, true)
		mb.gable_roof(m("thatch"), MeshBuilder.at(Vector3(0, 2.8, 0)), w, d, d * 0.6, 0.6, 0.35, m("wood"))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func cauldron(p: Dictionary) -> Node3D:
	var mesh := _cached("cauldron", func():
		var mb := MeshBuilder.new()
		mb.ellipsoid(m("iron"), MeshBuilder.at(Vector3(0, 0.55, 0)), Vector3(0.65, 0.5, 0.65), 12, 8, Color.WHITE, 0.0, 1.0, 0, -1.0, 0.6)
		mb.torus(m("iron"), MeshBuilder.at(Vector3(0, 0.95, 0)), 0.55, 0.06, 14, 4)
		mb.disc(Mat.stylized(Color.html("#5ae04a"), Mat.P.PLAIN, {"emis": Color.html("#3ac03a"), "emis_e": 1.5}), MeshBuilder.at(Vector3(0, 0.88, 0)), 0.52, 14)
		for i in 3:
			var a := TAU * i / 3.0
			mb.beam(m("iron"), Vector3(cos(a) * 0.5, 0.0, sin(a) * 0.5), Vector3(cos(a) * 0.45, 0.4, sin(a) * 0.45), Vector2(0.06, 0.06))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var bub := FxLib.particles(10, 1.5, 0.2, FxLib._ramp(Color(0.4, 1.0, 0.3, 0.0), Color(0.5, 1.0, 0.4, 0.7), Color(0.6, 1.0, 0.5, 0.0)), Vector3(0, 0.8, 0), 10.0, 0.3)
	bub.position.y = 0.9
	root.add_child(bub)
	var l := FxLib.light(Color.html("#6aff5a"), 1.0, 4.0)
	l.position.y = 1.2
	root.add_child(l)
	return root


static func stall(p: Dictionary) -> Node3D:
	var c := Mat.col(p.get("c", "#c9862f"))
	var mesh := _cached("stall|" + c.to_html(), func():
		var mb := MeshBuilder.new()
		var cloth := Mat.stylized(c, Mat.P.CLOTH)
		var stripe := Mat.stylized(Color.html("#efe4cc"), Mat.P.CLOTH)
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 0.9, 0)), Vector3(3.0, 0.12, 1.4))
		mb.box(m("wood_dark"), MeshBuilder.at(Vector3(0, 0.45, -0.6)), Vector3(3.0, 0.9, 0.08))
		for sx in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				mb.box(m("wood_dark"), MeshBuilder.at(Vector3(sx * 1.4, 1.2, sz * 0.62)), Vector3(0.12, 2.4 if sz > 0 else 2.0, 0.12))
		for i in 6:
			var mat := cloth if i % 2 == 0 else stripe
			var x := -1.5 + (i + 0.5) * 0.5
			mb.beam(mat, Vector3(x, 2.45, 0.7), Vector3(x, 2.05, -1.0), Vector2(0.5, 0.03), Vector3.UP)
		# Waren
		var fruits := [Color.html("#e04030"), Color.html("#f0c030"), Color.html("#60b030"), Color.html("#a050c0")]
		for i in 10:
			var f := Mat.stylized(fruits[i % 4], Mat.P.PLAIN, {"rim": 0.3})
			mb.ellipsoid(f, MeshBuilder.at(Vector3(-1.2 + (i % 5) * 0.55, 1.05, -0.3 + int(i / 5) * 0.4)), Vector3(0.14, 0.12, 0.14), 7, 5)
		mb.box(m("wood_light"), MeshBuilder.at(Vector3(1.0, 1.15, 0.2)), Vector3(0.6, 0.4, 0.5))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func cart(p: Dictionary) -> Node3D:
	var mesh := _cached("cart", func():
		var mb := MeshBuilder.new()
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 0.95, 0)), Vector3(1.6, 0.12, 2.6))
		for sx in [-1.0, 1.0]:
			mb.box(m("wood"), MeshBuilder.at(Vector3(sx * 0.8, 1.25, 0)), Vector3(0.08, 0.5, 2.6))
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 1.25, 1.3)), Vector3(1.6, 0.5, 0.08))
		for sx in [-1.0, 1.0]:
			mb.cylinder(m("wood_dark"), MeshBuilder.at_euler(Vector3(sx * 0.95, 0.55, 0.3), Vector3(0, 0, PI * 0.5)), 0.55, 0.55, 0.12, 14)
			mb.torus(m("iron"), MeshBuilder.at_euler(Vector3(sx * 0.95, 0.55, 0.3), Vector3(0, 0, PI * 0.5)), 0.55, 0.04, 14, 4)
		mb.beam(m("wood_dark"), Vector3(-0.3, 0.9, -1.3), Vector3(-0.3, 0.5, -3.0), Vector2(0.1, 0.1))
		mb.beam(m("wood_dark"), Vector3(0.3, 0.9, -1.3), Vector3(0.3, 0.5, -3.0), Vector2(0.1, 0.1))
		for i in 3:
			mb.cylinder(m("wood_light"), MeshBuilder.at(Vector3(-0.4 + i * 0.4, 1.0, 0.4)), 0.25, 0.25, 0.7, 8)
		mb.ellipsoid(m("straw"), MeshBuilder.at(Vector3(0, 1.1, -0.5)), Vector3(0.6, 0.35, 0.7), 8, 5)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func signpost(p: Dictionary) -> Node3D:
	var root := Node3D.new()
	var mb := MeshBuilder.new()
	mb.cylinder(m("wood"), MeshBuilder.at(Vector3(0, -0.2, 0)), 0.1, 0.09, 3.0, 8)
	var texts: Array = p.get("text", [])
	for i in texts.size():
		var y := 2.4 - i * 0.45
		var right := str(texts[i]).ends_with("→") or str(texts[i]).ends_with("↘") or str(texts[i]).ends_with("↑")
		var sx := 1.0 if right else -1.0
		mb.box(m("wood_light"), MeshBuilder.at(Vector3(sx * 0.7, y, 0)), Vector3(1.4, 0.32, 0.06))
		mb.box(m("wood_light"), MeshBuilder.at_euler(Vector3(sx * 1.45, y, 0), Vector3(0, 0, PI * 0.25)), Vector3(0.22, 0.22, 0.06))
		for side in [-1.0, 1.0]:
			var l := _label(str(texts[i]).replace("→", "").replace("←", "").replace("↑", "").replace("↓", "").replace("↘", "").replace("↙", "").strip_edges(), 0.13, Color.html("#3a2412"))
			l.outline_size = 2
			l.outline_modulate = Color(0.85, 0.7, 0.45, 1)
			l.double_sided = false
			l.position = Vector3(sx * 0.7, y, side * 0.04)
			l.rotation.y = 0.0 if side > 0 else PI
			root.add_child(l)
	root.add_child(_mi(mb.commit()))
	return root


static func bench(p: Dictionary) -> Node3D:
	var mesh := _cached("bench", func():
		var mb := MeshBuilder.new()
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 0.45, 0)), Vector3(1.8, 0.08, 0.45))
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 0.8, 0.2)), Vector3(1.8, 0.3, 0.06))
		for sx in [-0.75, 0.75]:
			mb.box(m("wood_dark"), MeshBuilder.at(Vector3(sx, 0.22, 0)), Vector3(0.08, 0.45, 0.4))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func barrel(p: Dictionary) -> Node3D:
	var mesh := _cached("barrel", func():
		var mb := MeshBuilder.new()
		mb.ellipsoid(m("wood"), MeshBuilder.at(Vector3(0, 0.5, 0)), Vector3(0.42, 0.55, 0.42), 12, 8, Color.WHITE, 0.0, 1.0, 0, -0.85, 0.85)
		for yy in [0.18, 0.5, 0.82]:
			mb.torus(m("iron"), MeshBuilder.at(Vector3(0, yy, 0)), 0.38 if yy != 0.5 else 0.43, 0.03, 12, 4)
		mb.disc(m("wood_light"), MeshBuilder.at(Vector3(0, 0.95, 0)), 0.33, 12)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func crate(p: Dictionary) -> Node3D:
	var mesh := _cached("crate", func():
		var mb := MeshBuilder.new()
		mb.box(m("wood_light"), MeshBuilder.at(Vector3(0, 0.45, 0)), Vector3(0.9, 0.9, 0.9))
		for sx in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				mb.box(m("wood_dark"), MeshBuilder.at(Vector3(sx * 0.42, 0.45, sz * 0.42)), Vector3(0.1, 0.92, 0.1))
		mb.beam(m("wood_dark"), Vector3(-0.42, 0.05, -0.46), Vector3(0.42, 0.85, -0.46), Vector2(0.08, 0.04), Vector3.BACK)
		mb.beam(m("wood_dark"), Vector3(-0.42, 0.05, 0.46), Vector3(0.42, 0.85, 0.46), Vector2(0.08, 0.04), Vector3.BACK)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func banner(p: Dictionary) -> Node3D:
	var c := Mat.col(p.get("c", "#8f1d2c"))
	var root := Node3D.new()
	var mb := MeshBuilder.new()
	mb.cylinder(m("wood_dark"), MeshBuilder.at(Vector3(0, -0.2, 0)), 0.07, 0.06, 5.2, 6)
	mb.beam(m("gold"), Vector3(-0.8, 4.8, 0), Vector3(0.8, 4.8, 0), Vector2(0.06, 0.06))
	mb.ellipsoid(m("gold"), MeshBuilder.at(Vector3(0, 5.05, 0)), Vector3(0.12, 0.12, 0.12), 6, 4)
	root.add_child(_mi(mb.commit()))
	var mb2 := MeshBuilder.new()
	var cloth := Mat.stylized(c, Mat.P.CLOTH, {"wind": 0.8})
	mb2.plane(cloth, MeshBuilder.at(Vector3(0, 4.75, 0.05)), 1.5, 3.0, Color.WHITE, 5)
	mb2.box(m("gold"), MeshBuilder.at(Vector3(0, 3.7, 0.08)), Vector3(0.6, 0.6, 0.02))
	root.add_child(_mi(mb2.commit(), false))
	return root


static func weaponrack(p: Dictionary) -> Node3D:
	var mesh := _cached("weaponrack", func():
		var mb := MeshBuilder.new()
		for sx in [-1.0, 1.0]:
			mb.box(m("wood_dark"), MeshBuilder.at(Vector3(sx * 1.0, 0.7, 0)), Vector3(0.12, 1.4, 0.3))
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 1.2, 0)), Vector3(2.2, 0.1, 0.12))
		mb.box(m("wood"), MeshBuilder.at(Vector3(0, 0.2, 0)), Vector3(2.2, 0.1, 0.4))
		for i in 5:
			var x := -0.8 + i * 0.4
			mb.beam(m("iron"), Vector3(x, 0.25, 0.05), Vector3(x + 0.05, 1.6, 0.0), Vector2(0.06, 0.02))
			mb.box(m("wood_dark"), MeshBuilder.at(Vector3(x, 0.3, 0.05)), Vector3(0.22, 0.06, 0.06))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func anvil(p: Dictionary) -> Node3D:
	var mesh := _cached("anvil", func():
		var mb := MeshBuilder.new()
		mb.cylinder(m("wood"), MeshBuilder.at(Vector3(0, 0, 0)), 0.4, 0.38, 0.55, 10)
		mb.box(m("iron"), MeshBuilder.at(Vector3(0, 0.62, 0)), Vector3(0.28, 0.16, 0.5))
		mb.box(m("iron"), MeshBuilder.at(Vector3(0, 0.78, 0)), Vector3(0.35, 0.16, 0.8))
		mb.cylinder(m("iron"), MeshBuilder.at_euler(Vector3(0, 0.78, -0.4), Vector3(-PI * 0.5, 0, 0)), 0.08, 0.0, 0.35, 6)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func throne(p: Dictionary) -> Node3D:
	var mesh := _cached("throne", func():
		var mb := MeshBuilder.new()
		mb.box(m("stone_castle"), MeshBuilder.at(Vector3(0, 0.2, 0)), Vector3(3.2, 0.4, 2.6))
		mb.box(m("stone_castle"), MeshBuilder.at(Vector3(0, 0.55, 0.2)), Vector3(2.6, 0.3, 2.0))
		mb.box(m("gold"), MeshBuilder.at(Vector3(0, 1.05, 0.4)), Vector3(1.3, 0.7, 1.0))
		mb.box(m("red_cushion"), MeshBuilder.at(Vector3(0, 1.45, 0.35)), Vector3(1.1, 0.14, 0.9))
		mb.box(m("gold"), MeshBuilder.at(Vector3(0, 2.4, 0.85)), Vector3(1.4, 2.6, 0.2))
		mb.box(m("red_cushion"), MeshBuilder.at(Vector3(0, 2.2, 0.73)), Vector3(1.0, 1.8, 0.06))
		for sx in [-1.0, 1.0]:
			mb.box(m("gold"), MeshBuilder.at(Vector3(sx * 0.65, 1.7, 0.35)), Vector3(0.14, 0.2, 0.9))
			mb.ellipsoid(m("gold"), MeshBuilder.at(Vector3(sx * 0.7, 3.8, 0.85)), Vector3(0.16, 0.16, 0.16), 8, 6)
		mb.cylinder(m("gold"), MeshBuilder.at(Vector3(0, 3.7, 0.85)), 0.35, 0.0, 0.7, 8)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func rosegarden(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 10.0))
	var d := float(p.get("d", 16.0))
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	for sx in [-1.0, 1.0]:
		for i in int(d / 1.4):
			var z := -d * 0.5 + (i + 0.5) * 1.4
			var c := Vector3(sx * w * 0.5, 0.45, z)
			mb.ellipsoid(m("hedge"), MeshBuilder.at(c), Vector3(0.7, 0.6, 0.75), 8, 6, Color(0.6, 0.5, 0, 1), 0.15, 1.5, i, -0.6, 1.0, 0.4)
			for k in 3:
				mb.ellipsoid(m("rose"), MeshBuilder.at(c + Vector3(rng.randf_range(-0.5, 0.5), rng.randf_range(0.1, 0.5), rng.randf_range(-0.5, 0.5))), Vector3(0.09, 0.08, 0.09), 6, 4)
	mb.box(m("flag"), MeshBuilder.at(Vector3(0, 0.02, 0)), Vector3(1.4, 0.06, d))
	var n := Node3D.new()
	n.add_child(_mi(mb.commit()))
	return n


static func brazier(p: Dictionary) -> Node3D:
	var mesh := _cached("brazier", func():
		var mb := MeshBuilder.new()
		for i in 3:
			var a := TAU * i / 3.0
			mb.beam(m("iron"), Vector3(cos(a) * 0.4, 0, sin(a) * 0.4), Vector3(cos(a) * 0.15, 1.0, sin(a) * 0.15), Vector2(0.06, 0.06))
		mb.ellipsoid(m("iron"), MeshBuilder.at(Vector3(0, 1.1, 0)), Vector3(0.45, 0.25, 0.45), 10, 6, Color.WHITE, 0, 1, 0, -1.0, 0.3)
		mb.disc(Mat.emissive(Color.html("#ff6a20"), 2.5), MeshBuilder.at(Vector3(0, 1.17, 0)), 0.38, 10)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var f := FxLib.fire(0.55)
	f.position.y = 1.15
	root.add_child(f)
	return root


static func shed(p: Dictionary) -> Node3D:
	var w := float(p.get("w", 4.0))
	var d := float(p.get("d", 4.0))
	var mb := MeshBuilder.new()
	mb.box(m("wood"), MeshBuilder.at(Vector3(0, 1.1, d * 0.5 - 0.1)), Vector3(w, 2.2, 0.15))
	for sx in [-1.0, 1.0]:
		mb.box(m("wood"), MeshBuilder.at(Vector3(sx * (w * 0.5 - 0.08), 1.1, 0)), Vector3(0.15, 2.2, d))
	mb.gable_roof(m("roof_slate"), MeshBuilder.at(Vector3(0, 2.2, 0)), w, d, 1.0, 0.3, 0.12)
	for i in 3:
		mb.box(m("wood_light"), MeshBuilder.at(Vector3(-0.8 + i * 0.6, 0.4, 0.8)), Vector3(0.5, 0.8, 0.5))
	var n := Node3D.new()
	n.add_child(_mi(mb.commit()))
	return n


static func scarecrow(p: Dictionary) -> Node3D:
	var mesh := _cached("scarecrow", func():
		var mb := MeshBuilder.new()
		mb.cylinder(m("wood"), MeshBuilder.at(Vector3(0, -0.3, 0)), 0.07, 0.06, 2.4, 6)
		mb.beam(m("wood"), Vector3(-0.9, 1.6, 0), Vector3(0.9, 1.6, 0), Vector2(0.07, 0.07))
		var shirt := Mat.stylized(Color.html("#6a7a3a"), Mat.P.CLOTH)
		mb.box(shirt, MeshBuilder.at(Vector3(0, 1.35, 0)), Vector3(0.6, 0.7, 0.3))
		mb.beam(shirt, Vector3(-0.85, 1.58, 0), Vector3(0.85, 1.58, 0), Vector2(0.22, 0.22))
		var pump := Mat.stylized(Color.html("#e07a20"), Mat.P.PLAIN, {"rim": 0.3})
		mb.ellipsoid(pump, MeshBuilder.at(Vector3(0, 2.0, 0)), Vector3(0.28, 0.24, 0.28), 10, 7, Color.WHITE, 0.08, 3.0, 5)
		mb.cylinder(m("straw"), MeshBuilder.at(Vector3(0, 2.18, 0)), 0.42, 0.42, 0.04, 12)
		mb.cylinder(m("straw"), MeshBuilder.at(Vector3(0, 2.2, 0)), 0.2, 0.15, 0.25, 10)
		for sx in [-1.0, 1.0]:
			mb.box(Mat.emissive(Color.html("#ffc040"), 1.5), MeshBuilder.at(Vector3(sx * 0.1, 2.05, -0.26)), Vector3(0.07, 0.07, 0.02))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func orepile(p: Dictionary) -> Node3D:
	var mesh := _cached("orepile", func():
		var mb := MeshBuilder.new()
		var rock := Mat.stylized(Color.html("#7a7068"), Mat.P.ROCK, {"tri": true})
		for i in 7:
			var a := TAU * i / 7.0
			mb.ellipsoid(rock if i % 2 == 0 else m("ore"), MeshBuilder.at(Vector3(cos(a) * 0.6, 0.2, sin(a) * 0.6)), Vector3(0.45, 0.35, 0.4), 7, 5, Color.WHITE, 0.3, 2.0, i)
		mb.ellipsoid(m("ore"), MeshBuilder.at(Vector3(0, 0.5, 0)), Vector3(0.55, 0.45, 0.5), 8, 5, Color.WHITE, 0.3, 2.0, 11)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


# =============================================================================== Dungeon-Requisiten
static func stairs(p: Dictionary) -> Node3D:
	var mb := MeshBuilder.new()
	for i in 8:
		mb.box(m("stone_dark"), MeshBuilder.at(Vector3(0, 0.12 + i * 0.25, 0.4 + i * 0.5)), Vector3(4.0, 0.25, 0.5))
	var n := Node3D.new()
	n.add_child(_mi(mb.commit()))
	return n


static func pillar(p: Dictionary) -> Node3D:
	var big: bool = p.get("big", false)
	var mesh := _cached("pillar|%s" % big, func():
		var mb := MeshBuilder.new()
		var r := 1.2 if big else 0.75
		var st := Mat.stylized(Color.html("#7a7670"), Mat.P.STONE, {"c2": Color.html("#3a3631")})
		mb.box(st, MeshBuilder.at(Vector3(0, 0.3, 0)), Vector3(r * 2.4, 0.6, r * 2.4))
		mb.cylinder(st, MeshBuilder.at(Vector3(0, 0.6, 0)), r, r * 0.92, 7.0, 12)
		mb.box(st, MeshBuilder.at(Vector3(0, 7.8, 0)), Vector3(r * 2.4, 0.8, r * 2.4))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func sarcophagus(p: Dictionary) -> Node3D:
	var mesh := _cached("sarcophagus", func():
		var mb := MeshBuilder.new()
		var st := Mat.stylized(Color.html("#8a867c"), Mat.P.STONE, {"c2": Color.html("#3e3a34"), "scale": 1.5})
		mb.box(st, MeshBuilder.at(Vector3(0, 0.45, 0)), Vector3(1.2, 0.9, 2.4))
		mb.box(st, MeshBuilder.at(Vector3(0, 0.98, 0)), Vector3(1.35, 0.16, 2.55))
		mb.ellipsoid(st, MeshBuilder.at(Vector3(0, 1.12, -0.85)), Vector3(0.22, 0.14, 0.24), 8, 5)
		mb.box(st, MeshBuilder.at(Vector3(0, 1.14, 0.1)), Vector3(0.5, 0.12, 1.4))
		mb.box(m("iron"), MeshBuilder.at(Vector3(0, 1.22, 0.2)), Vector3(0.08, 0.06, 1.0))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func bones(p: Dictionary, pile: bool) -> Node3D:
	var mesh := _cached("bones|%s" % pile, func():
		var mb := MeshBuilder.new()
		var rng := RandomNumberGenerator.new()
		rng.seed = 13 if pile else 7
		var n := 18 if pile else 6
		for i in n:
			var a := rng.randf() * TAU
			var d := rng.randf_range(0.0, 1.0 if pile else 0.8)
			var c := Vector3(cos(a) * d, rng.randf_range(0.05, 0.6 if pile else 0.1), sin(a) * d)
			var dir := Vector3(rng.randf_range(-1, 1), rng.randf_range(-0.2, 0.2), rng.randf_range(-1, 1)).normalized()
			mb.beam(m("bone"), c - dir * 0.3, c + dir * 0.3, Vector2(0.06, 0.06))
			mb.ellipsoid(m("bone"), MeshBuilder.at(c - dir * 0.32), Vector3(0.06, 0.06, 0.06), 5, 3)
			mb.ellipsoid(m("bone"), MeshBuilder.at(c + dir * 0.32), Vector3(0.06, 0.06, 0.06), 5, 3)
		for i in (3 if pile else 1):
			var c := Vector3(rng.randf_range(-0.4, 0.4), 0.15 + (0.5 if pile else 0.0), rng.randf_range(-0.4, 0.4))
			mb.ellipsoid(m("bone"), MeshBuilder.at(c, rng.randf() * TAU), Vector3(0.14, 0.15, 0.17), 8, 6)
			mb.box(m("dark"), MeshBuilder.at(c + Vector3(-0.05, 0.02, -0.15)), Vector3(0.05, 0.05, 0.02))
			mb.box(m("dark"), MeshBuilder.at(c + Vector3(0.05, 0.02, -0.15)), Vector3(0.05, 0.05, 0.02))
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	return root


static func altar(p: Dictionary) -> Node3D:
	var mesh := _cached("altar", func():
		var mb := MeshBuilder.new()
		var st := Mat.stylized(Color.html("#4a4650"), Mat.P.STONE, {"c2": Color.html("#1e1c22")})
		mb.box(st, MeshBuilder.at(Vector3(0, 0.25, 0)), Vector3(3.6, 0.5, 2.4))
		mb.box(st, MeshBuilder.at(Vector3(0, 0.9, 0)), Vector3(2.4, 0.9, 1.2))
		mb.box(Mat.stylized(Color.html("#5a1a6a"), Mat.P.CLOTH), MeshBuilder.at(Vector3(0, 1.37, 0)), Vector3(2.5, 0.04, 1.3))
		mb.ellipsoid(Mat.emissive(Color.html("#b070ff"), 2.0), MeshBuilder.at(Vector3(0, 1.7, 0)), Vector3(0.25, 0.25, 0.25), 10, 8)
		return mb.commit())
	var root := Node3D.new()
	root.add_child(_mi(mesh))
	var l := FxLib.light(Color.html("#b070ff"), 1.6, 7.0)
	l.position.y = 2.0
	root.add_child(l)
	root.add_child(FxLib.sparkles(Color.html("#c090ff"), 0.8, 12))
	return root


static func candles(p: Dictionary) -> Node3D:
	var root := Node3D.new()
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = int(float(p.get("x", 0.0)) * 7 + float(p.get("z", 0.0)))
	var flame := Mat.emissive(Color.html("#ffb840"), 4.0)
	for i in 6:
		var a := rng.randf() * TAU
		var d := rng.randf_range(0.0, 0.5)
		var h := rng.randf_range(0.2, 0.6)
		var c := Vector3(cos(a) * d, 0, sin(a) * d)
		mb.cylinder(m("candle"), MeshBuilder.at(c), 0.05, 0.05, h, 8)
		mb.ellipsoid(flame, MeshBuilder.at(c + Vector3(0, h + 0.05, 0)), Vector3(0.025, 0.05, 0.025), 5, 4)
	root.add_child(_mi(mb.commit(), false))
	var anim := AnimNode3D.new()
	anim.mode = "flicker"
	var l := FxLib.light(Color.html("#ffb050"), 1.2, 6.0)
	l.position.y = 0.8
	anim.add_child(l)
	root.add_child(anim)
	return root
