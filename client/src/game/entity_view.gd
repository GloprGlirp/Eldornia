class_name EntityView
extends Node3D
## Darstellung einer Einheit vom Server (Spieler, NPC, Gegner, Begleiter, Objekt, Falle, Bodeneffekt)
## mit Positionsinterpolation, Animationen, Reittier und Begleiter-Haustier.

var id := 0
var kind := ""                 # player, npc, mob, pet, obj, trap, ground
var info: Dictionary = {}
var name_text := ""
var title := ""
var level := 1
var hp := 1
var mhp := 1
var pw := 0
var mpw := 0
var pt := ""
var target_id := 0
var flags := 0
var auras: Array = []
var cast = null
var cast_start := 0.0
var fl: Dictionary = {}
var hostile := false
var side := "neutral"
var radius := 0.5
var height := 1.9
var look: Dictionary = {}
var model: Node3D
var mount_model: Node3D
var companion_model: Node3D
var is_me := false
var world
var _snaps: Array = []          # [t, pos, rot]
var _vel := Vector3.ZERO
var _last_pos := Vector3.ZERO
var _move_speed := 0.0
var _dash: Dictionary = {}
var _jump_t := -1.0
var dead := false
var emote := ""
var team = null
var stealth := false
var hidden_by_stealth := false
var swim := false
var _comp_phase := 0.0
var quest_mark := ""
var mark_node: Label3D
var shadow_blob: MeshInstance3D

const INTERP_DELAY := 0.12


func setup(p_world, d: Dictionary) -> void:
	world = p_world
	id = int(d["id"])
	kind = str(d.get("k", ""))
	is_me = id == Game.me_id
	info = d
	apply(d, true)
	_build_model()
	var p: Array = d.get("p", [0, 0, 0, 0])
	position = Vector3(float(p[0]), float(p[1]), float(p[2]))
	rotation.y = float(p[3])
	_last_pos = position
	_snaps = [[Game.now(), position, rotation.y]]


func apply(d: Dictionary, initial := false) -> void:
	if d.has("name"):
		name_text = str(d["name"])
		title = str(d.get("title", ""))
	if d.has("lvl"):
		level = int(d["lvl"])
	if d.has("hp"):
		var old := hp
		hp = int(d["hp"])
		mhp = maxi(1, int(d.get("mhp", mhp)))
		if not initial and hp < old and model and model.has_method("hit_react") and not dead:
			model.hit_react()
	if d.has("pw"):
		pw = int(d["pw"])
		mpw = int(d.get("mpw", mpw))
		pt = str(d.get("pt", pt)) if d.get("pt") != null else pt
	if d.has("tg"):
		target_id = int(d["tg"]) if d["tg"] != null else 0
	if d.has("st"):
		flags = int(d["st"])
		var was_dead := dead
		dead = (flags & 1) != 0
		if model and model.has_method("set_dead") and dead != was_dead:
			model.set_dead(dead)
		if model:
			if "sitting" in model:
				model.sitting = (flags & 4) != 0
			if "combat" in model:
				model.combat = (flags & 2) != 0
		stealth = (flags & 32) != 0
		_update_stealth()
	if d.has("au"):
		auras = d["au"]
		_update_stealth()
	if d.has("cast"):
		cast = d["cast"]
		cast_start = Game.now()
		if model:
			var casting: bool = cast != null and not bool(cast.get("ch", false))
			var chan: bool = cast != null and bool(cast.get("ch", false))
			if "casting" in model:
				model.casting = casting
			if "channeling" in model:
				model.channeling = chan
			if cast != null and "cast_color" in model:
				model.cast_color = Fx.school_color(str(cast.get("school", "arcane")))
	if d.has("fl"):
		fl = d["fl"]
		_update_mark()
	if d.has("hostile"):
		hostile = bool(d["hostile"])
	if d.has("side"):
		side = str(d["side"])
	if d.has("rad"):
		radius = float(d["rad"])
	if d.has("team"):
		team = d["team"]
	if d.has("emote"):
		emote = str(d["emote"]) if d["emote"] != null else ""
		if model and "emote" in model:
			model.emote = emote
	if d.has("look") and not initial:
		look = d["look"]
		_rebuild_on_look()
	elif d.has("look"):
		look = d["look"]
	if d.has("model") and not initial:
		info["model"] = d["model"]
		info["scale"] = d.get("scale", 1.0)
		_build_model()
	if d.has("p") and not initial and not is_me:
		var p: Array = d["p"]
		_snaps.append([Game.now(), Vector3(float(p[0]), float(p[1]), float(p[2])), float(p[3])])
		if _snaps.size() > 8:
			_snaps.pop_front()


func _update_stealth() -> void:
	var st := stealth
	for a in auras:
		if a is Array and a.size() > 8 and (int(a[8]) & 8) != 0:
			st = true
	if model:
		var a := 0.35 if st else 1.0
		_set_alpha(model, a)


func _set_alpha(n: Node, a: float) -> void:
	for c in n.get_children():
		if c is GeometryInstance3D:
			c.transparency = 1.0 - a
		_set_alpha(c, a)


# ------------------------------------------------------------------ Modelle
func _build_model() -> void:
	if model:
		model.queue_free()
		model = null
	var m := str(info.get("model", "human"))
	var sc := float(info.get("scale", 1.0))
	match kind:
		"player":
			var gear: Dictionary = look.get("gear", {})
			var l := look.duplicate()
			l.erase("gear")
			if l.get("form") == "baer":
				model = CreatureModel.new("bear", {"tint": "#5a3e2a"})
				height = 1.6
			else:
				model = HumanoidModel.new(l, gear)
				height = 1.9 if l.get("kind") != "dwarf" else 1.4
		"npc":
			if m == "humanoid" or m == "human":
				model = HumanoidModel.new(look, {})
				height = (1.9 if look.get("kind", "human") != "dwarf" else 1.4) * (0.75 if look.get("kind") == "kobold" else 1.0)
			else:
				model = CreatureModel.new(m, look)
				height = 1.5
		"mob", "pet":
			if m == "humanoid" or m == "human":
				var l2 := look.duplicate()
				if l2.get("poly", false):
					model = CreatureModel.new("ram", {"tint": "#f4f0e8", "tint2": "#e8e0d0"})
					sc = 0.6
					height = 0.9
				else:
					model = HumanoidModel.new(l2, {})
					height = 1.9 * (0.75 if l2.get("kind") == "kobold" else (0.8 if l2.get("kind") == "dwarf" else 1.0))
			else:
				if look.get("poly", false):
					model = CreatureModel.new("ram", {"tint": "#f4f0e8", "tint2": "#e8e0d0"})
					sc = 0.6
				else:
					model = CreatureModel.new(m, look)
				height = model.top_height() if model.has_method("top_height") else 1.4
		"obj":
			model = ObjectModels.make(info)
			height = 1.2
		"trap":
			model = ObjectModels.make({"model": str(info.get("model", "trap_frost")), "obj": "trap"})
			height = 0.3
		"ground":
			model = ObjectModels.ground_effect(str(info.get("fx", "fire")), float(info.get("r2", 4.0)))
			height = 0.1
		_:
			model = Node3D.new()
	model.scale = Vector3.ONE * sc
	add_child(model)
	height *= sc
	if model.has_method("set_dead") and dead:
		model.set_dead(true)
	if "emote" in model:
		model.emote = emote
	_update_stealth()
	_update_mount()
	_update_companion()
	if shadow_blob == null and kind in ["player", "npc", "mob", "pet"]:
		shadow_blob = MeshInstance3D.new()
		var q := PlaneMesh.new()
		q.size = Vector2(1.4, 1.4) * maxf(0.6, radius * 1.4)
		shadow_blob.mesh = q
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.albedo_texture = FxLib.soft_tex()
		mat.albedo_color = Color(0, 0, 0, 0.35)
		mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
		shadow_blob.material_override = mat
		shadow_blob.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		shadow_blob.position.y = 0.04
		add_child(shadow_blob)


func _rebuild_on_look() -> void:
	if kind == "player":
		var gear: Dictionary = look.get("gear", {})
		var l := look.duplicate()
		l.erase("gear")
		var want_bear: bool = l.get("form") == "baer"
		var is_bear: bool = model is CreatureModel
		if want_bear != is_bear:
			_build_model()
			return
		if model is HumanoidModel:
			var hm: HumanoidModel = model
			var old_gear := JSON.stringify(hm.gear)
			var old_look := JSON.stringify(_strip(hm.look))
			if old_gear != JSON.stringify(gear) or old_look != JSON.stringify(_strip(l)):
				hm.look = l
				hm.set_gear(gear)
				_update_stealth()
		_update_mount()
		_update_companion()
	elif kind in ["mob", "pet", "npc"]:
		_build_model()


func _strip(l: Dictionary) -> Dictionary:
	var o := l.duplicate()
	for k in ["mount", "companion", "guild_name", "form"]:
		o.erase(k)
	return o


func _update_mount() -> void:
	var mt = look.get("mount")
	if mt is Dictionary:
		if mount_model == null or mount_model.get_meta("mid", "") != str(mt.get("id")):
			if mount_model:
				mount_model.queue_free()
			var species := str(mt.get("model", "horse"))
			species = {"wolf_mount": "wolf", "gryphon": "dragon", "moth": "bird"}.get(species, species)
			var ml: Dictionary = mt.get("look", {}).duplicate()
			ml["saddle"] = true
			mount_model = CreatureModel.new(species, ml)
			mount_model.set_meta("mid", str(mt.get("id")))
			var s := float(ml.get("scale", 1.0))
			if species == "wolf":
				s *= 1.6
			mount_model.scale = Vector3.ONE * s
			add_child(mount_model)
		if model:
			model.position.y = 0.95 * mount_model.scale.y if str(mt.get("model", "")) != "wolf_mount" else 0.9
			if "mounted" in model:
				model.mounted = true
	else:
		if mount_model:
			mount_model.queue_free()
			mount_model = null
		if model:
			model.position.y = 0.0
			if "mounted" in model:
				model.mounted = false


func _update_companion() -> void:
	var c = look.get("companion")
	if c is Dictionary:
		if companion_model == null or companion_model.get_meta("cid", "") != str(c.get("id")):
			if companion_model:
				companion_model.queue_free()
			var m := str(c.get("model", "chicken"))
			var l: Dictionary = c.get("look", {})
			if m == "humanoid":
				companion_model = HumanoidModel.new(l, {})
			else:
				companion_model = CreatureModel.new(m, l)
			companion_model.scale = Vector3.ONE * float(l.get("scale", 0.6))
			companion_model.set_meta("cid", str(c.get("id")))
			world.add_child(companion_model)
			companion_model.global_position = global_position + Vector3(1.2, 0, 1.2)
	elif companion_model:
		companion_model.queue_free()
		companion_model = null


func _update_mark() -> void:
	var q = fl.get("q")
	var want := str(q) if q != null else ""
	if fl.get("l", false):
		want = "loot"
	if want == quest_mark:
		return
	quest_mark = want
	if mark_node:
		mark_node.queue_free()
		mark_node = null
	if want == "":
		return
	mark_node = Label3D.new()
	mark_node.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	mark_node.no_depth_test = false
	mark_node.font = UiSkin.font_deco
	mark_node.font_size = 96
	mark_node.pixel_size = 0.006
	mark_node.outline_size = 18
	mark_node.outline_modulate = Color(0.15, 0.08, 0.0)
	match want:
		"!":
			mark_node.text = "!"
			mark_node.modulate = Color(1.0, 0.85, 0.1)
		"!b":
			mark_node.text = "!"
			mark_node.modulate = Color(0.35, 0.65, 1.0)
		"!g":
			mark_node.text = "!"
			mark_node.modulate = Color(0.55, 0.55, 0.55)
		"?":
			mark_node.text = "?"
			mark_node.modulate = Color(1.0, 0.85, 0.1)
		"?b":
			mark_node.text = "?"
			mark_node.modulate = Color(0.35, 0.65, 1.0)
		"?g":
			mark_node.text = "?"
			mark_node.modulate = Color(0.6, 0.6, 0.6)
		"loot":
			mark_node.text = "✦"
			mark_node.font_size = 60
			mark_node.modulate = Color(1.0, 0.9, 0.4)
	add_child(mark_node)
	mark_node.position = Vector3(0, height + 0.75, 0)


# ------------------------------------------------------------------ Hilfen für Effekte
func chest_pos() -> Vector3:
	return global_position + Vector3.UP * (height * 0.6 + (0.9 if mount_model else 0.0))


func head_pos() -> Vector3:
	return global_position + Vector3.UP * (height + (0.9 if mount_model else 0.0))


func hand_pos() -> Vector3:
	var fwd := -global_transform.basis.z
	return global_position + Vector3.UP * (height * 0.65 + (0.9 if mount_model else 0.0)) + fwd * 0.5 + global_transform.basis.x * 0.25


func play_attack() -> void:
	if model and model.has_method("attack"):
		model.attack()


func cast_release() -> void:
	if model and model.has_method("cast_release"):
		model.cast_release()


func jump() -> void:
	_jump_t = 0.0


func dash_to(p: Vector3, dur: float, arc: bool) -> void:
	_dash = {"from": global_position, "to": p, "t": 0.0, "dur": dur, "arc": arc}


func is_enemy() -> bool:
	if kind == "player":
		return bool(fl.get("en", false))
	if kind in ["mob"]:
		return hostile or bool(look.get("critter", false)) or bool(look.get("dummy", false))
	return false


func is_attackable() -> bool:
	return not dead and is_enemy()


func reaction_color() -> Color:
	if kind == "player":
		if fl.get("en", false):
			return Color(1.0, 0.2, 0.15)
		return Color(0.3, 0.6, 1.0)
	if kind == "npc":
		return Color(0.3, 1.0, 0.3)
	if kind == "pet":
		return Color(0.3, 0.6, 1.0)
	if kind == "mob":
		if fl.get("tap", false):
			return Color(0.55, 0.55, 0.55)
		if look.get("critter", false) or look.get("dummy", false):
			return Color(1.0, 1.0, 0.2)
		if look.get("aggro", false):
			return Color(1.0, 0.2, 0.15)
		return Color(1.0, 0.95, 0.2)
	return Color(1, 1, 1)


func has_aura_flag(bit: int) -> bool:
	for a in auras:
		if a is Array and a.size() > 8 and (int(a[8]) & bit) != 0:
			return true
	return false


# ------------------------------------------------------------------ Bewegung
func _process(delta: float) -> void:
	var t := Game.now()
	if not _dash.is_empty():
		_dash["t"] += delta
		var k := clampf(_dash["t"] / _dash["dur"], 0.0, 1.0)
		var p: Vector3 = _dash["from"].lerp(_dash["to"], k)
		if _dash["arc"]:
			p.y += sin(k * PI) * 3.0
		position = p
		if k >= 1.0:
			_dash = {}
			_snaps = [[t, position, rotation.y]]
	elif not is_me:
		var rt := t - INTERP_DELAY
		var pos: Vector3 = position
		var rot := rotation.y
		if _snaps.size() == 1:
			pos = _snaps[0][1]
			rot = _snaps[0][2]
		else:
			var found := false
			for i in range(_snaps.size() - 1):
				var a: Array = _snaps[i]
				var b: Array = _snaps[i + 1]
				if rt >= a[0] and rt <= b[0]:
					var f: float = (rt - a[0]) / maxf(0.001, b[0] - a[0])
					pos = a[1].lerp(b[1], f)
					rot = lerp_angle(a[2], b[2], f)
					found = true
					break
			if not found:
				var last: Array = _snaps[_snaps.size() - 1]
				if rt > last[0]:
					pos = last[1]
					rot = last[2]
				else:
					pos = _snaps[0][1]
					rot = _snaps[0][2]
		# Bodenhöhe lokal, damit Figuren nicht schweben
		if kind in ["npc", "mob", "pet", "player"] and world and not swim:
			var gh: float = world.ground_height(pos.x, pos.z)
			if absf(pos.y - gh) < 2.0 and _jump_t < 0.0:
				pos.y = lerpf(pos.y, gh, 0.5)
		position = pos
		rotation.y = lerp_angle(rotation.y, rot, clampf(delta * 14.0, 0.0, 1.0))
	if _jump_t >= 0.0 and model:
		_jump_t += delta
		var k2 := _jump_t / 0.7
		model.position.y = (0.95 if mount_model else 0.0) + sin(clampf(k2, 0.0, 1.0) * PI) * 1.1
		if k2 >= 1.0:
			_jump_t = -1.0
			model.position.y = 0.95 if mount_model else 0.0
		if "airborne" in model:
			model.airborne = _jump_t >= 0.0
	# Laufanimation aus der tatsächlichen Bewegung
	var dpos := position - _last_pos
	_last_pos = position
	var hspeed := Vector2(dpos.x, dpos.z).length() / maxf(0.001, delta)
	_move_speed = lerpf(_move_speed, hspeed, clampf(delta * 10.0, 0.0, 1.0))
	if hspeed > 40.0:
		_move_speed = 0.0
	var anim_target = mount_model if mount_model else model
	if anim_target and "speed" in anim_target:
		anim_target.speed = _move_speed
		if dpos.length() > 0.0001:
			var local := global_transform.basis.inverse() * dpos
			anim_target.move_dir = Vector2(local.x, -local.z).normalized()
	if mount_model and model and "speed" in model:
		model.speed = 0.0
	if companion_model and is_instance_valid(companion_model):
		_comp_phase += delta
		var behind := global_position + global_transform.basis * Vector3(1.0, 0, 1.4)
		if world:
			behind.y = world.ground_height(behind.x, behind.z)
		var cd := companion_model.global_position.distance_to(behind)
		var nxt := companion_model.global_position.lerp(behind, clampf(delta * (3.0 if cd < 8 else 10.0), 0.0, 1.0))
		var cv := (nxt - companion_model.global_position) / maxf(0.001, delta)
		companion_model.global_position = nxt
		if cv.length() > 0.3:
			companion_model.rotation.y = lerp_angle(companion_model.rotation.y, atan2(-cv.x, -cv.z), clampf(delta * 8.0, 0.0, 1.0))
		if "speed" in companion_model:
			companion_model.speed = Vector2(cv.x, cv.z).length()
	if shadow_blob:
		shadow_blob.visible = not dead
	if mark_node:
		mark_node.position.y = height + 0.75 + sin(t * 3.0) * 0.06 + (0.9 if mount_model else 0.0)


func _exit_tree() -> void:
	if companion_model and is_instance_valid(companion_model):
		companion_model.queue_free()
