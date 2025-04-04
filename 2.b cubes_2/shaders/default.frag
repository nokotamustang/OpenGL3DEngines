#version 460 core

layout (location = 0) out vec4 fragColor;

in vec2 uv_0;
in vec3 normal;
in vec3 fragPos;
in vec4 shadow_coord;

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
uniform sampler2DShadow u_shadow_map;
uniform vec2 u_resolution;

const vec3 gamma = vec3(2.2);
const vec3 i_gamma = vec3(1 / 2.2);

float lookup(float ox, float oy) {
  vec2 pixelOffset = 1 / u_resolution;
  return textureProj(u_shadow_map, shadow_coord + vec4(ox * pixelOffset.x * shadow_coord.w, oy * pixelOffset.y * shadow_coord.w, 0.0, 0.0));
}

float getSoftShadowX4() {
  float shadow;
  float swidth = 1.5;  // shadow spread
  vec2 offset = mod(floor(gl_FragCoord.xy), 2.0) * swidth;
  shadow += lookup(-1.5 * swidth + offset.x, 1.5 * swidth - offset.y);
  shadow += lookup(-1.5 * swidth + offset.x, -0.5 * swidth - offset.y);
  shadow += lookup(0.5 * swidth + offset.x, 1.5 * swidth - offset.y);
  shadow += lookup(0.5 * swidth + offset.x, -0.5 * swidth - offset.y);
  return shadow / 4.0;
}

float getSoftShadowX8() {
  float shadow;
  float swidth = 1.0;
  float endp = swidth * 1.5;
  for (float y = -endp; y <= endp; y += swidth) {
    for (float x = -endp; x <= endp; x += swidth) {
      shadow += lookup(x, y);
    }
  }
  return shadow / 8.0;
}

float getSoftShadowX16() {
  float shadow;
  float swidth = 1.0;
  float endp = swidth * 1.5;
  for (float y = -endp; y <= endp; y += swidth) {
    for (float x = -endp; x <= endp; x += swidth) {
      shadow += lookup(x, y);
    }
  }
  return shadow / 16.0;
}

float getSoftShadowX64() {
  float shadow;
  float swidth = 0.6;
  float endp = swidth * 3.0 + swidth / 2.0;
  for (float y = -endp; y <= endp; y += swidth) {
    for (float x = -endp; x <= endp; x += swidth) {
      shadow += lookup(x, y);
    }
  }
  return shadow / 64;
}

float getShadow() {
  // Return 0 or 1 depending on the shadow map depth comparison, where 1 means the frag is in shadow
  float shadow = textureProj(u_shadow_map, shadow_coord);
  return shadow;
}

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

  // Shadow
  // float shadow = getShadow();

  // Shadow with 16 samples PCR lookup
  float shadow = getSoftShadowX16();
  // float shadow = getSoftShadowX64();
  // float shadow = getSoftShadowX4();
  // float shadow = getSoftShadowX8();

  vec3 light_color = mix(ambient, Lo * shadow, 0.5);
  light_color = light_color / (light_color + vec3(1.0));

  return mix(tex_color, tex_color * light_color, 0.5);
}

void main() {
  vec3 color = texture(u_texture_0, uv_0).rgb;
  color = pow(color, gamma);
  color = getLight(color);
  color = pow(color, i_gamma);
  fragColor = vec4(color, 1.0);
}