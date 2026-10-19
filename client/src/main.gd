extends Node
## Einstiegspunkt: entscheidet zwischen Spiel und Entwickler-Testszenen.


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	for a in args:
		if a.begins_with("--visual-test"):
			var vt = load("res://src/dev/visual_test.gd").new()
			add_child(vt)
			return
