shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_lambert_wrap, specular_schlick_ggx;

// Allzweck-Shader für Gebäude, Requisiten, Ausrüstung und Kreaturen.
// Die Muster werden prozedural erzeugt (UV in Metern bzw. objektbezogene Triplanar-Projektion),
// damit alles wie handgemalt wirkt, ohne Texturen zu benötigen.

#include "res://shaders/noise.gdshaderinc"

uniform vec4 albedo : source_color = vec4(0.8, 0.8, 0.8, 1.0);
uniform vec4 albedo2 : source_color = vec4(0.4, 0.4, 0.4, 1.0);
uniform int pattern = 0;
uniform float pattern_scale = 1.0;
uniform bool triplanar = false;
uniform bool use_vertex_color = false;
uniform float roughness_value : hint_range(0.0, 1.0) = 0.85;
uniform float metallic_value : hint_range(0.0, 1.0) = 0.0;
uniform float rim_amount : hint_range(0.0, 1.0) = 0.12;
uniform float rim_tint_value : hint_range(0.0, 1.0) = 0.5;
uniform vec4 emission_color : source_color = vec4(0.0, 0.0, 0.0, 1.0);
uniform float emission_energy = 1.0;
uniform float wind_strength = 0.0;
uniform float edge_wear = 0.0;
uniform float noise_amount = 1.0;

varying vec3 opos;
varying vec3 onorm;
varying vec3 wpos;

void vertex() {
	opos = VERTEX;
	onorm = NORMAL;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	if (wind_strength > 0.0) {
		// Stoffbahnen (Banner, Umhänge): Ausschlag wächst mit UV.y
		float w = UV.y * wind_strength;
		float t = TIME * 2.2 + wpos.x * 0.4 + wpos.z * 0.3;
		VERTEX.x += sin(t + UV.y * 3.0) * w * 0.12;
		VERTEX.z += cos(t * 0.8 + UV.y * 2.0) * w * 0.18;
	}
}

vec2 pat_uv(vec2 uv) {
	if (triplanar) {
		vec3 w = triplanar_weights(onorm);
		if (w.y > w.x && w.y > w.z) {
			return opos.xz;
		} else if (w.x > w.z) {
			return vec2(opos.z, opos.y);
		}
		return vec2(opos.x, opos.y);
	}
	return uv;
}

void fragment() {
	vec2 uv = pat_uv(UV) * pattern_scale;
	vec3 a = albedo.rgb;
	vec3 b = albedo2.rgb;
	if (use_vertex_color) {
		a *= COLOR.rgb;
		b *= COLOR.rgb;
	}
	vec3 col = a;
	float rough = roughness_value;
	float metal = metallic_value;
	vec3 emis = vec3(0.0);
	float n1 = vnoise3(opos * 3.1);
	float n2 = fbm3(opos * 0.9 + 4.0);

	if (pattern == 1) {
		// Holzbretter
		float plank_w = 0.22;
		float px = uv.x / plank_w;
		float id = floor(px);
		float fx = fract(px);
		float seam = smoothstep(0.0, 0.06, fx) * smoothstep(1.0, 0.94, fx);
		float grain = sin((uv.y * 7.0 + vnoise(vec2(uv.y * 0.8, id * 3.7)) * 4.0) + fx * 2.0) * 0.5 + 0.5;
		vec3 pc = mix(b, a, 0.55 + 0.45 * hash12(vec2(id, 1.7)));
		pc *= 0.85 + 0.2 * grain;
		col = mix(b * 0.55, pc, seam);
		float knot = smoothstep(0.08, 0.0, length(vec2(fract(uv.y * 0.7 + hash12(vec2(id))) - 0.5, fx - 0.5)));
		col = mix(col, b * 0.6, knot * 0.6);
	} else if (pattern == 2) {
		// Putz mit Flecken
		float st = fbm2(uv * 1.3);
		col = mix(a, a * vec3(0.88, 0.84, 0.76), smoothstep(0.45, 0.8, st));
		col *= 0.95 + 0.08 * vnoise(uv * 9.0);
		col = mix(col, b, smoothstep(0.75, 0.95, fbm2(uv * 0.6 + 9.0)) * 0.25);
	} else if (pattern == 3) {
		// Steinmauer (Läuferverband)
		float rh = 0.32;
		float row = floor(uv.y / rh);
		float bw = 0.62;
		float off = mod(row, 2.0) * 0.5 * bw;
		float bx = (uv.x + off) / bw;
		vec2 cell = vec2(floor(bx), row);
		vec2 f = vec2(fract(bx), fract(uv.y / rh));
		float mortar = smoothstep(0.0, 0.07, f.x) * smoothstep(1.0, 0.93, f.x) * smoothstep(0.0, 0.1, f.y) * smoothstep(1.0, 0.9, f.y);
		float tint = hash12(cell);
		vec3 stone = mix(a * 0.8, a * 1.12, tint) * (0.88 + 0.2 * vnoise(uv * 7.0 + cell));
		stone = mix(stone, b, smoothstep(0.65, 0.9, n2) * 0.3);
		col = mix(b * 0.6, stone, mortar);
	} else if (pattern == 4) {
		// Dachschindeln (Fischschuppen-Reihen)
		float rh = 0.28;
		float row = floor(uv.y / rh);
		float off = mod(row, 2.0) * 0.5;
		float sx = uv.x / 0.3 + off;
		vec2 cell = vec2(floor(sx), row);
		vec2 f = vec2(fract(sx) - 0.5, fract(uv.y / rh));
		float d = length(vec2(f.x * 1.1, (1.0 - f.y) * 0.9));
		float shingle = smoothstep(0.62, 0.52, d);
		vec3 sc = mix(a * 0.82, a * 1.15, hash12(cell)) * (0.9 + 0.15 * vnoise(uv * 6.0));
		col = mix(b, sc, 0.35 + 0.65 * shingle);
		col *= 0.8 + 0.25 * f.y;
	} else if (pattern == 5 || pattern == 18) {
		// Metall (gebürstet, mit abgegriffenen Kanten)
		float br = vnoise(vec2(uv.x * 40.0, uv.y * 2.0));
		col = a * (0.85 + 0.2 * br) * (0.9 + 0.15 * n2);
		float wear = smoothstep(0.55, 0.85, n1) * edge_wear;
		col = mix(col, a * 1.4, wear);
		col = mix(col, b, smoothstep(0.7, 0.9, n2) * 0.35);
		metal = max(metal, 0.65);
		rough = min(rough, 0.45);
		if (pattern == 18) {
			col *= vec3(1.08, 0.95, 0.65);
		}
	} else if (pattern == 6) {
		// Stoff (Webmuster + Falten)
		float wx = sin(uv.x * 120.0) * sin(uv.y * 120.0);
		float folds = fbm2(vec2(uv.x * 2.0, uv.y * 0.6));
		col = a * (0.84 + 0.28 * folds) * (0.985 + 0.015 * wx);
		col = mix(col, b, smoothstep(0.7, 0.95, folds) * 0.3);
	} else if (pattern == 7) {
		// Leder (Falten, Nähte)
		float cr = fbm2(uv * 6.0);
		col = mix(b, a, 0.55 + 0.45 * cr) * (0.9 + 0.12 * n1);
		float stitch = step(0.5, fract(uv.x * 10.0)) * smoothstep(0.02, 0.0, abs(fract(uv.y * 2.0) - 0.5) - 0.012);
		col = mix(col, a * 1.35, stitch * 0.6);
		rough = 0.7;
	} else if (pattern == 8) {
		// Rinde
		float ridge = vnoise(vec2(uv.x * 9.0, uv.y * 1.3)) * 0.7 + vnoise(vec2(uv.x * 23.0, uv.y * 3.0)) * 0.3;
		col = mix(b, a, smoothstep(0.25, 0.75, ridge));
		col *= 0.88 + 0.18 * n2;
	} else if (pattern == 9) {
		// Fels (Facetten)
		vec4 v = voronoi(uv * 1.4);
		float facet = hash12(v.zw);
		col = mix(b, a, 0.35 + 0.5 * facet) * (0.85 + 0.2 * fbm2(uv * 3.0));
		col *= mix(0.7, 1.0, smoothstep(0.0, 0.08, v.y));
		col = mix(col, a * 1.25, smoothstep(0.75, 0.95, n2) * 0.4);
	} else if (pattern == 10) {
		// Haut
		col = a * (0.96 + 0.06 * n2);
		col = mix(col, b, smoothstep(0.55, 0.9, vnoise3(opos * 6.0)) * 0.12);
		rough = 0.6;
	} else if (pattern == 11) {
		// Fell
		float strand = vnoise(vec2(uv.x * 55.0, uv.y * 6.0)) * 0.6 + vnoise(vec2(uv.x * 140.0, uv.y * 14.0)) * 0.4;
		col = mix(b, a, smoothstep(0.2, 0.8, strand)) * (0.85 + 0.25 * n2);
	} else if (pattern == 12) {
		// Kettenhemd
		vec2 g = uv * 26.0;
		g.x += mod(floor(g.y), 2.0) * 0.5;
		vec2 f = fract(g) - 0.5;
		float ring = smoothstep(0.42, 0.32, length(f)) * smoothstep(0.12, 0.2, length(f));
		col = mix(b * 0.5, a, ring) * (0.9 + 0.15 * n1);
		metal = 0.7;
		rough = 0.5;
	} else if (pattern == 13) {
		// Strohdach
		float straw = vnoise(vec2(uv.x * 30.0, uv.y * 2.5)) * 0.7 + vnoise(vec2(uv.x * 80.0, uv.y * 6.0)) * 0.3;
		col = mix(b, a, straw) * (0.85 + 0.2 * n2);
		col *= 0.8 + 0.2 * smoothstep(0.0, 0.3, fract(uv.y * 2.2));
	} else if (pattern == 14) {
		// Steinplatten
		vec4 v = voronoi(uv * 1.6);
		col = mix(a * 0.8, a * 1.1, hash12(v.zw)) * (0.9 + 0.15 * vnoise(uv * 5.0));
		col = mix(b, col, smoothstep(0.02, 0.09, v.y));
	} else if (pattern == 15) {
		// Eis / Kristall
		float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.5);
		col = mix(b, a, 0.4 + 0.6 * n2) + fres * 0.35;
		rough = 0.12;
		emis = a * 0.15 * (0.5 + n1);
	} else if (pattern == 16) {
		// Knochen
		col = a * (0.86 + 0.18 * n2);
		col = mix(col, b, smoothstep(0.6, 0.95, fbm3(opos * 5.0)) * 0.45);
		rough = 0.65;
	} else if (pattern == 17) {
		// Lavagestein mit glühenden Rissen
		vec4 v = voronoi(uv * 1.2);
		col = mix(b, a, hash12(v.zw) * 0.5 + 0.25) * (0.8 + 0.3 * n1);
		float crack = smoothstep(0.07, 0.0, v.y);
		emis = emission_color.rgb * crack * (0.6 + 0.4 * sin(TIME * 1.5 + hash12(v.zw) * 6.0));
	} else if (pattern == 19) {
		// Schuppen
		vec2 g = uv * 7.0;
		g.x += mod(floor(g.y), 2.0) * 0.5;
		vec2 f = fract(g) - vec2(0.5, 0.0);
		float sc = smoothstep(0.75, 0.55, length(vec2(f.x, f.y - 0.1) * vec2(1.0, 1.2)));
		col = mix(b, a, 0.3 + 0.7 * sc) * (0.85 + 0.2 * n2);
		col *= 0.75 + 0.3 * f.y;
		rough = 0.5;
	} else {
		col = a * (1.0 - noise_amount * 0.12 + noise_amount * 0.2 * n2);
	}

	ALBEDO = col;
	ROUGHNESS = rough;
	METALLIC = metal;
	SPECULAR = 0.4;
	RIM = rim_amount;
	RIM_TINT = rim_tint_value;
	EMISSION = emis + emission_color.rgb * emission_energy * float(pattern != 17);
}
