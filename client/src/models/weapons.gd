class_name WeaponModels
extends RefCounted
## Waffen, Schilde und Gegenstände in der Hand. Griffmitte liegt im Ursprung,
## die Klinge zeigt entlang +Y. Seltene Gegenstände werden größer, prunkvoller und leuchten.

static var _cache: Dictionary = {}


static func make(kind: String, vis: Dictionary = {}) -> Node3D:
	var key := kind + "|" + str(vis)
	var mesh: ArrayMesh = _cache.get(key)
	if mesh == null:
		mesh = _build(kind, vis)
		_cache[key] = mesh
	var root := Node3D.new()
	root.name = "W_" + kind
	if mesh:
		var mi := MeshInstance3D.new()
		mi.mesh = mesh
		root.add_child(mi)
	var glow_hex = vis.get("g")
	if glow_hex != null and str(glow_hex) != "":
		var gc := Color.html(str(glow_hex))
		var sp := FxLib.sparkles(gc, 0.2, 5)
		sp.draw_pass_1.size = Vector2(0.5, 0.5)
		sp.position = Vector3(0, 0.7 if kind not in ["shield", "book", "orb"] else 0.0, 0)
		root.add_child(sp)
	if kind == "torch" or kind == "lantern":
		var f := FxLib.fire(0.25) if kind == "torch" else Node3D.new()
		f.position = Vector3(0, 0.55 if kind == "torch" else 0.0, 0)
		root.add_child(f)
		if kind == "lantern":
			var l := FxLib.light(Color.html("#ffc070"), 1.2, 6.0)
			l.position.y = -0.25
			root.add_child(l)
	return root


static func _metal(vis: Dictionary, default := "#c8ccd4") -> Material:
	var c := Color.html(str(vis.get("m", default)))
	return Mat.stylized(c, Mat.P.METAL, {"c2": c.darkened(0.5), "wear": 0.7, "rim": 0.25})


static func _accent(vis: Dictionary, default := "#c9a040") -> Material:
	var c := Color.html(str(vis.get("a", default)))
	if c.v > 0.6 and c.s > 0.3 and c.h > 0.08 and c.h < 0.17:
		return Mat.stylized(c, Mat.P.GOLD, {"c2": c.darkened(0.5)})
	return Mat.stylized(c, Mat.P.METAL, {"c2": c.darkened(0.5)})


static func _grip(vis: Dictionary) -> Material:
	return Mat.stylized(Color.html(str(vis.get("w", "#5a3a22"))), Mat.P.LEATHER, {"c2": Color.html("#2a1a10")})


static func _glow_mat(vis: Dictionary) -> Material:
	var g = vis.get("g")
	if g == null or str(g) == "":
		return null
	return Mat.emissive(Color.html(str(g)), 3.0)


static func _build(kind: String, vis: Dictionary) -> ArrayMesh:
	var mb := MeshBuilder.new()
	var q := int(vis.get("q", 1))
	var s = 1.0 + max(0, q - 2) * 0.08
	var metal := _metal(vis)
	var accent := _accent(vis)
	var grip := _grip(vis)
	var glow := _glow_mat(vis)
	var wood := Mat.stylized(Color.html(str(vis.get("w", "#7a5232"))), Mat.P.WOOD, {"c2": Color.html("#3a2414")})
	match kind:
		"sword", "sword2h", "katana":
			var two := kind == "sword2h"
			var kat := kind == "katana"
			var bl = (0.95 if not two else 1.35) * s
			var bw = (0.075 if not two else 0.11) * s
			if kat:
				bl = 1.0 * s
				bw = 0.05
			mb.cylinder(grip, MeshBuilder.at(Vector3(0, -0.16 if not two else -0.3, 0)), 0.03, 0.03, 0.3 if not two else 0.48, 8)
			mb.ellipsoid(accent, MeshBuilder.at(Vector3(0, -0.2 if not two else -0.34, 0)), Vector3(0.05, 0.05, 0.05) * s, 8, 6)
			if kat:
				mb.cylinder(accent, MeshBuilder.at(Vector3(0, 0.12, 0)), 0.07, 0.07, 0.03, 12)
				var outline := PackedVector2Array([Vector2(-bw * 0.5, 0.15), Vector2(bw * 0.5, 0.15), Vector2(bw * 0.6, bl * 0.7), Vector2(bw * 0.2, bl + 0.12), Vector2(-bw * 0.3, bl * 0.85)])
				mb.extrude(metal, MeshBuilder.at_euler(Vector3.ZERO, Vector3(0, PI * 0.5, 0)), outline, 0.018)
			else:
				var guard_w = (0.32 if not two else 0.46) * s
				mb.box(accent, MeshBuilder.at(Vector3(0, 0.03, 0)), Vector3(guard_w, 0.06, 0.07))
				if q >= 3:
					for sx in [-1.0, 1.0]:
						mb.ellipsoid(accent, MeshBuilder.at(Vector3(sx * guard_w * 0.5, 0.06, 0)), Vector3(0.04, 0.06, 0.04), 6, 4)
				var outline := PackedVector2Array([Vector2(-bw, 0.06), Vector2(bw, 0.06), Vector2(bw * 0.92, bl * 0.82), Vector2(0, bl), Vector2(-bw * 0.92, bl * 0.82)])
				if q >= 4:
					outline = PackedVector2Array([Vector2(-bw, 0.06), Vector2(bw, 0.06), Vector2(bw * 1.35, bl * 0.3), Vector2(bw * 0.9, bl * 0.55), Vector2(bw * 1.1, bl * 0.8), Vector2(0, bl), Vector2(-bw * 1.1, bl * 0.8), Vector2(-bw * 0.9, bl * 0.55), Vector2(-bw * 1.35, bl * 0.3)])
				mb.extrude(metal, MeshBuilder.at_euler(Vector3.ZERO, Vector3(0, PI * 0.5, 0)), outline, 0.035 * s)
				if glow:
					mb.box(glow, MeshBuilder.at(Vector3(0, bl * 0.45, 0)), Vector3(0.012, bl * 0.7, bw * 0.4))
		"dagger":
			var bl = 0.42 * s
			mb.cylinder(grip, MeshBuilder.at(Vector3(0, -0.12, 0)), 0.025, 0.025, 0.14, 8)
			mb.box(accent, MeshBuilder.at(Vector3(0, 0.02, 0)), Vector3(0.18, 0.04, 0.05))
			var outline := PackedVector2Array([Vector2(-0.045, 0.04), Vector2(0.045, 0.04), Vector2(0.02, bl * 0.8), Vector2(0, bl), Vector2(-0.035, bl * 0.6)])
			mb.extrude(metal, MeshBuilder.at_euler(Vector3.ZERO, Vector3(0, PI * 0.5, 0)), outline, 0.02)
			if glow:
				mb.box(glow, MeshBuilder.at(Vector3(0, bl * 0.4, 0)), Vector3(0.01, bl * 0.5, 0.02))
		"axe", "axe2h":
			var two := kind == "axe2h"
			var hl = (0.75 if not two else 1.3) * s
			mb.cylinder(wood, MeshBuilder.at(Vector3(0, -0.25, 0)), 0.035, 0.03, hl, 8)
			mb.cylinder(grip, MeshBuilder.at(Vector3(0, -0.22, 0)), 0.04, 0.04, 0.25, 8)
			var top = hl - 0.35
			var hw = (0.28 if not two else 0.42) * s
			var outline := PackedVector2Array([Vector2(0.02, top - 0.08), Vector2(hw * 0.6, top - 0.18), Vector2(hw, top - 0.12), Vector2(hw * 1.05, top + 0.1), Vector2(hw, top + 0.28), Vector2(hw * 0.6, top + 0.22), Vector2(0.02, top + 0.12)])
			mb.extrude(metal, MeshBuilder.at(Vector3.ZERO), outline, 0.04 * s)
			if two:
				var mirror := PackedVector2Array()
				for i in range(outline.size() - 1, -1, -1):
					mirror.append(Vector2(-outline[i].x, outline[i].y))
				mb.extrude(metal, MeshBuilder.at(Vector3.ZERO), mirror, 0.04 * s)
			mb.box(accent, MeshBuilder.at(Vector3(0, top + 0.02, 0)), Vector3(0.09, 0.22, 0.09))
		"mace", "hammer", "hammer2h":
			var two := kind == "hammer2h"
			var hl = (0.7 if not two else 1.2) * s
			mb.cylinder(wood if kind != "mace" else grip, MeshBuilder.at(Vector3(0, -0.2, 0)), 0.03, 0.03, hl, 8)
			var top = hl - 0.25
			if kind == "mace":
				mb.ellipsoid(metal, MeshBuilder.at(Vector3(0, top, 0)), Vector3(0.12, 0.14, 0.12) * s, 10, 7)
				for i in 6:
					var a := TAU * i / 6.0
					mb.cylinder(accent, MeshBuilder.at_euler(Vector3(cos(a) * 0.1, top, sin(a) * 0.1) * s, Vector3(0, -a, -PI * 0.5)), 0.035, 0.0, 0.1 * s, 5)
			else:
				var hs = (0.13 if not two else 0.2) * s
				mb.box(metal, MeshBuilder.at(Vector3(0, top, 0)), Vector3(hs * 2.6, hs * 1.4, hs * 1.4))
				mb.box(accent, MeshBuilder.at(Vector3(0, top, 0)), Vector3(hs * 0.6, hs * 1.6, hs * 1.6))
		"staff":
			var hl = 1.7 * s
			mb.cylinder(wood, MeshBuilder.at(Vector3(0, -0.6, 0)), 0.035, 0.03, hl, 8)
			for k in 3:
				mb.torus(accent, MeshBuilder.at(Vector3(0, -0.4 + k * 0.5, 0)), 0.04, 0.012, 10, 4)
			var top = hl - 0.6
			for i in 3:
				var a := TAU * i / 3.0
				mb.beam(accent, Vector3(0, top - 0.05, 0), Vector3(cos(a) * 0.1, top + 0.18, sin(a) * 0.1), Vector2(0.02, 0.02))
			var gem_c := Color.html(str(vis.get("g", vis.get("a", "#7ad0ff"))))
			mb.ellipsoid(Mat.stylized(gem_c, Mat.P.ICE, {"emis": gem_c * 0.8, "rim": 0.5}), MeshBuilder.at(Vector3(0, top + 0.16, 0)), Vector3(0.07, 0.1, 0.07) * s, 8, 6)
		"wand":
			mb.cylinder(wood, MeshBuilder.at(Vector3(0, -0.1, 0)), 0.02, 0.012, 0.4, 6)
			var gem_c := Color.html(str(vis.get("g", "#c080ff")))
			mb.ellipsoid(Mat.emissive(gem_c, 2.0), MeshBuilder.at(Vector3(0, 0.32, 0)), Vector3(0.03, 0.04, 0.03), 6, 4)
		"bow":
			var h = 1.25 * s
			for k in 8:
				var t0 := float(k) / 8.0
				var t1 := float(k + 1) / 8.0
				var a0 := (t0 - 0.5) * 2.0
				var a1 := (t1 - 0.5) * 2.0
				var p0 := Vector3(0, a0 * h * 0.5, -(1.0 - a0 * a0) * 0.22 + 0.22)
				var p1 := Vector3(0, a1 * h * 0.5, -(1.0 - a1 * a1) * 0.22 + 0.22)
				mb.beam(wood, p0, p1, Vector2(0.04, 0.03) * (1.0 + (1.0 - abs(a0)) * 0.5), Vector3.BACK)
			mb.beam(Mat.stylized(Color.html("#e8e0c8")), Vector3(0, -h * 0.5, 0.22), Vector3(0, h * 0.5, 0.22), Vector2(0.006, 0.006), Vector3.BACK)
			mb.cylinder(grip, MeshBuilder.at(Vector3(0, -0.08, 0)), 0.035, 0.035, 0.16, 8)
			if q >= 3:
				for sy in [-1.0, 1.0]:
					mb.ellipsoid(accent, MeshBuilder.at(Vector3(0, sy * h * 0.48, 0.2)), Vector3(0.04, 0.06, 0.04), 6, 4)
		"shield", "shield_round", "shield_tower":
			var tower := kind == "shield_tower"
			var round := kind == "shield_round"
			var face := Mat.stylized(Color.html(str(vis.get("c", "#2d4f9a"))), Mat.P.WOOD if q < 3 else Mat.P.METAL, {"c2": Color.html(str(vis.get("c", "#2d4f9a"))).darkened(0.5)})
			if round:
				mb.cylinder(face, MeshBuilder.at_euler(Vector3(0, 0, 0.03), Vector3(PI * 0.5, 0, 0)), 0.4 * s, 0.42 * s, 0.06, 16)
				mb.torus(metal, MeshBuilder.at_euler(Vector3(0, 0, -0.01), Vector3(PI * 0.5, 0, 0)), 0.42 * s, 0.03, 18, 5)
				mb.ellipsoid(metal, MeshBuilder.at(Vector3(0, 0, -0.04)), Vector3(0.1, 0.1, 0.08), 8, 6, Color.WHITE, 0, 1, 0, 0.0, 1.0)
			else:
				var hh = (0.55 if not tower else 0.75) * s
				var ww = (0.38 if not tower else 0.42) * s
				var outline := PackedVector2Array([Vector2(-ww, hh * 0.7), Vector2(-ww * 0.4, hh * 0.85), Vector2(0, hh * 0.78), Vector2(ww * 0.4, hh * 0.85), Vector2(ww, hh * 0.7), Vector2(ww * 0.95, -hh * 0.1), Vector2(ww * 0.6, -hh * 0.6), Vector2(0, -hh), Vector2(-ww * 0.6, -hh * 0.6), Vector2(-ww * 0.95, -hh * 0.1)])
				if tower:
					outline = PackedVector2Array([Vector2(-ww, hh), Vector2(ww, hh), Vector2(ww, -hh * 0.7), Vector2(0, -hh), Vector2(-ww, -hh * 0.7)])
				mb.extrude(face, MeshBuilder.at(Vector3(0, 0, 0)), outline, 0.06)
				var rim := PackedVector2Array()
				for v in outline:
					rim.append(v * 1.06)
				mb.extrude(metal, MeshBuilder.at(Vector3(0, 0, 0.012)), rim, 0.045)
				mb.box(accent, MeshBuilder.at(Vector3(0, hh * 0.1, -0.04)), Vector3(0.08, hh * 1.2, 0.03))
				mb.box(accent, MeshBuilder.at(Vector3(0, hh * 0.35, -0.04)), Vector3(ww * 1.4, 0.08, 0.03))
				if q >= 3:
					mb.ellipsoid(accent, MeshBuilder.at(Vector3(0, hh * 0.35, -0.06)), Vector3(0.09, 0.09, 0.05), 8, 6)
				if glow:
					mb.ellipsoid(glow, MeshBuilder.at(Vector3(0, hh * 0.35, -0.08)), Vector3(0.05, 0.05, 0.03), 6, 4)
		"book":
			var cover := Mat.stylized(Color.html(str(vis.get("c", "#5a2a6a"))), Mat.P.LEATHER)
			mb.box(cover, MeshBuilder.at(Vector3(0, 0, 0)), Vector3(0.24, 0.32, 0.07))
			mb.box(Mat.stylized(Color.html("#f0e6c8")), MeshBuilder.at(Vector3(0.012, 0, 0)), Vector3(0.22, 0.3, 0.055))
			mb.box(accent, MeshBuilder.at(Vector3(0, 0, -0.04)), Vector3(0.1, 0.1, 0.01))
		"orb", "skull":
			if kind == "skull":
				var bone := Mat.stylized(Color.html("#e6dcc0"), Mat.P.BONE)
				mb.ellipsoid(bone, MeshBuilder.at(Vector3.ZERO), Vector3(0.11, 0.12, 0.13), 10, 8)
				mb.box(Mat.emissive(Color.html(str(vis.get("g", "#60ff90"))), 3.0), MeshBuilder.at(Vector3(-0.04, 0.01, -0.12)), Vector3(0.035, 0.03, 0.01))
				mb.box(Mat.emissive(Color.html(str(vis.get("g", "#60ff90"))), 3.0), MeshBuilder.at(Vector3(0.04, 0.01, -0.12)), Vector3(0.035, 0.03, 0.01))
			else:
				var gc := Color.html(str(vis.get("g", "#80c0ff")))
				mb.ellipsoid(Mat.stylized(gc, Mat.P.ICE, {"emis": gc * 0.9}), MeshBuilder.at(Vector3.ZERO), Vector3(0.1, 0.1, 0.1), 10, 8)
				mb.torus(accent, MeshBuilder.at(Vector3(0, -0.06, 0)), 0.08, 0.015, 10, 4)
		"spear", "pitchfork", "rod":
			var hl := 2.1 if kind == "spear" else (1.6 if kind == "pitchfork" else 1.9)
			mb.cylinder(wood, MeshBuilder.at(Vector3(0, -0.8, 0)), 0.03, 0.025, hl, 7)
			var top := hl - 0.8
			if kind == "spear":
				var outline := PackedVector2Array([Vector2(-0.05, top), Vector2(0.05, top), Vector2(0, top + 0.32)])
				mb.extrude(metal, MeshBuilder.at_euler(Vector3.ZERO, Vector3(0, PI * 0.5, 0)), outline, 0.025)
				mb.cylinder(Mat.stylized(Color.html("#8f1d2c"), Mat.P.CLOTH), MeshBuilder.at(Vector3(0, top - 0.15, 0)), 0.04, 0.05, 0.15, 6)
			elif kind == "pitchfork":
				mb.box(metal, MeshBuilder.at(Vector3(0, top, 0)), Vector3(0.3, 0.03, 0.03))
				for i in 3:
					mb.cylinder(metal, MeshBuilder.at(Vector3(-0.14 + i * 0.14, top, 0)), 0.012, 0.005, 0.35, 5)
			else:
				mb.beam(Mat.stylized(Color.html("#e8e0d0")), Vector3(0, top, 0), Vector3(0, top - 0.8, -0.4), Vector2(0.004, 0.004))
		"lute":
			var body := Mat.stylized(Color.html("#b07a3a"), Mat.P.WOOD)
			mb.ellipsoid(body, MeshBuilder.at(Vector3(0, -0.1, 0)), Vector3(0.18, 0.24, 0.08), 10, 7)
			mb.box(wood, MeshBuilder.at(Vector3(0, 0.25, 0)), Vector3(0.05, 0.45, 0.03))
			mb.disc(Mat.stylized(Color.html("#1a1008")), MeshBuilder.at_euler(Vector3(0, -0.05, -0.081), Vector3(PI * 0.5, 0, 0)), 0.05, 10)
		"lantern":
			var iron := Mat.stylized(Color.html("#3a3a40"), Mat.P.METAL)
			mb.box(iron, MeshBuilder.at(Vector3(0, -0.12, 0)), Vector3(0.18, 0.02, 0.18))
			mb.box(Mat.emissive(Color.html("#ffc060"), 3.0), MeshBuilder.at(Vector3(0, -0.25, 0)), Vector3(0.13, 0.2, 0.13))
			mb.box(iron, MeshBuilder.at(Vector3(0, -0.37, 0)), Vector3(0.18, 0.03, 0.18))
			mb.beam(iron, Vector3(0, 0, 0), Vector3(0, -0.12, 0), Vector2(0.01, 0.01))
		"bell":
			mb.cylinder(_accent({}, "#d0a840"), MeshBuilder.at(Vector3(0, 0.0, 0)), 0.1, 0.05, 0.14, 10)
			mb.cylinder(grip, MeshBuilder.at(Vector3(0, -0.15, 0)), 0.02, 0.02, 0.15, 6)
		"torch":
			mb.cylinder(wood, MeshBuilder.at(Vector3(0, -0.2, 0)), 0.03, 0.04, 0.7, 7)
			mb.cylinder(Mat.stylized(Color.html("#3a2a1a"), Mat.P.CLOTH), MeshBuilder.at(Vector3(0, 0.42, 0)), 0.05, 0.05, 0.12, 7)
		"book_held":
			return _build("book", vis)
		"pick":
			mb.cylinder(wood, MeshBuilder.at(Vector3(0, -0.2, 0)), 0.03, 0.03, 0.8, 7)
			mb.beam(metal, Vector3(-0.25, 0.55, 0), Vector3(0.25, 0.55, 0), Vector2(0.04, 0.05), Vector3.BACK)
		"herbbag":
			mb.ellipsoid(Mat.stylized(Color.html("#8a6a40"), Mat.P.LEATHER), MeshBuilder.at(Vector3(0, -0.15, 0)), Vector3(0.12, 0.14, 0.1), 8, 6)
		_:
			return null
	return mb.commit()


## Leitet aus einem Gegenstand (Server-Inhalt) den Modelltyp ab.
static func kind_for_item(item: Dictionary) -> String:
	var sub: String = str(item.get("sub", ""))
	match sub:
		"schwert": return "sword"
		"zweihandschwert": return "sword2h"
		"axt": return "axe"
		"zweihandaxt": return "axe2h"
		"streitkolben": return "mace"
		"kriegshammer": return "hammer2h"
		"dolch": return "dagger"
		"stab": return "staff"
		"zauberstab": return "wand"
		"katana": return "katana"
		"bogen": return "bow"
		"schild": return "shield_round" if str(item.get("id", "")).contains("holz") else "shield"
		"buch": return "book"
		"kugel", "fokus": return "orb"
		"schaedel": return "skull"
	return ""
