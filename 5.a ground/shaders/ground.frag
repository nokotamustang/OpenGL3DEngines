#version 460 core

layout (location = 0) out vec4 fragColor;

in vec2 uv_0;
in vec3 fragPos;
in float colorVariation;

struct Light {
  vec3 position;
  vec3 color;
};

uniform Light light;
uniform sampler2D u_texture_0;

const vec3 gamma = vec3(2.2);
const vec3 i_gamma = vec3(1 / 2.2);

vec3 getLight(vec3 color) {
  vec3 ambient = light.color;
  return color * ambient;
}

void main() {
  vec4 color = texture(u_texture_0, uv_0);
  color.rgb = pow(color.rgb, gamma);
  color.rgb = getLight(color.rgb);
  color.rgb = mix(color.rgb, 0.5 * color.rgb, colorVariation);
  color.rgb = pow(color.rgb, i_gamma);
  fragColor = vec4(color.rgb, 1.0);
}