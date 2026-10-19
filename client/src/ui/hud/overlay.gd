class_name HudOverlay
extends Control
## Zeichnet Namensplaketten, schwebenden Kampftext und Sprechblasen über den Einheiten.

var world
var fct: Array = []          # {pos, text, color, t, life, size, crit, vel}
var bubbles: Dictionary = {}  # id -> {text, until}
const KIND_TEXT := {"miss": "Verfehlt", "dodge": "Ausgewichen", "parry": "Pariert", "block": "Geblockt", "immune": "Immun",
	"evade": "Entkommen", "absorb": "Absorbiert", "resist": "Widerstanden", "interrupt": "Unterbrochen", "reflect": "Reflektiert"}


func _init(p_world) -> void:
	world = p_world
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


func add_combat(ev: Dictionary, src, dst) -> void:
	if not Settings.show_fct:
		return
	var k := str(ev.get("k", "hit"))
	var a := int(ev.get("a", 0))
	var me_src: bool = src != null and (src.is_me or (src.kind == "pet" and int(src.info.get("owner", 0)) == Game.me_id))
	var me_dst: bool = dst.is_me
	if not me_src and not me_dst:
		return
	var text := ""
	var col := Color(1, 1, 1)
	var size := 22
	var crit := false
	if k in ["hit", "crit", "block"]:
		if a <= 0:
			return
		text = str(a)
		if k == "crit":
			crit = true
			size = 34
			text += "!"
		if me_dst:
			col = Color(1.0, 0.25, 0.2)
			text = "-" + text
		elif str(ev.get("sc", "physical")) != "physical":
			col = Fx.school_color(str(ev.get("sc"))).lightened(0.25)
		else:
			col = Color(1.0, 1.0, 0.9) if not crit else Color(1.0, 0.85, 0.2)
		if int(ev.get("pe", 0)) == 1:
			size -= 4
		if k == "block":
			text += " (Geblockt)"
	elif k in ["heal", "healcrit"]:
		if a <= 0:
			return
		text = "+%d" % a
		col = Color(0.35, 1.0, 0.35)
		crit = k == "healcrit"
		size = 30 if crit else 20
		if not me_dst and not me_src:
			return
	elif KIND_TEXT.has(k):
		text = KIND_TEXT[k]
		col = Color(0.85, 0.85, 1.0) if me_src else Color(1.0, 0.6, 0.6)
		size = 20
	else:
		return
	if ev.get("ab") and me_src and not me_dst and k in ["hit", "crit"] and int(ev.get("pe", 0)) == 0:
		pass
	var p: Vector3 = dst.head_pos()
	fct.append({"pos": p, "text": text, "color": col, "t": 0.0, "life": 1.4 if crit else 1.1, "size": size, "crit": crit,
		"off": Vector2(randf_range(-30, 30), 0), "dst": dst})


func bubble(e, text: String) -> void:
	bubbles[e.id] = {"text": text, "until": Game.now() + clampf(2.0 + text.length() * 0.06, 3.0, 8.0)}


func _process(delta: float) -> void:
	for i in range(fct.size() - 1, -1, -1):
		fct[i]["t"] += delta
		if fct[i]["t"] >= fct[i]["life"]:
			fct.remove_at(i)
	queue_redraw()


func _draw() -> void:
	if world == null or world.me == null or world.cam_rig == null:
		return
	var cam: Camera3D = world.cam_rig.cam
	var f := UiSkin.font_bold
	var me = world.me
	var now := Game.now()
	# Namensplaketten
	if Settings.show_nameplates:
		var list: Array = world.entities.values()
		for e in list:
			if not is_instance_valid(e) or e.kind in ["ground", "trap"]:
				continue
			if e.kind == "obj" and not e.fl.get("u", false):
				continue
			var d: float = me.global_position.distance_to(e.global_position)
			var is_target: bool = e.id == world.target
			var hostile: bool = e.is_enemy()
			if d > (60.0 if hostile or is_target else 35.0):
				continue
			if e.kind in ["npc", "player", "pet"] and not hostile and not Settings.show_friendly_plates and not is_target:
				continue
			var hp_pos: Vector3 = e.head_pos() + Vector3.UP * 0.45
			if cam.is_position_behind(hp_pos):
				continue
			var sp := cam.unproject_position(hp_pos)
			if sp.x < -100 or sp.y < -50 or sp.x > size.x + 100 or sp.y > size.y + 50:
				continue
			var scale := clampf(1.25 - d / 70.0, 0.65, 1.15)
			var col: Color = e.reaction_color()
			var name: String = e.name_text
			var fs := int(15 * scale)
			if e.kind == "mob" and not e.look.get("critter", false):
				var w := 110.0 * scale
				var h := 9.0 * scale
				var bar := Rect2(sp.x - w * 0.5, sp.y, w, h)
				if not e.dead and (hostile or is_target or e.hp < e.mhp):
					draw_rect(bar.grow(1), Color(0, 0, 0, 0.8))
					var frac := float(e.hp) / maxf(1.0, e.mhp)
					var bc := col.darkened(0.15)
					draw_rect(Rect2(bar.position, Vector2(w * frac, h)), bc)
					draw_rect(Rect2(bar.position, Vector2(w * frac, h * 0.45)), bc.lightened(0.2))
					if is_target:
						draw_rect(bar.grow(2), Color(1, 1, 1, 0.9), false, 1.5)
					if e.cast != null:
						var c: Dictionary = e.cast
						var total := maxf(0.05, float(c.get("dur", 1.0)))
						var left := float(c.get("left", 0.0)) - (now - e.cast_start)
						var cf := clampf(1.0 - left / total, 0.0, 1.0)
						if c.get("ch", false):
							cf = 1.0 - cf
						var cb := Rect2(bar.position + Vector2(0, h + 3), Vector2(w, h * 0.8))
						draw_rect(cb.grow(1), Color(0, 0, 0, 0.8))
						var ccol := Color(0.6, 0.6, 0.6) if c.get("ni", false) else Color(1.0, 0.75, 0.15)
						draw_rect(Rect2(cb.position, Vector2(w * cf, cb.size.y)), ccol)
						var ct := str(c.get("name", ""))
						draw_string_outline(f, Vector2(cb.position.x, cb.end.y + 13 * scale), ct, HORIZONTAL_ALIGNMENT_CENTER, w, int(12 * scale), 3, Color.BLACK)
						draw_string(f, Vector2(cb.position.x, cb.end.y + 13 * scale), ct, HORIZONTAL_ALIGNMENT_CENTER, w, int(12 * scale), Color.WHITE)
				var lvl_txt := str(e.level)
				if e.look.get("boss", false):
					lvl_txt = "☠"
				elif e.look.get("elite", false):
					lvl_txt += "+"
				var lc := _level_color(e.level)
				name = name if e.title == "" or not is_target else name
				var ny := sp.y - 4
				draw_string_outline(f, Vector2(sp.x - 150, ny), name, HORIZONTAL_ALIGNMENT_CENTER, 300, fs, 4, Color.BLACK)
				draw_string(f, Vector2(sp.x - 150, ny), name, HORIZONTAL_ALIGNMENT_CENTER, 300, fs, col.lightened(0.25) if not e.dead else Color(0.6, 0.6, 0.6))
				if not e.dead:
					draw_string_outline(f, Vector2(sp.x + w * 0.5 + 4, sp.y + h), lvl_txt, HORIZONTAL_ALIGNMENT_LEFT, -1, int(13 * scale), 3, Color.BLACK)
					draw_string(f, Vector2(sp.x + w * 0.5 + 4, sp.y + h), lvl_txt, HORIZONTAL_ALIGNMENT_LEFT, -1, int(13 * scale), lc)
				if e.fl.get("qm", false):
					draw_string_outline(f, Vector2(sp.x - w * 0.5 - 14, sp.y + h), "!", HORIZONTAL_ALIGNMENT_LEFT, -1, int(16 * scale), 3, Color.BLACK)
					draw_string(f, Vector2(sp.x - w * 0.5 - 14, sp.y + h), "!", HORIZONTAL_ALIGNMENT_LEFT, -1, int(16 * scale), Color(1, 0.85, 0.1))
			else:
				var ny2 := sp.y + 6
				if e.kind == "player" and e.info.get("guild"):
					pass
				draw_string_outline(f, Vector2(sp.x - 150, ny2), name, HORIZONTAL_ALIGNMENT_CENTER, 300, fs, 4, Color.BLACK)
				var nc: Color = col if e.kind != "player" else (Content.class_color(str(e.info.get("cls", ""))) if not hostile else col)
				draw_string(f, Vector2(sp.x - 150, ny2), name, HORIZONTAL_ALIGNMENT_CENTER, 300, fs, nc)
				var sub := ""
				if e.kind == "npc" and e.title != "":
					sub = "<%s>" % e.title
				elif e.kind == "player":
					var g = e.look.get("guild_name")
					if g:
						sub = "<%s>" % g
					if e.title != "":
						sub = e.title + ("  " + sub if sub != "" else "")
				if sub != "":
					draw_string_outline(f, Vector2(sp.x - 150, ny2 + fs), sub, HORIZONTAL_ALIGNMENT_CENTER, 300, int(fs * 0.85), 3, Color.BLACK)
					draw_string(f, Vector2(sp.x - 150, ny2 + fs), sub, HORIZONTAL_ALIGNMENT_CENTER, 300, int(fs * 0.85), Color(0.85, 0.85, 0.85))
				if e.kind == "player" and hostile and not e.dead:
					var w2 := 90.0 * scale
					var bar2 := Rect2(sp.x - w2 * 0.5, ny2 + fs + 4, w2, 7 * scale)
					draw_rect(bar2.grow(1), Color(0, 0, 0, 0.8))
					draw_rect(Rect2(bar2.position, Vector2(w2 * float(e.hp) / maxf(1, e.mhp), bar2.size.y)), Color(0.9, 0.15, 0.1))
	# Sprechblasen
	for id in bubbles.keys():
		var b: Dictionary = bubbles[id]
		if now > b["until"]:
			bubbles.erase(id)
			continue
		var e2 = world.ent(int(id))
		if e2 == null:
			continue
		var bp: Vector3 = e2.head_pos() + Vector3.UP * 1.1
		if cam.is_position_behind(bp):
			continue
		var sp2 := cam.unproject_position(bp)
		var txt: String = b["text"]
		var lines := _wrap(txt, f, 15, 260)
		var bw := 0.0
		for ln in lines:
			bw = maxf(bw, f.get_string_size(ln, HORIZONTAL_ALIGNMENT_LEFT, -1, 15).x)
		var bh := lines.size() * 18 + 10
		var r := Rect2(sp2.x - bw * 0.5 - 10, sp2.y - bh - 10, bw + 20, bh)
		draw_style_box(UiSkin.flat(Color(0.95, 0.93, 0.85, 0.92), Color(0.3, 0.25, 0.2), 2, 8), r)
		var tri := PackedVector2Array([Vector2(sp2.x - 8, r.end.y - 1), Vector2(sp2.x + 8, r.end.y - 1), Vector2(sp2.x, r.end.y + 9)])
		draw_colored_polygon(tri, Color(0.95, 0.93, 0.85, 0.92))
		for i in lines.size():
			draw_string(f, Vector2(r.position.x + 10, r.position.y + 20 + i * 18), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(0.15, 0.1, 0.05))
	# Kampftext
	for t in fct:
		var dst = t["dst"]
		var base: Vector3 = t["pos"]
		if is_instance_valid(dst):
			base = dst.head_pos()
		if cam.is_position_behind(base):
			continue
		var sp3 := cam.unproject_position(base)
		var k: float = t["t"] / t["life"]
		var rise := k * 70.0
		var fsz: int = t["size"]
		if t["crit"] and k < 0.15:
			fsz = int(fsz * (1.0 + (0.15 - k) * 4.0))
		var a := 1.0 if k < 0.65 else 1.0 - (k - 0.65) / 0.35
		var pos := sp3 + t["off"] + Vector2(0, -rise - 20)
		var tw := f.get_string_size(t["text"], HORIZONTAL_ALIGNMENT_LEFT, -1, fsz).x
		draw_string_outline(f, pos - Vector2(tw * 0.5, 0), t["text"], HORIZONTAL_ALIGNMENT_LEFT, -1, fsz, 5, Color(0, 0, 0, a))
		draw_string(f, pos - Vector2(tw * 0.5, 0), t["text"], HORIZONTAL_ALIGNMENT_LEFT, -1, fsz, Color(t["color"], a))


func _wrap(text: String, f: Font, fs: int, width: float) -> Array:
	var words := text.split(" ")
	var lines: Array = []
	var cur := ""
	for w in words:
		var test := w if cur == "" else cur + " " + w
		if f.get_string_size(test, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x > width and cur != "":
			lines.append(cur)
			cur = w
		else:
			cur = test
	if cur != "":
		lines.append(cur)
	return lines.slice(0, 5)


static func _level_color(lvl: int) -> Color:
	var d := lvl - Game.level
	if d >= 5:
		return Color(1.0, 0.1, 0.1)
	if d >= 3:
		return Color(1.0, 0.5, 0.1)
	if d >= -2:
		return Color(1.0, 1.0, 0.0)
	if d >= -6:
		return Color(0.25, 0.75, 0.25)
	return Color(0.6, 0.6, 0.6)
