class_name AnimNode3D
extends Node3D
## Kleine Animationen für Requisiten: drehen (Windmühle), flackern (Feuer), schweben (Kristalle).

@export var mode := "spin"
@export var axis := Vector3(0, 0, 1)
@export var speed := 0.6
@export var amount := 0.15
var _t := 0.0
var _base_pos := Vector3.ZERO
var _base_energy := 1.0
var _light: Light3D


func _ready() -> void:
	_base_pos = position
	_t = randf() * 10.0
	if mode == "flicker":
		for c in get_children():
			if c is Light3D:
				_light = c
				_base_energy = c.light_energy
				break


func _process(delta: float) -> void:
	_t += delta
	match mode:
		"spin":
			rotate_object_local(axis.normalized(), speed * delta)
		"bob":
			position = _base_pos + Vector3(0, sin(_t * speed) * amount, 0)
			rotate_object_local(Vector3.UP, delta * 0.3)
		"flicker":
			if _light:
				_light.light_energy = _base_energy * (0.85 + 0.15 * sin(_t * 13.0) * sin(_t * 7.3 + 1.0) + randf() * 0.06)
			scale = Vector3.ONE * (0.95 + 0.07 * sin(_t * 11.0))
		"sway":
			rotation.z = sin(_t * speed) * amount
