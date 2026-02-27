import pygame
import json
import os
import tkinter as tk
from tkinter import filedialog

# --- Config ---
TILE_SIZE = 32
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (220, 220, 220, 100)
ACCENT = (0, 150, 255)
AXIS_COLOR = (255, 50, 50)

def save_map_json(grid):
    """Save infinite grid to bounded JSON with offset"""
    if not grid:
        print("✗ Map is empty, nothing to save.")
        return
        
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], title="Save Map Data As")
    if not filepath:
        return

    min_x = min(x for x, y in grid.keys())
    max_x = max(x for x, y in grid.keys())
    min_y = min(y for x, y in grid.keys())
    max_y = max(y for x, y in grid.keys())
    
    rows = max_y - min_y + 1
    cols = max_x - min_x + 1

    binary_grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for (gx, gy), val in grid.items():
        if val == BLACK:
            binary_grid[gy - min_y][gx - min_x] = 2  # Default to top grass
            
    # Simple auto-tiling logic for standard grass mapping aesthetics
    for r in range(rows):
        for c in range(cols):
            if binary_grid[r][c] != 0:
                above = (r == 0) or (binary_grid[r-1][c] == 0)
                if above:
                    left = (c == 0) or (binary_grid[r][c-1] == 0)
                    right = (c == cols - 1) or (binary_grid[r][c+1] == 0)
                    if left and right: binary_grid[r][c] = 2 # top mid
                    elif left: binary_grid[r][c] = 1 # top left
                    elif right: binary_grid[r][c] = 3 # top right (src_col 2)
                    else: binary_grid[r][c] = 2 # top mid
                else:
                    binary_grid[r][c] = 24 # underground dirt

    map_data = {
        "tile_width": TILE_SIZE,
        "tile_height": TILE_SIZE,
        "layers": [
            {
                "name": "Terrain",
                "solid": True,
                "parallax_factor": [1.0, 1.0],
                "offset_x": min_x,
                "offset_y": min_y,
                "tiles": binary_grid
            }
        ],
        "tilesets": [
            {
                "image": "src/Free/Terrain/Terrain (16x16).png",
                "tile_width": 16,
                "tile_height": 16,
                "scale": 2
            }
        ]
    }

    with open(filepath, "w") as f:
        json.dump(map_data, f, indent=4)
    print(f"✓ Saved map to {filepath}!")
    print(f"Bounding Box: Col {min_x} to {max_x}, Row {min_y} to {max_y}")

def load_map_json(grid):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Load Map Data")
    if not filepath:
        return False
        
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
            layer = data["layers"][0]
            tx = layer.get("offset_x", 0)
            ty = layer.get("offset_y", 0)
            tiles = layer.get("tiles", [])
            grid.clear()
            for r, row in enumerate(tiles):
                for c, val in enumerate(row):
                    if val > 0:
                        grid[(tx + c, ty + r)] = BLACK
        print(f"Loaded existing map from {filepath}!")
        return True
    except Exception as e:
        print("Could not load existing map:", e)
        return False

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Infinite 4-Quadrant Map Editor")
    
    grid = {}
    
    camera_x, camera_y = 0.0, 0.0
    zoom = 1.0
    
    is_panning = False
    pan_start_pos = (0, 0)
    pan_start_camera = (0.0, 0.0)

    clock = pygame.time.Clock()
    running = True

    while running:
        screen_w, screen_h = screen.get_size()
        screen.fill(WHITE)
        
        current_mouse_pos = pygame.mouse.get_pos()
        mouse_world_x = (current_mouse_pos[0] - screen_w/2) / zoom + camera_x
        mouse_world_y = (current_mouse_pos[1] - screen_h/2) / zoom + camera_y
        
        hover_col = int(mouse_world_x // TILE_SIZE)
        hover_row = int(mouse_world_y // TILE_SIZE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2: # Middle click
                    is_panning = True
                    pan_start_pos = event.pos
                    pan_start_camera = (camera_x, camera_y)
                elif event.button == 4: # Scroll up
                    zoom = min(4.0, zoom * 1.1)
                elif event.button == 5: # Scroll down
                    zoom = max(0.2, zoom / 1.1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    is_panning = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    save_map_json(grid)
                elif event.key == pygame.K_l:
                    load_map_json(grid)

        if is_panning:
            dx = (current_mouse_pos[0] - pan_start_pos[0]) / zoom
            dy = (current_mouse_pos[1] - pan_start_pos[1]) / zoom
            camera_x = pan_start_camera[0] - dx
            camera_y = pan_start_camera[1] - dy

        keys = pygame.key.get_pressed()
        is_space = keys[pygame.K_SPACE]
        buttons = pygame.mouse.get_pressed()
        
        if not is_panning and not is_space:
            if buttons[0]: # Left click
                grid[(hover_col, hover_row)] = BLACK
            elif buttons[2]: # Right click
                if (hover_col, hover_row) in grid:
                    del grid[(hover_col, hover_row)]
                    
        if is_space and buttons[0]:
            if not is_panning:
                is_panning = True
                pan_start_pos = current_mouse_pos
                pan_start_camera = (camera_x, camera_y)
        if not is_space and not buttons[2] and not buttons[0] and is_panning:
             if pygame.mouse.get_pressed()[1] == 0:
                 is_panning = False

        start_col = int(((camera_x - screen_w/(zoom)) / TILE_SIZE)) - 1
        end_col = int(((camera_x + screen_w/(zoom)) / TILE_SIZE)) + 1
        start_row = int(((camera_y - screen_h/(zoom)) / TILE_SIZE)) - 1
        end_row = int(((camera_y + screen_h/(zoom)) / TILE_SIZE)) + 1

        scaled_tile = max(1, int(TILE_SIZE * zoom))

        # Grid surface for alpha rendering
        grid_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        for r in range(start_row, end_row + 1):
            sy = (r * TILE_SIZE - camera_y) * zoom + screen_h/2
            pygame.draw.line(grid_surf, GRAY, (0, sy), (screen_w, sy), 1)
        for c in range(start_col, end_col + 1):
            sx = (c * TILE_SIZE - camera_x) * zoom + screen_w/2
            pygame.draw.line(grid_surf, GRAY, (sx, 0), (sx, screen_h), 1)
        screen.blit(grid_surf, (0, 0))

        origin_x = (-camera_x) * zoom + screen_w/2
        origin_y = (-camera_y) * zoom + screen_h/2
        if 0 <= origin_x <= screen_w:
            pygame.draw.line(screen, AXIS_COLOR, (origin_x, 0), (origin_x, screen_h), max(1, int(2*zoom)))
        if 0 <= origin_y <= screen_h:
            pygame.draw.line(screen, AXIS_COLOR, (0, origin_y), (screen_w, origin_y), max(1, int(2*zoom)))

        for (c, r), color in grid.items():
            if start_col <= c <= end_col and start_row <= r <= end_row:
                sx = (c * TILE_SIZE - camera_x) * zoom + screen_w/2
                sy = (r * TILE_SIZE - camera_y) * zoom + screen_h/2
                pygame.draw.rect(screen, color, (sx+1, sy+1, scaled_tile-1, scaled_tile-1))

        hx = (hover_col * TILE_SIZE - camera_x) * zoom + screen_w/2
        hy = (hover_row * TILE_SIZE - camera_y) * zoom + screen_h/2
        pygame.draw.rect(screen, (0, 255, 0, 100), (hx, hy, scaled_tile, scaled_tile), max(1, int(2*zoom)))

        font = pygame.font.SysFont("Arial", 14, bold=True)
        ui_texts = [
            f"Pos: ({hover_col}, {hover_row}) | Zoom: {zoom:.1f}x",
            "Controls:",
            "- Left/Right Click: Draw/Erase",
            "- Space+Click / Mid-Click: Pan Camera",
            "- Scroll Wheel: Zoom",
            "- [S] to Save  |  [L] to Load"
        ]
        
        box_width = 300
        box_height = len(ui_texts) * 20 + 10
        pygame.draw.rect(screen, WHITE, (5, screen_h - box_height - 5, box_width, box_height))
        pygame.draw.rect(screen, ACCENT, (5, screen_h - box_height - 5, box_width, box_height), 2)
        
        for i, txt in enumerate(ui_texts):
            text_surf = font.render(txt, True, BLACK)
            screen.blit(text_surf, (15, screen_h - box_height + i * 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()