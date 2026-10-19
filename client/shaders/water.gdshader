shader_type spatial;
render_mode blend_mix, depth_draw_always, cull_back, diffuse_burley, specular_schlick_ggx;

#include "res://shaders/noise.gdshaderinc"

uniform vec3 shallow : source_color = vec3(0.20, 0.62, 0.66);
uniform vec3 deep : source_color = vec3(0.04, 0.20, 0.34);
uniform vec3 foam : source_color = vec3(0.92, 0.97, 1.0);
uniform float depth_scale = 2.2;
uniform float wave_amp = 0.06;
uniform float is_lava = 0.0;
uniform vec3 lava_hot : source_color = vec3(1.0, 0.55, 0.1);
uniform vec3 lava_cool : source_color = vec3(0.25, 0.04, 0.02);
uniform sampler2D depth_tex : hint_depth_texture, filter_linear_mipmap;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;

varying vec3 wpos;

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t = TIME;
	VERTEX.y += (sin(w.x * 0.35 + t * 1.1) + sin(w.z * 0.42 + t * 0.9)) * wave_amp * (1.0 - is_lava * 0.7);
	wpos = w;
}

void fragment() {
	vec2 p = wpos.xz;
	float t = TIME * (1.0 - is_lava * 0.85);
	float depth_raw = texture(depth_tex, SCREEN_UV).r;
	vec4 ndc = vec4(SCREEN_UV * 2.0 - 1.0, depth_raw, 1.0);
	vec4 view = INV_PROJECTION_MATRIX * ndc;
	view.xyz /= view.w;
	float scene_depth = -view.z;
	float water_depth = clamp((scene_depth - (-VERTEX.z)) / depth_scale, 0.0, 1.0);

	float n1 = fbm2(p * 0.25 + vec2(t * 0.05, t * 0.03));
	float n2 = fbm2(p * 0.6 - vec2(t * 0.07, -t * 0.04));
	vec3 nrm = normalize(vec3((n1 - 0.5) * 0.6, 1.0, (n2 - 0.5) * 0.6));
	NORMAL = normalize((VIEW_MATRIX * vec4(nrm, 0.0)).xyz);

	if (is_lava > 0.5) {
		vec4 v = voronoi(p * 0.35 + vec2(t * 0.02));
		float crust = smoothstep(0.0, 0.25, v.y);
		float pulse = 0.6 + 0.4 * sin(TIME * 1.3 + hash12(v.zw) * 6.0);
		vec3 hot = lava_hot * (1.2 + n1 * 0.6) * pulse;
		ALBEDO = mix(hot * 0.3, lava_cool, crust);
		EMISSION = hot * (1.0 - crust) * 2.2 + lava_hot * 0.25;
		ROUGHNESS = 0.8;
		ALPHA = 1.0;
	} else {
		vec3 col = mix(shallow, deep, smoothstep(0.0, 1.0, water_depth));
		float shore_foam = smoothstep(0.18, 0.0, water_depth) * (0.6 + 0.4 * sin(t * 2.0 + n1 * 12.0));
		float caustic = smoothstep(0.55, 0.85, vnoise(p * 1.4 + vec2(t * 0.3, t * 0.2)));
		col += caustic * 0.04;
		col = mix(col, foam, clamp(shore_foam, 0.0, 1.0) * 0.75);
		vec3 refr = texture(screen_tex, SCREEN_UV + (vec2(n1, n2) - 0.5) * 0.02).rgb;
		col = mix(refr * shallow * 1.4, col, smoothstep(0.0, 0.45, water_depth) * 0.8 + 0.2);
		ALBEDO = col;
		ROUGHNESS = 0.06;
		METALLIC = 0.0;
		SPECULAR = 0.6;
		ALPHA = 1.0;
	}
}
