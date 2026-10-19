class_name AchievementWin
extends Win
## Erfolge nach Kategorien mit Fortschritt, Punkten, Titelbelohnungen und Statistiken.

var hud
var cats: VBoxContainer
var list: VBoxContainer
var head: RichTextLabel
var cur := ""

const COUNTER_NAMES := {"kills": "Besiegte Gegner", "quests": "Abgeschlossene Quests", "deaths": "Tode", "dungeons": "Abgeschlossene Dungeons",
	"bosses": "Besiegte Bosse", "crafts": "Hergestellte Gegenstände", "gathered": "Gesammelte Rohstoffe", "dailies": "Tägliche Quests",
	"bounties": "Kopfgelder", "pvp_kills": "Ehrenhafte Siege", "duels": "Gewonnene Duelle", "arena_wins": "Arenasiege",
	"stones": "Aktivierte Teleportsteine", "gold_earned": "Verdientes Gold (Kupfer)", "market_sold": "Auf dem Markt verkauft"}


func _init(p_hud) -> void:
	super("Erfolge", "erfolge", Vector2(760, 560))
	hud = p_hud


func _ready() -> void:
	head = UiSkin.rich("")
	body.add_child(head)
	var h := UiSkin.hbox(10)
	h.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(h)
	var cs := ScrollContainer.new()
	cs.custom_minimum_size = Vector2(180, 460)
	h.add_child(cs)
	cats = UiSkin.vbox(2)
	cs.add_child(cats)
	var ls := ScrollContainer.new()
	ls.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ls.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	h.add_child(ls)
	list = UiSkin.vbox(6)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ls.add_child(list)
	Game.state_changed.connect(func(w):
		if w == "achievements" and visible:
			refresh()
	)
	position = Vector2(160, 100)


func _on_open() -> void:
	Game.send({"t": "get", "w": "achievements"})
	refresh()


func refresh() -> void:
	var a: Dictionary = Game.achievements
	for c in cats.get_children():
		c.queue_free()
	for c in list.get_children():
		c.queue_free()
	if a.is_empty():
		head.text = "[center]Lade ...[/center]"
		return
	var all: Array = a.get("list", [])
	var done := all.filter(func(x): return x.get("done") != null).size()
	head.text = "[center][font_size=20][color=#ffd870]%d Erfolgspunkte[/color][/font_size]   ·   %d von %d Erfolgen[/center]" % [int(a.get("points", 0)), done, all.size()]
	var catlist: Array = a.get("cats", [])
	if cur == "" and not catlist.is_empty():
		cur = str(catlist[0])
	for c in catlist + ["Statistiken"]:
		var cat := str(c)
		var b := UiSkin.button(cat, func():
			cur = cat
			refresh()
		)
		b.add_theme_font_size_override("font_size", 15)
		if cat == cur:
			b.add_theme_color_override("font_color", Color.WHITE)
		cats.add_child(b)
	if cur == "Statistiken":
		var cnt: Dictionary = a.get("counters", {})
		for k in cnt:
			var row := UiSkin.hbox(8)
			var l := UiSkin.label(COUNTER_NAMES.get(k, str(k).capitalize()), 15)
			l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row.add_child(l)
			row.add_child(UiSkin.label(str(cnt[k]), 15, UiSkin.GOLD, UiSkin.font_bold))
			list.add_child(row)
		return
	var entries := all.filter(func(x): return str(x.get("cat", "")) == cur)
	entries.sort_custom(func(x, y): return (x.get("done") != null) and not (y.get("done") != null))
	for e in entries:
		list.add_child(_entry(e))


func _entry(e: Dictionary) -> Control:
	var is_done: bool = e.get("done") != null
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UiSkin.flat(Color(0.18, 0.13, 0.06, 0.9) if is_done else Color(0.06, 0.05, 0.04, 0.9),
		UiSkin.GOLD if is_done else Color(0.3, 0.27, 0.22), 1, 4))
	var h := UiSkin.hbox(10)
	p.add_child(h)
	var t := TextureRect.new()
	t.texture = Content.icon(str(e.get("icon", "trophy")), Color(0.5, 0.35, 0.1) if is_done else Color(0.22, 0.22, 0.22), 64)
	t.custom_minimum_size = Vector2(48, 48)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	h.add_child(t)
	var v := UiSkin.vbox(2)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	v.add_child(UiSkin.label(str(e.get("name", "")), 17, Color("#ffd870") if is_done else UiSkin.TEXT, UiSkin.font_bold))
	var d := UiSkin.label(str(e.get("desc", "")), 14, UiSkin.TEXT_DIM)
	d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(d)
	if e.get("title"):
		v.add_child(UiSkin.label("Belohnung: Titel „%s“" % e["title"], 13, Color(0.6, 0.8, 1.0)))
	var prog = e.get("prog")
	if prog is Array and not is_done:
		var b := StatBar.new(Color("#3a8a2a"), 12)
		b.custom_minimum_size = Vector2(300, 12)
		b.text_size = 10
		b.set_values(float(prog[0]), maxf(1, float(prog[1])), "%d / %d" % [int(prog[0]), int(prog[1])])
		v.add_child(b)
	var r := UiSkin.vbox(0)
	h.add_child(r)
	var pts := UiSkin.label(str(int(e.get("points", 0))), 20, UiSkin.GOLD, UiSkin.font_title)
	pts.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	r.add_child(pts)
	if is_done:
		var dt := Time.get_date_string_from_unix_time(int(e["done"]))
		r.add_child(UiSkin.label(dt, 12, UiSkin.TEXT_DIM))
	return p
