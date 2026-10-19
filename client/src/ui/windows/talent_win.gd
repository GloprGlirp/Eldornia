class_name TalentWin
extends Win
## Talentbäume (GDD 3): drei Spezialisierungen pro Klasse. Ab Stufe 10 ein Punkt pro Stufe; jede Reihe
## erfordert 5 Punkte mehr im selben Baum. Endtalente schalten neue Fähigkeiten frei.

var hud
var trees_row: HBoxContainer
var info: RichTextLabel
var reset_btn: Button
var trainer_npc := 0


func _init(p_hud) -> void:
	super("Talente", "talente", Vector2(900, 560))
	hud = p_hud


func _ready() -> void:
	info = UiSkin.rich("")
	body.add_child(info)
	trees_row = UiSkin.hbox(10)
	body.add_child(trees_row)
	var h := UiSkin.hbox(8)
	h.alignment = BoxContainer.ALIGNMENT_END
	body.add_child(h)
	reset_btn = UiSkin.button("Talente zurücksetzen", func():
		var cost := int(Game.talents.get("respec_cost", 0))
		hud.confirm("respec", "Alle Talentpunkte für %s zurücksetzen?" % Content.money_bb(cost), func():
			Game.send({"t": "talent_reset", "npc": trainer_npc})
		)
	)
	h.add_child(reset_btn)
	Game.state_changed.connect(func(w):
		if w in ["talents", "level"] and visible:
			refresh()
	)


func _on_open() -> void:
	Game.send({"t": "get", "w": "talents"})
	center()
	refresh()


func _on_close() -> void:
	trainer_npc = 0


func refresh() -> void:
	var td: Dictionary = Game.talents
	reset_btn.visible = trainer_npc != 0
	for c in trees_row.get_children():
		c.queue_free()
	if td.is_empty():
		info.text = "[center]Lade ...[/center]"
		return
	var pts := int(td.get("points", 0))
	var total := int(td.get("total", 0))
	if total == 0:
		info.text = "[center]Talentpunkte erhaltet Ihr ab Stufe 10 – einen pro Stufe.[/center]"
	else:
		info.text = "[center]Verfügbare Talentpunkte: [color=%s][b]%d[/b][/color] von %d[/center]" % ["#40ff40" if pts > 0 else "#ffffff", pts, total]
	var ranks: Dictionary = td.get("ranks", {})
	var specs: Dictionary = td.get("specs", {})
	var trees: Dictionary = td.get("trees", {})
	for spec in trees:
		var spent := 0
		for t in trees[spec]:
			spent += int(ranks.get(t["id"], 0))
		var col := PanelContainer.new()
		col.add_theme_stylebox_override("panel", UiSkin.inner_box())
		col.custom_minimum_size = Vector2(285, 440)
		trees_row.add_child(col)
		var v := UiSkin.vbox(8)
		col.add_child(v)
		var sd: Dictionary = specs.get(spec, {})
		var tl := UiSkin.title_label("%s  (%d)" % [str(sd.get("name", spec)), spent], 18)
		tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(tl)
		var role := UiSkin.label(_role_name(str(sd.get("role", ""))), 14, UiSkin.TEXT_DIM)
		role.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(role)
		for tier in 4:
			var row := UiSkin.hbox(10)
			row.alignment = BoxContainer.ALIGNMENT_CENTER
			row.custom_minimum_size.y = 76
			v.add_child(row)
			var unlocked := spent >= 5 * tier
			for t in trees[spec]:
				if int(t.get("tier", 0)) != tier:
					continue
				row.add_child(_talent(t, int(ranks.get(t["id"], 0)), unlocked, pts))
			if tier < 3:
				var ln := UiSkin.label("— %d Punkte —" % (5 * (tier + 1)), 11, Color(0.6, 0.55, 0.45, 0.6))
				ln.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
				v.add_child(ln)


func _role_name(r: String) -> String:
	return {"tank": "Verteidiger", "heal": "Heiler", "heiler": "Heiler", "dps": "Schaden", "melee": "Nahkampfschaden",
		"ranged": "Fernkampfschaden", "caster": "Zauberschaden"}.get(r, r)


func _talent(t: Dictionary, rank: int, unlocked: bool, pts: int) -> Control:
	var v := UiSkin.vbox(0)
	var s := IconSlot.new(50)
	s.drag_enabled = false
	var maxr := int(t.get("ranks", 1))
	var tex := Content.icon(str(t.get("icon", "star-swirl")), Color(0.45, 0.3, 0.12) if rank > 0 else Color(0.22, 0.22, 0.22), 64)
	s.set_icon(tex, _tip(t, rank, unlocked))
	s.dim = not unlocked or (rank == 0 and pts == 0)
	s.glow = unlocked and pts > 0 and rank < maxr
	s.quality = 5 if rank >= maxr else (2 if rank > 0 else -1)
	var tid := str(t["id"])
	s.clicked.connect(func(_s, b):
		if b == MOUSE_BUTTON_LEFT:
			Game.send({"t": "talent", "id": tid})
			Sfx.play("click", -6.0)
	)
	v.add_child(s)
	var l := UiSkin.label("%d/%d" % [rank, maxr], 13, Color(0.3, 1.0, 0.3) if rank > 0 else UiSkin.TEXT_DIM, UiSkin.font_bold)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(l)
	return v


func _tip(t: Dictionary, rank: int, unlocked: bool) -> String:
	var maxr := int(t.get("ranks", 1))
	var per = t.get("per_rank", 0)
	var desc := str(t.get("desc", ""))
	var s := "[font_size=18][b]%s[/b][/font_size]\nRang %d/%d\n" % [t.get("name", ""), rank, maxr]
	if rank > 0:
		s += "[color=#ffd100]%s[/color]\n" % desc.replace("{v}", _num(float(per) * rank))
	if rank < maxr:
		s += ("\nNächster Rang:\n" if rank > 0 else "") + "[color=#ffd100]%s[/color]\n" % desc.replace("{v}", _num(float(per) * (rank + 1)))
	if t.get("grants"):
		var ab: Dictionary = {}
		for c in Content.cls(Game.me_cls).get("abilities", []):
			if c.get("id") == t["grants"]:
				ab = c
		if not ab.is_empty():
			s += "\n" + Tips.ability_bb(ab)
	if not unlocked:
		s += "\n[color=#ff4040]Benötigt %d Punkte in diesem Baum.[/color]" % (5 * int(t.get("tier", 0)))
	return s


func _num(v: float) -> String:
	v = absf(v)
	return str(int(v)) if absf(v - round(v)) < 0.01 else "%.1f" % v
