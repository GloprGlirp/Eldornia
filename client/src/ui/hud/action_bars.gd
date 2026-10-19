class_name ActionBars
extends Control
## Aktionsleisten (GDD 4: Fähigkeiten auf 1–6 und mehr, Abklingzeiten sichtbar). Fähigkeiten, Gegenstände,
## Reittiere und Emotes können per Ziehen & Ablegen belegt werden.

var world
var slots: Array = []
var bar1: HBoxContainer
var bar2: HBoxContainer
var bar3: VBoxContainer
const KEYS1 := ["aktion_1", "aktion_2", "aktion_3", "aktion_4", "aktion_5", "aktion_6", "aktion_7", "aktion_8", "aktion_9",
	"aktion_10", "aktion_11", "aktion_12"]
const KEYS2 := ["leiste2_1", "leiste2_2", "leiste2_3", "leiste2_4", "leiste2_5", "leiste2_6"]


func _init(p_world) -> void:
	world = p_world
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	bar2 = UiSkin.hbox(3)
	add_child(bar2)
	bar1 = UiSkin.hbox(3)
	add_child(bar1)
	bar3 = UiSkin.vbox(3)
	add_child(bar3)
	for i in 36:
		var s := IconSlot.new(46 if i < 24 else 38)
		s.kind = "bar"
		s.index = i
		s.accepts_drop = true
		s.clicked.connect(_on_click)
		s.dropped.connect(_on_drop)
		slots.append(s)
		if i < 12:
			bar1.add_child(s)
			s.keybind = Settings.short_key_label(KEYS1[i])
		elif i < 24:
			bar2.add_child(s)
			if i - 12 < 6:
				s.keybind = Settings.short_key_label(KEYS2[i - 12])
		else:
			bar3.add_child(s)
	Game.state_changed.connect(_on_state)
	refresh()


func layout(vp: Vector2) -> void:
	var w1 := 12 * 49
	bar1.position = Vector2((vp.x - w1) * 0.5, vp.y - 66)
	bar2.position = Vector2((vp.x - w1) * 0.5, vp.y - 118)
	bar3.position = Vector2(vp.x - 46, vp.y * 0.5 - 12 * 41 * 0.5 + 40)


func _on_state(what: String) -> void:
	if what in ["abilities", "inventory", "cooldowns", "collections"]:
		refresh()


func refresh() -> void:
	for i in slots.size():
		var s: IconSlot = slots[i]
		var e = Game.bars[i] if i < Game.bars.size() else null
		s.payload = {}
		if e is Dictionary:
			if e.has("ab") and Game.abilities.has(str(e["ab"])):
				s.set_ability(Game.abilities[str(e["ab"])])
				s.payload = {"ab": e["ab"]}
			elif e.has("ab"):
				s.clear()
			elif e.has("item"):
				s.set_item(str(e["item"]), Game.count_item(str(e["item"])))
				s.quality = -1
				s.payload = {"item": e["item"]}
				s.dim = Game.count_item(str(e["item"])) == 0
			elif e.has("mount"):
				var md: Dictionary = Content.defs.get("mounts", {}).get(str(e["mount"]), {})
				s.set_icon(Content.icon("horse-head", Color(0.4, 0.3, 0.2)), "[b]%s[/b]\nReittier rufen" % md.get("name", e["mount"]))
				s.payload = {"mount": e["mount"]}
			elif e.has("emote"):
				s.set_icon(Content.icon("chat-bubble", Color(0.3, 0.3, 0.4)), "Emote: /%s" % e["emote"])
				s.payload = {"emote": e["emote"]}
		else:
			s.clear()


func _process(_d: float) -> void:
	var me = world.me if world else null
	var tgt = world.ent(world.target) if world else null
	var power = me.pw if me else 0
	for s in slots:
		var p: Dictionary = s.payload
		if p.has("ab"):
			var id := str(p["ab"])
			var ab: Dictionary = Game.abilities.get(id, {})
			var cd := Game.cd_left(id)
			var g := Game.gcd_left() if ab.get("gcd", true) else 0.0
			if cd > g and cd > 0:
				s.cd_end = Game.cooldowns.get(id, 0.0)
				s.cd_total = float(Game.cd_total.get(id, ab.get("cd", cd)))
				s.gcd = false
			elif g > 0:
				s.cd_end = Game.gcd_end
				s.cd_total = Game.gcd_total
				s.gcd = true
			else:
				s.cd_end = 0.0
			var cost := int(ab.get("cost", 0))
			var pct := float(ab.get("cost_pct", 0))
			if pct > 0 and me:
				cost = int(pct * (40 + 15 * Game.level + int(Game.stats.get("int", 10)) * 12 * 0.4))
			s.dim = cost > power
			var red := false
			if tgt and str(ab.get("target")) == "enemy" and me and tgt.is_attackable():
				var d: float = me.global_position.distance_to(tgt.global_position) - tgt.radius
				var rng := float(ab.get("range", 5.0)) + (1.5 if ab.get("melee", false) else 0.5)
				red = d > rng
			s.red = red
			var req: Dictionary = ab.get("req", {})
			s.glow = false
			if req.has("after"):
				for k in req["after"]:
					if Game.now() < float(Game.reactive_until.get(k, 0)):
						s.glow = true
				s.dim = s.dim or not s.glow
			if req.has("execute") and tgt and tgt.mhp > 0:
				var low: bool = float(tgt.hp) / tgt.mhp <= float(req["execute"])
				s.glow = low
				s.dim = s.dim or not low
			if req.has("combo"):
				s.dim = s.dim or Game.combo < int(req["combo"])
		elif p.has("item"):
			var iid := str(p["item"])
			var n := Game.count_item(iid)
			if s.count != n:
				s.count = n
				s.dim = n == 0
				s.queue_redraw()
			var use: Dictionary = Content.item(iid).get("use", {})
			if str(use.get("type", "")) in ["heal", "mana"]:
				var cd2 := Game.cd_left("trank")
				s.cd_end = Game.cooldowns.get("trank", 0.0) if cd2 > 0 else 0.0
				s.cd_total = 60.0
			elif str(use.get("type", "")) == "hearth":
				var cd3 := Game.cd_left("ruhestein")
				s.cd_end = Game.cooldowns.get("ruhestein", 0.0) if cd3 > 0 else 0.0
				s.cd_total = 900.0


func trigger(i: int) -> void:
	if i < 0 or i >= slots.size():
		return
	var s: IconSlot = slots[i]
	if s.payload.is_empty():
		return
	world.use_bar_entry(s.payload)
	var tw := s.create_tween()
	s.pivot_offset = s.size * 0.5
	tw.tween_property(s, "scale", Vector2(0.9, 0.9), 0.05)
	tw.tween_property(s, "scale", Vector2(1, 1), 0.08)


func handle_key(ev: InputEventKey) -> bool:
	for i in 12:
		if Settings.is_action(ev, KEYS1[i]):
			trigger(i)
			return true
	for i in 6:
		if Settings.is_action(ev, KEYS2[i]):
			trigger(12 + i)
			return true
	return false


func _on_click(s: IconSlot, button: int) -> void:
	if Input.is_key_pressed(KEY_SHIFT) and button == MOUSE_BUTTON_LEFT:
		return
	trigger(s.index)


func _on_drop(s: IconSlot, data: Dictionary) -> void:
	var entry = null
	if data.has("ab"):
		entry = {"ab": data["ab"]}
	elif data.has("item"):
		var it := Content.item(str(data["item"]))
		if str(it.get("type", "")) == "consumable":
			entry = {"item": data["item"]}
	elif data.has("mount"):
		entry = {"mount": data["mount"]}
	elif data.has("emote"):
		entry = {"emote": data["emote"]}
	if entry == null:
		return
	while Game.bars.size() < 36:
		Game.bars.append(null)
	var old = Game.bars[s.index]
	Game.bars[s.index] = entry
	if str(data.get("from", "")) == "bar":
		var fi := int(data.get("index", -1))
		if fi >= 0 and fi != s.index:
			Game.bars[fi] = old
	Game.save_bars()
	refresh()


## Wird von der HUD aufgerufen, wenn ein Leistenplatz ins Leere gezogen wurde.
func remove_from(i: int) -> void:
	if i >= 0 and i < Game.bars.size():
		Game.bars[i] = null
		Game.save_bars()
		refresh()
