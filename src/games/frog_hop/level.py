"""
Frog Hop — Level builder.
Creates platforms from terrain tileset + places fruits.
No direct pygame import — uses engine Renderer.
"""
import os
from src.pyengine2D import Node2D, Collider2D, RectangleNode, Engine
from src.pyengine2D.scene.tilemap import TilemapNode

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TERRAIN_PATH = os.path.join(_SRC, "Free", "Terrain", "Terrain (16x16).png")
BG_PATH = os.path.join(_SRC, "Free", "Background", "Green.png")

# Each platform:  (x, y, width_tiles, height_tiles)
PLATFORMS = [
    (0,   500, 12, 1),
    (250, 400, 4,  2),
    (450, 320, 4,  2),
    (650, 250, 5,  2),
    (900, 200, 4,  5),
    (1100, 350, 6, 1),
    (1350, 280, 5, 1),
    (1600, 200, 4, 1),
    (1800, 400, 8, 1),
    (500,  150, 3, 1),
]

# Fruit positions: (x, y, fruit_name)
FRUIT_SPAWNS = [
    (280, 360, "Apple"),
    (490, 280, "Cherries"),
    (700, 210, "Orange"),
    (520, 110, "Strawberry"),
    (950, 160, "Bananas"),
    (1150, 310, "Kiwi"),
    (1400, 240, "Melon"),
    (1650, 160, "Pineapple"),
    (1900, 360, "Apple"),
    (1950, 360, "Cherries"),
]

TILE = 16
SCALE = 2
SCALED_TILE = TILE * SCALE   # 32


class Background(Node2D):
    """Tiled background drawn behind everything."""

    def __init__(self, name, bg_path, world_w, world_h):
        super().__init__(name, 0, 0)
        r = Engine.instance.renderer
        bg_tile = r.load_image(bg_path, alpha=False)
        tile_size = 128
        self._tile = r.scale_surface(bg_tile, tile_size, tile_size)
        self._tile_size = tile_size

    def render(self, surface):
        screen_w, screen_h = Engine.instance.renderer.get_surface_size(surface)
        cam_x, cam_y = 0, 0
        if Node2D.camera:
            hw = Engine.instance.virtual_w // 2 if Engine.instance else 400
            hh = Engine.instance.virtual_h // 2 if Engine.instance else 300
            cam_x = Node2D.camera.local_x - hw
            cam_y = Node2D.camera.local_y - hh

        px = int(cam_x * 0.3)
        py = int(cam_y * 0.3)
        ts = self._tile_size

        start_x = -(px % ts)
        start_y = -(py % ts)

        r = Engine.instance.renderer
        for yy in range(start_y, screen_h + ts, ts):
            for xx in range(start_x, screen_w + ts, ts):
                r.blit(surface, self._tile, (xx, yy))

        super().render(surface)


def build_level(world_node, collision_world):
    """Construct the full level inside *world_node*. Returns fruit list."""
    bg = Background("BG", BG_PATH, 2500, 800)
    world_node.add_child(bg)

    # Convert PLATFORMS into a tilemap grid
    # Now we simply load the map_data.json output by the draw2d.py map editor!
    map_dir = os.path.join(_SRC, "games", "frog_hop", "maps")
    map_path = os.path.join(map_dir, "map_data.json")
    tilemap = TilemapNode("LevelMap")
    
    if os.path.exists(map_path):
        tilemap.load_from_json(map_path)
    else:
        print(f"WARNING: map.json not found at {map_path}! Please run python draw2d.py to create it.")
        
    world_node.add_child(tilemap)

    from .entities.fruit import Fruit
    fruits = []
    for i, (fx, fy, fname) in enumerate(FRUIT_SPAWNS):
        fruit = Fruit(f"Fruit_{i}", fx, fy, collision_world, fruit_name=fname)
        world_node.add_child(fruit)
        fruits.append(fruit)

    return fruits
