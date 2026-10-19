class_name MarketWin
extends Win
## Marktplatz / Auktionshaus (GDD 8): Suche mit Filtern (Kategorie, Seltenheit, Stufe, Wert), Preisvergleich,
## Sofortkauf und Gebote, Einstellen mit Gebühren und Laufzeit, eigene Angebote und Verlauf.

var hud
var tabs: TabContainer
# Suche
var q_edit: LineEdit
var cat_opt: OptionButton
var rar_opt: OptionButton
var lmin: SpinBox
var lmax: SpinBox
var stat_opt: OptionButton
var smin: SpinBox
var sort_opt: OptionButton
var results: VBoxContainer
var page_l: Label
var page := 0
var total := 0
# Verkaufen
var sell_slot := -1
var sell_icon: IconSlot
var sell_name: Label
var price_in: _Money
var bid_in: _Money
var dur_opt: OptionButton
var fee_l: RichTextLabel
var price_info: RichTextLabel
# Meine
var mine_box: VBoxContainer

const CATS := [["", "Alle Kategorien"], ["waffe", "Waffen"], ["ruestung", "Rüstung"], ["schmuck", "Schmuck"], ["verbrauch", "Verbrauchsgüter"],
	["material", "Materialien"], ["rezept", "Rezepte"], ["sonstiges", "Sonstiges"]]
const STATS := [["", "Beliebiger Wert"], ["str", "Stärke"], ["agi", "Beweglichkeit"], ["sta", "Ausdauer"], ["int", "Intelligenz"],
	["spi", "Willenskraft"], ["ap", "Angriffskraft"], ["sp", "Zaubermacht"], ["crit", "Kritisch"], ["haste", "Tempo"]]
const SORTS := [["price", "Preis"], ["level", "Stufe"], ["rarity", "Seltenheit"], ["new", "Neueste"]]


func _init(p_hud) -> void:
	super("Marktplatz", "markt", Vector2(820, 600))
	hud = p_hud


func _ready() -> void:
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(800, 540)
	body.add_child(tabs)
	_build_search()
	_build_sell()
	var ms := ScrollContainer.new()
	ms.name = "Meine Auktionen"
	tabs.add_child(ms)
	mine_box = UiSkin.vbox(4)
	mine_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ms.add_child(mine_box)
	tabs.tab_changed.connect(func(i):
		if i == 2:
			Game.send({"t": "market_mine"})
	)
	Game.state_changed.connect(func(w):
		if w == "inventory" and visible:
			_update_sell()
	)


func _on_open() -> void:
	center()


func _on_close() -> void:
	sell_slot = -1


func _opt(items: Array) -> OptionButton:
	var o := OptionButton.new()
	for it in items:
		o.add_item(str(it[1]))
	o.add_theme_font_size_override("font_size", 15)
	return o


func _build_search() -> void:
	var v := UiSkin.vbox(6)
	v.name = "Durchsuchen"
	tabs.add_child(v)
	var r1 := UiSkin.hbox(6)
	v.add_child(r1)
	q_edit = LineEdit.new()
	q_edit.placeholder_text = "Gegenstandsname …"
	q_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	q_edit.text_submitted.connect(func(_t): search(0))
	r1.add_child(q_edit)
	cat_opt = _opt(CATS)
	r1.add_child(cat_opt)
	var rars := [["-1", "Jede Seltenheit"]]
	for i in Content.RARITY_NAMES.size():
		rars.append([str(i), Content.RARITY_NAMES[i] + "+"])
	rar_opt = _opt(rars)
	r1.add_child(rar_opt)
	var r2 := UiSkin.hbox(6)
	v.add_child(r2)
	r2.add_child(UiSkin.label("Stufe", 15))
	lmin = SpinBox.new()
	lmin.min_value = 0
	lmin.max_value = 50
	r2.add_child(lmin)
	r2.add_child(UiSkin.label("–", 15))
	lmax = SpinBox.new()
	lmax.min_value = 0
	lmax.max_value = 50
	lmax.value = 50
	r2.add_child(lmax)
	stat_opt = _opt(STATS)
	r2.add_child(stat_opt)
	r2.add_child(UiSkin.label("min.", 15))
	smin = SpinBox.new()
	smin.max_value = 500
	r2.add_child(smin)
	sort_opt = _opt(SORTS)
	r2.add_child(sort_opt)
	r2.add_child(UiSkin.button("Suchen", func(): search(0), 100))
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(sc)
	results = UiSkin.vbox(3)
	results.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(results)
	var r3 := UiSkin.hbox(8)
	r3.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(r3)
	r3.add_child(UiSkin.button("◀", func(): search(maxi(0, page - 1))))
	page_l = UiSkin.label("", 15)
	r3.add_child(page_l)
	r3.add_child(UiSkin.button("▶", func():
		if (page + 1) * 50 < total:
			search(page + 1)
	))


func search(p: int) -> void:
	page = p
	var m := {"t": "market_search", "q": q_edit.text, "page": p, "lmin": int(lmin.value), "lmax": int(lmax.value),
		"sort": SORTS[sort_opt.selected][0]}
	if cat_opt.selected > 0:
		m["cat"] = CATS[cat_opt.selected][0]
	if rar_opt.selected > 0:
		m["rarity"] = rar_opt.selected - 1
	if stat_opt.selected > 0 and smin.value > 0:
		m["stat"] = STATS[stat_opt.selected][0]
		m["smin"] = smin.value
	Game.send(m)


func _build_sell() -> void:
	var v := UiSkin.vbox(10)
	v.name = "Verkaufen"
	tabs.add_child(v)
	v.add_child(UiSkin.label("Rechtsklickt einen Gegenstand in Euren Taschen oder zieht ihn hierher.", 15, UiSkin.TEXT_DIM))
	var h := UiSkin.hbox(10)
	v.add_child(h)
	sell_icon = IconSlot.new(56)
	sell_icon.accepts_drop = true
	sell_icon.drag_enabled = false
	sell_icon.dropped.connect(func(_s, d):
		if str(d.get("from", "")) == "bag":
			accept_bag_item(int(d.get("index", -1)))
	)
	sell_icon.clicked.connect(func(_s, _b):
		sell_slot = -1
		_update_sell()
	)
	h.add_child(sell_icon)
	sell_name = UiSkin.label("Kein Gegenstand gewählt", 18, UiSkin.TEXT, UiSkin.font_bold)
	h.add_child(sell_name)
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 12)
	g.add_theme_constant_override("v_separation", 8)
	v.add_child(g)
	g.add_child(UiSkin.label("Sofortkaufpreis (gesamt):", 16))
	price_in = _Money.new()
	price_in.changed.connect(_update_fee)
	g.add_child(price_in)
	g.add_child(UiSkin.label("Startgebot (optional):", 16))
	bid_in = _Money.new()
	g.add_child(bid_in)
	g.add_child(UiSkin.label("Laufzeit:", 16))
	dur_opt = _opt([[12, "12 Stunden"], [24, "24 Stunden"], [48, "48 Stunden"]])
	dur_opt.selected = 1
	dur_opt.item_selected.connect(func(_i): _update_fee())
	g.add_child(dur_opt)
	fee_l = UiSkin.rich("")
	v.add_child(fee_l)
	price_info = UiSkin.rich("")
	v.add_child(price_info)
	var b := UiSkin.button("Angebot erstellen", func():
		if sell_slot < 0:
			return
		Game.send({"t": "market_post", "slot": sell_slot, "price": price_in.value(), "bid": bid_in.value(),
			"hours": [12, 24, 48][dur_opt.selected]})
		sell_slot = -1
		_update_sell()
	, 200)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(b)


func accept_bag_item(slot: int) -> bool:
	if tabs.current_tab != 1:
		tabs.current_tab = 1
	sell_slot = slot
	var inst = Game.bags[slot] if slot >= 0 and slot < Game.bags.size() else null
	if inst is Dictionary:
		Game.send({"t": "market_price", "i": inst["i"]})
		var it := Content.item(str(inst["i"]))
		price_in.set_value(maxi(1, int(it.get("sell", 1)) * int(inst.get("n", 1)) * 3))
	_update_sell()
	return true


func _update_sell() -> void:
	var inst = Game.bags[sell_slot] if sell_slot >= 0 and sell_slot < Game.bags.size() else null
	if inst is Dictionary:
		sell_icon.set_item(str(inst["i"]), int(inst.get("n", 1)), inst)
		var it := Content.item(str(inst["i"]))
		sell_name.text = "%s%s" % [it.get("name", ""), (" ×%d" % int(inst["n"])) if int(inst.get("n", 1)) > 1 else ""]
		sell_name.add_theme_color_override("font_color", Content.rarity_color(int(it.get("q", 1))))
	else:
		sell_slot = -1
		sell_icon.clear()
		sell_name.text = "Kein Gegenstand gewählt"
		sell_name.add_theme_color_override("font_color", UiSkin.TEXT)
		price_info.text = ""
	_update_fee()


func _update_fee() -> void:
	var inst = Game.bags[sell_slot] if sell_slot >= 0 and sell_slot < Game.bags.size() else null
	if not (inst is Dictionary):
		fee_l.text = ""
		return
	var it := Content.item(str(inst["i"]))
	var mul = [1, 2, 4][dur_opt.selected]
	var dep := maxi(1, int(int(it.get("sell", 1)) * int(inst.get("n", 1)) * 0.05 * mul))
	var cut := int(price_in.value() * 0.05)
	fee_l.text = "Einstellgebühr: %s   ·   Verkaufsgebühr (5 %%): %s   ·   Ihr erhaltet: %s" % [Content.money_bb(dep), Content.money_bb(cut), Content.money_bb(price_in.value() - cut)]


func on_msg(t: String, m: Dictionary) -> void:
	match t:
		"market":
			_results(m)
		"market_price":
			var n := 1
			var inst = Game.bags[sell_slot] if sell_slot >= 0 and sell_slot < Game.bags.size() else null
			if inst is Dictionary:
				n = int(inst.get("n", 1))
			var s := "[b]Preisvergleich (pro Stück)[/b]\n"
			s += "Günstigstes Angebot: %s   ·   Durchschnitt: %s   (%d Angebote)\n" % [Content.money_bb(int(m.get("min", 0))), Content.money_bb(int(m.get("avg", 0))), int(m.get("count", 0))]
			s += "Zuletzt verkauft für: %s  (%d Verkäufe)   ·   Händlerpreis: %s" % [Content.money_bb(int(m.get("sold_avg", 0))), int(m.get("sold_count", 0)), Content.money_bb(int(m.get("vendor", 0)))]
			price_info.text = s
			if int(m.get("min", 0)) > 0:
				price_in.set_value(maxi(1, int(m["min"]) * n - 1))
		"market_mine":
			_mine(m)


func _results(m: Dictionary) -> void:
	total = int(m.get("total", 0))
	page = int(m.get("page", 0))
	page_l.text = "Seite %d / %d  (%d Angebote)" % [page + 1, maxi(1, ceili(total / 50.0)), total]
	for c in results.get_children():
		c.queue_free()
	if m.get("list", []).is_empty():
		results.add_child(UiSkin.label("Keine Angebote gefunden.", 15, UiSkin.TEXT_DIM))
	for l in m.get("list", []):
		results.add_child(_listing(l, false))


func _listing(l: Dictionary, mine: bool) -> Control:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", UiSkin.inner_box())
	var h := UiSkin.hbox(8)
	p.add_child(h)
	var iid := str(l.get("i", ""))
	var s := IconSlot.new(40)
	s.set_item(iid, int(l.get("n", 1)), l.get("extra", {}))
	s.drag_enabled = false
	h.add_child(s)
	var it := Content.item(iid)
	var nv := UiSkin.vbox(0)
	nv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(nv)
	var nl := UiSkin.label(str(it.get("name", iid)), 15, Content.rarity_color(int(it.get("q", 1))), UiSkin.font_bold)
	nv.add_child(nl)
	nv.add_child(UiSkin.label("Stufe %d  ·  %s  ·  noch %s" % [int(it.get("lvl", 1)), str(l.get("seller", "")), Content.fmt_time(float(l.get("left", 0)))], 13, UiSkin.TEXT_DIM))
	var pv := UiSkin.vbox(0)
	h.add_child(pv)
	var price := int(l.get("price", 0))
	var n := maxi(1, int(l.get("n", 1)))
	pv.add_child(UiSkin.rich("[right]%s[/right]" % Content.money_bb(price)))
	if n > 1:
		pv.add_child(UiSkin.rich("[right][font_size=12]%s / Stück[/font_size][/right]" % Content.money_bb(int(price / n))))
	if int(l.get("start_bid", 0)) > 0:
		var cur_bid := int(l.get("bid", 0))
		pv.add_child(UiSkin.rich("[right][font_size=13]Gebot: %s%s[/font_size][/right]" % [Content.money_bb(cur_bid if cur_bid > 0 else int(l["start_bid"])), " (Ihr)" if l.get("top_bidder", false) else ""]))
	pv.custom_minimum_size.x = 170
	var lid = l.get("id")
	if mine or l.get("mine", false):
		var cb := UiSkin.button("Zurückziehen", func(): Game.send({"t": "market_cancel", "id": lid}))
		h.add_child(cb)
	else:
		var bb := UiSkin.button("Kaufen", func():
			hud.confirm("mbuy", "%s für %s kaufen?" % [it.get("name", ""), Content.money_bb(price)], func():
				Game.send({"t": "market_buy", "id": lid})
				get_tree().create_timer(0.4).timeout.connect(func(): search(page))
			)
		)
		bb.disabled = price > Game.copper
		h.add_child(bb)
		if int(l.get("start_bid", 0)) > 0:
			var minb := maxi(int(l.get("start_bid", 0)), int(int(l.get("bid", 0)) * 1.05) + 1)
			h.add_child(UiSkin.button("Bieten", func():
				hud.ask_text("mbid", "Gebot in Kupfer (mindestens %s):" % Content.money(minb), str(minb), func(t):
					if t.is_valid_int():
						Game.send({"t": "market_bid", "id": lid, "amount": int(t)})
				)
			))
	return p


func _mine(m: Dictionary) -> void:
	for c in mine_box.get_children():
		c.queue_free()
	mine_box.add_child(UiSkin.title_label("Eigene Angebote (%d / 40)" % m.get("list", []).size(), 18))
	for l in m.get("list", []):
		mine_box.add_child(_listing(l, true))
	if not m.get("bids", []).is_empty():
		mine_box.add_child(UiSkin.title_label("Meine Gebote", 18))
		for l in m.get("bids", []):
			mine_box.add_child(_listing(l, false))
	mine_box.add_child(UiSkin.title_label("Verlauf", 18))
	for h in m.get("history", []):
		var it := Content.item(str(h.get("i", "")))
		var sold: bool = h.get("sold", false)
		var line := "%s  %s%s  %s %s%s" % [Time.get_date_string_from_unix_time(int(h.get("t", 0))), it.get("name", ""),
			(" ×%d" % int(h["n"])) if int(h.get("n", 1)) > 1 else "", "verkauft für" if sold else "gekauft für",
			Content.money_bb(int(h.get("price", 0))), ("  (Gebühr %s)" % Content.money_bb(int(h.get("fee", 0)))) if sold and int(h.get("fee", 0)) > 0 else ""]
		mine_box.add_child(UiSkin.rich("[color=%s]%s[/color]" % ["#80ff80" if sold else "#ffd870", line]))


class _Money extends HBoxContainer:
	signal changed
	var g: SpinBox
	var s: SpinBox
	var c: SpinBox

	func _init() -> void:
		add_theme_constant_override("separation", 4)
		g = _spin(999999, "G")
		s = _spin(99, "S")
		c = _spin(99, "K")

	func _spin(mx: int, suffix: String) -> SpinBox:
		var sp := SpinBox.new()
		sp.max_value = mx
		sp.suffix = suffix
		sp.custom_minimum_size.x = 90 if suffix == "G" else 70
		sp.value_changed.connect(func(_v): changed.emit())
		add_child(sp)
		return sp

	func value() -> int:
		return int(g.value) * 10000 + int(s.value) * 100 + int(c.value)

	func set_value(v: int) -> void:
		g.set_value_no_signal(int(v / 10000))
		s.set_value_no_signal(int((v % 10000) / 100))
		c.set_value_no_signal(v % 100)
		changed.emit()
