"""
The `TileMap` class loads a Tiled .tmx map, renders tile layers, and exposes wall information for a
game environment.
"""
import json
import pygame
from os.path import join, dirname, abspath
from gameObjects.drawable import Drawable
from utils import vec

TILE_SIZE = 16

_HERE    = dirname(abspath(__file__))
_PROJECT = dirname(_HERE)

class TileMap:

    TILESET_IMAGE  = "Dungeon_Tileset.png"
    TILESET_COLS   = 10
    TILESET_ROWS   = 10
    TILESET_MARGIN = 0

    TILE_LAYERS = ["background", "corridors", "floor squares", "door+walls",
                   "Tile Layer 1", "objects", "walls"]

    def __init__(self, mapPath):
        with open(mapPath) as f:
            data = json.load(f)

        self.tileW  = data["tilewidth"]
        self.tileH  = data["tileheight"]
        self.mapW   = data["width"]
        self.mapH   = data["height"]
        self.pixelW = self.mapW * self.tileW
        self.pixelH = self.mapH * self.tileH

        rawSheet = pygame.image.load(join(_PROJECT, "images", self.TILESET_IMAGE)).convert_alpha()
        self._tiles = self._sliceTileset(rawSheet)

        self._surface = pygame.Surface((self.pixelW, self.pixelH), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 0))

        for layer in data["layers"]:
            if layer["type"] == "tilelayer" and layer["name"] in self.TILE_LAYERS:
                self._renderLayer(layer)

        # Build wall rects
        self.wallRects = []
        self.doorRects = {}

        for layer in data["layers"]:
            if layer["type"] != "objectgroup":
                continue
            for obj in layer["objects"]:
                rect  = pygame.Rect(int(obj["x"]), int(obj["y"]),
                                    int(obj.get("width", 16)), int(obj.get("height", 16)))
                props = {p["name"]: p["value"] for p in obj.get("properties", [])}
                door_id = props.get("door")
                if door_id == "final_gate":
                    self.doorRects[door_id] = rect  # win zone only, not a wall
                elif door_id:
                    self.doorRects[door_id] = rect
                    self.wallRects.append(rect)   # door starts as solid wall
                elif layer["name"].lower() == "walls":
                    self.wallRects.append(rect)   # normal wall

        # Read spawn points from ALL object layers
        self.spawnPoints = {}
        SKIP_LAYERS = {"walls"}
        for layer in data["layers"]:
            if layer["type"] != "objectgroup":
                continue
            if layer["name"].lower() in SKIP_LAYERS:
                continue
            for obj in layer["objects"]:
                props = {p["name"]: p["value"] for p in obj.get("properties", [])}

                for k, v in props.items():
                    self.spawnPoints.setdefault(k, [])
                    self.spawnPoints[k].append((obj["x"], obj["y"]))

                if not props:
                    layerKey = layer["name"].lower().replace(" ", "_")
                    self.spawnPoints.setdefault(layerKey, [])
                    self.spawnPoints[layerKey].append((obj["x"], obj["y"]))

        # Read sequence torches — layer named "sequence", property note:1-4
        self.sequenceTorches = []
        for layer in data["layers"]:
            if layer["type"] == "objectgroup" and layer["name"].lower() == "sequence":
                for obj in layer["objects"]:
                    props = {p["name"]: p["value"] for p in obj.get("properties", [])}
                    note = props.get("note")
                    if note is not None:
                        self.sequenceTorches.append(((obj["x"], obj["y"]), int(note)))

    def openDoor(self, doorId):
        if doorId in self.doorRects:
            rect = self.doorRects[doorId]
            if rect in self.wallRects:
                self.wallRects.remove(rect)
            del self.doorRects[doorId]

    def getSpawn(self, spawnType, index=0):
        points = self.spawnPoints.get(spawnType, [])
        if index < len(points):
            return points[index]
        return None

    def _sliceTileset(self, sheet):
        tiles = {}
        gid = 1
        for row in range(self.TILESET_ROWS):
            for col in range(self.TILESET_COLS):
                rect = pygame.Rect(col * self.tileW,
                                   self.TILESET_MARGIN + row * self.tileH,
                                   self.tileW, self.tileH)
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
        offset  = Drawable.CAMERA_OFFSET
        srcRect = pygame.Rect(offset[0], offset[1],
                              drawSurface.get_width(), drawSurface.get_height())
        drawSurface.blit(self._surface, (0, 0), srcRect)

    def getSize(self):
        return vec(self.pixelW, self.pixelH)