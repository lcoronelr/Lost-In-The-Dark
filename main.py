"""
    """
    The main function initializes a Pygame window for a game called "Lost in the Dark", manages screens,
    handles events, updates the game state, and exits the game loop when needed.
    """
    Author : Luis Coronel
    The main function initializes a Pygame window for a game called "Lost in the Dark", manages screens,
    handles events, updates the game state, and exits when needed.
    """
import pygame
from screens import ScreenManager
from utils import RESOLUTION, UPSCALED

def main():
    # Initialize
    pygame.init()
    pygame.font.init()

    screen      = pygame.display.set_mode(list(map(int, UPSCALED)))
    drawSurface = pygame.Surface(list(map(int, RESOLUTION)))
    pygame.display.set_caption("Lost in the Dark")

    screenManager = ScreenManager()
    gameClock     = pygame.time.Clock()

    RUNNING = True

    while RUNNING:
        # --- draw ---
        screenManager.draw(drawSurface)
        pygame.transform.scale(drawSurface, list(map(int, UPSCALED)), screen)
        pygame.display.flip()

        # --- events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                RUNNING = False
            else:
                result = screenManager.handleEvent(event)
                if result == "exit":
                    RUNNING = False

        # --- update ---
        seconds = gameClock.tick(60) / 1000
        screenManager.update(seconds)

    pygame.quit()


if __name__ == "__main__":
    main()