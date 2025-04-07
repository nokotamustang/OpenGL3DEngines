#version 460 core

layout (location = 0) out vec4 fragColor;

in vec3 normal;
in vec3 fragPos;

struct Light {
  vec3 position;
  vec3 Ia;
  vec3 Id;
  vec3 Is;
};

struct Material {
  vec3 Ka;
  // vec3 Kd;
  // vec3 Ks;
  // float shininess;
};

uniform Light light;
uniform Material material;

vec3 getLight(vec3 color) {
  vec3 Normal = normalize(normal);

  // Ambient
  vec3 ambient = light.Ia;

  // Diffuse
  vec3 lightDir = normalize(light.position - fragPos);
  float diff = max(dot(Normal, lightDir), 0.0);
  vec3 diffuse = light.Id * diff;

  // Specular
  vec3 viewDir = normalize(-fragPos);
  vec3 reflectDir = reflect(-lightDir, Normal);
  float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
  vec3 specular = light.Is * spec;

  return color * (ambient + diffuse + specular);
}

void main() {
  vec3 color = material.Ka;
  color = getLight(color);
  fragColor = vec4(color, 1.0);
}