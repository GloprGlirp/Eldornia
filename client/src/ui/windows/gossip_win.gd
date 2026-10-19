class_name GossipWin
extends Win
## Gespräch mit NPCs und Questdialog (Annehmen, Fortschritt, Abgabe mit Belohnungswahl) im Pergamentstil.

var hud
var portrait: ModelPreview
var name_l: Label
var title_l: Label
var text: RichTextLabel
var opts: VBoxContainer
var rewards: VBoxContainer
var btn_row: HBoxContainer
var npc_ent := 0
var giver := ""
var mode := ""
var quest: Dictionary = {}
var choice := -1
var shared := false
var _gossip: Dictionary = {}

const SVC := {
	"vendor": ["Ich möchte mir Eure Waren ansehen.", "shop"], "trainer": ["Unterrichtet mich.", "spell-book"],
	"prof_trainer": ["Ich möchte einen Beruf erlernen.", "anvil"], "innkeeper": ["Macht dieses Gasthaus zu meinem Zuhause.", "beer-stein"],
	"auction": ["Ich möchte das Auktionshaus nutzen.", "scales"], "mail": ["Habt Ihr Post für mich?", "envelope"],
	"guild": ["Ich möchte eine Gilde verwalten.", "family-tree"], "stable": ["Zeigt mir meine Reittiere und Begleiter.", "horse-head"],
	"transmog": ["Ich möchte das Aussehen meiner Ausrüstung ändern.", "sewing-needle"], "repair": ["Repariert meine Ausrüstung.", "hammer-nails"],
	"finder": ["Ich suche Gefährten für einen Dungeon.", "eye-target"], "arena": ["Ich möchte in der Arena kämpfen.", "crossed-swords"],
	"spirit": ["Segnet mich.", "angel-wings"], "bank": ["Ich möchte an mein Schließfach.", "locked-chest"],
}


func _init(p_hud) -> void:
	super("", "gespraech", Vector2(520, 560))
	hud = p_hud


func _ready() -> void:
	var top := UiSkin.hbox(10)
	body.add_child(top)
	portrait = ModelPreview.new(Vector2(96, 110))
	top.add_child(portrait)
	var tv := UiSkin.vbox(2)
	tv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tv)
	name_l = UiSkin.title_label("", 22)
	tv.add_child(name_l)
	title_l = UiSkin.label("", 15, UiSkin.TEXT_DIM, UiSkin.font_italic)
	tv.add_child(title_l)
	var parch := PanelContainer.new()
	parch.add_theme_stylebox_override("panel", UiSkin.parchment_box())
	parch.custom_minimum_size = Vector2(490, 360)
	parch.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(parch)
	var sc := ScrollContainer.new()
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	parch.add_child(sc)
	var pv := UiSkin.vbox(10)
	pv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(pv)
	text = UiSkin.rich("")
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.add_theme_color_override("default_color", UiSkin.PARCH_TEXT)
	text.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
	text.add_theme_font_size_override("normal_font_size", 17)
	pv.add_child(text)
	rewards = UiSkin.vbox(6)
	pv.add_child(rewards)
	opts = UiSkin.vbox(2)
	pv.add_child(opts)
	btn_row = UiSkin.hbox(10)
	btn_row.alignment = BoxContainer.ALIGNMENT_CENTER
	body.add_child(btn_row)


func _on_close() -> void:
	if mode == "gossip" or mode == "":
		pass
	npc_ent = 0


func _set_npc(m: Dictionary) -> void:
	name_l.text = str(m.get("name", ""))
	title_l.text = ("<%s>" % m["title"]) if m.get("title") else ""
	title = name_l.text
	var e = hud.world.ent(int(m.get("npc", 0)))
	if e and e.kind == "npc":
		if e.model is HumanoidModel:
			portrait.show_humanoid(e.look, {})
			portrait.cam.position = Vector3(0, 1.62 if str(e.look.get("kind", "human")) != "dwarf" else 1.15, 1.25)
			portrait.cam.look_at_from_position(portrait.cam.position, portrait.cam.position + Vector3(0, -0.05, -1))
		else:
			portrait.show_creature(str(e.info.get("model", "wolf")), e.look, 1.4)
		portrait.visible = true
	elif m.get("look") is Dictionary and str(m.get("model", "")) in ["human", "humanoid"]:
		portrait.show_humanoid(m["look"], {})
		portrait.visible = true
	else:
		portrait.visible = false


func _clear() -> void:
	for c in opts.get_children():
		c.queue_free()
	for c in rewards.get_children():
		c.queue_free()
	for c in btn_row.get_children():
		c.queue_free()


# ============================================================================== Gespräch
func show_gossip(m: Dictionary) -> void:
	_gossip = m
	mode = "gossip"
	npc_ent = int(m.get("npc", 0))
	giver = str(m.get("npc_id", ""))
	_set_npc(m)
	_clear()
	text.text = "%s\n" % _fmt(str(m.get("text", "")))
	var quests: Array = m.get("quests", [])
	if not quests.is_empty():
		opts.add_child(_head("Aufträge"))
	for q in quests:
		var st := str(q.get("state", ""))
		var icon := "!" if st == "available" else "?"
		var col := Color("#c08000") if st != "active" else Color("#7a7060")
		if str(q.get("type", "")) in ["daily", "weekly"]:
			col = Color("#2060c0") if st != "active" else col
		var qid := str(q["id"])
		opts.add_child(_option("%s  %s" % [icon, str(q.get("title", ""))], col, func():
			Game.send({"t": "quest_view", "giver": giver, "q": qid})
		))
	var svc: Array = m.get("services", [])
	if not svc.is_empty() and not quests.is_empty():
		opts.add_child(UiSkin.spacer(0, 6))
	for s in svc:
		if not SVC.has(s):
			continue
		var sid := str(s)
		opts.add_child(_option("◆  " + str(SVC[s][0]), Color("#3a2410"), func():
			Game.send({"t": "gossip", "npc": npc_ent, "opt": sid})
			if sid in ["vendor", "trainer", "prof_trainer", "auction", "mail", "guild", "stable", "transmog", "finder", "arena"]:
				close_win()
		))
	for o in m.get("options", []):
		if o is Dictionary:
			var reply := str(o.get("text", ""))
			opts.add_child(_option("◆  " + str(o.get("label", "")), Color("#3a2410"), func(): text.text = _fmt(reply) + "\n"))
	btn_row.add_child(UiSkin.button("Auf Wiedersehen", close_win, 160))


func _head(t: String) -> Label:
	var l := UiSkin.label(t, 18, Color("#5a2a08"), UiSkin.font_title)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
	return l


func _option(t: String, col: Color, cb: Callable) -> Button:
	var b := Button.new()
	b.flat = true
	b.text = t
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.add_theme_font_override("font", UiSkin.font_bold)
	b.add_theme_font_size_override("font_size", 17)
	b.add_theme_color_override("font_color", col)
	b.add_theme_color_override("font_hover_color", col.lightened(0.35))
	b.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0))
	b.add_theme_constant_override("outline_size", 0)
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.pressed.connect(cb)
	b.pressed.connect(func(): Sfx.play("click", -10.0))
	return b


func _fmt(s: String) -> String:
	return s.replace("$N", Game.me_name).replace("$K", Content.class_name_of(Game.me_cls))


# ============================================================================== Quest
func show_quest(m: Dictionary) -> void:
	mode = str(m.get("mode", "offer"))
	quest = m.get("q", {})
	giver = str(m.get("giver", ""))
	shared = m.has("shared")
	choice = -1
	if not _gossip.is_empty() and int(_gossip.get("npc", 0)) != 0:
		_set_npc(_gossip)
	_clear()
	var s := "[font_size=23][b]%s[/b][/font_size]\n" % quest.get("title", "")
	if quest.get("type_name"):
		s += "[i]%s – Stufe %d[/i]\n" % [quest["type_name"], int(quest.get("level", 1))]
	if shared:
		s += "[i]%s teilt diese Quest mit Euch.[/i]\n" % m["shared"]
	s += "\n%s\n" % _fmt(str(quest.get("text", "")))
	if mode == "offer":
		s += "\n[font_size=19][b]Ziele[/b][/font_size]\n%s\n" % _fmt(str(quest.get("objective", "")))
		if quest.get("dungeon"):
			s += "[color=#7a2a08]Dieser Auftrag führt Euch in: %s[/color]\n" % quest["dungeon"]
	elif mode == "progress":
		for o in quest.get("progress", []):
			var have := int(o.get("have", 0))
			var need := int(o.get("need", 1))
			s += "\n%s %s%s" % ["✔" if have >= need else "•", o.get("text", ""), (": %d/%d" % [have, need]) if need > 1 else ""]
		s += "\n"
	text.text = s
	_rewards()
	match mode:
		"offer":
			btn_row.add_child(UiSkin.button("Annehmen", func():
				if shared:
					Game.send({"t": "quest_accept_shared", "q": quest["id"]})
				else:
					Game.send({"t": "quest_accept", "giver": giver, "q": quest["id"]})
			, 140))
			btn_row.add_child(UiSkin.button("Ablehnen", _back, 140))
		"progress":
			var b := UiSkin.button("Weiter", Callable(), 140)
			b.disabled = true
			btn_row.add_child(b)
			btn_row.add_child(UiSkin.button("Zurück", _back, 140))
		"complete":
			btn_row.add_child(UiSkin.button("Quest abschließen", func():
				var r: Dictionary = quest.get("rewards", {})
				if not r.get("choice", []).is_empty() and choice < 0:
					hud.error_text("Wählt zuerst eine Belohnung.")
					return
				Game.send({"t": "quest_complete", "giver": giver, "q": quest["id"], "choice": choice if choice >= 0 else null})
			, 180))
			btn_row.add_child(UiSkin.button("Zurück", _back, 120))


func _back() -> void:
	if not _gossip.is_empty() and str(_gossip.get("npc_id", "")) == giver:
		show_gossip(_gossip)
	else:
		close_win()


## Nach Annahme/Abgabe: Gesprächsfenster schließen (eine Folgequest öffnet es gleich wieder).
func after_quest_action() -> void:
	if mode in ["offer", "complete"]:
		close_win()
		_gossip = {}


func _rewards() -> void:
	var r: Dictionary = quest.get("rewards", {})
	if r.is_empty() or mode == "progress":
		return
	rewards.add_child(_head("Belohnungen"))
	var ch: Array = r.get("choice", [])
	if not ch.is_empty():
		var l := UiSkin.label("Wählt eine dieser Belohnungen:", 15, UiSkin.PARCH_TEXT)
		l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
		rewards.add_child(l)
		var g := GridContainer.new()
		g.columns = 2
		g.add_theme_constant_override("h_separation", 10)
		rewards.add_child(g)
		var btns: Array = []
		for i in ch.size():
			var box := _reward_item(str(ch[i]), 1, i)
			btns.append(box)
			g.add_child(box)
		for i in btns.size():
			var idx := i
			var bx: PanelContainer = btns[i]
			var pick := func():
				if mode == "complete":
					choice = idx
					for j in btns.size():
						btns[j].add_theme_stylebox_override("panel", _rbox(j == idx))
			bx.gui_input.connect(func(ev):
				if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
					pick.call()
			)
			var slot: IconSlot = bx.get_child(0).get_child(0)
			slot.clicked.connect(func(_s, _b): pick.call())
	var items: Array = r.get("items", [])
	if not items.is_empty():
		var l2 := UiSkin.label("Ihr erhaltet außerdem:" if not ch.is_empty() else "Ihr erhaltet:", 15, UiSkin.PARCH_TEXT)
		l2.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
		rewards.add_child(l2)
		var g2 := GridContainer.new()
		g2.columns = 2
		rewards.add_child(g2)
		for it in items:
			g2.add_child(_reward_item(str(it[0]), int(it[1]), -1))
	var extra := ""
	if int(r.get("xp", 0)) > 0:
		extra += "%d Erfahrung   " % int(r["xp"])
	if int(r.get("copper", 0)) > 0:
		extra += Content.money_bb(int(r["copper"])) + "   "
	var fac: Dictionary = Content.defs.get("factions", {})
	for f in r.get("rep", {}):
		extra += "\n+%d Ruf: %s" % [int(r["rep"][f]), fac.get(f, {}).get("name", f)]
	var cur: Dictionary = Content.defs.get("currencies", {})
	for c in r.get("currency", {}):
		extra += "\n%d× %s" % [int(r["currency"][c]), cur.get(c, {}).get("name", c)]
	if r.get("title"):
		extra += "\nTitel: %s" % Content.defs.get("titles", {}).get(r["title"], r["title"])
	if extra != "":
		var rl := UiSkin.rich(extra)
		rl.add_theme_color_override("default_color", UiSkin.PARCH_TEXT)
		rl.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
		rewards.add_child(rl)


func _rbox(selected: bool) -> StyleBoxFlat:
	return UiSkin.flat(Color(1, 0.85, 0.4, 0.45) if selected else Color(0, 0, 0, 0.12), Color("#c08a2a") if selected else Color(0.3, 0.2, 0.1, 0.4), 2, 4)


func _reward_item(iid: String, n: int, _i: int) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", _rbox(false))
	p.custom_minimum_size = Vector2(220, 50)
	p.mouse_filter = Control.MOUSE_FILTER_STOP
	var h := UiSkin.hbox(6)
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.add_child(h)
	var s := IconSlot.new(42)
	s.set_item(iid, n)
	s.drag_enabled = false
	s.mouse_filter = Control.MOUSE_FILTER_PASS
	h.add_child(s)
	var it := Content.item(iid)
	var l := UiSkin.label(str(it.get("name", iid)), 15, Content.rarity_color(int(it.get("q", 1))).darkened(0.35), UiSkin.font_bold)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 160
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(l)
	return p
