class_name ObjectModels
extends RefCounted
## Modelle für Weltobjekte: Erzadern, Kräuter, Truhen, Teleportationssteine, Briefkästen, Anschlagbretter,
## Schmieden, Alchemietische, Fallen und Bodeneffekte.

static var _cache: Dictionary = {}

const ORE_COLORS := {
	"ore_copper": ["#c87a3a", "#5a3a1a"], "ore_iron": ["#9aa0aa", "#4a4a52"], "ore_mithril": ["#a8d8ff", "#3a5a7a"],
	"ore_glut": ["#ff6a2a", "#4a1a0a"], "ore_star": ["#e0e8ff", "#5a5aa0"],
}
const HERB_COLORS := {
	"herb_peace": ["#f8f0a0", "#4a8a2a"], "herb_silver": ["#d8e8f0", "#5a8a6a"], "herb_frost": ["#a8e0ff", "#3a6a7a"],
	"herb_moon": ["#c0a0ff", "#3a3a6a"], "herb_mushroom": ["#80ffd0", "#2a5a4a"], "herb_fire": ["#ff6a2a", "#6a3a1a"],
	"herb_ashshroom": ["#ffa040", "#3a2a2a"], "herb_sky": ["#ffe8a0", "#6a8ac0"],
}


static func make(info: Dictionary) -> Node3D:
	var obj := str(info.get("obj", ""))
	var model := str(info.get("model", obj))
	var sub := str(info.get("sub", ""))
	var root := Node3D.new()
	var mi := MeshInstance3D.new()
	var key := model + "|" + sub
	if _cache.has(key):
		mi.mesh = _cache[key]
	else:
		var mesh := _build(model, obj, sub)
		_cache[key] = mesh
		mi.mesh = mesh
	root.add_child(mi)
	# Leuchteffekte
	if model.begins_with("ore_") and model in ["ore_mithril", "ore_glut", "ore_star"]:
		var c := Color.html(ORE_COLORS[model][0])
		root.add_child(FxLib.sparkles(c, 0.9, 6))
	elif model.begins_with("herb_"):
		var c := Color.html(HERB_COLORS.get(model, ["#ffffff"])[0])
		var s := FxLib.sparkles(c, 0.5, 4)
		s.position.y = 0.4
		root.add_child(s)
	elif obj == "stone":
		var l := FxLib.light(Color("#7ab0ff"), 1.4, 7.0)
		l.position.y = 2.0
		root.add_child(l)
		var sp := FxLib.sparkles(Color("#9ad0ff"), 1.0, 10)
		sp.position.y = 1.5
		root.add_child(sp)
	elif obj == "forge":
		var f := FxLib.fire(0.6)
		f.position = Vector3(0, 0.9, 0)
		root.add_child(f)
	elif obj == "chest" and info.get("look", {}).get("glow", true):
		var sp2 := FxLib.sparkles(Color("#ffd870"), 0.6, 6)
		sp2.position.y = 0.6
		root.add_child(sp2)
	return root


static func _build(model: String, obj: String, sub: String) -> ArrayMesh:
	var mb := MeshBuilder.new()
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(model + sub)
	if model.begins_with("ore_"):
		var cols: Array = ORE_COLORS.get(model, ["#aaaaaa", "#444444"])
		var rock := Mat.stylized(Color.html("#7a7268"), Mat.P.ROCK, {"c2": Color.html("#3a3630"), "tri": true})
		var ore := Mat.stylized(Color.html(cols[0]), Mat.P.METAL, {"c2": Color.html(cols[1]), "emis": Color.html(cols[0]) * (0.25 if model in ["ore_glut", "ore_star", "ore_mithril"] else 0.0)})
		for i in 4:
			var a := rng.randf() * TAU
			var d := rng.randf_range(0.0, 0.5)
			var s := rng.randf_range(0.45, 0.8)
			mb.ellipsoid(rock, MeshBuilder.at_euler(Vector3(cos(a) * d, s * 0.35, sin(a) * d), Vector3(rng.randf(), rng.randf() * 3, rng.randf())),
				Vector3(s, s * 0.7, s * 0.85), 9, 6, Color.WHITE, 0.25, 3.0, rng.randi() % 100)
		for i in 7:
			var a := rng.randf() * TAU
			var d := rng.randf_range(0.2, 0.6)
			mb.cylinder(ore, MeshBuilder.at_euler(Vector3(cos(a) * d, rng.randf_range(0.3, 0.6), sin(a) * d),
				Vector3(rng.randf_range(-0.6, 0.6), rng.randf() * 3, rng.randf_range(-0.6, 0.6))), 0.09, 0.0, rng.randf_range(0.25, 0.45), 5)
	elif model.begins_with("herb_") or (obj == "quest" and sub == "herb"):
		var cols: Array = HERB_COLORS.get(model, ["#f8f0a0", "#4a8a2a"])
		var stem := Mat.foliage(Color.html(cols[1]), Color.html(cols[1]).darkened(0.5), Color.html(cols[1]).lightened(0.3))
		var petal := Mat.stylized(Color.html(cols[0]), Mat.P.PLAIN, {"emis": Color.html(cols[0]) * 0.15, "c2": Color.html(cols[0]).darkened(0.3)})
		if model in ["herb_mushroom", "herb_ashshroom"]:
			var cap := Mat.stylized(Color.html(cols[0]), Mat.P.PLAIN, {"emis": Color.html(cols[0]) * 0.4})
			var st := Mat.stylized(Color.html("#e8e0d0"), Mat.P.PLAIN)
			for i in 3:
				var p := Vector3(rng.randf_range(-0.25, 0.25), 0, rng.randf_range(-0.25, 0.25))
				var h := rng.randf_range(0.2, 0.42)
				mb.cylinder(st, MeshBuilder.at(p), 0.05, 0.04, h, 7)
				mb.ellipsoid(cap, MeshBuilder.at(p + Vector3(0, h, 0)), Vector3(0.16, 0.08, 0.16), 10, 5)
		else:
			for i in 7:
				var a := TAU * i / 7.0 + rng.randf() * 0.3
				var len := rng.randf_range(0.3, 0.55)
				mb.beam(stem, Vector3(0, 0, 0), Vector3(cos(a) * 0.15, len, sin(a) * 0.15), Vector2(0.06, 0.012))
				if i % 2 == 0:
					mb.ellipsoid(petal, MeshBuilder.at(Vector3(cos(a) * 0.16, len, sin(a) * 0.16)), Vector3(0.07, 0.05, 0.07), 7, 5)
	elif obj == "quest" and sub == "chicken":
		var gold := Mat.stylized(Color.html("#ffd040"), Mat.P.GOLD, {"emis": Color.html("#ffc020") * 0.2})
		mb.ellipsoid(gold, MeshBuilder.at(Vector3(0, 0.25, 0)), Vector3(0.18, 0.16, 0.24), 12, 8)
		mb.ellipsoid(gold, MeshBuilder.at(Vector3(0, 0.42, -0.16)), Vector3(0.09, 0.09, 0.09), 10, 7)
	elif obj == "chest":
		var wood := Mat.stylized(Color.html("#7a4a26"), Mat.P.WOOD, {"c2": Color.html("#3a2010")})
		var metal := Mat.stylized(Color.html("#d8b060"), Mat.P.GOLD, {"c2": Color.html("#6a4a1a")})
		mb.box(wood, MeshBuilder.at(Vector3(0, 0.3, 0)), Vector3(1.1, 0.6, 0.7))
		mb.cylinder(wood, MeshBuilder.at_euler(Vector3(-0.55, 0.6, 0), Vector3(0, 0, -PI * 0.5)), 0.35, 0.35, 1.1, 12, false)
		for x in [-0.4, 0.0, 0.4]:
			mb.box(metal, MeshBuilder.at(Vector3(x, 0.45, 0)), Vector3(0.08, 0.92, 0.74))
		mb.box(metal, MeshBuilder.at(Vector3(0, 0.55, -0.37)), Vector3(0.18, 0.2, 0.05))
	elif obj == "stone":
		var st := Mat.stylized(Color.html("#7a7a86"), Mat.P.STONE, {"c2": Color.html("#3a3a46"), "tri": true})
		var rune := Mat.emissive(Color.html("#7ab8ff"), 3.0)
		var outline := PackedVector2Array([Vector2(-0.55, 0), Vector2(0.55, 0), Vector2(0.45, 2.4), Vector2(0, 2.9), Vector2(-0.45, 2.4)])
		mb.extrude(st, MeshBuilder.at(Vector3(0, 0, 0.2)), outline, 0.4)
		mb.cylinder(st, MeshBuilder.at(Vector3(0, -0.05, 0)), 1.1, 1.0, 0.2, 14)
		for i in 4:
			mb.box(rune, MeshBuilder.at(Vector3(0, 0.6 + i * 0.45, -0.21)), Vector3(0.22 - i * 0.03, 0.06, 0.01))
			mb.box(rune, MeshBuilder.at(Vector3(0, 0.6 + i * 0.45, 0.21)), Vector3(0.22 - i * 0.03, 0.06, 0.01))
	elif obj == "mailbox":
		var wood := Mat.stylized(Color.html("#5a3a22"), Mat.P.WOOD)
		var box := Mat.stylized(Color.html("#2d4f9a"), Mat.P.METAL, {"c2": Color.html("#1a2a4a")})
		var gold := Mat.stylized(Color.html("#e0b648"), Mat.P.GOLD)
		mb.box(wood, MeshBuilder.at(Vector3(0, 0.6, 0)), Vector3(0.14, 1.2, 0.14))
		mb.box(box, MeshBuilder.at(Vector3(0, 1.35, 0)), Vector3(0.5, 0.4, 0.7))
		mb.cylinder(box, MeshBuilder.at_euler(Vector3(-0.25, 1.55, 0), Vector3(0, 0, -PI * 0.5)), 0.25, 0.25, 0.5, 12, false)
		mb.box(gold, MeshBuilder.at(Vector3(0.26, 1.4, 0)), Vector3(0.02, 0.1, 0.4))
	elif obj == "board":
		var wood := Mat.stylized(Color.html("#6a4422"), Mat.P.WOOD, {"c2": Color.html("#3a2412")})
		var paper := Mat.stylized(Color.html("#e8d8b0"), Mat.P.PLAIN)
		for x in [-0.9, 0.9]:
			mb.box(wood, MeshBuilder.at(Vector3(x, 1.0, 0)), Vector3(0.14, 2.0, 0.14))
		mb.box(wood, MeshBuilder.at(Vector3(0, 1.4, 0)), Vector3(1.9, 1.0, 0.08))
		mb.gable_roof(wood, MeshBuilder.at(Vector3(0, 2.0, 0)), 2.2, 0.5, 0.35)
		for i in 4:
			mb.box(paper, MeshBuilder.at_euler(Vector3(-0.6 + i * 0.4, 1.4 + (i % 2) * 0.12, -0.05), Vector3(0, 0, rng.randf_range(-0.1, 0.1))), Vector3(0.3, 0.4, 0.01))
	elif obj == "forge":
		var stone := Mat.stylized(Color.html("#6a625a"), Mat.P.STONE, {"tri": true})
		var coal := Mat.emissive(Color.html("#ff5a10"), 2.5)
		mb.cylinder(stone, MeshBuilder.at(Vector3(0, 0, 0)), 0.9, 0.8, 0.8, 12)
		mb.disc(coal, MeshBuilder.at(Vector3(0, 0.81, 0)), 0.65, 12)
	elif obj == "alchemy":
		var wood := Mat.stylized(Color.html("#6a4422"), Mat.P.WOOD)
		var glass := Mat.stylized(Color.html("#60d0a0"), Mat.P.ICE, {"emis": Color.html("#40ffa0") * 0.3})
		var glass2 := Mat.stylized(Color.html("#d060c0"), Mat.P.ICE, {"emis": Color.html("#ff60e0") * 0.3})
		mb.box(wood, MeshBuilder.at(Vector3(0, 0.85, 0)), Vector3(1.6, 0.1, 0.8))
		for x in [-0.7, 0.7]:
			for z in [-0.3, 0.3]:
				mb.box(wood, MeshBuilder.at(Vector3(x, 0.42, z)), Vector3(0.08, 0.84, 0.08))
		mb.ellipsoid(glass, MeshBuilder.at(Vector3(-0.4, 1.05, 0)), Vector3(0.14, 0.14, 0.14), 10, 8)
		mb.cylinder(glass, MeshBuilder.at(Vector3(-0.4, 1.15, 0)), 0.04, 0.04, 0.2, 6)
		mb.cylinder(glass2, MeshBuilder.at(Vector3(0.2, 0.9, 0.1)), 0.08, 0.06, 0.3, 8)
		mb.cylinder(glass, MeshBuilder.at(Vector3(0.5, 0.9, -0.15)), 0.06, 0.06, 0.22, 8)
	elif model.begins_with("trap_"):
		var metal := Mat.stylized(Color.html("#8a8e96"), Mat.P.METAL)
		var c = {"trap_frost": "#8ad8ff", "trap_fire": "#ff7a20", "trap_nature": "#7ad04a"}.get(model, "#8ad8ff")
		var glow := Mat.emissive(Color.html(c), 2.0)
		mb.torus(metal, MeshBuilder.at(Vector3(0, 0.05, 0)), 0.45, 0.05, 16, 6)
		for i in 8:
			var a := TAU * i / 8.0
			mb.cylinder(metal, MeshBuilder.at_euler(Vector3(cos(a) * 0.45, 0.1, sin(a) * 0.45), Vector3(0, 0, 0)), 0.03, 0.0, 0.2, 4)
		mb.disc(glow, MeshBuilder.at(Vector3(0, 0.03, 0)), 0.3, 12)
	else:
		var st := Mat.stylized(Color.html("#8a8070"), Mat.P.STONE)
		mb.box(st, MeshBuilder.at(Vector3(0, 0.3, 0)), Vector3(0.6, 0.6, 0.6))
	return mb.commit()


## Bodeneffekt (Feuer, Lava, Gift, Schattenfeuer, Seuchenwolke): Scheibe + Partikel
static func ground_effect(fx: String, radius: float) -> Node3D:
	var root := Node3D.new()
	var col = {"fire": Color("#ff6a1a"), "lava": Color("#ff4a0a"), "poison": Color("#7ad04a"), "shadowfire": Color("#9a5ad0"),
		"plague": Color("#9ad04a"), "frost": Color("#8ad8ff"), "holy": Color("#ffe080")}.get(fx, Color("#ff6a1a"))
	var mi := MeshInstance3D.new()
	var mesh := PlaneMesh.new()
	mesh.size = Vector2(radius * 2.0, radius * 2.0)
	mi.mesh = mesh
	var mat := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = """shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled;
uniform vec4 col : source_color;
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f*f*(3.0-2.0*f);
 return mix(mix(hash(i), hash(i+vec2(1,0)), f.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y); }
void fragment(){
 vec2 uv = UV * 2.0 - 1.0; float r = length(uv);
 float n = noise(uv * 5.0 + vec2(TIME * 0.6, -TIME * 0.4)) * 0.6 + noise(uv * 11.0 - TIME) * 0.4;
 float edge = smoothstep(1.0, 0.85, r) * (0.35 + 0.65 * smoothstep(0.6, 1.0, r));
 float a = smoothstep(1.0, 0.92, r) * (0.25 + n * 0.75) * 0.9 + edge * 0.6;
 ALBEDO = col.rgb * (0.8 + n); ALPHA = clamp(a, 0.0, 1.0);
}"""
	mat.shader = sh
	mat.set_shader_parameter("col", col)
	mi.material_override = mat
	mi.position.y = 0.06
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)
	if fx in ["fire", "lava", "shadowfire"]:
		for i in int(clampf(radius * 0.8, 1, 5)):
			var f := FxLib.fire(0.5 if fx != "lava" else 0.7, col, i == 0)
			var a := randf() * TAU
			f.position = Vector3(cos(a), 0, sin(a)) * randf() * radius * 0.7
			root.add_child(f)
	else:
		var sp := FxLib.sparkles(col, radius * 0.8, int(radius * 4))
		sp.position.y = 0.5
		root.add_child(sp)
	return root
