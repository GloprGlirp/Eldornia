class_name IconSlot
extends Control
## Symbolplatz für Gegenstände und Fähigkeiten: Symbol, Anzahl, Seltenheitsrahmen, Abklingzeit,
## Tastenbelegung, Tooltip und Ziehen & Ablegen.

signal clicked(slot: IconSlot, button: int)
signal dropped(slot: IconSlot, data: Dictionary)

var kind := ""            # bag, equip, bar, ab, loot, vendor, trade, bank, mail, any
var index := -1
var key := ""             # Ausrüstungsslot oder Fähigkeits-ID
var payload: Dictionary = {}
var tex: Texture2D
var count := 0
var quality := -1
var keybind := ""
var cd_end := 0.0
var cd_total := 0.0
var gcd := false
var dim := false
var red := false
var glow := false
var placeholder: Texture2D
var tip_bb := ""
var tip_fn: Callable
var drag_enabled := true
var accepts_drop := false
var _hover := false
var _glow_t := 0.0


func _init(p_size := 44) -> void:
	custom_minimum_size = Vector2(p_size, p_size)
	mouse_filter = Control.MOUSE_FILTER_STOP
	mouse_entered.connect(func(): _hover = true; queue_redraw())
	mouse_exited.connect(func(): _hover = false; queue_redraw())


func set_item(id: String, n := 1, inst = null) -> void:
	if id == "":
		clear()
		return
	var it := Content.item(id)
	tex = Content.item_icon(it) if not it.is_empty() else null
	count = n
	quality = int(it.get("q", 1))
	payload = {"item": id, "inst": inst}
	tip_bb = ""
	tip_fn = func(): return Tips.item_bb(id, inst)
	tooltip_text = " "
	queue_redraw()


func set_ability(ab: Dictionary) -> void:
	tex = Content.ability_icon(ab)
	count = 0
	quality = -1
	payload = {"ab": ab.get("id")}
	tip_fn = func(): return Tips.ability_bb(ab)
	tooltip_text = " "
	queue_redraw()


func set_icon(t: Texture2D, tip := "") -> void:
	tex = t
	tip_bb = tip
	tip_fn = Callable()
	tooltip_text = " " if tip != "" else ""
	queue_redraw()


func clear() -> void:
	tex = null
	count = 0
	quality = -1
	payload = {}
	tip_bb = ""
	tip_fn = Callable()
	tooltip_text = ""
	cd_end = 0.0
	queue_redraw()


func _make_custom_tooltip(_for_text: String) -> Object:
	var bb := tip_bb
	if tip_fn.is_valid():
		bb = tip_fn.call()
	if bb == "":
		return null
	return Tips.panel(bb, 300)


func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed and not ev.is_echo():
		if ev.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
			clicked.emit(self, ev.button_index)
			accept_event()


func _process(delta: float) -> void:
	if cd_end > 0.0 or glow:
		_glow_t += delta
		queue_redraw()
		if cd_end > 0.0 and Game.now() > cd_end:
			cd_end = 0.0


func _draw() -> void:
	var r := Rect2(Vector2.ZERO, size)
	draw_style_box(UiSkin.slot_box(), r)
	var inner := r.grow(-3)
	if tex:
		draw_texture_rect(tex, inner, false, Color(0.4, 0.4, 0.4) if dim else (Color(1, 0.45, 0.45) if red else Color.WHITE))
	elif placeholder:
		draw_texture_rect(placeholder, inner, false, Color(1, 1, 1, 0.25))
	# Abklingzeit (Sektor)
	if cd_end > 0.0 and cd_total > 0.0:
		var left := cd_end - Game.now()
		if left > 0:
			var frac := clampf(left / cd_total, 0.0, 1.0)
			var c := inner.get_center()
			var rad := inner.size.length() * 0.75
			var pts := PackedVector2Array([c])
			var steps := 28
			var a0 := -PI * 0.5
			for i in steps + 1:
				var a := a0 + TAU * (1.0 - frac) + TAU * frac * float(i) / steps
				var p := c + Vector2(cos(a), sin(a)) * rad
				p.x = clampf(p.x, inner.position.x, inner.end.x)
				p.y = clampf(p.y, inner.position.y, inner.end.y)
				pts.append(p)
			draw_colored_polygon(pts, Color(0, 0, 0, 0.62))
			if left >= 1.5 and not gcd:
				var txt := Content.fmt_time(left)
				var f := UiSkin.font_bold
				var fs := int(size.y * 0.38)
				var w := f.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
				draw_string_outline(f, Vector2((size.x - w) * 0.5, size.y * 0.62), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, 4, Color(0, 0, 0))
				draw_string(f, Vector2((size.x - w) * 0.5, size.y * 0.62), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, fs, Color("#ffe080"))
	# Rahmen nach Seltenheit
	if quality >= 2:
		draw_rect(inner.grow(1), Content.rarity_color(quality), false, 2.0)
	if glow:
		var a := 0.5 + 0.5 * sin(_glow_t * 6.0)
		draw_rect(inner.grow(1), Color(1.0, 0.85, 0.3, a), false, 3.0)
	if _hover:
		draw_rect(inner, Color(1, 1, 1, 0.12))
		draw_rect(inner.grow(1), Color(1, 0.9, 0.6, 0.8), false, 1.0)
	var f2 := UiSkin.font_bold
	if count > 1:
		var t := str(count)
		var fs2 := 14
		var w2 := f2.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2).x
		draw_string_outline(f2, Vector2(size.x - w2 - 4, size.y - 4), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, 4, Color.BLACK)
		draw_string(f2, Vector2(size.x - w2 - 4, size.y - 4), t, HORIZONTAL_ALIGNMENT_LEFT, -1, fs2, Color.WHITE)
	if keybind != "":
		draw_string_outline(f2, Vector2(4, 14), keybind, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, 3, Color.BLACK)
		draw_string(f2, Vector2(4, 14), keybind, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("#e8e0c8"))


# ------------------------------------------------------------------ Ziehen & Ablegen
func _get_drag_data(_at: Vector2) -> Variant:
	if not drag_enabled or tex == null or payload.is_empty():
		return null
	var prev := TextureRect.new()
	prev.texture = tex
	prev.size = Vector2(40, 40)
	prev.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	prev.modulate = Color(1, 1, 1, 0.85)
	var holder := Control.new()
	holder.add_child(prev)
	prev.position = Vector2(-20, -20)
	set_drag_preview(holder)
	var d := payload.duplicate()
	d["from"] = kind
	d["index"] = index
	d["key"] = key
	return d


func _can_drop_data(_at: Vector2, data: Variant) -> bool:
	return accepts_drop and data is Dictionary


func _drop_data(_at: Vector2, data: Variant) -> void:
	dropped.emit(self, data)
