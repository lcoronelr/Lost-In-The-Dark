import pygame
from . import Drawable
from .torch    import Torch
from .lighting import LightingOverlay
from .hud      import HUD
from .tilemap  import TileMap
from .items    import WallTorch, Key, Box, PressurePlate, Door
from utils     import vec, RESOLUTION
from os.path   import join, dirname, abspath

_HERE    = dirname(abspath(__file__))
_PROJECT = dirname(_HERE)

HITBOX_W = 8
HITBOX_H = 8

AMBIENT_SOUND = 0.5
FLAME_MIN_VOL = 0.0
FLAME_MAX_VOL = 0.8

DEFAULT_SPAWN = vec(624, 380)


class GameEngine(object):

    def __init__(self, mapFile="level3.tmj"):
        self.tilemap   = TileMap(join(_PROJECT, "maps", mapFile))
        self.worldSize = self.tilemap.getSize()

        spawn    = self.tilemap.getSpawn("player_spawn")
        spawnPos = vec(*spawn) if spawn else DEFAULT_SPAWN

        self.torch    = Torch(position=spawnPos)
        self.lighting = LightingOverlay()
        self.hud      = HUD()

        # Spawn items from map
        self.torches = [WallTorch(p) for p in self.tilemap.spawnPoints.get("torch_wall", [])]
        self.keys    = [Key(p)       for p in self.tilemap.spawnPoints.get("key", [])]
        self.boxes   = [Box(p)       for p in self.tilemap.spawnPoints.get("box", [])]
        self.plates  = [PressurePlate(p, doorId="gate_2")
                        for p in self.tilemap.spawnPoints.get("pressure_plate", [])]

        # Door overlays 
        self.doors = {}
        for doorId, rect in self.tilemap.doorRects.items():
            self.doors[doorId] = Door(doorId, rect)

        self.hasKey  = False
        self.isDead  = False   # lose condition

        Drawable.updateOffset(self.torch, self.worldSize)

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
            pass

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, drawSurface):
        self.tilemap.draw(drawSurface)

        for plate in self.plates:
            plate.draw(drawSurface)
        for door in self.doors.values():
            door.draw(drawSurface)
        for key in self.keys:
            key.draw(drawSurface)
        for box in self.boxes:
            box.draw(drawSurface)
        for wt in self.torches:
            wt.draw(drawSurface)

        self.torch.draw(drawSurface)
        self.lighting.draw(drawSurface, self.torch, self.torches)
        self.hud.draw(drawSurface, self.torch)

    # ── Handle Events ────────────────────────────────────────────────────────

    def handleEvent(self, event):
        self.torch.handleEvent(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            for wt in self.torches:
                cost = wt.tryLight(self.torch)
                if cost > 0:
                    self.torch.health = max(0, self.torch.health - cost)

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, seconds):
        if self.isDead:
            return

        self.torch.update(seconds)
        self._resolveCollisions()
        Drawable.updateOffset(self.torch, self.worldSize)
        self._updateSound()

        for wt in self.torches:
            wt.update(seconds)

        for box in self.boxes:
            box.tryPush(self.torch)
            box.update(seconds, self.tilemap.wallRects)

        # Box on plate → open gate_2
        for plate in self.plates:
            for box in self.boxes:
                if plate.check(box):
                    self.tilemap.openDoor(plate.doorId)
                    if plate.doorId in self.doors:
                        self.doors[plate.doorId].unlock()

        # Key collected → open gate_1
        for key in self.keys:
            if key.tryCollect(self.torch):
                self.hasKey = True
                self.tilemap.openDoor("gate_1")
                if "gate_1" in self.doors:
                    self.doors["gate_1"].unlock()

        # Update door animations
        for door in self.doors.values():
            door.update(seconds)

        # Lose condition — health at zero
        if self.torch.health <= 0:
            self.isDead = True
            if self.ambientSound: self.ambientSound.stop()
            if self.flameSound:   self.flameSound.stop()

    def stop(self):
        if self.ambientSound: self.ambientSound.stop()
        if self.flameSound:   self.flameSound.stop()

    # https://www.metanetsoftware.com/technique/tutorialA.html

    def _updateSound(self):
        from utils.constants import MIN_INTENSITY, MAX_INTENSITY
        t = (self.torch.lightRadius - MIN_INTENSITY) / (MAX_INTENSITY - MIN_INTENSITY)
        t = max(0.0, min(1.0, t))
        if self.flameSound:
            self.flameSound.set_volume(FLAME_MIN_VOL + t * (FLAME_MAX_VOL - FLAME_MIN_VOL))

    def _resolveCollisions(self):
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
            ol  = tRect.right  - wall.left
            or_ = wall.right   - tRect.left
            ot  = tRect.bottom - wall.top
            ob  = wall.bottom  - tRect.top
            minH = ol if ol < or_ else -or_
            minV = ot if ot < ob  else -ob
            if abs(minH) < abs(minV):
                self.torch.position[0] -= minH
                self.torch.velocity[0]  = 0
            else:
                self.torch.position[1] -= minV
                self.torch.velocity[1]  = 0
            tRect.x = int(self.torch.position[0] - hw)
            tRect.y = int(self.torch.position[1] - hh)