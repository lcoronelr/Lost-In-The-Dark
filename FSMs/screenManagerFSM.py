from FSMs import AbstractGameFSM
from statemachine import State

class ScreenManagerFSM(AbstractGameFSM):
    """
    States
    ------
    mainMenu : main menu
    level1   : level 1
    level2   : level 2 (coming soon)
    level3   : level 3 dungeon
    paused   : ESC overlay shown over any level

    Transitions
    -----------
    startLevel1/2/3 : mainMenu -> level
    pause           : any level -> paused
    resume          : paused -> back to whichever level was active
    quitGame        : paused or any level -> mainMenu
    """

    mainMenu = State(initial=True)
    level1   = State()
    level2   = State()
    level3   = State()
    paused   = State()

    startLevel1 = mainMenu.to(level1)
    startLevel2 = mainMenu.to(level2)
    startLevel3 = mainMenu.to(level3)

    # Pause from any level
    pause = level1.to(paused) | level2.to(paused) | level3.to(paused)

    # Resume goes back to whichever level we came from
    resumeLevel1 = paused.to(level1)
    resumeLevel2 = paused.to(level2)
    resumeLevel3 = paused.to(level3)

    # Quit from paused or directly from a level
    quitGame = paused.to(mainMenu)  | \
               level1.to(mainMenu)  | \
               level2.to(mainMenu)  | \
               level3.to(mainMenu)

    def isInGame(self):
        return self.current_state.id in ["level1", "level2", "level3", "paused"]

    def isPaused(self):
        return self == "paused"