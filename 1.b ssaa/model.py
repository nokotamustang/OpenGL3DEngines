import glm
import numpy


class Cube:
    def __init__(self, app, color=(0.9, 0.1, 0.1), position=(0, 0, 0)):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.color = glm.vec3(color)
        self.vbo = self.get_vbo()
        self.shader_program = self.get_shader_program()
        self.vao = self.get_vao()
        self.on_init()

    def on_init(self):
        # Light
        self.shader_program['light.position'].value = self.app.light.position
        self.shader_program['light.Ia'].value = self.app.light.Ia
        self.shader_program['light.Id'].value = self.app.light.Id
        self.shader_program['light.Is'].value = self.app.light.Is
        # Position
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.position)
        # Color
        self.shader_program['material.Ka'].value = self.color

    def update(self):
        m_model = glm.rotate(self.position, self.app.time, glm.vec3(0, 1, 0))
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(m_model)

    def render(self):
        self.vao.render()

    def destroy(self):
        self.vbo.release()
        self.shader_program.release()
        self.vao.release()

    def get_vao(self):
        vao = self.ctx.vertex_array(self.shader_program, [
            (self.vbo, '3f 3f', 'in_position', 'in_normal'),
        ])
        return vao

    def get_vertex_data(self):
        vertices = [
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
            (-1, 1, -1), (-1, -1, -1), (1, -1, -1), (1, 1, -1)
        ]
        indices = [
            (0, 2, 3), (0, 1, 2),
            (1, 7, 2), (1, 6, 7),
            (6, 5, 4), (4, 7, 6),
            (3, 4, 5), (3, 5, 0),
            (3, 7, 4), (3, 2, 7),
            (0, 6, 1), (0, 5, 6),
        ]
        normals = [
            (0, 0, 1) * 6,
            (1, 0, 0) * 6,
            (0, 0, -1) * 6,
            (-1, 0, 0) * 6,
            (0, 1, 0) * 6,
            (0, -1, 0) * 6,
        ]
        normals = numpy.array(normals, dtype='f4').reshape(36, 3)
        vertex_data = self.generate_vertex_data(vertices, indices)
        vertex_data = numpy.hstack([vertex_data, normals])
        return numpy.array(vertex_data, dtype='f4')

    def generate_vertex_data(self, vertices, indices):
        data = [vertices[ind] for triangle in indices for ind in triangle]
        return numpy.array(data, dtype='f4')

    def get_vbo(self):
        return self.ctx.buffer(self.get_vertex_data())

    def get_shader_program(self, shader_name='default'):
        with open(f'{self.app.base_path}/{shader_name}.vert', 'r') as f:
            vertex_shader_source = f.read()
        with open(f'{self.app.base_path}/{shader_name}.frag', 'r') as f:
            fragment_shader_source = f.read()
        shader_program = self.ctx.program(
            vertex_shader=vertex_shader_source,
            fragment_shader=fragment_shader_source,
        )
        return shader_program
