class_name MenuScene
extends Node3D
## 3D-Kulisse für Anmeldung und Charakterwahl: eine Lichtung mit Lagerfeuer am Rand der Grünmark,
## im Hintergrund Burg Eldenstein. Wird lokal erzeugt (funktioniert auch ohne Server).

var builder: ZoneBuilder
var cam: Camera3D
var model: Node3D
var pedestal := Vector3(0, 0, 0)
var _t := 0.0
var mode := "login"      # login | select | create
var _cam_from := Vector3.ZERO
var _cam_target := Vector3.ZERO
var model_rot := 0.0
var _drag := false


func _ready() -> void:
	var zone := _make_zone()
	builder = ZoneBuilder.new()
	builder.build(self, zone)
	pedestal = Vector3(0, builder.height(0, 0), 0)
	cam = Camera3D.new()
	cam.fov = 52
	cam.far = 900
	add_child(cam)
	cam.make_current()
	_set_mode_cam(true)


func _make_zone() -> Dictionary:
	var n := 97
	var step := 2.0
	var size := (n - 1) * step
	var half := size * 0.5
	var noise := FastNoiseLite.new()
	noise.seed = 7
	noise.frequency = 0.012
	var raw := PackedByteArray()
	raw.resize(n * n * 2)
	for j in n:
		for i in n:
			var x := -half + i * step
			var z := -half + j * step
			var d := Vector2(x, z).length()
			var h := noise.get_noise_2d(x, z) * 4.0
			h *= clampf((d - 10.0) / 30.0, 0.0, 1.0)
			# Hügelkette dahinter
			if z < -30:
				h += pow((-z - 30.0) / 60.0, 1.5) * 26.0 + noise.get_noise_2d(x * 2.0, z) * 5.0
			if absf(x) > 70 or z > 70:
				h += 14.0 * clampf((maxf(absf(x), z) - 70.0) / 25.0, 0.0, 1.0)
			# Burghügel
			var cd := Vector2(x - 25, z + 70).length()
			h += maxf(0.0, 18.0 - cd * 0.55)
			raw.encode_s16((j * n + i) * 2, int(h * 100))
	var props: Array = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	for k in 140:
		var a := rng.randf() * TAU
		var r := rng.randf_range(14.0, 85.0)
		var x := cos(a) * r
		var z := sin(a) * r
		if z > 5.0 and absf(x) < 18.0:
			continue
		props.append({"t": ["tree", "pine", "tree", "birch"][rng.randi() % 4], "x": x, "z": z, "s": rng.randf_range(0.8, 1.4), "r": rng.randf() * TAU})
	for k in 40:
		props.append({"t": "rock", "x": rng.randf_range(-60, 60), "z": rng.randf_range(-40, 40), "s": rng.randf_range(0.4, 1.6), "r": rng.randf() * TAU})
	for k in 80:
		props.append({"t": "flowers", "x": rng.randf_range(-30, 30), "z": rng.randf_range(-20, 30), "s": rng.randf_range(0.7, 1.3), "v": rng.randi() % 4})
	for k in 20:
		props.append({"t": "bush", "x": rng.randf_range(-40, 40), "z": rng.randf_range(-30, 20), "s": rng.randf_range(0.7, 1.3), "r": rng.randf() * TAU})
	props.append({"t": "campfire", "x": 3.5, "z": 2.5})
	props.append({"t": "tent", "x": 7.5, "z": -3.5, "r": -0.9, "c": "#7a3a2a"})
	props.append({"t": "crate", "x": 5.6, "z": -0.8})
	props.append({"t": "barrel", "x": 6.4, "z": 0.2})
	props.append({"t": "banner", "x": -3.5, "z": -2.5, "c": "#8f1d2c"})
	props.append({"t": "weaponrack", "x": -5, "z": 1.5, "r": 1.2})
	props.append({"t": "lantern", "x": -2.5, "z": 3.5})
	props.append({"t": "keep", "x": 25, "z": -75, "r": 0.3, "w": 24, "d": 14})
	props.append({"t": "tower", "x": 8, "z": -68, "rad": 4, "h": 16})
	props.append({"t": "tower", "x": 42, "z": -82, "rad": 4, "h": 16})
	props.append({"t": "wall", "x1": 8, "z1": -68, "x2": 42, "z2": -82})
	return {"id": "menu", "name": "Eldornia", "type": "outdoor", "theme": "gruen", "n": n, "step": step, "size": size,
		"heights": Marshalls.raw_to_base64(raw), "props": props, "water": [{"x": -38, "z": 22, "r": 14, "level": -0.6}],
		"roads": [{"w": 3.0, "pts": [[0, 40], [2, 18], [3, 6], [8, -20], [20, -55]]}], "paved": [], "accent": []}


func show_model(look: Dictionary, gear: Dictionary) -> void:
	if model:
		model.queue_free()
	var hm := HumanoidModel.new(look, gear)
	hm.idle_anim = "idle"
	add_child(hm)
	hm.position = pedestal
	hm.rotation.y = model_rot
	model = hm


func clear_model() -> void:
	if model:
		model.queue_free()
		model = null


func set_mode(m: String) -> void:
	mode = m
	_set_mode_cam(false)


func _set_mode_cam(instant: bool) -> void:
	match mode:
		"login":
			_cam_target = Vector3(10, 8, -40)
			_cam_from = Vector3(-6, 6, 26)
		"select", "create":
			_cam_target = pedestal + Vector3(0, 1.05, 0)
			_cam_from = pedestal + Vector3(-1.2 if mode == "create" else -0.6, 1.5, 4.2)
	if instant:
		cam.position = _cam_from
		cam.look_at(_cam_target)


func _process(delta: float) -> void:
	_t += delta
	var from := _cam_from
	if mode == "login":
		from = _cam_from + Vector3(sin(_t * 0.05) * 6.0, sin(_t * 0.07) * 0.8, cos(_t * 0.05) * 2.0)
	cam.position = cam.position.lerp(from, clampf(delta * 2.0, 0.0, 1.0))
	var cur_t := cam.global_transform.basis * Vector3(0, 0, -1)
	var want := (_cam_target - cam.position).normalized()
	var dir := cur_t.lerp(want, clampf(delta * 3.0, 0.0, 1.0)).normalized()
	cam.look_at(cam.position + dir)
	if model and not _drag:
		model.rotation.y = lerp_angle(model.rotation.y, model_rot, clampf(delta * 6.0, 0.0, 1.0))


func rotate_model(dx: float) -> void:
	model_rot += dx * 0.01
	if model:
		model.rotation.y = model_rot
