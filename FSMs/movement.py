from . import AbstractGameFSM
from utils import vec, magnitude, EPSILON, scale, RESOLUTION

from statemachine import State

class MovementFSM(AbstractGameFSM):
    
    def __init__(self, obj):
        super().__init__(obj)
    
    def update(self, seconds):
        super().update(seconds)
        
        objsize = self.obj.getSize()

        if self.obj.position[0] < 0:
            self.obj.position[0] = 0
            self.obj.velocity[0] = 0
        # right 
        if self.obj.position[0] + objsize[0] > RESOLUTION[0]:
            self.obj.position[0] = RESOLUTION[0] - objsize[0]
            self.obj.velocity[0] = 0
        
        #top 
        if self.obj.position[1] < 0:
            self.obj.position[1] = 0
            self.obj.velocity[1] = 0
        
        #  bottom 
        if self.obj.position[1] + objsize[1] > RESOLUTION[1]:
            self.obj.position[1] = RESOLUTION[1] - objsize[1]
            self.obj.velocity[1] = 0        


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
        self.accel = 200
        
        super().__init__(obj)

    def update(self, seconds=0):
        if self == "positive":
            self.obj.velocity += self.direction * self.accel * seconds
        elif self == "negative":
            self.obj.velocity -= self.direction * self.accel * seconds
                
        elif self == "stalemate":
            pass
        else:
            if self.obj.velocity[self.axis] > self.accel * seconds:
                self.obj.velocity[self.axis] -= self.accel * seconds
            elif self.obj.velocity[self.axis] < -self.accel * seconds:
                self.obj.velocity[self.axis] += self.accel * seconds
            else:
                self.obj.velocity[self.axis] = 0
        
        
    
        super().update(seconds)