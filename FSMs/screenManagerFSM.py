from FSMs import AbstractGameFSM
from statemachine import State

class ScreenManagerFSM(AbstractGameFSM):

    mainMenu = State(initial=True)
    level1   = State()
    level2   = State()
    level3   = State()
    paused   = State()

    startLevel1 = mainMenu.to(level1)
    startLevel2 = mainMenu.to(level2)
    startLevel3 = mainMenu.to(level3)

    pause = level1.to(paused) | level2.to(paused) | level3.to(paused)

    resumeLevel1 = paused.to(level1)
    resumeLevel2 = paused.to(level2)
    resumeLevel3 = paused.to(level3)

    quitGame = paused.to(mainMenu)  | \
               level1.to(mainMenu)  | \
               level2.to(mainMenu)  | \
               level3.to(mainMenu)

    def isInGame(self):
        return self.current_state.id in ["level1", "level2", "level3", "paused"]

    def isPaused(self):
        return self == "paused"