import pygame

import gamevalues as gv
from weapon import Gun


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
    width, height = surface.get_size()
    font = pygame.font.Font(None, gv.UI_FONT_SIZE)
    small = pygame.font.Font(None, gv.UI_SMALL_FONT_SIZE)
    status = pygame.Rect(12, 12, 250, 148)
    pygame.draw.rect(surface, gv.UI_PANEL, status, border_radius=8)
    pygame.draw.rect(surface, gv.UI_BORDER, status, 1, border_radius=8)
    surface.blit(small.render("PILOT STATUS", True, gv.UI_ACCENT), (status.x + 14, status.y + 10))
    hearts = round(player.health / gv.PLAYER_HEALTH * gv.PLAYER_HEART_COUNT)
    for index in range(gv.PLAYER_HEART_COUNT):
        color = gv.HEART_COLOR if index < hearts else gv.HEART_EMPTY_COLOR
        pygame.draw.circle(surface, color, (status.x + 24 + index * 22, status.y + 37), 8)
    surface.blit(font.render(f"HP: {hearts} / {gv.PLAYER_HEART_COUNT}", True, gv.UI_TEXT), (status.x + 14, status.y + 52))
    surface.blit(small.render("HELD", True, gv.UI_MUTED), (status.x + 14, status.y + 82))
    surface.blit(font.render(player.current_weapon.name, True, gv.UI_TEXT), (status.x + 14, status.y + 98))
    if isinstance(player.current_weapon, Gun):
        ammo = player.current_weapon
        surface.blit(small.render(f"AMMO {ammo.ammo_current}/{ammo.ammo_reserve}", True, gv.UI_ACCENT), (status.x + 135, status.y + 82))
    if player.shield_charges:
        surface.blit(small.render(f"Shield: {player.shield_charges}", True, gv.UI_ACCENT), (status.x + 135, status.y + 105))
    timer_y = status.bottom + 8
    for name, remaining in player.active_powerups.items():
        surface.blit(small.render(f"{name}: {remaining:.1f}s", True, gv.UI_ACCENT), (status.x + 14, timer_y))
        timer_y += 20

    hotbar_y = height - 54
    hotbar_x = width // 2 - 80
    for index, weapon in enumerate(player.weapon_slots):
        slot = pygame.Rect(hotbar_x + index * 84, hotbar_y, 76, 42)
        pygame.draw.rect(surface, gv.UI_PANEL, slot, border_radius=5)
        pygame.draw.rect(surface, gv.UI_ACCENT if index == player.active_slot else gv.UI_BORDER, slot, 2, border_radius=5)
        surface.blit(small.render(f"{index + 1} {weapon.name[:8]}", True, gv.UI_TEXT), (slot.x + 6, slot.y + 12))

    panel = pygame.Rect(width - 250, 16, 234, 76)
    pygame.draw.rect(surface, gv.UI_PANEL, panel, border_radius=5)
    pygame.draw.rect(surface, gv.UI_BORDER, panel, 1, border_radius=5)
    surface.blit(small.render("OBJECTIVE", True, gv.UI_ACCENT), (panel.x + 12, panel.y + 10))
    surface.blit(small.render(objective.current, True, gv.UI_TEXT), (panel.x + 12, panel.y + 34))

    map_rect = pygame.Rect(width - 250, 104, 234, 84)
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
        story_box = pygame.Rect(width * 0.18, height - 72, width * 0.64, 52)
        pygame.draw.rect(surface, (10, 15, 27, 220), story_box, border_radius=8)
        pygame.draw.rect(surface, gv.UI_BORDER, story_box, 1, border_radius=8)
        surface.blit(story, (story_box.centerx - story.get_width() // 2, story_box.y + 17))
    if player.item_message_timer > 0:
        acquired = font.render(f"ITEM ACQUIRED  {player.item_message}", True, gv.UI_ACCENT)
        surface.blit(acquired, (width // 2 - acquired.get_width() // 2, height - 58))


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


class InventorySlot:
    SIZE = 64

    def __init__(self, item=None, label=""):
        self.item = item
        self.label = label
        self.rect = pygame.Rect(0, 0, self.SIZE, self.SIZE)
        self.hovered = False

    def draw(self, surface, font, active=False):
        color = (54, 67, 91) if active else ((46, 54, 75) if self.hovered else (29, 37, 56))
        border = gv.UI_ACCENT if active else gv.UI_BORDER
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, border, self.rect, 2 if active else 1, border_radius=5)
        if self.item:
            pygame.draw.rect(surface, gv.UI_ACCENT, self.rect.inflate(-16, -16), border_radius=4)
            text = font.render(self.item.name[:9], True, gv.UI_TEXT)
            surface.blit(text, (self.rect.centerx - text.get_width() // 2, self.rect.bottom - 18))
        else:
            text = font.render("empty", True, gv.UI_MUTED)
            surface.blit(text, (self.rect.centerx - text.get_width() // 2, self.rect.centery - 8))


class Inventory:
    STORAGE_SIZE = 20

    def __init__(self, player):
        self.player = player
        self.open = False
        self.equip_slots = [InventorySlot(player.weapon_slots[0], "Weapon 1"), InventorySlot(player.weapon_slots[1], "Weapon 2")]
        self.storage_slots = [InventorySlot() for _ in range(self.STORAGE_SIZE)]
        self.active_equip = player.active_slot
        self.drag_item = None
        self.drag_source = None

    def sync(self):
        self.active_equip = self.player.active_slot
        for index, item in enumerate(self.player.weapon_slots):
            self.equip_slots[index].item = item

    def toggle(self):
        self.open = not self.open

    def swap_equip(self):
        self.player.equip_slot(1 - self.player.active_slot)
        self.sync()

    def _layout(self, surface):
        width, height = surface.get_size()
        left = width // 2 - 250
        top = max(80, height // 2 - 170)
        for index, slot in enumerate(self.equip_slots):
            slot.rect.topleft = (left + 30, top + 55 + index * 100)
        grid_left = width // 2 + 20
        for index, slot in enumerate(self.storage_slots):
            slot.rect.topleft = (grid_left + (index % 5) * 78, top + 55 + (index // 5) * 78)

    def update_hover(self, pos, surface):
        self._layout(surface)
        for slot in self.equip_slots + self.storage_slots:
            slot.hovered = slot.rect.collidepoint(pos)

    def handle_mousedown(self, pos, surface):
        self._layout(surface)
        for kind, slots in (("equip", self.equip_slots), ("storage", self.storage_slots)):
            for index, slot in enumerate(slots):
                if slot.rect.collidepoint(pos) and slot.item:
                    self.drag_item = slot.item
                    self.drag_source = (kind, index)
                    slot.item = None
                    return

    def handle_mouseup(self, pos, surface):
        if self.drag_item is None:
            return
        self._layout(surface)
        targets = [("equip", index, slot) for index, slot in enumerate(self.equip_slots)] + [("storage", index, slot) for index, slot in enumerate(self.storage_slots)]
        for kind, index, slot in targets:
            if slot.rect.collidepoint(pos):
                old = slot.item
                slot.item = self.drag_item
                self.drag_item = None
                if kind == "equip" and slot.item:
                    self.player.weapon_slots[index] = slot.item
                    self.player.equip_slot(index)
                if old:
                    self._return_item(old)
                self.sync()
                return
        self._return_item(self.drag_item)
        self.drag_item = None

    def _return_item(self, item):
        for slot in self.storage_slots:
            if slot.item is None:
                slot.item = item
                return

    def draw(self, surface):
        self._layout(surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((5, 9, 18, 210))
        surface.blit(overlay, (0, 0))
        width, height = surface.get_size()
        panel = pygame.Rect(width // 2 - 390, max(35, height // 2 - 205), 780, 410)
        pygame.draw.rect(surface, gv.UI_PANEL, panel, border_radius=8)
        pygame.draw.rect(surface, gv.UI_ACCENT, panel, 2, border_radius=8)
        title = pygame.font.Font(None, 34).render("ARSENAL  |  TAB to close", True, gv.UI_TEXT)
        surface.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 16))
        font = pygame.font.Font(None, 18)
        for index, slot in enumerate(self.equip_slots):
            slot.draw(surface, font, index == self.player.active_slot)
        for slot in self.storage_slots:
            slot.draw(surface, font)
        hovered = next((slot for slot in self.equip_slots + self.storage_slots if slot.hovered and slot.item), None)
        if hovered:
            tooltip = pygame.Rect(hovered.rect.right + 10, hovered.rect.y, 250, 82)
            if tooltip.right > width:
                tooltip.right = hovered.rect.left - 10
            pygame.draw.rect(surface, gv.UI_PANEL, tooltip, border_radius=5)
            pygame.draw.rect(surface, gv.UI_ACCENT, tooltip, 1, border_radius=5)
            surface.blit(font.render(hovered.item.name, True, gv.UI_TEXT), (tooltip.x + 8, tooltip.y + 8))
            surface.blit(font.render(hovered.item.description, True, gv.UI_MUTED), (tooltip.x + 8, tooltip.y + 30))
            surface.blit(font.render(hovered.item.describe(), True, gv.UI_MUTED), (tooltip.x + 8, tooltip.y + 52))
        selected = self.player.current_weapon
        details = pygame.font.Font(None, 21).render(selected.describe(), True, gv.UI_MUTED)
        surface.blit(details, (panel.x + 30, panel.bottom - 32))


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
