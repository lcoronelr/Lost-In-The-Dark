import pygame
from utils import MAX_HEALTH, RESOLUTION, MIN_INTENSITY, MAX_INTENSITY

class HUD:
    """Simple heads-up display: health bar + flame state."""

    BAR_W  = 60
    BAR_H  = 6
    MARGIN = 4

        ## adapted from: https://www.youtube.com/watch?v=E82_hdoe06M


    STATE_COLORS = {
        "low"    : (60,  180, 255),
        "normal" : (255, 140,   0),
        "high"   : (255, 255, 120),
    }

    def __init__(self):
        pygame.font.init()
        self._font = pygame.font.SysFont("monospace", 8)

    def draw(self, surface, torch):
        x, y = self.MARGIN, self.MARGIN

        # health bar 
        pct  = torch.health / MAX_HEALTH
        bg   = pygame.Rect(x, y, self.BAR_W, self.BAR_H)
        fill = pygame.Rect(x, y, int(self.BAR_W * pct), self.BAR_H)
        pygame.draw.rect(surface, (60, 0, 0),   bg)
        pygame.draw.rect(surface, (220, 50, 50), fill)
        pygame.draw.rect(surface, (200, 200, 200), bg, 1)

        #flame state 
        state = torch.FSMflame.current_state.id
        color = self.STATE_COLORS.get(state, (255, 255, 255))
        label = self._font.render(f"FLAME: {state.upper()}", True, color)
        surface.blit(label, (x, y + self.BAR_H + 2))

        #intensity bar
        ix = x + self.BAR_W + 6
        t  = (torch.lightRadius - MIN_INTENSITY) / (MAX_INTENSITY - MIN_INTENSITY)
        intensity_fill = pygame.Rect(ix, y, int(self.BAR_W * t), self.BAR_H)
        intensity_bg   = pygame.Rect(ix, y, self.BAR_W, self.BAR_H)
        pygame.draw.rect(surface, (30, 30, 0),   intensity_bg)
        pygame.draw.rect(surface, color,          intensity_fill)
        pygame.draw.rect(surface, (200, 200, 200), intensity_bg, 1)
        hint = self._font.render("Q    E", True, (255, 255, 255))
        surface.blit(hint, (ix, y + self.BAR_H + 2))


        #inventory ---- goes here 