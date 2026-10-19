shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_lambert_wrap, specular_schlick_ggx;

#include "res://shaders/noise.gdshaderinc"

// Farbpalette der Zone (handgemalter Stil)
uniform vec3 grass_a : source_color = vec3(0.36, 0.55, 0.16);
uniform vec3 grass_b : source_color = vec3(0.22, 0.42, 0.12);
uniform vec3 grass_c : source_color = vec3(0.58, 0.60, 0.22);
uniform vec3 flower_a : source_color = vec3(0.95, 0.85, 0.35);
uniform vec3 flower_b : source_color = vec3(0.85, 0.45, 0.75);
uniform vec3 dirt : source_color = vec3(0.50, 0.38, 0.24);
uniform vec3 dirt_dark : source_color = vec3(0.33, 0.24, 0.15);
uniform vec3 rock : source_color = vec3(0.50, 0.47, 0.42);
uniform vec3 rock_dark : source_color = vec3(0.30, 0.28, 0.27);
uniform vec3 cobble : source_color = vec3(0.56, 0.54, 0.50);
uniform vec3 cobble_dark : source_color = vec3(0.30, 0.28, 0.26);
uniform vec3 farmland : source_color = vec3(0.36, 0.25, 0.15);
uniform vec3 sand : source_color = vec3(0.72, 0.64, 0.45);
uniform vec3 snow : source_color = vec3(0.90, 0.94, 1.0);
uniform vec3 accent : source_color = vec3(0.3, 0.8, 0.7);
uniform vec3 accent_glow : source_color = vec3(0.0, 0.0, 0.0);
uniform float snow_amount = 0.0;
uniform float snow_height = 9999.0;
uniform float water_level = -100.0;
uniform float flower_density = 1.0;
uniform float rock_slope = 0.36;
uniform float strata = 1.0;

varying vec3 wpos;
varying vec3 wnorm;

vec3 rock_color(vec3 p, vec3 n) {
	// geschichteter Fels mit Rissen (triplanar)
	vec3 w = triplanar_weights(n);
	float band = sin(p.y * 1.7 + fbm2(p.xz * 0.15) * 4.0) * 0.5 + 0.5;
	float nx = fbm2(p.zy * 0.35);
	float ny = fbm2(p.xz * 0.35);
	float nz = fbm2(p.xy * 0.35);
	float nn = nx * w.x + ny * w.y + nz * w.z;
	vec4 vx = voronoi(p.zy * 0.45);
	vec4 vz = voronoi(p.xy * 0.45);
	vec4 vy = voronoi(p.xz * 0.45);
	float edge = vx.y * w.x + vy.y * w.y + vz.y * w.z;
	vec3 c = mix(rock_dark, rock, smoothstep(0.25, 0.75, nn));
	c = mix(c, c * 1.12, band * strata * 0.35);
	c *= mix(0.62, 1.0, smoothstep(0.0, 0.08, edge));
	c += vec3(0.05) * smoothstep(0.3, 0.12, edge) * (1.0 - smoothstep(0.12, 0.0, edge));
	return c;
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnorm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 p = wpos.xz;
	float n_large = fbm2(p * 0.018);
	float n_mid = fbm2(p * 0.09 + 3.0);
	float n_small = vnoise(p * 0.85);
	float strokes = brush(p * 1.3, 0.6 + n_large * 1.2, 2.6);

	// --- Gras
	vec3 g = mix(grass_b, grass_a, smoothstep(0.32, 0.72, n_large));
	g = mix(g, grass_c, smoothstep(0.58, 0.85, n_mid) * 0.55);
	g *= 0.86 + 0.26 * strokes;
	g *= 0.94 + 0.12 * n_small;
	float clumps = vnoise(p * 0.35 + 11.0);
	g = mix(g, g * vec3(0.78, 0.88, 0.7), smoothstep(0.55, 0.9, clumps) * 0.55);
	g = mix(g, g * vec3(1.12, 1.08, 0.82), smoothstep(0.62, 0.95, vnoise(p * 0.22 - 5.0)) * 0.4);
	// Blumentupfer
	vec4 fv = voronoi(p * 1.9);
	float fl = smoothstep(0.16, 0.05, fv.x) * step(0.82, hash12(fv.zw)) * smoothstep(0.45, 0.65, n_mid) * flower_density;
	vec3 fcol = mix(flower_a, flower_b, step(0.5, hash12(fv.zw + 3.1)));
	g = mix(g, fcol, fl);

	// --- Sand am Ufer
	float shore = 1.0 - smoothstep(water_level + 0.15, water_level + 1.1 + n_mid * 0.6, wpos.y);
	vec3 col = mix(g, sand * (0.9 + 0.2 * n_small), shore);

	// --- Feldwege (Erde mit Kieseln und Fahrrinnen)
	float road = COLOR.r;
	road = smoothstep(0.08, 0.6, road + (n_mid - 0.5) * 0.35);
	vec3 d = mix(dirt_dark, dirt, 0.5 + 0.5 * strokes);
	vec4 pv = voronoi(p * 3.2);
	d = mix(d, d * 1.25, smoothstep(0.22, 0.1, pv.x) * step(0.6, hash12(pv.zw)));
	d *= 0.9 + 0.15 * n_small;
	col = mix(col, d, road);

	// --- Kopfsteinpflaster
	float cob = smoothstep(0.15, 0.55, COLOR.g + (n_small - 0.5) * 0.2);
	vec4 cv = voronoi(p * 2.4);
	float stone_tint = hash12(cv.zw);
	vec3 cs = cobble * (0.78 + 0.34 * stone_tint) * (0.9 + 0.12 * vnoise(p * 9.0));
	cs = mix(cs, cs * vec3(1.05, 0.98, 0.9), step(0.7, hash12(cv.zw + 4.0)) * 0.6);
	cs *= 0.85 + 0.15 * smoothstep(0.0, 0.25, cv.y);
	cs = mix(cobble_dark, cs, smoothstep(0.015, 0.06, cv.y));
	col = mix(col, cs, cob);

	// --- Ackerland mit Furchen
	float farm = smoothstep(0.2, 0.6, COLOR.b);
	float furrow = sin(p.x * 3.2 + vnoise(p * 0.3) * 1.5) * 0.5 + 0.5;
	vec3 fcolr = mix(farmland * 0.7, farmland * 1.15, furrow) * (0.9 + 0.2 * n_small);
	col = mix(col, fcolr, farm);

	// --- Akzentschicht der Zone (Moos, Eis, Lavakruste, Kristallsand)
	float acc = smoothstep(0.2, 0.7, COLOR.a);
	vec4 av = voronoi(p * 0.7);
	vec3 accc = accent * (0.75 + 0.45 * hash12(av.zw)) * (0.85 + 0.25 * n_small);
	float crack = smoothstep(0.06, 0.0, av.y);
	col = mix(col, accc, acc);

	// --- Fels an Hängen
	float slope = 1.0 - wnorm.y;
	float rw = smoothstep(rock_slope - 0.06, rock_slope + 0.06, slope + (n_mid - 0.5) * 0.14);
	if (rw > 0.002) {
		col = mix(col, rock_color(wpos, wnorm), rw);
	}

	// --- Schnee
	float sn = snow_amount * smoothstep(0.30, 0.18, slope + (n_mid - 0.5) * 0.25);
	sn = max(sn, smoothstep(snow_height, snow_height + 6.0, wpos.y + n_large * 6.0) * smoothstep(0.55, 0.3, slope));
	sn *= 1.0 - road * 0.65 * snow_amount;
	vec3 snc = snow * (0.9 + 0.1 * strokes) * (0.95 + 0.08 * n_small);
	snc = mix(snc, snc * vec3(0.82, 0.88, 1.0), smoothstep(0.4, 0.8, n_mid) * 0.5);
	col = mix(col, snc, clamp(sn, 0.0, 1.0));

	ALBEDO = col;
	ROUGHNESS = mix(0.95, 0.55, sn * 0.6 + shore * 0.3);
	SPECULAR = 0.25;
	EMISSION = accent_glow * acc * (0.4 + 0.6 * crack);
}
