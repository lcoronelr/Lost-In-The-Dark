import pygame
import math
from . import Drawable
from .torch    import Torch
from .lighting import LightingOverlay
from .hud      import HUD
from .tilemap  import TileMap
from .items    import WallTorch, Key, Box, PressurePlate, Door
from .enemy    import Enemy, Fireball
from utils     import vec, RESOLUTION, magnitude, UPSCALED
from os.path   import join, dirname, abspath

_HERE    = dirname(abspath(__file__))
_PROJECT = dirname(_HERE)

HITBOX_W      = 8
HITBOX_H      = 8
AMBIENT_SOUND = 0.5
FLAME_MIN_VOL = 0.0
FLAME_MAX_VOL = 0.8
DEFAULT_SPAWN = vec(624, 380)
FIREBALL_COST = 5
ENEMY_OFFSET  = vec(-40, -40)


class GameEngine(object):

    def __init__(self, mapFile="level3.tmj"):
        self.tilemap   = TileMap(join(_PROJECT, "maps", mapFile))
        self.worldSize = self.tilemap.getSize()

        spawn    = self.tilemap.getSpawn("player_spawn")
        spawnPos = vec(*spawn) if spawn else DEFAULT_SPAWN

        self.torch    = Torch(position=spawnPos)
        self.lighting = LightingOverlay()
        self.hud      = HUD()

        # Items
        self.torches = [WallTorch(p) for p in self.tilemap.spawnPoints.get("torch_wall", [])]
        self.keys    = [Key(p)       for p in self.tilemap.spawnPoints.get("key", [])]
        self.boxes   = [Box(p)       for p in self.tilemap.spawnPoints.get("box", [])]
        self.plates  = [PressurePlate(p, doorId="gate_2")
                        for p in self.tilemap.spawnPoints.get("pressure_plate", [])]
        self.doors   = {did: Door(did, rect)
                        for did, rect in self.tilemap.doorRects.items()}

        # Enemy — spawns near the key
        self.enemies = []
        keySpawns = self.tilemap.spawnPoints.get("key", [])
        if keySpawns:
            self.enemies.append(Enemy(vec(*keySpawns[0]) + ENEMY_OFFSET))

        self.fireballs = []
        self.hasKey    = False
        self.isDead    = False
        
        self._fireballCooldown = 0.0

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
            print("windows can't initialize audio") #issues with windows audio
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
        for enemy in self.enemies:
            enemy.draw(drawSurface)
        for fb in self.fireballs:
            fb.draw(drawSurface)

        self.torch.draw(drawSurface)
        self.lighting.draw(drawSurface, self.torch, self.torches, self.fireballs)
        self.hud.draw(drawSurface, self.torch)

    # ── Handle Events ────────────────────────────────────────────────────────

    def handleEvent(self, event):
        self.torch.handleEvent(event)

        if event.type == pygame.KEYDOWN:
            # F — light nearby wall torch
            if event.key == pygame.K_f:
                for wt in self.torches:
                    cost = wt.tryLight(self.torch)
                    if cost > 0:
                        self.torch.health = max(0, self.torch.health - cost)

        # LEFT CLICK — shoot fireball toward mouse cursor
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            

            if self.torch.health > FIREBALL_COST and self._fireballCooldown <= 0:
                self.torch.health -= FIREBALL_COST
                self._fireballCooldown = 1 # cooldown speed
                mx, my = pygame.mouse.get_pos()
                wx = mx * RESOLUTION[0] / UPSCALED[0] + Drawable.CAMERA_OFFSET[0]
                wy = my * RESOLUTION[1] / UPSCALED[1] + Drawable.CAMERA_OFFSET[1]
                target = vec(wx, wy)
                diff   = target - self.torch.position
                if magnitude(diff) > 0:
                    self.fireballs.append(Fireball(self.torch.position.copy(), diff))

    # ── Update ───────────────────────────────────────────────────────────────

    def update(self, seconds):
        self._fireballCooldown = max(0, self._fireballCooldown - seconds)

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

        for plate in self.plates:
            for box in self.boxes:
                if plate.check(box):
                    self.tilemap.openDoor(plate.doorId)
                    if plate.doorId in self.doors:
                        self.doors[plate.doorId].unlock()

        for key in self.keys:
            if key.tryCollect(self.torch):
                self.hasKey = True
                self.tilemap.openDoor("gate_1")
                if "gate_1" in self.doors:
                    self.doors["gate_1"].unlock()

        for door in self.doors.values():
            door.update(seconds)

        for enemy in self.enemies:
            enemy.update(seconds,self.torch.position,self.torch.lightRadius,self.tilemap.wallRects)
            dmg = enemy.tryDamagePlayer(self.torch)
            if dmg > 0:
                self.torch.health = max(0, self.torch.health - dmg)

        self.fireballs = [fb for fb in self.fireballs if fb.active]
        for fb in self.fireballs:
            fb.update(seconds, self.tilemap.wallRects, self.enemies)

        self.enemies = [e for e in self.enemies if e.alive]

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