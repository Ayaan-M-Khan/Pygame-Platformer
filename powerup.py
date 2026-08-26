import pygame
import gamevalues as gv


class PowerUp:
    colors = {"dash": (91, 219, 190), "double_jump": (111, 167, 242), "shield": (244, 208, 91), "health": (236, 112, 120)}

    def __init__(self, x, y, kind):
        self.kind = kind
        self.rect = pygame.Rect(x, y, gv.POWERUP_SIZE, gv.POWERUP_SIZE)
        self.collected = False

    def draw(self, surface, camera_x, camera_y):
        if not self.collected:
            rect = self.rect.move(-round(camera_x), -round(camera_y))
            pygame.draw.circle(surface, self.colors[self.kind], rect.center, rect.width // 2)
            pygame.draw.circle(surface, (255, 245, 207), rect.center, rect.width // 2, 2)


def create_powerups(spawns):
    return [PowerUp(x, y, kind) for x, y, kind in spawns]
