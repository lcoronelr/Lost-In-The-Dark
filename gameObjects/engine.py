import pygame

from . import Drawable, Kirby

from utils import vec, RESOLUTION

class GameEngine(object):
    import pygame

    def __init__(self):       
        self.kirby = Kirby((0,0))
        self.size = vec(*RESOLUTION)
        self.background = Drawable((0,0), "background.png")
    
    def draw(self, drawSurface):        
        self.background.draw(drawSurface)
        
        self.kirby.draw(drawSurface)
            
    def handleEvent(self, event):
        self.kirby.handleEvent(event)
    
    def update(self, seconds):
        self.kirby.update(seconds)
        
        Drawable.updateOffset(self.kirby, self.size)
    

