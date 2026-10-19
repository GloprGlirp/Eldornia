class_name Mat
extends RefCounted
## Materialfabrik mit Cache. Alle prozeduralen Modelle teilen sich wenige Shader.

enum P { PLAIN, WOOD, PLASTER, STONE, ROOF, METAL, CLOTH, LEATHER, BARK, ROCK, SKIN, FUR, CHAIN, THATCH, FLAGSTONE, ICE, BONE, LAVA, GOLD, SCALES }

static var _cache: Dictionary = {}
static var _stylized: Shader
static var _foliage: Shader
static var _water: Shader
static var _grass: Shader


static func _shader(path: String) -> Shader:
	return load(path) as Shader


static func stylized(color: Color, pattern: int = P.PLAIN, opts: Dictionary = {}) -> ShaderMaterial:
	var key := "s|%s|%d|%s" % [color.to_html(), pattern, str(opts)]
	if _cache.has(key):
		return _cache[key]
	if _stylized == null:
		_stylized = _shader("res://shaders/stylized.gdshader")
	var m := ShaderMaterial.new()
	m.shader = _stylized
	m.set_shader_parameter("albedo", color)
	var c2: Color = opts.get("c2", color.darkened(0.45))
	m.set_shader_parameter("albedo2", c2)
	m.set_shader_parameter("pattern", pattern)
	m.set_shader_parameter("pattern_scale", opts.get("scale", 1.0))
	m.set_shader_parameter("triplanar", opts.get("tri", false))
	m.set_shader_parameter("use_vertex_color", opts.get("vcol", false))
	var rough := 0.85
	var metal := 0.0
	match pattern:
		P.METAL, P.GOLD:
			rough = 0.42
			metal = 0.7
		P.CHAIN:
			rough = 0.5
			metal = 0.6
		P.ICE:
			rough = 0.1
		P.SKIN:
			rough = 0.6
	m.set_shader_parameter("roughness_value", opts.get("rough", rough))
	m.set_shader_parameter("metallic_value", opts.get("metal", metal))
	m.set_shader_parameter("rim_amount", opts.get("rim", 0.12))
	m.set_shader_parameter("rim_tint_value", opts.get("rim_tint", 0.5))
	var emis: Color = opts.get("emis", Color(0, 0, 0))
	m.set_shader_parameter("emission_color", emis)
	m.set_shader_parameter("emission_energy", opts.get("emis_e", 1.0))
	m.set_shader_parameter("wind_strength", opts.get("wind", 0.0))
	m.set_shader_parameter("edge_wear", opts.get("wear", 0.5))
	m.set_shader_parameter("noise_amount", opts.get("noise", 1.0))
	if opts.get("cull_off", false):
		pass
	_cache[key] = m
	return m


static func foliage(light: Color, dark: Color, tip: Color, cards := false, opts: Dictionary = {}) -> ShaderMaterial:
	var key := "f|%s|%s|%s|%s|%s" % [light.to_html(), dark.to_html(), tip.to_html(), cards, str(opts)]
	if _cache.has(key):
		return _cache[key]
	if _foliage == null:
		_foliage = _shader("res://shaders/foliage.gdshader")
	var m := ShaderMaterial.new()
	m.shader = _foliage
	m.set_shader_parameter("leaf_light", light)
	m.set_shader_parameter("leaf_dark", dark)
	m.set_shader_parameter("leaf_tip", tip)
	m.set_shader_parameter("leaf_cards", cards)
	m.set_shader_parameter("leaf_density", opts.get("density", 6.0))
	m.set_shader_parameter("wind", opts.get("wind", 1.0))
	m.set_shader_parameter("emission_tint", opts.get("emis", Color(0, 0, 0)))
	m.set_shader_parameter("tint_variation", opts.get("var", 0.25))
	_cache[key] = m
	return m


static func emissive(color: Color, energy := 2.0, unshaded := true) -> StandardMaterial3D:
	var key := "e|%s|%f|%s" % [color.to_html(), energy, unshaded]
	if _cache.has(key):
		return _cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.emission_enabled = true
	m.emission = color
	m.emission_energy_multiplier = energy
	if unshaded:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_cache[key] = m
	return m


static func glow_additive(color: Color, energy := 1.5) -> StandardMaterial3D:
	var key := "ga|%s|%f" % [color.to_html(), energy]
	if _cache.has(key):
		return _cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.no_depth_test = false
	m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	m.emission_enabled = true
	m.emission = color
	m.emission_energy_multiplier = energy
	_cache[key] = m
	return m


static func transparent(color: Color, unshaded := true) -> StandardMaterial3D:
	var key := "t|%s|%s" % [color.to_html(), unshaded]
	if _cache.has(key):
		return _cache[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	if unshaded:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_cache[key] = m
	return m


static func water(shallow: Color, deep: Color, lava := false) -> ShaderMaterial:
	var key := "w|%s|%s|%s" % [shallow.to_html(), deep.to_html(), lava]
	if _cache.has(key):
		return _cache[key]
	if _water == null:
		_water = _shader("res://shaders/water.gdshader")
	var m := ShaderMaterial.new()
	m.shader = _water
	m.set_shader_parameter("shallow", shallow)
	m.set_shader_parameter("deep", deep)
	m.set_shader_parameter("is_lava", 1.0 if lava else 0.0)
	_cache[key] = m
	return m


static func grass(a: Color, b: Color, tip: Color) -> ShaderMaterial:
	var key := "g|%s|%s|%s" % [a.to_html(), b.to_html(), tip.to_html()]
	if _cache.has(key):
		return _cache[key]
	if _grass == null:
		_grass = _shader("res://shaders/grass.gdshader")
	var m := ShaderMaterial.new()
	m.shader = _grass
	m.set_shader_parameter("grass_a", a)
	m.set_shader_parameter("grass_b", b)
	m.set_shader_parameter("tip_color", tip)
	_cache[key] = m
	return m


static func col(hex) -> Color:
	if hex is Color:
		return hex
	if hex == null or str(hex) == "":
		return Color.WHITE
	return Color.html(str(hex))
