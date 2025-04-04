import moderngl
import glm
import pygame


class Camera:
    yaw = -90
    pitch = 0
    fov = 50  # Degrees
    near = 0.1
    far = 100
    sensitivity = 0.1
    speed = 0.005

    position = None
    up = glm.vec3(0, 1, 0)
    right = glm.vec3(1, 0, 0)
    forward = glm.vec3(0, 0, -1)

    def __init__(self, app, position=(0, 0, 0), yaw=yaw, pitch=pitch,
                 fov=fov, near=near, far=far, sensitivity=sensitivity):
        self.app = app
        self.position = glm.vec3(position)
        self.yaw = yaw
        self.pitch = pitch
        self.fov = fov
        self.near = near
        self.far = far
        self.sensitivity = sensitivity
        # View matrix
        self.m_view = self.get_view_matrix()
        # Aspect ratio and Projection matrix
        self.set_aspect_and_projection()
        # Key bindings
        self.key_bindings = {
            "forward": pygame.K_w,
            "backward": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
            "up": pygame.K_SPACE,
            "down": pygame.K_LCTRL,
        }

    def set_aspect_and_projection(self):
        self.aspect_ratio = self.app.win_size[0] / self.app.win_size[1]
        self.m_proj = self.get_projection_matrix()

    def rotate(self):
        rel_x, rel_y = pygame.mouse.get_rel()
        self.yaw += rel_x * self.sensitivity
        self.pitch -= rel_y * self.sensitivity
        self.pitch = max(-89, min(89, self.pitch))

    def update_camera_vectors(self):
        yaw, pitch = glm.radians(self.yaw), glm.radians(self.pitch)
        self.forward.x = glm.cos(yaw) * glm.cos(pitch)
        self.forward.y = glm.sin(pitch)
        self.forward.z = glm.sin(yaw) * glm.cos(pitch)
        self.forward = glm.normalize(self.forward)
        self.right = glm.normalize(glm.cross(self.forward, glm.vec3(0, 1, 0)))
        self.up = glm.normalize(glm.cross(self.right, self.forward))

    def update(self):
        self.move()
        self.rotate()
        self.update_camera_vectors()
        self.m_view = self.get_view_matrix()

    def move(self):
        self.velocity = self.speed * self.app.delta_time
        keys = pygame.key.get_pressed()
        if keys[self.key_bindings["forward"]]:
            self.position += self.forward * self.velocity
        if keys[self.key_bindings["backward"]]:
            self.position -= self.forward * self.velocity
        if keys[self.key_bindings["left"]]:
            self.position -= self.right * self.velocity
        if keys[self.key_bindings["right"]]:
            self.position += self.right * self.velocity
        if keys[self.key_bindings["up"]]:
            self.position += self.up * self.velocity
        if keys[self.key_bindings["down"]]:
            self.position -= self.up * self.velocity

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.forward, self.up)

    def get_projection_matrix(self):
        return glm.perspective(glm.radians(self.fov), self.aspect_ratio, self.near, self.far)


class Light:
    def __init__(self, position=(10, 10, -10), color=(1, 1, 1), strength=1.0):
        self.position = glm.vec3(position)
        self.color = glm.vec3(color)
        self.direction = glm.vec3(0, 0, 0)
        self.strength = strength
        # View matrix
        self.m_view_light = self.get_view_matrix()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.direction, glm.vec3(0, 1, 0))


class Shader():
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.programs = []
        self.programs_count = -1
        self.programs_map = {}

    def get_shader(self, shader_name, geometry=False):
        if shader_name in self.programs_map:
            # print(f"Reuse shader: {shader_name} at index: {self.programs_map[shader_name]}")
            return self.programs[self.programs_map[shader_name]]

        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.vert', 'r') as f:
            vertex_shader_source = f.read()
        with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.frag', 'r') as f:
            fragment_shader_source = f.read()

        if geometry is True:
            with open(f'{self.app.base_path}/{self.app.shader_path}/{shader_name}.geom', 'r') as f:
                geometry_shader_source = f.read()
            shader_program = self.ctx.program(
                vertex_shader=vertex_shader_source,
                fragment_shader=fragment_shader_source,
                geometry_shader=geometry_shader_source,
            )
        else:
            shader_program = self.ctx.program(
                vertex_shader=vertex_shader_source,
                fragment_shader=fragment_shader_source,
            )
        self.programs_count += 1
        self.programs_map[shader_name] = self.programs_count
        self.programs.append(shader_program)
        print(f"loaded shader: {shader_name} at index: {self.programs_count}")
        return shader_program

    def destroy(self):
        for program in self.programs:
            program.release()


class Texture:
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx
        self.textures = []
        self.texture_count = -1
        self.texture_map = {}

    def get_texture(self, path):
        if path in self.texture_map:
            return self.texture_map[path]

        texture = pygame.image.load(path).convert()
        texture = pygame.transform.flip(texture, flip_x=False, flip_y=True)  # Flip Pygame -> OpenGL
        texture = self.ctx.texture(size=texture.get_size(), components=3,
                                   data=pygame.image.tostring(texture, 'RGB'))
        # Mipmaps
        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        texture.min_lod = -1000
        texture.max_lod = 1000
        # Set levels of mipmaps
        texture.build_mipmaps(base=0, max_level=1000)
        # AF
        texture.anisotropy = 32.0
        # Add to list
        self.texture_count += 1
        self.texture_map[path] = self.texture_count
        self.textures.append(texture)
        print(f"loaded texture: {path} at index: {self.texture_count}")
        return self.texture_count

    def get_depth_texture(self, size, name='depth_texture'):
        if name in self.texture_map:
            return self.texture_map[name]
        depth_texture = self.ctx.depth_texture(size=size)
        # Remove repetition
        depth_texture.repeat_x = False
        depth_texture.repeat_y = False
        # Add to list
        self.texture_count += 1
        self.texture_map[name] = self.texture_count
        self.textures.append(depth_texture)
        print(f"loaded depth texture: {name} at index: {self.texture_count}")
        return self.texture_count

    def get_color_texture(self, size, name='color_texture'):
        if name in self.texture_map:
            return self.texture_map[name]
        color_texture = self.ctx.texture(size=size, components=4, samples=4)
        # Remove repetition
        color_texture.repeat_x = False
        color_texture.repeat_y = False
        # Add to list
        self.texture_count += 1
        self.texture_map[name] = self.texture_count
        self.textures.append(color_texture)
        print(f"loaded color texture: {name} at index: {self.texture_count}")
        return self.texture_count

    def destroy(self):
        for texture in self.textures:
            texture.release()


class Shadow():
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx

        # Using a texture here not a renderbuffer because we pass it to the shader
        self.depth_tex_id = self.app.texture.get_depth_texture(self.app.win_size)
        self.depth_texture = self.app.texture.textures[self.depth_tex_id]
        # self.depth_buffer = self.ctx.depth_renderbuffer(size=self.app.win_size)

        self.depth_fbo = self.ctx.framebuffer(depth_attachment=self.depth_texture)
        # self.depth_fbo = self.ctx.framebuffer(depth_attachment=self.depth_buffer)

    def destroy(self):
        self.depth_fbo.release()
        self.depth_texture.release()
