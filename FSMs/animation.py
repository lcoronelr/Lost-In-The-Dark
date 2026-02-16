from . import AbstractGameFSM
from utils import magnitude, EPSILON, SpriteManager

from statemachine import State

class AnimateFSM(AbstractGameFSM):
    """For anything that animates. Adds behavior on
       transitioning into a state to change animation."""
    def on_enter_state(self):
        state = self.current_state.id
        if self.obj.row != self.obj.rowList[state]:
            self.obj.nFrames = self.obj.nFramesList[state]
            self.obj.frame = 0
            self.obj.row = self.obj.rowList[state]
            self.obj.framesPerSecond = self.obj.framesPerSecondList[state]
            self.obj.animationTimer = 0
            self.obj.image = SpriteManager.getInstance().getSprite(self.obj.imageName,
                                                                   (self.obj.frame, self.obj.row))
         
        
class WalkingFSM(AnimateFSM):
    """Two-state FSM for walking / stopping in
       a top-down environment."""
       
    standing = State(initial=True)
    moving   = State()
    
    move = standing.to(moving)
    stop = moving.to(standing)
        
    
    def updateState(self):
        if self.hasVelocity() and self != "moving":
            self.move()
        elif not self.hasVelocity() and self != "standing":
            self.stop()
    
    def hasVelocity(self):
        return magnitude(self.obj.velocity) > EPSILON
    
    def noVelocity(self):
        return not self.hasVelocity()