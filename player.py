#Imort statements 
import gamevalues as gv
import pygame

#Create Player Class
class Player:
    #Define the constructor for the Player class with default values for health, speed, jump strength, and projectile attributes
    def __init__(
        self,
        x,
        y,
        health=gv.PLAYER_HEALTH,
        speed=gv.PLAYER_MAX_SPEED,
        jump_strength=gv.PLAYER_JUMP_FORCE,
        image=None,
        projectile_image=None,
        projectile_speed=0,
        projectile_damage=0,
    ):
        self.rect = pygame.Rect(round(x), round(y), gv.PLAYER_WIDTH, gv.PLAYER_HEIGHT)
        self.width = self.rect.width
        self.height = self.rect.height
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.health = health
        self.speed = speed
        self.jump_strength = jump_strength
        self.image = image
        self.projectile_image = projectile_image
        self.projectile_speed = projectile_speed
        self.projectile_damage = projectile_damage
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.has_dash = False
        self.extra_jumps = 0
        self.jumps_remaining = 0
        self.dash_cooldown = 0.0

    #Define properties for the x and y coordinates of the player, allowing for easy access and modification of the player's position
    @property
    def x(self):
        return float(self.rect.x)

    @x.setter
    def x(self, value):
        self.rect.x = round(value)

    @property
    def y(self):
        return float(self.rect.y)

    @y.setter
    def y(self, value):
        self.rect.y = round(value)

    def update(self, keys, platforms, dt):
        """Advance movement and resolve collisions against platform rectangles."""
        dt = min(max(dt, 0.0), 0.05)
        self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
        was_on_ground = self.on_ground
        self.on_ground = False

        if was_on_ground:
            self.coyote_timer = gv.COYOTE_TIME
        else:
            self.coyote_timer = max(0.0, self.coyote_timer - dt)

        if keys[pygame.K_SPACE]:
            self.jump_buffer_timer = gv.JUMP_BUFFER_TIME
        else:
            self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - dt)

        horizontal_input = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        acceleration = gv.PLAYER_ACCELERATION if was_on_ground else gv.PLAYER_AIR_ACCELERATION
        if horizontal_input:
            self.vel_x += horizontal_input * acceleration * dt
            self.vel_x = max(-self.speed, min(self.speed, self.vel_x))
        else:
            friction = gv.PLAYER_FRICTION * dt
            if abs(self.vel_x) <= friction:
                self.vel_x = 0.0
            else:
                self.vel_x -= friction if self.vel_x > 0 else -friction

        if self.jump_buffer_timer > 0 and (was_on_ground or self.coyote_timer > 0 or self.jumps_remaining > 0):
            self.vel_y = -self.jump_strength
            self.jump_buffer_timer = 0.0
            self.coyote_timer = 0.0
            if not was_on_ground and self.jumps_remaining > 0:
                self.jumps_remaining -= 1

        if was_on_ground:
            self.jumps_remaining = self.extra_jumps

        if self.has_dash and keys[pygame.K_LSHIFT] and self.dash_cooldown <= 0:
            direction = horizontal_input or 1
            self.vel_x = direction * gv.DASH_SPEED
            self.vel_y = 0.0
            self.dash_cooldown = gv.DASH_COOLDOWN

        if not keys[pygame.K_SPACE] and self.vel_y < 0:
            self.vel_y += gv.PLAYER_GRAVITY * (1 - gv.JUMP_RELEASE_MULTIPLIER) * dt

        self.vel_y = min(self.vel_y + gv.PLAYER_GRAVITY * dt, gv.PLAYER_MAX_FALL_SPEED)

        self._move_horizontally(platforms, self.vel_x * dt)
        self._move_vertically(platforms, self.vel_y * dt)

    def _move_horizontally(self, platforms, distance):
        previous_bottom = self.rect.bottom
        self.rect.x += round(distance)
        for platform in platforms:
            platform_rect = self._platform_rect(platform)
            if previous_bottom > platform_rect.top and self.rect.colliderect(platform_rect):
                if distance > 0:
                    self.rect.right = platform_rect.left
                elif distance < 0:
                    self.rect.left = platform_rect.right
                self.vel_x = 0.0

    def _move_vertically(self, platforms, distance):
        previous_bottom = self.rect.bottom
        self.rect.y += round(distance)
        for platform in platforms:
            platform_rect = self._platform_rect(platform)
            if getattr(platform, "can_pass_through", False) and distance < 0:
                continue
            if self.rect.colliderect(platform_rect):
                if distance > 0:
                    self.rect.bottom = platform_rect.top
                    self.vel_y = 0.0
                    self.on_ground = True
                elif distance < 0:
                    if previous_bottom <= platform_rect.top:
                        continue
                    self.rect.top = platform_rect.bottom
                    self.vel_y = 0.0

    @staticmethod
    def _platform_rect(platform):
        return platform.rect if hasattr(platform, "rect") else platform

    def draw(self, surface, camera_x=0, camera_y=0):
        draw_rect = self.rect.move(-round(camera_x), -round(camera_y))
        pygame.draw.rect(surface, gv.PLAYER_COLOR, draw_rect, border_radius=8)
        pygame.draw.rect(surface, gv.PLAYER_OUTLINE_COLOR, draw_rect, width=2, border_radius=8)

    def move(self, keys):
        """Compatibility wrapper for callers that still use the original API."""
        self.update(keys, (), 1 / gv.TARGET_FPS)