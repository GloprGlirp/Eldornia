class_name Win
extends PanelContainer
## Fensterrahmen: Titelzeile (verschiebbar), Schließen-Knopf und Inhaltsbereich.

signal closed

var title := ""
var body: VBoxContainer
var title_label: Label
var header: HBoxContainer
var _drag := false
var _drag_off := Vector2.ZERO
var win_id := ""
static var positions: Dictionary = {}


func _init(p_title := "", p_id := "", min_size := Vector2(380, 300)) -> void:
	title = p_title
	win_id = p_id if p_id != "" else p_title
	custom_minimum_size = min_size
	mouse_filter = Control.MOUSE_FILTER_STOP
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	add_child(v)
	header = HBoxContainer.new()
	header.mouse_filter = Control.MOUSE_FILTER_STOP
	header.custom_minimum_size.y = 30
	v.add_child(header)
	title_label = UiSkin.title_label(title, 20)
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	header.add_child(title_label)
	var close := Button.new()
	close.text = "✕"
	close.custom_minimum_size = Vector2(30, 28)
	close.tooltip_text = "Schließen (Esc)"
	close.add_theme_font_size_override("font_size", 15)
	close.pressed.connect(close_win)
	header.add_child(close)
	var sep := ColorRect.new()
	sep.color = Color(0.9, 0.7, 0.35, 0.35)
	sep.custom_minimum_size.y = 1
	v.add_child(sep)
	body = VBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 6)
	v.add_child(body)
	header.gui_input.connect(_on_header_input)
	visible = false


func open() -> void:
	if visible:
		move_to_front()
		return
	visible = true
	move_to_front()
	Sfx.play("open", -10.0)
	if positions.has(win_id):
		position = positions[win_id]
	_clamp_to_screen.call_deferred()
	_on_open()


func close_win() -> void:
	if not visible:
		return
	visible = false
	positions[win_id] = position
	Sfx.play("close", -12.0)
	_on_close()
	closed.emit()


func toggle() -> void:
	if visible:
		close_win()
	else:
		open()


func _on_open() -> void:
	pass


func _on_close() -> void:
	pass


func _clamp_to_screen() -> void:
	var vp := get_viewport_rect().size
	if size.x <= 1:
		return
	position.x = clampf(position.x, 0, maxf(0, vp.x - size.x))
	position.y = clampf(position.y, 0, maxf(0, vp.y - size.y))


func center(offset := Vector2.ZERO) -> void:
	var vp := get_viewport_rect().size
	position = ((vp - get_combined_minimum_size()) * 0.5 + offset).floor()


func _on_header_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
		_drag = ev.pressed
		_drag_off = get_global_mouse_position() - global_position
		if ev.pressed:
			move_to_front()
	elif ev is InputEventMouseMotion and _drag:
		global_position = get_global_mouse_position() - _drag_off
		_clamp_to_screen()


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed:
		move_to_front()


func clear_body() -> void:
	for c in body.get_children():
		c.queue_free()
