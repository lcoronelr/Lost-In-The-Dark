from . import vec

RESOLUTION = vec(320, 240)
SCALE = 2
UPSCALED = RESOLUTION * SCALE

EPSILON = 0.01

MIN_INTENSITY = 20    # pixels radius at minimum flame
MAX_INTENSITY = 140   # pixels radius at maximum flame
DEFAULT_INTENSITY = 70 # starting radius

HIGH_INTENSITY_THRESHOLD = 90   # anything above this it drains
LOW_INTENSITY_THRESHOLD  = 40   # health regens below this
HEALTH_DRAIN_RATE  = 10   # Drain rate
HEALTH_REGEN_RATE  = 5    # regen rate
MAX_HEALTH = 100