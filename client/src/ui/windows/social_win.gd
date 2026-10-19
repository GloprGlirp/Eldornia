class_name SocialWin
extends Win
## Soziales (GDD 10): Freundesliste, Ignorierliste, Gruppe/Schlachtzug, Spielersuche (/wer).

var hud
var tabs: TabContainer
var friends: VBoxContainer
var ignore: VBoxContainer
var group: VBoxContainer
var who_list: VBoxContainer
var who_q: LineEdit


func _init(p_hud) -> void:
	super("Soziales", "soziales", Vector2(480, 520))
	hud = p_hud


func _ready() -> void:
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(460, 470)
	body.add_child(tabs)
	friends = _tab("Freunde")
	ignore = _tab("Ignoriert")
	group = _tab("Gruppe")
	var wv := UiSkin.vbox(6)
	wv.name = "Wer ist online"
	tabs.add_child(wv)
	var wh := UiSkin.hbox(6)
	wv.add_child(wh)
	who_q = LineEdit.new()
	who_q.placeholder_text = "Name oder Klasse"
	who_q.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	who_q.text_submitted.connect(func(t): Game.send({"t": "who", "q": t}))
	wh.add_child(who_q)
	wh.add_child(UiSkin.button("Suchen", func(): Game.send({"t": "who", "q": who_q.text})))
	var ws := ScrollContainer.new()
	ws.size_flags_vertical = Control.SIZE_EXPAND_FILL
	wv.add_child(ws)
	who_list = UiSkin.vbox(2)
	who_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ws.add_child(who_list)
	tabs.tab_changed.connect(func(i):
		if i == 3:
			Game.send({"t": "who", "q": who_q.text})
	)
	Game.state_changed.connect(func(w):
		if visible and w in ["friends", "party"]:
			refresh()
	)
	position = Vector2(220, 120)


func _tab(n: String) -> VBoxContainer:
	var sc := ScrollContainer.new()
	sc.name = n
	tabs.add_child(sc)
	var v := UiSkin.vbox(4)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(v)
	return v


func _on_open() -> void:
	Game.send({"t": "get", "w": "friends"})
	refresh()


func refresh() -> void:
	for l in [friends, ignore, group]:
		for c in l.get_children():
			c.queue_free()
	# Freunde
	var ah := UiSkin.hbox(6)
	var fe := LineEdit.new()
	fe.placeholder_text = "Name"
	fe.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ah.add_child(fe)
	ah.add_child(UiSkin.button("Hinzufügen", func(): Game.send({"t": "friend_add", "name": fe.text})))
	friends.add_child(ah)
	var fl := Game.friends.duplicate()
	fl.sort_custom(func(a, b): return a.get("online", false) and not b.get("online", false))
	for f in fl:
		var h := UiSkin.hbox(6)
		var on: bool = f.get("online", false)
		var nl := UiSkin.label(str(f.get("name", "")), 16, Content.class_color(str(f.get("cls", ""))) if on else Color(0.55, 0.55, 0.55), UiSkin.font_bold)
		nl.custom_minimum_size.x = 130
		h.add_child(nl)
		var info := ("Stufe %s %s – %s" % [str(f.get("lvl", "")), Content.class_name_of(str(f.get("cls", ""))), str(f.get("zone", ""))]) if on else "Offline"
		var il := UiSkin.label(info, 13, UiSkin.TEXT_DIM)
		il.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		il.clip_text = true
		h.add_child(il)
		var name := str(f.get("name", ""))
		if on:
			h.add_child(UiSkin.button("✉", func(): hud.chat.start_whisper(name)))
			h.add_child(UiSkin.button("+", func(): Game.send({"t": "invite", "name": name})))
		var fid = f.get("id")
		h.add_child(UiSkin.button("✕", func(): Game.send({"t": "friend_remove", "id": fid})))
		friends.add_child(h)
	if Game.friends.is_empty():
		friends.add_child(UiSkin.label("Eure Freundesliste ist leer.", 14, UiSkin.TEXT_DIM))
	# Ignoriert
	var ih := UiSkin.hbox(6)
	var ie := LineEdit.new()
	ie.placeholder_text = "Name"
	ie.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ih.add_child(ie)
	ih.add_child(UiSkin.button("Ignorieren", func(): Game.send({"t": "friend_add", "name": ie.text, "ignore": true})))
	ignore.add_child(ih)
	for n in Game.ignore:
		ignore.add_child(UiSkin.label("• " + str(n), 15))
	# Gruppe
	var members: Array = Game.party.get("members", [])
	var gh := UiSkin.hbox(6)
	var ge := LineEdit.new()
	ge.placeholder_text = "Name"
	ge.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	gh.add_child(ge)
	gh.add_child(UiSkin.button("Einladen", func(): Game.send({"t": "invite", "name": ge.text})))
	group.add_child(gh)
	if members.is_empty():
		group.add_child(UiSkin.label("Ihr seid in keiner Gruppe. Gruppen umfassen bis zu 5 Spieler, Schlachtzüge bis zu 10.", 14, UiSkin.TEXT_DIM))
	else:
		var raid: bool = Game.party.get("raid", false)
		group.add_child(UiSkin.label("Schlachtzug (%d/10)" % members.size() if raid else "Gruppe (%d/5)" % members.size(), 17, UiSkin.GOLD, UiSkin.font_title))
		for m in members:
			var lead := int(Game.party.get("leader", 0) if Game.party.get("leader") != null else 0) == int(m.get("id", 0))
			group.add_child(UiSkin.label("%s%s  –  Stufe %d %s  (%s)" % ["♛ " if lead else "", m.get("name", ""), int(m.get("lvl", 1)),
				Content.class_name_of(str(m.get("cls", ""))), m.get("zone", "")], 15, Content.class_color(str(m.get("cls", "")))))
		var bh := UiSkin.hbox(6)
		bh.add_child(UiSkin.button("Verlassen", func(): Game.send({"t": "party_leave"})))
		if hud._is_leader() and not raid:
			bh.add_child(UiSkin.button("In Schlachtzug umwandeln", func(): Game.send({"t": "party_raid"})))
		group.add_child(bh)


func show_who(m: Dictionary) -> void:
	tabs.current_tab = 3
	for c in who_list.get_children():
		c.queue_free()
	who_list.add_child(UiSkin.label("%d Spieler gefunden" % int(m.get("total", 0)), 14, UiSkin.TEXT_DIM))
	for p in m.get("list", []):
		var h := UiSkin.hbox(6)
		var nm := str(p.get("name", ""))
		var b := Button.new()
		b.flat = true
		b.text = nm
		b.add_theme_color_override("font_color", Content.class_color(str(p.get("cls", ""))))
		b.custom_minimum_size.x = 120
		b.pressed.connect(func(): hud.chat.start_whisper(nm))
		h.add_child(b)
		var g := ("<%s>  " % p["guild"]) if p.get("guild") else ""
		h.add_child(UiSkin.label("%sStufe %d %s – %s" % [g, int(p.get("lvl", 1)), Content.class_name_of(str(p.get("cls", ""))), p.get("zone", "")], 14))
		who_list.add_child(h)
