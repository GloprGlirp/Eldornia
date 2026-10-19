shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_lambert_wrap, specular_disabled;

// Laubkronen im handgemalten Stil: dichte Blattwolken (Volumen) plus Blattkarten am Rand.
#include "res://shaders/noise.gdshaderinc"

uniform vec3 leaf_light : source_color = vec3(0.55, 0.72, 0.22);
uniform vec3 leaf_dark : source_color = vec3(0.12, 0.30, 0.10);
uniform vec3 leaf_tip : source_color = vec3(0.80, 0.85, 0.35);
uniform bool leaf_cards = false;
uniform float leaf_density = 7.0;
uniform float wind = 1.0;
uniform vec3 emission_tint : source_color = vec3(0.0);
uniform float tint_variation = 0.25;

varying vec3 wpos;
varying float ao;
varying float var;

void vertex() {
	vec3 world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float w = COLOR.g * wind;
	float t = TIME * 1.6 + INSTANCE_CUSTOM.g * 6.28 + world.x * 0.15 + world.z * 0.12;
	VERTEX.x += sin(t) * 0.08 * w + sin(t * 2.7 + VERTEX.y) * 0.03 * w;
	VERTEX.z += cos(t * 0.9) * 0.06 * w;
	VERTEX.y += sin(t * 1.9 + VERTEX.x * 2.0) * 0.025 * w;
	wpos = world;
	ao = COLOR.r;
	var = INSTANCE_CUSTOM.r;
}

void fragment() {
	vec3 n_world = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz;
	float up = n_world.y * 0.5 + 0.5;
	float n = fbm3(wpos * 1.6);
	float clusters = vnoise3(wpos * 4.5);
	float light = clamp(ao * 0.75 + up * 0.45 + (clusters - 0.5) * 0.35, 0.0, 1.0);
	vec3 col = mix(leaf_dark, leaf_light, smoothstep(0.15, 0.95, light));
	col = mix(col, leaf_tip, smoothstep(0.75, 1.0, light) * smoothstep(0.55, 0.8, n));
	// Farbvariation pro Baum
	col *= 1.0 + (var - 0.5) * tint_variation;
	col = mix(col, col * vec3(1.1, 0.95, 0.7), smoothstep(0.65, 1.0, var) * 0.4);
	float alpha = 1.0;
	if (leaf_cards) {
		vec2 uv = UV * leaf_density;
		vec4 v = voronoi(uv);
		float ang = hash12(v.zw) * 6.283;
		vec2 off = uv - (floor(uv) + 0.5);
		vec2 c = fract(uv) - 0.5;
		// Blattform: gestreckte Ellipse in Zufallsrichtung
		vec2 q = vec2(cos(ang) * c.x - sin(ang) * c.y, sin(ang) * c.x + cos(ang) * c.y);
		float leaf = 1.0 - smoothstep(0.32, 0.38, length(q * vec2(1.0, 1.9)));
		float edge_fade = smoothstep(0.5, 0.35, length(UV - 0.5));
		alpha = leaf * step(0.15, edge_fade + hash12(v.zw) * 0.5);
		col *= 0.85 + 0.3 * hash12(v.zw + 1.3);
		ALPHA_SCISSOR_THRESHOLD = 0.5;
	}
	ALBEDO = col;
	ALPHA = alpha;
	ROUGHNESS = 0.9;
	BACKLIGHT = col * 0.45;
	EMISSION = emission_tint * (0.4 + 0.6 * clusters);
}
