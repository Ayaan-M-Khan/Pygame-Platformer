#Import statements
import pygame
import gamevalues as gv

#Create Enemy Class
# The Enemy class represents an enemy character in the game. It has properties such as position, health, type (kind), and behavior (movement, jumping, shooting). The class includes methods for updating the enemy's state, drawing it on the screen, and handling damage taken.
#
class Enemy:
    colors = {"walker": (204, 93, 83), "jumper": (190, 111, 215), "shooter": (89, 164, 205), "heavy": (148, 104, 77), "boss": (224, 75, 112)}

    def __init__(self, x, y, kind):
        self.kind = kind
        size = (70, 78) if kind == "boss" else ((52, 52) if kind == "heavy" else (40, 40))
        self.rect = pygame.Rect(x, y, *size)
        self.spawn_x = float(x)
        self.health = gv.ENEMY_HEALTH[kind]
        self.direction = 1
        self.velocity_y = 0.0
        self.jump_timer = gv.JUMPER_INTERVAL
        self.shoot_timer = gv.SHOOTER_INTERVAL
        self.phase = 1

    @property
    def alive(self):
        return self.health > 0

    def update(self, dt, platforms, player_rect):
        projectile = None
        if self.kind in ("walker", "heavy", "boss"):
            speed = gv.ENEMY_SPEED[self.kind]
            self.rect.x += round(speed * self.direction * dt)
            if self._past_platform_edge(platforms) or abs(self.rect.centerx - self.spawn_x) > gv.ENEMY_PATROL_DISTANCE[self.kind]:
                self.direction *= -1
        if self.kind == "jumper":
            self.rect.x += round((1 if player_rect.centerx > self.rect.centerx else -1) * gv.ENEMY_SPEED["jumper"] * dt)
            self.jump_timer -= dt
            if self.jump_timer <= 0 and self.rect.bottom >= self._floor_top(platforms):
                self.velocity_y = -gv.JUMPER_JUMP_FORCE
                self.jump_timer = gv.JUMPER_INTERVAL
        if self.kind in ("shooter", "boss"):
            self.shoot_timer -= dt
            if self.shoot_timer <= 0 and abs(player_rect.centerx - self.rect.centerx) < 850:
                direction = 1 if player_rect.centerx >= self.rect.centerx else -1
                projectile = {"rect": pygame.Rect(self.rect.centerx, self.rect.centery, 12, 8), "velocity": direction * gv.ENEMY_PROJECTILE_SPEED, "damage": gv.ENEMY_PROJECTILE_DAMAGE, "owner": "enemy"}
                self.shoot_timer = gv.SHOOTER_INTERVAL / (1.5 if self.phase == 2 else (2 if self.phase == 3 else 1))
        self.velocity_y = min(self.velocity_y + gv.ENEMY_GRAVITY * dt, gv.ENEMY_MAX_FALL_SPEED)
        self.rect.y += round(self.velocity_y * dt)
        for platform in platforms:
            if self.rect.colliderect(platform.rect) and self.velocity_y >= 0:
                self.rect.bottom = platform.rect.top
                self.velocity_y = 0
        if self.kind == "boss":
            health_ratio = self.health / gv.ENEMY_HEALTH["boss"]
            self.phase = 1 if health_ratio > 0.66 else (2 if health_ratio > 0.33 else 3)
        return projectile

    def _past_platform_edge(self, platforms):
        feet = self.rect.move(self.direction * 4, 2)
        return not any(platform.active and platform.rect.colliderect(feet) for platform in platforms)

    def _floor_top(self, platforms):
        floors = [platform.rect.top for platform in platforms if platform.active and platform.rect.colliderect(self.rect.inflate(20, 4))]
        return min(floors, default=gv.WORLD_HEIGHT)

    def draw(self, surface, camera_x, camera_y):
        rect = self.rect.move(-round(camera_x), -round(camera_y))
        pygame.draw.rect(surface, self.colors[self.kind], rect, border_radius=8)
        pygame.draw.rect(surface, (255, 232, 188), rect, 2, border_radius=8)
        if self.kind == "boss":
            bar = pygame.Rect(rect.x, rect.y - 12, rect.width, 7)
            pygame.draw.rect(surface, (60, 30, 45), bar)
            fill = bar.copy()
            fill.width = round(bar.width * max(0, self.health) / gv.ENEMY_HEALTH["boss"])
            pygame.draw.rect(surface, (245, 80, 105), fill)

    def take_damage(self, amount):
        self.health -= amount


def create_enemies(spawns):
    return [Enemy(x, y, kind) for x, y, kind in spawns]
