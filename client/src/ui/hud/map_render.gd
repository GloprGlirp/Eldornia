class_name MapRender
extends RefCounted
## Erzeugt eine gemalte Kartentextur einer Zone (Gelände, Wasser, Wege, Gebäude, Wälder).

static var cache: Dictionary = {}


static func texture(zone: Dictionary, hf: Heightfield) -> Dictionary:
	var zid := str(zone.get("id", ""))
	if cache.has(zid):
		return cache[zid]
	var res: Dictionary
	if hf:
		res = _outdoor(zone, hf)
	else:
		res = _dungeon(zone)
	cache[zid] = res
	return res


static func _outdoor(zone: Dictionary, hf: Heightfield) -> Dictionary:
	var n := 320
	var size := hf.size
	var half := size * 0.5
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var theme := Themes.get_theme(str(zone.get("theme", "gruen")))
	var terr: Dictionary = theme.get("terrain", {})
	var grass := Color.html(str(terr.get("grass_a", "#5f9a2c")))
	var grass2 := Color.html(str(terr.get("grass_b", "#3b7322")))
	var rock := Color.html(str(terr.get("rock", "#8f877a")))
	var snow := Color.html(str(terr.get("snow", "#eef4ff")))
	var snow_h := float(terr.get("snow_height", 9999.0))
	var noise := FastNoiseLite.new()
	noise.frequency = 0.05
	var water: Array = zone.get("water", [])
	var wcols: Array = theme.get("water", ["#3aa6b0", "#0e3f5e"])
	var void_level := float(zone.get("void", -1000.0))
	for j in n:
		for i in n:
			var x := -half + (i + 0.5) / n * size
			var z := -half + (j + 0.5) / n * size
			var h := hf.height(x, z)
			var nn := hf.normal(x, z)
			var c := grass.lerp(grass2, clampf(0.5 + noise.get_noise_2d(x, z) * 0.8, 0.0, 1.0))
			var steep := 1.0 - nn.y
			c = c.lerp(rock, clampf(steep * 4.0, 0.0, 1.0))
			if h > snow_h:
				c = c.lerp(snow, clampf((h - snow_h) / 4.0, 0.0, 1.0))
			# Schummerung
			var shade := clampf(0.75 + nn.x * 1.6 - nn.z * 1.2, 0.45, 1.25)
			c = Color(c.r * shade, c.g * shade, c.b * shade)
			c = c.lightened(clampf(h / 60.0, -0.2, 0.25))
			if h <= void_level + 1.0:
				c = Color(0.55, 0.7, 0.9, 0.0)
			for w in water:
				var dx := x - float(w["x"])
				var dz := z - float(w["z"])
				if dx * dx + dz * dz < float(w["r"]) * float(w["r"]) and h < float(w.get("level", -0.8)):
					c = Color.html(wcols[0]).lerp(Color.html(wcols[1]), clampf((float(w.get("level", -0.8)) - h) / 3.0, 0.0, 1.0))
					if w.get("lava", false):
						c = Color("#ff6a1a").lerp(Color("#8a1a0a"), 0.4)
			img.set_pixel(i, j, c)
	var k := n / size
	# Wege
	for road in zone.get("roads", []):
		var pts: Array = road["pts"]
		var rw := maxf(1.5, float(road["w"]) * k * 0.6)
		var rc := Color.html(str(terr.get("dirt", "#94704a"))).lightened(0.05)
		for s in range(pts.size() - 1):
			var a := Vector2(float(pts[s][0]), float(pts[s][1]))
			var b := Vector2(float(pts[s + 1][0]), float(pts[s + 1][1]))
			var steps := int(a.distance_to(b) * k * 1.5) + 1
			for t in steps + 1:
				var p := a.lerp(b, float(t) / steps)
				_dot(img, (p.x + half) * k, (p.y + half) * k, rw, rc)
	# Gebäude & Bäume
	for p in zone.get("props", []):
		var t := str(p.get("t", ""))
		if not p.has("x"):
			if p.has("x1") and t in ["wall", "palisade", "ice_wall"]:
				var a2 := Vector2(float(p["x1"]), float(p["z1"]))
				var b2 := Vector2(float(p["x2"]), float(p["z2"]))
				var st := int(a2.distance_to(b2) * k) + 1
				for q in st + 1:
					var pp := a2.lerp(b2, float(q) / st)
					_dot(img, (pp.x + half) * k, (pp.y + half) * k, 1.2, Color("#5a5048"))
			continue
		var px := (float(p["x"]) + half) * k
		var pz := (float(p["z"]) + half) * k
		if t in ["tree", "pine", "birch", "ashtree", "skytree"]:
			_dot(img, px, pz, 1.4 * float(p.get("s", 1.0)), Color(0.1, 0.25, 0.08, 0.55))
		elif t in ["house", "inn", "smithy", "chapel", "keep", "barn", "kitchen", "shed", "hut", "mausoleum", "tavern", "hall",
				"dwarf_hall", "dwarf_house", "elf_house", "temple", "sky_temple", "ash_fort"]:
			var w := float(p.get("w", 6)) * k * 0.5
			var d := float(p.get("d", 6)) * k * 0.5
			for yy in range(int(pz - d), int(pz + d) + 1):
				for xx in range(int(px - w), int(px + w) + 1):
					if xx >= 0 and yy >= 0 and xx < n and yy < n:
						img.set_pixel(xx, yy, Color("#8a5a3a") if t not in ["keep", "dwarf_hall", "temple", "sky_temple"] else Color("#9a9088"))
		elif t == "tower":
			_dot(img, px, pz, float(p.get("rad", 3)) * k, Color("#9a9088"))
		elif t == "field":
			var w2 := float(p.get("w", 10)) * k * 0.5
			var d2 := float(p.get("d", 10)) * k * 0.5
			for yy in range(int(pz - d2), int(pz + d2) + 1):
				for xx in range(int(px - w2), int(px + w2) + 1):
					if xx >= 0 and yy >= 0 and xx < n and yy < n and (xx + yy) % 3 != 0:
						img.set_pixel(xx, yy, Color("#c8b058") if str(p.get("crop", "")) == "wheat" else Color("#6a8a3a"))
	return {"tex": ImageTexture.create_from_image(img), "size": size, "origin": Vector2(-half, -half)}


static func _dungeon(zone: Dictionary) -> Dictionary:
	var rects: Array = zone.get("rects", [])
	var mn := Vector2(1e9, 1e9)
	var mx := Vector2(-1e9, -1e9)
	for r in rects:
		mn.x = minf(mn.x, float(r[0]))
		mn.y = minf(mn.y, float(r[1]))
		mx.x = maxf(mx.x, float(r[2]))
		mx.y = maxf(mx.y, float(r[3]))
	var pad := 10.0
	mn -= Vector2(pad, pad)
	mx += Vector2(pad, pad)
	var size := maxf(mx.x - mn.x, mx.y - mn.y)
	var n := 256
	var k := n / size
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	img.fill(Color(0.05, 0.04, 0.035, 1.0))
	for r in rects:
		var x0 := int((float(r[0]) - mn.x) * k)
		var y0 := int((float(r[1]) - mn.y) * k)
		var x1 := int((float(r[2]) - mn.x) * k)
		var y1 := int((float(r[3]) - mn.y) * k)
		for y in range(maxi(0, y0), mini(n, y1)):
			for x in range(maxi(0, x0), mini(n, x1)):
				var edge := x - x0 < 2 or x1 - x < 3 or y - y0 < 2 or y1 - y < 3
				img.set_pixel(x, y, Color("#8a7a62") if edge else Color("#5a5040"))
	return {"tex": ImageTexture.create_from_image(img), "size": size, "origin": mn}


static func _dot(img: Image, cx: float, cy: float, r: float, c: Color) -> void:
	var n := img.get_width()
	for yy in range(int(cy - r), int(cy + r) + 1):
		for xx in range(int(cx - r), int(cx + r) + 1):
			if xx < 0 or yy < 0 or xx >= n or yy >= n:
				continue
			if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
				if c.a >= 0.99:
					img.set_pixel(xx, yy, c)
				else:
					img.set_pixel(xx, yy, img.get_pixel(xx, yy).lerp(Color(c.r, c.g, c.b), c.a))
