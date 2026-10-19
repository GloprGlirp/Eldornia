class_name WorldView
extends Node3D
## Die Spielwelt auf dem Client: Zone, Einheiten, eigener Charakter (Steuerung wie in WoW),
## Kamera, Zielauswahl, Bodenziele und Effekte.

signal leave_requested
signal target_changed(id: int)
signal zone_built

const RUN := 7.0
const BACK := 4.5
const SPRINT := 1.35
const GRAVITY := 24.0
const JUMP_V := 8.5
const SEND_RATE := 0.1

var hud
var zone: Dictionary = {}
var zone_root: Node3D
var builder: ZoneBuilder
var hf: Heightfield
var grid := PackedByteArray()
var grid_n := 0
var grid_half := 0.0
var water: Array = []
var entities: Dictionary = {}
var me: EntityView
var fx: Fx
var cam_rig: CameraRig
var target := 0
var focus_target := 0
var selection: Decal
var ground_cursor: Decal
var ground_ability := ""
var ground_radius := 5.0
var welcome: Dictionary = {}

# eigene Bewegung
var vel_y := 0.0
var on_ground := true
var autorun := false
var _send_t := 0.0
var _last_sent := Vector4.ZERO
var _moving_sent := false
var _mouse_l := false
var _mouse_r := false
var _drag_dist := 0.0
var _press_pos := Vector2.ZERO
var _yaw := 0.0
var _zone_ready := false
var _pending_u: Array = []
var _tab_list: Array = []
var _step_t := 0.0
var _last_mount_speed := 1.0
var rooted := false
var stunned := false


func _ready() -> void:
	Game.msg.connect(_on_msg)
	fx = Fx.new(self)
	add_child(fx)
	cam_rig = CameraRig.new(self)
	add_child(cam_rig)
	selection = Fx.decal("ring_sel", 1.0, Color(1, 0.2, 0.1, 0.9), 0.0, 6.0)
	selection.visible = false
	add_child(selection)
	ground_cursor = Fx.decal("cursor", 5.0, Color(0.5, 0.8, 1.0, 0.9))
	ground_cursor.visible = false
	add_child(ground_cursor)


# ============================================================================== Zone
func start(m: Dictionary, done: Callable) -> void:
	welcome = m
	_load_zone(str(m["zone"]), m["p"], done)


func change_zone(m: Dictionary, done: Callable) -> void:
	_load_zone(str(m["zone"]), m["p"], done)


func _load_zone(zid: String, p: Array, done: Callable) -> void:
	_zone_ready = false
	for id in entities.keys():
		_despawn(int(id))
	entities.clear()
	target = 0
	selection.visible = false
	if me:
		me.queue_free()
		me = null
	Net.load_zone(zid, func(data):
		if data == null:
			Net.close_world("Zonendaten konnten nicht geladen werden.")
			return
		_build_zone(data)
		_spawn_me(p)
		_zone_ready = true
		Game.send({"t": "ready"})
		for u in _pending_u:
			_on_update(u)
		_pending_u.clear()
		zone_built.emit()
		Sfx.play_music(str(data.get("music", data.get("theme", "gruen"))) if data.get("type") != "dungeon" else "dungeon")
		done.call()
	)


func _build_zone(data: Dictionary) -> void:
	if zone_root:
		zone_root.queue_free()
	zone = data
	zone_root = Node3D.new()
	zone_root.name = "Zone"
	add_child(zone_root)
	builder = ZoneBuilder.new()
	var t0 := Time.get_ticks_msec()
	builder.build(zone_root, data)
	print("Zone %s gebaut in %d ms" % [str(data.get("id", "")), Time.get_ticks_msec() - t0])
	hf = builder.hf
	water = data.get("water", [])
	grid_n = int(data.get("grid_n", 0))
	var raw := Marshalls.base64_to_raw(str(data.get("grid", "")))
	grid = raw.decompress_dynamic(grid_n * grid_n + 16, FileAccess.COMPRESSION_DEFLATE) if raw.size() > 0 else PackedByteArray()
	grid_half = grid_n * float(data.get("grid_cell", 1.0)) * 0.5
	_apply_graphics()
	if hud:
		hud.on_zone(data)


func _apply_graphics() -> void:
	if builder == null:
		return
	if builder.sun:
		builder.sun.shadow_enabled = Settings.shadows
		builder.sun.directional_shadow_max_distance = 90.0 + 60.0 * Settings.quality
	if builder.env:
		builder.env.ssao_enabled = Settings.ssao and Settings.quality >= 1
		builder.env.ssil_enabled = false
		builder.env.glow_enabled = Settings.quality >= 1
	if builder.grass:
		builder.grass.enabled = Settings.grass and Settings.quality >= 1
		builder.grass.visible = builder.grass.enabled
	var vp := get_viewport()
	vp.msaa_3d = [Viewport.MSAA_DISABLED, Viewport.MSAA_2X, Viewport.MSAA_2X, Viewport.MSAA_4X][clampi(Settings.quality, 0, 3)]
	vp.scaling_3d_scale = 0.75 if Settings.quality == 0 else 1.0
	if cam_rig and cam_rig.cam:
		cam_rig.cam.far = 280.0 + 220.0 * Settings.view_distance


func ground_height(x: float, z: float) -> float:
	if hf:
		return hf.height(x, z)
	return 0.0


func water_level(x: float, z: float) -> Variant:
	for w in water:
		var dx := x - float(w["x"])
		var dz := z - float(w["z"])
		if dx * dx + dz * dz < float(w["r"]) * float(w["r"]):
			return float(w.get("level", -0.8))
	return null


func cell(x: float, z: float) -> int:
	if grid_n == 0:
		return 0
	var i := int(x + grid_half)
	var j := int(z + grid_half)
	if i < 0 or j < 0 or i >= grid_n or j >= grid_n:
		return 3
	var k := j * grid_n + i
	if k >= grid.size():
		return 0
	return grid[k]


func walkable(x: float, z: float) -> bool:
	var c := cell(x, z)
	return c == 0 or c == 2


# ============================================================================== Einheiten
func ent(id: int) -> EntityView:
	if id == Game.me_id and me:
		return me
	return entities.get(id)


func _spawn_me(p: Array) -> void:
	var d := {"id": Game.me_id, "k": "player", "name": Game.me_name, "lvl": Game.level, "look": welcome.get("look", {}),
		"p": p, "model": "human", "hp": Game.stats.get("hp", 100), "mhp": 100, "side": "player"}
	me = EntityView.new()
	me.setup(self, d)
	me.is_me = true
	add_child(me)
	_yaw = float(p[3])
	me.rotation.y = _yaw
	cam_rig.reset(_yaw)
	vel_y = 0.0


func _spawn(d: Dictionary) -> void:
	var id := int(d["id"])
	if id == Game.me_id:
		return
	if entities.has(id):
		_despawn(id)
	var e := EntityView.new()
	e.setup(self, d)
	add_child(e)
	entities[id] = e


func _despawn(id: int) -> void:
	var e: EntityView = entities.get(id)
	if e:
		entities.erase(id)
		e.queue_free()
	if id == target:
		set_target(0)


# ============================================================================== Netzwerk
func _on_msg(t: String, m: Dictionary) -> void:
	match t:
		"u":
			if not _zone_ready:
				_pending_u.append(m)
			else:
				_on_update(m)
		"force":
			if me:
				var p: Array = m["p"]
				me.position = Vector3(float(p[0]), float(p[1]), float(p[2]))
				if str(m.get("k", "")) in ["tele", "block", "speed", "root", "charge", "leap", "blink", "knock"]:
					if str(m.get("k")) in ["charge", "leap", "blink", "knock", "tele"]:
						_yaw = float(p[3])
						me.rotation.y = _yaw
				vel_y = 0.0
				_last_sent = Vector4(me.position.x, me.position.y, me.position.z, _yaw)
		"died":
			if me:
				me.dead = true
				if me.model and me.model.has_method("set_dead"):
					me.model.set_dead(true)
			Sfx.play("death")
		"revived":
			if me:
				me.dead = false
				if me.model and me.model.has_method("set_dead"):
					me.model.set_dead(false)


func _on_update(m: Dictionary) -> void:
	for d in m.get("sp", []):
		_spawn(d)
	for id in m.get("ds", []):
		_despawn(int(id))
	for d in m.get("e", []):
		var id := int(d["id"])
		if id == Game.me_id and me:
			me.apply(d)
			if d.has("st"):
				var was: bool = me.dead
				me.dead = (int(d["st"]) & 1) != 0
				if me.model and me.model.has_method("set_dead") and was != me.dead:
					me.model.set_dead(me.dead)
			if hud:
				hud.on_me_update(d)
		else:
			var e: EntityView = entities.get(id)
			if e:
				e.apply(d)
	for ev in m.get("ev", []):
		_combat_event(ev)
	for f in m.get("fx", []):
		fx.handle(f)


func _combat_event(ev: Dictionary) -> void:
	var dst := ent(int(ev.get("d", 0)))
	var src := ent(int(ev.get("s", 0)))
	var k := str(ev.get("k", "hit"))
	if hud and dst:
		hud.combat_text(ev, src, dst)
	if k in ["hit", "crit", "block"] and dst:
		if src and src != dst and int(ev.get("pe", 0)) == 0 and ev.get("ab") == null:
			src.play_attack()
		if int(ev.get("pe", 0)) == 0:
			Sfx.play_at("crit" if k == "crit" else ("block" if k == "block" else "hit"), dst.global_position, self, -6.0 if (dst.is_me or (src and src.is_me)) else -14.0)
	elif k in ["miss", "dodge", "parry"] and src and ev.get("ab") == null:
		src.play_attack()
		if dst:
			Sfx.play_at("miss", dst.global_position, self, -12.0)
	elif k == "heal" or k == "healcrit":
		if dst and int(ev.get("a", 0)) > 0 and ev.get("ab") != "Lebensentzug":
			fx.burst(dst.chest_pos(), Color(0.4, 1.0, 0.4), 10, 0.2, 2.0, 0.6)
	elif k == "release" and src:
		src.cast_release()
	elif k == "interrupt" and dst:
		fx.flash(dst.head_pos(), Color(1, 1, 1), 1.0, 0.3)


# ============================================================================== Ziel
func set_target(id: int) -> void:
	target = id
	Game.send({"t": "tg", "id": id if id != 0 else null})
	target_changed.emit(id)
	if id != 0:
		Sfx.play("click", -14.0)


func entity_at_screen(pos: Vector2) -> EntityView:
	var cam := cam_rig.cam
	var best: EntityView = null
	var best_d := 1e9
	var candidates: Array = entities.values()
	if me:
		candidates.append(me)
	for e in candidates:
		if not is_instance_valid(e) or e.kind in ["ground", "trap"]:
			continue
		var top: Vector3 = e.global_position + Vector3.UP * e.height
		var mid: Vector3 = e.global_position + Vector3.UP * e.height * 0.5
		if cam.is_position_behind(mid):
			continue
		var sm := cam.unproject_position(mid)
		var st := cam.unproject_position(top)
		var sb := cam.unproject_position(e.global_position)
		var h := absf(sb.y - st.y)
		var w := maxf(h * 0.35, 14.0) * (1.4 if e.kind == "obj" else 1.0) * clampf(e.radius * 1.5, 0.8, 3.0)
		var r := Rect2(Vector2(sm.x - w, st.y - 6), Vector2(w * 2, h + 12))
		if r.has_point(pos):
			var d := cam.global_position.distance_to(mid)
			if e == me:
				d += 1000.0
			if d < best_d:
				best_d = d
				best = e
	return best


func tab_target(friendly := false) -> void:
	if not me:
		return
	var cam := cam_rig.cam
	var fwd := -cam.global_transform.basis.z
	fwd.y = 0
	fwd = fwd.normalized()
	var cands: Array = []
	for e in entities.values():
		if e.dead:
			continue
		if friendly:
			if not (e.kind == "player" and not e.is_enemy()):
				continue
		elif not e.is_attackable() or e.look.get("critter", false):
			continue
		var d: Vector3 = e.global_position - me.global_position
		var dist := d.length()
		if dist > 45.0:
			continue
		var dir := Vector3(d.x, 0, d.z).normalized()
		var dot := fwd.dot(dir)
		if dot < 0.2 and dist > 6.0:
			continue
		var sp := cam.unproject_position(e.chest_pos())
		if cam.is_position_behind(e.chest_pos()):
			continue
		cands.append([dist * (1.6 - dot), e.id])
	cands.sort_custom(func(a, b): return a[0] < b[0])
	if cands.is_empty():
		return
	var ids: Array = cands.map(func(c): return c[1])
	var i := ids.find(target)
	var nxt: int = ids[(i + 1) % ids.size()] if i >= 0 else ids[0]
	set_target(nxt)


func nearest_enemy_in_front(max_dist := 30.0) -> int:
	if not me:
		return 0
	var fwd := -me.global_transform.basis.z
	var best := 0
	var bd := 1e9
	for e in entities.values():
		if not e.is_attackable() or e.look.get("critter", false):
			continue
		var d: Vector3 = e.global_position - me.global_position
		var dist := d.length()
		if dist > max_dist:
			continue
		var dot := fwd.dot(Vector3(d.x, 0, d.z).normalized())
		if dot < 0.3 and dist > 4:
			continue
		var score := dist * (1.5 - dot)
		if score < bd:
			bd = score
			best = e.id
	return best


func interact(e: EntityView) -> void:
	if e == null or not me:
		return
	if e.kind == "mob" and not e.dead and e.is_attackable():
		set_target(e.id)
		Game.send({"t": "atk", "id": e.id})
		_face_entity(e)
		return
	if e.kind == "player" and e != me:
		set_target(e.id)
		if e.is_attackable():
			Game.send({"t": "atk", "id": e.id})
			return
	var dist := me.global_position.distance_to(e.global_position)
	if dist > 6.5 + e.radius:
		if hud:
			hud.error_text("Ihr seid zu weit entfernt.")
		return
	if e.kind in ["npc", "obj", "player"] or (e.kind == "mob" and e.dead):
		if e.kind == "npc":
			set_target(e.id)
		_face_entity(e)
		Game.send({"t": "interact", "id": e.id})


func _face_entity(e: EntityView) -> void:
	if not me or _mouse_r:
		return
	var d := e.global_position - me.global_position
	if Vector2(d.x, d.z).length() > 0.3:
		_yaw = atan2(-d.x, -d.z)
		me.rotation.y = _yaw
		_send_move(true)


# ============================================================================== Fähigkeiten
func use_bar_entry(entry) -> void:
	if not (entry is Dictionary) or not me:
		return
	if entry.has("ab"):
		use_ability(str(entry["ab"]))
	elif entry.has("item"):
		var iid := str(entry["item"])
		Game.send({"t": "use", "item": iid, "tid": target if target != 0 else null})
	elif entry.has("mount"):
		Game.send({"t": "mount", "m": entry["mount"]})
	elif entry.has("emote"):
		Game.send({"t": "emote", "e": entry["emote"]})


func use_ability(ab_id: String) -> void:
	var ab: Dictionary = Game.abilities.get(ab_id, {})
	if ab.is_empty():
		return
	if me and me.dead:
		return
	var tgt := target
	var tgt_e := ent(tgt)
	if str(ab.get("target")) == "enemy":
		if tgt_e == null or not tgt_e.is_attackable():
			if Settings.target_assist:
				var n := nearest_enemy_in_front(maxf(8.0, float(ab.get("range", 5.0)) + 3.0))
				if n != 0:
					set_target(n)
					tgt = n
					tgt_e = ent(n)
		if tgt_e and tgt_e.is_attackable():
			_face_entity(tgt_e)
	if ab.get("ground", false) or (ab.get("area") is Dictionary and str(ab["area"].get("center", "")) == "target" and (tgt_e == null or not tgt_e.is_attackable())):
		ground_ability = ab_id
		ground_radius = float(ab.get("area", {}).get("radius", 5.0)) if ab.get("area") is Dictionary else 5.0
		ground_cursor.size = Vector3(ground_radius * 2, 8, ground_radius * 2)
		ground_cursor.visible = true
		return
	if Game.gcd_left() > 0.25 and ab.get("gcd", true):
		return
	Game.send({"t": "ab", "ab": ab_id, "tid": tgt if tgt != 0 else null})


func confirm_ground(pos: Vector3) -> void:
	if ground_ability == "":
		return
	Game.send({"t": "ab", "ab": ground_ability, "tid": target if target != 0 else null, "gp": [snappedf(pos.x, 0.01), snappedf(pos.z, 0.01)]})
	cancel_ground()


func cancel_ground() -> void:
	ground_ability = ""
	ground_cursor.visible = false


func mouse_ground(pos: Vector2) -> Variant:
	var cam := cam_rig.cam
	var origin := cam.project_ray_origin(pos)
	var dir := cam.project_ray_normal(pos)
	if hf:
		return hf.raycast(origin, dir, 120.0)
	if absf(dir.y) > 0.001:
		var t := -origin.y / dir.y
		if t > 0:
			return origin + dir * t
	return null


# ============================================================================== Eingabe
func _ui_has_focus() -> bool:
	var f := get_viewport().gui_get_focus_owner()
	return f is LineEdit or f is TextEdit


func _unhandled_input(ev: InputEvent) -> void:
	if not _zone_ready or not me:
		return
	if ev is InputEventMouseButton:
		_mouse_button(ev)
	elif ev is InputEventMouseMotion:
		if _mouse_l or _mouse_r:
			_drag_dist += ev.relative.length()
			if _drag_dist > 4.0:
				if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
					Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
				var sens := 0.0045 * Settings.mouse_sens
				cam_rig.yaw -= ev.relative.x * sens
				cam_rig.pitch = clampf(cam_rig.pitch + ev.relative.y * sens * (-1.0 if Settings.invert_y else 1.0), -1.35, 1.2)
				if _mouse_r and not me.dead:
					_yaw = cam_rig.yaw
		elif ground_ability != "":
			var p = mouse_ground(ev.position)
			if p != null:
				ground_cursor.position = p
				var inrange := me.global_position.distance_to(p) <= float(Game.abilities.get(ground_ability, {}).get("range", 30)) + 1.0
				ground_cursor.modulate = Color(0.5, 0.8, 1.0, 0.9) if inrange else Color(1.0, 0.3, 0.2, 0.9)
	elif ev is InputEventKey and ev.pressed and not ev.echo:
		if _ui_has_focus():
			return
		if Settings.is_action(ev, "springen"):
			_jump()
		elif Settings.is_action(ev, "ziel_naechstes"):
			tab_target(ev.shift_pressed)
		elif Settings.is_action(ev, "ziel_freund"):
			tab_target(true)
		elif Settings.is_action(ev, "ziel_selbst"):
			set_target(Game.me_id)
		elif Settings.is_action(ev, "interagieren"):
			var e := ent(target)
			if e:
				interact(e)
			else:
				_interact_nearest()
		elif Settings.is_action(ev, "laufen_auto"):
			autorun = not autorun
		elif Settings.is_action(ev, "reiten"):
			Game.send({"t": "mount"})
		elif ev.keycode == KEY_ESCAPE:
			if ground_ability != "":
				cancel_ground()
			elif hud and hud.close_top_window():
				pass
			elif target != 0:
				set_target(0)
			elif hud:
				hud.toggle_game_menu()
		elif hud:
			hud.handle_key(ev)


func _interact_nearest() -> void:
	var best: EntityView = null
	var bd := 7.0
	for e in entities.values():
		if e.kind in ["npc", "obj"] or (e.kind == "mob" and e.dead and e.fl.get("l", false)):
			var d := me.global_position.distance_to(e.global_position)
			if d < bd:
				bd = d
				best = e
	if best:
		interact(best)


func _mouse_button(ev: InputEventMouseButton) -> void:
	match ev.button_index:
		MOUSE_BUTTON_WHEEL_UP:
			if ev.pressed:
				cam_rig.zoom(-1.0)
		MOUSE_BUTTON_WHEEL_DOWN:
			if ev.pressed:
				cam_rig.zoom(1.0)
		MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT:
			var left := ev.button_index == MOUSE_BUTTON_LEFT
			if ev.pressed:
				if left:
					_mouse_l = true
				else:
					_mouse_r = true
				_drag_dist = 0.0
				_press_pos = ev.position
			else:
				var was_drag := _drag_dist > 4.0
				if left:
					_mouse_l = false
				else:
					_mouse_r = false
				if not _mouse_l and not _mouse_r and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
					Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
					Input.warp_mouse(_press_pos)
				if not was_drag:
					_click(_press_pos, left)


func _click(pos: Vector2, left: bool) -> void:
	if ground_ability != "":
		if left:
			var p = mouse_ground(pos)
			if p != null:
				confirm_ground(p)
		else:
			cancel_ground()
		return
	var e := entity_at_screen(pos)
	if left:
		if e:
			set_target(e.id)
		else:
			pass
	else:
		if e:
			interact(e)


func _jump() -> void:
	if on_ground and not me.dead and not rooted and not stunned:
		vel_y = JUMP_V
		on_ground = false
		me.jump()
		Game.send({"t": "jump"})
		Sfx.play("jump", -14.0)


# ============================================================================== Bewegung
func _process(delta: float) -> void:
	if not _zone_ready or not me:
		return
	_update_cc_state()
	_move_me(delta)
	cam_rig.update(delta)
	_update_selection()
	if builder and builder.grass:
		builder.grass.focus = me.global_position


func _update_cc_state() -> void:
	rooted = false
	stunned = false
	for a in me.auras:
		if a is Array and a.size() > 8:
			var f := int(a[8])
			if (f & 1) != 0:
				stunned = true
			if (f & 2) != 0:
				rooted = true


func _move_me(delta: float) -> void:
	var input := Vector2.ZERO        # x = seitwärts (rechts +), y = vorwärts
	var turn := 0.0
	var typing := _ui_has_focus()
	if not typing and not me.dead:
		if Settings.key_pressed("vor"):
			input.y += 1.0
		if Settings.key_pressed("zurueck"):
			input.y -= 1.0
			autorun = false
		if Settings.key_pressed("links_seit"):
			input.x -= 1.0
		if Settings.key_pressed("rechts_seit"):
			input.x += 1.0
		var l := Settings.key_pressed("links")
		var r := Settings.key_pressed("rechts")
		if _mouse_r:
			if l:
				input.x -= 1.0
			if r:
				input.x += 1.0
		else:
			if l:
				turn += 1.0
			if r:
				turn -= 1.0
	if _mouse_l and _mouse_r:
		input.y = 1.0
		autorun = false
	if autorun:
		input.y = maxf(input.y, 1.0)
	if stunned or me.dead:
		input = Vector2.ZERO
		turn = 0.0
	if turn != 0.0:
		_yaw += turn * 2.6 * delta
		if not _mouse_l:
			cam_rig.yaw = lerp_angle(cam_rig.yaw, _yaw, 1.0)
	if not stunned and not me.dead:
		me.rotation.y = _yaw
	var mount_speed := 1.0
	var mt = me.look.get("mount")
	if mt is Dictionary:
		var md: Dictionary = Content.defs.get("mounts", {}).get(str(mt.get("id")), {})
		mount_speed = float(md.get("speed", 1.6))
	var speed := RUN * _speed_mult() * mount_speed
	if input.y < 0 and input.x == 0:
		speed = BACK * _speed_mult()
	if Settings.key_pressed("sprinten") and input.y > 0 and not typing:
		speed *= SPRINT
	var dir := Vector3.ZERO
	if input.length() > 0.01 and not rooted:
		var basis := Basis(Vector3.UP, _yaw)
		dir = basis * Vector3(input.x, 0, -input.y).normalized()
	var pos := me.position
	var nx := pos.x + dir.x * speed * delta
	var nz := pos.z + dir.z * speed * delta
	if dir != Vector3.ZERO:
		if walkable(nx, nz):
			pos.x = nx
			pos.z = nz
		elif walkable(nx, pos.z):
			pos.x = nx
		elif walkable(pos.x, nz):
			pos.z = nz
	# Höhe & Schwerkraft
	var gh := ground_height(pos.x, pos.z)
	var wl = water_level(pos.x, pos.z)
	var swimming := false
	if wl != null and gh < float(wl) - 1.2:
		swimming = true
		gh = float(wl) - 1.15
	if swimming:
		pos.y = lerpf(pos.y, gh, clampf(delta * 6.0, 0.0, 1.0))
		vel_y = 0.0
		on_ground = true
	else:
		vel_y -= GRAVITY * delta
		pos.y += vel_y * delta
		if pos.y <= gh:
			pos.y = gh
			if not on_ground and vel_y < -9.0:
				Sfx.play("step", -6.0)
			vel_y = 0.0
			on_ground = true
		elif pos.y > gh + 0.3:
			on_ground = false
		if on_ground and pos.y - gh < 0.6:
			pos.y = gh
	me.swim = swimming
	me.position = pos
	if me.model and "airborne" in me.model:
		me.model.airborne = not on_ground and not swimming
	# Schritte
	if dir != Vector3.ZERO and on_ground and not swimming and mt == null:
		_step_t -= delta * speed
		if _step_t <= 0.0:
			_step_t = 2.4
			Sfx.play("step", -20.0)
	_send_t -= delta
	var moving := dir != Vector3.ZERO or not on_ground
	if _send_t <= 0.0 or moving != _moving_sent:
		_send_move(moving)


func _speed_mult() -> float:
	var m := 1.0
	for a in me.auras:
		if a is Array and a.size() > 8 and (int(a[8]) & 16) != 0:
			m = minf(m, 0.6)
	return m


func _send_move(moving: bool) -> void:
	_send_t = SEND_RATE
	var p := me.position
	var cur := Vector4(p.x, p.y, p.z, _yaw)
	if cur.is_equal_approx(_last_sent) and moving == _moving_sent:
		return
	_last_sent = cur
	_moving_sent = moving
	Game.send({"t": "mv", "p": [snappedf(p.x, 0.01), snappedf(p.y, 0.01), snappedf(p.z, 0.01), snappedf(wrapf(_yaw, -PI, PI), 0.001)],
		"m": moving, "sp": Settings.key_pressed("sprinten"), "j": not on_ground})


func _update_selection() -> void:
	var e := ent(target)
	if e == null or e.kind in ["ground"]:
		selection.visible = false
		if target != 0 and e == null:
			target = 0
			target_changed.emit(0)
		return
	selection.visible = true
	selection.position = e.global_position
	var r := maxf(0.7, e.radius * 1.4)
	selection.size = Vector3(r * 2, 6, r * 2)
	selection.modulate = Color(e.reaction_color(), 0.95)


func _exit_tree() -> void:
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
