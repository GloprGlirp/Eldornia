class_name QuestLogWin
extends Win
## Questlog (GDD 7): Haupt-, Neben-, Tages-, Wochen-, Klassen-, Dungeon- und Kopfgeldquests.

var hud
var list: VBoxContainer
var detail: RichTextLabel
var sel := ""
var abandon_btn: Button
var share_btn: Button
var track_btn: Button
var count_l: Label

const TYPE_NAMES := {"main": "Hauptquest", "side": "Nebenquest", "daily": "Tägliche Quest", "weekly": "Wöchentliche Quest",
	"class": "Klassenquest", "hidden": "Verborgene Quest", "bounty": "Kopfgeld", "dungeon": "Dungeon", "raid": "Schlachtzug",
	"profession": "Berufsquest", "event": "Ereignis"}


func _init(p_hud) -> void:
	super("Questlog", "questlog", Vector2(760, 520))
	hud = p_hud


func _ready() -> void:
	count_l = UiSkin.label("", 14, UiSkin.TEXT_DIM)
	body.add_child(count_l)
	var h := UiSkin.hbox(10)
	h.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(h)
	var ls := ScrollContainer.new()
	ls.custom_minimum_size = Vector2(280, 420)
	h.add_child(ls)
	list = UiSkin.vbox(2)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ls.add_child(list)
	var right := PanelContainer.new()
	right.add_theme_stylebox_override("panel", UiSkin.parchment_box())
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.custom_minimum_size = Vector2(440, 420)
	h.add_child(right)
	var rv := UiSkin.vbox(6)
	right.add_child(rv)
	var ds := ScrollContainer.new()
	ds.size_flags_vertical = Control.SIZE_EXPAND_FILL
	ds.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	rv.add_child(ds)
	detail = UiSkin.rich("")
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.add_theme_color_override("default_color", UiSkin.PARCH_TEXT)
	detail.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
	ds.add_child(detail)
	var bh := UiSkin.hbox(8)
	bh.alignment = BoxContainer.ALIGNMENT_CENTER
	body.add_child(bh)
	abandon_btn = UiSkin.button("Abbrechen", func():
		var q := _find(sel)
		if not q.is_empty():
			var qid := sel
			hud.confirm("abandon", "„%s“ abbrechen?" % q.get("title", ""), func(): Game.send({"t": "quest_abandon", "q": qid}))
	)
	bh.add_child(abandon_btn)
	share_btn = UiSkin.button("Teilen", func(): Game.send({"t": "quest_share", "q": sel}))
	bh.add_child(share_btn)
	track_btn = UiSkin.button("Verfolgen", func():
		hud.tracker.tracked[sel] = not hud.tracker.tracked.get(sel, true)
		hud.tracker.refresh()
		_detail()
	)
	bh.add_child(track_btn)
	Game.state_changed.connect(func(w):
		if w == "quests" and visible:
			refresh()
	)
	position = Vector2(80, 110)


func _on_open() -> void:
	refresh()


func select(qid: String) -> void:
	sel = qid
	refresh()


func _find(qid: String) -> Dictionary:
	for q in Game.quests:
		if str(q["id"]) == qid:
			return q
	return {}


func refresh() -> void:
	for c in list.get_children():
		c.queue_free()
	count_l.text = "%d / 25 Quests  ·  %d abgeschlossen" % [Game.quests.size(), Game.quests_done_count]
	if _find(sel).is_empty():
		sel = str(Game.quests[0]["id"]) if not Game.quests.is_empty() else ""
	var by_zone: Dictionary = {}
	for q in Game.quests:
		var z := str(q.get("zone", "")) if q.get("zone") else "Sonstige"
		if not by_zone.has(z):
			by_zone[z] = []
		by_zone[z].append(q)
	for z in by_zone:
		list.add_child(UiSkin.label(z, 16, UiSkin.GOLD, UiSkin.font_title))
		for q in by_zone[z]:
			var b := Button.new()
			b.flat = str(q["id"]) != sel
			b.alignment = HORIZONTAL_ALIGNMENT_LEFT
			b.add_theme_font_override("font", UiSkin.font_body)
			b.add_theme_font_size_override("font_size", 15)
			var col := HudOverlay._level_color(int(q.get("level", 1)))
			b.add_theme_color_override("font_color", col)
			b.add_theme_color_override("font_hover_color", col.lightened(0.3))
			b.text = "  [%d] %s%s" % [int(q.get("level", 1)), str(q.get("title", "")), "  (Fertig)" if q.get("done", false) else ""]
			var qid := str(q["id"])
			b.pressed.connect(func():
				sel = qid
				refresh()
			)
			list.add_child(b)
	_detail()


func _detail() -> void:
	var q := _find(sel)
	abandon_btn.disabled = q.is_empty()
	share_btn.disabled = q.is_empty() or Game.party.get("members", []).is_empty()
	track_btn.disabled = q.is_empty()
	if q.is_empty():
		detail.text = "[center][i]Euer Questlog ist leer.[/i]\n\nSprecht mit Personen, über deren Köpfen ein gelbes [b]![/b] schwebt.[/center]"
		return
	track_btn.text = "Nicht verfolgen" if hud.tracker.tracked.get(sel, true) else "Verfolgen"
	var s := "[font_size=22][b]%s[/b][/font_size]\n" % q.get("title", "")
	s += "[i]%s – Stufe %d[/i]\n\n" % [TYPE_NAMES.get(str(q.get("type", "")), "Quest"), int(q.get("level", 1))]
	s += "[b]Ziel[/b]\n%s\n\n" % q.get("objective", "")
	for o in q.get("progress", []):
		var have := int(o.get("have", 0))
		var need := int(o.get("need", 1))
		s += "%s %s%s\n" % ["✔" if have >= need else "•", o.get("text", ""), (": %d/%d" % [have, need]) if need > 1 else ""]
	s += "\n[b]Beschreibung[/b]\n%s\n\n" % q.get("text", "")
	if q.get("done", false):
		s += "[color=#1a6a10][b]Kehrt zu %s zurück.[/b][/color]\n" % q.get("ender", "")
	else:
		s += "Abgabe bei: %s%s\n" % [q.get("ender", ""), (" (%s)" % q["zone"]) if q.get("zone") else ""]
	detail.text = s
