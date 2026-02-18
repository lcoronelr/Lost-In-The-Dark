import pygame
from . import Drawable
from .torch    import Torch
from .lighting import LightingOverlay
from .hud      import HUD
from utils     import vec, RESOLUTION

# Simple placeholder dungeon tile colors
FLOOR_COLOR = (40, 50, 10)
WALL_COLOR  = (20, 18, 16)

class GameEngine(object):
    """
    Top-level game manager for Lost in the Dark.

    Currently sets up:
      - A placeholder dungeon floor (solid color)
      - The Torch player
      - The darkness/lighting overlay
      - HUD
    """

    WORLD_SIZE = RESOLUTION   # expand this when you add a real map

    def __init__(self):
        self.worldSize  = vec(*self.WORLD_SIZE)

        # Placeholder background — replace with actual map later 
        self._background = pygame.Surface(list(map(int, RESOLUTION)))
        self._background.fill(FLOOR_COLOR)
        # Draw a simple border wall so movement feels bounded
        pygame.draw.rect(self._background, WALL_COLOR,
                         pygame.Rect(0, 0, int(RESOLUTION[0]), int(RESOLUTION[1])), 8)

        # Game objects
        centre = RESOLUTION // 2
        self.torch    = Torch(position=centre)
        self.lighting = LightingOverlay()
        self.hud      = HUD()

    def draw(self, drawSurface):
        drawSurface.blit(self._background, (0, 0))
        self.torch.draw(drawSurface)
        self.lighting.draw(drawSurface, self.torch)
        self.hud.draw(drawSurface, self.torch)

    def handleEvent(self, event):
        self.torch.handleEvent(event)

    def update(self, seconds):
        self.torch.update(seconds)
        Drawable.updateOffset(self.torch, self.worldSize)