extends Node
## Automatischer Durchlauf für Tests: meldet sich an, betritt die Welt, öffnet Fenster und speichert
## Bildschirmfotos. Aufruf: godot --path client -- --server=http://127.0.0.1:8000 --auto=name:pass --out=/pfad [--steps=a,b]

var main
var user := ""
var pw := ""
var out_dir := "user://auto"
var steps: Array = []


func _init(p_main) -> void:
	main = p_main


func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--auto="):
			var p := a.substr(7).split(":")
			user = p[0]
			pw = p[1] if p.size() > 1 else ""
		elif a.begins_with("--out="):
			out_dir = a.substr(6)
		elif a.begins_with("--steps="):
			steps = Array(a.substr(8).split(","))
	DirAccess.make_dir_recursive_absolute(out_dir)
	_run()


func _wait(s: float) -> void:
	await get_tree().create_timer(s).timeout


func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png(out_dir + "/" + name + ".png")
	print("Bild: ", name)


func _run() -> void:
	await _wait(1.0)
	await shot("01_login")
	var done := [false]
	Net.post_json("/api/login", {"username": user, "password": pw}, func(ok, code, data):
		if ok:
			Net.token = str(data["token"])
			Game.username = user
		else:
			print("Login fehlgeschlagen: ", code, " ", data)
		done[0] = true
	)
	while not done[0]:
		await _wait(0.1)
	main._on_logged_in()
	await _wait(3.0)
	await shot("02_select")
	var chars := [null]
	Net.get_json("/api/characters", func(ok, _c, data):
		chars[0] = data if ok else []
	)
	while chars[0] == null:
		await _wait(0.1)
	var lst: Array = chars[0].get("characters", []) if chars[0] is Dictionary else chars[0]
	if lst.is_empty():
		print("Keine Charaktere")
		get_tree().quit(1)
		return
	main._enter_world(int(lst[0]["id"]))
	var t := 0.0
	while (main.world == null or main.world.me == null or main.loading != null) and t < 90.0:
		await _wait(0.5)
		t += 0.5
	await _wait(4.0)
	await shot("03_world")
	var hud = main.hud
	var wins := ["inventar", "charakter", "zauberbuch", "talente", "questlog", "karte", "berufe", "erfolge", "sammlung",
		"gruppensuche", "soziales", "gilde", "einstellungen", "menue", "hilfe"]
	for w in wins:
		if not steps.is_empty() and not w in steps:
			continue
		hud.open_window(w)
		await _wait(1.2)
		await shot("w_" + w)
		hud.close_window(w)
		await _wait(0.2)
	# Gespräch mit nächstem NPC
	var best = null
	var bd := 1e9
	for e in main.world.entities.values():
		if e.kind == "npc":
			var d: float = e.global_position.distance_to(main.world.me.global_position)
			if d < bd:
				bd = d
				best = e
	if best:
		Game.send({"t": "chat", "text": ".tp %f %f" % [best.global_position.x + 1.5, best.global_position.z + 1.5]})
		await _wait(2.0)
		Game.send({"t": "interact", "id": best.id})
		await _wait(1.5)
		await shot("04_gossip")
	# Kampf
	var mob = null
	bd = 1e9
	for e in main.world.entities.values():
		if e.kind == "mob" and e.is_attackable() and not e.dead:
			var d2: float = e.global_position.distance_to(main.world.me.global_position)
			if d2 < bd:
				bd = d2
				mob = e
	if mob:
		Game.send({"t": "chat", "text": ".tp %f %f" % [mob.global_position.x + 3, mob.global_position.z + 3]})
		await _wait(2.0)
		main.world.set_target(mob.id)
		main.world.interact(mob)
		for i in 6:
			main.hud.bars.trigger(i % 3)
			await _wait(1.6)
		await shot("05_combat")
	await _wait(1.0)
	print("Automatischer Durchlauf fertig.")
	get_tree().quit(0)
