extends Node3D
## Entwickler-Testszene: baut eine Zone aus einer JSON-Datei, stellt Figuren auf und speichert
## Screenshots aus festen Kamerapositionen.
## Aufruf: godot --path client -- --visual-test --zone=/pfad/zone.json --out=/pfad/ordner [--shots=a,b]

var cam: Camera3D
var builder: ZoneBuilder
var out_dir := "user://shots"
var shots: Array = []
var _shot_i := 0
var _frames := 0
var _models: Array = []


func _ready() -> void:
	var zone_path := ""
	var only := ""
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--zone="):
			zone_path = a.substr(7)
		elif a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--shots="):
			only = a.substr(8)
	DirAccess.make_dir_recursive_absolute(out_dir)
	var txt := FileAccess.get_file_as_string(zone_path)
	var zone: Dictionary = JSON.parse_string(txt)
	builder = ZoneBuilder.new()
	var t0 := Time.get_ticks_msec()
	builder.build(self, zone)
	print("Zone gebaut in ", Time.get_ticks_msec() - t0, " ms")
	cam = Camera3D.new()
	cam.fov = 60
	cam.far = 900
	add_child(cam)
	_spawn_characters()
	var all := {
		"village": [Vector3(38, 22, 62), Vector3(2, 2, 16)],
		"plaza": [Vector3(6, 9, 44), Vector3(2, 1, 18)],
		"chars": [Vector3(0.5, 2.2, 31.5), Vector3(0.5, 1.2, 24.5)],
		"close1": [Vector3(-2.0, 1.7, 27.6), Vector3(-2.0, 1.25, 24.5)],
		"close2": [Vector3(2.0, 1.7, 27.6), Vector3(2.0, 1.25, 24.5)],
		"close3": [Vector3(-5.8, 1.2, 26.8), Vector3(-5.8, 0.7, 24.5)],
		"close4": [Vector3(5.9, 1.7, 27.6), Vector3(5.9, 1.25, 24.5)],
		"creatures": [Vector3(-26, 3.0, -30), Vector3(-26, 1.0, -40)],
		"castle": [Vector3(0, 28, -34), Vector3(0, 10, -112)],
		"courtyard": [Vector3(0, 13, -88), Vector3(0, 9, -120)],
		"forest": [Vector3(-95, 12, -20), Vector3(-130, 3, -60)],
		"farm": [Vector3(60, 12, 2), Vector3(80, 4, 40)],
		"camp": [Vector3(100, 18, -60), Vector3(126, 3, -98)],
		"crypt": [Vector3(-100, 10, 112), Vector3(-125, 2, 128)],
		"lake": [Vector3(-40, 10, 20), Vector3(-70, -1, 0)],
		"dungeon": [Vector3(0, 6, 20), Vector3(0, 1, -30)],
	}
	if zone.get("type") == "dungeon":
		all = {"dungeon": [Vector3(0, 5, 4), Vector3(0, 1.5, -40)], "boss": [Vector3(-8, 6, -90), Vector3(-16, 1, -110)]}
	for k in all:
		if only == "" or k in only.split(","):
			shots.append([k, all[k][0], all[k][1]])
	_apply_shot()


func _h(x: float, z: float) -> float:
	return builder.height(x, z)


func _place(model: Node3D, x: float, z: float, rot := 0.0) -> void:
	add_child(model)
	model.position = Vector3(x, _h(x, z), z)
	model.rotation.y = rot
	_models.append(model)


func _item(sub: String, slot: String, q: int, vis: Dictionary, id := "") -> Dictionary:
	return {"sub": sub, "slot": slot, "q": q, "vis": vis, "id": id}


func _spawn_characters() -> void:
	var y0 := 24.5
	# Ritter mit Platte (episch)
	var knight := HumanoidModel.new({"skin": "#e0ae8c", "hair": "#6a4422", "hair_style": "short", "beard": "#6a4422"}, {
		"chest": _item("platte", "chest", 4, {"m": "#c8ccd8", "c": "#2d4f9a", "a": "#e0b648", "g": "#60a0ff"}),
		"shoulders": _item("platte", "shoulders", 4, {"m": "#c8ccd8", "c": "#2d4f9a", "a": "#e0b648", "g": "#60a0ff"}),
		"legs": _item("platte", "legs", 3, {"m": "#b8bcc8"}),
		"feet": _item("platte", "feet", 3, {"m": "#b8bcc8"}),
		"hands": _item("platte", "hands", 3, {"m": "#b8bcc8"}),
		"back": _item("stoff", "back", 3, {"c": "#2d4f9a"}),
		"main_hand": _item("schwert", "main_hand", 4, {"m": "#dfe6f0", "a": "#e0b648", "g": "#80c0ff"}),
		"off_hand": _item("schild", "off_hand", 3, {"c": "#2d4f9a", "m": "#c8ccd8", "a": "#e0b648"}),
	})
	_place(knight, -3.0, y0, PI)
	knight.combat = true
	# Magierin in Robe
	var mage := HumanoidModel.new({"body": "f", "skin": "#f2c9a8", "hair": "#d8b060", "hair_style": "long"}, {
		"chest": _item("stoff", "chest", 3, {"c": "#5a2a8a", "c2": "#2a1040"}),
		"shoulders": _item("stoff", "shoulders", 3, {"c": "#5a2a8a"}),
		"head": _item("stoff", "head", 3, {"c": "#5a2a8a", "g": "#c080ff"}),
		"main_hand": _item("stab", "main_hand", 3, {"a": "#c9a040", "g": "#c080ff"}),
	})
	_place(mage, -1.0, y0, PI)
	mage.casting = true
	mage.cast_color = Color(0.8, 0.5, 1.0)
	# Simon
	var simon := HumanoidModel.new({"skin": "#e8b89a", "hair": "#4a2c17", "hair_style": "short", "beard": "#4a2c17", "top": "#6b1d3a",
		"bottom": "#2b1a2f", "cape": "#8f1d2c", "crown": true, "eyes": "big"})
	_place(simon, 1.0, y0, PI)
	# Kathi
	var kathi := HumanoidModel.new({"body": "f", "skin": "#f2c9a8", "hair": "#e3c06a", "hair_style": "long", "top": "#e88fb0", "bottom": "#e88fb0", "dress": true, "apron": "#f4f0e6"})
	_place(kathi, 3.0, y0, PI)
	# Dorftrottel
	var trottel := HumanoidModel.new({"skin": "#f0c4a0", "hair": "#c4632f", "hair_style": "wild", "top": "#9a8a3a", "bottom": "#6a4a2a", "anim": "goofy"})
	_place(trottel, 5.0, y0, PI)
	# Gaukelkobold & einäugiger Kobold
	var gk := HumanoidModel.new({"kind": "kobold", "skin": "#9c6b3c", "top": "#d43c8f", "bottom": "#2fb5a8", "hat": "jester", "anim": "juggle"})
	gk.scale = Vector3.ONE * 0.85
	_place(gk, -5.0, y0, PI)
	var ek := HumanoidModel.new({"kind": "kobold", "skin": "#7d6a4a", "top": "#3a3a3a", "bottom": "#5a4a3a", "eyepatch": true, "hood": true, "anim": "shifty"})
	ek.scale = Vector3.ONE * 0.85
	_place(ek, -6.6, y0, PI)
	# Der Blinde
	var blind := HumanoidModel.new({"skin": "#c9a084", "hair": "#e0e0e0", "hair_style": "long", "beard": "#e0e0e0", "beard_style": "long", "top": "#5a4a6a", "bottom": "#3a3040", "robe": true, "blindfold": true, "held": "staff"})
	_place(blind, 6.8, y0, PI)
	# Kreaturen
	var cx := -26.0
	var cz := -40.0
	var list := [["wolf", {}], ["boar", {}], ["bear", {}], ["spider", {}], ["chicken", {}], ["golem", {}], ["fire_elemental", {}], ["treant", {}]]
	for i in list.size():
		var c := CreatureModel.new(list[i][0], list[i][1])
		_place(c, cx - 10.0 + i * 3.0, cz, PI)
	var skel := HumanoidModel.new({"kind": "skeleton", "held": "sword"})
	_place(skel, cx + 14.0, cz, PI)
	var dragon := CreatureModel.new("dragon", {"tint": "#3a3436", "tint2": "#ff6a1a"})
	dragon.scale = Vector3.ONE * 1.6
	_place(dragon, cx + 2.0, cz - 9.0, PI * 0.8)
	var dwarf := HumanoidModel.new({"kind": "dwarf", "skin": "#e0ae8c", "hair": "#a86a32", "top": "#3a5a8a", "bottom": "#4a3a2a", "held": "hammer2h", "armor": true})
	_place(dwarf, cx + 17.0, cz, PI)


func _apply_shot() -> void:
	if _shot_i >= shots.size():
		get_tree().quit()
		return
	var s: Array = shots[_shot_i]
	var pos: Vector3 = s[1]
	var target: Vector3 = s[2]
	# Höhen relativ zum Gelände
	pos.y += _h(pos.x, pos.z)
	target.y += _h(target.x, target.z)
	cam.position = pos
	cam.look_at(target)
	if builder.grass:
		builder.grass.focus = target
	_frames = 0


func _process(_delta: float) -> void:
	_frames += 1
	if _frames == 12:
		var img := get_viewport().get_texture().get_image()
		var path := out_dir.path_join("%s.png" % shots[_shot_i][0])
		img.save_png(path)
		print("Screenshot: ", path)
		_shot_i += 1
		_apply_shot()
