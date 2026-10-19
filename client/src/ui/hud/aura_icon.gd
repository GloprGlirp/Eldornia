class_name AuraIcon
extends Control
## Kleines Buff-/Debuff-Symbol mit Restzeit. Rechtsklick auf eigene Buffs entfernt sie (sofern erlaubt).

var a: Array
var mine := false
var tex: Texture2D
var _start := 0.0


func _init(p_a: Array, p_mine: bool) -> void:
	a = p_a
	mine = p_mine
	_start = Game.now()
	custom_minimum_size = Vector2(26, 34)
	var icon := str(a[4]) if a.size() > 4 and str(a[4]) != "" else "magic-swirl"
	var school := str(a[9]) if a.size() > 9 else "physical"
	var sc: Array = Content.SCHOOL_BG.get(school if school != "" else "physical", Content.SCHOOL_BG["physical"])
	tex = Content.icon(icon, Color.html(sc[0]).darkened(0.2) if int(a[5]) == 0 else Color(0.45, 0.08, 0.08), 32)
	tooltip_text = " "
	mouse_filter = Control.MOUSE_FILTER_STOP


func _make_custom_tooltip(_t: String) -> Object:
	var left := float(a[2]) - (Game.now() - _start)
	var aa := a.duplicate()
	aa[2] = left
	return Tips.panel(Tips.aura_bb(aa), 200)


func _process(_d: float) -> void:
	queue_redraw()


func _draw() -> void:
	var r := Rect2(Vector2(1, 1), Vector2(24, 24))
	draw_texture_rect(tex, r, false)
	draw_rect(r, Color(0.8, 0.1, 0.1) if int(a[5]) == 1 else Color(0.1, 0.1, 0.1), false, 1.5)
	var left := float(a[2]) - (Game.now() - _start)
	var f := UiSkin.font_bold
	if float(a[3]) > 0 and float(a[3]) < 7200 and left > 0:
		var t := Content.fmt_time(left)
		var w := f.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, 11).x
		draw_string_outline(f, Vector2(13 - w * 0.5, 34), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, 3, Color.BLACK)
		draw_string(f, Vector2(13 - w * 0.5, 34), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1, 0.9, 0.5))
	if int(a[6]) > 1:
		draw_string_outline(f, Vector2(15, 24), str(int(a[6])), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, 3, Color.BLACK)
		draw_string(f, Vector2(15, 24), str(int(a[6])), HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
