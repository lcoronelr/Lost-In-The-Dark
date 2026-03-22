from FSMs import AbstractGameFSM
from statemachine import State

class ScreenManagerFSM(AbstractGameFSM):
    """
    States
    ------
    mainMenu : showing the main menu
    level1   : placeholder level
    level2   : placeholder level  
    level3   : the dungeon level (currently implemented)

    Transitions
    -----------
    startLevel1 / startLevel2 / startLevel3 : mainMenu -> level
    quitGame                                 : any level -> mainMenu
    """

    mainMenu = State(initial=True)
    level1   = State()
    level2   = State()
    level3   = State()

    startLevel1 = mainMenu.to(level1)
    startLevel2 = mainMenu.to(level2)
    startLevel3 = mainMenu.to(level3)

    quitGame = level1.to(mainMenu) | level2.to(mainMenu) | level3.to(mainMenu)

    def isInGame(self):
        return self != "mainMenu"