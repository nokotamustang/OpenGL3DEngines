#version 460 core

layout (points) in;
layout (triangle_strip, max_vertices = 36) out;

out GS_OUT {
	vec2 textCoord;
	float colorVariation;
	vec3 normal;
	vec3 fragPos;
	// vec4 shadow_coord;
} gs_out;

uniform mat4 m_proj;
uniform mat4 m_view;
// uniform mat4 m_view_light;
uniform vec3 camPos;
uniform sampler2D u_wind;
uniform float u_time;

// Because of GL texture uv coordinates, be aware that:
// 0,0 is the first tile in the atlas and is the bottom left tile
// 3,0 is the fourth tile in the atlas and it the bottom right tile
// 3,3 is the last tile in the atlas and it the top right tile
uniform vec2 u_current_tile = vec2(0.0, 0.0);
const float n_tiles = 4.0;
const float n_tile_shift = 1.0 / n_tiles;

const float c_min_size = 0.4;
const float LOD1 = 50.0;
const float LOD2 = 100.0;
const float LOD3 = 400.0; // Basically, no render at this distance
const float PI = 3.141592653589793;
const float q_PI = PI * 0.25;
const float qq_PI = q_PI * 0.5;
// const float tiny = 0.05;

const mat4 modelWindApply = mat4(1.0);
const vec2 windDirection = vec2(1.0, 1.0);
const float windStrength = 0.15;
const float grass_scale = 2.0;

// Variables set by main in this shader
float grass_size;
float dist_length;
float lod2_dist = 1.0;
float lod3_dist = 1.0;

// Constants
const vec4 v_pos_1 = vec4(-0.25, 0.0, 0.0, 0.0);
const vec4 v_pos_2 = vec4(0.25, 0.0, 0.0, 0.0);
const vec4 v_pos_3 = vec4(-0.25, 0.5, 0.0, 0.0);
const vec4 v_pos_4 = vec4(0.25, 0.5, 0.0, 0.0);
const vec2 t_coord_1 = vec2(0.0, 0.0);
const vec2 t_coord_2 = vec2(1.0, 0.0);
const vec2 t_coord_3 = vec2(0.0, 1.0);
const vec2 t_coord_4 = vec2(1.0, 1.0);
const mat4 model0 = mat4(1.0);
const float rot_45 = radians(45);
const mat4 model45 = mat4(cos(rot_45), 0, sin(rot_45), 0, 0, 1.0, 0, 0, -sin(rot_45), 0, cos(rot_45), 0, 0, 0, 0, 1);
const mat4 modelm45 = mat4(cos(-rot_45), 0, sin(-rot_45), 0, 0, 1.0, 0, 0, -sin(-rot_45), 0, cos(-rot_45), 0, 0, 0, 0, 1);
const float rot_90 = radians(90);
const mat4 model90 = mat4(cos(rot_90), 0, sin(rot_90), 0, 0, 1.0, 0, 0, -sin(rot_90), 0, cos(rot_90), 0, 0, 0, 0, 1);
// const mat4 m_shadow_bias = mat4(0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.5, 0.5, 0.5, 1.0);

// Functions
mat4 rotationX(in float angle);
mat4 rotationY(in float angle);
mat4 rotationZ(in float angle);
float random(vec2 st);
float noise(in vec2 st);
float fbm(in vec2 _st);

void emitGrassVertex(vec4 in_pos, mat4 wind_mat, mat4 rot_mat, vec4 vertexPosition, vec2 textCoords) {
	gl_Position = m_proj * m_view * (in_pos + wind_mat * rot_mat * (vertexPosition * grass_size));
	// gs_out.textCoord = textCoords;

	// The textCoords is given for each vertex from 0,0 to 1,1
	// but now the texture is an atlas, so we need to offset the texture coordinates
	gs_out.textCoord = vec2((textCoords.x / n_tiles) + (u_current_tile.x * n_tile_shift), (textCoords.y / n_tiles) + (u_current_tile.y * n_tile_shift));

	gs_out.fragPos = vec3((in_pos + wind_mat * rot_mat * (vertexPosition * grass_size)));
	gs_out.normal = vec3(wind_mat * rot_mat * vec4(0.0, 1.0, 0.0, 0.0));
	gs_out.colorVariation = fbm(in_pos.xz);
	// gs_out.shadow_coord = m_shadow_bias * m_proj * m_view_light * in_pos;
	// gs_out.shadow_coord.z -= tiny;
	EmitVertex();
}

void createQuad(vec3 base_position, mat4 y_rot, mat4 cam_rot) {
	const vec4 in_pos = gl_in[0].gl_Position;

    // Diminish the wind based on LOD levels
	const float wind_scale = 0.6 + (lod2_dist * 0.25) + (lod3_dist * 0.15);
	// Wind calculation using the flow map texture and time
	vec2 uv = (base_position.xz * 0.1) + windDirection * windStrength * u_time * wind_scale;
	uv.x = mod(uv.x, 1.0);
	uv.y = mod(uv.y, 1.0);
	const vec4 wind = texture(u_wind, uv);
	const mat4 wind_mat = (rotationX(wind.x * PI * 0.75 - PI * 0.25) * rotationZ(wind.y * PI * 0.75 - PI * 0.25));

	mat4 rot_mat = cam_rot * y_rot; 
	// Some additional random rotation on Y
	rot_mat *= rotationY(random(base_position.zx) * q_PI - qq_PI); 

	// Billboard creation with 4 vertices
	emitGrassVertex(in_pos, modelWindApply, rot_mat, v_pos_1, t_coord_1);
	emitGrassVertex(in_pos, modelWindApply, rot_mat, v_pos_2, t_coord_2);
	emitGrassVertex(in_pos, wind_mat, rot_mat, v_pos_3, t_coord_3);
	emitGrassVertex(in_pos, modelWindApply, rot_mat, v_pos_4, t_coord_4);
	EndPrimitive();
	// gs_out.shadow_coord = m_shadow_bias * m_proj * m_view_light * m_model * in_pos;
	// gs_out.shadow_coord.z -= tiny;
}

void createGrass(int numberQuads) {
	// Create a rotation matrix to make the billboards face the camPos
	mat4 cam_rot = mat4(1.0);
	cam_rot[0][0] = m_view[0][0];
	cam_rot[0][2] = m_view[2][0];
	cam_rot[2][0] = m_view[0][2];
	cam_rot[2][2] = m_view[2][2];

	if (numberQuads == 1) {
		createQuad(gl_in[0].gl_Position.xyz, model0, cam_rot);
	} else if (numberQuads == 2) {
		createQuad(gl_in[0].gl_Position.xyz, model45, cam_rot);
		createQuad(gl_in[0].gl_Position.xyz, modelm45, cam_rot);
	} else if (numberQuads == 3) {
		createQuad(gl_in[0].gl_Position.xyz, model0, cam_rot);
		createQuad(gl_in[0].gl_Position.xyz, model45, cam_rot);
		createQuad(gl_in[0].gl_Position.xyz, modelm45, cam_rot);
	}
}

void main() {
	// Distance of position to camera
	const vec3 in_pos = gl_in[0].gl_Position.xyz;
	dist_length = length(in_pos - camPos);
	grass_size = random(in_pos.xz) * grass_scale * (1.0 - c_min_size) + c_min_size;
	float t = 6.0;
	if (dist_length > LOD1) {
		t *= 1.5;
	}
	dist_length += (random(in_pos.xz) * t - t / 2.0);
	if (dist_length > LOD3) {
		return;
	}
	int detail_level = 3;
	if (dist_length > LOD1) {
		detail_level = 2;
		lod2_dist = 0.0;
	}
	if (dist_length > LOD2) {
		detail_level = 1;
		lod3_dist = 0.0;
	}

	if ((detail_level == 1) && ((int(in_pos.x * 10) % 1) == 0 || (int(in_pos.z * 10) % 1) == 0)) {
		createGrass(detail_level);
	} else if ((detail_level == 2) && ((int(in_pos.x * 5) % 1) == 0 || (int(in_pos.z * 5) % 1) == 0)) {
		createGrass(detail_level);
	} else if (detail_level != 1 && detail_level != 2) {
		createGrass(detail_level);
	}
}

mat4 rotationX(in float angle) {
	return mat4(1.0, 0, 0, 0, 0, cos(angle), -sin(angle), 0, 0, sin(angle), cos(angle), 0, 0, 0, 0, 1);
}

mat4 rotationY(in float angle) {
	return mat4(cos(angle), 0, sin(angle), 0, 0, 1.0, 0, 0, -sin(angle), 0, cos(angle), 0, 0, 0, 0, 1);
}

mat4 rotationZ(in float angle) {
	return mat4(cos(angle), -sin(angle), 0, 0, sin(angle), cos(angle), 0, 0, 0, 0, 1, 0, 0, 0, 0, 1);
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