class_name MailWin
extends Win
## Briefkasten: Posteingang (Gegenstände/Gold entnehmen) und Briefe mit Anhängen versenden.

var hud
var tabs: TabContainer
var inbox: VBoxContainer
var to_e: LineEdit
var subj_e: LineEdit
var body_e: TextEdit
var attach: Array = []
var attach_row: HBoxContainer
var money_g: SpinBox
var money_s: SpinBox


func _init(p_hud) -> void:
	super("Briefkasten", "post", Vector2(560, 540))
	hud = p_hud


func _ready() -> void:
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(540, 480)
	body.add_child(tabs)
	var sc := ScrollContainer.new()
	sc.name = "Posteingang"
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	tabs.add_child(sc)
	inbox = UiSkin.vbox(6)
	inbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(inbox)
	var sv := UiSkin.vbox(8)
	sv.name = "Senden"
	tabs.add_child(sv)
	to_e = LineEdit.new()
	to_e.placeholder_text = "Empfänger"
	sv.add_child(to_e)
	subj_e = LineEdit.new()
	subj_e.placeholder_text = "Betreff"
	subj_e.max_length = 64
	sv.add_child(subj_e)
	body_e = TextEdit.new()
	body_e.placeholder_text = "Nachricht …"
	body_e.custom_minimum_size = Vector2(500, 150)
	body_e.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
	sv.add_child(body_e)
	sv.add_child(UiSkin.label("Anhänge (Rechtsklick auf Gegenstände in den Taschen, max. 6):", 14, UiSkin.TEXT_DIM))
	attach_row = UiSkin.hbox(4)
	sv.add_child(attach_row)
	var mh := UiSkin.hbox(6)
	sv.add_child(mh)
	mh.add_child(UiSkin.label("Gold senden:", 15))
	money_g = SpinBox.new()
	money_g.max_value = 999999
	money_g.suffix = "G"
	mh.add_child(money_g)
	money_s = SpinBox.new()
	money_s.max_value = 99
	money_s.suffix = "S"
	mh.add_child(money_s)
	sv.add_child(UiSkin.rich("Porto: %s pro Brief" % Content.money_bb(30)))
	sv.add_child(UiSkin.button("Senden", func():
		Game.send({"t": "mail_send", "to": to_e.text, "subject": subj_e.text, "body": body_e.text, "slots": attach,
			"copper": int(money_g.value) * 10000 + int(money_s.value) * 100})
		attach = []
		subj_e.text = ""
		body_e.text = ""
		money_g.value = 0
		money_s.value = 0
		_attach()
	, 160))
	position = Vector2(80, 110)


func _on_close() -> void:
	attach = []


func accept_bag_item(slot: int) -> bool:
	if tabs.current_tab != 1:
		tabs.current_tab = 1
	if slot in attach:
		attach.erase(slot)
	elif attach.size() < 6:
		attach.append(slot)
	_attach()
	return true


func _attach() -> void:
	for c in attach_row.get_children():
		c.queue_free()
	for i in 6:
		var s := IconSlot.new(40)
		s.drag_enabled = false
		if i < attach.size():
			var inst = Game.bags[attach[i]] if attach[i] < Game.bags.size() else null
			if inst is Dictionary:
				s.set_item(str(inst["i"]), int(inst.get("n", 1)), inst)
			var slot: int = attach[i]
			s.clicked.connect(func(_s, _b):
				attach.erase(slot)
				_attach()
			)
		attach_row.add_child(s)


func show_mail(m: Dictionary) -> void:
	tabs.current_tab = 0
	_attach()
	for c in inbox.get_children():
		c.queue_free()
	var lst: Array = m.get("list", [])
	if lst.is_empty():
		inbox.add_child(UiSkin.label("Euer Posteingang ist leer.", 15, UiSkin.TEXT_DIM))
	for mail in lst:
		var p := PanelContainer.new()
		p.add_theme_stylebox_override("panel", UiSkin.parchment_box())
		inbox.add_child(p)
		var v := UiSkin.vbox(4)
		p.add_child(v)
		var t := UiSkin.rich("[color=#3a2410][b]%s[/b]  –  von %s[/color]\n[color=#4a3420]%s[/color]" % [mail.get("subject", ""), mail.get("from", ""), mail.get("body", "")])
		t.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0))
		v.add_child(t)
		var h := UiSkin.hbox(4)
		v.add_child(h)
		for it in mail.get("items", []):
			var s := IconSlot.new(40)
			var iid := str(it[0])
			if iid.begins_with("cur:"):
				var cd: Dictionary = Content.defs.get("currencies", {}).get(iid.substr(4), {})
				s.set_icon(Content.icon(str(cd.get("icon", "two-coins")), Color(0.35, 0.3, 0.15), 48), "%d× %s" % [int(it[1]), cd.get("name", iid)])
				s.count = int(it[1])
			else:
				s.set_item(iid, int(it[1]))
			h.add_child(s)
		if int(mail.get("copper", 0)) > 0:
			h.add_child(UiSkin.rich(Content.money_bb(int(mail["copper"]))))
		h.add_child(UiSkin.spacer())
		var mid = mail.get("id")
		var has_stuff: bool = not mail.get("items", []).is_empty() or int(mail.get("copper", 0)) > 0
		h.add_child(UiSkin.button("Nehmen" if has_stuff else "Löschen", func(): Game.send({"t": "mail_take", "id": mid})))
