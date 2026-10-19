class_name InspectWin
extends Win
## Andere Spieler betrachten: Ausrüstung, Gilde, Titel, Erfolge.

var hud
var head: RichTextLabel
var preview: ModelPreview
var grid: GridContainer


func _init(p_hud) -> void:
	super("Betrachten", "inspektion", Vector2(520, 460))
	hud = p_hud


func _ready() -> void:
	head = UiSkin.rich("")
	body.add_child(head)
	var h := UiSkin.hbox(10)
	body.add_child(h)
	preview = ModelPreview.new(Vector2(220, 320))
	h.add_child(preview)
	grid = GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	h.add_child(grid)


func show_inspect(m: Dictionary) -> void:
	center()
	var cls := str(m.get("cls", ""))
	head.text = "[center][font_size=20][color=#%s]%s%s[/color][/font_size]\nStufe %d %s%s  ·  %d Erfolge[/center]" % [
		Content.class_color(cls).to_html(false), (str(m["title"]) + " ") if m.get("title") else "", m.get("name", ""),
		int(m.get("lvl", 1)), Content.class_name_of(cls), ("  ·  <%s>" % m["guild"]) if m.get("guild") else "", int(m.get("ach", 0))]
	for c in grid.get_children():
		c.queue_free()
	var eq: Dictionary = m.get("eq", {})
	for s in CharacterWin.LEFT + CharacterWin.RIGHT + CharacterWin.BOTTOM:
		var sl := IconSlot.new(46)
		sl.drag_enabled = false
		sl.placeholder = Content.icon(CharacterWin.PLACEHOLDER.get(s, "swap-bag"), Color(0.15, 0.13, 0.11), 48, Color(0.6, 0.55, 0.45))
		var inst = eq.get(s)
		if inst is Dictionary:
			sl.set_item(str(inst["i"]), 1, inst)
		grid.add_child(sl)
	var e = hud.world.ent(int(m.get("id", 0)))
	if e:
		preview.show_humanoid(e.look, e.look.get("gear", {}))
