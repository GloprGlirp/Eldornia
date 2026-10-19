class_name FinderWin
extends Win
## Gruppenfinder (GDD 10): Dungeons nach Schwierigkeit (Normal/Heroisch/Mythisch) mit Rollenwahl,
## Sperren, Wochenherausforderung, Affixe; Arena-Warteschlangen.

var hud
var tabs: TabContainer
var dlist: VBoxContainer
var arena_box: VBoxContainer
var status: RichTextLabel
var data: Dictionary = {}
var role := "dps"
var arena_state := "none"


func _init(p_hud) -> void:
	super("Gruppenfinder", "gruppensuche", Vector2(640, 560))
	hud = p_hud


func _ready() -> void:
	status = UiSkin.rich("")
	body.add_child(status)
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(620, 460)
	body.add_child(tabs)
	var ds := ScrollContainer.new()
	ds.name = "Dungeons"
	ds.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	tabs.add_child(ds)
	dlist = UiSkin.vbox(8)
	dlist.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ds.add_child(dlist)
	arena_box = UiSkin.vbox(10)
	arena_box.name = "Arena"
	tabs.add_child(arena_box)
	position = Vector2(200, 110)


func _on_open() -> void:
	Game.send({"t": "get", "w": "finder"})


func open_mode(w: String, _m: Dictionary) -> void:
	tabs.current_tab = 1 if w == "arena" else 0
	Game.send({"t": "get", "w": "finder"})


func refresh_queue() -> void:
	_status()


func on_arena_queue(m: Dictionary) -> void:
	arena_state = str(m.get("state", "none"))
	_arena()


func on_finder(m: Dictionary) -> void:
	data = m
	role = str(m.get("role", "dps"))
	_render()


func _status() -> void:
	var q = Game.queue_state
	if q is Dictionary and str(q.get("state")) == "searching":
		var mode_name: String = Content.defs.get("modes", {}).get(str(q.get("mode", "normal")), {}).get("name", q.get("mode", ""))
		status.text = "[center][color=#80c0ff]Suche Gruppe für %s (%s) als %s …[/color]   [url=leave][color=#ff8060]Suche verlassen[/color][/url][/center]" % [
			q.get("name", ""), mode_name, _role_name(str(q.get("role", "dps")))]
		if not status.meta_clicked.is_connected(_on_meta):
			status.meta_clicked.connect(_on_meta)
	else:
		status.text = ""


func _on_meta(_m) -> void:
	Game.send({"t": "queue_leave"})


func _role_name(r: String) -> String:
	return {"tank": "Tank", "heiler": "Heiler", "dps": "Schaden"}.get(r, r)


func _render() -> void:
	_status()
	for c in dlist.get_children():
		c.queue_free()
	var rh := UiSkin.hbox(8)
	rh.add_child(UiSkin.label("Eure Rolle:", 16, UiSkin.GOLD, UiSkin.font_bold))
	for r in [["tank", "shield"], ["heiler", "health-normal"], ["dps", "crossed-swords"]]:
		var rid: String = r[0]
		var b := UiSkin.button(_role_name(rid) + (" ✓" if role == rid else ""), func():
			role = rid
			Game.send({"t": "role", "role": rid})
			_render()
		)
		rh.add_child(b)
	dlist.add_child(rh)
	var wk = data.get("weekly")
	if wk is Dictionary:
		dlist.add_child(UiSkin.rich("[color=#ffd870]Wochenherausforderung:[/color] %s  [color=#aaa](Bonusbeute)[/color]" % wk.get("name", "")))
	var aff: Array = data.get("affixes", [])
	if not aff.is_empty():
		var at := "[color=#ff9060]Mythische Affixe diese Woche:[/color] "
		for a in aff:
			at += "[hint=%s]%s[/hint]  " % [a.get("desc", ""), a.get("name", "")]
		dlist.add_child(UiSkin.rich(at))
	for d in data.get("list", []):
		var p := PanelContainer.new()
		p.add_theme_stylebox_override("panel", UiSkin.inner_box())
		dlist.add_child(p)
		var v := UiSkin.vbox(4)
		p.add_child(v)
		var hh := UiSkin.hbox(8)
		v.add_child(hh)
		var lv: Array = d.get("levels", [1, 1])
		var tl := UiSkin.label(str(d.get("name", "")), 18, UiSkin.GOLD, UiSkin.font_title)
		tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		hh.add_child(tl)
		hh.add_child(UiSkin.label("Stufe %d–%d  ·  %s" % [int(lv[0]), int(lv[1]), str(d.get("players", ""))], 14, HudOverlay._level_color(int(lv[0]))))
		var mh := UiSkin.hbox(6)
		v.add_child(mh)
		var zid := str(d.get("id", ""))
		for md in d.get("modes", []):
			var mid := str(md.get("id", "normal"))
			var min_lvl := int(lv[0]) + (0 if mid == "normal" else (5 if mid == "heroisch" else 8))
			var b2 := UiSkin.button("%s anmelden" % str(md.get("name", mid)), func():
				Game.send({"t": "queue", "zone": zid, "mode": mid, "role": role})
			)
			b2.disabled = Game.level < min_lvl
			b2.tooltip_text = "Ab Stufe %d" % min_lvl
			mh.add_child(b2)
		var locks: Array = d.get("locks", [])
		if not locks.is_empty():
			var lt := "[color=#ff8060]Gesperrt:[/color] "
			for l in locks:
				lt += "%s (%s, noch %s)  " % [l.get("boss", ""), l.get("mode", ""), Content.fmt_time(float(l.get("left", 0)))]
			v.add_child(UiSkin.rich(lt))
	_arena()


func _arena() -> void:
	for c in arena_box.get_children():
		c.queue_free()
	arena_box.add_child(UiSkin.title_label("Arena von Eldornia", 22))
	arena_box.add_child(UiSkin.rich("Eure Wertung: [color=#ffd870][b]%d[/b][/color]\nKämpft in fairen Duellen gegen andere Spieler. Siege bringen Arenapunkte und erhöhen Eure Wertung." % int(data.get("arena_rating", 1500))))
	if arena_state == "searching":
		arena_box.add_child(UiSkin.rich("[color=#80c0ff]Ihr sucht einen Arenakampf …[/color]"))
		arena_box.add_child(UiSkin.button("Suche verlassen", func(): Game.send({"t": "arena_leave"})))
		return
	var h := UiSkin.hbox(10)
	arena_box.add_child(h)
	for br in ["1v1", "2v2", "3v3"]:
		var bracket: String = br
		h.add_child(UiSkin.button("%s anmelden" % br.replace("v", " gegen "), func(): Game.send({"t": "arena_queue", "bracket": bracket})))
	arena_box.add_child(UiSkin.label("Für 2v2 und 3v3 meldet der Gruppenanführer die ganze Gruppe an.", 14, UiSkin.TEXT_DIM))
