import pygame
from . import Drawable
from .torch    import Torch
from .lighting import LightingOverlay
from .hud      import HUD
from .tilemap  import TileMap
from utils     import vec, RESOLUTION
from os.path   import join, dirname, abspath

# 
_HERE       = dirname(abspath(__file__))
_PROJECT    = dirname(_HERE)

# Spawn point 
SPAWN_X = 624
SPAWN_Y = 380


class GameEngine(object):
    """
    Top-level game manager for Lost in the Dark.
    """

    def __init__(self):
        # Load the tile map
        self.tilemap  = TileMap(join(_PROJECT, "maps", "level1.tmj"))
        self.worldSize = self.tilemap.getSize()
        # Other objects
        self.torch    = Torch(position=vec(SPAWN_X, SPAWN_Y))
        self.lighting = LightingOverlay()
        self.hud      = HUD()
        # Camera
        Drawable.updateOffset(self.torch, self.worldSize)

    def draw(self, drawSurface):
        self.tilemap.draw(drawSurface)
        self.torch.draw(drawSurface)
        self.lighting.draw(drawSurface, self.torch)
        self.hud.draw(drawSurface, self.torch)

    def handleEvent(self, event):
        self.torch.handleEvent(event)

    def update(self, seconds):
        self.torch.update(seconds)
        # Wall collisions AFTER moving
        self._resolveCollisions()
        Drawable.updateOffset(self.torch, self.worldSize)

# https://www.metanetsoftware.com/technique/tutorialA.html

    def _resolveCollisions(self):
        """Push torch out of any wall rect it overlaps.
           Torch position is the CENTER of the sprite."""
        size  = self.torch.SIZE
        half  = vec(15, 24)  # actual visual center of sprite within the 32x32 cell
        # Build rect from center position
        tRect = pygame.Rect(
            self.torch.position[0] - half[0],
            self.torch.position[1] - half[1],
            size[0], size[1]
        )

        for wall in self.tilemap.wallRects:
            if not tRect.colliderect(wall):
                continue

            # Compute overlap on each axis and push out on the smallest one
            overlapLeft  = tRect.right  - wall.left
            overlapRight = wall.right   - tRect.left
            overlapTop   = tRect.bottom - wall.top
            overlapBot   = wall.bottom  - tRect.top

            minH = overlapLeft if overlapLeft < overlapRight else -overlapRight
            minV = overlapTop  if overlapTop  < overlapBot   else -overlapBot

            if abs(minH) < abs(minV):
                self.torch.position[0] -= minH
                self.torch.velocity[0]  = 0
            else:
                self.torch.position[1] -= minV
                self.torch.velocity[1]  = 0

            tRect.x = int(self.torch.position[0] - half[0])
            tRect.y = int(self.torch.position[1] - half[1])