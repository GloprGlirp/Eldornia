class_name Themes
extends RefCounted
## Farbstimmungen der Regionen von Eldornia (Gelände, Himmel, Licht, Vegetation).

const DATA := {
	"gruen": {
		"terrain": {
			"grass_a": "#5f9a2c", "grass_b": "#3b7322", "grass_c": "#a3a63a", "flower_a": "#f4dc5a", "flower_b": "#d870c0",
			"dirt": "#94704a", "dirt_dark": "#5e4630", "rock": "#8f877a", "rock_dark": "#57514c",
			"cobble": "#9a948a", "cobble_dark": "#4c4741", "farmland": "#5a3e26", "sand": "#c4b07a",
			"snow": "#eef4ff", "accent": "#4a8a3a", "snow_amount": 0.0, "snow_height": 9999.0, "flower_density": 1.0,
		},
		"sky": {"top": "#3f7fd0", "horizon": "#cfe3ef", "ground": "#6f8070", "sun": "#fff0d0",
				"cloud_light": "#ffffff", "cloud_dark": "#9fb0c8", "cover": 0.48},
		"fog": "#bcd3e2", "fog_density": 0.0028, "sun_color": "#fff1d6", "sun_energy": 1.35,
		"ambient": "#a9bccc", "ambient_energy": 0.55, "sun_pitch": -48.0, "sun_yaw": 35.0,
		"leaf": ["#7fae32", "#2b5a1a", "#c6d45a"], "pine": ["#3f7a3a", "#173a20", "#6aa060"],
		"grass": ["#5f9a2c", "#3b7322", "#c9d060"], "water": ["#3aa6b0", "#0e3f5e"],
		"bark": ["#6e4a2e", "#3c2616"], "glow": 0.25,
	},
	"frost": {
		"terrain": {
			"grass_a": "#7d9a7a", "grass_b": "#58745e", "grass_c": "#a7b4a0", "flower_a": "#dfe8ff", "flower_b": "#9fc0ff",
			"dirt": "#8a7e74", "dirt_dark": "#57504a", "rock": "#8d96a3", "rock_dark": "#4c5260",
			"cobble": "#a0a6ae", "cobble_dark": "#4a4e56", "farmland": "#5a4a3e", "sand": "#b0aaa0",
			"snow": "#f2f7ff", "accent": "#a8d8ff", "snow_amount": 1.0, "snow_height": 14.0, "flower_density": 0.2,
		},
		"sky": {"top": "#5d86c2", "horizon": "#dde8f2", "ground": "#8a96a6", "sun": "#fff6e6",
				"cloud_light": "#ffffff", "cloud_dark": "#aab6c8", "cover": 0.62},
		"fog": "#d6e2ee", "fog_density": 0.0042, "sun_color": "#f4f6ff", "sun_energy": 1.2,
		"ambient": "#c4d4e8", "ambient_energy": 0.7, "sun_pitch": -38.0, "sun_yaw": 60.0,
		"leaf": ["#6e9a7a", "#22403a", "#e8f0ff"], "pine": ["#3d6a5a", "#152e2a", "#e6eef8"],
		"grass": ["#7d9a7a", "#58745e", "#d8e4e0"], "water": ["#7ac0d8", "#1e4a6e"],
		"bark": ["#5a4a40", "#2e2420"], "glow": 0.2,
	},
	"mond": {
		"terrain": {
			"grass_a": "#3f7a6a", "grass_b": "#244a46", "grass_c": "#6a8a5a", "flower_a": "#9fe8ff", "flower_b": "#e090ff",
			"dirt": "#6a5a6a", "dirt_dark": "#3e3446", "rock": "#7a7a92", "rock_dark": "#43405a",
			"cobble": "#8a8aa0", "cobble_dark": "#3a3850", "farmland": "#3e3040", "sand": "#a8a0b8",
			"snow": "#eef0ff", "accent": "#5ae0c8", "snow_amount": 0.0, "snow_height": 9999.0, "flower_density": 1.6,
		},
		"sky": {"top": "#3a3a8a", "horizon": "#b8a8d8", "ground": "#4a4a6a", "sun": "#d8e0ff",
				"cloud_light": "#e8e0ff", "cloud_dark": "#7a70a8", "cover": 0.45},
		"fog": "#8a88b8", "fog_density": 0.0055, "sun_color": "#c8d4ff", "sun_energy": 0.9,
		"ambient": "#8a8ac8", "ambient_energy": 0.75, "sun_pitch": -32.0, "sun_yaw": -40.0,
		"leaf": ["#4ac0a0", "#1a3a50", "#c8a0ff"], "pine": ["#3a8a7a", "#16303a", "#90e0d0"],
		"grass": ["#3f7a6a", "#244a46", "#8ae0d0"], "water": ["#5ad0d8", "#1a2a5e"],
		"bark": ["#5a4a6a", "#2a2036"], "glow": 0.6, "leaf_emis": "#103a30",
	},
	"asche": {
		"terrain": {
			"grass_a": "#5a4a3a", "grass_b": "#3a2e26", "grass_c": "#7a5a3a", "flower_a": "#ff8a30", "flower_b": "#ffcf50",
			"dirt": "#5a4438", "dirt_dark": "#2e221c", "rock": "#4a4240", "rock_dark": "#221e1e",
			"cobble": "#5a5250", "cobble_dark": "#1e1a1a", "farmland": "#2a1e18", "sand": "#6a5a4a",
			"snow": "#a09890", "accent": "#2a1a14", "accent_glow": "#ff5a10", "snow_amount": 0.0, "snow_height": 9999.0,
			"flower_density": 0.15,
		},
		"sky": {"top": "#4a2a2a", "horizon": "#c87a4a", "ground": "#3a2a24", "sun": "#ffb070",
				"cloud_light": "#a07a6a", "cloud_dark": "#3a2a2a", "cover": 0.7},
		"fog": "#7a4a36", "fog_density": 0.0065, "sun_color": "#ffb878", "sun_energy": 1.25,
		"ambient": "#a0705a", "ambient_energy": 0.55, "sun_pitch": -28.0, "sun_yaw": 20.0,
		"leaf": ["#5a4a30", "#2a1a10", "#a07030"], "pine": ["#3a3020", "#1a120c", "#6a5030"],
		"grass": ["#5a4a3a", "#3a2e26", "#8a6040"], "water": ["#ff7a20", "#3a0a04"], "lava": true,
		"bark": ["#2a2220", "#100c0c"], "glow": 0.7,
	},
	"himmel": {
		"terrain": {
			"grass_a": "#6ab05a", "grass_b": "#3a8a5a", "grass_c": "#c8d880", "flower_a": "#ffffff", "flower_b": "#ffd0f0",
			"dirt": "#b0a080", "dirt_dark": "#7a6a50", "rock": "#c8c0b0", "rock_dark": "#8a8070",
			"cobble": "#e0d8c8", "cobble_dark": "#9a9080", "farmland": "#6a5a40", "sand": "#e8dcc0",
			"snow": "#ffffff", "accent": "#a0f0ff", "accent_glow": "#40a0c0", "snow_amount": 0.0, "snow_height": 9999.0,
			"flower_density": 1.4,
		},
		"sky": {"top": "#2a6ad8", "horizon": "#e8f0ff", "ground": "#c8d8f0", "sun": "#fffbe8",
				"cloud_light": "#ffffff", "cloud_dark": "#c8d4ec", "cover": 0.35},
		"fog": "#d8e6f8", "fog_density": 0.0022, "sun_color": "#fffaf0", "sun_energy": 1.5,
		"ambient": "#c0d0f0", "ambient_energy": 0.7, "sun_pitch": -55.0, "sun_yaw": 10.0,
		"leaf": ["#8ad070", "#2a6a5a", "#fff0a0"], "pine": ["#5aa090", "#1a4a40", "#c0f0e0"],
		"grass": ["#6ab05a", "#3a8a5a", "#e8f0a0"], "water": ["#7ae0f0", "#2060c0"],
		"bark": ["#9a8070", "#5a4436"], "glow": 0.45,
	},
	"dungeon": {
		"terrain": {},
		"sky": {"top": "#05060a", "horizon": "#0b0d14", "ground": "#05060a", "sun": "#6a7aa8",
				"cloud_light": "#101218", "cloud_dark": "#08090c", "cover": 0.0},
		"fog": "#0a0b10", "fog_density": 0.02, "sun_color": "#6a7aa8", "sun_energy": 0.15,
		"ambient": "#3a4060", "ambient_energy": 0.45, "sun_pitch": -70.0, "sun_yaw": 0.0,
		"leaf": ["#3a5a2a", "#1a2a10", "#5a7a3a"], "pine": ["#2a4a2a", "#0a1a0a", "#4a6a4a"],
		"grass": ["#2a3a1a", "#1a2a10", "#3a4a2a"], "water": ["#2a5a6a", "#0a1a2a"],
		"bark": ["#3a2a20", "#1a1210"], "glow": 0.5,
	},
}


static func get_theme(id: String) -> Dictionary:
	return DATA.get(id, DATA["gruen"])


static func c(theme: Dictionary, key: String, fallback := "#ffffff") -> Color:
	var v = theme.get(key, fallback)
	return Color.html(str(v))
