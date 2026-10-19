class_name PartyFrames
extends VBoxContainer
## Gruppen- und Schlachtzugsrahmen (bis zu 10 Spieler): Name, Rolle, Gesundheit, Ressource, Schwächungen.

var hud
var frames: Array = []


func _init(p_hud) -> void:
	hud = p_hud
	add_theme_constant_override("separation", 4)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	Game.state_changed.connect(func(w):
		if w == "party":
			_rebuild()
	)


func _rebuild() -> void:
	for c in get_children():
		c.queue_free()
	frames.clear()
	var members: Array = Game.party.get("members", [])
	var raid: bool = Game.party.get("raid", false)
	for m in members:
		if int(m.get("id", 0)) == Game.me_id:
			continue
		var f := _Member.new(hud, m, raid)
		add_child(f)
		frames.append(f)


func _process(_d: float) -> void:
	for f in frames:
		if is_instance_valid(f):
			f.tick()


class _Member extends Control:
	var hud
	var d: Dictionary
	var hp: StatBar
	var pw: StatBar
	var name_l: Label
	var info_l: Label
	var role_i: TextureRect
	var debuffs: HBoxContainer
	var compact := false
	var _sig := ""

	func _init(p_hud, p_d: Dictionary, p_compact: bool) -> void:
		hud = p_hud
		d = p_d
		compact = p_compact
		custom_minimum_size = Vector2(190, 40 if compact else 52)
		mouse_filter = Control.MOUSE_FILTER_STOP

	func _ready() -> void:
		var bg := Panel.new()
		bg.add_theme_stylebox_override("panel", UiSkin.flat(Color(0.03, 0.02, 0.02, 0.75), Color(0.45, 0.35, 0.2), 1, 4))
		bg.set_anchors_preset(Control.PRESET_FULL_RECT)
		bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(bg)
		role_i = TextureRect.new()
		role_i.position = Vector2(4, 4)
		role_i.size = Vector2(16, 16)
		role_i.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		role_i.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var role := str(d.get("role", "dps"))
		role_i.texture = Content.icon({"tank": "shield", "heiler": "health-normal", "dps": "crossed-swords"}.get(role, "crossed-swords"),
			{"tank": Color(0.2, 0.3, 0.6), "heiler": Color(0.2, 0.5, 0.2), "dps": Color(0.55, 0.15, 0.1)}.get(role, Color(0.4, 0.2, 0.1)), 32)
		add_child(role_i)
		name_l = UiSkin.label(str(d.get("name", "")), 14, Content.class_color(str(d.get("cls", ""))), UiSkin.font_bold)
		name_l.position = Vector2(24, 1)
		name_l.size = Vector2(120, 18)
		name_l.clip_text = true
		name_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(name_l)
		info_l = UiSkin.label("", 12, Color(1, 0.85, 0.3))
		info_l.position = Vector2(146, 2)
		info_l.size = Vector2(40, 16)
		info_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		info_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(info_l)
		hp = StatBar.new(Color("#1fa81f"), 14)
		hp.position = Vector2(4, 21)
		hp.size = Vector2(182, 13 if not compact else 10)
		hp.text_size = 11
		add_child(hp)
		if not compact:
			pw = StatBar.new(Content.power_color(str(d.get("pt", "mana"))), 6)
			pw.position = Vector2(4, 36)
			pw.size = Vector2(182, 6)
			pw.show_text = false
			add_child(pw)
		debuffs = UiSkin.hbox(1)
		debuffs.position = Vector2(192, 4)
		debuffs.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(debuffs)

	func _gui_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.pressed:
			var id := int(d.get("id", 0))
			if ev.button_index == MOUSE_BUTTON_LEFT and hud.world.ent(id):
				hud.world.set_target(id)
			elif ev.button_index == MOUSE_BUTTON_RIGHT:
				if hud.world.ent(id):
					hud._unit_menu(id)
				else:
					_menu_far(id)
			accept_event()

	func _menu_far(id: int) -> void:
		var pm := PopupMenu.new()
		pm.add_item("Flüstern")
		if hud._is_leader():
			pm.add_item("Aus Gruppe entfernen")
			pm.add_item("Zum Anführer machen")
		pm.id_pressed.connect(func(i):
			match i:
				0: hud.chat.start_whisper(str(d.get("name", "")))
				1: Game.send({"t": "party_kick", "id": id})
				2: Game.send({"t": "party_lead", "id": id})
		)
		pm.popup_hide.connect(pm.queue_free)
		add_child(pm)
		pm.position = Vector2i(get_global_mouse_position())
		pm.popup()

	func tick() -> void:
		var id := int(d.get("id", 0))
		var e = hud.world.ent(id)
		var cur_hp := int(d.get("hp", 0))
		var cur_mhp := int(d.get("mhp", 1))
		var cur_pw := int(d.get("pw", 0))
		var cur_mpw := int(d.get("mpw", 0))
		var dead: bool = d.get("dead", false)
		var auras: Array = d.get("au", [])
		if e:
			cur_hp = e.hp
			cur_mhp = e.mhp
			cur_pw = e.pw
			cur_mpw = e.mpw
			dead = e.dead
			auras = e.auras.filter(func(a): return a is Array and int(a[5]) == 1)
		var near: bool = e != null
		modulate = Color(1, 1, 1, 1.0 if near else 0.55)
		if dead:
			hp.set_values(0, 1, "Tot")
		else:
			hp.set_values(cur_hp, maxf(1, cur_mhp), "%d %%" % int(100.0 * cur_hp / maxf(1, cur_mhp)))
		hp.color = Color("#1fa81f") if float(cur_hp) / maxf(1, cur_mhp) > 0.35 else Color("#d8a020")
		if pw:
			pw.set_values(cur_pw, maxf(1, cur_mpw))
		var lead: bool = int(Game.party.get("leader", 0) if Game.party.get("leader") != null else 0) == id
		info_l.text = ("♛ " if lead else "") + str(d.get("lvl", ""))
		if not near and str(d.get("zone", "")) != "":
			name_l.tooltip_text = str(d.get("zone", ""))
		var sig := str(auras.size()) + ",".join(auras.map(func(a): return str(a[0])))
		if sig != _sig:
			_sig = sig
			for c in debuffs.get_children():
				c.queue_free()
			for a in auras.slice(0, 4):
				var t := TextureRect.new()
				t.texture = Content.icon(str(a[4]) if str(a[4]) != "" else "poison-bottle", Color(0.45, 0.08, 0.08), 32)
				t.custom_minimum_size = Vector2(18, 18)
				t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
				t.tooltip_text = str(a[1])
				debuffs.add_child(t)
