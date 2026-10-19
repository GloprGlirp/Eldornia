class_name ChatBox
extends Control
## Chatfenster mit Reitern, Kanälen (Sagen, Rufen, Gruppe, Schlachtzug, Gilde, Welt, Handel, Flüstern),
## anklickbaren Namen und Gegenstandslinks sowie Befehlsverlauf.

var hud
var tabs: TabBar
var chat_log: RichTextLabel
var input: LineEdit
var ch_label: Label
var input_row: HBoxContainer
var channel := "say"
var whisper_to := ""
var lines: Array = []          # [kind, bbcode]
var history: Array = []
var hist_i := -1
var _fade_t := 0.0

const CH_COLORS := {
	"say": "#ffffff", "yell": "#ff4040", "party": "#aaaaff", "raid": "#ff7f00", "guild": "#40ff40", "guild_sys": "#40ff40",
	"world": "#ffc0c0", "trade": "#ffc0c0", "lfg": "#ffc0c0", "whisper": "#ff80ff", "sys": "#ffff00", "err": "#ff4040",
	"npc": "#ffffa0", "emote": "#ff8040", "loot": "#00aa00", "xp": "#8080ff", "rep": "#8080ff", "skill": "#5555ff",
	"yell_npc": "#ff4040",
}
const CH_NAMES := {"say": "Sagen", "yell": "Rufen", "party": "Gruppe", "raid": "Schlachtzug", "guild": "Gilde", "world": "Welt",
	"trade": "Handel", "lfg": "Suche", "whisper": "Flüstern"}
const TABS := [["Allgemein", []], ["Gruppe", ["party", "raid"]], ["Gilde", ["guild", "guild_sys"]],
	["Handel", ["world", "trade", "lfg"]], ["Flüstern", ["whisper"]], ["Kampf & Beute", ["loot", "xp", "rep", "skill"]]]
const PREFIX := {"/s ": "say", "/sagen ": "say", "/y ": "yell", "/rufen ": "yell", "/p ": "party", "/gruppe ": "party",
	"/ra ": "raid", "/g ": "guild", "/gilde ": "guild", "/1 ": "world", "/welt ": "world", "/2 ": "trade", "/handel ": "trade",
	"/4 ": "lfg", "/suche ": "lfg"}


func _init(p_hud) -> void:
	hud = p_hud
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	var v := UiSkin.vbox(0)
	v.set_anchors_preset(Control.PRESET_FULL_RECT)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(v)
	tabs = TabBar.new()
	for t in TABS:
		tabs.add_tab(t[0])
	tabs.add_theme_font_size_override("font_size", 13)
	tabs.tab_changed.connect(func(_i): _rerender())
	tabs.clip_tabs = true
	v.add_child(tabs)
	var bg := PanelContainer.new()
	bg.add_theme_stylebox_override("panel", UiSkin.flat(Color(0, 0, 0, 0.35), Color(0, 0, 0, 0), 0, 4))
	bg.size_flags_vertical = Control.SIZE_EXPAND_FILL
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(bg)
	chat_log = RichTextLabel.new()
	chat_log.bbcode_enabled = true
	chat_log.scroll_following = true
	chat_log.selection_enabled = false
	chat_log.add_theme_font_size_override("normal_font_size", 15)
	chat_log.add_theme_font_size_override("bold_font_size", 15)
	chat_log.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 1))
	chat_log.add_theme_constant_override("shadow_offset_x", 1)
	chat_log.add_theme_constant_override("shadow_offset_y", 1)
	chat_log.meta_clicked.connect(_on_meta)
	chat_log.mouse_filter = Control.MOUSE_FILTER_PASS
	bg.add_child(chat_log)
	input_row = UiSkin.hbox(4)
	input_row.visible = false
	v.add_child(input_row)
	ch_label = UiSkin.label("Sagen:", 15, Color.WHITE, UiSkin.font_bold)
	input_row.add_child(ch_label)
	input = LineEdit.new()
	input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	input.max_length = 255
	input.add_theme_font_size_override("font_size", 15)
	input.text_submitted.connect(_on_submit)
	input.text_changed.connect(_on_changed)
	input.gui_input.connect(_on_input_key)
	input.focus_exited.connect(func():
		if input.text == "":
			input_row.visible = false
	)
	input_row.add_child(input)
	Game.chat_line.connect(_on_chat)
	add_line("sys", "", "Willkommen in Eldornia! Drückt [b]H[/b] für die Sammlung, [b]Esc[/b] für das Menü und [b]/hilfe[/b] für Chatbefehle.")


func focus_input(prefill := "") -> void:
	input_row.visible = true
	input.text = prefill
	_update_label()
	input.grab_focus()
	input.caret_column = input.text.length()


func start_whisper(name: String) -> void:
	channel = "whisper"
	whisper_to = name
	focus_input()


func _update_label() -> void:
	var c: String = CH_COLORS.get(channel, "#ffffff")
	if channel == "whisper":
		ch_label.text = "An %s:" % whisper_to
	else:
		ch_label.text = "%s:" % CH_NAMES.get(channel, channel)
	ch_label.add_theme_color_override("font_color", Color.html(c))


func _on_changed(t: String) -> void:
	var low := t.to_lower()
	for p in PREFIX:
		if low == p:
			channel = PREFIX[p]
			input.text = ""
			_update_label()
			return
	if low.begins_with("/w ") or low.begins_with("/fl "):
		var rest := t.substr(t.find(" ") + 1)
		if rest.ends_with(" ") and rest.strip_edges() != "" and not rest.strip_edges().contains(" "):
			channel = "whisper"
			whisper_to = rest.strip_edges()
			input.text = ""
			_update_label()
	elif low == "/r " and _last_whisper() != "":
		channel = "whisper"
		whisper_to = _last_whisper()
		input.text = ""
		_update_label()


var _last_whisper_from := ""


func _last_whisper() -> String:
	return _last_whisper_from


func _on_input_key(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed:
		if ev.keycode == KEY_ESCAPE:
			input.text = ""
			input.release_focus()
			input_row.visible = false
			input.accept_event()
		elif ev.keycode == KEY_UP and not history.is_empty():
			hist_i = clampi(hist_i - 1 if hist_i >= 0 else history.size() - 1, 0, history.size() - 1)
			input.text = history[hist_i]
			input.caret_column = input.text.length()
			input.accept_event()
		elif ev.keycode == KEY_DOWN and not history.is_empty() and hist_i >= 0:
			hist_i = mini(hist_i + 1, history.size())
			input.text = history[hist_i] if hist_i < history.size() else ""
			input.accept_event()


func _on_submit(t: String) -> void:
	t = t.strip_edges()
	input.text = ""
	input.release_focus()
	input_row.visible = false
	hist_i = -1
	if t == "":
		return
	history.append(t)
	if history.size() > 30:
		history.pop_front()
	if t.begins_with("/"):
		if _local_command(t):
			return
		Game.send({"t": "chat", "text": t})
		return
	var m := {"t": "chat", "ch": channel, "text": t}
	if channel == "whisper":
		m["to"] = whisper_to
	Game.send(m)


func _local_command(t: String) -> bool:
	var parts := t.substr(1).split(" ", false, 1)
	if parts.is_empty():
		return false
	var cmd := parts[0].to_lower()
	var arg := parts[1] if parts.size() > 1 else ""
	match cmd:
		"sitzen", "sit":
			Game.send({"t": "sit"})
		"verlassen" when Game.zone_inst:
			Game.send({"t": "leave_instance"})
		"freund":
			Game.send({"t": "friend_add", "name": arg})
		"ignorieren", "ignore":
			Game.send({"t": "friend_add", "name": arg, "ignore": true})
		"gildegründen":
			var a := arg.split(" ", false, 1)
			if a.size() == 2:
				Game.send({"t": "guild_create", "tag": a[0], "name": a[1]})
		"ginvite", "gildeeinladen":
			Game.send({"t": "guild_invite", "name": arg})
		"glocken", "gquit":
			Game.send({"t": "guild_leave"})
		"motd":
			Game.send({"t": "guild_motd", "text": arg})
		"einstellungen", "optionen":
			hud.open_window("einstellungen")
		"hilfe", "help":
			hud.open_window("hilfe")
			return false
		"ruhestein", "heim":
			Game.send({"t": "hearth"})
		"schlachtzug", "raid":
			Game.send({"t": "party_raid"})
		"abmelden", "logout":
			hud.world.leave_requested.emit()
		_:
			return false
	return true


func _on_chat(ch: String, from: String, text: String, extra: Dictionary) -> void:
	if ch == "whisper" and not extra.get("out", false):
		_last_whisper_from = from
		Sfx.play("whisper", -6.0)
	if ch in ["say", "yell", "npc"] and extra.get("fid") and ch == "npc":
		var e = hud.world.ent(int(extra["fid"]))
		if e:
			hud.bubble(e, text)
	if ch == "yell" and extra.get("fid") and not extra.has("cls"):
		var e2 = hud.world.ent(int(extra["fid"]))
		if e2:
			hud.bubble(e2, text)
		hud.raid_warning("%s ruft: %s" % [from, text], Color(1.0, 0.3, 0.2))
	add_line(ch, from, text, extra)


func add_line(kind: String, from: String, text: String, extra: Dictionary = {}) -> void:
	var col: String = CH_COLORS.get(kind, "#ffffff")
	var safe := text.replace("[", "⟦").replace("]", "⟧") if kind not in ["sys", "err", "loot", "xp", "rep", "skill", "guild_sys"] else text
	var who := ""
	if from != "":
		var ncol := col
		if extra.has("cls"):
			ncol = "#" + Content.class_color(str(extra["cls"])).to_html(false)
		var gm := "[color=#00b4ff]<GM>[/color] " if extra.get("gm", false) else ""
		who = "%s[url=p:%s][color=%s]%s[/color][/url]" % [gm, from, ncol, from]
	var line := ""
	var ts := Time.get_time_string_from_system().substr(0, 5)
	match kind:
		"say", "npc":
			line = "%s sagt: %s" % [who, safe]
		"yell":
			line = "%s ruft: %s" % [who, safe]
		"party":
			line = "[Gruppe] %s: %s" % [who, safe]
		"raid":
			line = "[Schlachtzug] %s: %s" % [who, safe]
		"guild":
			line = "[Gilde] %s: %s" % [who, safe]
		"world":
			line = "[1. Welt] %s: %s" % [who, safe]
		"trade":
			line = "[2. Handel] %s: %s" % [who, safe]
		"lfg":
			line = "[4. Suche] %s: %s" % [who, safe]
		"whisper":
			if extra.get("out", false):
				line = "An [url=p:%s]%s[/url]: %s" % [str(extra.get("to", "")), str(extra.get("to", "")), safe]
			else:
				line = "%s flüstert: %s" % [who, safe]
		"emote":
			line = safe
		"loot":
			var q := int(extra.get("q", 1))
			var iid := str(extra.get("i", ""))
			var rc: String = Content.RARITY_COLORS[clampi(q, 0, 6)]
			line = safe
			var a := line.find("[")
			var b := line.find("]", a)
			if a >= 0 and b > a:
				line = line.substr(0, a) + "[url=i:%s][color=%s]%s[/color][/url]" % [iid, rc, line.substr(a, b - a + 1).replace("[", "⟦").replace("]", "⟧")] + line.substr(b + 1)
		_:
			line = safe
	var bb := "[color=#888]%s[/color] [color=%s]%s[/color]" % [ts, col, line]
	lines.append([kind, bb])
	if lines.size() > 400:
		lines = lines.slice(lines.size() - 300)
		_rerender()
		return
	if _visible_in_tab(kind):
		chat_log.append_text(bb + "\n")


func _visible_in_tab(kind: String) -> bool:
	var i := tabs.current_tab if tabs else 0
	var filt: Array = TABS[i][1]
	if filt.is_empty():
		return not kind in ["xp"] or true
	if kind in ["sys", "err"] and i != 5:
		return true
	return kind in filt


func _rerender() -> void:
	chat_log.clear()
	for l in lines:
		if _visible_in_tab(l[0]):
			chat_log.append_text(l[1] + "\n")


func _on_meta(meta) -> void:
	var s := str(meta)
	if s.begins_with("p:"):
		start_whisper(s.substr(2))
	elif s.begins_with("i:"):
		var iid := s.substr(2)
		var p := Tips.panel(Tips.item_bb(iid, null, true), 300)
		p.position = get_global_mouse_position() + Vector2(10, -200)
		p.mouse_filter = Control.MOUSE_FILTER_STOP
		hud.add_child(p)
		p.gui_input.connect(func(ev):
			if ev is InputEventMouseButton and ev.pressed:
				p.queue_free()
		)
		get_tree().create_timer(6.0).timeout.connect(func():
			if is_instance_valid(p):
				p.queue_free()
		)


func _process(delta: float) -> void:
	# Chat blendet bei Untätigkeit leicht aus (wie in WoW)
	var hover := get_global_rect().has_point(get_global_mouse_position())
	if hover or input_row.visible:
		_fade_t = 0.0
	else:
		_fade_t += delta
	var target_a := 1.0 if _fade_t < 12.0 else 0.65
	modulate.a = lerpf(modulate.a, target_a, clampf(delta * 3.0, 0.0, 1.0))
	tabs.modulate.a = 1.0 if hover else 0.35
