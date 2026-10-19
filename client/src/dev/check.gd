extends Node
## Entwicklerprüfung: lädt alle Skripte und meldet Parse-/Kompilierfehler (godot --headless -- --check).


func _ready() -> void:
	var bad := 0
	var n := 0
	for path in _scripts("res://src"):
		n += 1
		var s = load(path)
		if s == null or not (s is Script) or not s.can_instantiate():
			bad += 1
			print("FEHLER: ", path)
	print("Skripte geprüft: %d, fehlerhaft: %d" % [n, bad])
	get_tree().quit(1 if bad > 0 else 0)


func _scripts(dir: String) -> Array:
	var out: Array = []
	var d := DirAccess.open(dir)
	if d == null:
		return out
	for f in d.get_files():
		if f.ends_with(".gd"):
			out.append(dir + "/" + f)
	for sub in d.get_directories():
		out += _scripts(dir + "/" + sub)
	return out
