"""
draw2d.py — Infinite 4-Quadrant Map Editor + Live Scene Viewer

Controls:
  Left Click       → Paint tile
  Right Click      → Erase tile
  Space + Drag     → Pan camera
  Middle Click     → Pan camera
  Scroll Wheel     → Zoom
  WASD             → Move editor camera (world units)
  [S]              → Save map to JSON
  [L]              → Load map from JSON
  [D]              → Toggle renderer debug overlay
"""

import pygame
import json
import os
import sys
import tkinter as tk
from tkinter import filedialog

# ---------------------------------------------------------------------------
# Engine imports — guarded so the editor launches even without a full engine
# environment (e.g. when run in isolation).
# ---------------------------------------------------------------------------
try:
    from src.pyengine2D.scene.node import Node
    from src.pyengine2D.scene.node2d import Node2D
    from src.pyengine2D.scene.camera2d import Camera2D
    from src.pyengine2D.rendering.renderer2d import Renderer2D
    _ENGINE_AVAILABLE = True
except ImportError as _e:
    print(f"[draw2d] Warning: engine not available ({_e}). Scene rendering disabled.")
    _ENGINE_AVAILABLE = False

# Optional scene-node imports (for building the live preview scene)
try:
    from src.pyengine2D.scene.tilemap import TilemapNode
except ImportError:
    TilemapNode = None

try:
    from src.pyengine2D.scene.sprite_node import SpriteNode
except ImportError:
    SpriteNode = None

try:
    from src.pyengine2D.scene.animated_sprite import AnimatedSprite
except ImportError:
    AnimatedSprite = None

try:
    from src.pyengine2D.scene.particles import ParticleEmitter2D
except ImportError:
    ParticleEmitter2D = None

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TILE_SIZE    = 32
SCREEN_WIDTH  = 1024
SCREEN_HEIGHT = 768

CAM_MOVE_SPEED = 300   # world-pixels per second when using WASD

# Palette colours
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
GRAY       = (220, 220, 220, 100)
ACCENT     = (0,   150, 255)
AXIS_COLOR = (255,  50,  50)

# ---------------------------------------------------------------------------
# Helpers — map save / load (unchanged from original)
# ---------------------------------------------------------------------------

def save_map_json(grid):
    """Save infinite grid to bounded JSON with offset."""
    if not grid:
        print("✗ Map is empty, nothing to save.")
        return

    root_tk = tk.Tk()
    root_tk.withdraw()
    root_tk.attributes('-topmost', True)
    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json")],
        title="Save Map Data As",
    )
    if not filepath:
        return

    min_x = min(x for x, y in grid.keys())
    max_x = max(x for x, y in grid.keys())
    min_y = min(y for x, y in grid.keys())
    max_y = max(y for x, y in grid.keys())

    rows = max_y - min_y + 1
    cols = max_x - min_x + 1

    binary_grid = [[0] * cols for _ in range(rows)]
    for (gx, gy), val in grid.items():
        if val == BLACK:
            binary_grid[gy - min_y][gx - min_x] = 2  # Default to top-grass

    # Simple auto-tiling logic for standard grass mapping aesthetics
    for r in range(rows):
        for c in range(cols):
            if binary_grid[r][c] != 0:
                above = (r == 0) or (binary_grid[r - 1][c] == 0)
                if above:
                    left  = (c == 0)        or (binary_grid[r][c - 1] == 0)
                    right = (c == cols - 1) or (binary_grid[r][c + 1] == 0)
                    if left and right:
                        binary_grid[r][c] = 2   # top mid
                    elif left:
                        binary_grid[r][c] = 1   # top left
                    elif right:
                        binary_grid[r][c] = 3   # top right
                    else:
                        binary_grid[r][c] = 2   # top mid
                else:
                    binary_grid[r][c] = 24      # underground dirt

    map_data = {
        "tile_width":  TILE_SIZE,
        "tile_height": TILE_SIZE,
        "layers": [
            {
                "name":             "Terrain",
                "solid":            True,
                "parallax_factor":  [1.0, 1.0],
                "offset_x":        min_x,
                "offset_y":        min_y,
                "tiles":           binary_grid,
            }
        ],
        "tilesets": [
            {
                "image":       "src/Free/Terrain/Terrain (16x16).png",
                "tile_width":  16,
                "tile_height": 16,
                "scale":       2,
            }
        ],
    }

    with open(filepath, "w") as f:
        json.dump(map_data, f, indent=4)
    print(f"✓ Saved map to {filepath}!")
    print(f"Bounding Box: Col {min_x} to {max_x}, Row {min_y} to {max_y}")


def load_map_json(grid):
    """Load a map from JSON into the editor grid."""
    root_tk = tk.Tk()
    root_tk.withdraw()
    root_tk.attributes('-topmost', True)
    filepath = filedialog.askopenfilename(
        filetypes=[("JSON Files", "*.json")],
        title="Load Map Data",
    )
    if not filepath:
        return False

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        layer = data["layers"][0]
        tx    = layer.get("offset_x", 0)
        ty    = layer.get("offset_y", 0)
        tiles = layer.get("tiles", [])
        grid.clear()
        for r, row in enumerate(tiles):
            for c, val in enumerate(row):
                if val > 0:
                    grid[(tx + c, ty + r)] = BLACK
        print(f"✓ Loaded map from {filepath}!")
        return True
    except Exception as e:
        print(f"✗ Could not load map: {e}")
        return False


# ---------------------------------------------------------------------------
# Scene builder — builds a minimal scene tree for the live preview
# ---------------------------------------------------------------------------

def _build_scene_root() -> "Node":
    """
    Returns the scene root used for Renderer2D.

    If specific engine node types are available the scene is populated with
    representative placeholder nodes so the renderer has something to iterate.
    Override or extend this function to load your actual game scene instead.
    """
    if not _ENGINE_AVAILABLE:
        return None  # type: ignore[return-value]

    root = Node("EditorSceneRoot")

    # TODO: add_child() your actual game nodes here, for example:
    #
    #   map_node = TilemapNode("Terrain", tile_size=16)
    #   map_node.load("assets/map_data.json")
    #   root.add_child(map_node)
    #
    # For now the root is empty — the Renderer2D will traverse it harmlessly
    # and the editor grid overlay is drawn on top.

    return root


# ---------------------------------------------------------------------------
# Main editor loop
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Map Editor & Live Scene Viewer — PyEngine2D")

    clock = pygame.time.Clock()

    # ── Editor state ────────────────────────────────────────────────────────
    grid: dict = {}

    # Editor camera (world-space centre that the editor looks at)
    # NOTE: these are separate from the engine Camera2D local_x/local_y so that
    # the editor can be used without a running Engine instance.
    camera_x: float = 0.0
    camera_y: float = 0.0
    zoom: float = 1.0

    is_panning = False
    pan_start_pos    = (0, 0)
    pan_start_camera = (0.0, 0.0)

    # ── Renderer2D integration ───────────────────────────────────────────────
    scene_root    = None
    renderer      = None
    engine_camera = None
    debug_mode    = False   # toggled with [D]

    if _ENGINE_AVAILABLE:
        # Create a Camera2D whose position tracks the editor camera.
        # Node2D.camera must point to this so get_screen_position() works.
        engine_camera = Camera2D("EditorCamera")
        engine_camera.local_x = camera_x
        engine_camera.local_y = camera_y
        Node2D.camera = engine_camera

        # Build or load the scene
        scene_root = _build_scene_root()

        # Create the renderer
        renderer = Renderer2D(engine_camera, debug_mode=False)

    running = True
    while running:
        delta = clock.tick(60) / 1000.0
        screen_w, screen_h = screen.get_size()

        # ── Mouse world coords ───────────────────────────────────────────────
        current_mouse_pos = pygame.mouse.get_pos()
        mouse_world_x = (current_mouse_pos[0] - screen_w / 2) / zoom + camera_x
        mouse_world_y = (current_mouse_pos[1] - screen_h / 2) / zoom + camera_y

        hover_col = int(mouse_world_x // TILE_SIZE)
        hover_row = int(mouse_world_y // TILE_SIZE)
        if mouse_world_x < 0 and mouse_world_x % TILE_SIZE != 0:
            hover_col -= 1
        if mouse_world_y < 0 and mouse_world_y % TILE_SIZE != 0:
            hover_row -= 1

        # ── Events ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2:   # Middle-click → pan
                    is_panning = True
                    pan_start_pos    = event.pos
                    pan_start_camera = (camera_x, camera_y)
                elif event.button == 4: # Scroll up → zoom in
                    zoom = min(4.0, zoom * 1.1)
                    if engine_camera:
                        # Propagate zoom if Camera2D supports it
                        if hasattr(engine_camera, 'zoom'):
                            engine_camera.zoom = zoom
                elif event.button == 5: # Scroll down → zoom out
                    zoom = max(0.2, zoom / 1.1)
                    if engine_camera:
                        if hasattr(engine_camera, 'zoom'):
                            engine_camera.zoom = zoom

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    is_panning = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    save_map_json(grid)
                elif event.key == pygame.K_l:
                    load_map_json(grid)
                elif event.key == pygame.K_d:
                    debug_mode = not debug_mode
                    if renderer:
                        renderer.debug_mode = debug_mode
                    print(f"[draw2d] Debug overlay: {'ON' if debug_mode else 'OFF'}")

        # ── Panning (middle-click drag or space+drag) ────────────────────────
        keys    = pygame.key.get_pressed()
        buttons = pygame.mouse.get_pressed()
        is_space = keys[pygame.K_SPACE]

        if is_panning:
            dx = (current_mouse_pos[0] - pan_start_pos[0]) / zoom
            dy = (current_mouse_pos[1] - pan_start_pos[1]) / zoom
            camera_x = pan_start_camera[0] - dx
            camera_y = pan_start_camera[1] - dy

        # Space + left-drag also pans
        if is_space and buttons[0] and not is_panning:
            is_panning = True
            pan_start_pos    = current_mouse_pos
            pan_start_camera = (camera_x, camera_y)
        if not is_space and not buttons[1] and is_panning and not keys[pygame.K_SPACE]:
            if not buttons[1]:  # middle-click not held either
                is_panning = False

        # ── WASD camera movement ─────────────────────────────────────────────
        cam_speed = CAM_MOVE_SPEED * delta / zoom
        if keys[pygame.K_a]:
            camera_x -= cam_speed
        if keys[pygame.K_d] and not (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
            camera_x += cam_speed
        if keys[pygame.K_w]:
            camera_y -= cam_speed
        if keys[pygame.K_s] and not (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]):
            # Only move camera on S if not triggering save (already handled in KEYDOWN for shift-less)
            # We use KEYDOWN for save so this is safe.
            camera_y += cam_speed

        # ── Tile painting / erasing ──────────────────────────────────────────
        if not is_panning and not is_space:
            if buttons[0]:  # Left click → draw
                grid[(hover_col, hover_row)] = BLACK
            elif buttons[2]:  # Right click → erase
                grid.pop((hover_col, hover_row), None)

        # ── Sync engine camera to editor camera ──────────────────────────────
        if engine_camera is not None:
            engine_camera.local_x = camera_x
            engine_camera.local_y = camera_y

        # ── Update scene tree ────────────────────────────────────────────────
        if scene_root is not None:
            scene_root.update(delta)

        # ====================================================================
        # RENDER
        # ====================================================================

        screen.fill(WHITE)

        # -- 1. Renderer2D draws the scene tree (behind editor UI) ------------
        if renderer is not None and scene_root is not None:
            renderer.draw(scene_root, screen)

        # -- 2. Editor grid overlay ------------------------------------------
        start_col = int((camera_x - screen_w  / zoom) / TILE_SIZE) - 1
        end_col   = int((camera_x + screen_w  / zoom) / TILE_SIZE) + 1
        start_row = int((camera_y - screen_h  / zoom) / TILE_SIZE) - 1
        end_row   = int((camera_y + screen_h  / zoom) / TILE_SIZE) + 1

        scaled_tile = max(1, int(TILE_SIZE * zoom))

        grid_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        for r in range(start_row, end_row + 1):
            sy = (r * TILE_SIZE - camera_y) * zoom + screen_h / 2
            pygame.draw.line(grid_surf, GRAY, (0, sy), (screen_w, sy), 1)
        for c in range(start_col, end_col + 1):
            sx = (c * TILE_SIZE - camera_x) * zoom + screen_w / 2
            pygame.draw.line(grid_surf, GRAY, (sx, 0), (sx, screen_h), 1)
        screen.blit(grid_surf, (0, 0))

        # -- 3. World axes ----------------------------------------------------
        origin_x = (-camera_x) * zoom + screen_w / 2
        origin_y = (-camera_y) * zoom + screen_h / 2
        axis_w   = max(1, int(2 * zoom))
        if 0 <= origin_x <= screen_w:
            pygame.draw.line(screen, AXIS_COLOR, (int(origin_x), 0), (int(origin_x), screen_h), axis_w)
        if 0 <= origin_y <= screen_h:
            pygame.draw.line(screen, AXIS_COLOR, (0, int(origin_y)), (screen_w, int(origin_y)), axis_w)

        # -- 4. Painted tiles -------------------------------------------------
        for (c, r), color in grid.items():
            if start_col <= c <= end_col and start_row <= r <= end_row:
                sx = (c * TILE_SIZE - camera_x) * zoom + screen_w / 2
                sy = (r * TILE_SIZE - camera_y) * zoom + screen_h / 2
                pygame.draw.rect(screen, color, (sx + 1, sy + 1, scaled_tile - 1, scaled_tile - 1))

        # -- 5. Hover highlight -----------------------------------------------
        hx = (hover_col * TILE_SIZE - camera_x) * zoom + screen_w / 2
        hy = (hover_row * TILE_SIZE - camera_y) * zoom + screen_h / 2
        pygame.draw.rect(
            screen, (0, 200, 80),
            (int(hx), int(hy), scaled_tile, scaled_tile),
            max(1, int(2 * zoom)),
        )

        # -- 6. Editor HUD ----------------------------------------------------
        font = pygame.font.SysFont("Arial", 14, bold=True)
        ui_texts = [
            f"Pos: ({hover_col}, {hover_row})  |  Cam: ({int(camera_x)}, {int(camera_y)})  |  Zoom: {zoom:.1f}×",
            "Controls:",
            "  Left / Right Click : Draw / Erase tile",
            "  Space+Drag / Mid-Click : Pan",
            "  WASD : Move camera",
            "  Scroll Wheel : Zoom",
            "  [S] Save   [L] Load   [D] Toggle Debug",
        ]
        if _ENGINE_AVAILABLE:
            ui_texts.insert(1, f"Scene: {'✓ active' if scene_root else '—'}  |  Debug: {'ON' if debug_mode else 'off'}")

        box_width  = 440
        box_height = len(ui_texts) * 20 + 10
        box_x = 5
        box_y = screen_h - box_height - 5

        pygame.draw.rect(screen, WHITE,  (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, ACCENT, (box_x, box_y, box_width, box_height), 2)

        for i, txt in enumerate(ui_texts):
            text_surf = font.render(txt, True, BLACK)
            screen.blit(text_surf, (box_x + 10, box_y + 5 + i * 20))

        # -- 7. Present -------------------------------------------------------
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()