import glm
import numpy


def generate_vertex_data(vertices, indices):
    data = [vertices[ind] for triangle in indices for ind in triangle]
    return numpy.array(data, dtype='f4')


class Cube:
    def __init__(self, app, albedo=(0.9, 0.1, 0.1),
                 metallic: float = 0.0, roughness: float = 0.0, ao: float = 1.0,
                 position=(0, 0, 0), size=(0.5, 0.5, 0.5), texture: str = 'crate_0'):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.size = size
        self.albedo = glm.vec3(albedo)
        self.metallic = metallic
        self.roughness = roughness
        self.ao = ao

        self.vbo = self.get_vbo()
        self.shader_program = app.shader.get_shader('default')
        self.vao = self.get_vao()

        # self.shadow_vbo = self.get_vbo()
        self.shadow_program = app.shader.get_shader('shadow')
        self.shadow_vao = self.get_shadow_vao()

        self.tex_id = app.texture.get_texture(path=f'textures/{texture}.png')
        self.depth_tex_id = app.shadow.depth_tex_id
        self.m_model = self.position
        self.on_init()

    def on_init(self):
        # Set resolution
        self.shader_program['u_resolution'].write(glm.vec2(self.app.win_size))
        # n lights
        self.shader_program['num_lights'].value = len(self.app.lights)
        # Send lights into uniform array of Light struct
        for i, light in enumerate(self.app.lights):
            self.shader_program[f'lights[{i}].position'].value = light.position
            self.shader_program[f'lights[{i}].color'].value = light.color
            self.shader_program[f'lights[{i}].strength'].value = light.strength
        self.shader_program['m_view_light'].write(self.app.light.m_view_light)
        # Position
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.position)
        # Material: Albedo (rgb), metallic, rough, ao
        self.shader_program['material.Ka'].value = self.albedo
        self.shader_program['material.Km'].value = self.metallic
        self.shader_program['material.Kr'].value = self.roughness
        self.shader_program['material.Kao'].value = self.ao
        # Shadow depth map
        self.shader_program['u_shadow_map'] = self.depth_tex_id
        self.app.texture.textures[self.depth_tex_id].use(location=self.depth_tex_id)
        # Camera
        self.shader_program['camPos'].write = self.app.camera.position
        # Shadow program
        self.shadow_program['m_proj'].write(self.app.camera.m_proj)
        self.shadow_program['m_view_light'].write(self.app.light.m_view_light)
        self.shadow_program['m_model'].write(self.m_model)

    def update(self):
        self.m_model = glm.rotate(self.position, self.app.time, glm.vec3(0, 1, 0))

    def render(self):
        # n lights
        self.shader_program['num_lights'].value = len(self.app.lights)
        # Send lights into uniform array of Light struct
        for i, light in enumerate(self.app.lights):
            self.shader_program[f'lights[{i}].position'].value = light.position
            self.shader_program[f'lights[{i}].color'].value = light.color
            self.shader_program[f'lights[{i}].strength'].value = light.strength
        self.shader_program['m_view_light'].write(self.app.light.m_view_light)
        # Position
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['m_model'].write(self.m_model)
        # Material: Albedo (rgb), metallic, rough, ao
        self.shader_program['material.Ka'].value = self.albedo
        self.shader_program['material.Km'].value = self.metallic
        self.shader_program['material.Kr'].value = self.roughness
        self.shader_program['material.Kao'].value = self.ao
        # Shadow depth map
        self.shader_program['u_shadow_map'] = self.depth_tex_id
        self.app.texture.textures[self.depth_tex_id].use(location=self.depth_tex_id)
        # Camera
        self.shader_program['camPos'].write = self.app.camera.position
        # Texture
        self.shader_program['u_texture_0'] = self.tex_id
        self.app.texture.textures[self.tex_id].use(location=self.tex_id)
        # Render
        self.vao.render()

    def render_shadow(self):
        self.shadow_program['m_proj'].write(self.app.camera.m_proj)
        self.shadow_program['m_view_light'].write(self.app.light.m_view_light)
        self.shadow_program['m_model'].write(self.m_model)
        self.shadow_vao.render()

    def destroy(self):
        self.vao.release()
        self.shadow_vao.release()
        self.shader_program.release()
        self.shadow_program.release()
        self.vbo.release()
        # self.shadow_vbo.release()

    def get_vao(self):
        vao = self.ctx.vertex_array(self.shader_program, [
            (self.vbo, '2f 3f 3f', 'in_texcoord_0', 'in_position', 'in_normal'),
        ])
        return vao

    def get_shadow_vao(self):
        vao = self.ctx.vertex_array(self.shadow_program, [
            (self.vbo, '2f 3f 3f', 'in_texcoord_0', 'in_position', 'in_normal'),
        ], skip_errors=True)
        # Temporary fix for the issue with the shadow program because we are not using texture coordinates
        # So we set skip_errors=True to ignore the missing in_texcoord_0 attribute
        return vao

    def get_vertex_data(self, size=(0.5, 0.5, 0.5)):
        # Vertices
        vertices = [
            (-size[0], -size[1], size[2]), (size[0], -size[1], size[2]), (size[0], size[1], size[2]), (-size[0], size[1], size[2]),
            (-size[0], size[1], -size[2]), (-size[0], -size[1], -size[2]), (size[0], -size[1], -size[2]), (size[0], size[1], -size[2])
        ]
        indices = [
            (0, 2, 3), (0, 1, 2),
            (1, 7, 2), (1, 6, 7),
            (6, 5, 4), (4, 7, 6),
            (3, 4, 5), (3, 5, 0),
            (3, 7, 4), (3, 2, 7),
            (0, 6, 1), (0, 5, 6),
        ]
        vertex_data = generate_vertex_data(vertices, indices)

        # Texture coordinates
        texture_coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
        texture_indices = [(0, 2, 3), (0, 1, 2),
                           (0, 2, 3), (0, 1, 2),
                           (0, 1, 2), (2, 3, 0),
                           (2, 3, 0), (2, 0, 1),
                           (0, 2, 3), (0, 1, 2),
                           (3, 1, 2), (3, 0, 1)]
        texture_coord_data = generate_vertex_data(texture_coords, texture_indices)
        vertex_data = numpy.hstack([texture_coord_data, vertex_data])

        # Normals
        normals = [
            (0, 0, 1) * 6,
            (1, 0, 0) * 6,
            (0, 0, -1) * 6,
            (-1, 0, 0) * 6,
            (0, 1, 0) * 6,
            (0, -1, 0) * 6,
        ]
        normals = numpy.array(normals, dtype='f4').reshape(36, 3)
        vertex_data = numpy.hstack([vertex_data, normals])

        return numpy.array(vertex_data, dtype='f4')

    def get_vbo(self):
        return self.ctx.buffer(self.get_vertex_data(size=self.size))


class Floor(Cube):
    def __init__(self, app, albedo=(0.9, 0.1, 0.1),
                 metallic: float = 0.0, roughness: float = 0.0, ao: float = 1.0,
                 position=(0, 0, 0), size=(0.5, 0.5, 0.5), texture: str = 'ground'):
        super().__init__(app, albedo, metallic, roughness, ao, position, size, texture)

    def update(self):
        # m_model = glm.rotate(self.position, self.app.time, glm.vec3(0, 1, 0))
        self.shader_program['m_view'].write(self.app.camera.m_view)
        # self.shader_program['m_model'].write(m_model)
