class_name LoadingScreen
extends Control
## Ladebildschirm mit Regionsbild-Stimmung, Tipp und Fortschrittsbalken.

const TIPS := [
	"Halte die rechte Maustaste gedrückt, um Kamera und Charakter zu drehen. Beide Maustasten zusammen lassen dich laufen.",
	"Mit Tab wählst du den nächsten Gegner vor dir aus.",
	"Bodenmarkierungen kündigen gefährliche Bossangriffe an – geh rechtzeitig aus der markierten Fläche!",
	"Unterbrich gefährliche Zauber mit Fähigkeiten wie Schildschlag, Gegenzauber oder Tritt.",
	"Iss und trink nach dem Kampf, um schneller Gesundheit und Mana zu regenerieren.",
	"Simon der zweiäugige Herrscher sieht alles. Mit beiden Augen. Gleichzeitig.",
	"Der Gaukelkobold verkauft Tränke – fast nie verflucht.",
	"In Dungeons gibt es persönliche Beute: Jeder würfelt für sich selbst.",
	"Teleportationssteine verbinden die Regionen. Berühre jeden Stein einmal, um ihn freizuschalten.",
	"Berufe lernst du bei den Lehrern in Eichenau. Sammler und Handwerker sind auf dem Marktplatz gefragt.",
	"Heroische und mythische Dungeons bringen bessere Beute – aber die Gegner sind deutlich stärker.",
	"Ein Druide in Bärengestalt kann eine Gruppe ebenso gut beschützen wie ein Ritter.",
	"Der Blinde sieht mehr, als du denkst.",
	"Talentpunkte bekommst du ab Stufe 10 – öffne das Talentfenster mit N.",
]
const MOODS := {
	"gruenmark": ["#2a4a1a", "#9ac060"], "frostklamm": ["#1a2a4a", "#c0d8f0"], "mondhain": ["#1a1a4a", "#a080f0"],
	"aschenlande": ["#3a1008", "#ff7a30"], "himmelsbruch": ["#1a2a5a", "#f0e0a0"],
}

var bg: ColorRect
var title: Label
var text: Label
var tip: Label
var bar: StatBar
var _p := 0.0
var _fading := false
var _mat: ShaderMaterial


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	bg = ColorRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_mat = ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = """shader_type canvas_item;
uniform vec4 c0 : source_color = vec4(0.1, 0.08, 0.05, 1.0);
uniform vec4 c1 : source_color = vec4(0.6, 0.45, 0.2, 1.0);
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f*f*(3.0-2.0*f);
 return mix(mix(hash(i), hash(i+vec2(1,0)), f.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), f.x), f.y); }
void fragment(){
 vec2 uv = UV;
 float n = 0.0; float a = 0.5; vec2 p = uv * 4.0 + vec2(TIME * 0.02, 0.0);
 for (int i = 0; i < 5; i++){ n += noise(p) * a; p *= 2.0; a *= 0.5; }
 float glow = smoothstep(0.9, 0.0, distance(uv, vec2(0.5, 0.42)));
 vec3 col = mix(c0.rgb, c1.rgb, n * 0.55 + glow * 0.45);
 col *= 1.0 - smoothstep(0.35, 0.95, distance(uv, vec2(0.5)));
 COLOR = vec4(col, 1.0);
}"""
	_mat.shader = sh
	bg.material = _mat
	add_child(bg)
	title = UiSkin.title_label("ELDORNIA", 64)
	title.add_theme_font_override("font", UiSkin.font_deco)
	title.set_anchors_preset(Control.PRESET_CENTER)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.position = Vector2(-500, -170)
	title.size = Vector2(1000, 100)
	add_child(title)
	text = UiSkin.label("", 22, UiSkin.TEXT, UiSkin.font_title)
	text.set_anchors_preset(Control.PRESET_CENTER)
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	text.position = Vector2(-500, -40)
	text.size = Vector2(1000, 40)
	add_child(text)
	bar = StatBar.new(Color("#c8a040"), 18)
	bar.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	bar.position = Vector2(-300, -120)
	bar.size = Vector2(600, 18)
	bar.show_text = false
	add_child(bar)
	tip = UiSkin.label("Tipp: " + TIPS[randi() % TIPS.size()], 17, Color("#e8dcc0"), UiSkin.font_italic)
	tip.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tip.position = Vector2(-450, -90)
	tip.size = Vector2(900, 60)
	add_child(tip)


func set_text(t: String) -> void:
	if text:
		text.text = t


func set_zone(zid: String) -> void:
	var m: Array = MOODS.get(zid, ["#1a1410", "#8a6a3a"])
	if _mat:
		_mat.set_shader_parameter("c0", Color.html(m[0]).darkened(0.4))
		_mat.set_shader_parameter("c1", Color.html(m[1]).darkened(0.25))
	var z: Dictionary = Content.defs.get("zones", {}).get(zid, {})
	if title and z.has("name"):
		title.text = str(z["name"])


func _process(delta: float) -> void:
	if not _fading:
		_p = minf(0.92, _p + delta * 0.35 * (1.0 - _p))
		bar.set_values(_p, 1.0)


func fade_out() -> void:
	_fading = true
	bar.set_values(1.0, 1.0)
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.6)
	tw.tween_callback(queue_free)
