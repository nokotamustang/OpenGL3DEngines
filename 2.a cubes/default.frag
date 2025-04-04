#version 460 core

layout (location = 0) out vec4 fragColor;

in vec2 uv_0;
in vec3 normal;
in vec3 fragPos;

struct Light {
  vec3 position;
  vec3 color;
  float strength;
};

struct Material {
  vec3 Ka;
  vec3 Kd;
  vec3 Ks;
  float Kao;
};

// uniform vec3 camPos;
uniform Light lights[99];
uniform float num_lights;
uniform Material material;
uniform sampler2D u_texture_0;

const vec3 gamma = vec3(2.2);
const vec3 i_gamma = vec3(1 / 2.2);

vec3 calculateLight(vec3 N, Light light) {
  // Radience
  float distance = length(light.position - fragPos);
  // float attenuation = 1.0;
  float attenuation = light.strength / (distance * distance);
  vec3 radiance = light.color * attenuation;

  // Ambient
  vec3 ambient = material.Ka;

  // Diffuse
  vec3 lightDir = normalize(light.position - fragPos);
  float diff = max(dot(N, lightDir), 0.0);
  vec3 diffuse = material.Kd * diff;

  // Specular
  vec3 viewDir = normalize(-fragPos);
  vec3 reflectDir = reflect(-lightDir, N);
  float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
  vec3 specular = material.Ks * spec;
  return (ambient + diffuse + specular) * radiance * light.strength;
}

vec3 getLight(vec3 tex_color) {
  vec3 N = normalize(normal);
  // vec3 V = normalize(camPos - fragPos);
  vec3 ambient = vec3(0.03) * material.Ka * material.Kao;

  vec3 Lo = vec3(0.0);
  for (int i = 0; i < num_lights; i++) {
    Lo += calculateLight(N, lights[i]);
  }

  vec3 light_color = mix(ambient, Lo, 0.5);
  light_color = light_color / (light_color + vec3(1.0));

  // return tex_color * light_color;
  return mix(tex_color, tex_color * light_color, 0.5);
}

void main() {
  vec3 color = texture(u_texture_0, uv_0).rgb;
  color = pow(color, gamma);
  color = getLight(color);
  color = pow(color, i_gamma);
  fragColor = vec4(color, 1.0);
}