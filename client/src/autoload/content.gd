extends Node
## Spielinhalte vom Server (Klassen, Fähigkeiten, Talente, Gegenstände) und gemalte Symbole.
## Symbole: game-icons.net (Lorc, Delapouite & Mitwirkende), CC BY 3.0.

signal loaded

var defs: Dictionary = {}
var items: Dictionary = {}
var ready_ok := false
var _icon_paths: Dictionary = {}
var _icon_cache: Dictionary = {}

const RARITY_COLORS := ["#9d9d9d", "#ffffff", "#1eff00", "#0070dd", "#a335ee", "#ff8000", "#2ee6d6"]
const RARITY_NAMES := ["Schlecht", "Gewöhnlich", "Ungewöhnlich", "Selten", "Episch", "Legendär", "Mythisch"]
const SCHOOL_BG := {
	"physical": ["#8a6a4a", "#2a1a10"], "fire": ["#ff7a20", "#5a1000"], "frost": ["#7fd0ff", "#0a2a5a"],
	"arcane": ["#d58cff", "#2a0a4a"], "nature": ["#8ad04a", "#0a3a10"], "shadow": ["#9a5ad0", "#140a24"],
	"holy": ["#ffe080", "#5a4010"], "blood": ["#e04040", "#3a0808"],
}
const CLASS_COLORS := {
	"ritter": "#C79C6E", "magier": "#69CCF0", "raeuber": "#FFF569", "samurai": "#E05050", "bogenschuetze": "#ABD473",
	"barbar": "#A0522D", "druide": "#FF7D0A", "totenbeschwoerer": "#9482C9",
}
const POWER_COLORS := {
	"mana": "#2f6cff", "resolve": "#d8b048", "rage": "#c4161b", "energy": "#f0dc40", "focus": "#ff8a2a",
	"concentration": "#6ac040",
}
const POWER_NAMES := {
	"mana": "Mana", "resolve": "Entschlossenheit", "rage": "Wut", "energy": "Energie", "focus": "Fokus",
	"concentration": "Konzentration",
}


func _ready() -> void:
	var f := FileAccess.open("res://assets/icons.json", FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			_icon_paths = d


func fetch(callback: Callable) -> void:
	Net.get_json("/api/content", func(ok: bool, code: int, data):
		if ok and data is Dictionary:
			defs = data
			for k in data.get("start_items", {}):
				items[k] = data["start_items"][k]
			ready_ok = true
			loaded.emit()
		callback.call(ok, code, data)
	)


func add_items(d) -> void:
	if d is Dictionary:
		for k in d:
			items[k] = d[k]


func item(id: String) -> Dictionary:
	return items.get(id, {})


func cls(id: String) -> Dictionary:
	return defs.get("classes", {}).get(id, {})


func class_name_of(id: String) -> String:
	return str(cls(id).get("name", id.capitalize()))


func rarity_color(q: int) -> Color:
	return Color.html(RARITY_COLORS[clampi(q, 0, 6)])


func class_color(id: String) -> Color:
	return Color.html(CLASS_COLORS.get(id, "#ffffff"))


func power_color(pt: String) -> Color:
	return Color.html(POWER_COLORS.get(pt, "#2f6cff"))


static func money(copper: int, short := false) -> String:
	var g := int(copper / 10000)
	var s := int((copper % 10000) / 100)
	var c := int(copper % 100)
	var parts: Array = []
	if g > 0:
		parts.append("%d%s" % [g, "g" if short else " Gold"])
	if s > 0:
		parts.append("%d%s" % [s, "s" if short else " Silber"])
	if c > 0 or parts.is_empty():
		parts.append("%d%s" % [c, "k" if short else " Kupfer"])
	return " ".join(parts)


static func money_bb(copper: int) -> String:
	var g := int(copper / 10000)
	var s := int((copper % 10000) / 100)
	var c := int(copper % 100)
	var out := ""
	if g > 0:
		out += "[color=#ffd700]%d●[/color] " % g
	if s > 0 or g > 0:
		out += "[color=#d8d8e0]%d●[/color] " % s
	out += "[color=#d0884a]%d●[/color]" % c
	return out


static func fmt_time(sec: float) -> String:
	sec = maxf(0.0, sec)
	if sec >= 86400:
		return "%d T" % int(sec / 86400)
	if sec >= 3600:
		return "%d Std" % int(sec / 3600)
	if sec >= 60:
		return "%d Min" % int(ceil(sec / 60))
	if sec >= 10:
		return "%d" % int(sec)
	return "%.1f" % sec


# ============================================================================== Symbole
## Liefert ein gemaltes Symbol (Glyphe von game-icons.net auf farbigem, gemaltem Hintergrund).
func icon(name: String, bg := Color(0.45, 0.32, 0.2), size := 64, fg := Color(1, 0.96, 0.86)) -> Texture2D:
	var key := "%s|%s|%d|%s" % [name, bg.to_html(), size, fg.to_html()]
	if _icon_cache.has(key):
		return _icon_cache[key]
	var img := _render_icon(name, bg, size, fg)
	var tex := ImageTexture.create_from_image(img)
	_icon_cache[key] = tex
	return tex


func ability_icon(ab: Dictionary, size := 64) -> Texture2D:
	var sc: Array = SCHOOL_BG.get(str(ab.get("school", "physical")), SCHOOL_BG["physical"])
	return icon(str(ab.get("icon", "sword-wound")), Color.html(sc[0]).lerp(Color.html(sc[1]), 0.35), size)


func item_icon(it: Dictionary, size := 64) -> Texture2D:
	var q := int(it.get("q", 1))
	var base := Color(0.33, 0.27, 0.2)
	var vis: Dictionary = it.get("vis", {})
	if vis.has("c"):
		base = Color.html(str(vis["c"])).lerp(base, 0.55)
	elif vis.has("m"):
		base = Color.html(str(vis["m"])).lerp(base, 0.6)
	if q >= 4:
		base = base.lerp(rarity_color(q), 0.35)
	return icon(str(it.get("icon", "swap-bag")), base, size)


func _glyph(name: String, px: int) -> Image:
	var paths: Array = _icon_paths.get(name, _icon_paths.get("swap-bag", []))
	if paths.is_empty():
		var empty := Image.create(px, px, false, Image.FORMAT_RGBA8)
		return empty
	var svg := "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 512 512\" width=\"512\" height=\"512\">"
	for d in paths:
		svg += "<path fill=\"#ffffff\" d=\"%s\"/>" % d
	svg += "</svg>"
	var img := Image.new()
	var err := img.load_svg_from_string(svg, float(px) / 512.0)
	if err != OK:
		img = Image.create(px, px, false, Image.FORMAT_RGBA8)
	img.convert(Image.FORMAT_RGBA8)
	return img


func _render_icon(name: String, bg: Color, size: int, fg: Color) -> Image:
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var inner := int(size * 0.8)
	var off := int((size - inner) / 2)
	var g := _glyph(name, inner)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(name)
	var hl := bg.lightened(0.45)
	var dk := bg.darkened(0.65)
	# gemalter Hintergrund: Verlauf + weiche Flecken
	var blobs: Array = []
	for i in 5:
		blobs.append([rng.randf() * size, rng.randf() * size, rng.randf_range(size * 0.2, size * 0.5), rng.randf_range(-0.18, 0.18)])
	for y in size:
		for x in size:
			var u := float(x) / size
			var v := float(y) / size
			var t := clampf(0.15 + v * 0.75 - u * 0.2, 0.0, 1.0)
			var c := hl.lerp(dk, t)
			for b in blobs:
				var d := Vector2(x - b[0], y - b[1]).length() / b[2]
				if d < 1.0:
					c = c.lightened(b[3] * (1.0 - d)) if b[3] > 0 else c.darkened(-b[3] * (1.0 - d))
			var r := Vector2(u - 0.5, v - 0.5).length()
			c = c.darkened(clampf((r - 0.32) * 1.6, 0.0, 0.6))
			img.set_pixel(x, y, Color(c.r, c.g, c.b, 1.0))
	# Glyphe mit Schatten und Lichtkante
	var gw := g.get_width()
	for y in gw:
		for x in gw:
			var a := g.get_pixel(x, y).a
			var sx := x + off + 2
			var sy := y + off + 2
			if a > 0.01 and sx < size and sy < size:
				var sc := img.get_pixel(sx, sy)
				img.set_pixel(sx, sy, sc.lerp(Color(0, 0, 0), a * 0.55))
	for y in gw:
		for x in gw:
			var a := g.get_pixel(x, y).a
			if a <= 0.01:
				continue
			var px := x + off
			var py := y + off
			var top := 1.0 - float(y) / gw
			var col := fg.lerp(fg.darkened(0.3), 1.0 - top)
			var up := g.get_pixel(x, maxi(0, y - 1)).a
			if up < 0.3:
				col = col.lightened(0.25)
			var dc := img.get_pixel(px, py)
			img.set_pixel(px, py, dc.lerp(col, a))
	# Rahmen (abgeschrägte Kante)
	for i in size:
		for k in 2:
			var e := 0.35 if k == 0 else 0.15
			_tint(img, i, k, Color(1, 1, 1), e * 0.6)
			_tint(img, k, i, Color(1, 1, 1), e * 0.4)
			_tint(img, i, size - 1 - k, Color(0, 0, 0), e * 1.5)
			_tint(img, size - 1 - k, i, Color(0, 0, 0), e * 1.5)
	return img


func _tint(img: Image, x: int, y: int, c: Color, amt: float) -> void:
	var o := img.get_pixel(x, y)
	img.set_pixel(x, y, o.lerp(c, clampf(amt, 0.0, 1.0)))
