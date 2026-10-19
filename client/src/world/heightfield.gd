class_name Heightfield
extends RefCounted
## Höhenkarte einer Außenzone – identisch zur Berechnung auf dem Server
## (gleiche Dreiecksaufteilung), damit Client und Server dieselbe Bodenhöhe sehen.

var n := 0
var step := 2.0
var size := 0.0
var half := 0.0
var h := PackedFloat32Array()
var void_level := -1000.0   # Himmelsbruch: Löcher in der Welt


func load_from(data: Dictionary) -> void:
	n = int(data["n"])
	step = float(data["step"])
	size = float(data["size"])
	half = size * 0.5
	var raw := Marshalls.base64_to_raw(str(data["heights"]))
	h.resize(n * n)
	for i in n * n:
		h[i] = raw.decode_s16(i * 2) * 0.01
	void_level = float(data.get("void", -1000.0))


func at_index(i: int, j: int) -> float:
	i = clampi(i, 0, n - 1)
	j = clampi(j, 0, n - 1)
	return h[j * n + i]


func height(x: float, z: float) -> float:
	var fx := clampf((x + half) / step, 0.0, n - 1.001)
	var fz := clampf((z + half) / step, 0.0, n - 1.001)
	var i := int(fx)
	var j := int(fz)
	var tx := fx - i
	var tz := fz - j
	var a := h[j * n + i]
	var b := h[j * n + i + 1]
	var c := h[(j + 1) * n + i]
	var e := h[(j + 1) * n + i + 1]
	if tx + tz <= 1.0:
		return a + (b - a) * tx + (c - a) * tz
	return e + (c - e) * (1.0 - tx) + (b - e) * (1.0 - tz)


func normal(x: float, z: float) -> Vector3:
	var d := step
	var hl := height(x - d, z)
	var hr := height(x + d, z)
	var hd := height(x, z - d)
	var hu := height(x, z + d)
	return Vector3(hl - hr, 2.0 * d, hd - hu).normalized()


func is_void(x: float, z: float) -> bool:
	return height(x, z) <= void_level + 1.0


## Strahl gegen das Gelände (für Bodenziele und Kamerakollision)
func raycast(origin: Vector3, dir: Vector3, max_dist := 300.0) -> Variant:
	var t := 0.0
	var stepl := 1.0
	var prev_above := origin.y - height(origin.x, origin.z)
	while t < max_dist:
		t += stepl
		var p := origin + dir * t
		var above := p.y - height(p.x, p.z)
		if above < 0.0 and prev_above >= 0.0:
			# Feinsuche
			var lo := t - stepl
			var hi := t
			for k in 10:
				var mid := (lo + hi) * 0.5
				var q := origin + dir * mid
				if q.y - height(q.x, q.z) < 0.0:
					hi = mid
				else:
					lo = mid
			return origin + dir * hi
		prev_above = above
		stepl = clampf(absf(above) * 0.5, 0.5, 4.0)
	return null
