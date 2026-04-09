"""
Enemy — Skeleton1 that wanders, chases when player enters light radius,
        and deals damage on contact.
Fireball — player-fired projectile that illuminates while traveling,
           deals damage to enemy on hit.
"""

import pygame
import math
from os.path import join, dirname, abspath
from gameObjects.drawable import Drawable
from utils.vector import vec, magnitude, scale
from FSMs import AbstractGameFSM
from statemachine import State

_HERE    = dirname(abspath(__file__))
_PROJECT = dirname(_HERE)
_ENEMIES = join(_PROJECT, "images", "Enemy_Animations_Set")

# Enemy constants
EASY_ENEMY_SPEED_WANDER   = 30
EASY_ENEMY_SPEED_CHASE    = 55
EASY_ENEMY_DAMAGE         = 50       # half health on contact
EASY_ENEMY_DAMAGE_COOLDOWN = 2.0     # seconds before it can damage again
EASY_ENEMY_WANDER_RANGE   = 60       # how far it wanders from spawn
EASY_ENEMY_SIZE           = 14       # hitbox radius

# Fireball constants
FIREBALL_SPEED   = 120
FIREBALL_RADIUS  = 20           # light radius while traveling
FIREBALL_DAMAGE  = 30
FIREBALL_SIZE    = 3            # hitbox radius



def _loadStrip(filename, frameW=32, frameH=32):
    """Load a horizontal sprite strip and slice into frames."""
    path = join(_ENEMIES, filename)
    sheet = pygame.image.load(path).convert_alpha()
    w, h  = sheet.get_size()
    frames = []
    for x in range(0, w, frameW):
        frame = pygame.Surface((frameW, frameH), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (x, 0, frameW, frameH))
        frames.append(frame)
    return frames


# ── Enemy FSM ─────────────────────────────────────────────────────────────────

class EnemyFSM(AbstractGameFSM):
    """Two states: wander and chase."""
    wander = State(initial=True)
    chase  = State()

    startChase = wander.to(chase)
    stopChase  = chase.to(wander)


# ── Enemy ─────────────────────────────────────────────────────────────────────

class Enemy:
    """
    Skeleton that wanders near its spawn point.
    Chases when player enters light radius.
    Deals ENEMY_DAMAGE on contact, once per cooldown.
    Takes damage from fireballs.
    """

    def __init__(self, position):
        self.position   = vec(*position)
        self.spawnPos   = vec(*position)
        self.velocity   = vec(0.0, 0.0)
        self.health     = 90
        self._max_health = 90
        self.alive      = True
        self._damageCd  = 0.0
        self._facingLeft = False
        self._hitTimer  = 0.0

        # Animation — using available skeleton1 files
        self._idleFrames = _loadStrip("enemies-skeleton1_idle.png")          # 6 frames
        self._moveFrames = _loadStrip("enemies-skeleton1_movement.png")      # 10 frames
        self._hitFrames  = _loadStrip("enemies-skeleton1_take_damage.png")   # 5 frames

        self._frames     = self._idleFrames
        self._frame      = 0
        self._animTimer  = 0.0
        self._fps        = 8

        # FSM
        self.FSM = EnemyFSM(self)

        # Wander
        self._wanderTarget = self._newWanderTarget()
        self._wanderTimer  = 0.0

    def _newWanderTarget(self):
        import random
        angle = random.uniform(0, 2 * math.pi)
        dist  = random.uniform(10, EASY_ENEMY_WANDER_RANGE)
        return self.spawnPos + vec(math.cos(angle) * dist,
                                   math.sin(angle) * dist)

    def update(self, seconds, torchPos, torchRadius, wallRects):
        if not self.alive:
            return

        self._damageCd -= seconds
        self._hitTimer  = max(0, self._hitTimer - seconds)
        self._wanderTimer += seconds

        dist = magnitude(torchPos - self.position)

        # FSM transitions
        if self.FSM == "wander" and dist <= torchRadius:
            self.FSM.startChase()
        elif self.FSM == "chase" and dist > torchRadius * 1.2:
            self.FSM.stopChase()


        # Movement
        if self.FSM == "chase":
            direction = torchPos - self.position
            if magnitude(direction) > 0:
                self.velocity = scale(direction, EASY_ENEMY_SPEED_CHASE)
        else:
            toTarget = self._wanderTarget - self.position
            if magnitude(toTarget) < 8 or self._wanderTimer > 3.0:
                self._wanderTarget = self._newWanderTarget()
                self._wanderTimer  = 0.0
            if magnitude(toTarget) > 0:
                self.velocity = scale(toTarget, EASY_ENEMY_SPEED_WANDER)

        self._facingLeft = self.velocity[0] < 0
        self.position   += self.velocity * seconds
        self._resolveWalls(wallRects)
        self._updateAnim(seconds)

    def tryDamagePlayer(self, torch):
        """Returns damage dealt this frame, 0 if on cooldown or not touching."""
        if not self.alive or self._damageCd > 0:
            return 0
        if magnitude(torch.position - self.position) < EASY_ENEMY_SIZE + 6:
            self._damageCd = EASY_ENEMY_DAMAGE_COOLDOWN
            return EASY_ENEMY_DAMAGE
        return 0

    def takeDamage(self, amount):
        self.health   -= amount
        self._hitTimer = 0.4
        if self.health <= 0:
            self.alive = False

    def _updateAnim(self, seconds):
        moving = magnitude(self.velocity) > 1
        if self._hitTimer > 0:
            target = self._hitFrames
        elif moving:
            target = self._moveFrames
        else:
            target = self._idleFrames

        if target is not self._frames:
            self._frames = target
            self._frame  = 0

        self._animTimer += seconds
        if self._animTimer >= 1 / self._fps:
            self._animTimer -= 1 / self._fps
            self._frame = (self._frame + 1) % len(self._frames)

    def _resolveWalls(self, wallRects):
        hw    = EASY_ENEMY_SIZE // 2
        eRect = pygame.Rect(int(self.position[0]) - hw,
                            int(self.position[1]) - hw,
                            EASY_ENEMY_SIZE, EASY_ENEMY_SIZE)
        for wall in wallRects:
            if not eRect.colliderect(wall):
                continue
            ol  = eRect.right  - wall.left
            or_ = wall.right   - eRect.left
            ot  = eRect.bottom - wall.top
            ob  = wall.bottom  - eRect.top
            minH = ol if ol < or_ else -or_
            minV = ot if ot < ob  else -ob
            if abs(minH) < abs(minV):
                self.position[0] -= minH
                self.velocity[0]  = 0
            else:
                self.position[1] -= minV
                self.velocity[1]  = 0
            eRect.x = int(self.position[0] - hw)
            eRect.y = int(self.position[1] - hw)

    def draw(self, surface):
        if not self.alive:
            return
        offset = Drawable.CAMERA_OFFSET
        frame  = self._frames[self._frame].copy()

        if self._facingLeft:
            frame = pygame.transform.flip(frame, True, False)

        if self._hitTimer > 0:
            frame.fill((255, 80, 80, 0), special_flags=pygame.BLEND_RGB_ADD)

        fw, fh = frame.get_size()
        sx = int(self.position[0] - offset[0] - fw // 2)
        sy = int(self.position[1] - offset[1] - fh // 2)
        surface.blit(frame, (sx, sy))

        # Health bar — fixed above sprite
        BAR_W  = fw
        BAR_H  = 3
        BAR_Y  = sy - 6
        pct    = max(0, self.health / self._max_health)
        bg     = pygame.Rect(sx, BAR_Y, BAR_W, BAR_H)
        fill   = pygame.Rect(sx, BAR_Y, int(BAR_W * pct), BAR_H)
        pygame.draw.rect(surface, (60, 0, 0),   bg)
        pygame.draw.rect(surface, (220, 50, 50), fill)
        pygame.draw.rect(surface, (200, 200, 200), bg, 1)


# ── Fireball ──────────────────────────────────────────────────────────────────

class Fireball:
    """
    Shoots toward mouse. Glows orange and illuminates darkness while flying.
    Disappears on wall or enemy collision.
    """

    def __init__(self, position, direction):
        self.position    = vec(*position)
        self.velocity    = scale(direction, FIREBALL_SPEED)
        self.lightRadius = FIREBALL_RADIUS
        self.active      = True
        self._fireballCooldown = 0.0

    def update(self, seconds, wallRects, enemies):
        self._fireballCooldown = max(0, self._fireballCooldown - seconds)
        if not self.active:
            return

        self.position += self.velocity * seconds

        # Wall collision
        hw    = FIREBALL_SIZE
        fRect = pygame.Rect(int(self.position[0]) - hw,
                            int(self.position[1]) - hw,
                            hw * 2, hw * 2)
        for wall in wallRects:
            if fRect.colliderect(wall):
                self.active = False
                return

        # Enemy collision
        for enemy in enemies:
            if not enemy.alive:
                continue
            if magnitude(enemy.position - self.position) < EASY_ENEMY_SIZE + FIREBALL_SIZE:
                enemy.takeDamage(FIREBALL_DAMAGE)
                self.active = False
                return

    def draw(self, surface):
        if not self.active:
            return
        offset = Drawable.CAMERA_OFFSET
        sx = int(self.position[0] - offset[0])
        sy = int(self.position[1] - offset[1])

        # Outer glow
        glow = pygame.Surface((FIREBALL_RADIUS * 2, FIREBALL_RADIUS * 2), pygame.SRCALPHA)
        for r in range(FIREBALL_RADIUS, 0, -1):
            alpha = int(180 * (r / FIREBALL_RADIUS) ** 2)
            pygame.draw.circle(glow, (255, 100, 0, alpha),
                               (FIREBALL_RADIUS, FIREBALL_RADIUS), r)
        surface.blit(glow, (sx - FIREBALL_RADIUS, sy - FIREBALL_RADIUS))

        # Bright core
        pygame.draw.circle(surface, (255, 220, 100), (sx, sy), FIREBALL_SIZE)

