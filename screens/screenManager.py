from FSMs import ScreenManagerFSM
from . import TextEntry, EventMenu
from gameObjects import GameEngine
from utils.vector import vec
from utils.constants import RESOLUTION

from pygame.locals import *
import pygame

# click zones in 320x240 space (x, y, width, height)
RECT_LEVEL1 = (55, 55,  210, 22)
RECT_LEVEL2 = (55, 104, 210, 27)
RECT_LEVEL3 = (55, 155, 210, 24)
RECT_EXIT = (258, 17, 54, 18)

def mouseHit(event, rect):
    """Returns True if a left click landed inside rect (320x240 space)."""
    from utils.constants import UPSCALED
    if event.type != MOUSEBUTTONDOWN or event.button != 1:
        return False
    sx = event.pos[0] * RESOLUTION[0] / UPSCALED[0]
    sy = event.pos[1] * RESOLUTION[1] / UPSCALED[1]
    x, y, w, h = rect
    return x <= sx <= x + w and y <= sy <= y + h


class ScreenManager(object):

    def __init__(self):
        self.state = ScreenManagerFSM(self)
        self.game  = None

        # Placeholder text shown for levels not yet built
        self.comingSoon = TextEntry(vec(0, 0), "COMING SOON",   "default8")
        self.escHint    = TextEntry(vec(0, 0), "ESC: MAIN MENU","default8",color=(160, 160, 160))
        cs = self.comingSoon.getSize()
        eh = self.escHint.getSize()
        self.comingSoon.position = RESOLUTION // 2 - cs // 2
        self.escHint.position    = vec(RESOLUTION[0] // 2 - eh[0] // 2,
                                       RESOLUTION[1] // 2 + 16)

        # Main menu with background image and four clickable options
        self.mainMenu = EventMenu("menu_bg.png", fontName="default8",color=(80, 50, 20))
        self.mainMenu.addOption("level1", "LEVEL  1", vec(160, 66),lambda e: mouseHit(e, RECT_LEVEL1), center="both")
        self.mainMenu.addOption("level2", "LEVEL  2", vec(160, 117),lambda e: mouseHit(e, RECT_LEVEL2),center="both")
        self.mainMenu.addOption("level3", "LEVEL  3", vec(160, 167),lambda e: mouseHit(e, RECT_LEVEL3),center="both")
        self.mainMenu.addOption("exit", "EXIT", vec(284, 25),lambda e: mouseHit(e, RECT_EXIT),center="both")

    def draw(self, drawSurf):
        if self.state == "mainMenu":
            self.mainMenu.draw(drawSurf)

        elif self.state == "level3" and self.game:
            self.game.draw(drawSurf)

        elif self.state in ["level1", "level2"]:
            drawSurf.fill((10, 10, 20))
            self.comingSoon.draw(drawSurf)
            self.escHint.draw(drawSurf)

    def handleEvent(self, event):
        if self.state.isInGame():
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.game = None
                self.state.quitGame()
                return
            if self.state == "level3" and self.game:
                self.game.handleEvent(event)

        elif self.state == "mainMenu":
            choice = self.mainMenu.handleEvent(event)
            if choice == "level1":
                self.state.startLevel1()
            elif choice == "level2":
                self.state.startLevel2()
            elif choice == "level3":
                self.game = GameEngine()
                self.state.startLevel3()
            elif choice == "exit":
                return "exit"

    def update(self, seconds):
        if self.state == "level3" and self.game:
            self.game.update(seconds)
        elif self.state == "mainMenu":
            self.mainMenu.update(seconds)