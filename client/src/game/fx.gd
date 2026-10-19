class_name Fx
extends Node3D
## Zaubereffekte: Geschosse, Einschläge, Flächen, Bodenmarkierungen (Telegraphen), Stufenaufstieg u. v. m.

const SCHOOL := {
	"physical": Color(1.0, 0.92, 0.75), "fire": Color(1.0, 0.45, 0.1), "frost": Color(0.5, 0.82, 1.0),
	"arcane": Color(0.85, 0.5, 1.0), "nature": Color(0.5, 0.95, 0.3), "shadow": Color(0.62, 0.32, 0.95),
	"holy": Color(1.0, 0.9, 0.5), "blood": Color(0.9, 0.15, 0.15),
}

var world  # WorldView
static var _tex: Dictionary = {}
var _projectiles: Array = []
var _timed: Array = []          # [node, until, fade]


func _init(p_world) -> void:
	world = p_world


static func school_color(s: String) -> Color:
	return SCHOOL.get(s, SCHOOL["physical"])


# ============================================================================== Texturen für Decals
static func shape_tex(kind: String, ang := 0.0) -> ImageTexture:
	var key := "%s|%.2f" % [kind, ang]
	if _tex.has(key):
		return _tex[key]
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var u := (x + 0.5) / n * 2.0 - 1.0
			var v := (y + 0.5) / n * 2.0 - 1.0
			var r := sqrt(u * u + v * v)
			var a := 0.0
			match kind:
				"circle":
					a = 1.0 if r <= 1.0 else 0.0
					a *= 0.35 + 0.65 * smoothstep(0.75, 1.0, r)
					a = maxf(a, smoothstep(0.02, 0.0, absf(r - 0.97)) * (1.0 if r < 1.0 else 0.0))
				"disc":
					a = smoothstep(1.0, 0.94, r)
				"ring_sel":
					a = smoothstep(0.08, 0.0, absf(r - 0.88)) * 0.95 + smoothstep(0.2, 0.0, absf(r - 0.88)) * 0.35
				"ring":
					a = smoothstep(0.06, 0.0, absf(r - 0.94))
				"cone":
					var phi := atan2(u, -v)
					var inside: float = 1.0 if (r <= 1.0 and absf(phi) <= ang * 0.5) else 0.0
					a = inside * (0.35 + 0.65 * smoothstep(0.75, 1.0, r))
					if inside > 0.0 and (absf(absf(phi) - ang * 0.5) < 0.04 or r > 0.96):
						a = 1.0
				"line":
					a = 1.0 if (absf(u) <= 1.0 and absf(v) <= 1.0) else 0.0
					a *= 0.35 + 0.65 * smoothstep(0.75, 1.0, absf(u))
				"cursor":
					a = smoothstep(0.06, 0.0, absf(r - 0.92)) + (0.18 if r < 0.92 else 0.0)
			img.set_pixel(x, y, Color(1, 1, 1, clampf(a, 0.0, 1.0)))
	var t := ImageTexture.create_from_image(img)
	_tex[key] = t
	return t


static func decal(kind: String, radius: float, color: Color, ang := 0.0, depth := 8.0) -> Decal:
	var d := Decal.new()
	d.texture_albedo = shape_tex(kind, ang)
	d.size = Vector3(radius * 2.0, depth, radius * 2.0)
	d.modulate = color
	d.albedo_mix = 1.0
	d.emission_energy = 1.0
	d.texture_emission = d.texture_albedo
	d.upper_fade = 0.2
	d.lower_fade = 0.2
	d.cull_mask = 1
	return d


# ============================================================================== Hilfen
func _ground(x: float, z: float) -> float:
	return world.ground_height(x, z)


func _add_timed(n: Node3D, life: float, fade := 0.3) -> void:
	add_child(n)
	_timed.append([n, Game.now() + life, fade, life])


func burst(pos: Vector3, color: Color, amount := 24, size := 0.25, speed := 4.0, life := 0.6) -> void:
	var p := FxLib.particles(amount, life, size, FxLib._ramp(Color(color, 1.0), Color(color.lightened(0.3), 0.8), Color(color, 0.0)),
		Vector3(0, speed * 0.5, 0), 180.0, 0.25)
	p.one_shot = true
	p.explosiveness = 0.95
	p.preprocess = 0.0
	var pm: ParticleProcessMaterial = p.process_material
	pm.initial_velocity_min = speed * 0.5
	pm.initial_velocity_max = speed
	pm.gravity = Vector3(0, -3, 0)
	p.position = pos
	p.emitting = true
	_add_timed(p, life + 0.3, 0.0)
	var l := FxLib.light(color, 2.0, 5.0)
	l.position = pos
	_add_timed(l, 0.25, 0.25)


func flash(pos: Vector3, color: Color, size := 2.0, life := 0.3) -> void:
	var s := FxLib.glow_sprite(Color(color, 0.9), size)
	s.position = pos
	_add_timed(s, life, life)


# ============================================================================== Effekte vom Server
func handle(f: Dictionary) -> void:
	var k := str(f.get("k", ""))
	match k:
		"proj":
			_projectile(f)
		"impact":
			var e = world.ent(int(f.get("id", 0)))
			if e:
				var c := school_color(str(f.get("school", "physical")))
				burst(e.chest_pos(), c, 22, 0.3, 4.0)
				Sfx.play_at(str(f.get("school", "hit")) if str(f.get("school")) != "physical" else "hit", e.global_position, self, -4.0)
		"strike":
			var a = world.ent(int(f.get("id", 0)))
			var b = world.ent(int(f.get("to", 0)))
			if a:
				a.play_attack()
			if b:
				_slash(b.chest_pos(), a.global_position if a else b.global_position)
		"swing":
			var a2 = world.ent(int(f.get("id", 0)))
			if a2:
				a2.play_attack()
				Sfx.play_at("swing", a2.global_position, self, -10.0)
		"area":
			_area(f)
		"buff":
			var e2 = world.ent(int(f.get("id", 0)))
			if e2:
				_column(e2.global_position, school_color(str(f.get("school", "holy"))), 1.2)
		"nova":
			var x := float(f.get("x", 0))
			var z := float(f.get("z", 0))
			var e3 = world.ent(int(f.get("id", 0)))
			if e3 and not f.has("x"):
				x = e3.global_position.x
				z = e3.global_position.z
			_ring(Vector3(x, _ground(x, z), z), float(f.get("r", 5)), school_color(str(f.get("school", "physical"))))
		"tele":
			_telegraph(f)
		"boom":
			_boom(f)
		"levelup":
			var e4 = world.ent(int(f.get("id", 0)))
			if e4:
				_column(e4.global_position, Color(1.0, 0.85, 0.35), 3.0, 2.0)
				_ring(e4.global_position, 3.0, Color(1.0, 0.85, 0.35))
				if e4.id == Game.me_id:
					Sfx.play("levelup")
		"achievement":
			var e5 = world.ent(int(f.get("id", 0)))
			if e5:
				_column(e5.global_position, Color(1.0, 0.7, 0.2), 2.0, 1.4)
				if e5.id == Game.me_id:
					Sfx.play("achievement")
		"summon":
			var p := Vector3(float(f["x"]), _ground(float(f["x"]), float(f["z"])), float(f["z"]))
			_ring(p, 2.0, school_color(str(f.get("school", "shadow"))))
			burst(p + Vector3.UP * 0.5, school_color(str(f.get("school", "shadow"))), 30, 0.3, 3.0, 0.9)
		"blink":
			var c2 := school_color("arcane")
			for key in [["x", "z"], ["x2", "z2"]]:
				if f.has(key[0]):
					var p2 := Vector3(float(f[key[0]]), _ground(float(f[key[0]]), float(f[key[1]])) + 1.0, float(f[key[1]]))
					burst(p2, c2, 26, 0.25, 5.0)
					flash(p2, c2, 2.5)
			Sfx.play("arcane", -6.0)
		"charge", "leap":
			var e6 = world.ent(int(f.get("id", 0)))
			if e6:
				burst(e6.global_position + Vector3.UP * 0.3, Color(0.7, 0.6, 0.45), 20, 0.4, 2.5, 0.8)
				e6.dash_to(Vector3(float(f["x"]), _ground(float(f["x"]), float(f["z"])), float(f["z"])), 0.35 if k == "charge" else 0.45, k == "leap")
		"trap":
			var p3 := Vector3(float(f["x"]), _ground(float(f["x"]), float(f["z"])), float(f["z"]))
			burst(p3 + Vector3.UP * 0.3, Color(0.9, 0.9, 0.95) if str(f.get("fx")) == "blades" else Color(0.5, 0.9, 0.3), 30, 0.2, 6.0, 0.5)
			Sfx.play_at("crit", p3, self, -4.0)
		"chest":
			var e7 = world.ent(int(f.get("id", 0)))
			if e7:
				burst(e7.global_position + Vector3.UP * 0.7, Color(1.0, 0.85, 0.3), 30, 0.18, 3.0, 1.2)
				Sfx.play("coin")
		"shapeshift":
			var e8 = world.ent(int(f.get("id", 0)))
			if e8:
				burst(e8.global_position + Vector3.UP, Color(0.5, 0.9, 0.3), 40, 0.5, 2.5, 0.9)
		"taunt":
			var e9 = world.ent(int(f.get("id", 0)))
			if e9:
				flash(e9.head_pos() + Vector3.UP * 0.6, Color(1.0, 0.2, 0.1), 1.2, 0.8)
		"enrage":
			var e10 = world.ent(int(f.get("id", 0)))
			if e10:
				burst(e10.chest_pos(), Color(1.0, 0.15, 0.1), 40, 0.4, 3.0, 1.0)
				Sfx.play_at("boss", e10.global_position, self, -6.0)
		"rez":
			var e11 = world.ent(int(f.get("id", 0)))
			if e11:
				_column(e11.global_position, Color(1.0, 0.95, 0.7), 2.2, 1.5)
		"jump":
			var e12 = world.ent(int(f.get("id", 0)))
			if e12 and e12.id != Game.me_id:
				e12.jump()
		"say":
			var e13 = world.ent(int(f.get("id", 0)))
			if e13 and world.hud:
				world.hud.bubble(e13, str(f.get("text", "")))
		"duelflag":
			var p4 := Vector3(float(f["x"]), _ground(float(f["x"]), float(f["z"])), float(f["z"]))
			var flag := MeshInstance3D.new()
			var mb := MeshBuilder.new()
			mb.cylinder(Mat.stylized(Color("#5a3a22"), Mat.P.WOOD), MeshBuilder.at(Vector3.ZERO), 0.05, 0.05, 2.6, 6)
			mb.box(Mat.stylized(Color("#c02020"), Mat.P.CLOTH), MeshBuilder.at(Vector3(0.45, 2.2, 0)), Vector3(0.9, 0.6, 0.04))
			flag.mesh = mb.commit()
			flag.position = p4
			_add_timed(flag, 120.0, 1.0)


func _projectile(f: Dictionary) -> void:
	var a = world.ent(int(f.get("from", 0)))
	var b = world.ent(int(f.get("to", 0)))
	if a == null or b == null:
		return
	var school := str(f.get("school", "physical"))
	var c := school_color(school)
	var node := Node3D.new()
	var start: Vector3 = a.hand_pos()
	node.position = start
	var ab := str(f.get("ab", ""))
	if school == "physical" or ab == "autoshot":
		# Pfeil / Bolzen
		var mi := MeshInstance3D.new()
		var mb := MeshBuilder.new()
		mb.cylinder(Mat.stylized(Color("#8a6038"), Mat.P.WOOD), MeshBuilder.at_euler(Vector3.ZERO, Vector3(PI * 0.5, 0, 0)), 0.018, 0.018, 0.8, 5)
		mb.cylinder(Mat.stylized(Color("#b8bcc6"), Mat.P.METAL), MeshBuilder.at_euler(Vector3(0, 0, -0.4), Vector3(PI * 0.5, 0, 0)), 0.04, 0.0, 0.14, 5)
		mi.mesh = mb.commit()
		node.add_child(mi)
	else:
		var core := FxLib.glow_sprite(Color(c, 1.0), 0.7)
		node.add_child(core)
		var core2 := FxLib.glow_sprite(Color(1, 1, 1, 0.9), 0.3)
		node.add_child(core2)
		var trail := FxLib.particles(30, 0.45, 0.32, FxLib._ramp(Color(c, 0.9), Color(c, 0.5), Color(c, 0.0)), Vector3.ZERO, 30.0, 0.05)
		node.add_child(trail)
		var l := FxLib.light(c, 2.5, 6.0)
		node.add_child(l)
		if school == "fire":
			node.add_child(FxLib.fire(0.35, c, false))
	add_child(node)
	_projectiles.append({"node": node, "to": b, "speed": float(f.get("sp", 25.0)), "school": school, "arrow": school == "physical" or ab == "autoshot",
		"target_pos": b.chest_pos()})
	if a.has_method("cast_release"):
		a.cast_release()
	Sfx.play_at("cast" if school != "physical" else "swing", start, self, -10.0)


func _slash(pos: Vector3, from: Vector3) -> void:
	var mi := MeshInstance3D.new()
	var mesh := TorusMesh.new()
	mesh.inner_radius = 0.6
	mesh.outer_radius = 0.75
	mesh.rings = 24
	mi.mesh = mesh
	var m := Mat.glow_additive(Color(1.0, 0.95, 0.8), 1.2)
	mi.material_override = m
	mi.position = pos
	mi.look_at_from_position(pos, from + Vector3.UP * 1.2, Vector3.UP)
	mi.rotate_object_local(Vector3.RIGHT, PI * 0.5)
	mi.rotate_object_local(Vector3.FORWARD, randf_range(-0.8, 0.8))
	mi.scale = Vector3(1, 0.15, 1)
	_add_timed(mi, 0.18, 0.18)


func _area(f: Dictionary) -> void:
	var x := float(f.get("x", 0))
	var z := float(f.get("z", 0))
	var r := float(f.get("r", 5))
	var c := school_color(str(f.get("school", "physical")))
	var shape := str(f.get("shape", "circle"))
	var p := Vector3(x, _ground(x, z), z)
	if shape == "cone":
		var d := decal("cone", r, Color(c, 0.8), deg_to_rad(110))
		d.position = p
		d.rotation.y = float(f.get("rot", 0))
		_add_timed(d, 0.45, 0.4)
	else:
		_ring(p, r, c)
		var d2 := decal("disc", r, Color(c, 0.35))
		d2.position = p
		_add_timed(d2, 0.5, 0.45)
	burst(p + Vector3.UP * 0.5, c, int(clampf(r * 6, 10, 60)), 0.35, r * 0.8, 0.7)
	var school := str(f.get("school", "physical"))
	Sfx.play_at(school if school != "physical" else "crit", p, self, -5.0)


func _ring(p: Vector3, r: float, c: Color) -> void:
	var d := decal("ring", 1.0, Color(c, 1.0))
	d.position = p
	add_child(d)
	var tw := create_tween()
	tw.tween_property(d, "size", Vector3(r * 2.2, 8.0, r * 2.2), 0.35).from(Vector3(0.6, 8.0, 0.6))
	tw.parallel().tween_property(d, "modulate:a", 0.0, 0.45)
	tw.tween_callback(d.queue_free)


func _column(p: Vector3, c: Color, h := 2.0, life := 1.0) -> void:
	var sp := FxLib.particles(40, 1.0, 0.18, FxLib._ramp(Color(c, 0.0), Color(c, 1.0), Color(c, 0.0)), Vector3(0, h * 1.5, 0), 6.0, 0.6)
	sp.position = p
	_add_timed(sp, life + 1.0, 0.5)
	var glow := FxLib.glow_sprite(Color(c, 0.6), 2.0)
	glow.position = p + Vector3.UP * 1.0
	_add_timed(glow, life, life)
	var l := FxLib.light(c, 2.5, 6.0)
	l.position = p + Vector3.UP
	_add_timed(l, life, life)


func _telegraph(f: Dictionary) -> void:
	var shape := str(f.get("shape", "circle"))
	var x := float(f.get("x", 0))
	var z := float(f.get("z", 0))
	var r := float(f.get("r", 4))
	var dur := float(f.get("dur", 1.5))
	var school := str(f.get("school", "physical"))
	var c := Color(1.0, 0.25, 0.1) if school in ["physical", "fire"] else school_color(school).lerp(Color(1, 0.2, 0.1), 0.4)
	var p := Vector3(x, _ground(x, z), z)
	var outer: Decal
	var inner: Decal
	match shape:
		"cone":
			var ang := float(f.get("ang", 1.6))
			outer = decal("cone", r, Color(c, 0.85), ang)
			inner = decal("cone", r, Color(c.lightened(0.2), 0.55), ang)
			outer.rotation.y = float(f.get("rot", 0))
			inner.rotation.y = outer.rotation.y
		"line":
			var w := float(f.get("w", 4))
			outer = decal("line", 1.0, Color(c, 0.85))
			outer.size = Vector3(w, 8.0, r)
			inner = decal("line", 1.0, Color(c.lightened(0.2), 0.55))
			inner.size = Vector3(w, 8.0, r)
			var rot := float(f.get("rot", 0))
			outer.rotation.y = rot
			inner.rotation.y = rot
			var fwd := Vector3(-sin(rot), 0, -cos(rot))
			p += fwd * r * 0.5
		"ring":
			outer = decal("circle", r, Color(c, 0.85))
			inner = decal("ring", float(f.get("r0", 6)), Color(0.4, 1.0, 0.4, 0.9))
		_:
			outer = decal("circle", r, Color(c, 0.85))
			inner = decal("disc", r, Color(c.lightened(0.2), 0.45))
	outer.position = p
	inner.position = p
	add_child(outer)
	add_child(inner)
	var tw := create_tween()
	if shape in ["circle"]:
		tw.tween_property(inner, "size", Vector3(r * 2.0, 8.0, r * 2.0), dur).from(Vector3(0.2, 8.0, 0.2))
	elif shape == "line":
		inner.modulate.a = 0.15
		tw.tween_property(inner, "modulate:a", 0.75, dur)
	else:
		tw.tween_property(inner, "modulate:a", 0.75, dur).from(0.1)
	tw.tween_callback(func():
		outer.queue_free()
		inner.queue_free()
	)
	var me = world.me
	if me and me.global_position.distance_to(p) < r + 3.0:
		Sfx.play("warn", -4.0)


func _boom(f: Dictionary) -> void:
	var x := float(f.get("x", 0))
	var z := float(f.get("z", 0))
	var r := float(f.get("r", 4))
	var school := str(f.get("school", "physical"))
	var c := school_color(school)
	var p := Vector3(x, _ground(x, z), z)
	var shape := str(f.get("shape", "circle"))
	if shape == "cone":
		var d := decal("cone", r, Color(1, 0.8, 0.5, 0.9), float(f.get("ang", 1.6)))
		d.position = p
		d.rotation.y = float(f.get("rot", 0))
		_add_timed(d, 0.35, 0.35)
		var fwd := Vector3(-sin(float(f.get("rot", 0))), 0, -cos(float(f.get("rot", 0))))
		burst(p + fwd * r * 0.5 + Vector3.UP * 0.5, c, 50, 0.45, r * 0.6, 0.6)
	else:
		_ring(p, r, c)
		burst(p + Vector3.UP * 0.5, c, int(clampf(r * 8, 16, 80)), 0.45, r * 0.9, 0.7)
	Sfx.play_at("crit" if school == "physical" else school, p, self, -2.0)
	if world.cam_rig:
		var me = world.me
		if me and me.global_position.distance_to(p) < r + 8:
			world.cam_rig.shake(0.25)


func _process(delta: float) -> void:
	var t := Game.now()
	for i in range(_timed.size() - 1, -1, -1):
		var e: Array = _timed[i]
		var n: Node3D = e[0]
		if not is_instance_valid(n):
			_timed.remove_at(i)
			continue
		var left: float = e[1] - t
		if left <= 0:
			n.queue_free()
			_timed.remove_at(i)
		elif left < e[2] and e[2] > 0.0:
			var a = left / e[2]
			if n is Decal:
				n.modulate.a = minf(n.modulate.a, a)
			elif n is MeshInstance3D and n.material_override is StandardMaterial3D:
				n.material_override.albedo_color.a = a
			elif n is OmniLight3D:
				n.light_energy *= 0.9
			elif n is MeshInstance3D and n.mesh is QuadMesh:
				var qm: StandardMaterial3D = n.mesh.material
				if qm:
					qm.albedo_color.a = a * 0.9
	for i in range(_projectiles.size() - 1, -1, -1):
		var pr: Dictionary = _projectiles[i]
		var node: Node3D = pr["node"]
		var tgt = pr["to"]
		var tp: Vector3 = pr["target_pos"]
		if is_instance_valid(tgt):
			tp = tgt.chest_pos()
			pr["target_pos"] = tp
		var d := tp - node.position
		var step: float = pr["speed"] * delta
		if d.length() <= step + 0.1:
			_projectiles.remove_at(i)
			if not pr["arrow"]:
				burst(tp, school_color(pr["school"]), 26, 0.32, 4.5)
				Sfx.play_at(pr["school"], tp, self, -3.0)
			else:
				Sfx.play_at("hit", tp, self, -8.0)
			node.queue_free()
		else:
			node.position += d.normalized() * step
			if pr["arrow"]:
				node.look_at(tp, Vector3.UP)
