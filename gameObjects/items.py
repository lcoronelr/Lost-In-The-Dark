"""
Game objects for Level 1:
  WallTorch     — press F nearby to light, costs health, emits light
  Key           — walk over to collect, opens gate_1
  Box           — push by walking into it, glides to stop, opens gate_2 via plate
  PressurePlate — drawn in code, activates when box is on it
  Door          — drawn as colored rect overlay, animates open when unlocked
"""

import pygame
from os.path import join, dirname, abspath
from gameObjects.drawable import Drawable
from utils.vector import vec, magnitude

_HERE    = dirname(abspath(__file__))
_PROJECT = dirname(_HERE)
_ITEMS   = join(_PROJECT, "images", "items and trap_animation")

# Interaction ranges
TORCH_INTERACT_RANGE = 20
TORCH_LIGHT_COST     = 10
TORCH_LIGHT_RADIUS   = 60   # how far lit torches illuminate

# Box physics
BOX_PUSH_SPEED = 60
BOX_FRICTION   = 150

# Pressure plate
PLATE_SIZE = 12


def _loadFrames(folder, prefix, count):
    """Load numbered PNGs: prefix1.png ... prefixN.png"""
    frames = []
    for i in range(1, count + 1):
        path = join(_ITEMS, folder, f"{prefix}{i}.png")
        surf = pygame.image.load(path).convert_alpha()
        frames.append(surf)
    return frames


# ── Wall Torch ────────────────────────────────────────────────────────────────

class WallTorch:
    """
    Starts unlit/dark. Press F nearby to ignite — costs health once.
    When lit, animates flame and emits a small ambient light radius.
    """

    def __init__(self, position):
        self.position    = vec(*position)
        self.lit         = False
        self.frame       = 0
        self.timer       = 0
        self.fps         = 6
        self.lightRadius = TORCH_LIGHT_RADIUS
        self._frames     = _loadFrames("torch", "torch_", 4)

    def update(self, seconds):
        if not self.lit:
            return
        self.timer += seconds
        if self.timer >= 1 / self.fps:
            self.timer -= 1 / self.fps
            self.frame = (self.frame + 1) % len(self._frames)

    def tryLight(self, torch):
        """Returns health cost if just lit, else 0."""
        if self.lit:
            return 0
        if magnitude(torch.position - self.position) <= TORCH_INTERACT_RANGE:
            self.lit   = True
            self.frame = 0
            return TORCH_LIGHT_COST
        return 0

    def draw(self, surface):
        offset = Drawable.CAMERA_OFFSET
        sx = int(self.position[0] - offset[0])
        sy = int(self.position[1] - offset[1])

        # Stone stand
        pygame.draw.rect(surface, (80, 70, 60), (sx - 3, sy, 6, 8))

        # Flame
        frame_surf = self._frames[self.frame]
        fw, fh = frame_surf.get_size()
        fx, fy = sx - fw // 2, sy - fh

        if self.lit:
            surface.blit(frame_surf, (fx, fy))
        else:
            dark = frame_surf.copy()
            dark.fill((30, 30, 30, 200), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(dark, (fx, fy))


# ── Key ───────────────────────────────────────────────────────────────────────

class Key:
    """Animated spinning key. Walk over to collect."""

    def __init__(self, position):
        self.position  = vec(*position)
        self.collected = False
        self.frame     = 0
        self.timer     = 0
        self.fps       = 6
        self._frames   = _loadFrames("keys", "keys_1_", 4)

    def update(self, seconds):
        if self.collected:
            return
        self.timer += seconds
        if self.timer >= 1 / self.fps:
            self.timer -= 1 / self.fps
            self.frame = (self.frame + 1) % len(self._frames)

    def tryCollect(self, torch):
        """Returns True if just picked up."""
        if self.collected:
            return False
        if magnitude(torch.position - self.position) <= 14:
            self.collected = True
            return True
        return False

    def draw(self, surface):
        if self.collected:
            return
        offset = Drawable.CAMERA_OFFSET
        f = self._frames[self.frame]
        fw, fh = f.get_size()
        sx = int(self.position[0] - offset[0] - fw // 2)
        sy = int(self.position[1] - offset[1] - fh // 2)
        surface.blit(f, (sx, sy))


# ── Pressure Plate ────────────────────────────────────────────────────────────

class PressurePlate:
    """Flat rect drawn in code. Activates when box is on it."""

    def __init__(self, position, doorId="gate_2"):
        self.position = vec(*position)
        self.doorId   = doorId
        self.active   = False
        self._rect    = pygame.Rect(
            int(self.position[0]) - PLATE_SIZE // 2,
            int(self.position[1]) - PLATE_SIZE // 2,
            PLATE_SIZE, PLATE_SIZE
        )

    def check(self, box):
        """Returns True the first time the box lands on it."""
        if self.active:
            return False
        if self._rect.collidepoint(int(box.position[0]), int(box.position[1])):
            self.active = True
            return True
        return False

    def draw(self, surface):
        offset = Drawable.CAMERA_OFFSET
        rx = int(self._rect.x - offset[0])
        ry = int(self._rect.y - offset[1])
        color = (200, 120, 30) if self.active else (80, 75, 70)
        pygame.draw.rect(surface, color, (rx, ry, PLATE_SIZE, PLATE_SIZE))
        pygame.draw.rect(surface, (40, 35, 30), (rx, ry, PLATE_SIZE, PLATE_SIZE), 1)


# ── Box ───────────────────────────────────────────────────────────────────────

class Box:
    """
    Pushable box. Player walks into it → impulse push in that direction.
    Only pushes once per contact — must separate before pushing again.
    """

    SIZE = 14

    def __init__(self, position):
        self.position    = vec(*position)
        self.velocity    = vec(0.0, 0.0)
        self.frame       = 0
        self.timer       = 0
        self.fps         = 4
        self._frames     = _loadFrames("box_1", "box_1_", 4)
        self._inContact  = False   # tracks if player was touching last frame

    def tryPush(self, torch):
        """Push only on the leading edge of contact (not every frame)."""
        dx = self.position[0] - torch.position[0]
        dy = self.position[1] - torch.position[1]
        dist = magnitude(vec(dx, dy))
        pushRange = self.SIZE // 2 + 6

        touching = dist < pushRange and dist > 0

        if touching and not self._inContact:
            # First frame of contact — apply impulse
            pushDir = vec(dx, dy) / dist
            self.velocity = pushDir * BOX_PUSH_SPEED

        self._inContact = touching

    def update(self, seconds, wallRects):
        # Animate
        self.timer += seconds
        if self.timer >= 1 / self.fps:
            self.timer -= 1 / self.fps
            self.frame = (self.frame + 1) % len(self._frames)

        # Friction
        speed = magnitude(self.velocity)
        if speed > 0:
            friction = min(BOX_FRICTION * seconds, speed)
            self.velocity -= (self.velocity / speed) * friction

        self.position += self.velocity * seconds
        self._resolveWalls(wallRects)

    def _resolveWalls(self, wallRects):
        hw = self.SIZE // 2
        bRect = pygame.Rect(
            int(self.position[0]) - hw,
            int(self.position[1]) - hw,
            self.SIZE, self.SIZE
        )
        for wall in wallRects:
            if not bRect.colliderect(wall):
                continue
            ol = bRect.right  - wall.left
            or_ = wall.right  - bRect.left
            ot = bRect.bottom - wall.top
            ob = wall.bottom  - bRect.top
            minH = ol if ol < or_ else -or_
            minV = ot if ot < ob  else -ob
            if abs(minH) < abs(minV):
                self.position[0] -= minH
                self.velocity[0]  = 0
            else:
                self.position[1] -= minV
                self.velocity[1]  = 0
            bRect.x = int(self.position[0] - hw)
            bRect.y = int(self.position[1] - hw)

    def draw(self, surface):
        offset = Drawable.CAMERA_OFFSET
        f = self._frames[self.frame]
        fw, fh = f.get_size()
        sx = int(self.position[0] - offset[0] - fw // 2)
        sy = int(self.position[1] - offset[1] - fh // 2)
        surface.blit(f, (sx, sy))


# ── Door ─────────────────────────────────────────────────────────────────────

class Door:
    """
    Drawn as a colored rect overlay on top of the door tile.
    Animates open by fading/sliding the rect away when unlocked.
    """

    OPEN_SPEED = 60   # pixels per second the door slides

    def __init__(self, doorId, rect):
        self.doorId  = doorId
        self.rect    = pygame.Rect(rect)   # original full rect
        self._offset = 0.0                 # how many pixels it has slid open
        self.open    = False
        self._color  = (60, 40, 20, 220)   # dark wood color semi-transparent

    def unlock(self):
        self.open = True

    def update(self, seconds):
        if self.open:
            self._offset = min(self._offset + self.OPEN_SPEED * seconds,
                               self.rect.height)

    def draw(self, surface):
        remaining = self.rect.height - int(self._offset)
        if remaining <= 0:
            return
        offset = Drawable.CAMERA_OFFSET
        rx = int(self.rect.x - offset[0])
        ry = int(self.rect.y - offset[1])
        # Slide upward as it opens
        drawRect = pygame.Rect(rx, ry, self.rect.width, remaining)
        pygame.draw.rect(surface, (60, 40, 20), drawRect)
        pygame.draw.rect(surface, (40, 25, 10), drawRect, 1)