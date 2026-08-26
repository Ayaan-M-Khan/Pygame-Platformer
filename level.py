# Import Statements
import math
import pygame
import gamevalues as gv

# Create Platform Classes to manange different platforms and the level structure
class Platform:
    def __init__(self, x, y, width, height=None, kind="solid", section=""):
        self.rect = pygame.Rect(x, y, width, height or gv.PLATFORM_HEIGHT)
        self.kind = kind
        self.section = section
        self.active = True

    @property
    def can_pass_through(self):
        return self.kind == "one_way"

    def update(self, dt):
        return None

    def draw(self, surface, camera_x, camera_y):
        if not self.active:
            return
        visible_rect = self.rect.move(-round(camera_x), -round(camera_y))
        color = gv.PLATFORM_COLORS.get(self.kind, gv.PLATFORM_COLOR)
        pygame.draw.rect(surface, color, visible_rect, border_radius=4)


class MovingPlatform(Platform):
    def __init__(self, x, y, width, height, axis, distance, speed, section):
        super().__init__(x, y, width, height, "moving", section)
        self.start_position = pygame.Vector2(x, y)
        self.axis = axis
        self.distance = distance
        self.speed = speed
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt * self.speed
        offset = pygame.Vector2(1, 0) if self.axis == "x" else pygame.Vector2(0, 1)
        amount = (math.sin(self.elapsed) + 1) * 0.5 * self.distance
        self.rect.topleft = self.start_position + offset * amount


class BreakablePlatform(Platform):
    def __init__(self, x, y, width, section):
        super().__init__(x, y, width, gv.PLATFORM_HEIGHT, "breakable", section)
        self.break_timer = None

    def update(self, dt):
        if self.break_timer is not None:
            self.break_timer -= dt
            if self.break_timer <= 0:
                self.active = False

    def start_breaking(self):
        if self.break_timer is None:
            self.break_timer = gv.BREAKABLE_PLATFORM_DELAY


class HazardPlatform(Platform):
    def __init__(self, x, y, width, section):
        super().__init__(x, y, width, gv.PLATFORM_HEIGHT, "hazard", section)


class Level:
    def __init__(self):
        self.width = gv.WORLD_WIDTH
        self.height = gv.WORLD_HEIGHT
        self.platforms = self._create_platforms()
        self.enemy_spawns = [
            (880, 590, "walker"),
            (1160, 470, "jumper"),
            (1510, 560, "walker"),
            (1740, 420, "shooter"),
            (2170, 500, "walker"),
            (2530, 440, "jumper"),
            (2920, 570, "heavy"),
            (3290, 470, "shooter"),
            (3650, 570, "walker"),
            (4020, 500, "jumper"),
            (4580, 570, "boss"),
        ]
        self.powerup_spawns = [
            (420, 490, "health"),
            (1530, 330, "dash"),
            (2640, 250, "double_jump"),
            (3440, 390, "shield"),
        ]
        self.goal = pygame.Rect(4880, 500, 60, 180)

    def _create_platforms(self):
        platforms = []
        add = lambda x, y, width, section, kind="solid": platforms.append(
            Platform(x, y, width, gv.PLATFORM_HEIGHT, kind, section)
        )
        y = 580 + 50
        add(0, y, 720, "starting area")
        add(760, y, 520, "first challenge")
        add(1320, y, 620, "power-up approach")
        add(1980, y, 550, "combat section")
        add(2580, y, 540, "hazard section")
        add(3170, y, 620, "advanced platforming")
        add(3840, y, 1140, "boss approach")

        for platform in (
            (180, 570, 180, "starting area"),
            (470, 500, 150, "starting area"),
            (820, 570, 170, "first challenge"),
            (1060, 490, 160, "first challenge"),
            (1370, 560, 170, "power-up approach"),
            (1440, 400, 180, "power-up approach"),
            (1660, 500, 180, "power-up approach", "one_way"),
            (2040, 560, 170, "combat section"),
            (2260, 450, 180, "combat section"),
            (2470, 360, 150, "combat section"),
            (2670, 520, 170, "hazard section"),
            (2900, 430, 170, "hazard section"),
            (3190, 550, 160, "advanced platforming"),
            (3430, 450, 180, "advanced platforming"),
            (3690, 360, 170, "advanced platforming"),
            (3970, 550, 180, "boss approach"),
            (4250, 470, 170, "boss approach"),
        ):
            add(*platform)

        platforms.append(MovingPlatform(1840, 560, 130, gv.PLATFORM_HEIGHT, "y", 100, 1.4, "power-up approach"))
        platforms.append(BreakablePlatform(2780, 350, 130, "hazard section"))
        platforms.append(BreakablePlatform(3080, 300, 130, "hazard section"))
        platforms.append(HazardPlatform(2710, 656, 150, "hazard section"))
        platforms.append(HazardPlatform(3020, 656, 110, "hazard section"))
        platforms.append(Platform(4430, 680, 500, gv.PLATFORM_HEIGHT, "boss_floor", "boss arena"))
        platforms.append(Platform(4430, 500, gv.PLATFORM_HEIGHT, 180, "boss_floor", "boss arena"))
        platforms.append(Platform(4930, 500, gv.PLATFORM_HEIGHT, 180, "boss_floor", "boss arena"))
        return platforms

    def update(self, dt):
        for platform in self.platforms:
            platform.update(dt)

    def collision_rects(self):
        return [platform for platform in self.platforms if platform.active]

    def section_at(self, x):
        for platform in self.platforms:
            if platform.rect.left <= x <= platform.rect.right and platform.section:
                return platform.section
        return "open route"

    def draw(self, surface, camera_x, camera_y):
        for platform in self.platforms:
            platform.draw(surface, camera_x, camera_y)
        goal = self.goal.move(-round(camera_x), -round(camera_y))
        pygame.draw.rect(surface, gv.GOAL_COLOR, goal, 4)
