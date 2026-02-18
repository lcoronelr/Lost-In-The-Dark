from . import AbstractGameFSM
from utils import *
from statemachine import State

class FlameFSM(AbstractGameFSM):
    """
    Three-state FSM for the torch flame intensity.

    States
    ------
    low    : Stealth mode. Limited vision. Health slowly regenerates.
    normal : Balanced. No health change.
    high   : High visibility. Health drains. Attracts enemies faster.

    Transitions are triggered automatically in updateState() based on
    the torch's current lightRadius vs the thresholds in constants.py.
    """

    low    = State(initial=True)
    normal = State()
    high   = State()

    # All valid transitions
    raise_to_normal = low.to(normal)
    raise_to_high   = normal.to(high)
    lower_to_normal = high.to(normal)
    lower_to_low    = normal.to(low)

    # Direct jumps (if intensity changes quickly)
    jump_high = low.to(high)
    jump_low  = high.to(low)

    def updateState(self):
        r = self.obj.lightRadius
        if r >= HIGH_INTENSITY_THRESHOLD and self != "high":
            if self == "low":
                self.jump_high()
            else:
                self.raise_to_high()
        elif r < HIGH_INTENSITY_THRESHOLD and r > LOW_INTENSITY_THRESHOLD and self != "normal":
            if self == "low":
                self.raise_to_normal()
            else:
                self.lower_to_normal()
        elif r <= LOW_INTENSITY_THRESHOLD and self != "low":
            if self == "high":
                self.jump_low()
            else:
                self.lower_to_low()