"""
TilemapNode — efficient tilemap rendering, auto-collision, and viewport streaming.

Loads map data from a Python dict (JSON-compatible) or a .tmx XML file.
Solid tile layers auto-generate Collider2D nodes for physics.
Each layer is baked to a cached surface for fast rendering.
"""
import json
import os
import xml.etree.ElementTree as ET

import pygame

from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.collision.collider2d import Collider2D
from src.pyengine2D.rendering.surface_cache import SurfaceCache


class TilemapNode(Node2D):
    """
    A tilemap node that loads layered tile data, renders efficiently
    via cached surfaces, and optionally generates collision geometry.

    Map dict format::

        {
            "tile_width": 32,
            "tile_height": 32,
            "layers": [
                {
                    "name": "Ground",
                    "solid": true,
                    "parallax_factor": [1.0, 1.0],   # optional
                    "tiles": [[1, 1, 0, ...], ...]    # 2D grid (row-major)
                },
                ...
            ],
            "tilesets": [
                {
                    "image": "path/to/tileset.png",
                    "tile_width": 32,
                    "tile_height": 32
                }
            ]
        }

    Features:
        - Baked layer surfaces (draw once, blit fast).
        - Auto-generated Collider2D nodes for solid tiles (row-merged).
        - Viewport streaming (only render visible tile region).
        - Multi-layer parallax support.
        - Debug overlay (tile borders + solid markers via show_debug).
    """

    def __init__(self, name="Tilemap"):
        super().__init__(name, 0, 0)
        self.tile_width = 0
        self.tile_height = 0
        self.map_cols = 0
        self.map_rows = 0
        self.layers = []           # list of layer dicts
        self.tileset_surfaces = [] # loaded tileset images
        self.tileset_cols = []     # columns per tileset
        self._surface_cache = SurfaceCache()
        self._collision_nodes = [] # generated Collider2D nodes
        self.show_debug = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_from_dict(self, data, base_path=""):
        """Load map from a Python dict (mirrors JSON structure)."""
        self.tile_width = data.get("tile_width", 32)
        self.tile_height = data.get("tile_height", 32)
        self.layers = data.get("layers", [])

        # Determine map dimensions from first layer
        if self.layers and self.layers[0].get("tiles"):
            self.map_rows = len(self.layers[0]["tiles"])
            self.map_cols = len(self.layers[0]["tiles"][0]) if self.map_rows else 0
            
            # Apply offset from first layer if present
            offset_col = self.layers[0].get("offset_x", 0)
            offset_row = self.layers[0].get("offset_y", 0)
            self.local_x = offset_col * self.tile_width
            self.local_y = offset_row * self.tile_height

        # Load tilesets
        self.tileset_surfaces = []
        self.tileset_cols = []
        for ts in data.get("tilesets", []):
            img_path = ts["image"]
            if base_path:
                joined_path = os.path.join(base_path, img_path)
                if os.path.exists(joined_path):
                    img_path = joined_path
            surf = pygame.image.load(img_path).convert_alpha()
            
            # Handle option to scale tileset up at load time
            scale = ts.get("scale", 1)
            if scale != 1:
                w, h = surf.get_size()
                surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
                
            self.tileset_surfaces.append(surf)
            self.tileset_cols.append(surf.get_width() // ts.get("tile_width", self.tile_width))

        self._bake_layers()
        self._generate_colliders()

    def load_from_json(self, json_path):
        """Load map from a JSON file."""
        base_path = os.path.dirname(json_path)
        with open(json_path, "r") as f:
            data = json.load(f)
        self.load_from_dict(data, base_path=base_path)

    def load_from_tmx(self, tmx_path):
        """
        Load map from a Tiled .tmx XML file (CSV layer data only).
        Constructs an internal dictionary matching load_from_dict() format.
        """
        base_path = os.path.dirname(tmx_path)
        tree = ET.parse(tmx_path)
        root = tree.getroot()

        data = {
            "tile_width": int(root.attrib.get("tilewidth", 32)),
            "tile_height": int(root.attrib.get("tileheight", 32)),
            "layers": [],
            "tilesets": []
        }

        # Parse tilesets
        for ts_node in root.findall("tileset"):
            firstgid = int(ts_node.attrib.get("firstgid", 1))
            name = ts_node.attrib.get("name", "Tileset")
            tw = int(ts_node.attrib.get("tilewidth", data["tile_width"]))
            th = int(ts_node.attrib.get("tileheight", data["tile_height"]))
            
            # The image tag is generally a child of tileset in embedded sets
            img_node = ts_node.find("image")
            if img_node is not None:
                source = img_node.attrib.get("source")
                data["tilesets"].append({
                    "image": source,
                    "tile_width": tw,
                    "tile_height": th
                })

        # Parse layers
        for layer_node in root.findall("layer"):
            layer_name = layer_node.attrib.get("name", "Layer")
            width = int(layer_node.attrib.get("width", 0))
            height = int(layer_node.attrib.get("height", 0))
            
            # Custom Tiled properties (like "solid": true/false)
            is_solid = False
            props = layer_node.find("properties")
            if props is not None:
                for p in props.findall("property"):
                    if p.attrib.get("name") == "solid" and p.attrib.get("value") == "true":
                        is_solid = True
            
            # Parse CSV data
            data_node = layer_node.find("data")
            if data_node is not None and data_node.attrib.get("encoding") == "csv":
                raw_csv = data_node.text.strip()
                raw_ints = [int(v.strip()) for v in raw_csv.replace("\n", "").split(",") if v.strip()]
                
                # Convert 1D CSV list to 2D row-major list
                tiles_2d = []
                for r in range(height):
                    row_data = raw_ints[r * width : (r + 1) * width]
                    tiles_2d.append(row_data)
                    
                data["layers"].append({
                    "name": layer_name,
                    "solid": is_solid,
                    "tiles": tiles_2d
                })

        self.load_from_dict(data, base_path=base_path)

    # ------------------------------------------------------------------
    # Baking layers to cached surfaces
    # ------------------------------------------------------------------

    def _bake_layers(self):
        """Pre-render each layer to chunked surfaces for fast, culled blitting."""
        self._surface_cache.invalidate()
        self.chunk_size = 32

        for layer_idx, layer in enumerate(self.layers):
            tiles = layer.get("tiles", [])
            if not tiles:
                continue

            rows = len(tiles)
            cols = len(tiles[0]) if rows else 0
            
            chunks_x = (cols + self.chunk_size - 1) // self.chunk_size
            chunks_y = (rows + self.chunk_size - 1) // self.chunk_size

            for cy in range(chunks_y):
                for cx in range(chunks_x):
                    c_cols = min(self.chunk_size, cols - cx * self.chunk_size)
                    c_rows = min(self.chunk_size, rows - cy * self.chunk_size)
                    c_w = c_cols * self.tile_width
                    c_h = c_rows * self.tile_height
                    
                    if c_w <= 0 or c_h <= 0:
                        continue

                    surf = pygame.Surface((c_w, c_h), pygame.SRCALPHA)
                    surf.fill((0, 0, 0, 0))

                    has_tiles = False
                    for r in range(c_rows):
                        for c in range(c_cols):
                            global_r = cy * self.chunk_size + r
                            global_c = cx * self.chunk_size + c
                            tile_id = tiles[global_r][global_c]
                            if tile_id <= 0:
                                continue
                            has_tiles = True
                            self._draw_tile(surf, tile_id, c, r)

                    if has_tiles:
                        cache_key = f"chunk_{layer_idx}_{cx}_{cy}"
                        self._surface_cache.store(cache_key, surf)

    def _draw_tile(self, target, tile_id, col, row):
        """Blit a single tile from the first tileset onto *target*."""
        if not self.tileset_surfaces:
            return
        ts_surf = self.tileset_surfaces[0]
        ts_cols = self.tileset_cols[0]
        # tile_id 1-based (0 = empty)
        idx = tile_id - 1
        src_col = idx % ts_cols
        src_row = idx // ts_cols
        src_rect = pygame.Rect(
            src_col * self.tile_width,
            src_row * self.tile_height,
            self.tile_width,
            self.tile_height,
        )
        dest_x = col * self.tile_width
        dest_y = row * self.tile_height
        target.blit(ts_surf, (dest_x, dest_y), src_rect)

    # ------------------------------------------------------------------
    # Collision generation (row-merged)
    # ------------------------------------------------------------------

    def _generate_colliders(self):
        """Auto-create Collider2D nodes for solid tiles, merging adjacent tiles in each row."""
        # Remove old colliders
        for node in self._collision_nodes:
            self.remove_child(node)
        self._collision_nodes.clear()

        for layer in self.layers:
            if not layer.get("solid", False):
                continue
            tiles = layer.get("tiles", [])
            for r, row_data in enumerate(tiles):
                c = 0
                while c < len(row_data):
                    if row_data[c] <= 0:
                        c += 1
                        continue
                    # Start of a solid run
                    start_c = c
                    while c < len(row_data) and row_data[c] > 0:
                        c += 1
                    # Create a merged collider for columns [start_c, c)
                    cw = (c - start_c) * self.tile_width
                    ch = self.tile_height
                    cx = start_c * self.tile_width
                    cy = r * self.tile_height
                    col_name = f"TileCol_{layer.get('name', '')}_{r}_{start_c}"
                    col_node = Collider2D(col_name, cx, cy, cw, ch, is_static=True)
                    col_node.layer = "wall"
                    col_node.mask = set()
                    self.add_child(col_node)
                    self._collision_nodes.append(col_node)

    # ------------------------------------------------------------------
    # Rendering (viewport streaming)
    # ------------------------------------------------------------------

    def render(self, surface):
        """Render visible portion of each layer, using cached chunks."""
        cam_x, cam_y = 0.0, 0.0
        screen_w, screen_h = surface.get_size()

        if Node2D.camera:
            from src.pyengine2D.core.engine import Engine
            half_w = Engine.instance.virtual_w // 2 if Engine.instance else screen_w // 2
            half_h = Engine.instance.virtual_h // 2 if Engine.instance else screen_h // 2
            cx, cy = Node2D.camera.get_global_position()
            cam_x = cx - half_w
            cam_y = cy - half_h

        gx, gy = self.get_global_position()
        screen_rect = pygame.Rect(-128, -128, screen_w + 256, screen_h + 256)
        chunk_size = getattr(self, 'chunk_size', 32)
        from src.pyengine2D.core.engine import Engine
        engine_instance = Engine.instance

        for layer_idx, layer in enumerate(self.layers):
            tiles = layer.get("tiles", [])
            if not tiles: continue
            
            rows = len(tiles)
            cols = len(tiles[0]) if rows else 0
            chunks_x = (cols + chunk_size - 1) // chunk_size
            chunks_y = (rows + chunk_size - 1) // chunk_size

            # Parallax factor (optional)
            pfx = layer.get("parallax_factor", [1.0, 1.0])[0]
            pfy = layer.get("parallax_factor", [1.0, 1.0])[1]

            for cy_idx in range(chunks_y):
                for cx_idx in range(chunks_x):
                    cache_key = f"chunk_{layer_idx}_{cx_idx}_{cy_idx}"
                    chunk_surf = self._surface_cache.get(cache_key)
                    if chunk_surf is None:
                        continue

                    chunk_local_x = cx_idx * chunk_size * self.tile_width
                    chunk_local_y = cy_idx * chunk_size * self.tile_height

                    draw_x = gx + chunk_local_x - cam_x * pfx
                    draw_y = gy + chunk_local_y - cam_y * pfy
                    
                    c_w, c_h = chunk_surf.get_size()
                    chunk_rect = pygame.Rect(draw_x, draw_y, c_w, c_h)
                    
                    if screen_rect.colliderect(chunk_rect):
                        if engine_instance:
                            engine_instance.renderer.blit(surface, chunk_surf, (int(draw_x), int(draw_y)))
                        else:
                            surface.blit(chunk_surf, (int(draw_x), int(draw_y)))

        # Debug overlay
        if self.show_debug:
            self._render_debug(surface, cam_x, cam_y, gx, gy, screen_w, screen_h)

        super().render(surface)

    def _render_debug(self, surface, cam_x, cam_y, gx, gy, screen_w, screen_h):
        """Draw tile borders and solid markers."""
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        if not renderer:
            return

        start_col = max(0, int(cam_x / self.tile_width))
        start_row = max(0, int(cam_y / self.tile_height))
        end_col = min(self.map_cols, int((cam_x + screen_w) / self.tile_width) + 1)
        end_row = min(self.map_rows, int((cam_y + screen_h) / self.tile_height) + 1)

        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                sx = int(c * self.tile_width + gx - cam_x)
                sy = int(r * self.tile_height + gy - cam_y)
                renderer.draw_rect(surface, (60, 60, 60), sx, sy,
                                   self.tile_width, self.tile_height, width=1)

                # Check if any layer marks this tile as solid
                for layer in self.layers:
                    if layer.get("solid"):
                        tiles = layer.get("tiles", [])
                        if r < len(tiles) and c < len(tiles[r]) and tiles[r][c] > 0:
                            renderer.draw_rect(surface, (255, 0, 0, 100),
                                               sx + 2, sy + 2,
                                               self.tile_width - 4, self.tile_height - 4, width=1)
                            break

    # ------------------------------------------------------------------
    # Streaming helpers
    # ------------------------------------------------------------------

    def stream_to_camera(self, camera, margin_tiles=2):
        """
        Hint method: ensures only tiles near *camera* are considered for
        rendering.  The default render() already viewport-clips via
        src_rect, so this is effectively a no-op for most cases.
        Override for chunk-based streaming of very large maps (>10k tiles).
        """
        pass  # viewport clipping is already handled in render()

    def get_collider_count(self):
        """Number of auto-generated collision nodes."""
        return len(self._collision_nodes)

    def invalidate_cache(self):
        """Force re-bake of all layer surfaces (e.g. after tile edits)."""
        self._bake_layers()
