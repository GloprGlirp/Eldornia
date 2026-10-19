shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_lambert_wrap, specular_disabled;

#include "res://shaders/noise.gdshaderinc"

uniform vec3 grass_a : source_color = vec3(0.36, 0.55, 0.16);
uniform vec3 grass_b : source_color = vec3(0.22, 0.42, 0.12);
uniform vec3 tip_color : source_color = vec3(0.75, 0.80, 0.35);
uniform float fade_start = 38.0;
uniform float fade_end = 55.0;
uniform float blades = 5.0;

varying vec3 wpos;
varying float tipf;

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float d = distance(w, CAMERA_POSITION_WORLD);
	float shrink = 1.0 - smoothstep(fade_start, fade_end, d);
	VERTEX.y *= shrink;
	float t = TIME * 1.8 + w.x * 0.3 + w.z * 0.25;
	float sway = UV.y * UV.y;
	VERTEX.x += sin(t) * 0.12 * sway;
	VERTEX.z += cos(t * 0.8) * 0.08 * sway;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	tipf = UV.y;
}

void fragment() {
	float x = UV.x * blades;
	float id = floor(x);
	float fx = fract(x) - 0.5;
	float h = 0.55 + 0.45 * hash12(vec2(id, 3.3));
	float width = 0.42 * (1.0 - UV.y / h);
	float bend = (hash12(vec2(id, 7.7)) - 0.5) * 0.5 * UV.y * UV.y;
	float blade = step(abs(fx - bend), width) * step(UV.y, h);
	vec2 p = wpos.xz;
	float n_large = fbm2(p * 0.018);
	vec3 base = mix(grass_b, grass_a, smoothstep(0.32, 0.72, n_large));
	vec3 col = mix(base * 0.82, mix(base * 1.08, tip_color, 0.22), smoothstep(0.0, 1.0, tipf / h));
	ALBEDO = col;
	ALPHA = blade;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	ROUGHNESS = 0.9;
	BACKLIGHT = col * 0.3;
}
