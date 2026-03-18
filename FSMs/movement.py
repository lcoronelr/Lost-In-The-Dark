from . import AbstractGameFSM
from utils import vec, magnitude, EPSILON, scale, RESOLUTION

from statemachine import State

class MovementFSM(AbstractGameFSM):
    
    def __init__(self, obj):
        super().__init__(obj)
    
    def update(self, seconds):
        super().update(seconds)    


class AccelerationFSM(MovementFSM):
    """Axis-based acceleration with gradual stopping."""
    not_moving = State(initial=True)
    
    negative = State()
    positive = State()
    
    stalemate = State()
    
    decrease  = not_moving.to(negative) | positive.to(stalemate)
    
    increase = not_moving.to(positive) | negative.to(stalemate)
    
    stop_decrease = negative.to(not_moving) | stalemate.to(positive)
    
    stop_increase = positive.to(not_moving) | stalemate.to(negative)
    
    stop_all      = not_moving.to.itself(internal=True) | negative.to(not_moving) | \
                    positive.to(not_moving) | stalemate.to(not_moving)
    
    def __init__(self, obj, axis=0):
        self.axis      = axis
        self.direction = vec(0,0)
        self.direction[self.axis] = 1
        self.accel = 100
        
        super().__init__(obj)

    def update(self, seconds=0):
        if self == "positive":
            self.obj.velocity += self.direction * seconds * self.accel
        elif self == "negative":
            self.obj.velocity -= self.direction * seconds  * self.accel
        super().update(seconds)