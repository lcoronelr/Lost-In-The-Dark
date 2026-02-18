import pygame
from gameObjects import GameEngine
from utils import RESOLUTION, UPSCALED

def main():
    #Initialize the module
    pygame.init()
    
    pygame.font.init()
    
    
    #Get the screen and set a title
    screen      = pygame.display.set_mode(list(map(int, UPSCALED)))
    drawSurface = pygame.Surface(list(map(int, RESOLUTION)))
    pygame.display.set_caption("Lost in the Dark")

    gameEngine = GameEngine()
    gameClock  = pygame.time.Clock()

    RUNNING = True
    
    while RUNNING:
        #---draw---
        gameEngine.draw(drawSurface)
        pygame.transform.scale(drawSurface, list(map(int, UPSCALED)), screen)
        pygame.display.flip()
        gameClock = pygame.time.Clock()
        
        # events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                RUNNING = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                RUNNING = False
            else:
                gameEngine.handleEvent(event)

        # --- update ---
        seconds = gameClock.tick(60) / 1000
        gameEngine.update(seconds)

    pygame.quit()


if __name__ == "__main__":
    main()