import pygame

import gamevalues as gv


class Weapon:
    def __init__(self, name, damage, cooldown, range, knockback, kind="melee"):
        self.name = name
        self.damage = damage
        self.cooldown = cooldown
        self.range = range
        self.knockback = knockback
        self.kind = kind
        self.last_attack = -cooldown

    def ready(self, now):
        return now - self.last_attack >= self.cooldown

    def attack(self, player, now):
        if not self.ready(now):
            return None
        self.last_attack = now
        if self.kind == "melee":
            x = player.rect.right if player.facing > 0 else player.rect.left - self.range
            return {"kind": "melee", "rect": pygame.Rect(x, player.rect.centery - 24, self.range, 48), "damage": self.damage, "knockback": self.knockback, "expires": now + gv.SWORD_ATTACK_TIME}
        return {"kind": "ranged", "direction": player.facing, "damage": self.damage, "knockback": self.knockback}


class WeaponChest:
    def __init__(self, x, y, weapon_id):
        self.rect = pygame.Rect(x, y, gv.CHEST_WIDTH, gv.CHEST_HEIGHT)
        self.weapon_id = weapon_id
        self.opened = False

    def open(self, player):
        if self.opened:
            return None
        self.opened = True
        weapon = create_weapon(self.weapon_id)
        player.add_weapon(weapon)
        player.equip_weapon(weapon.name)
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
        return Weapon("Ember Blade", gv.EMBER_BLADE_DAMAGE, gv.SWORD_COOLDOWN, gv.SWORD_RANGE, gv.SWORD_KNOCKBACK)
    if weapon_id == "storm_bow":
        return Weapon("Storm Bow", gv.STORM_BOW_DAMAGE, gv.STORM_BOW_COOLDOWN, gv.STORM_BOW_RANGE, gv.STORM_BOW_KNOCKBACK, "ranged")
    if weapon_id == "ranged":
        return Weapon("Pulse Caster", gv.PROJECTILE_DAMAGE, gv.PROJECTILE_COOLDOWN * 1000, gv.PROJECTILE_RANGE, gv.PROJECTILE_KNOCKBACK, "ranged")
    return Weapon("Iron Sword", gv.SWORD_DAMAGE, gv.SWORD_COOLDOWN, gv.SWORD_RANGE, gv.SWORD_KNOCKBACK)
