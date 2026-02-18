import pygame
from . import Mobile
from utils import *

from FSMs import AccelerationFSM, FlameFSM

# How fast the light radius changes per second when holding Q or E
INTENSITY_CHANGE_RATE = 60

class Torch(Mobile):
    """
    The player character — a living torch.

    Controls
    --------
    WASD / Arrow keys : move
    Q                 : decrease flame (stealth / regen)
    E                 : increase flame (visibility / danger)
    """

    SIZE = vec(8, 8)   # placeholder size until sprite is added

    def __init__(self, position=(0, 0)):
        # No sprite file yet — we draw a placeholder circle
        self.image     = pygame.Surface(list(map(int, self.SIZE)), pygame.SRCALPHA)
        self.position  = vec(*position)
        self.imageName = ""
        self.velocity  = vec(0, 0)
        self.maxVelocity = 160

        # Flame / health state
        self.lightRadius = float(DEFAULT_INTENSITY)
        self.targetRadius = float(DEFAULT_INTENSITY)
        self.health      = float(MAX_HEALTH)

        # Input flags
        self._increasing = False
        self._decreasing = False

        # FSMs
        self.FSMx     = AccelerationFSM(self, axis=0)
        self.FSMy     = AccelerationFSM(self, axis=1)
        self.FSMflame = FlameFSM(self)

        self._redrawPlaceholder()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handleEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_a, pygame.K_LEFT):
                self.FSMx.decrease()
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.FSMx.increase()
            elif event.key in (pygame.K_w, pygame.K_UP):
                self.FSMy.decrease()
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.FSMy.increase()
            elif event.key == pygame.K_q:
                self._decreasing = True
            elif event.key == pygame.K_e:
                self._increasing = True

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_a, pygame.K_LEFT):
                self.FSMx.stop_decrease()
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self.FSMx.stop_increase()
            elif event.key in (pygame.K_w, pygame.K_UP):
                self.FSMy.stop_decrease()
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.FSMy.stop_increase()
            elif event.key == pygame.K_q:
                self._decreasing = False
            elif event.key == pygame.K_e:
                self._increasing = False

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, seconds):
        # Movement FSMs
        self.FSMx.update(seconds)
        self.FSMy.update(seconds)

        # Position + velocity cap
        from utils import magnitude, scale
        if magnitude(self.velocity) > self.maxVelocity:
            self.velocity = scale(self.velocity, self.maxVelocity)
        self.position += self.velocity * seconds

        # Clamp to world
        size = self.SIZE
        self.position[0] = max(0, min(self.position[0], RESOLUTION[0] - size[0]))
        self.position[1] = max(0, min(self.position[1], RESOLUTION[1] - size[1]))

        # Flame intensity adjustment
        if self._increasing:
            self.lightRadius = min(MAX_INTENSITY,
                                   self.lightRadius + INTENSITY_CHANGE_RATE * seconds)
        if self._decreasing:
            self.lightRadius = max(MIN_INTENSITY,
                                   self.lightRadius - INTENSITY_CHANGE_RATE * seconds)

        # Health logic driven by flame state
        self.FSMflame.updateState()
        if self.FSMflame == "high":
            self.health = max(0, self.health - HEALTH_DRAIN_RATE * seconds)
        elif self.FSMflame == "low":
            self.health = min(MAX_HEALTH, self.health + HEALTH_REGEN_RATE * seconds)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self, drawSurface):
        """Draw the placeholder torch dot. Replace with sprite later."""
        self._redrawPlaceholder()
        from gameObjects.drawable import Drawable
        pos = list(map(int, self.position - Drawable.CAMERA_OFFSET))
        drawSurface.blit(self.image, pos)

    def _redrawPlaceholder(self):
        self.image.fill((0, 0, 0, 0))
        color = self._flameColor()
        pygame.draw.circle(self.image, color,
                           (int(self.SIZE[0] // 2), int(self.SIZE[1] // 2)),
                           int(self.SIZE[0] // 2))

    def _flameColor(self):
        """Interpolate color: blue (low) → orange (normal) → white (high)."""
        t = (self.lightRadius - MIN_INTENSITY) / (MAX_INTENSITY - MIN_INTENSITY)
        t = max(0.0, min(1.0, t))
        if t < 0.5:
            s = t * 2
            return (int(255 * s), int(140 * s), 0)
        else:
            s = (t - 0.5) * 2
            return (255, int(140 + 115 * s), int(255 * s))

    def getSize(self):
        return self.SIZE.copy()

    # Convenience properties for the HUD
    @property
    def flameState(self):
        return self.FSMflame.current_state.id