class_name UiSkin
extends RefCounted
## Gemalte Oberfläche im Stil klassischer Fantasy-MMOs: dunkles Leder/Stein, goldene Rahmen, Pergament.
## Alle Texturen werden beim Start prozedural erzeugt.

static var theme: Theme
static var font_body: FontFile
static var font_bold: FontFile
static var font_title: FontFile
static var font_deco: FontFile
static var font_italic: FontFile
static var _tex: Dictionary = {}

const GOLD := Color("#e8c374")
const GOLD_DARK := Color("#7a5a2a")
const TEXT := Color("#f2e6c8")
const TEXT_DIM := Color("#b8a888")
const PARCH_TEXT := Color("#3a2410")
const RED := Color("#ff5040")
const GREEN := Color("#5aff5a")
const YELLOW := Color("#ffd23a")


static func init() -> void:
	if theme:
		return
	font_body = load("res://assets/fonts/AlegreyaSans-Medium.woff2")
	font_bold = load("res://assets/fonts/AlegreyaSans-Bold.woff2")
	font_italic = load("res://assets/fonts/AlegreyaSans-Italic.woff2")
	font_title = load("res://assets/fonts/Cinzel-Bold.woff2")
	font_deco = load("res://assets/fonts/CinzelDecorative-Bold.woff2")
	theme = Theme.new()
	theme.default_font = font_body
	theme.default_font_size = 17
	var t := theme
	# Panels
	t.set_stylebox("panel", "PanelContainer", frame_box())
	t.set_stylebox("panel", "Panel", frame_box())
	t.set_stylebox("panel", "PopupPanel", frame_box())
	t.set_stylebox("panel", "TooltipPanel", tooltip_box())
	t.set_color("font_color", "TooltipLabel", TEXT)
	t.set_font("font", "TooltipLabel", font_body)
	t.set_font_size("font_size", "TooltipLabel", 16)
	# Labels
	t.set_color("font_color", "Label", TEXT)
	t.set_color("font_shadow_color", "Label", Color(0, 0, 0, 0.85))
	t.set_constant("shadow_offset_x", "Label", 1)
	t.set_constant("shadow_offset_y", "Label", 1)
	t.set_color("default_color", "RichTextLabel", TEXT)
	t.set_font("normal_font", "RichTextLabel", font_body)
	t.set_font("bold_font", "RichTextLabel", font_bold)
	t.set_font("italics_font", "RichTextLabel", font_italic)
	t.set_font_size("normal_font_size", "RichTextLabel", 17)
	t.set_font_size("bold_font_size", "RichTextLabel", 17)
	t.set_font_size("italics_font_size", "RichTextLabel", 17)
	t.set_color("font_shadow_color", "RichTextLabel", Color(0, 0, 0, 0.8))
	t.set_constant("shadow_offset_x", "RichTextLabel", 1)
	t.set_constant("shadow_offset_y", "RichTextLabel", 1)
	# Buttons
	for cls in ["Button", "OptionButton", "MenuButton"]:
		t.set_stylebox("normal", cls, button_box(0))
		t.set_stylebox("hover", cls, button_box(1))
		t.set_stylebox("pressed", cls, button_box(2))
		t.set_stylebox("disabled", cls, button_box(3))
		t.set_stylebox("focus", cls, StyleBoxEmpty.new())
		t.set_color("font_color", cls, Color("#ffd98a"))
		t.set_color("font_hover_color", cls, Color("#fff2c8"))
		t.set_color("font_pressed_color", cls, Color("#e8c374"))
		t.set_color("font_disabled_color", cls, Color("#7a6a5a"))
		t.set_color("font_outline_color", cls, Color(0, 0, 0, 0.9))
		t.set_constant("outline_size", cls, 3)
		t.set_font("font", cls, font_bold)
		t.set_font_size("font_size", cls, 17)
	t.set_stylebox("normal", "CheckBox", StyleBoxEmpty.new())
	t.set_stylebox("hover", "CheckBox", StyleBoxEmpty.new())
	t.set_stylebox("pressed", "CheckBox", StyleBoxEmpty.new())
	t.set_stylebox("focus", "CheckBox", StyleBoxEmpty.new())
	t.set_color("font_color", "CheckBox", TEXT)
	t.set_color("font_hover_color", "CheckBox", Color.WHITE)
	# Eingabefelder
	var le := StyleBoxFlat.new()
	le.bg_color = Color(0.03, 0.02, 0.015, 0.9)
	le.border_color = GOLD_DARK
	le.set_border_width_all(2)
	le.set_corner_radius_all(3)
	le.content_margin_left = 8
	le.content_margin_right = 8
	le.content_margin_top = 5
	le.content_margin_bottom = 5
	var lef := le.duplicate()
	lef.border_color = GOLD
	for cls in ["LineEdit", "TextEdit", "SpinBox"]:
		t.set_stylebox("normal", cls, le)
		t.set_stylebox("focus", cls, lef)
		t.set_stylebox("read_only", cls, le)
		t.set_color("font_color", cls, TEXT)
		t.set_color("caret_color", cls, GOLD)
		t.set_color("selection_color", cls, Color(0.6, 0.45, 0.2, 0.6))
		t.set_color("font_placeholder_color", cls, Color(0.6, 0.55, 0.45, 0.6))
	# Scrollbalken
	var sb_bg := StyleBoxFlat.new()
	sb_bg.bg_color = Color(0, 0, 0, 0.35)
	sb_bg.set_corner_radius_all(4)
	sb_bg.content_margin_left = 4
	sb_bg.content_margin_right = 4
	var grab := StyleBoxFlat.new()
	grab.bg_color = Color("#8a6a3a")
	grab.border_color = Color("#d8b060")
	grab.set_border_width_all(1)
	grab.set_corner_radius_all(4)
	var grab_h := grab.duplicate()
	grab_h.bg_color = Color("#b08848")
	for cls in ["VScrollBar", "HScrollBar"]:
		t.set_stylebox("scroll", cls, sb_bg)
		t.set_stylebox("grabber", cls, grab)
		t.set_stylebox("grabber_highlight", cls, grab_h)
		t.set_stylebox("grabber_pressed", cls, grab_h)
	# Reiter
	t.set_stylebox("tab_selected", "TabContainer", tab_box(true))
	t.set_stylebox("tab_unselected", "TabContainer", tab_box(false))
	t.set_stylebox("tab_hovered", "TabContainer", tab_box(false, true))
	t.set_stylebox("panel", "TabContainer", inner_box())
	t.set_color("font_selected_color", "TabContainer", Color("#ffe6a0"))
	t.set_color("font_unselected_color", "TabContainer", Color("#b8a080"))
	t.set_color("font_hovered_color", "TabContainer", Color("#f0dcb0"))
	t.set_font("font", "TabContainer", font_bold)
	t.set_stylebox("tab_selected", "TabBar", tab_box(true))
	t.set_stylebox("tab_unselected", "TabBar", tab_box(false))
	t.set_stylebox("tab_hovered", "TabBar", tab_box(false, true))
	t.set_font("font", "TabBar", font_bold)
	t.set_color("font_selected_color", "TabBar", Color("#ffe6a0"))
	t.set_color("font_unselected_color", "TabBar", Color("#b8a080"))
	# Listen / Popups
	var pm := tooltip_box()
	t.set_stylebox("panel", "PopupMenu", pm)
	t.set_color("font_color", "PopupMenu", TEXT)
	t.set_color("font_hover_color", "PopupMenu", Color.WHITE)
	var hov := StyleBoxFlat.new()
	hov.bg_color = Color(0.6, 0.45, 0.2, 0.45)
	t.set_stylebox("hover", "PopupMenu", hov)
	t.set_stylebox("panel", "ItemList", inner_box())
	t.set_stylebox("selected", "ItemList", hov)
	t.set_stylebox("selected_focus", "ItemList", hov)
	t.set_color("font_color", "ItemList", TEXT)
	# Schieberegler
	var sl := StyleBoxFlat.new()
	sl.bg_color = Color(0, 0, 0, 0.6)
	sl.border_color = GOLD_DARK
	sl.set_border_width_all(1)
	sl.set_corner_radius_all(3)
	sl.content_margin_top = 3
	sl.content_margin_bottom = 3
	var slf := StyleBoxFlat.new()
	slf.bg_color = Color("#b08040")
	slf.set_corner_radius_all(3)
	t.set_stylebox("slider", "HSlider", sl)
	t.set_stylebox("grabber_area", "HSlider", slf)
	t.set_stylebox("grabber_area_highlight", "HSlider", slf)
	t.set_stylebox("panel", "ProgressBar", sl)


# ============================================================================== Texturen
static func _noise_img(w: int, h: int, c0: Color, c1: Color, seed_v: int, grain := 0.08) -> Image:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	var n := FastNoiseLite.new()
	n.seed = seed_v
	n.frequency = 0.06
	n.fractal_octaves = 4
	var n2 := FastNoiseLite.new()
	n2.seed = seed_v + 7
	n2.frequency = 0.35
	for y in h:
		for x in w:
			var v := n.get_noise_2d(x, y) * 0.5 + 0.5
			var g := n2.get_noise_2d(x, y) * grain
			var c := c0.lerp(c1, clampf(v, 0.0, 1.0))
			c = Color(clampf(c.r + g, 0, 1), clampf(c.g + g, 0, 1), clampf(c.b + g * 0.8, 0, 1), c.a)
			img.set_pixel(x, y, c)
	return img


static func _gold_frame(img: Image, border: int, dark := false) -> void:
	var w := img.get_width()
	var h := img.get_height()
	var g0 := Color("#4a3214") if not dark else Color("#2a2018")
	var g1 := Color("#f6dc96") if not dark else Color("#8a7a68")
	var g2 := Color("#a07a34") if not dark else Color("#4a4038")
	for y in h:
		for x in w:
			var d := mini(mini(x, y), mini(w - 1 - x, h - 1 - y))
			if d < border:
				var t := float(d) / border
				var c: Color
				if t < 0.25:
					c = g0
				elif t < 0.55:
					c = g1.lerp(g2, (t - 0.25) / 0.3)
				else:
					c = g2.lerp(g0, (t - 0.55) / 0.45)
				# Licht von oben links
				if x < y:
					c = c.darkened(0.12)
				var o := img.get_pixel(x, y)
				img.set_pixel(x, y, Color(c.r, c.g, c.b, maxf(o.a, 1.0)))
			elif d < border + 4:
				var o := img.get_pixel(x, y)
				img.set_pixel(x, y, o.darkened(0.35 * (1.0 - float(d - border) / 4.0)))
	# Ecknieten
	for cx in [border / 2 + 1, w - border / 2 - 2]:
		for cy in [border / 2 + 1, h - border / 2 - 2]:
			for yy in range(-3, 4):
				for xx in range(-3, 4):
					var r := sqrt(xx * xx + yy * yy)
					if r <= 3.0:
						var px: int = clampi(cx + xx, 0, w - 1)
						var py: int = clampi(cy + yy, 0, h - 1)
						var c := g1.lerp(g0, r / 3.0)
						img.set_pixel(px, py, c)


static func tex(key: String) -> ImageTexture:
	if _tex.has(key):
		return _tex[key]
	var img: Image
	match key:
		"frame":
			img = _noise_img(96, 96, Color("#2c2016"), Color("#130d08"), 11, 0.05)
			_gold_frame(img, 6)
		"frame_dark":
			img = _noise_img(96, 96, Color("#1a1612"), Color("#0a0806"), 13, 0.04)
			_gold_frame(img, 5, true)
		"inner":
			img = _noise_img(64, 64, Color("#16100b"), Color("#0b0705"), 17, 0.03)
			for y in 64:
				for x in 64:
					var d := mini(mini(x, y), mini(63 - x, 63 - y))
					if d < 2:
						img.set_pixel(x, y, Color("#5a4428") if d == 1 else Color("#2a1e10"))
		"parchment":
			img = _noise_img(128, 128, Color("#efe0b8"), Color("#c9ae7c"), 23, 0.04)
			for y in 128:
				for x in 128:
					var d := float(mini(mini(x, y), mini(127 - x, 127 - y)))
					if d < 14:
						img.set_pixel(x, y, img.get_pixel(x, y).darkened(0.35 * (1.0 - d / 14.0)))
		"button0", "button1", "button2", "button3":
			var s := int(key.substr(6))
			var top := [Color("#9a2a1a"), Color("#c03a22"), Color("#5a160c"), Color("#4a3a32")][s]
			var bot := [Color("#3a0c06"), Color("#5a1408"), Color("#2a0804"), Color("#2a2420")][s]
			img = Image.create(48, 28, false, Image.FORMAT_RGBA8)
			var nz := FastNoiseLite.new()
			nz.seed = 5
			nz.frequency = 0.2
			for y in 28:
				for x in 48:
					var c := top.lerp(bot, float(y) / 27.0)
					c = c.lightened(nz.get_noise_2d(x, y) * 0.06)
					if y < 12:
						c = c.lightened(0.08 * (1.0 - y / 12.0))
					img.set_pixel(x, y, c)
			_gold_frame(img, 3, s == 3)
		"tooltip":
			img = Image.create(32, 32, false, Image.FORMAT_RGBA8)
			for y in 32:
				for x in 32:
					var d := mini(mini(x, y), mini(31 - x, 31 - y))
					var c := Color(0.03, 0.03, 0.07, 0.95)
					if d < 2:
						c = Color("#9a8a6a") if d == 0 else Color("#4a4030")
					img.set_pixel(x, y, c)
		"slot":
			img = Image.create(40, 40, false, Image.FORMAT_RGBA8)
			for y in 40:
				for x in 40:
					var d := mini(mini(x, y), mini(39 - x, 39 - y))
					var c := Color(0.06, 0.05, 0.04, 0.92)
					if d < 2:
						c = Color("#5a4a32")
					elif d < 4:
						c = Color(0, 0, 0, 0.9)
					img.set_pixel(x, y, c)
		_:
			img = Image.create(8, 8, false, Image.FORMAT_RGBA8)
	var t := ImageTexture.create_from_image(img)
	_tex[key] = t
	return t


static func _tbox(key: String, margin: int, content: int) -> StyleBoxTexture:
	var sb := StyleBoxTexture.new()
	sb.texture = tex(key)
	sb.texture_margin_left = margin
	sb.texture_margin_right = margin
	sb.texture_margin_top = margin
	sb.texture_margin_bottom = margin
	sb.content_margin_left = content
	sb.content_margin_right = content
	sb.content_margin_top = content
	sb.content_margin_bottom = content
	sb.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	sb.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	return sb


static func frame_box() -> StyleBoxTexture:
	return _tbox("frame", 14, 14)


static func dark_box() -> StyleBoxTexture:
	return _tbox("frame_dark", 12, 10)


static func inner_box() -> StyleBoxTexture:
	return _tbox("inner", 4, 8)


static func parchment_box() -> StyleBoxTexture:
	var sb := _tbox("parchment", 20, 18)
	return sb


static func tooltip_box() -> StyleBoxTexture:
	return _tbox("tooltip", 4, 10)


static func slot_box() -> StyleBoxTexture:
	return _tbox("slot", 5, 3)


static func button_box(state: int) -> StyleBoxTexture:
	var sb := _tbox("button%d" % state, 6, 8)
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 5
	sb.content_margin_bottom = 6
	return sb


static func tab_box(selected: bool, hover := false) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("#3a2614") if selected else (Color("#2a1c10") if hover else Color("#1a120a"))
	sb.border_color = GOLD if selected else GOLD_DARK
	sb.set_border_width_all(2)
	sb.border_width_bottom = 0 if selected else 2
	sb.corner_radius_top_left = 6
	sb.corner_radius_top_right = 6
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	return sb


static func flat(bg: Color, border := Color(0, 0, 0, 0), bw := 0, radius := 3) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = border
	sb.set_border_width_all(bw)
	sb.set_corner_radius_all(radius)
	return sb


# ============================================================================== Hilfen für Bausteine
static func label(text: String, size := 17, color := TEXT, font: Font = null) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if font:
		l.add_theme_font_override("font", font)
	return l


static func title_label(text: String, size := 22) -> Label:
	var l := label(text, size, GOLD, font_title)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	l.add_theme_constant_override("outline_size", 4)
	return l


static func button(text: String, cb: Callable = Callable(), min_w := 0) -> Button:
	var b := Button.new()
	b.text = text
	if min_w > 0:
		b.custom_minimum_size.x = min_w
	if cb.is_valid():
		b.pressed.connect(cb)
	b.pressed.connect(func(): Sfx.play("click", -8.0))
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	return b


static func rich(text := "", fit := true) -> RichTextLabel:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.fit_content = fit
	r.scroll_active = not fit
	r.text = text
	r.selection_enabled = false
	r.mouse_filter = Control.MOUSE_FILTER_PASS
	return r


static func hbox(sep := 8) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", sep)
	return h


static func vbox(sep := 6) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", sep)
	return v


static func spacer(w := 0, h := 0) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(w, h)
	if w == 0 and h == 0:
		c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return c
