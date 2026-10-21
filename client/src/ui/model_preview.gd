class_name ModelPreview
extends SubViewportContainer
## Kleine 3D-Vorschau einer Figur oder Kreatur (Charakterfenster, Betrachten, Sammlung). Mit der Maus drehbar.

var vp: SubViewport
var pivot: Node3D
var cam: Camera3D
var model: Node3D
var _drag := false
var _key := ""
var spin := 0.0


func _init(p_size := Vector2(220, 300)) -> void:
	custom_minimum_size = p_size
	stretch = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	vp = SubViewport.new()
	vp.own_world_3d = true
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.size = Vector2i(p_size)
	vp.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	add_child(vp)
	var env := WorldEnvironment.new()
	var e := Environment.new()
	e.background_mode = Environment.BG_CLEAR_COLOR
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.75, 0.72, 0.8)
	e.ambient_light_energy = 0.9
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = e
	vp.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35, 35, 0)
	sun.light_energy = 1.4
	sun.light_color = Color(1.0, 0.95, 0.85)
	vp.add_child(sun)
	var rim := DirectionalLight3D.new()
	rim.rotation_degrees = Vector3(-15, -150, 0)
	rim.light_energy = 0.8
	rim.light_color = Color(0.6, 0.75, 1.0)
	vp.add_child(rim)
	pivot = Node3D.new()
	pivot.rotation.y = PI      # Modelle schauen nach -z, die Kamera steht bei +z
	vp.add_child(pivot)
	cam = Camera3D.new()
	cam.fov = 30
	cam.position = Vector3(0, 1.05, 5.2)
	vp.add_child(cam)
	cam.look_at_from_position(cam.position, Vector3(0, 0.95, 0))


## Zeigt eine Spielfigur mit Aussehen + Ausrüstung.
func show_humanoid(look: Dictionary, gear: Dictionary) -> void:
	var key := "h" + str(look) + str(gear)
	if key == _key:
		return
	_key = key
	_clear()
	var l := look.duplicate()
	l.erase("gear")
	l.erase("mount")
	l.erase("companion")
	model = HumanoidModel.new(l, gear)
	pivot.add_child(model)
	var h := 1.9 if str(l.get("kind", "human")) != "dwarf" else 1.4
	_frame(h)


func show_creature(kind: String, look: Dictionary, h := 1.6, dist_mul := 1.0) -> void:
	var key := "c" + kind + str(look)
	if key == _key:
		return
	_key = key
	_clear()
	model = CreatureModel.new(kind, look)
	pivot.add_child(model)
	_frame(h, dist_mul)


func _frame(h: float, dist_mul := 1.0) -> void:
	var d := (h * 2.6 + 0.6) * dist_mul
	cam.position = Vector3(0, h * 0.55, d)
	cam.look_at_from_position(cam.position, Vector3(0, h * 0.5, 0))


func _clear() -> void:
	if model:
		model.queue_free()
		model = null


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		_drag = ev.pressed
		accept_event()
	elif ev is InputEventMouseMotion and _drag:
		pivot.rotation.y += ev.relative.x * 0.012
		accept_event()


func _process(delta: float) -> void:
	if spin != 0.0 and not _drag:
		pivot.rotation.y += spin * delta
