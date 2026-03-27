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

# Hitbox: small rect around the character's feet, in pixels (width, height)
HITBOX_W = 8
HITBOX_H = 8

# Sounds
AMBIENT_SOUND = 0.5
FLAME_MIN_VOL = 0.0
FLAME_MAX_VOL = 0.8

# Fallback spawn if no player_spawn point found in map
DEFAULT_SPAWN = vec(624, 380)   # level3 spawn, overridden by map if Spawn layer exists


class GameEngine(object):
    """
    Top-level game manager for Lost in the Dark.
    Accepts a mapFile parameter so it can load any level.
    """

    def __init__(self, mapFile="level3.tmj"):
        # Load the tile map
        self.tilemap   = TileMap(join(_PROJECT, "maps", mapFile))
        self.worldSize = self.tilemap.getSize()

        # Read player spawn from map, fall back to default
        spawn    = self.tilemap.getSpawn("player_spawn")
        spawnPos = vec(*spawn) if spawn else DEFAULT_SPAWN

        # Other objects
        self.torch    = Torch(position=spawnPos)
        self.lighting = LightingOverlay()
        self.hud      = HUD()

        # Camera
        Drawable.updateOffset(self.torch, self.worldSize)

        # Sounds
        self.ambientSound = None
        self.flameSound   = None
        try:
            pygame.mixer.init()
            self.ambientSound = pygame.mixer.Sound(join(_PROJECT, "sounds", "ambient.wav"))
            self.flameSound   = pygame.mixer.Sound(join(_PROJECT, "sounds", "flame.wav"))
            self.ambientSound.set_volume(AMBIENT_SOUND)
            self.flameSound.set_volume(FLAME_MIN_VOL)
            self.ambientSound.play(loops=-1)
            self.flameSound.play(loops=-1)
        except pygame.error:
            pass   # no audio device — game runs silently

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
        self._updateSound()

    def stop(self):
        """Call this when leaving the level so sounds don't keep playing."""
        if self.ambientSound: self.ambientSound.stop()
        if self.flameSound:   self.flameSound.stop()

    # https://www.metanetsoftware.com/technique/tutorialA.html

    def _updateSound(self):
        """Scale flame sound volume to match the current light radius."""
        from utils.constants import MIN_INTENSITY, MAX_INTENSITY
        t = (self.torch.lightRadius - MIN_INTENSITY) / (MAX_INTENSITY - MIN_INTENSITY)
        t = max(0.0, min(1.0, t))
        if self.flameSound:
            self.flameSound.set_volume(FLAME_MIN_VOL + t * (FLAME_MAX_VOL - FLAME_MIN_VOL))

    def _resolveCollisions(self):
        """Push torch out of any wall rect it overlaps.
           Uses a small hitbox centered on position so narrow corridors work."""
        hw = HITBOX_W // 2
        hh = HITBOX_H // 2
        tRect = pygame.Rect(
            self.torch.position[0] - hw,
            self.torch.position[1] - hh,
            HITBOX_W, HITBOX_H
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

            tRect.x = int(self.torch.position[0] - hw)
            tRect.y = int(self.torch.position[1] - hh)