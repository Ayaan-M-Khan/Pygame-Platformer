#Import Statements
import pygame

#Import Files
import math
import gamevalues as gv
from enemy import create_enemies
from level import Level
from player import Player
from powerup import create_powerups
from ui import ObjectiveManager, draw_hud, draw_inventory

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
	projectiles = []
	camera = Camera()
	shoot_cooldown = 0.0
	player.invulnerability_timer = 0.0
	message = "Reach the beacon"
	inventory_open = False
	running = True
	frame_count = 0

	while running and (max_frames is None or frame_count < max_frames):
		dt = clock.tick(gv.TARGET_FPS) / 1000.0
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_TAB:
					inventory_open = not inventory_open
				elif event.key == pygame.K_1:
					player.equip_slot(0)
				elif event.key == pygame.K_2:
					player.equip_slot(1)
				elif event.key == pygame.K_z:
					attack = player.attack(pygame.time.get_ticks())
					if attack and attack["kind"] == "ranged":
						projectiles.append(spawn_projectile(player, attack["direction"], attack["damage"]))
				elif event.key == pygame.K_e:
					for chest in level.weapon_chests:
						if chest.rect.inflate(50, 40).colliderect(player.rect):
							weapon = chest.open(player)
							if weapon:
								objective.complete("Reach the ancient ruins", f"The {weapon.name} answers your hand. The ruins lie ahead.")
								message = f"ITEM ACQUIRED  {weapon.name}"
							break

		keys = pygame.key.get_pressed()
		level.update(dt)
		player.update(keys, level.collision_rects(), dt)
		player.rect.left = max(0, player.rect.left)
		player.rect.right = min(level.width, player.rect.right)
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
				if player.attack_effect and player.attack_effect["rect"].colliderect(enemy.rect) and not enemy.hit_by_attack:
					enemy.take_damage(player.attack_effect["damage"])
					enemy.rect.x += player.attack_effect["knockback"] * player.facing
					enemy.hit_by_attack = True

		for platform in level.platforms:
			if platform.kind == "breakable" and platform.active and player.rect.bottom == platform.rect.top and player.rect.colliderect(platform.rect):
				platform.start_breaking()
			if platform.active and platform.kind == "hazard" and player.rect.colliderect(platform.rect) and player.invulnerability_timer <= 0:
				player.health -= gv.HAZARD_DAMAGE
				player.invulnerability_timer = gv.PLAYER_INVULNERABILITY_TIME

		for projectile in projectiles[:]:
			projectile["rect"].x += round(projectile["velocity"] * dt)
			if not pygame.Rect(0, 0, level.width, level.height).colliderect(projectile["rect"]):
				projectiles.remove(projectile)
				continue
			if projectile["owner"] == "player":
				for enemy in enemies:
					if enemy.alive and projectile["rect"].colliderect(enemy.rect):
						enemy.take_damage(projectile["damage"])
						projectiles.remove(projectile)
						break
			elif projectile["rect"].colliderect(player.rect) and player.invulnerability_timer <= 0:
				player.health -= projectile["damage"]
				player.invulnerability_timer = gv.PLAYER_INVULNERABILITY_TIME
				projectiles.remove(projectile)

		for powerup in powerups:
			if not powerup.collected and player.rect.colliderect(powerup.rect):
				powerup.collected = True
				if powerup.kind == "dash":
					player.has_dash = True
				elif powerup.kind == "double_jump":
					player.extra_jumps = 1
				elif powerup.kind == "health":
					player.health = min(gv.PLAYER_HEALTH, player.health + 40)
				elif powerup.kind == "shield":
					player.shield_charges += 2
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
		for projectile in projectiles:
			pygame.draw.rect(screen, (255, 235, 130), projectile["rect"].move(-round(camera.x), -round(camera.y)))
		if player.attack_effect:
			attack_rect = player.attack_effect["rect"].move(-round(camera.x), -round(camera.y))
			pygame.draw.rect(screen, (246, 215, 126), attack_rect, 3)
		player.draw(screen, camera.x, camera.y)
		draw_hud(screen, player, level, enemies, objective, pygame.time.get_ticks())
		if inventory_open:
			draw_inventory(screen, player)
		font = pygame.font.Font(None, 30)
		screen.blit(font.render(message, True, (245, 239, 211)), (18, gv.SCREEN_HEIGHT - 38))
		pygame.display.flip()
		frame_count += 1

	pygame.quit()


if __name__ == "__main__":
	run()



