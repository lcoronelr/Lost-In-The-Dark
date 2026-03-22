import pygame
from . import Mobile
from utils import *
from gameObjects.drawable import Drawable
from FSMs import FlameFSM

# How fast the light radius changes per second when holding Q or E
INTENSITY_CHANGE_RATE = 60

# Player speed (pixels per second)
MOVE_SPEED = 60

# Sprite sheet layout (32x32 per cell, 8 cols x 5 rows)
# Row 0 : walking                          (8 frames)
# Row 1 : idle    — full flame             (6 frames)
# Row 2 : idle    — full flame with sparks (8 frames)  [unused]
# Row 3 : idle    — medium flame           (6 frames)
# Row 4 : idle    — flame dying out / dark (8 frames)  <- low flame

_SPRITE_FILE = "Fire_Elemental_Sprite_Sheet.png"

# (is_moving, flame_state) -> (row, nFrames)
_ANIM = {
    (True,  "high")   : (0, 8),
    (True,  "normal") : (0, 8),
    (True,  "low")    : (0, 8),   # still walk row, brightness handles dimming
    (False, "high")   : (1, 6),
    (False, "normal") : (3, 6),
    (False, "low")    : (4, 8),   # dying flame row
}

class Torch(Mobile):
    """
    The player character — a living torch.

    Controls
    --------
    WASD / Arrow keys : move
    Q                 : decrease flame (stealth / regen)
    E                 : increase flame (visibility / danger)
    """

    SIZE = vec(32, 32)

    def __init__(self, position=(0, 0)):
        super().__init__(position, _SPRITE_FILE)

        self.position    = vec(*position)
        self.imageName   = _SPRITE_FILE
        self.velocity    = vec(0, 0)
        self.maxVelocity = MOVE_SPEED

        # Animation state
        self.row             = 1
        self.frame           = 0
        self.nFrames         = 6
        self.framesPerSecond = 8
        self.animationTimer  = 0

        # Flame / health state
        self.lightRadius = float(DEFAULT_INTENSITY)
        self.health      = float(MAX_HEALTH)

        # Held movement keys — direct velocity, no acceleration
        self._heldX = 0   # -1, 0, or 1
        self._heldY = 0   # -1, 0, or 1

        # Input flags
        self._increasing = False
        self._decreasing = False

        # Only the flame FSM — movement is now direct
        self.FSMflame = FlameFSM(self)

        self._updateSprite()

    def handleEvent(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_a, pygame.K_LEFT):
                self._heldX = -1
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self._heldX = 1
            elif event.key in (pygame.K_w, pygame.K_UP):
                self._heldY = -1
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self._heldY = 1
            elif event.key == pygame.K_q:
                self._decreasing = True
            elif event.key == pygame.K_e:
                self._increasing = True

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_a, pygame.K_LEFT) and self._heldX == -1:
                self._heldX = 0
            elif event.key in (pygame.K_d, pygame.K_RIGHT) and self._heldX == 1:
                self._heldX = 0
            elif event.key in (pygame.K_w, pygame.K_UP) and self._heldY == -1:
                self._heldY = 0
            elif event.key in (pygame.K_s, pygame.K_DOWN) and self._heldY == 1:
                self._heldY = 0
            elif event.key == pygame.K_q:
                self._decreasing = False
            elif event.key == pygame.K_e:
                self._increasing = False

    def update(self, seconds):
        # Direct velocity — stops instantly when key released
        self.velocity = vec(self._heldX, self._heldY)
        if magnitude(self.velocity) > EPSILON:
            self.velocity = scale(self.velocity, MOVE_SPEED)

        self.position += self.velocity * seconds

        # world bounds — use a large world size, collision handled by engine
        self.position[0] = max(0, self.position[0])
        self.position[1] = max(0, self.position[1])

        # Flame intensity adjustment
        if self._increasing:
            self.lightRadius = min(MAX_INTENSITY, self.lightRadius + INTENSITY_CHANGE_RATE * seconds)
        if self._decreasing:
            self.lightRadius = max(MIN_INTENSITY, self.lightRadius - INTENSITY_CHANGE_RATE * seconds)

        # Health logic driven by flame state
        self.FSMflame.updateState()
        if self.FSMflame == "high":
            self.health = max(0,          self.health - HEALTH_DRAIN_RATE * seconds)
        elif self.FSMflame == "low":
            self.health = min(MAX_HEALTH, self.health + HEALTH_REGEN_RATE * seconds)

        # Pick animation row based on movement + flame state
        is_moving   = magnitude(self.velocity) > EPSILON
        flame_state = self.FSMflame.current_state.id
        new_row, new_nFrames = _ANIM[(is_moving, flame_state)]

        if new_row != self.row:
            self.row            = new_row
            self.nFrames        = new_nFrames
            self.frame          = 0
            self.animationTimer = 0

        # Advance animation
        self.animationTimer += seconds
        if self.animationTimer >= 1 / self.framesPerSecond:
            self.animationTimer -= 1 / self.framesPerSecond
            self.frame = (self.frame + 1) % self.nFrames

        self._updateSprite()

    # reference to : https://www.youtube.com/watch?v=NGFk44fY0O4 and https://stackoverflow.com/questions/31038285/python-pygame-game-lighting

    def draw(self, drawSurface):
        """Draw the torch sprite centered on position."""
        centered = self.position - vec(15, 24)
        pos = list(map(int, centered - Drawable.CAMERA_OFFSET))
        drawSurface.blit(self.image, pos)

    def _updateSprite(self):
        """Pull the current (frame, row) from the sheet and apply brightness."""
        raw = SpriteManager.getInstance().getSprite(_SPRITE_FILE, (self.frame, self.row))
        self.image = raw.copy()
        self._applyBrightness()

    def _applyBrightness(self):
        """Darken sprite when flame is low, full bright when high.
           Tied to lightRadius so Q/E visually dims/brightens the character."""
        t = (self.lightRadius - MIN_INTENSITY) / (MAX_INTENSITY - MIN_INTENSITY)
        t = max(0.0, min(1.0, t))
        # 20 = nearly black at min, 255 = full bright at max
        b = int(20 + t * 235)
        overlay = pygame.Surface(list(map(int, self.SIZE)), pygame.SRCALPHA)
        overlay.fill((b, b, b, 255))
        self.image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def getSize(self):
        return self.SIZE.copy()