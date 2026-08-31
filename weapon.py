import math
import random

import pygame

import gamevalues as gv


class Weapon:
    def __init__(self, name, damage, cooldown, range, knockback, kind="melee", description=""):
        self.name = name
        self.damage = damage
        self.cooldown = cooldown
        self.range = range
        self.knockback = knockback
        self.kind = kind
        self.description = description or f"A reliable {kind} weapon."
        self.last_attack = -cooldown
        self.angle = 0.0

    def update_aim(self, player_rect, mouse_position, camera_x=0, camera_y=0):
        screen_rect = player_rect.move(-round(camera_x), -round(camera_y))
        self.angle = math.atan2(mouse_position[1] - screen_rect.centery, mouse_position[0] - screen_rect.centerx)

    def describe(self):
        return f"{self.kind.title()} | {self.damage} damage | {self.cooldown / 1000:.1f}s cooldown"

    def ready(self, now):
        return now - self.last_attack >= self.cooldown


class Sword(Weapon):
    def __init__(self, name="Iron Sword", damage=None, cooldown=None, knockback=None):
        super().__init__(name, damage or gv.SWORD_DAMAGE, cooldown or gv.SWORD_COOLDOWN, gv.SWORD_RANGE, knockback or gv.SWORD_KNOCKBACK, description="A close-range blade with a sweeping arc.")
        self.swinging = False
        self.swing_start = 0
        self.base_direction = 1
        self.hit_set = set()

    def swing(self, player, now):
        if not self.ready(now):
            return None
        self.last_attack = now
        self.swinging = True
        self.swing_start = now
        self.base_direction = player.facing
        self.angle = player.aim_angle
        self.hit_set.clear()
        return {"kind": "melee", "damage": self.damage, "knockback": self.knockback, "expires": now + gv.SWORD_ATTACK_TIME}

    def update(self, now):
        if self.swinging and now - self.swing_start >= gv.SWORD_ATTACK_TIME:
            self.swinging = False

    def check_hits(self, player_rect, enemies, now):
        self.update(now)
        if not self.swinging:
            return []
        progress = min(1.0, (now - self.swing_start) / gv.SWORD_ATTACK_TIME)
        hits = []
        for step in range(5):
            reach = self.range * (0.35 + 0.65 * min(1.0, progress + step * 0.08))
            center = pygame.Vector2(player_rect.center) + pygame.Vector2(math.cos(self.angle), math.sin(self.angle)) * reach
            hitbox = pygame.Rect(center.x - self.range // 2, center.y - 28, self.range, 56)
            for enemy in enemies:
                if id(enemy) not in self.hit_set and enemy.alive and hitbox.colliderect(enemy.rect):
                    self.hit_set.add(id(enemy))
                    hits.append(enemy)
        return hits

    def draw(self, surface, player_rect, camera_x=0, camera_y=0):
        rect = player_rect.move(-round(camera_x), -round(camera_y))
        start = rect.center
        length = self.range + 12
        end = (start[0] + math.cos(self.angle) * length, start[1] + math.sin(self.angle) * length)
        pygame.draw.line(surface, (230, 238, 244), start, end, 6 if self.swinging else 4)
        if self.swinging:
            pygame.draw.arc(surface, (112, 207, 255), rect.inflate(self.range, self.range), -self.angle - 0.8, -self.angle + 0.8, 3)


class Bullet:
    def __init__(self, x, y, direction, speed, damage, range, color=(255, 235, 130), radius=5):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(direction) * speed if isinstance(direction, (tuple, list)) else pygame.Vector2(direction * speed, 0)
        self.damage = damage
        self.range = range
        self.travelled = 0.0
        self.color = color
        self.radius = radius
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(round(self.position.x - self.radius), round(self.position.y - self.radius), self.radius * 2, self.radius * 2)

    def update(self, dt, platforms, world_width):
        displacement = self.velocity * dt
        self.position += displacement
        self.travelled += displacement.length()
        if self.travelled >= self.range or self.position.x < 0 or self.position.x > world_width:
            self.alive = False
        if any(platform.active and self.rect.colliderect(platform.rect) for platform in platforms):
            self.alive = False

    def draw(self, surface, camera_x=0, camera_y=0):
        center = (round(self.position.x - camera_x), round(self.position.y - camera_y))
        pygame.draw.circle(surface, self.color, center, self.radius)
        pygame.draw.circle(surface, (255, 255, 255), center, max(1, self.radius - 2))


class Coin:
    def __init__(self, x, y, velocity):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(velocity)
        self.alive = True

    def update(self, dt, platforms):
        self.velocity.y += 900 * dt
        self.position += self.velocity * dt
        rect = pygame.Rect(round(self.position.x - 6), round(self.position.y - 6), 12, 12)
        for platform in platforms:
            if platform.active and rect.colliderect(platform.rect) and self.velocity.y > 0:
                self.position.y = platform.rect.top - 6
                self.velocity.y *= -0.35
        self.velocity.x *= 0.96

    def draw(self, surface, camera_x=0, camera_y=0):
        center = (round(self.position.x - camera_x), round(self.position.y - camera_y))
        pygame.draw.circle(surface, (255, 210, 65), center, 6)
        pygame.draw.circle(surface, (255, 246, 165), (center[0] - 2, center[1] - 2), 2)


def coin_burst(x, y, count=5):
    return [Coin(x, y, (random.uniform(-180, 180), random.uniform(-360, -160))) for _ in range(count)]


class Gun(Weapon):
    STATS = {
        "Pulse Caster": dict(damage=gv.PROJECTILE_DAMAGE, speed=gv.PROJECTILE_SPEED, fire_rate=250, spread=0, bullets=1, mag_size=12, total_ammo=72, range=gv.PROJECTILE_RANGE),
        "Storm Bow": dict(damage=gv.STORM_BOW_DAMAGE, speed=gv.PROJECTILE_SPEED + 100, fire_rate=gv.STORM_BOW_COOLDOWN, spread=0, bullets=1, mag_size=8, total_ammo=48, range=gv.STORM_BOW_RANGE),
        "Scatter Blaster": dict(damage=12, speed=gv.PROJECTILE_SPEED - 80, fire_rate=650, spread=0, bullets=3, mag_size=6, total_ammo=30, range=500),
    }

    def __init__(self, gun_type="Pulse Caster"):
        stats = self.STATS[gun_type]
        super().__init__(gun_type, stats["damage"], stats["fire_rate"], stats["range"], gv.PROJECTILE_KNOCKBACK, "ranged", "Directional ranged weapon with a finite magazine.")
        self.stats = stats
        self.speed = stats["speed"]
        self.ammo_current = stats["mag_size"]
        self.ammo_reserve = stats["total_ammo"] - stats["mag_size"]
        self.muzzle_flash_until = 0

    def fire(self, player, now):
        if not self.ready(now) or self.ammo_current < self.stats["bullets"]:
            return []
        self.last_attack = now
        self.ammo_current -= self.stats["bullets"]
        self.muzzle_flash_until = now + 80
        direction = (math.cos(self.angle), math.sin(self.angle))
        bullets = [Bullet(player.rect.centerx + direction[0] * 20, player.rect.centery + direction[1] * 20, direction, self.speed, self.damage, self.range) for _ in range(self.stats["bullets"])]
        for bullet in bullets:
            bullet.owner = "player"
        return bullets

    def reload(self):
        missing = self.stats["mag_size"] - self.ammo_current
        moved = min(missing, self.ammo_reserve)
        self.ammo_current += moved
        self.ammo_reserve -= moved

    def draw(self, surface, player_rect, camera_x=0, camera_y=0, now=0, facing=1):
        rect = player_rect.move(-round(camera_x), -round(camera_y))
        direction = facing
        start = rect.center
        end = (start[0] + math.cos(self.angle) * 28, start[1] + math.sin(self.angle) * 28)
        pygame.draw.line(surface, (81, 190, 211), start, end, 5)
        if now < self.muzzle_flash_until:
            pygame.draw.circle(surface, (255, 218, 100), end, 8)


class WeaponChest:
    LOOT_TABLE = ("ember_blade", "storm_bow", "scatter_blaster")

    def __init__(self, x, y, weapon_id):
        self.rect = pygame.Rect(x, y, gv.CHEST_WIDTH, gv.CHEST_HEIGHT)
        self.weapon_id = weapon_id
        self.opened = False
        self.coin_drops = []

    def open(self, player):
        if self.opened:
            return None
        self.opened = True
        weapon = create_weapon(self.weapon_id or random.choice(self.LOOT_TABLE))
        if hasattr(weapon, "ammo_reserve"):
            for existing in player.weapon_slots:
                if existing is not weapon and existing.name == weapon.name and hasattr(existing, "ammo_reserve"):
                    existing.ammo_reserve += weapon.ammo_reserve + weapon.ammo_current
                    existing.reload()
                    player.equip_weapon(existing.name)
                    self.coin_drops = coin_burst(self.rect.centerx, self.rect.centery)
                    return existing
        player.add_weapon(weapon)
        player.equip_weapon(weapon.name)
        self.coin_drops = coin_burst(self.rect.centerx, self.rect.centery)
        return weapon

    def draw(self, surface, camera_x, camera_y):
        rect = self.rect.move(-round(camera_x), -round(camera_y))
        body = (82, 55, 42) if not self.opened else (125, 91, 57)
        pygame.draw.rect(surface, body, rect, border_radius=4)
        pygame.draw.rect(surface, (238, 188, 83), rect, 2, border_radius=4)
        lid = rect.move(0, -8 if self.opened else 0)
        pygame.draw.line(surface, (238, 188, 83), lid.midtop, lid.midright, 2)


def create_weapon(weapon_id):
    if weapon_id == "ember_blade":
        return Sword("Ember Blade", gv.EMBER_BLADE_DAMAGE)
    if weapon_id == "storm_bow":
        return Gun("Storm Bow")
    if weapon_id == "ranged":
        return Gun("Pulse Caster")
    if weapon_id == "scatter_blaster":
        return Gun("Scatter Blaster")
    return Sword()
