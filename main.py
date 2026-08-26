import gamevalues as gv
import pygame

from player import Player


def create_platforms():
	return [
		pygame.Rect(0, 500, gv.SCREEN_WIDTH, gv.PLATFORM_HEIGHT),
		pygame.Rect(180, 410, 180, gv.PLATFORM_HEIGHT),
		pygame.Rect(450, 330, 190, gv.PLATFORM_HEIGHT),
		pygame.Rect(720, 420, 160, gv.PLATFORM_HEIGHT),
	]


def draw_platforms(surface, platforms):
	for platform in platforms:
		pygame.draw.rect(surface, gv.PLATFORM_COLOR, platform, border_radius=4)


def run(max_frames=None):
	pygame.init()
	screen = pygame.display.set_mode((gv.SCREEN_WIDTH, gv.SCREEN_HEIGHT))
	pygame.display.set_caption(gv.WINDOW_TITLE)
	clock = pygame.time.Clock()
	platforms = create_platforms()
	player = Player(*gv.START_POSITION)
	running = True
	frame_count = 0

	while running and (max_frames is None or frame_count < max_frames):
		dt = clock.tick(gv.TARGET_FPS) / 1000.0
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		player.update(pygame.key.get_pressed(), platforms, dt)

		screen.fill(gv.BACKGROUND_COLOR)
		draw_platforms(screen, platforms)
		player.draw(screen)
		pygame.display.flip()
		frame_count += 1

	pygame.quit()


if __name__ == "__main__":
	run()



