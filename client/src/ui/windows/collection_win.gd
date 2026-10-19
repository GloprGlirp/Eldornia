class_name CollectionWin
extends Win
## Sammlung (GDD 5/7): Reittiere, Haustiere, kosmetische Skins (Transmogrifikation). Mit 3D-Vorschau.

var hud
var tabs: TabContainer
var mount_list: VBoxContainer
var pet_list: VBoxContainer
var skin_list: VBoxContainer
var preview: ModelPreview
var head: Label

const SLOT_NAMES := {"head": "Kopf", "shoulders": "Schultern", "back": "Rücken", "chest": "Brust", "hands": "Hände", "legs": "Beine",
	"feet": "Füße", "main_hand": "Waffenhand", "off_hand": "Schildhand"}


func _init(p_hud) -> void:
	super("Sammlung", "sammlung", Vector2(720, 540))
	hud = p_hud


func _ready() -> void:
	head = UiSkin.label("", 15, UiSkin.TEXT_DIM)
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	body.add_child(head)
	var h := UiSkin.hbox(10)
	body.add_child(h)
	tabs = TabContainer.new()
	tabs.custom_minimum_size = Vector2(430, 460)
	h.add_child(tabs)
	mount_list = _tab("Reittiere")
	pet_list = _tab("Haustiere")
	skin_list = _tab("Aussehen")
	preview = ModelPreview.new(Vector2(250, 330))
	preview.spin = 0.4
	h.add_child(preview)
	Game.state_changed.connect(func(w):
		if w == "collections" and visible:
			refresh()
	)
	position = Vector2(180, 100)


func _tab(n: String) -> VBoxContainer:
	var sc := ScrollContainer.new()
	sc.name = n
	tabs.add_child(sc)
	var v := UiSkin.vbox(4)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(v)
	return v


func _on_open() -> void:
	Game.send({"t": "get", "w": "collections"})
	refresh()


func open_mode(w: String, _m: Dictionary) -> void:
	tabs.current_tab = 2 if w == "transmog" else 0
	refresh()


func refresh() -> void:
	var c: Dictionary = Game.collections
	for l in [mount_list, pet_list, skin_list]:
		for x in l.get_children():
			x.queue_free()
	if c.is_empty():
		return
	head.text = "Reittiere %d/%d   ·   Haustiere %d/%d   ·   Titel %d/%d   ·   Skins %d/%d" % [
		c.get("mounts", []).size(), int(c.get("all_mounts", 0)), c.get("pets", []).size(), int(c.get("all_pets", 0)),
		c.get("titles", []).size(), int(c.get("all_titles", 0)), c.get("skins", []).size(), int(c.get("all_skins", 0))]
	# Reittiere
	if c.get("mounts", []).is_empty():
		mount_list.add_child(_hint("Noch keine Reittiere. Ab Stufe 10 verkauft Stallmeister Fritz in Eichenau Pferde; seltene Reittiere erbeutet Ihr von Bossen."))
	for m in c.get("mounts", []):
		var mid := str(m["id"])
		var row := _row(Content.icon("horse-head", Color(0.4, 0.28, 0.16), 48), str(m.get("name", mid)),
			"Tempo +%d %%  ·  ab Stufe %d" % [int((float(m.get("speed", 1.6)) - 1.0) * 100), int(m.get("lvl", 10))], {"mount": mid})
		var b := UiSkin.button("Rufen", func(): Game.send({"t": "mount", "m": mid}))
		row.add_child(b)
		var md: Dictionary = m
		row.gui_input.connect(func(ev):
			if ev is InputEventMouseButton and ev.pressed:
				preview.show_creature(str(md.get("model", "horse")), md.get("look", {}), 1.8, 1.3)
		)
		mount_list.add_child(row)
	# Haustiere
	if c.get("pets", []).is_empty():
		pet_list.add_child(_hint("Haustiere findet Ihr als seltene Beute, bei Händlern und als Erfolgsbelohnung."))
	else:
		pet_list.add_child(UiSkin.button("Begleiter wegschicken", func(): Game.send({"t": "companion", "pet": null})))
	for p in c.get("pets", []):
		var pid := str(p["id"])
		var active := str(c.get("pet", "")) == pid
		var row2 := _row(Content.icon("paw", Color(0.3, 0.35, 0.2), 48), str(p.get("name", pid)) + ("  ✓" if active else ""), "Haustier", {})
		row2.add_child(UiSkin.button("Rufen", func(): Game.send({"t": "companion", "pet": pid})))
		var pd: Dictionary = p
		row2.gui_input.connect(func(ev):
			if ev is InputEventMouseButton and ev.pressed:
				if str(pd.get("model", "")) == "humanoid":
					preview.show_humanoid(pd.get("look", {}), {})
				else:
					preview.show_creature(str(pd.get("model", "wolf")), pd.get("look", {}), 0.8, 1.4)
		)
		pet_list.add_child(row2)
	# Skins
	var tm: Dictionary = c.get("transmog", {})
	skin_list.add_child(_hint("Skins verändern nur das Aussehen. Anwenden könnt Ihr sie bei der Schneiderin in Eichenau."))
	for s in SLOT_NAMES:
		var options: Array = c.get("skins", []).filter(func(x): return str(x.get("slot", "")) == s)
		if options.is_empty() and not tm.has(s):
			continue
		skin_list.add_child(UiSkin.label(SLOT_NAMES[s], 16, UiSkin.GOLD, UiSkin.font_bold))
		var slot = s
		var none := UiSkin.button("Original" + (" ✓" if not tm.has(s) else ""), func(): Game.send({"t": "transmog", "slot": slot, "skin": null}))
		skin_list.add_child(none)
		for sk in options:
			var sid := str(sk["id"])
			skin_list.add_child(UiSkin.button(str(sk.get("name", sid)) + (" ✓" if str(tm.get(s, "")) == sid else ""), func():
				Game.send({"t": "transmog", "slot": slot, "skin": sid})
			))
	if hud.world.me and preview.model == null:
		preview.show_humanoid(hud.world.me.look, hud.world.me.look.get("gear", {}))


func _hint(t: String) -> Label:
	var l := UiSkin.label(t, 14, UiSkin.TEXT_DIM)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 400
	return l


func _row(tex: Texture2D, name: String, sub: String, drag: Dictionary) -> HBoxContainer:
	var h := UiSkin.hbox(8)
	h.mouse_filter = Control.MOUSE_FILTER_STOP
	var s := IconSlot.new(40)
	s.set_icon(tex, name)
	if not drag.is_empty():
		s.payload = drag
	else:
		s.drag_enabled = false
	h.add_child(s)
	var v := UiSkin.vbox(0)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(UiSkin.label(name, 16, UiSkin.TEXT, UiSkin.font_bold))
	v.add_child(UiSkin.label(sub, 13, UiSkin.TEXT_DIM))
	h.add_child(v)
	return h
