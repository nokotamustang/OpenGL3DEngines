#version 460 core

layout (location = 0) in vec3 in_texcoord_0;
layout (location = 1) in vec3 in_position;

out vec2 uv_0;
out vec3 fragPos;
out float colorVariation;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform mat4 m_model;

float random(vec2 st);
float noise(in vec2 st);
float fbm(in vec2 _st);

void main() {
    uv_0 = in_texcoord_0.xy;
    fragPos = vec3(m_model * vec4(in_position, 1.0));
    colorVariation = fbm(in_position.xz);
    gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
}

float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float noise(in vec2 st) {
    const vec2 i = floor(st);
    const vec2 f = fract(st);
	// Four corners in 2D of a tile
    const float a = random(i);
    const float b = random(i + vec2(1.0, 0.0));
    const float c = random(i + vec2(0.0, 1.0));
    const float d = random(i + vec2(1.0, 1.0));
	// Smooth Interpolation
    const vec2 u = smoothstep(0., 1., f);
	// Mix 4 percentages
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

const vec2 fbm_shift = vec2(100.0);
const mat2 fbm_rot = mat2(cos(0.5), sin(0.5), -sin(0.5), cos(0.50));
const int num_octaves = 3;
float fbm(in vec2 _st) {
	// Craete variation with Fractal Brownian Motion, which we use to vary the color of the grass
	// Returns a value between 0 and 1
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < num_octaves; ++i) {
        v += a * noise(_st);
        _st = fbm_rot * _st * 2.0 + fbm_shift;
        a *= 0.5;
    }
    return v;
}