"""
LightingOverlay — renders darkness with light circles for the player torch
and any lit wall torches.
"""
import pygame
from utils import RESOLUTION, vec
from gameObjects.drawable import Drawable

class LightingOverlay:
    # reference to: https://www.youtube.com/watch?v=NGFk44fY0O4
    # and https://stackoverflow.com/questions/31038285/python-pygame-game-lighting

    def __init__(self):
        self._surface = pygame.Surface(list(map(int, RESOLUTION)), pygame.SRCALPHA)

    def draw(self, drawSurface, torch, wallTorches=None):
        self._surface.fill((0, 0, 0, RESOLUTION[1]))   # near-black darkness

        # Player torch light
        self._drawLight(torch.position, torch.lightRadius)

        # Lit wall torches
        if wallTorches:
            for wt in wallTorches:
                if wt.lit:
                    self._drawLight(wt.position, wt.lightRadius)

        drawSurface.blit(self._surface, (0, 0))

    def _drawLight(self, position, radius):
        """Punch a light circle into the darkness surface."""
        centre = position - Drawable.CAMERA_OFFSET
        cx, cy = int(centre[0]), int(centre[1])
        r      = int(radius)

        for i in range(r, 0, -1):
            alpha = int(240 * (i / r) ** 1.8)
            pygame.draw.circle(self._surface, (0, 0, 0, alpha), (cx, cy), i)

        core = max(1, r // 4)
        pygame.draw.circle(self._surface, (0, 0, 0, 0), (cx, cy), core)