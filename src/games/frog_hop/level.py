"""
Frog Hop — Level builder.
Loads per-level configs (map + fruits + traps).
No direct pygame import — uses engine Renderer.
"""
import os
from src.pyengine2D import Node2D, Engine
from src.pyengine2D.scene.tilemap import TilemapNode

_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BG_PATH = os.path.join(_SRC, "Free", "Background", "Green.png")
MAP_DIR = os.path.join(_SRC, "games", "frog_hop", "maps")

# ── Level configurations ────────────────────────────────────────────
LEVELS = [
    {
        "map": "map_data_1.json",
        "player_start": (50, 400),
        "fruits": [
            (280, 360, "Apple"),
            (490, 280, "Cherries"),
            (700, 210, "Orange"),
            (520, 224, "Strawberry"),
            (950, 160, "Bananas"),
            (1150, 310, "Kiwi"),
            (1400, 240, "Melon"),
            (1650, 160, "Pineapple"),
            (1900, 360, "Apple"),
            (1950, 360, "Cherries"),
        ],
        "traps": [],  # Level 1 is the tutorial — no traps
        "enemies": [
            ("Mask Dude", 500, 350, {"speed": 60})
        ],
    },
    {
        "map": "map_data_2.json",
        "player_start": (64, 400),
        "fruits": [
            (192, 416, "Apple"),
            (176, 352, "Cherries"),
            (320, 288, "Orange"),
            (464, 224, "Strawberry"),
            (624, 160, "Bananas"),
            (784, 288, "Kiwi"),
            (1072, 160, "Melon"),
            (1316, 352, "Pineapple"),
        ],
        "traps": [
            # (type, x, y, **kwargs)
            ("spikes", 304, 304),
            ("spikes", 336, 304),
            ("fire",   928, 224),
            ("saw",    580, 173, {"end_x": 680, "end_y": 173, "speed": 100}),
            ("trampoline", 1250, 370),
            ("fire",   1456, 352),
            ("spikes", 1488, 368),
        ],
        "enemies": [
            ("Pink Man", 500, 350, {"speed": 80}),
            ("Pink Man", 1100, 350, {"speed": 80})
        ],
    },
    {
        "map": "map_data_3.json",
        "player_start": (50, 484),
        "fruits": [
            (144, 448, "Apple"),
            (272, 384, "Cherries"),
            (400, 320, "Orange"),
            (528, 256, "Strawberry"),
            (656, 192, "Bananas"),
            (976, 192, "Kiwi"),
            (912, 128, "Melon"),
            (1104, 128, "Pineapple"),
            (1392, 320, "Apple"),
            (1776, 512, "Cherries"),
        ],
        "traps": [
            ("spikes", 464, 336),
            ("fire",   688, 192),
            ("saw",    780, 205, {"end_x": 840, "end_y": 205, "speed": 130}),
            ("saw",    940, 205, {"end_x": 1000, "end_y": 205, "speed": 140}),
            ("spikes", 1104, 208),
            ("saw",    1200, 269, {"end_x": 1280, "end_y": 269, "speed": 150}),
            ("fire",   1520, 384),
            ("trampoline", 1680, 530),
            ("spikes", 1840, 528),
            ("spikes", 1872, 528),
        ],
        "enemies": [
            ("Virtual Guy", 600, 400, {"speed": 120}),
            ("Ninja Frog", 1400, 400, {"speed": 120}) # Using ninja frog sprite as enemy for fun
        ],
    },
]


class BackgroundLayer(Node2D):
    """Tiled background drawn behind everything with varying scroll speeds."""

    def __init__(self, name, bg_path, scroll_factor=0.3, tile_size=128):
        super().__init__(name, 0, 0)
        self.scroll_factor = scroll_factor
        r = Engine.instance.renderer
        bg_tile = r.load_image(bg_path, alpha=True) # allow alpha for dust
        self._tile = r.scale_surface(bg_tile, tile_size, tile_size)
        self._tile_size = tile_size

    def render(self, surface):
        screen_w, screen_h = Engine.instance.renderer.get_surface_size(surface)
        cam_x, cam_y = 0, 0
        if Node2D.camera:
            hw = Engine.instance.virtual_w // 2 if Engine.instance else 400
            hh = Engine.instance.virtual_h // 2 if Engine.instance else 300
            cx, cy = Node2D.camera.get_global_position()
            cam_x = cx - hw
            cam_y = cy - hh

        px = int(cam_x * self.scroll_factor)
        py = int(cam_y * self.scroll_factor)
        ts = self._tile_size

        start_x = -(px % ts)
        start_y = -(py % ts)

        r = Engine.instance.renderer
        for yy in range(start_y, screen_h + ts, ts):
            for xx in range(start_x, screen_w + ts, ts):
                r.blit(surface, self._tile, (xx, yy))

        super().render(surface)


def build_level(world_node, collision_world, level_index=0):
    """Construct level *level_index* inside *world_node*.

    Returns ``(fruits, traps, player_start)``.
    """
    cfg = LEVELS[level_index]

    # Multiple Background Layers
    colors = ["Green.png", "Blue.png", "Brown.png"]
    bg_color = colors[level_index % len(colors)]
    bg_path = os.path.join(_SRC, "Free", "Background", bg_color)
    dust_path = os.path.join(_SRC, "Free", "Other", "Dust Particle.png")
    
    bg0 = BackgroundLayer("BG_Back", bg_path, scroll_factor=0.2, tile_size=128)
    bg1 = BackgroundLayer("BG_Dust", dust_path, scroll_factor=0.5, tile_size=128)
    
    world_node.add_child(bg0)
    world_node.add_child(bg1)

    # Tilemap
    map_path = os.path.join(MAP_DIR, cfg["map"])
    tilemap = TilemapNode("LevelMap")
    if os.path.exists(map_path):
        tilemap.load_from_json(map_path)
    else:
        print(f"WARNING: {cfg['map']} not found at {map_path}!")
    world_node.add_child(tilemap)

    # Fruits
    from .entities.fruit import Fruit
    fruits = []
    for i, (fx, fy, fname) in enumerate(cfg["fruits"]):
        fruit = Fruit(f"Fruit_{i}", fx, fy, collision_world, fruit_name=fname)
        world_node.add_child(fruit)
        fruits.append(fruit)

    # Traps
    from .entities.trap import Spikes, Saw, Fire, Trampoline
    trap_classes = {
        "spikes": Spikes,
        "saw": Saw,
        "fire": Fire,
        "trampoline": Trampoline,
    }
    traps = []
    for i, entry in enumerate(cfg.get("traps", [])):
        ttype = entry[0]
        tx, ty = entry[1], entry[2]
        kwargs = entry[3] if len(entry) > 3 else {}
        cls = trap_classes[ttype]
        trap = cls(f"Trap_{ttype}_{i}", tx, ty, collision_world, **kwargs)
        world_node.add_child(trap)
        traps.append(trap)

    # Enemies
    from .entities.enemy import Enemy
    for i, entry in enumerate(cfg.get("enemies", [])):
        etype = entry[0]
        ex, ey = entry[1], entry[2]
        kwargs = entry[3] if len(entry) > 3 else {}
        enemy = Enemy(f"Enemy_{i}", ex, ey, collision_world, enemy_type=etype, **kwargs)
        world_node.add_child(enemy)

    player_start = cfg.get("player_start", (50, 400))
    return fruits, traps, player_start
