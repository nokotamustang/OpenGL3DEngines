import math
import glm
import moderngl
import numpy
import pygame


def generate_vertex_data(vertices, indices):
    data = [vertices[ind] for triangle in indices for ind in triangle]
    return numpy.array(data, dtype='f4')


class Terrain:
    def __init__(self, app, position=(0, 0, 0), width=128, depth=128, max_height=100,
                 height_map_path="height_map", rounding_factor=5):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))

        height_map, height_map_w, height_map_d = self.load_height_image(height_map_path)

        # Temporary limit for terrain size
        if width != height_map_w and width <= height_map_w:
            height_map_w = width
        if depth != height_map_d and depth <= height_map_d:
            height_map_d = depth
        half_width = math.floor(height_map_w / 2)
        half_depth = math.floor(height_map_d / 2)

        # Get value at 0,0 i.e. half_width, half_depth; use this to place the terrain under the camera
        centre_height = round(height_map[half_depth][half_width][0] / 255 * max_height, rounding_factor) + 1

        self.vertices = self.get_vertices(height_map_w, height_map_d, max_height, centre_height, height_map, half_width, half_depth, rounding_factor)
        self.indices = self.get_indices(self.vertices)
        self.vertex_data = self.generate_vertex_data(self.vertices, self.indices)

    def load_height_image(self, height_map_path):
        return self.app.texture.get_image_data(f'{self.app.base_path}/{self.app.texture_path}/{height_map_path}.png')

    def get_vertices(self, height_map_w: int, height_map_d: int, max_height: int, centre_height: int,
                     height_map: list, half_width: int, half_depth: int, rounding_factor=5):
        vertices = []
        for z in range(1, height_map_d):
            for x in range(1, height_map_w):
                y1 = round(height_map[z][x-1][0] / 255 * max_height - centre_height, rounding_factor)
                y2 = round(height_map[z][x][0] / 255 * max_height - centre_height, rounding_factor)
                y3 = round(height_map[z-1][x][0] / 255 * max_height - centre_height, rounding_factor)
                y4 = round(height_map[z-1][x-1][0] / 255 * max_height - centre_height, rounding_factor)
                vertices.append((x-0.5-half_width, y1, z+0.5-half_depth))
                vertices.append((x+0.5-half_width, y2, z+0.5-half_depth))
                vertices.append((x+0.5-half_width, y3, z-0.5-half_depth))
                vertices.append((x-0.5-half_width, y4, z-0.5-half_depth))
        return vertices

    def get_indices(self, vertices: list):
        indices = []
        for i in range(0, len(vertices) - 1, 4):
            indices.append((i, i + 2, i + 3))
            indices.append((i, i + 1, i + 2))
        return indices

    def generate_vertex_data(self, vertices, indices):
        vertex_data = generate_vertex_data(vertices, indices)
        texture_coords = []
        texture_indices = []
        for _ in range(0, len(vertices) - 1, 4):
            texture_coords.extend(self.app.texture.random_quad())
            texture_indices.append((0, 2, 3))
            texture_indices.append((0, 1, 2))
        texture_coord_data = generate_vertex_data(texture_coords, texture_indices)
        vertex_data = numpy.hstack([texture_coord_data, vertex_data])
        return numpy.array(vertex_data, dtype='f4')


class Ground():
    def __init__(self, app, position=(0, 0, 0), texture: str = 'dirt', terrain: Terrain = None, shader_name='ground'):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.terrain = terrain
        self.vbo = self.get_vbo()
        self.shader_program = self.get_shader_program(shader_name)
        self.vao = self.get_vao()
        self.tex_id = app.texture.get_alpha_texture(path=f'textures/{texture}.png')
        self.on_init()

    def on_init(self):
        # Texture
        self.shader_program['u_texture_0'] = self.tex_id
        # Light
        self.shader_program['light.color'].value = self.app.light.color
        # Position
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.position)
        # self.shader_program['camPos'].write = self.app.camera.position
        # Set point size
        self.ctx.point_size = 4

    def update(self):
        self.shader_program['m_view'].write(self.app.camera.m_view)
        # self.shader_program['camPos'].write = self.app.camera.position

    def render(self):
        self.app.texture.textures[self.tex_id].use(location=self.tex_id)
        self.vao.render()
        # self.vao.render(moderngl.TRIANGLE_STRIP)

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def get_vao(self):
        vao = self.ctx.vertex_array(self.shader_program, [
            (self.vbo, '2f 3f', 'in_texcoord_0', 'in_position'),
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
