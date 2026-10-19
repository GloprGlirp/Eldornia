class_name CameraRig
extends Node3D
## Frei drehbare, erhöhte Third-Person-Kamera (GDD 11): über und hinter dem Charakter, Zoom per Mausrad,
## Drehung per Maustaste, automatische Anpassung in engen Dungeons, weit herausgezoomter Modus für große Kämpfe.

var world
var cam: Camera3D
var yaw := 0.0
var pitch := 0.42
var dist := 9.0
var want_dist := 9.0
var max_dist := 26.0
var _shake := 0.0
var _focus := Vector3.ZERO


func _init(p_world) -> void:
	world = p_world


func _ready() -> void:
	cam = Camera3D.new()
	cam.fov = 62
	cam.near = 0.12
	cam.far = 600
	add_child(cam)
	cam.make_current()


func reset(p_yaw: float) -> void:
	yaw = p_yaw
	pitch = 0.42
	if world.me:
		_focus = world.me.global_position + Vector3.UP * 1.7


func zoom(d: float) -> void:
	want_dist = clampf(want_dist + d * (1.2 + want_dist * 0.12), 1.2, max_dist)


func shake(a: float) -> void:
	_shake = maxf(_shake, a)


func update(delta: float) -> void:
	var me = world.me
	if me == null:
		return
	var head: float = 1.65 if me.mount_model == null else 2.5
	if me.model is CreatureModel:
		head = 1.6
	var target_focus: Vector3 = me.global_position + Vector3.UP * head
	_focus = _focus.lerp(target_focus, clampf(delta * 18.0, 0.0, 1.0))
	if _focus.distance_to(target_focus) > 6.0:
		_focus = target_focus
	var indoor: bool = world.hf == null
	max_dist = 14.0 if indoor else 26.0
	var d := want_dist
	if indoor:
		d = minf(d, 12.0)
	var dir := Vector3(sin(yaw) * cos(pitch), sin(pitch), cos(yaw) * cos(pitch))
	# Kollision mit Gelände bzw. Dungeonwänden
	var allowed := d
	var steps := 24
	for i in range(1, steps + 1):
		var t := d * float(i) / steps
		var p := _focus + dir * t
		var blocked := false
		if world.hf:
			if p.y < world.ground_height(p.x, p.z) + 0.35:
				blocked = true
		else:
			if p.y > 5.2 or p.y < 0.3 or world.cell(p.x, p.z) == 3:
				blocked = true
		if blocked:
			allowed = maxf(0.6, t - d / steps)
			break
	dist = lerpf(dist, allowed, clampf(delta * (14.0 if allowed < dist else 4.0), 0.0, 1.0))
	var cp := _focus + dir * dist
	if world.hf:
		cp.y = maxf(cp.y, world.ground_height(cp.x, cp.z) + 0.35)
	if _shake > 0.0:
		_shake = maxf(0.0, _shake - delta)
		cp += Vector3(randf_range(-1, 1), randf_range(-1, 1), randf_range(-1, 1)) * _shake * 0.5
	cam.global_position = cp
	cam.look_at(_focus, Vector3.UP)
	# Charakter ausblenden, wenn die Kamera ganz nah ist
	if me.model:
		me.model.visible = dist > 0.9
