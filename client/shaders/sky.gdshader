shader_type sky;
render_mode use_half_res_pass;

#include "res://shaders/noise.gdshaderinc"

uniform vec3 top_color : source_color = vec3(0.24, 0.48, 0.82);
uniform vec3 horizon_color : source_color = vec3(0.78, 0.86, 0.92);
uniform vec3 ground_color : source_color = vec3(0.36, 0.40, 0.38);
uniform vec3 sun_color : source_color = vec3(1.0, 0.92, 0.75);
uniform vec3 cloud_light : source_color = vec3(1.0, 0.98, 0.95);
uniform vec3 cloud_dark : source_color = vec3(0.62, 0.68, 0.80);
uniform float cloud_cover = 0.5;
uniform float cloud_speed = 0.006;
uniform float night = 0.0;
uniform float sun_size = 0.03;

void sky() {
	vec3 dir = EYEDIR;
	float h = dir.y;
	vec3 col;
	if (h > 0.0) {
		col = mix(horizon_color, top_color, pow(clamp(h, 0.0, 1.0), 0.55));
	} else {
		col = mix(horizon_color, ground_color, clamp(-h * 4.0, 0.0, 1.0));
	}
	// Sonne und Halo
	vec3 sd = normalize(LIGHT0_DIRECTION);
	float sdot = max(dot(dir, sd), 0.0);
	if (LIGHT0_ENABLED) {
		col += sun_color * pow(sdot, 12.0) * 0.35 * (1.0 - night);
		col += sun_color * pow(sdot, 220.0) * 0.6;
		col = mix(col, sun_color * 3.0, smoothstep(1.0 - sun_size * 0.02, 1.0 - sun_size * 0.012, sdot));
	}
	// Gemalte Wolken
	if (h > 0.0 && !AT_CUBEMAP_PASS) {
		vec2 uv = dir.xz / (h + 0.12) * 0.8;
		uv += TIME * cloud_speed * vec2(1.0, 0.4);
		float c = fbm2(uv * 1.3);
		c = c * 0.7 + fbm2(uv * 3.1 + 5.0) * 0.3;
		float cov = smoothstep(1.0 - cloud_cover, 1.0 - cloud_cover + 0.28, c);
		float shade = smoothstep(0.2, 0.9, fbm2(uv * 2.2 - 2.0));
		vec3 cc = mix(cloud_dark, cloud_light, shade);
		cc += sun_color * pow(sdot, 6.0) * 0.25;
		cc = mix(cc, cc * vec3(0.25, 0.28, 0.4), night);
		float fade = smoothstep(0.0, 0.18, h);
		col = mix(col, cc, cov * fade * 0.92);
	} else if (h > 0.0) {
		float c = fbm2(dir.xz / (h + 0.12) * 1.04);
		col = mix(col, mix(cloud_dark, cloud_light, 0.6), smoothstep(1.0 - cloud_cover, 1.0 - cloud_cover + 0.3, c) * 0.6 * smoothstep(0.0, 0.2, h));
	}
	// Sterne
	if (night > 0.01 && h > 0.0) {
		vec2 suv = dir.xz / (h + 0.3) * 60.0;
		float s = step(0.985, hash12(floor(suv))) * (0.5 + 0.5 * sin(TIME * 2.0 + hash12(floor(suv) + 3.0) * 10.0));
		col += vec3(s) * night * smoothstep(0.05, 0.3, h);
	}
	COLOR = col;
}
