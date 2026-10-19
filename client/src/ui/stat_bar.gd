class_name StatBar
extends Control
## Glänzender Statusbalken (Gesundheit, Ressourcen, Zauberbalken, Erfahrung) mit weichem Nachlauf.

var value := 1.0
var max_value := 1.0
var color := Color("#20b020")
var bg := Color(0.05, 0.04, 0.03, 0.9)
var text := ""
var text_size := 13
var show_text := true
var _shown := 1.0
var _trail := 1.0
var border := Color(0, 0, 0, 0.9)
var spark := false
var center_text := true
var left_text := ""
var marker := -1.0      # z. B. Unterbrechbarkeit / Schwellen


func _init(c := Color("#20b020"), h := 16) -> void:
	color = c
	custom_minimum_size.y = h
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func set_values(v: float, m: float, txt := "") -> void:
	value = v
	max_value = maxf(0.0001, m)
	text = txt
	queue_redraw()


func _process(delta: float) -> void:
	var f := clampf(value / max_value, 0.0, 1.0)
	if absf(_shown - f) > 0.001 or absf(_trail - f) > 0.001:
		_shown = lerpf(_shown, f, clampf(delta * 14.0, 0.0, 1.0))
		if _trail < f:
			_trail = f
		else:
			_trail = lerpf(_trail, f, clampf(delta * 2.5, 0.0, 1.0))
		queue_redraw()


func snap() -> void:
	_shown = clampf(value / max_value, 0.0, 1.0)
	_trail = _shown
	queue_redraw()


func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	draw_rect(r, bg)
	var inner := r.grow(-1)
	if _trail > _shown:
		draw_rect(Rect2(inner.position, Vector2(inner.size.x * _trail, inner.size.y)), color.lightened(0.5) * Color(1, 1, 1, 0.6))
	var fill := Rect2(inner.position, Vector2(inner.size.x * _shown, inner.size.y))
	draw_rect(fill, color.darkened(0.15))
	draw_rect(Rect2(fill.position, Vector2(fill.size.x, fill.size.y * 0.45)), color.lightened(0.18))
	draw_rect(Rect2(fill.position + Vector2(0, fill.size.y * 0.8), Vector2(fill.size.x, fill.size.y * 0.2)), color.darkened(0.4))
	if spark and _shown > 0.01 and _shown < 0.999:
		var x := fill.end.x
		draw_rect(Rect2(Vector2(x - 2, inner.position.y), Vector2(4, inner.size.y)), Color(1, 1, 0.85, 0.9))
	if marker >= 0.0:
		var mx := inner.position.x + inner.size.x * marker
		draw_line(Vector2(mx, inner.position.y), Vector2(mx, inner.end.y), Color(1, 1, 1, 0.7), 1.0)
	draw_rect(r, border, false, 1.0)
	if show_text and (text != "" or left_text != ""):
		var f := UiSkin.font_bold
		if text != "":
			var w := f.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, text_size).x
			var pos := Vector2((size.x - w) * 0.5 if center_text else size.x - w - 4, (size.y + text_size * 0.72) * 0.5)
			draw_string_outline(f, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, text_size, 3, Color(0, 0, 0, 0.9))
			draw_string(f, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, text_size, Color(1, 1, 1))
		if left_text != "":
			var pos2 := Vector2(5, (size.y + text_size * 0.72) * 0.5)
			draw_string_outline(f, pos2, left_text, HORIZONTAL_ALIGNMENT_LEFT, size.x * 0.7, text_size, 3, Color(0, 0, 0, 0.9))
			draw_string(f, pos2, left_text, HORIZONTAL_ALIGNMENT_LEFT, size.x * 0.7, text_size, Color(1, 1, 1))
