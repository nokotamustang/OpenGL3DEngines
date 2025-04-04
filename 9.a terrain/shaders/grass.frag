#version 460 core

layout (location = 0) out vec4 fragColor;

in GS_OUT {
  vec2 textCoord;
  float colorVariation;
  vec3 normal;
  vec3 fragPos;
  // vec4 shadow_coord;
} fs_in;

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
uniform Light global_light;
uniform float num_lights;
uniform Material material;
uniform sampler2D u_texture_0;
// uniform sampler2DShadow u_shadow_map;
// uniform vec2 u_resolution;

const vec3 gamma = vec3(2.2);
const vec3 i_gamma = vec3(1 / 2.2);

// float lookup(float ox, float oy) {
//   vec2 pixelOffset = 1 / u_resolution;
//   return textureProj(u_shadow_map, fs_in.shadow_coord + vec4(ox * pixelOffset.x * fs_in.shadow_coord.w, oy * pixelOffset.y * fs_in.shadow_coord.w, 0.0, 0.0));
// }

// float getSoftShadowX16() {
//   float shadow;
//   float swidth = 1.0;
//   float endp = swidth * 1.5;
//   for (float y = -endp; y <= endp; y += swidth) {
//     for (float x = -endp; x <= endp; x += swidth) {
//       shadow += lookup(x, y);
//     }
//   }
//   return shadow / 16.0;
// }

vec3 calculateLight(vec3 N, Light light) {
  // Radience
  float distance = length(light.position - fs_in.fragPos);
  // float attenuation = 1.0;
  float attenuation = light.strength / (distance * distance);
  vec3 radiance = light.color * attenuation;

  // Ambient
  vec3 ambient = material.Ka;

  // Diffuse
  vec3 lightDir = normalize(light.position - fs_in.fragPos);
  float diff = max(dot(N, lightDir), 0.0);
  vec3 diffuse = material.Kd * diff;

  // Specular
  vec3 viewDir = normalize(-fs_in.fragPos);
  vec3 reflectDir = reflect(-lightDir, N);
  float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
  vec3 specular = material.Ks * spec;
  return (ambient + diffuse + specular) * radiance * light.strength;
}

vec3 getLight() {
  vec3 N = normalize(fs_in.normal);
  // vec3 V = normalize(camPos - fragPos);
  vec3 ambient = vec3(0.03) * material.Ka * material.Kao;

  vec3 Lo = vec3(0.0);
  for (int i = 0; i < num_lights; i++) {
    Lo += calculateLight(N, lights[i]);
  }

  vec3 light_color = mix(ambient, Lo, 0.5);
  light_color = light_color / (light_color + vec3(1.0));
  return light_color;
}

vec3 calculateGlobalLight(vec3 N, Light light) {
  // Radience
  float distance = length(light.position - fs_in.fragPos);
  float attenuation = 1.0;
  vec3 radiance = light.color * attenuation;

  // Ambient
  vec3 ambient = material.Ka;

  // Diffuse
  vec3 lightDir = normalize(light.position - fs_in.fragPos);
  float diff = max(dot(N, lightDir), 0.0);
  vec3 diffuse = material.Kd * diff;

  // Specular
  vec3 viewDir = normalize(-fs_in.fragPos);
  vec3 reflectDir = reflect(-lightDir, N);
  float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
  vec3 specular = material.Ks * spec;
  return (ambient + diffuse + specular) * radiance * light.strength;
}

vec3 getGlobalLight() {
  vec3 N = normalize(fs_in.normal);
  vec3 ambient = vec3(0.03) * material.Ka * material.Kao; 
  // float shadow = getSoftShadowX4();
  vec3 Lo = calculateGlobalLight(N, global_light);
  vec3 light_color = mix(ambient, Lo, 0.5);
  light_color = light_color / (light_color + vec3(1.0));
  // return light_color * shadow;
  return light_color;
}

void main() {
  vec4 color = texture(u_texture_0, fs_in.textCoord);
  if (color.a < 0.75)
    discard;
  vec3 local_color = getLight();
  vec3 global_color = getGlobalLight();
  vec3 illumination = mix(global_color, local_color, 0.5);
  color.rgb = pow(color.rgb, gamma);
  color.rgb = mix(color.rgb, illumination, 0.5);
  color.xyz = mix(color.rgb, 0.5 * color.rgb, fs_in.colorVariation);
  color.rgb = pow(color.rgb, i_gamma);
  fragColor = vec4(color.rgb, 1.0);
}