import pygame

import gamevalues as gv


class ObjectiveManager:
    def __init__(self):
        self.current = "Find the Ember Blade"
        self.story = "The path ahead is sealed. Find a weapon powerful enough to continue."
        self.story_timer = gv.STORY_MESSAGE_DURATION

    def complete(self, objective, story):
        if self.current != objective:
            self.current = objective
            self.story = story
            self.story_timer = gv.STORY_MESSAGE_DURATION

    def update(self, dt):
        self.story_timer = max(0.0, self.story_timer - dt)


def draw_bar(surface, rect, value, maximum, fill_color):
    pygame.draw.rect(surface, gv.UI_BAR_BACKGROUND, rect, border_radius=3)
    fill = rect.copy()
    fill.width = round(rect.width * max(0, min(value / maximum, 1))) if maximum else 0
    pygame.draw.rect(surface, fill_color, fill, border_radius=3)
    pygame.draw.rect(surface, gv.UI_BORDER, rect, 1, border_radius=3)


def draw_hud(surface, player, level, enemies, objective, now):
    font = pygame.font.Font(None, gv.UI_FONT_SIZE)
    small = pygame.font.Font(None, gv.UI_SMALL_FONT_SIZE)
    hearts = round(player.health / gv.PLAYER_HEALTH * gv.PLAYER_HEART_COUNT)
    for index in range(gv.PLAYER_HEART_COUNT):
        color = gv.HEART_COLOR if index < hearts else gv.HEART_EMPTY_COLOR
        pygame.draw.circle(surface, color, (24 + index * 22, 24), 8)
    surface.blit(font.render(f"HP: {hearts} / {gv.PLAYER_HEART_COUNT}", True, gv.UI_TEXT), (16, 42))
    surface.blit(small.render("HELD", True, gv.UI_MUTED), (16, 72))
    surface.blit(font.render(player.current_weapon.name, True, gv.UI_TEXT), (16, 88))
    if player.shield_charges:
        surface.blit(small.render(f"Shield charges: {player.shield_charges}", True, gv.UI_ACCENT), (16, 116))
    timer_y = 140
    for name, remaining in player.active_powerups.items():
        surface.blit(small.render(f"{name}: {remaining:.1f}s", True, gv.UI_ACCENT), (16, timer_y))
        timer_y += 20

    panel = pygame.Rect(gv.SCREEN_WIDTH - 250, 16, 234, 76)
    pygame.draw.rect(surface, gv.UI_PANEL, panel, border_radius=5)
    pygame.draw.rect(surface, gv.UI_BORDER, panel, 1, border_radius=5)
    surface.blit(small.render("OBJECTIVE", True, gv.UI_ACCENT), (panel.x + 12, panel.y + 10))
    surface.blit(small.render(objective.current, True, gv.UI_TEXT), (panel.x + 12, panel.y + 34))

    map_rect = pygame.Rect(gv.SCREEN_WIDTH - 250, 104, 234, 84)
    pygame.draw.rect(surface, gv.UI_PANEL, map_rect, border_radius=5)
    pygame.draw.rect(surface, gv.UI_BORDER, map_rect, 1, border_radius=5)
    surface.blit(small.render("MAP", True, gv.UI_ACCENT), (map_rect.x + 12, map_rect.y + 8))
    map_y = map_rect.y + 51
    pygame.draw.line(surface, gv.UI_MUTED, (map_rect.x + 12, map_y), (map_rect.right - 12, map_y), 2)
    for platform in level.platforms:
        if platform.rect.width > 120:
            x = map_rect.x + 12 + round(platform.rect.centerx / level.width * (map_rect.width - 24))
            pygame.draw.rect(surface, gv.UI_MUTED, (x, map_y - 5, 5, 10))
    player_x = map_rect.x + 12 + round(player.rect.centerx / level.width * (map_rect.width - 24))
    pygame.draw.circle(surface, gv.HEART_COLOR, (player_x, map_y), 5)
    boss_x = map_rect.x + 12 + round(4580 / level.width * (map_rect.width - 24))
    pygame.draw.circle(surface, gv.BOSS_COLOR, (boss_x, map_y), 5)

    boss = next((enemy for enemy in enemies if enemy.is_boss and enemy.alive), None)
    if boss:
        title = font.render(boss.name, True, gv.BOSS_COLOR)
        surface.blit(title, (gv.SCREEN_WIDTH // 2 - title.get_width() // 2, 14))
        bar = pygame.Rect(gv.SCREEN_WIDTH // 2 - 180, 44, 360, 14)
        draw_bar(surface, bar, boss.health, boss.max_health, gv.BOSS_COLOR)
        text = small.render(f"{max(0, boss.health)} / {boss.max_health}", True, gv.UI_TEXT)
        surface.blit(text, (gv.SCREEN_WIDTH // 2 - text.get_width() // 2, 62))

    if objective.story_timer > 0:
        story = small.render(f'"{objective.story}"', True, gv.UI_TEXT)
        surface.blit(story, (gv.SCREEN_WIDTH // 2 - story.get_width() // 2, gv.SCREEN_HEIGHT - 28))
    if player.item_message_timer > 0:
        acquired = font.render(f"ITEM ACQUIRED  {player.item_message}", True, gv.UI_ACCENT)
        surface.blit(acquired, (gv.SCREEN_WIDTH // 2 - acquired.get_width() // 2, gv.SCREEN_HEIGHT - 58))


def draw_inventory(surface, player):
    overlay = pygame.Surface((gv.SCREEN_WIDTH, gv.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 9, 18, 150))
    surface.blit(overlay, (0, 0))
    panel = pygame.Rect(
        (gv.SCREEN_WIDTH - gv.INVENTORY_PANEL_WIDTH) // 2,
        (gv.SCREEN_HEIGHT - gv.INVENTORY_PANEL_HEIGHT) // 2,
        gv.INVENTORY_PANEL_WIDTH,
        gv.INVENTORY_PANEL_HEIGHT,
    )
    pygame.draw.rect(surface, gv.UI_PANEL, panel, border_radius=8)
    pygame.draw.rect(surface, gv.UI_ACCENT, panel, 2, border_radius=8)
    title_font = pygame.font.Font(None, 32)
    item_font = pygame.font.Font(None, 22)
    surface.blit(title_font.render(gv.INVENTORY_TITLE, True, gv.UI_TEXT), (panel.x + 18, panel.y + 14))
    for slot, weapon in enumerate(player.weapon_slots):
        slot_rect = pygame.Rect(panel.x + 22 + slot * (gv.INVENTORY_SLOT_SIZE + 20), panel.y + 58, gv.INVENTORY_SLOT_SIZE, 125)
        selected = slot == player.active_slot
        pygame.draw.rect(surface, (53, 62, 79) if selected else (30, 38, 55), slot_rect, border_radius=5)
        pygame.draw.rect(surface, gv.UI_ACCENT if selected else gv.UI_BORDER, slot_rect, 2, border_radius=5)
        surface.blit(item_font.render(f"{slot + 1}", True, gv.UI_ACCENT), (slot_rect.x + 10, slot_rect.y + 8))
        surface.blit(item_font.render(weapon.name, True, gv.UI_TEXT), (slot_rect.x + 10, slot_rect.y + 38))
        surface.blit(item_font.render(weapon.describe(), True, gv.UI_MUTED), (slot_rect.x + 10, slot_rect.y + 68))
        if slot_rect.collidepoint(pygame.mouse.get_pos()):
            tooltip = pygame.Rect(slot_rect.right + 10, slot_rect.y, 210, 74)
            pygame.draw.rect(surface, gv.UI_PANEL, tooltip, border_radius=5)
            pygame.draw.rect(surface, gv.UI_BORDER, tooltip, 1, border_radius=5)
            surface.blit(item_font.render(weapon.description, True, gv.UI_TEXT), (tooltip.x + 8, tooltip.y + 10))
            surface.blit(item_font.render(weapon.describe(), True, gv.UI_MUTED), (tooltip.x + 8, tooltip.y + 38))


def draw_pause_menu(surface, player):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((5, 9, 18, 190))
    surface.blit(overlay, (0, 0))
    width, height = surface.get_size()
    panel = pygame.Rect(width * 0.25, height * 0.2, width * 0.5, height * 0.6)
    pygame.draw.rect(surface, gv.UI_PANEL, panel, border_radius=8)
    pygame.draw.rect(surface, gv.UI_ACCENT, panel, 2, border_radius=8)
    title = pygame.font.Font(None, 42).render("PAUSED", True, gv.UI_TEXT)
    surface.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 25))
    text = pygame.font.Font(None, 25)
    lines = ["Press P or Escape to resume", "Tab: loadout", f"Equipped: {player.current_weapon.name}"]
    for index, line in enumerate(lines):
        rendered = text.render(line, True, gv.UI_MUTED)
        surface.blit(rendered, (panel.centerx - rendered.get_width() // 2, panel.y + 105 + index * 34))
