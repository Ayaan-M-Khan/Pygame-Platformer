#Import Statements
import pygame

#Import Files
import math
import gamevalues as gv
from enemy import create_enemies
from level import Level
from player import Player
from powerup import create_powerups
from ui import Inventory, ObjectiveManager, draw_hud, draw_pause_menu
from weapon import Bullet, Coin, Gun, Sword

#Create the Camera angle for the player using the camera class and player values
class Camera:
	def __init__(self):
		self.x = 0.0
		self.y = 100.0

	def follow(self, target, level, dt):
		target_x = target.centerx - gv.SCREEN_WIDTH * 0.38
		target_y = target.centery - gv.SCREEN_HEIGHT * 0.55
		max_x = level.width - gv.SCREEN_WIDTH
		max_y = level.height - gv.SCREEN_HEIGHT
		self.x += (max(0, min(max_x, target_x)) - self.x) * min(1, dt * 7)
		self.y += (max(0, min(max_y, target_y)) - self.y) * min(1, dt * 7)


def spawn_projectile(player, direction, damage=gv.PROJECTILE_DAMAGE):
	return {
		"rect": pygame.Rect(player.rect.centerx, player.rect.centery - 4, 16, 8),
		"velocity": direction * gv.PROJECTILE_SPEED,
		"damage": damage,
		"owner": "player",
	}


def projectile_hits_terrain(projectile, platforms):
	return any(platform.active and projectile["rect"].colliderect(platform.rect) for platform in platforms)


#Main Game Loop
def run(max_frames=None):
	pygame.init()
	screen = pygame.display.set_mode((gv.SCREEN_WIDTH, gv.SCREEN_HEIGHT))
	pygame.display.set_caption(gv.WINDOW_TITLE)
	clock = pygame.time.Clock()
	level = Level()
	player = Player(*gv.START_POSITION)
	player.x, player.y = gv.RESPAWN_POSITION
	enemies = create_enemies(level.enemy_spawns)
	powerups = create_powerups(level.powerup_spawns)
	objective = ObjectiveManager()
	inventory_ui = Inventory(player)
	projectiles = []
	coins = []
	camera = Camera()
	shoot_cooldown = 0.0
	player.invulnerability_timer = 0.0
	message = "Reach the beacon"
	inventory_open = False
	paused = False
	running = True
	frame_count = 0

	while running and (max_frames is None or frame_count < max_frames):
		dt = clock.tick(gv.TARGET_FPS) / 1000.0
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key in (pygame.K_p, pygame.K_ESCAPE):
					paused = not paused
					continue
				if event.key == pygame.K_TAB:
					inventory_ui.toggle()
					inventory_open = inventory_ui.open
				elif event.key == pygame.K_1:
					player.equip_slot(0)
				elif event.key == pygame.K_2:
					player.equip_slot(1)
				elif event.key == pygame.K_z:
					result = player.attack(pygame.time.get_ticks())
					if isinstance(result, list):
						projectiles.extend(result)
				elif event.key == pygame.K_r and isinstance(player.current_weapon, Gun):
					player.current_weapon.reload()
				elif event.key == pygame.K_e:
					for chest in level.weapon_chests:
						if chest.rect.inflate(50, 40).colliderect(player.rect):
							weapon = chest.open(player)
							if weapon:
								coins.extend(chest.coin_drops)
								objective.complete("Reach the ancient ruins", f"The {weapon.name} answers your hand. The ruins lie ahead.")
								message = f"ITEM ACQUIRED  {weapon.name}"
							break
			elif event.type == pygame.MOUSEMOTION and inventory_ui.open:
				inventory_ui.update_hover(event.pos, screen)
			elif event.type == pygame.MOUSEBUTTONDOWN and inventory_ui.open:
				inventory_ui.handle_mousedown(event.pos, screen)
			elif event.type == pygame.MOUSEBUTTONUP and inventory_ui.open:
				inventory_ui.handle_mouseup(event.pos, screen)

		inventory_ui.sync()
		if paused:
			screen.fill(gv.BACKGROUND_COLOR)
			level.draw(screen, camera.x, camera.y)
			player.draw(screen, camera.x, camera.y)
			draw_hud(screen, player, level, enemies, objective, pygame.time.get_ticks())
			draw_pause_menu(screen, player)
			pygame.display.flip()
			frame_count += 1
			continue

		if inventory_ui.open:
			screen.fill(gv.BACKGROUND_COLOR)
			level.draw(screen, camera.x, camera.y)
			player.draw(screen, camera.x, camera.y)
			inventory_ui.draw(screen)
			pygame.display.flip()
			frame_count += 1
			continue

		keys = pygame.key.get_pressed()
		level.update(dt, camera.x)
		player.update(keys, level.collision_rects(), dt)
		player.rect.left = max(0, player.rect.left)
		player.rect.right = min(level.width, player.rect.right)
		player.update_aim(pygame.mouse.get_pos(), camera.x, camera.y)
		if keys[pygame.K_f] or pygame.mouse.get_pressed()[0]:
			result = player.attack(pygame.time.get_ticks())
			if isinstance(result, list):
				projectiles.extend(result)
		shoot_cooldown = max(0.0, shoot_cooldown - dt)
		for enemy in enemies:
			if enemy.alive:
				enemy.hit_by_attack = False
				enemy_projectile = enemy.update(dt, level.collision_rects(), player.rect)
				if enemy_projectile is not None:
					projectiles.append(enemy_projectile)
				if enemy.rect.colliderect(player.rect) and player.invulnerability_timer <= 0:
					if player.shield_charges:
						player.shield_charges -= 1
					else:
						player.health -= gv.CONTACT_DAMAGE
					player.invulnerability_timer = gv.PLAYER_INVULNERABILITY_TIME
		if isinstance(player.current_weapon, Sword):
			for enemy in enemies:
				if enemy.alive:
					for hit in player.current_weapon.check_hits(player.rect, [enemy], pygame.time.get_ticks()):
						hit.take_damage(player.current_weapon.damage)
						hit.rect.x += player.current_weapon.knockback * player.facing

		for platform in level.platforms:
			if platform.kind == "breakable" and platform.active and player.rect.bottom == platform.rect.top and player.rect.colliderect(platform.rect):
				platform.start_breaking()
			if platform.active and platform.kind == "hazard" and player.rect.colliderect(platform.rect) and player.invulnerability_timer <= 0:
				player.health -= gv.HAZARD_DAMAGE
				player.invulnerability_timer = gv.PLAYER_INVULNERABILITY_TIME

		for projectile in projectiles[:]:
			projectile.update(dt, level.collision_rects(), level.width)
			if not projectile.alive:
				projectiles.remove(projectile)
				continue
			if getattr(projectile, "owner", "player") == "player":
				for enemy in enemies:
					if enemy.alive and projectile.rect.colliderect(enemy.rect):
						enemy.take_damage(projectile.damage)
						projectiles.remove(projectile)
						break
			elif projectile.rect.colliderect(player.rect) and player.invulnerability_timer <= 0:
				player.health -= projectile.damage
				player.invulnerability_timer = gv.PLAYER_INVULNERABILITY_TIME
				projectiles.remove(projectile)

		for coin in coins[:]:
			coin.update(dt, level.collision_rects())
			if coin.position.distance_to(player.rect.center) < 24:
				coins.remove(coin)

		for powerup in powerups:
			if not powerup.collected and player.rect.colliderect(powerup.rect):
				powerup.collected = True
				if powerup.kind == "dash":
					player.has_dash = True
					player.active_powerups["Dash"] = gv.POWERUP_DURATION
				elif powerup.kind == "double_jump":
					player.extra_jumps = 1
					player.active_powerups["Double Jump"] = gv.POWERUP_DURATION
				elif powerup.kind == "health":
					player.health = min(gv.PLAYER_HEALTH, player.health + 40)
				elif powerup.kind == "shield":
					player.shield_charges += 2
					player.active_powerups["Shield"] = gv.POWERUP_DURATION
				message = f"Collected {powerup.kind.replace('_', ' ')}"
		objective.update(dt)
		for chest in level.weapon_chests:
			if chest.opened and objective.current == "Find the Ember Blade":
				objective.complete("Reach the ancient ruins", "The new weapon is ready. Push toward the ancient ruins.")

		if player.y > level.height + 100 or player.health <= 0:
			player.x, player.y = gv.RESPAWN_POSITION
			player.vel_x = player.vel_y = 0
			player.health = gv.PLAYER_HEALTH

		boss_alive = any(enemy.alive and enemy.kind == "boss" for enemy in enemies)
		if player.rect.centerx >= 3000 and objective.current == "Reach the ancient ruins":
			objective.complete("Defeat the Red Warden", "The arena guardian has awakened. Break through its crimson guard.")
		if not boss_alive and objective.current == "Defeat the Red Warden":
			objective.complete("Reach the beacon", "The guardian falls. Carry the ember light to the beacon.")
		if player.rect.colliderect(level.goal) and not boss_alive:
			message = "Beacon reached - level complete!"
		camera.follow(player.rect, level, dt)

		screen.fill(gv.BACKGROUND_COLOR)
		level.draw(screen, camera.x, camera.y)
		for chest in level.weapon_chests:
			chest.draw(screen, camera.x, camera.y)
		for powerup in powerups:
			powerup.draw(screen, camera.x, camera.y)
		for enemy in enemies:
			if enemy.alive:
				enemy.draw(screen, camera.x, camera.y)
		for coin in coins:
			coin.draw(screen, camera.x, camera.y)
		for projectile in projectiles:
			projectile.draw(screen, camera.x, camera.y)
		player.draw(screen, camera.x, camera.y)
		draw_hud(screen, player, level, enemies, objective, pygame.time.get_ticks())
		if inventory_open:
			inventory_ui.draw(screen)
		font = pygame.font.Font(None, 30)
		screen.blit(font.render(message, True, (245, 239, 211)), (18, gv.SCREEN_HEIGHT - 38))
		pygame.display.flip()
		frame_count += 1

	pygame.quit()


if __name__ == "__main__":
	run()



