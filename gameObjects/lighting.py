"""
LightingOverlay — renders darkness with light circles for the player torch,
lit wall torches, and active fireballs.
reference to: https://www.youtube.com/watch?v=NGFk44fY0O4
and https://stackoverflow.com/questions/31038285/python-pygame-game-lighting
"""
import pygame
from utils import RESOLUTION, vec
from gameObjects.drawable import Drawable

class LightingOverlay:

    def __init__(self):
        self._surface = pygame.Surface(list(map(int, RESOLUTION)), pygame.SRCALPHA)
        # Pre-build light gradient surfaces per radius (cached)
        self._cache = {}

    def draw(self, drawSurface, torch, wallTorches=None, fireballs=None):
        # Full opaque darkness
        self._surface.fill((0, 0, 0, 255))

        # Blit each light using BLEND_RGBA_MIN so overlaps merge cleanly
        self._blitLight(torch.position, int(torch.lightRadius))

        if wallTorches:
            for wt in wallTorches:
                if wt.lit:
                    self._blitLight(wt.position, int(wt.lightRadius))

        if fireballs:
            for fb in fireballs:
                if fb.active:
                    self._blitLight(fb.position, int(fb.lightRadius))

        drawSurface.blit(self._surface, (0, 0))

    def _buildLight(self, r):
        """Build and cache a radial gradient surface for radius r."""
        size = r * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 255))   # start fully dark
        for i in range(r, 0, -1):
            alpha = int(255 * (i / r) ** 2)
            pygame.draw.circle(surf, (0, 0, 0, alpha), (r, r), i)
        pygame.draw.circle(surf, (0, 0, 0, 0), (r, r), max(1, r // 4))
        return surf

    def _blitLight(self, position, r):
        if r <= 0:
            return
        if r not in self._cache:
            self._cache[r] = self._buildLight(r)
        surf   = self._cache[r]
        centre = position - Drawable.CAMERA_OFFSET
        cx, cy = int(centre[0]), int(centre[1])
        # BLEND_RGBA_MIN keeps the lower (more transparent) alpha value per pixel
        # so where two lights overlap the overlap stays bright instead of going dark
        self._surface.blit(surf, (cx - r, cy - r),special_flags=pygame.BLEND_RGBA_MIN)