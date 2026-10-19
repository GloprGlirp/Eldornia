class_name TradeWin
extends Win
## Direkter Handel zwischen zwei Spielern (GDD 10). Beide Seiten sperren ihr Angebot und bestätigen;
## der Server tauscht atomar.

var hud
var data: Dictionary = {}
var my_slots: Array = []
var my_box: GridContainer
var their_box: GridContainer
var my_money: SpinBox
var their_money: RichTextLabel
var my_state: Label
var their_state: Label
var lock_btn: Button
var ok_btn: Button
var their_name: Label


func _init(p_hud) -> void:
	super("Handel", "handel", Vector2(560, 380))
	hud = p_hud


func _ready() -> void:
	var h := UiSkin.hbox(16)
	body.add_child(h)
	var lv := UiSkin.vbox(6)
	h.add_child(lv)
	lv.add_child(UiSkin.title_label(Game.me_name, 18))
	my_box = GridContainer.new()
	my_box.columns = 3
	lv.add_child(my_box)
	var mh := UiSkin.hbox(4)
	lv.add_child(mh)
	mh.add_child(UiSkin.label("Gold:", 15))
	my_money = SpinBox.new()
	my_money.max_value = 999999
	my_money.suffix = "G"
	my_money.value_changed.connect(func(_v): _send())
	mh.add_child(my_money)
	my_state = UiSkin.label("", 15, UiSkin.TEXT_DIM)
	lv.add_child(my_state)
	var rv := UiSkin.vbox(6)
	h.add_child(rv)
	their_name = UiSkin.title_label("", 18)
	rv.add_child(their_name)
	their_box = GridContainer.new()
	their_box.columns = 3
	rv.add_child(their_box)
	their_money = UiSkin.rich("")
	rv.add_child(their_money)
	their_state = UiSkin.label("", 15, UiSkin.TEXT_DIM)
	rv.add_child(their_state)
	var bh := UiSkin.hbox(8)
	bh.alignment = BoxContainer.ALIGNMENT_CENTER
	body.add_child(bh)
	lock_btn = UiSkin.button("Angebot sperren", func(): Game.send({"t": "trade_lock"}))
	bh.add_child(lock_btn)
	ok_btn = UiSkin.button("Handeln", func(): Game.send({"t": "trade_confirm"}))
	bh.add_child(ok_btn)
	bh.add_child(UiSkin.button("Abbrechen", func(): close_win()))
	position = Vector2(300, 140)


func _on_close() -> void:
	if not data.is_empty():
		Game.send({"t": "trade_cancel"})
	data = {}
	my_slots = []


func accept_bag_item(slot: int) -> bool:
	if data.get("my_lock", false):
		return true
	if slot in my_slots:
		my_slots.erase(slot)
	elif my_slots.size() < 6:
		my_slots.append(slot)
	_send()
	return true


func _send() -> void:
	if data.is_empty():
		return
	Game.send({"t": "trade_set", "slots": my_slots, "copper": int(my_money.value) * 10000})


func show_trade(m: Dictionary) -> void:
	data = m
	my_slots = m.get("my_slots", [])
	their_name.text = str(m.get("with", ""))
	_fill(my_box, m.get("mine", []), true)
	_fill(their_box, m.get("theirs", []), false)
	my_money.set_value_no_signal(int(m.get("my_copper", 0)) / 10000)
	my_money.editable = not m.get("my_lock", false)
	their_money.text = "Gold: " + Content.money_bb(int(m.get("their_copper", 0)))
	my_state.text = "✔ Bestätigt" if m.get("my_ok", false) else ("🔒 Gesperrt" if m.get("my_lock", false) else "Offen")
	their_state.text = "✔ Bestätigt" if m.get("their_ok", false) else ("🔒 Gesperrt" if m.get("their_lock", false) else "Offen")
	lock_btn.disabled = m.get("my_lock", false)
	ok_btn.disabled = not (m.get("my_lock", false) and m.get("their_lock", false)) or m.get("my_ok", false)


func _fill(box: GridContainer, items: Array, mine: bool) -> void:
	for c in box.get_children():
		c.queue_free()
	for i in 6:
		var s := IconSlot.new(46)
		s.drag_enabled = false
		if i < items.size() and items[i] is Dictionary:
			s.set_item(str(items[i]["i"]), int(items[i].get("n", 1)), items[i])
			if mine:
				var idx := i
				s.clicked.connect(func(_s, _b):
					if idx < my_slots.size() and not data.get("my_lock", false):
						my_slots.remove_at(idx)
						_send()
				)
		if mine:
			s.accepts_drop = true
			s.dropped.connect(func(_s, d):
				if str(d.get("from", "")) == "bag":
					accept_bag_item(int(d.get("index", -1)))
			)
		box.add_child(s)
