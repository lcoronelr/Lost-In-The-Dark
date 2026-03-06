import json
import pygame
from os.path import join, dirname, abspath
from gameObjects.drawable import Drawable
from utils import vec
# https://www.pygame.org/docs/ref/surface.html
# Tdiled JSON map format from https://doc.mapeditor.org/en/stable/reference/json-map-format/


TILE_SIZE = 16

_HERE    = dirname(abspath(__file__))
_PROJECT = dirname(_HERE)

class TileMap:
    """
    Loads a Tiled .tmj map and renders all tile layers and exposses the walls.s
    """

    TILESET_IMAGE  = "Dungeon_Tileset.png"  # 160x160, 10x10 grid of 16px tiles
    TILESET_COLS   = 10
    TILESET_ROWS   = 10
    TILESET_MARGIN = 0

    def __init__(self, mapPath):
        with open(mapPath) as f:
            data = json.load(f)

        self.tileW  = data["tilewidth"]   # should be 16
        self.tileH  = data["tileheight"]  # should be 16
        self.mapW   = data["width"]       # should be 80 tiles
        self.mapH   = data["height"]      # should be 60 tiles
        self.pixelW = self.mapW * self.tileW   # should be 1280
        self.pixelH = self.mapH * self.tileH   # should be 960

        rawSheet = pygame.image.load(join(_PROJECT, "images", self.TILESET_IMAGE)).convert_alpha()
        self._tiles = self._sliceTileset(rawSheet)

        # Pre-render all tile layers onto one surface for speed
        self._surface = pygame.Surface((self.pixelW, self.pixelH), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 0))

        TILE_LAYERS = ["background", "corridors", "floor squares", "door+walls"]
        for layer in data["layers"]:
            if layer["type"] == "tilelayer" and layer["name"] in TILE_LAYERS:
                self._renderLayer(layer)

        # Build wall rects from walls
        self.wallRects = []
        for layer in data["layers"]:
            if layer["type"] == "objectgroup" and layer["name"] == "Walls":
                for obj in layer["objects"]:
                    self.wallRects.append(pygame.Rect(obj["x"], obj["y"], obj["width"], obj["height"]))

    def _sliceTileset(self, sheet):
        """Return dict: gid -> Surface."""
        tiles = {}
        gid = 1
        for row in range(self.TILESET_ROWS):
            for col in range(self.TILESET_COLS):
                rect = pygame.Rect(col * self.tileW,self.TILESET_MARGIN + row * self.tileH,self.tileW,self.tileH)
                surf = pygame.Surface((self.tileW, self.tileH), pygame.SRCALPHA)
                surf.blit(sheet, (0, 0), rect)
                tiles[gid] = surf
                gid += 1
        return tiles

    def _renderLayer(self, layer):
        data = layer["data"]
        W    = layer["width"]
        for idx, gid in enumerate(data):
            if gid == 0:
                continue
            tile = self._tiles.get(gid)
            if tile is None:
                continue
            col = idx % W
            row = idx // W
            self._surface.blit(tile, (col * self.tileW, row * self.tileH))


    def draw(self, drawSurface):
        """Blit only the visible portion (camera window) of the map."""
        offset = Drawable.CAMERA_OFFSET
        srcRect = pygame.Rect(offset[0], offset[1],drawSurface.get_width(),drawSurface.get_height())
        drawSurface.blit(self._surface, (0, 0), srcRect)

    def getSize(self):
        return vec(self.pixelW, self.pixelH)