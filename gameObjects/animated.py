from . import Drawable
from utils import SpriteManager

class Animated(Drawable):
    
    def __init__(self, position=(0,0), fileName=""):
        super().__init__(position, fileName, (0,0))
        self.fileName = fileName
        self.row = 0
        self.frame = 0
        self.nFrames = 1
        self.animate = True
        self.framesPerSecond = 8
        self.animationTimer = 0
        self.FSManimated = None
    
    def update(self, seconds):
        if self.FSManimated:
            self.FSManimated.updateState()
            
        if not self.animate:
            return
        
        self.animationTimer += seconds 
           
        if self.animationTimer > 1 / self.framesPerSecond:
            self.frame += 1
            self.frame %= self.nFrames
            self.animationTimer -= 1 / self.framesPerSecond
            self.image = SpriteManager.getInstance().getSprite(self.fileName,
                                        (self.frame, self.row))
    
