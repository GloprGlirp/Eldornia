class_name FxLib
extends RefCounted
## Partikel- und Leuchteffekte (Feuer, Rauch, Funken, magisches Glühen).

static var _soft: GradientTexture2D
static var _mats: Dictionary = {}


static func soft_tex() -> GradientTexture2D:
	if _soft == null:
		var g := Gradient.new()
		g.set_color(0, Color(1, 1, 1, 1))
		g.set_color(1, Color(1, 1, 1, 0))
		g.add_point(0.35, Color(1, 1, 1, 0.7))
		_soft = GradientTexture2D.new()
		_soft.gradient = g
		_soft.fill = GradientTexture2D.FILL_RADIAL
		_soft.fill_from = Vector2(0.5, 0.5)
		_soft.fill_to = Vector2(1.0, 0.5)
		_soft.width = 64
		_soft.height = 64
	return _soft


static func sprite_mat(additive := true) -> StandardMaterial3D:
	var key := "add" if additive else "mix"
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if additive else BaseMaterial3D.BLEND_MODE_MIX
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.albedo_texture = soft_tex()
	m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	_mats[key] = m
	return m


static func _ramp(c0: Color, c1: Color, c2: Color) -> GradientTexture1D:
	var g := Gradient.new()
	g.set_color(0, c0)
	g.set_color(1, c2)
	g.add_point(0.4, c1)
	var t := GradientTexture1D.new()
	t.gradient = g
	return t


static func particles(amount: int, lifetime: float, size: float, color_ramp: GradientTexture1D,
		velocity := Vector3(0, 1.5, 0), spread := 15.0, emit_radius := 0.2, gravity := Vector3.ZERO,
		additive := true, scale_curve_up := false) -> GPUParticles3D:
	var p := GPUParticles3D.new()
	p.amount = amount
	p.lifetime = lifetime
	p.preprocess = lifetime
	p.local_coords = false
	var pm := ParticleProcessMaterial.new()
	pm.direction = velocity.normalized() if velocity.length() > 0.001 else Vector3.UP
	pm.spread = spread
	pm.initial_velocity_min = velocity.length() * 0.6
	pm.initial_velocity_max = velocity.length() * 1.2
	pm.gravity = gravity
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	pm.emission_sphere_radius = emit_radius
	pm.scale_min = size * 0.6
	pm.scale_max = size * 1.1
	pm.color_ramp = color_ramp
	var curve := CurveTexture.new()
	var c := Curve.new()
	if scale_curve_up:
		c.add_point(Vector2(0, 0.4))
		c.add_point(Vector2(1, 1.0))
	else:
		c.add_point(Vector2(0, 1.0))
		c.add_point(Vector2(1, 0.2))
	curve.curve = c
	pm.scale_curve = curve
	p.process_material = pm
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	q.material = sprite_mat(additive)
	p.draw_pass_1 = q
	p.visibility_aabb = AABB(Vector3(-4, -1, -4), Vector3(8, 10, 8))
	return p


static func fire(size := 1.0, color := Color(1.0, 0.55, 0.15), light := true) -> Node3D:
	var root := Node3D.new()
	root.name = "Fire"
	var flames := particles(int(18 * size) + 6, 0.8, 0.55 * size,
		_ramp(Color(color.r, color.g * 1.2, color.b, 0.0), Color(color.r, color.g, color.b, 0.9), Color(color.r * 0.6, color.g * 0.2, 0.0, 0.0)),
		Vector3(0, 1.4 * size, 0), 12.0, 0.22 * size)
	root.add_child(flames)
	var core := particles(int(10 * size) + 4, 0.5, 0.35 * size,
		_ramp(Color(1, 0.95, 0.7, 0.0), Color(1, 0.9, 0.6, 1.0), Color(1, 0.6, 0.2, 0.0)),
		Vector3(0, 1.0 * size, 0), 8.0, 0.12 * size)
	root.add_child(core)
	var embers := particles(int(8 * size) + 2, 1.8, 0.06 * size,
		_ramp(Color(1, 0.7, 0.3, 1.0), Color(1, 0.5, 0.1, 1.0), Color(1, 0.3, 0.0, 0.0)),
		Vector3(0, 2.2 * size, 0), 25.0, 0.3 * size)
	root.add_child(embers)
	var smoke := particles(int(6 * size) + 2, 3.0, 0.9 * size,
		_ramp(Color(0.2, 0.2, 0.2, 0.0), Color(0.25, 0.24, 0.24, 0.25), Color(0.3, 0.3, 0.3, 0.0)),
		Vector3(0, 1.2 * size, 0), 10.0, 0.2 * size, Vector3(0.2, 0.0, 0.1), false, true)
	smoke.position.y = 0.8 * size
	root.add_child(smoke)
	if light:
		var anim := AnimNode3D.new()
		anim.mode = "flicker"
		var l := OmniLight3D.new()
		l.light_color = color.lightened(0.2)
		l.light_energy = 2.2 * size
		l.omni_range = 9.0 * size
		l.omni_attenuation = 1.4
		l.position.y = 0.6 * size
		l.shadow_enabled = false
		anim.add_child(l)
		root.add_child(anim)
	return root


static func glow_sprite(color: Color, size := 1.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(size, size)
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	m.albedo_texture = soft_tex()
	m.albedo_color = color
	m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	q.material = m
	mi.mesh = q
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi


static func sparkles(color: Color, radius := 1.0, amount := 16) -> GPUParticles3D:
	return particles(amount, 1.6, 0.12, _ramp(Color(color, 0.0), Color(color, 1.0), Color(color, 0.0)),
		Vector3(0, 0.5, 0), 180.0, radius)


static func light(color: Color, energy := 1.5, rng := 8.0) -> OmniLight3D:
	var l := OmniLight3D.new()
	l.light_color = color
	l.light_energy = energy
	l.omni_range = rng
	l.shadow_enabled = false
	return l
