import math
import glm
import moderngl
import numpy


def generate_vertex_data(vertices, indices):
    data = [vertices[ind] for triangle in indices for ind in triangle]
    return numpy.array(data, dtype='f4')


def delta_ab(a, b):
    return glm.vec3(b[0] - a[0], b[1] - a[1], b[2] - a[2])


def dot_product(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def angle_between_vectors(a, b):
    # unit_vector_of_ground = glm.vec3(0, 1, 0)
    return math.acos(dot_product(a, b))


def uniform_points_in_3d_triangle(p1, p2, p3, n):
    points = []
    for i in range(n):
        for j in range(n - i):
            k = n - i - j
            x = (i * p1[0] + j * p2[0] + k * p3[0]) / n
            y = (i * p1[1] + j * p2[1] + k * p3[1]) / n
            z = (i * p1[2] + j * p2[2] + k * p3[2]) / n
            points.append((x, y, z))
    return points


class Terrain:
    def __init__(self, app, position=(0, 0, 0), width=128, depth=128, max_height=100.0,
                 flora_steepness_degree_max=75, grass_step_size=15,
                 height_map_path="height_map", scale=1.0, rounding_factor=6):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.rounding_factor = rounding_factor
        self.max_height = max_height

        self.scale = scale
        self.half_scale: float = self.scale / 2
        self.height_map, self.height_map_w, self.height_map_d = self.load_height_image(height_map_path)

        # Temporary limit for terrain size
        if width != self.height_map_w and width <= self.height_map_w:
            self.height_map_w = width
        if depth != self. height_map_d and depth <= self.height_map_d:
            self.height_map_d = depth
        self.half_width = math.floor(self.height_map_w / 2 * self.scale)
        self.half_depth = math.floor(self.height_map_d / 2 * self.scale)

        # Flora
        self.grass_step_size = grass_step_size
        self.flora_steepness_max = flora_steepness_degree_max

        # Get value at 0,0 i.e. half_width, half_depth; use this to place the terrain under the camera
        self.base_height = self.lookup_height(self.half_width, self.half_depth) + 1
        self.vertices = self.get_vertices(self.height_map_w, self.height_map_d, self.max_height,
                                          self.base_height, self.height_map,
                                          self.half_width, self.half_depth, self.rounding_factor)
        self.vertex_data = self.generate_vertex_data(self.vertices, self.grass_step_size)

    def lookup_height(self, x, z):
        height = round(self.height_map[z][x][0] / 255 * self.max_height, self.rounding_factor)
        return height

    def load_height_image(self, height_map_path):
        return self.app.texture.get_image_data(f'{self.app.base_path}/{self.app.texture_path}/{height_map_path}.png')

    def get_vertices(self, height_map_w: int, height_map_d: int, max_h: float, offset_h: int,
                     height_map: list, half_width: int, half_depth: int, r_factor=5):
        vertices = []
        offset_w = half_width * self.scale
        offset_d = half_depth * self.scale
        for z in range(1, height_map_d):
            for x in range(1, height_map_w):
                y1 = round(height_map[z][x-1][0] / 255 * max_h - offset_h, r_factor)
                y2 = round(height_map[z][x][0] / 255 * max_h - offset_h, r_factor)
                y3 = round(height_map[z-1][x][0] / 255 * max_h - offset_h, r_factor)
                y4 = round(height_map[z-1][x-1][0] / 255 * max_h - offset_h, r_factor)
                x_pos = x * self.scale
                z_pos = z * self.scale
                vertices.append((x_pos-self.half_scale-offset_w, y1, z_pos+self.half_scale-offset_d))
                vertices.append((x_pos+self.half_scale-offset_w, y2, z_pos+self.half_scale-offset_d))
                vertices.append((x_pos+self.half_scale-offset_w, y3, z_pos-self.half_scale-offset_d))
                vertices.append((x_pos-self.half_scale-offset_w, y4, z_pos-self.half_scale-offset_d))
        return vertices

    def generate_vertex_data(self, vertices, grass_step_size=12):
        grass_vertices = []
        indices = []
        texture_coords = []
        texture_indices = []
        normals = []
        for i in range(0, len(vertices) - 1, 4):
            v1 = vertices[i]
            v2 = vertices[i + 1]
            v3 = vertices[i + 2]
            v4 = vertices[i + 3]
            indices.append((i, i + 2, i + 3))  # Triangle 1
            indices.append((i, i + 1, i + 2))  # Triangle 2
            texture_coords.extend(self.app.texture.random_quad())
            texture_indices.append((0, 2, 3))
            texture_indices.append((0, 1, 2))
            # Normals
            normal_1 = glm.normalize(glm.cross(delta_ab(v1, v3), delta_ab(v1, v4)))
            new_normals = [[normal_1] * 3]
            normal_2 = glm.normalize(glm.cross(delta_ab(v1, v2), delta_ab(v1, v3)))
            new_normals.extend([[normal_2] * 3])
            normals.append(new_normals)

            # Add grass blade points along each triangle
            # grass_vertices.append(uniform_points_in_3d_triangle(v1, v2, v3, grass_step_size))
            # grass_vertices.append(uniform_points_in_3d_triangle(v1, v3, v4, grass_step_size))

            # Add grass only if the triangle is not too steep
            if angle_between_vectors(normal_1, glm.vec3(0, 1, 0)) < math.radians(self.flora_steepness_max):
                grass_vertices.append(uniform_points_in_3d_triangle(v1, v2, v3, grass_step_size))
            if angle_between_vectors(normal_2, glm.vec3(0, 1, 0)) < math.radians(self.flora_steepness_max):
                grass_vertices.append(uniform_points_in_3d_triangle(v1, v3, v4, grass_step_size))

        self.vertices_mesh = numpy.array(grass_vertices, dtype='f4')

        # Pack vertex data
        texture_coord_data = generate_vertex_data(texture_coords, texture_indices)
        vertex_data = generate_vertex_data(vertices, indices)
        vertex_data = numpy.hstack([texture_coord_data, vertex_data])
        normals = numpy.array(normals, dtype='f4').reshape(int(len(normals * 6)), 3)
        vertex_data = numpy.hstack([vertex_data, normals])
        return numpy.array(vertex_data, dtype='f4')


class Ground():
    def __init__(self, app, position=(0, 0, 0), texture: str = 'dirt',
                 terrain: Terrain = None, shader_name='ground',
                 albedo=(1.0, 1.0, 1.0), diffuse=0.6, specular=0.3, ao: float = 1.0):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.albedo = 0.06 * glm.vec3(albedo)  # Ambient (Albedo)
        self.diffuse = diffuse * glm.vec3(albedo)  # Diffuse (Lambert)
        self.specular = specular * glm.vec3(albedo)  # Specular (Blinn-Phong)
        self.ao = ao
        self.terrain = terrain
        self.vbo = self.get_vbo()
        self.shader_program = self.get_shader_program(shader_name)
        self.vao = self.get_vao()
        self.tex_id = app.texture.get_alpha_texture(path=f'textures/{texture}.png')
        self.on_init()

    def on_init(self):
        # Texture
        self.shader_program['u_texture_0'] = self.tex_id
        # n lights
        self.shader_program['num_lights'].value = len(self.app.lights)
        # Send lights into uniform array of Light struct
        for i, light in enumerate(self.app.lights):
            self.shader_program[f'lights[{i}].position'].value = light.position
            self.shader_program[f'lights[{i}].color'].value = light.color
            self.shader_program[f'lights[{i}].strength'].value = light.strength
        # Global light
        # self.shader_program['global_light.position'].value = self.app.global_light.position
        self.shader_program['global_light.color'].value = self.app.global_light.color
        # self.shader_program['global_light.strength'].value = self.app.global_light.strength
        # Position
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.position)
        # Material: Albedo (rgb)
        self.shader_program['material.Ka'].value = self.albedo
        self.shader_program['material.Kd'].value = self.diffuse
        self.shader_program['material.Ks'].value = self.specular
        self.shader_program['material.Kao'].value = self.ao
        # self.shader_program['camPos'].write = self.app.camera.position
        # Set point size
        # self.ctx.point_size = 4

    def update(self):
        self.shader_program['m_view'].write(self.app.camera.m_view)
        # self.shader_program['camPos'].write = self.app.camera.position

    def render(self):
        self.app.texture.textures[self.tex_id].use(location=self.tex_id)
        self.vao.render(moderngl.TRIANGLES)
        # self.vao.render(moderngl.TRIANGLE_STRIP)

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def get_vao(self):
        vao = self.ctx.vertex_array(self.shader_program, [
            (self.vbo, '2f 3f 3f', 'in_texcoord_0', 'in_position', 'in_normal'),
        ])
        return vao

    def get_vbo(self):
        return self.ctx.buffer(self.terrain.vertex_data)

    def get_shader_program(self, shader_name='default'):
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.vert', 'r') as f:
            vertex_shader_source = f.read()
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.frag', 'r') as f:
            fragment_shader_source = f.read()
        shader_program = self.ctx.program(
            vertex_shader=vertex_shader_source,
            fragment_shader=fragment_shader_source
        )
        return shader_program

    def get_model_matrix(self):
        return glm.mat4()


class Grass:
    def __init__(self, app, position=(0, 0, 0), texture: str = 'grass',
                 terrain: Terrain = None, shader_name='flora',
                 albedo=(1.0, 1.0, 1.0), diffuse=0.3, specular=0.5, ao: float = 1.0):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.albedo = 0.06 * glm.vec3(albedo)
        self.diffuse = diffuse * glm.vec3(albedo)
        self.specular = specular * glm.vec3(albedo)
        self.ao = ao
        self.terrain = terrain
        self.vbo = self.get_vbo()
        self.shader_program = self.get_shader_program(shader_name)
        self.vao = self.get_vao()
        self.tex_id = app.texture.get_alpha_texture(path=f'textures/{texture}.png')
        self.tex_id_wind = app.texture.get_basic_texture(path=f'textures/flow_map.png')
        self.on_init()

    def on_init(self):
        # Variables
        self.shader_program['u_time'].value = self.app.time
        # Texture
        self.shader_program['u_wind'] = self.tex_id_wind
        self.shader_program['u_texture_0'] = self.tex_id
        # n lights
        self.shader_program['num_lights'].value = len(self.app.lights)
        # Send lights into uniform array of Light struct
        for i, light in enumerate(self.app.lights):
            self.shader_program[f'lights[{i}].position'].value = light.position
            self.shader_program[f'lights[{i}].color'].value = light.color
            self.shader_program[f'lights[{i}].strength'].value = light.strength
        # Global light
        # self.shader_program['global_light.position'].value = self.app.global_light.position
        self.shader_program['global_light.color'].value = self.app.global_light.color
        # self.shader_program['global_light.strength'].value = self.app.global_light.strength
        # Position
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.position)
        self.shader_program['camPos'].write = self.app.camera.position
        # Material: Albedo (rgb)
        self.shader_program['material.Ka'].value = self.albedo
        self.shader_program['material.Kd'].value = self.diffuse
        self.shader_program['material.Ks'].value = self.specular
        self.shader_program['material.Kao'].value = self.ao
        # Set point size
        self.ctx.point_size = 4

    def update(self):
        # m_model = glm.rotate(self.get_model_matrix(), self.app.time, glm.vec3(0, 1, 0))
        # self.shader_program['m_model'].write(m_model)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['u_time'].value = self.app.time
        self.shader_program['camPos'].write = self.app.camera.position

    def render(self):
        self.app.texture.textures[self.tex_id_wind].use(location=self.tex_id_wind)
        self.app.texture.textures[self.tex_id].use(location=self.tex_id)
        self.vao.render(moderngl.POINTS)

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def get_vao(self):
        vao = self.ctx.vertex_array(self.shader_program, [
            (self.vbo, '3f', 'in_position'),
        ])
        return vao

    def get_vbo(self):
        return self.ctx.buffer(self.terrain.vertices_mesh)

    def get_shader_program(self, shader_name='default'):
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.vert', 'r') as f:
            vertex_shader_source = f.read()
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.frag', 'r') as f:
            fragment_shader_source = f.read()
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.geom', 'r') as f:
            geometry_shader_source = f.read()
        shader_program = self.ctx.program(
            vertex_shader=vertex_shader_source,
            fragment_shader=fragment_shader_source,
            geometry_shader=geometry_shader_source
        )
        return shader_program

    def get_model_matrix(self):
        return glm.mat4()


class SkyBox():
    def __init__(self, app, texture_cube_name='skybox',
                 pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        self.app = app
        self.ctx = app.ctx
        self.pos = pos
        self.rot = glm.vec3([glm.radians(a) for a in rot])
        self.scale = scale
        self.m_model = self.get_model_matrix()
        self.tex_id = app.texture.get_texture_cube(path=f'textures/{texture_cube_name}')

        self.vbo = self.get_vbo()
        self.shader_program = self.get_shader_program()
        self.vao = self.get_vao()
        self.camera = self.app.camera
        self.on_init()

    def get_vertex_data(self):
        z = 0.9999
        vertices = [(-1, -1, z), (3, -1, z), (-1, 3, z)]
        vertex_data = numpy.array(vertices, dtype='f4')
        return vertex_data

    def get_vbo(self):
        vertex_data = self.get_vertex_data()
        vbo = self.ctx.buffer(vertex_data)
        return vbo

    def get_vao(self):
        vao = self.ctx.vertex_array(self.shader_program, [
            (self.vbo, '3f', 'in_position'),
        ])
        return vao

    def get_model_matrix(self):
        m_model = glm.mat4()
        # Translate
        m_model = glm.translate(m_model, self.pos)
        # Rotate
        m_model = glm.rotate(m_model, self.rot.z, glm.vec3(0, 0, 1))
        m_model = glm.rotate(m_model, self.rot.y, glm.vec3(0, 1, 0))
        m_model = glm.rotate(m_model, self.rot.x, glm.vec3(1, 0, 0))
        # Scale
        m_model = glm.scale(m_model, self.scale)
        return m_model

    def render(self):
        self.update()
        self.vao.render()

    def get_shader_program(self, shader_name='skybox'):
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.vert', 'r') as f:
            vertex_shader_source = f.read()
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.frag', 'r') as f:
            fragment_shader_source = f.read()
        shader_program = self.ctx.program(
            vertex_shader=vertex_shader_source,
            fragment_shader=fragment_shader_source
        )
        return shader_program

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def update(self):
        m_view = glm.mat4(glm.mat3(self.camera.m_view))
        self.shader_program['m_invProjView'].write(glm.inverse(self.camera.m_proj * m_view))

    def on_init(self):
        # Texture
        self.shader_program['u_texture_skybox'] = 0
        self.app.texture.textures[self.tex_id].use(location=0)
