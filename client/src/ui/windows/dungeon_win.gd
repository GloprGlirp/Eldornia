class_name DungeonWin
extends Win
## Auswahl des Schwierigkeitsgrads am Dungeoneingang (Normal / Heroisch / Mythisch mit Affixen) und Sperren.

var hud
var info: RichTextLabel
var modes: VBoxContainer


func _init(p_hud) -> void:
	super("Dungeon", "dungeon", Vector2(460, 360))
	hud = p_hud


func _ready() -> void:
	info = UiSkin.rich("")
	body.add_child(info)
	modes = UiSkin.vbox(8)
	body.add_child(modes)


func show_select(m: Dictionary) -> void:
	center()
	title_label.text = str(m.get("name", "Dungeon"))
	var lv = m.get("levels")
	var s := "[center]"
	if lv is Array and lv.size() >= 2:
		s += "Stufe %d–%d" % [int(lv[0]), int(lv[1])]
	if str(m.get("players", "")) != "":
		s += "  ·  %s" % m["players"]
	s += "[/center]"
	var locks: Array = m.get("locks", [])
	if not locks.is_empty():
		s += "\n[color=#ff8060]Bereits besiegt (keine Beute bis zur Rücksetzung):[/color]"
		for l in locks:
			s += "\n • %s (%s) – noch %s" % [l.get("boss", ""), l.get("mode", ""), Content.fmt_time(float(l.get("left", 0)))]
	info.text = s
	for c in modes.get_children():
		c.queue_free()
	var zid := str(m.get("zone", ""))
	for md in m.get("modes", []):
		var mid := str(md.get("id", "normal"))
		var p := PanelContainer.new()
		p.add_theme_stylebox_override("panel", UiSkin.inner_box())
		var h := UiSkin.hbox(8)
		p.add_child(h)
		var v := UiSkin.vbox(0)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var col = {"normal": UiSkin.TEXT, "heroisch": Color("#a335ee"), "mythisch": Color("#ff8000")}.get(mid, UiSkin.TEXT)
		v.add_child(UiSkin.label(str(md.get("name", mid)), 18, col, UiSkin.font_title))
		var d := UiSkin.label(str(md.get("desc", "")), 13, UiSkin.TEXT_DIM)
		d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		d.custom_minimum_size.x = 280
		v.add_child(d)
		if mid == "mythisch":
			var at := ""
			for a in m.get("affixes", []):
				at += "%s: %s\n" % [a.get("name", ""), a.get("desc", "")]
			if at != "":
				var al := UiSkin.label(at.strip_edges(), 12, Color(1, 0.6, 0.4))
				al.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				al.custom_minimum_size.x = 280
				v.add_child(al)
		h.add_child(v)
		var minl := int(md.get("min_level", 1))
		var b := UiSkin.button("Betreten", func():
			Game.send({"t": "dungeon_enter", "zone": zid, "mode": mid})
			close_win()
		)
		b.disabled = Game.level < minl
		b.tooltip_text = "Ab Stufe %d" % minl
		h.add_child(b)
		modes.add_child(p)
	reset_size()
