
import glm
import moderngl
import pygame


class Camera:
    yaw = -90
    pitch = 0
    fov = 50  # Degrees
    near = 0.1
    far = 100
    sensitivity = 0.1
    speed = 0.005

    position = glm.vec3(0, 0, 4)
    up = glm.vec3(0, 1, 0)
    right = glm.vec3(1, 0, 0)
    forward = glm.vec3(0, 0, -1)

    def __init__(self, app, position=position, yaw=yaw, pitch=pitch,
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
        self.velocity = self.speed * self.app.raw_delta_time
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
    def __init__(self, position=(50, 50, -10), color=(1, 1, 1)):
        self.position = glm.vec3(position)
        self.color = glm.vec3(color)
        self.direction = glm.vec3(0, 0, 0)
        # Intensities
        self.Ia = 0.06 * self.color  # Ambient (Albedo)
        self.Id = 0.8 * self.color  # Diffuse (Lambert)
        self.Is = 1.0 * self.color  # Specular (Blinn-Phong)
        # View matrix
        self.m_view_light = self.get_view_matrix()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.direction, glm.vec3(0, 1, 0))


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
        color_texture = self.ctx.texture(size=size, components=4)
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


class AA():
    def __init__(self, app):
        self.app = app
        self.ctx = app.ctx

        # We use a renderbuffer for the depth and color attachments --
        # From mgl docs:
        # They are optimized for use as render targets, while Texture objects may not be,
        # and are the logical choice when you do not need to sample from the produced image.
        # If you need to resample, use Textures instead.
        # Renderbuffer objects also natively accommodate multi-sampling.

        # self.depth_tex_id = self.app.texture.get_depth_texture(self.app.win_size)
        # self.depth_texture = self.app.texture.textures[self.depth_tex_id]
        # self.depth_buffer = self.ctx.depth_renderbuffer(size=self.app.win_size, samples=4)

        # self.color_tex_id = self.app.texture.get_color_texture(self.app.win_size)
        # self.color_texture = self.app.texture.textures[self.color_tex_id]
        self.color_buffer = self.ctx.renderbuffer(size=self.app.win_size, samples=4)

        # The depth attachment here for demonstration purposes, it's not used in this example
        # self.aa_fbo = self.ctx.framebuffer(color_attachments=[self.color_buffer],
        #                                    depth_attachment=self.depth_buffer)

        # We don't need the depth attachment here
        self.aa_fbo = self.ctx.framebuffer(color_attachments=[self.color_buffer])

    def destroy(self):
        self.aa_fbo.release()
        self.depth_texture.release()
        self.color_texture.release()
