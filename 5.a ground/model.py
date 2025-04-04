import glm
import moderngl
import numpy


def generate_vertex_data(vertices, indices):
    data = [vertices[ind] for triangle in indices for ind in triangle]
    return numpy.array(data, dtype='f4')


class Terrain:
    def __init__(self, app, position=(0, 0, 0), width=128, step=1, curve=0.5):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))

        half_step = step / 2
        half_width = width / 2

        vertices = []
        # vertices = [(-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1)]  # Example single quad
        num_tiles = int(width / step)
        for z in range(0, num_tiles):
            for x in range(0, num_tiles):
                # Determine the vertices of the tile from counter-clockwise so bottom left is 0, bottom right is 1, top right is 2 and top left is 3
                # Assume x, y is the center of the tile, so use half_step to determine the corners
                # Also, subtract half_width to center the terrain in the world
                y1 = 0.5 * numpy.sin(curve * (x-half_step)) + 0.5 * numpy.sin(curve * (z+half_step))
                y2 = 0.5 * numpy.sin(curve * (x+half_step)) + 0.5 * numpy.sin(curve * (z+half_step))
                y3 = 0.5 * numpy.sin(curve * (x+half_step)) + 0.5 * numpy.sin(curve * (z-half_step))
                y4 = 0.5 * numpy.sin(curve * (x-half_step)) + 0.5 * numpy.sin(curve * (z-half_step))
                vertices.append((x-half_step-half_width, y1, z+half_step-half_width))
                vertices.append((x+half_step-half_width, y2, z+half_step-half_width))
                vertices.append((x+half_step-half_width, y3, z-half_step-half_width))
                vertices.append((x-half_step-half_width, y4, z-half_step-half_width))
        self.vertices = vertices

        indices = []
        # indices = [(0, 2, 3), (0, 1, 2)] # Triangle example for single quad
        for i in range(0, len(vertices) - 1, 4):
            indices.append((i, i + 2, i + 3))
            indices.append((i, i + 1, i + 2))
        self.indices = indices

        # Generate vertex data
        vertex_data = generate_vertex_data(vertices, indices)
        # Texture coordinates and texture indices
        texture_coords = []
        texture_indices = []
        for i in range(0, len(vertices) - 1, 4):
            # texture_coords.append((0, 0))
            # texture_coords.append((1, 0))
            # texture_coords.append((1, 1))
            # texture_coords.append((0, 1))
            # Randomize texture coordinates to rotate the texture
            rand_int = numpy.random.randint(4)
            if rand_int == 0:
                texture_coords.append((0, 0))
                texture_coords.append((1, 0))
                texture_coords.append((1, 1))
                texture_coords.append((0, 1))
            elif rand_int == 1:
                texture_coords.append((1, 0))
                texture_coords.append((1, 1))
                texture_coords.append((0, 1))
                texture_coords.append((0, 0))
            elif rand_int == 2:
                texture_coords.append((1, 1))
                texture_coords.append((0, 1))
                texture_coords.append((0, 0))
                texture_coords.append((1, 0))
            elif rand_int == 3:
                texture_coords.append((0, 1))
                texture_coords.append((0, 0))
                texture_coords.append((1, 0))
                texture_coords.append((1, 1))
            texture_indices.append((0, 2, 3))
            texture_indices.append((0, 1, 2))
        texture_coord_data = generate_vertex_data(texture_coords, texture_indices)
        vertex_data = numpy.hstack([texture_coord_data, vertex_data])
        self.vertex_data = numpy.array(vertex_data, dtype='f4')


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
