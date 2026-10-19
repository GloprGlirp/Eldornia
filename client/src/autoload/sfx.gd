extends Node
## Prozedural erzeugte Klänge (keine externen Audiodateien nötig) und Hintergrundmusik pro Region.

const RATE := 22050

var _cache: Dictionary = {}
var _players: Array = []
var _players3d: Array = []
var _music: AudioStreamPlayer
var _music_cache: Dictionary = {}
var _music_theme := ""
var _thread: Thread
var _pending_theme := ""
var _last_play: Dictionary = {}


func _ready() -> void:
	for i in 12:
		var p := AudioStreamPlayer.new()
		p.bus = "Master"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	add_child(_music)
	_music.finished.connect(func(): if _music.stream: _music.play())


func play(name: String, vol := 0.0, pitch := 1.0) -> void:
	if Settings.vol_sfx <= 0.01:
		return
	var t := Time.get_ticks_msec()
	if t - int(_last_play.get(name, 0)) < 45:
		return
	_last_play[name] = t
	var s := _sound(name)
	if s == null:
		return
	for p in _players:
		if not p.playing:
			p.stream = s
			p.volume_db = vol + linear_to_db(Settings.vol_sfx)
			p.pitch_scale = pitch * randf_range(0.96, 1.04)
			p.play()
			return


func play_at(name: String, pos: Vector3, parent: Node, vol := 0.0) -> void:
	if Settings.vol_sfx <= 0.01 or parent == null or not parent.is_inside_tree():
		return
	var s := _sound(name)
	if s == null:
		return
	var p: AudioStreamPlayer3D = null
	for q in _players3d:
		if is_instance_valid(q) and not q.playing and q.get_parent() == parent:
			p = q
			break
	if p == null:
		if _players3d.size() > 24:
			_players3d = _players3d.filter(func(x): return is_instance_valid(x))
		p = AudioStreamPlayer3D.new()
		p.unit_size = 8.0
		p.max_distance = 70.0
		parent.add_child(p)
		_players3d.append(p)
	p.global_position = pos
	p.stream = s
	p.volume_db = vol + linear_to_db(Settings.vol_sfx)
	p.pitch_scale = randf_range(0.92, 1.08)
	p.play()


# ============================================================================== Synthese
func _sound(name: String) -> AudioStreamWAV:
	if _cache.has(name):
		return _cache[name]
	var data := PackedFloat32Array()
	match name:
		"click": data = _tone(880, 0.05, 0.3, "sine", 0.0)
		"open": data = _sweep(300, 600, 0.12, 0.25)
		"close": data = _sweep(600, 300, 0.1, 0.22)
		"swing": data = _noise_burst(0.18, 0.35, 2500, 900)
		"hit": data = _mix([_noise_burst(0.12, 0.5, 900, 200), _tone(110, 0.12, 0.5, "sine", 6.0)])
		"crit": data = _mix([_noise_burst(0.2, 0.6, 1400, 300), _tone(90, 0.2, 0.6, "sine", 4.0), _tone(1200, 0.08, 0.15, "square", 8.0)])
		"block": data = _mix([_tone(520, 0.15, 0.35, "square", 9.0), _noise_burst(0.08, 0.3, 3000, 1500)])
		"miss": data = _noise_burst(0.14, 0.2, 3500, 1800)
		"cast": data = _shimmer(420, 0.6, 0.18)
		"fire": data = _mix([_noise_burst(0.5, 0.55, 600, 120), _sweep(200, 80, 0.4, 0.3)])
		"frost": data = _mix([_shimmer(1400, 0.4, 0.25), _noise_burst(0.3, 0.25, 5000, 3000)])
		"arcane": data = _shimmer(900, 0.5, 0.3)
		"shadow": data = _mix([_sweep(220, 70, 0.5, 0.4), _noise_burst(0.3, 0.2, 500, 200)])
		"nature": data = _mix([_shimmer(660, 0.4, 0.22), _noise_burst(0.25, 0.15, 2000, 800)])
		"holy", "heal": data = _chord([523, 659, 784], 0.6, 0.22)
		"levelup": data = _arp([392, 523, 659, 784, 1046], 0.11, 0.3)
		"quest": data = _arp([523, 659, 784], 0.12, 0.28)
		"quest_done": data = _arp([392, 523, 659, 784, 1046, 1318], 0.09, 0.3)
		"coin": data = _mix([_tone(1800, 0.08, 0.25, "square", 18.0), _tone(2400, 0.12, 0.2, "sine", 12.0)])
		"loot": data = _arp([700, 1050], 0.07, 0.2)
		"error": data = _tone(140, 0.16, 0.35, "square", 3.0)
		"step": data = _noise_burst(0.06, 0.12, 700, 300)
		"jump": data = _sweep(250, 450, 0.12, 0.15)
		"death": data = _sweep(400, 60, 0.9, 0.35)
		"whisper": data = _chord([880, 1320], 0.25, 0.18)
		"achievement": data = _arp([523, 784, 1046, 1568], 0.1, 0.32)
		"boss": data = _mix([_tone(55, 1.2, 0.5, "saw", 1.5), _tone(82, 1.2, 0.35, "saw", 1.5)])
		"warning": data = _mix([_tone(440, 0.18, 0.32, "square", 5.0), _tone(554, 0.18, 0.3, "square", 5.0, 0.18), _tone(440, 0.2, 0.3, "square", 5.0, 0.36)])
		"popup": data = _chord([660, 990], 0.18, 0.16)
		"quest_accept": data = _arp([523, 784], 0.1, 0.25)
		"ready": data = _arp([523, 659, 784, 1046], 0.14, 0.32)
		"discover": data = _chord([392, 494, 587, 784], 1.2, 0.18)
		"sell": data = _mix([_tone(1500, 0.08, 0.22, "square", 18.0), _tone(1900, 0.1, 0.2, "sine", 12.0, 0.06)])
		"warn": data = _mix([_tone(330, 0.15, 0.3, "square", 6.0), _tone(330, 0.15, 0.3, "square", 6.0, 0.2)])
		"mount": data = _arp([300, 400, 500], 0.08, 0.2)
		"gather": data = _noise_burst(0.3, 0.3, 1800, 500)
		"craft": data = _mix([_tone(800, 0.1, 0.3, "square", 14.0), _tone(800, 0.1, 0.25, "square", 14.0, 0.25)])
		_: return null
	var s := _to_wav(data)
	_cache[name] = s
	return s


func _to_wav(data: PackedFloat32Array) -> AudioStreamWAV:
	var bytes := PackedByteArray()
	bytes.resize(data.size() * 2)
	for i in data.size():
		bytes.encode_s16(i * 2, int(clampf(data[i], -1.0, 1.0) * 32000))
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_16_BITS
	s.mix_rate = RATE
	s.stereo = false
	s.data = bytes
	return s


func _env(i: int, n: int, attack := 0.01, decay := 4.0) -> float:
	var t := float(i) / RATE
	var a := minf(1.0, t / maxf(0.001, attack))
	var d := exp(-t * decay)
	var tail := 1.0 - float(i) / n
	return a * d * minf(1.0, tail * 8.0)


func _osc(kind: String, ph: float) -> float:
	match kind:
		"square":
			return 1.0 if fmod(ph, 1.0) < 0.5 else -1.0
		"saw":
			return fmod(ph, 1.0) * 2.0 - 1.0
		_:
			return sin(ph * TAU)


func _tone(freq: float, dur: float, vol: float, kind := "sine", decay := 6.0, delay := 0.0) -> PackedFloat32Array:
	var n := int((dur + delay) * RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var d0 := int(delay * RATE)
	for i in n:
		if i < d0:
			out[i] = 0.0
			continue
		var j := i - d0
		out[i] = _osc(kind, freq * j / RATE) * vol * _env(j, n - d0, 0.005, decay)
	return out


func _sweep(f0: float, f1: float, dur: float, vol: float) -> PackedFloat32Array:
	var n := int(dur * RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var ph := 0.0
	for i in n:
		var f := lerpf(f0, f1, float(i) / n)
		ph += f / RATE
		out[i] = sin(ph * TAU) * vol * _env(i, n, 0.01, 2.0)
	return out


func _noise_burst(dur: float, vol: float, f_hi: float, f_lo: float) -> PackedFloat32Array:
	var n := int(dur * RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	var lp := 0.0
	var prev := 0.0
	for i in n:
		var cutoff := lerpf(f_hi, f_lo, float(i) / n)
		var a := clampf(cutoff / RATE * TAU, 0.0, 1.0)
		lp += (randf() * 2.0 - 1.0 - lp) * a
		var hp := lp - prev * 0.6
		prev = lp
		out[i] = hp * vol * 1.6 * _env(i, n, 0.004, 9.0 / dur)
	return out


func _shimmer(freq: float, dur: float, vol: float) -> PackedFloat32Array:
	var n := int(dur * RATE)
	var out := PackedFloat32Array()
	out.resize(n)
	for i in n:
		var t := float(i) / RATE
		var v := sin(freq * t * TAU) + 0.5 * sin(freq * 1.5 * t * TAU + sin(t * 30.0)) + 0.3 * sin(freq * 2.01 * t * TAU)
		out[i] = v * vol * 0.5 * sin(PI * float(i) / n)
	return out


func _chord(freqs: Array, dur: float, vol: float) -> PackedFloat32Array:
	var parts: Array = []
	for i in freqs.size():
		parts.append(_tone(freqs[i], dur, vol / freqs.size() * 1.6, "sine", 3.0, i * 0.04))
	return _mix(parts)


func _arp(freqs: Array, step: float, vol: float) -> PackedFloat32Array:
	var parts: Array = []
	for i in freqs.size():
		parts.append(_tone(freqs[i], step * 4.0, vol, "sine", 5.0, i * step))
		parts.append(_tone(freqs[i] * 2.0, step * 3.0, vol * 0.25, "sine", 7.0, i * step))
	return _mix(parts)


func _mix(parts: Array) -> PackedFloat32Array:
	var n := 0
	for p in parts:
		n = maxi(n, p.size())
	var out := PackedFloat32Array()
	out.resize(n)
	for p in parts:
		for i in p.size():
			out[i] += p[i]
	return out


# ============================================================================== Musik (generativ)
const MUSIC_SCALES := {
	"gruen": [0, 2, 4, 7, 9], "frost": [0, 2, 3, 7, 8], "mond": [0, 2, 4, 6, 9], "asche": [0, 1, 4, 5, 7],
	"himmel": [0, 2, 4, 7, 11], "dungeon": [0, 1, 3, 6, 7], "menu": [0, 2, 4, 7, 9],
}
const MUSIC_ROOT := {"gruen": 196.0, "frost": 174.6, "mond": 220.0, "asche": 146.8, "himmel": 233.1, "dungeon": 130.8, "menu": 196.0}


func play_music(theme: String) -> void:
	if theme == _music_theme:
		return
	_music_theme = theme
	if Settings.vol_music <= 0.01:
		_music.stop()
		return
	if _music_cache.has(theme):
		_start_music(_music_cache[theme])
		return
	if _thread and _thread.is_alive():
		_pending_theme = theme
		return
	_thread = Thread.new()
	_thread.start(_gen_music.bind(theme))


func _start_music(s: AudioStreamWAV) -> void:
	_music.stream = s
	_music.volume_db = linear_to_db(maxf(0.001, Settings.vol_music)) - 6.0
	_music.play()


func _gen_music(theme: String) -> void:
	var rate := 16000
	var dur := 48.0
	var n := int(dur * rate)
	var out := PackedFloat32Array()
	out.resize(n)
	var scale: Array = MUSIC_SCALES.get(theme, MUSIC_SCALES["gruen"])
	var root: float = MUSIC_ROOT.get(theme, 196.0)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(theme)
	var chords := [0, 3, 4, 2] if theme != "dungeon" else [0, 1, 0, 3]
	var bar := dur / 8.0
	# Flächenklänge
	for b in 8:
		var deg: int = chords[b % chords.size()]
		for k in [0, 2, 4]:
			var idx: int = (deg + k) % scale.size()
			var octave := int((deg + k) / scale.size())
			var f := root * pow(2.0, (scale[idx] + 12 * octave) / 12.0) * 0.5
			var s0 := int(b * bar * rate)
			var s1 := mini(n, int((b + 1.15) * bar * rate))
			for i in range(s0, s1):
				var t := float(i - s0) / rate
				var env := minf(1.0, t / 1.5) * minf(1.0, float(s1 - i) / rate / 1.2)
				out[i] += (sin(f * t * TAU) + 0.35 * sin(f * 2.0 * t * TAU + 0.3)) * 0.05 * env
	# Melodie (gezupft)
	var t_note := 0.0
	while t_note < dur - 1.0:
		var step: float = [0.5, 0.75, 1.0, 1.5][rng.randi() % 4] * (1.3 if theme == "dungeon" else 1.0)
		if rng.randf() < 0.78:
			var idx := rng.randi() % scale.size()
			var f := root * pow(2.0, (scale[idx] + 12 * (1 + rng.randi() % 2)) / 12.0)
			var s0 := int(t_note * rate)
			var len := int(minf(1.6, step * 1.8) * rate)
			for i in range(s0, mini(n, s0 + len)):
				var t := float(i - s0) / rate
				out[i] += (sin(f * t * TAU) + 0.3 * sin(f * 3.0 * t * TAU)) * 0.09 * exp(-t * 3.2)
		t_note += step
	# leichter Hall
	var d := int(0.23 * rate)
	for i in range(d, n):
		out[i] += out[i - d] * 0.32
	var bytes := PackedByteArray()
	bytes.resize(n * 2)
	for i in n:
		bytes.encode_s16(i * 2, int(clampf(out[i], -1.0, 1.0) * 30000))
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_16_BITS
	s.mix_rate = rate
	s.data = bytes
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_end = n
	call_deferred("_music_ready", theme, s)


func _music_ready(theme: String, s: AudioStreamWAV) -> void:
	_music_cache[theme] = s
	if _thread:
		_thread.wait_to_finish()
		_thread = null
	if theme == _music_theme:
		_start_music(s)
	if _pending_theme != "" and _pending_theme != theme:
		var p := _pending_theme
		_pending_theme = ""
		_music_theme = ""
		play_music(p)


func set_music_volume() -> void:
	if _music.playing:
		_music.volume_db = linear_to_db(maxf(0.001, Settings.vol_music)) - 6.0
	elif Settings.vol_music > 0.01 and _music_theme != "":
		var th := _music_theme
		_music_theme = ""
		play_music(th)
