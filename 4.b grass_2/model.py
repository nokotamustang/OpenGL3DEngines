import glm
import moderngl
import numpy


class Terrain:
    def __init__(self, app, position=(0, 0, 0), width=32, step=0.1, curve=0.5):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.width = width
        self.step = step

        vertices = []
        for x in numpy.arange(-width, width, step):
            for z in numpy.arange(-width, width, step):
                y = 0.5 * numpy.sin(curve * x) + 0.5 * numpy.sin(curve * z)
                vertices.append((x, y, z))
        self.vertices_mesh = numpy.array(vertices, dtype='f4')


class Grass:
    def __init__(self, app, position=(0, 0, 0), texture: str = 'grass', terrain: Terrain = None, shader_name='grass'):
        self.app = app
        self.ctx = app.ctx
        self.position = glm.mat4(glm.translate(glm.mat4(1), glm.vec3(position)))
        self.terrain = terrain
        self.vbo = self.get_vbo()
        self.shader_program = self.get_shader_program(shader_name)
        self.vao = self.get_vao()
        self.tex_id = app.texture.get_alpha_texture(path=f'textures/{texture}.png')
        self.tex_id_wind = app.texture.get_basic_texture(path=f'textures/flow_map.png')

        # Not ideal format but workable
        self.tex_size = 4096
        self.num_tiles = 4
        self.tile_uv = self.num_tiles * 0.25
        self.current_tile = 4
        self.max_tile = 15
        self.current_tile_xy = glm.vec2(0, 3)

        # Tile indices: count from top left to bottom right, and store the top left corner of each tile
        self.tile_indices = []
        for i in range(self.num_tiles):
            for j in range(self.num_tiles):
                self.tile_indices.append(glm.vec2(i * self.tile_uv, j * self.tile_uv))

        # Create a random selection of tile_indices (0-15) for each grass vertex
        # self.terrain_types = []
        # width = self.terrain.width
        # step = self.terrain.step
        # for x in numpy.arange(-width, width, step):
        #     for z in numpy.arange(-width, width, step):
        #         self.terrain_types.append(numpy.random.randint(0, 16))

        self.on_init()

    def on_init(self):
        # Variables
        self.shader_program['u_time'].value = self.app.time
        # Texture
        self.shader_program['u_wind'] = self.tex_id_wind
        self.shader_program['u_texture_0'] = self.tex_id
        # Light
        self.shader_program['light.color'].value = self.app.light.color
        # Position
        self.shader_program['m_proj'].write(self.app.camera.m_proj)
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['camPos'].write = self.app.camera.position
        # tile_indices
        self.shader_program['u_current_tile'].value = self.current_tile_xy
        # Set point size
        self.ctx.point_size = 4

    def update(self):
        self.shader_program['m_view'].write(self.app.camera.m_view)
        self.shader_program['u_time'].value = self.app.time
        self.shader_program['camPos'].write = self.app.camera.position

    def change_tile(self):
        self.current_tile = self.current_tile + 1
        if self.current_tile >= self.max_tile:
            self.current_tile = 0
        self.current_tile_xy = self.tile_indices[self.current_tile]
        self.shader_program['u_current_tile'].value = self.current_tile_xy

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
