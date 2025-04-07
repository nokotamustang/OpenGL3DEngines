#version 460 core

layout (location = 0) out vec4 fragColor;

in vec2 uv_0;
in vec3 normal;
in vec3 fragPos;
in vec4 shadow_coord;
in vec4 shadow_coord_2;

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
// uniform vec2 u_resolution;
uniform Light lights[99];
uniform float num_lights;
uniform Material material;
uniform sampler2D u_texture_0;
uniform sampler2DShadow u_shadow_map;
uniform sampler2DShadow u_shadow_map_2;
uniform float global_ambient;

const vec3 gamma = vec3(2.2);
const vec3 i_gamma = vec3(1 / 2.2);

// Return 0 or 1 depending on the shadow map depth comparison, where 0 means the frag is in shadow
float getShadow() {
  return textureProj(u_shadow_map, shadow_coord);
}
float getShadow2() {
  return textureProj(u_shadow_map_2, shadow_coord_2);
}

// float lookup(float ox, float oy) {
//   vec2 pixelOffset = 1 / u_resolution;
//   return textureProj(u_shadow_map, shadow_coord + vec4(ox * pixelOffset.x * shadow_coord.w, oy * pixelOffset.y * shadow_coord.w, 0.0, 0.0));
// }

// float getSoftShadowX4(float strength) {
//   float shadow;
//   float swidth = 1.5;
//   vec2 offset = mod(floor(gl_FragCoord.xy), 2.0) * swidth;
//   shadow += lookup(-1.5 * swidth + offset.x, 1.5 * swidth - offset.y);
//   shadow += lookup(-1.5 * swidth + offset.x, -0.5 * swidth - offset.y);
//   shadow += lookup(0.5 * swidth + offset.x, 1.5 * swidth - offset.y);
//   shadow += lookup(0.5 * swidth + offset.x, -0.5 * swidth - offset.y);
//   return (shadow * 0.25) * strength;
// }

// float getSoftShadowX8(float strength) {
//   float shadow;
//   float swidth = 1.0;
//   float endp = swidth * 1.5;
//   for (float y = -endp; y <= endp; y += swidth) {
//     for (float x = -endp; x <= endp; x += swidth) {
//       shadow += lookup(x, y);
//     }
//   }
//   return (shadow / 8.0) * strength;
// }

// float getSoftShadowX16(float strength) {
//   float shadow;
//   float swidth = 1.0;
//   float endp = swidth * 1.5;
//   for (float y = -endp; y <= endp; y += swidth) {
//     for (float x = -endp; x <= endp; x += swidth) {
//       shadow += lookup(x, y);
//     }
//   }
//   return (shadow / 16.0) * strength;
// }

// float getSoftShadowX64(float strength) {
//   float shadow = 0.0;
//   float swidth = 0.6;
//   float endp = swidth * 3.0 + swidth / 2.0;
//   for (float y = -endp; y <= endp; y += swidth) {
//     for (float x = -endp; x <= endp; x += swidth) {
//       shadow += lookup(x, y);
//     }
//   }
//   return (shadow / 64) * strength;
// }

vec3 calculateBlinnPhong(int index, vec3 N, Light light) {
  // Radiance
  float distance = length(light.position - fragPos);
  float strength = light.strength * 100.0;
  float attenuation = strength / (distance * distance); // or 1.0;
  if (index == 0) {
    attenuation = 1.0;
  }
  vec3 radiance = light.color * attenuation * strength;

  // Ambient
  vec3 ambient = material.Ka;

  // Diffuse (Lambertian)
  vec3 lightDir = normalize(light.position - fragPos);
  float diff = max(dot(N, lightDir), 0.0);
  vec3 diffuse = material.Kd * diff;

  // Specular
  vec3 viewDir = normalize(-fragPos);
  vec3 reflectDir = reflect(-lightDir, N);
  float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
  vec3 specular = material.Ks * spec;
  return (ambient + diffuse + specular) * radiance;
}

vec3 getLight(vec3 tex_color) {
  vec3 N = normalize(normal);
  // vec3 V = normalize(camPos - fragPos);
  vec3 ambient = vec3(0.01) * material.Ka * material.Kao;

  vec3 Lo = vec3(0.0);
  for (int i = 0; i < num_lights; i++) {
    Lo += calculateBlinnPhong(i, N, lights[i]);
  } 

  // Shadow
  float shadow = getShadow();
  if (shadow > 0.0) {
    float shadow_2 = getShadow2();
    if (shadow_2 == 0.0) {
      shadow = 0.0;
    }
  }

  // Mix the shadow back into the lighting, this allows local illumination to tint it
  Lo = mix(Lo, vec3(shadow), 0.9);

  vec3 light_color = mix(ambient, Lo, 0.5);
  light_color = light_color / (light_color + vec3(1.0));

  // Remove light to represent global ambient level
  light_color = light_color - (1.0 - global_ambient);

  return mix(tex_color, tex_color * light_color, 0.5);
}

void main() {
  vec3 color = texture(u_texture_0, uv_0).rgb;
  color = pow(color, gamma);
  color = getLight(color);
  color = pow(color, i_gamma);
  fragColor = vec4(color, 1.0);
}