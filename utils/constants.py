"""
variables for the game
"""

from . import vec


RESOLUTION = vec(320, 240)
SCALE = 3
UPSCALED = RESOLUTION * SCALE

EPSILON = 0.01

MIN_INTENSITY = 20    # pixels radius at minimum flame
MAX_INTENSITY = 140   # pixels radius at maximum flame
DEFAULT_INTENSITY = 70

HIGH_INTENSITY_THRESHOLD = 90
LOW_INTENSITY_THRESHOLD  = 40
HEALTH_DRAIN_RATE  = 15
HEALTH_REGEN_RATE  = 3
MAX_HEALTH = 100