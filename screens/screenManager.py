from FSMs import ScreenManagerFSM
from . import TextEntry, EventMenu
from gameObjects import GameEngine
from gameObjects.drawable import Drawable
from utils.vector import vec
from utils.constants import RESOLUTION

from pygame.locals import *
import pygame

# Click zones in 320x240 space (x, y, width, height)
RECT_LEVEL1  = (55, 55,  210, 22)
RECT_LEVEL2  = (55, 104, 210, 27)
RECT_LEVEL3  = (55, 155, 210, 24)
RECT_EXIT    = (258, 17, 54,  18)

RECT_RESUME   = (95, 95,  130, 18)
RECT_RESTART  = (95, 118, 130, 18)
RECT_MAINMENU = (95, 141, 130, 18)

RECT_DEAD_RESTART = (95, 98,  130, 18)
RECT_DEAD_MENU    = (95, 121, 130, 18)

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
        self.state        = ScreenManagerFSM(self)
        self.game         = None
        self._activeLevel = None
        self._activeMap   = None

        # Level 2 placeholder text
        self.comingSoon = TextEntry(vec(0, 0), "COMING SOON",    "default8")
        self.escHint    = TextEntry(vec(0, 0), "ESC: MAIN MENU", "default8",
                                    color=(160, 160, 160))
        cs = self.comingSoon.getSize()
        eh = self.escHint.getSize()
        self.comingSoon.position = RESOLUTION // 2 - cs // 2
        self.escHint.position    = vec(RESOLUTION[0] // 2 - eh[0] // 2,
                                       RESOLUTION[1] // 2 + 16)

        # Pause overlay
        self._pauseSurf  = pygame.Surface(list(map(int, RESOLUTION)), pygame.SRCALPHA)
        self._pauseSurf.fill((0, 0, 0, 160))
        self._pauseTitle   = TextEntry(vec(160, 75),  "PAUSED",    "default8", color=(255, 220, 100))
        self._pauseResume  = TextEntry(vec(160, 98),  "RESUME",    "default8", color=(200, 200, 200))
        self._pauseRestart = TextEntry(vec(160, 121), "RESTART",   "default8", color=(200, 200, 200))
        self._pauseMenu    = TextEntry(vec(160, 144), "MAIN MENU", "default8", color=(200, 200, 200))
        for entry in [self._pauseTitle, self._pauseResume,
                      self._pauseRestart, self._pauseMenu]:
            s = entry.getSize()
            entry.position -= vec(s[0] // 2, 0)

        # Death overlay
        self._deadSurf    = pygame.Surface(list(map(int, RESOLUTION)), pygame.SRCALPHA)
        self._deadSurf.fill((60, 0, 0, 180))
        self._deadTitle   = TextEntry(vec(160, 75),  "YOU DIED",  "default8", color=(255, 60,  60))
        self._deadRestart = TextEntry(vec(160, 105), "RESTART",   "default8", color=(200, 200, 200))
        self._deadMenu    = TextEntry(vec(160, 128), "MAIN MENU", "default8", color=(200, 200, 200))
        for entry in [self._deadTitle, self._deadRestart, self._deadMenu]:
            s = entry.getSize()
            entry.position -= vec(s[0] // 2, 0)

        # Win overlay
        self._winSurf    = pygame.Surface(list(map(int, RESOLUTION)), pygame.SRCALPHA)
        self._winSurf.fill((0, 0, 0, 200))
        self._winTitle   = TextEntry(vec(160, 75),  "YOU ESCAPED", "default8", color=(255, 220, 80))
        self._winRestart = TextEntry(vec(160, 105), "RESTART",     "default8", color=(200, 200, 200))
        self._winMenu    = TextEntry(vec(160, 128), "MAIN MENU",   "default8", color=(200, 200, 200))
        for entry in [self._winTitle, self._winRestart, self._winMenu]:
            s = entry.getSize()
            entry.position -= vec(s[0] // 2, 0)

        # Main menu
        self.mainMenu = EventMenu("menu_bg.png", fontName="default8", color=(80, 50, 20))
        self.mainMenu.addOption("level1", "LEVEL  1", vec(160, 66),
                                lambda e: mouseHit(e, RECT_LEVEL1), center="both")
        self.mainMenu.addOption("level2", "LEVEL  2", vec(160, 117),
                                lambda e: mouseHit(e, RECT_LEVEL2), center="both")
        self.mainMenu.addOption("level3", "LEVEL  3", vec(160, 167),
                                lambda e: mouseHit(e, RECT_LEVEL3), center="both")
        self.mainMenu.addOption("exit",   "EXIT",     vec(284, 25),
                                lambda e: mouseHit(e, RECT_EXIT),   center="both")

    # ── Draw ───────────────────────────────────────────────────────────

    def draw(self, drawSurf):
        if self.state == "mainMenu":
            self.mainMenu.draw(drawSurf)

        elif self.state in ["level1", "level3"] and self.game:
            self.game.draw(drawSurf)
            if self.game.isWon:
                drawSurf.blit(self._winSurf, (0, 0))
                self._winTitle.drawFixed(drawSurf)
                self._winRestart.drawFixed(drawSurf)
                self._winMenu.drawFixed(drawSurf)
            elif self.game.isDead:
                drawSurf.blit(self._deadSurf, (0, 0))
                self._deadTitle.drawFixed(drawSurf)
                self._deadRestart.drawFixed(drawSurf)
                self._deadMenu.drawFixed(drawSurf)

        elif self.state == "level2":
            drawSurf.fill((10, 10, 20))
            self.comingSoon.drawFixed(drawSurf)
            self.escHint.drawFixed(drawSurf)

        elif self.state == "paused" and self.game:
            self.game.draw(drawSurf)
            drawSurf.blit(self._pauseSurf, (0, 0))
            self._pauseTitle.drawFixed(drawSurf)
            self._pauseResume.drawFixed(drawSurf)
            self._pauseRestart.drawFixed(drawSurf)
            self._pauseMenu.drawFixed(drawSurf)

    # ── Handle Events ──────────────────────────────────────────────────

    def handleEvent(self, event):
        # ── In a level (not paused) ────────────────────────────────────
        if self.state.isInGame() and not self.state.isPaused():

            if self.state == "level2":
                if event.type == KEYDOWN and event.key == K_ESCAPE:
                    self._goToMenu()
                return

            # Win screen intercepts all input
            if self.state in ["level1", "level3"] and self.game and self.game.isWon:
                if mouseHit(event, RECT_DEAD_RESTART):
                    self._restartLevel()
                elif mouseHit(event, RECT_DEAD_MENU):
                    self._goToMenu()
                return

            # Death screen intercepts all input
            if self.state in ["level1", "level3"] and self.game and self.game.isDead:
                if mouseHit(event, RECT_DEAD_RESTART):
                    self._restartLevel()
                elif mouseHit(event, RECT_DEAD_MENU):
                    self._goToMenu()
                return

            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.state.pause()
                return

            if self.state in ["level1", "level3"] and self.game:
                self.game.handleEvent(event)

        # ── Paused ─────────────────────────────────────────────────────
        elif self.state.isPaused():
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self._resume()
                return
            if mouseHit(event, RECT_RESUME):
                self._resume()
            elif mouseHit(event, RECT_RESTART):
                self._restartLevel()
            elif mouseHit(event, RECT_MAINMENU):
                self._goToMenu()

        # ── Main menu ──────────────────────────────────────────────────
        elif self.state == "mainMenu":
            choice = self.mainMenu.handleEvent(event)
            if choice == "level1":
                self._startLevel("level1", "level1.tmj")
            elif choice == "level2":
                self.state.startLevel2()
            elif choice == "level3":
                self._startLevel("level3", "level3.tmj")
            elif choice == "exit":
                return "exit"

    # ── Update ─────────────────────────────────────────────────────────

    def update(self, seconds):
        if self.state in ["level1", "level3"] and self.game and not self.game.isDead and not self.game.isWon:
            self.game.update(seconds)
        elif self.state == "mainMenu":
            self.mainMenu.update(seconds)

    # ── Helpers ────────────────────────────────────────────────────────

    def _goToMenu(self):
        """Stop game, reset camera, go to main menu."""
        if self.game:
            self.game.stop()
        self.game         = None
        self._activeLevel = None
        self._activeMap   = None
        Drawable.CAMERA_OFFSET = vec(0, 0)
        self.state.quitGame()

    def _startLevel(self, levelName, mapFile):
        """Create a fresh GameEngine and transition to the level."""
        Drawable.CAMERA_OFFSET = vec(0, 0)
        self.game         = GameEngine(mapFile=mapFile)
        self._activeLevel = levelName
        self._activeMap   = mapFile
        if levelName == "level1":
            self.state.startLevel1()
        elif levelName == "level3":
            self.state.startLevel3()

    def _restartLevel(self):
        """Fresh game on same map. Resume if paused, stay in level if dead/won."""
        if self._activeMap is None:
            return
        if self.game:
            self.game.stop()
        self.game = GameEngine(mapFile=self._activeMap)
        if self.state.isPaused():
            self._resume()

    def _resume(self):
        """Return to whichever level was active before pausing."""
        if self._activeLevel == "level1":
            self.state.resumeLevel1()
        elif self._activeLevel == "level2":
            self.state.resumeLevel2()
        elif self._activeLevel == "level3":
            self.state.resumeLevel3()