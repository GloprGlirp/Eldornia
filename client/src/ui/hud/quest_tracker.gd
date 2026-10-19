class_name QuestTracker
extends VBoxContainer
## Questverfolgung am rechten Bildschirmrand (GDD 11: aktuelle Questziele).

var hud
var tracked: Dictionary = {}     # qid -> false, wenn ausgeblendet
var collapsed := false
var head: Button
var list: VBoxContainer


func _init(p_hud) -> void:
	hud = p_hud
	add_theme_constant_override("separation", 2)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	head = Button.new()
	head.flat = true
	head.text = "▾ Quests"
	head.alignment = HORIZONTAL_ALIGNMENT_LEFT
	head.add_theme_font_override("font", UiSkin.font_title)
	head.add_theme_font_size_override("font_size", 17)
	head.add_theme_color_override("font_color", UiSkin.GOLD)
	head.pressed.connect(func():
		collapsed = not collapsed
		refresh()
	)
	add_child(head)
	list = UiSkin.vbox(6)
	list.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(list)
	Game.state_changed.connect(func(w):
		if w in ["quests", "inventory"]:
			refresh()
	)
	refresh()


func refresh() -> void:
	for c in list.get_children():
		c.queue_free()
	var qs: Array = Game.quests.filter(func(q): return tracked.get(str(q["id"]), true))
	head.visible = not Game.quests.is_empty()
	head.text = ("▸ " if collapsed else "▾ ") + "Quests (%d/25)" % Game.quests.size()
	if collapsed:
		return
	var shown := 0
	for q in qs:
		if shown >= 8:
			break
		shown += 1
		var box := UiSkin.vbox(0)
		box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var title := Button.new()
		title.flat = true
		title.alignment = HORIZONTAL_ALIGNMENT_LEFT
		title.add_theme_font_override("font", UiSkin.font_bold)
		title.add_theme_font_size_override("font_size", 16)
		var lv := int(q.get("level", 1))
		var col := HudOverlay._level_color(lv)
		title.add_theme_color_override("font_color", col)
		title.add_theme_color_override("font_hover_color", col.lightened(0.3))
		title.add_theme_color_override("font_outline_color", Color.BLACK)
		title.add_theme_constant_override("outline_size", 4)
		var tag := ""
		match str(q.get("type", "")):
			"daily": tag = " (Täglich)"
			"weekly": tag = " (Wöchentlich)"
			"dungeon": tag = " (Dungeon)"
			"bounty": tag = " (Kopfgeld)"
			"main": tag = " ◆"
		title.text = "[%d] %s%s" % [lv, str(q.get("title", "")), tag]
		var qid := str(q["id"])
		title.pressed.connect(func():
			var w: QuestLogWin = hud.open_window("questlog")
			w.select(qid)
		)
		box.add_child(title)
		if q.get("done", false):
			var l := UiSkin.label("  – Bereit zur Abgabe bei %s" % str(q.get("ender", "")), 14, Color(0.4, 1.0, 0.4))
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			l.mouse_filter = Control.MOUSE_FILTER_IGNORE
			l.add_theme_color_override("font_outline_color", Color.BLACK)
			l.add_theme_constant_override("outline_size", 3)
			box.add_child(l)
		else:
			for o in q.get("progress", []):
				var have := int(o.get("have", 0))
				var need := int(o.get("need", 1))
				var txt := "  – %s" % str(o.get("text", ""))
				if need > 1:
					txt += ": %d/%d" % [have, need]
				var l2 := UiSkin.label(txt, 14, Color(0.85, 0.85, 0.85) if have < need else Color(0.5, 0.5, 0.5))
				l2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				l2.mouse_filter = Control.MOUSE_FILTER_IGNORE
				l2.add_theme_color_override("font_outline_color", Color.BLACK)
				l2.add_theme_constant_override("outline_size", 3)
				box.add_child(l2)
		list.add_child(box)
