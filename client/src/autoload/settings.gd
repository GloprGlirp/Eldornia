extends Node
## Einstellungen (Server, Grafik, Audio, Tastenbelegung) – gespeichert in user://einstellungen.cfg

signal changed

const PATH := "user://einstellungen.cfg"
const DEFAULT_SERVER := "https://eldornia.onrender.com"

## Standard-Tastenbelegung (GDD 4: WASD, Maus, 1–6, Leertaste, E, I, M, J, G – konfigurierbar)
const DEFAULT_KEYS := {
	"vor": [KEY_W, KEY_UP], "zurueck": [KEY_S, KEY_DOWN], "links": [KEY_A], "rechts": [KEY_D],
	"links_seit": [KEY_Q], "rechts_seit": [KEY_R], "springen": [KEY_SPACE], "laufen_auto": [KEY_NUMLOCK],
	"sprinten": [KEY_SHIFT], "interagieren": [KEY_E, KEY_F], "ziel_naechstes": [KEY_TAB], "ziel_selbst": [KEY_F1],
	"ziel_freund": [KEY_F2], "ziel_loeschen": [KEY_ESCAPE],
	"aktion_1": [KEY_1], "aktion_2": [KEY_2], "aktion_3": [KEY_3], "aktion_4": [KEY_4], "aktion_5": [KEY_5],
	"aktion_6": [KEY_6], "aktion_7": [KEY_7], "aktion_8": [KEY_8], "aktion_9": [KEY_9], "aktion_10": [KEY_0],
	"aktion_11": [KEY_MINUS, 223], "aktion_12": [KEY_EQUAL, 180],
	"leiste2_1": [KEY_Z], "leiste2_2": [KEY_X], "leiste2_3": [KEY_C], "leiste2_4": [KEY_V], "leiste2_5": [KEY_T],
	"leiste2_6": [KEY_CAPSLOCK],
	"inventar": [KEY_I, KEY_B], "charakter": [KEY_K], "zauberbuch": [KEY_P], "talente": [KEY_N], "questlog": [KEY_J, KEY_L],
	"karte": [KEY_M], "gilde": [KEY_G], "berufe": [KEY_U], "erfolge": [KEY_Y], "sammlung": [KEY_H],
	"gruppensuche": [KEY_O], "soziales": [KEY_SEMICOLON], "reiten": [KEY_APOSTROPHE], "chat": [KEY_ENTER],
	"chat_befehl": [KEY_SLASH], "ui_umschalten": [KEY_F12], "screenshot": [KEY_PRINT],
}
const ACTION_NAMES := {
	"vor": "Vorwärts", "zurueck": "Rückwärts", "links": "Links drehen", "rechts": "Rechts drehen",
	"links_seit": "Seitwärts links", "rechts_seit": "Seitwärts rechts", "springen": "Springen / Ausweichen",
	"laufen_auto": "Automatisch laufen", "sprinten": "Sprinten", "interagieren": "Interagieren",
	"ziel_naechstes": "Nächstes Ziel (Feind)", "ziel_selbst": "Sich selbst anvisieren", "ziel_freund": "Nächster Verbündeter",
	"ziel_loeschen": "Ziel löschen / Menü", "inventar": "Inventar", "charakter": "Charakter", "zauberbuch": "Zauberbuch",
	"talente": "Talente", "questlog": "Questlog", "karte": "Weltkarte", "gilde": "Gilde", "berufe": "Berufe",
	"erfolge": "Erfolge", "sammlung": "Sammlung", "gruppensuche": "Gruppenfinder", "soziales": "Soziales",
	"reiten": "Reittier rufen", "chat": "Chat öffnen", "chat_befehl": "Chatbefehl", "ui_umschalten": "Oberfläche ein/aus",
	"screenshot": "Bildschirmfoto",
}

var server := DEFAULT_SERVER
var username := ""
var remember := true
var quality := 2            # 0 niedrig, 1 mittel, 2 hoch, 3 ultra
var view_distance := 1.0
var shadows := true
var ssao := true
var grass := true
var vsync := true
var fullscreen := false
var ui_scale := 1.0
var vol_master := 0.8
var vol_music := 0.5
var vol_sfx := 0.8
var mouse_sens := 1.0
var invert_y := false
var show_fct := true
var show_nameplates := true
var show_friendly_plates := true
var target_assist := true      # optionale Zielerfassung (GDD 4)
var click_to_move := false
var keys: Dictionary = {}


func _ready() -> void:
	keys = DEFAULT_KEYS.duplicate(true)
	if OS.has_feature("web"):
		var origin = JavaScriptBridge.eval("window.location.origin")
		if origin is String and origin.begins_with("http"):
			server = origin
	load_settings()
	apply()


func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) != OK:
		return
	server = cfg.get_value("netz", "server", server)
	if OS.has_feature("web"):
		var origin = JavaScriptBridge.eval("window.location.origin")
		if origin is String and origin.begins_with("http"):
			server = origin
	username = cfg.get_value("netz", "benutzer", "")
	remember = cfg.get_value("netz", "merken", true)
	quality = cfg.get_value("grafik", "qualitaet", quality)
	view_distance = cfg.get_value("grafik", "sichtweite", view_distance)
	shadows = cfg.get_value("grafik", "schatten", shadows)
	ssao = cfg.get_value("grafik", "ssao", ssao)
	grass = cfg.get_value("grafik", "gras", grass)
	vsync = cfg.get_value("grafik", "vsync", vsync)
	fullscreen = cfg.get_value("grafik", "vollbild", fullscreen)
	ui_scale = cfg.get_value("grafik", "ui_skalierung", ui_scale)
	vol_master = cfg.get_value("audio", "gesamt", vol_master)
	vol_music = cfg.get_value("audio", "musik", vol_music)
	vol_sfx = cfg.get_value("audio", "effekte", vol_sfx)
	mouse_sens = cfg.get_value("steuerung", "maus", mouse_sens)
	invert_y = cfg.get_value("steuerung", "invertieren", invert_y)
	target_assist = cfg.get_value("steuerung", "zielhilfe", target_assist)
	show_fct = cfg.get_value("anzeige", "kampftext", show_fct)
	show_nameplates = cfg.get_value("anzeige", "namensplaketten", show_nameplates)
	show_friendly_plates = cfg.get_value("anzeige", "freundliche_plaketten", show_friendly_plates)
	var saved: Dictionary = cfg.get_value("steuerung", "tasten", {})
	for k in saved:
		if keys.has(k):
			keys[k] = saved[k]


func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("netz", "server", server)
	cfg.set_value("netz", "benutzer", username if remember else "")
	cfg.set_value("netz", "merken", remember)
	cfg.set_value("grafik", "qualitaet", quality)
	cfg.set_value("grafik", "sichtweite", view_distance)
	cfg.set_value("grafik", "schatten", shadows)
	cfg.set_value("grafik", "ssao", ssao)
	cfg.set_value("grafik", "gras", grass)
	cfg.set_value("grafik", "vsync", vsync)
	cfg.set_value("grafik", "vollbild", fullscreen)
	cfg.set_value("grafik", "ui_skalierung", ui_scale)
	cfg.set_value("audio", "gesamt", vol_master)
	cfg.set_value("audio", "musik", vol_music)
	cfg.set_value("audio", "effekte", vol_sfx)
	cfg.set_value("steuerung", "maus", mouse_sens)
	cfg.set_value("steuerung", "invertieren", invert_y)
	cfg.set_value("steuerung", "zielhilfe", target_assist)
	cfg.set_value("steuerung", "tasten", keys)
	cfg.set_value("anzeige", "kampftext", show_fct)
	cfg.set_value("anzeige", "namensplaketten", show_nameplates)
	cfg.set_value("anzeige", "freundliche_plaketten", show_friendly_plates)
	cfg.save(PATH)


func apply() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	if not OS.has_feature("web"):
		var mode := DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED
		if DisplayServer.window_get_mode() != mode and DisplayServer.get_name() != "headless":
			DisplayServer.window_set_mode(mode)
	if get_tree() and get_tree().root:
		get_tree().root.content_scale_factor = ui_scale
	_apply_audio()
	changed.emit()


func _apply_audio() -> void:
	var master := AudioServer.get_bus_index("Master")
	AudioServer.set_bus_volume_db(master, linear_to_db(maxf(0.001, vol_master)))


## Liefert true, wenn das Ereignis zur Aktion passt.
func is_action(ev: InputEvent, action: String) -> bool:
	if not (ev is InputEventKey):
		return false
	var k: int = ev.keycode if ev.keycode != 0 else ev.physical_keycode
	for code in keys.get(action, []):
		if int(code) == k:
			return true
		if int(code) == KEY_SHIFT and ev.keycode == KEY_SHIFT:
			return true
	return false


func key_pressed(action: String) -> bool:
	for code in keys.get(action, []):
		if Input.is_key_pressed(int(code)):
			return true
	return false


func key_label(action: String) -> String:
	var arr: Array = keys.get(action, [])
	if arr.is_empty():
		return ""
	var s := OS.get_keycode_string(int(arr[0]))
	return s.replace("Shift", "⇧").replace("Minus", "ß").replace("Equal", "´")


func short_key_label(action: String) -> String:
	var s := key_label(action)
	if s.length() > 3:
		s = s.substr(0, 3)
	return s
