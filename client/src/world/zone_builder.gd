class_name ZoneBuilder
extends RefCounted
## Baut eine komplette Zone (Licht, Himmel, Gelände, Wasser, Vegetation, Gebäude) aus den
## Zonendaten des Servers.

var zone: Dictionary
var theme_id := "gruen"
var theme: Dictionary
var hf: Heightfield
var terrain: TerrainBuilder
var root: Node3D
var env: Environment
var sun: DirectionalLight3D
var sky_mat: ShaderMaterial
var grass: GrassField
var dungeon: DungeonBuilder


func build(p_root: Node3D, p_zone: Dictionary) -> void:
	root = p_root
	zone = p_zone
	theme_id = str(zone.get("theme", "dungeon" if zone.get("type") == "dungeon" else "gruen"))
	theme = Themes.get_theme(theme_id)
	_build_environment()
	if zone.has("heights"):
		hf = Heightfield.new()
		hf.load_from(zone)
		var tnode := Node3D.new()
		tnode.name = "Terrain"
		root.add_child(tnode)
		terrain = TerrainBuilder.new(hf, zone, theme)
		terrain.build(tnode)
		_build_water()
		var veg := Node3D.new()
		veg.name = "Vegetation"
		root.add_child(veg)
		Vegetation.populate(veg, zone.get("props", []), hf, theme_id)
		var props := Node3D.new()
		props.name = "Props"
		root.add_child(props)
		PropFactory.populate(props, zone.get("props", []), hf, theme_id)
		grass = GrassField.new()
		grass.name = "Grass"
		grass.setup(hf, terrain, theme)
		root.add_child(grass)
		if zone.has("void"):
			_build_sky_islands_underside()
	elif zone.has("rects"):
		dungeon = DungeonBuilder.new()
		dungeon.build(root, zone, theme)


func _build_environment() -> void:
	var we := WorldEnvironment.new()
	we.name = "WorldEnvironment"
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky.gdshader")
	var s: Dictionary = theme.get("sky", {})
	sky_mat.set_shader_parameter("top_color", Color.html(s.get("top", "#3f7fd0")))
	sky_mat.set_shader_parameter("horizon_color", Color.html(s.get("horizon", "#cfe3ef")))
	sky_mat.set_shader_parameter("ground_color", Color.html(s.get("ground", "#6f8070")))
	sky_mat.set_shader_parameter("sun_color", Color.html(s.get("sun", "#fff0d0")))
	sky_mat.set_shader_parameter("cloud_light", Color.html(s.get("cloud_light", "#ffffff")))
	sky_mat.set_shader_parameter("cloud_dark", Color.html(s.get("cloud_dark", "#9fb0c8")))
	sky_mat.set_shader_parameter("cloud_cover", float(s.get("cover", 0.5)))
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_128
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.html(theme.get("ambient", "#a9bccc"))
	env.ambient_light_energy = float(theme.get("ambient_energy", 0.55))
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.tonemap_exposure = 1.0
	env.tonemap_white = 6.0
	env.glow_enabled = true
	env.glow_intensity = float(theme.get("glow", 0.3))
	env.glow_strength = 0.9
	env.glow_bloom = 0.06
	env.glow_hdr_threshold = 1.1
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SOFTLIGHT
	env.ssao_enabled = true
	env.ssao_radius = 1.4
	env.ssao_intensity = 1.6
	env.ssao_power = 1.4
	env.fog_enabled = true
	env.fog_light_color = Color.html(theme.get("fog", "#bcd3e2"))
	env.fog_density = float(theme.get("fog_density", 0.003))
	env.fog_sky_affect = 0.25
	env.fog_aerial_perspective = 0.35
	env.fog_height = -20.0
	env.fog_height_density = 0.0
	env.adjustment_enabled = true
	env.adjustment_saturation = 1.12
	env.adjustment_contrast = 1.05
	if zone.get("type") == "dungeon":
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color.html(theme.get("fog", "#0a0b10"))
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.fog_density = float(theme.get("fog_density", 0.02))
		env.glow_intensity = 0.6
	we.environment = env
	root.add_child(we)
	sun = DirectionalLight3D.new()
	sun.name = "Sun"
	sun.light_color = Color.html(theme.get("sun_color", "#fff1d6"))
	sun.light_energy = float(theme.get("sun_energy", 1.3))
	sun.rotation_degrees = Vector3(float(theme.get("sun_pitch", -48.0)), float(theme.get("sun_yaw", 35.0)), 0)
	sun.shadow_enabled = true
	sun.shadow_bias = 0.04
	sun.shadow_normal_bias = 1.2
	sun.shadow_blur = 1.5
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 140.0
	sun.directional_shadow_split_1 = 0.06
	sun.directional_shadow_split_2 = 0.18
	sun.directional_shadow_split_3 = 0.45
	sun.light_angular_distance = 0.8
	root.add_child(sun)


func _build_water() -> void:
	var water: Array = zone.get("water", [])
	if water.is_empty():
		return
	var cols: Array = theme.get("water", ["#3aa6b0", "#0e3f5e"])
	var lava: bool = theme.get("lava", false)
	for w in water:
		var mb := MeshBuilder.new()
		var is_lava: bool = w.get("lava", lava)
		var mat := Mat.water(Color.html(cols[0]), Color.html(cols[1]), is_lava)
		var r := float(w.get("r", 20.0)) + 3.0
		# fein unterteilte Scheibe für die Wellen
		var rings := 10
		var seg := 48
		var c := Vector3(float(w["x"]), float(w.get("level", -0.8)), float(w["z"]))
		for ri in rings:
			var r0 := r * ri / rings
			var r1 := r * (ri + 1) / rings
			for i in seg:
				var a0 := TAU * i / seg
				var a1 := TAU * (i + 1) / seg
				var p00 := c + Vector3(cos(a0) * r0, 0, sin(a0) * r0)
				var p01 := c + Vector3(cos(a1) * r0, 0, sin(a1) * r0)
				var p10 := c + Vector3(cos(a0) * r1, 0, sin(a0) * r1)
				var p11 := c + Vector3(cos(a1) * r1, 0, sin(a1) * r1)
				if ri > 0:
					mb.tri(mat, p00, p10, p11, Vector3.UP, Vector3.UP, Vector3.UP)
				mb.tri(mat, p00, p11, p01, Vector3.UP, Vector3.UP, Vector3.UP)
		var mi := MeshInstance3D.new()
		mi.mesh = mb.commit()
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.name = "Water"
		root.add_child(mi)
		if is_lava:
			var l := FxLib.light(Color.html("#ff6a20"), 2.0, r * 1.2)
			l.position = c + Vector3(0, 3.0, 0)
			root.add_child(l)


## Unterseiten der schwebenden Inseln (Himmelsbruch)
func _build_sky_islands_underside() -> void:
	var islands: Array = zone.get("islands", [])
	var rock := Mat.stylized(Color.html("#9a8a78"), Mat.P.ROCK, {"c2": Color.html("#5a4a3a"), "tri": true, "scale": 0.3})
	var crystal := Mat.stylized(Color.html("#80e8ff"), Mat.P.ICE, {"emis": Color.html("#40a0d0")})
	for isl in islands:
		var mb := MeshBuilder.new()
		var r := float(isl["r"])
		var c := Vector3(float(isl["x"]), float(isl.get("h", 0.0)) - 1.0, float(isl["z"]))
		mb.cylinder(rock, MeshBuilder.at(c + Vector3(0, -r * 0.9, 0)), r * 0.15, r * 1.02, r * 0.9, 18, false)
		var rng := RandomNumberGenerator.new()
		rng.seed = int(c.x * 13 + c.z)
		for i in 7:
			var a := rng.randf() * TAU
			var d := rng.randf_range(0.2, 0.75) * r
			var len := rng.randf_range(0.4, 1.0) * r
			mb.cylinder(rock, MeshBuilder.at(c + Vector3(cos(a) * d, -r * 0.5 - len, sin(a) * d)), 0.0, r * 0.18, len, 7)
		for i in 4:
			var a := rng.randf() * TAU
			var d := rng.randf_range(0.3, 0.8) * r
			mb.cylinder(crystal, MeshBuilder.at_euler(c + Vector3(cos(a) * d, -r * 0.4, sin(a) * d), Vector3(PI, 0, rng.randf_range(-0.4, 0.4))), r * 0.06, 0.0, r * 0.35, 6)
		var mi := MeshInstance3D.new()
		mi.mesh = mb.commit()
		root.add_child(mi)


func height(x: float, z: float) -> float:
	if hf:
		return hf.height(x, z)
	return 0.0
