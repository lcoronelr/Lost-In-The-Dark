import pygame
from utils import RESOLUTION, vec
from gameObjects.drawable import Drawable

class LightingOverlay:
    """
    Renders a full-screen dark overlay with a soft circular
    light cutout centred on the torch player.

    Uses a mask surface blitted with BLEND_RGBA_MULT so only
    the lit area is visible.
    """

    def __init__(self):
        self._surface = pygame.Surface(list(map(int, RESOLUTION)), pygame.SRCALPHA)

    def draw(self, drawSurface, torch):
        self._surface.fill((0, 0, 0, 240))   # near-black darkness

        # Centre of torch in screen coords
        size   = torch.getSize()
        centre = torch.position + size // 2 - Drawable.CAMERA_OFFSET
        cx, cy = int(centre[0]), int(centre[1])
        r      = int(torch.lightRadius)

        # Soft glow: draw concentric circles from dark-edge to fully transparent
        for i in range(r, 0, -1):
            alpha = int(240 * (i / r) ** 1.8)   # brighter near centre
            pygame.draw.circle(self._surface, (0, 0, 0, alpha), (cx, cy), i)

        # Punch out the centre completely
        core = max(1, r // 4)
        pygame.draw.circle(self._surface, (0, 0, 0, 0), (cx, cy), core)

        drawSurface.blit(self._surface, (0, 0))