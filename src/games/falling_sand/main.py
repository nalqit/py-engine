import pygame
import sys
import random

from src.engine.scene.node2d import Node2D
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600

# Reduced resolution for cellular automata to simulate large grids smoothly in python
GRID_W = 200
GRID_H = 150
CELL_SIZE = 4

EMPTY = 0
SAND = 1
WATER = 2
STONE = 3

COLORS = {
    EMPTY: (0, 0, 0, 0),
    SAND: (220, 200, 100, 255),
    WATER: (50, 100, 200, 150),
    STONE: (100, 100, 100, 255)
}

# Pre-map integers directly to 32-bit pixel values for PixelArray
mapped_colors = {}

class SandSimulationNode(Node2D):
    def __init__(self, name):
        super().__init__(name, 0, 0)
        self.grid = [EMPTY] * (GRID_W * GRID_H)
        self.next_grid = [EMPTY] * (GRID_W * GRID_H)
        
        self.surface = pygame.Surface((GRID_W, GRID_H)).convert_alpha()
        self.surface.fill((0,0,0,0))
        
        # Pre-fill mapped colors
        for k, c in COLORS.items():
            mapped_colors[k] = self.surface.map_rgb(c)
            
        self.active_cells = 0
        
        # Brush state
        self.current_mat = SAND
        self.brush_size = 3
        
    def update(self, delta):
        # Apply brush
        mx, my = pygame.mouse.get_pos()
        sw, sh = pygame.display.get_surface().get_size()
        vx = int((mx / sw) * VIRTUAL_W)
        vy = int((my / sh) * VIRTUAL_H)
        
        gx = max(0, min(GRID_W - 1, vx // CELL_SIZE))
        gy = max(0, min(GRID_H - 1, vy // CELL_SIZE))
        
        if pygame.mouse.get_pressed()[0]:
            for bx in range(-self.brush_size, self.brush_size+1):
                for by in range(-self.brush_size, self.brush_size+1):
                    if bx*bx + by*by <= self.brush_size*self.brush_size:
                        tx, ty = gx + bx, gy + by
                        if 0 <= tx < GRID_W and 0 <= ty < GRID_H:
                            self.grid[ty * GRID_W + tx] = self.current_mat
                            
        # Change mat
        keys = pygame.key.get_pressed()
        if keys[pygame.K_1]: self.current_mat = SAND
        elif keys[pygame.K_2]: self.current_mat = WATER
        elif keys[pygame.K_3]: self.current_mat = STONE
        elif keys[pygame.K_4]: self.current_mat = EMPTY

        # Copy grid
        self.next_grid[:] = self.grid[:]
        active = 0
        
        # Cellular Automata Update (Bottom to top to prevent falling multiple cells per tick if ordered)
        # We iterate bottom-up for gravity
        for y in range(GRID_H - 2, -1, -1):
            for x in range(GRID_W):
                idx = y * GRID_W + x
                mat = self.grid[idx]
                
                if mat == EMPTY or mat == STONE:
                    if mat == STONE: active += 1
                    continue
                    
                active += 1
                down = idx + GRID_W
                
                if mat == SAND:
                    if self.grid[down] == EMPTY or self.grid[down] == WATER:
                        # Fall down (swap with water if it's there)
                        self.next_grid[down] = SAND
                        self.next_grid[idx] = self.grid[down]
                    else:
                        # Try diagonals
                        dl = down - 1
                        dr = down + 1
                        can_l = x > 0 and (self.grid[dl] == EMPTY or self.grid[dl] == WATER)
                        can_r = x < GRID_W - 1 and (self.grid[dr] == EMPTY or self.grid[dr] == WATER)
                        
                        if can_l and can_r:
                            choice = dl if random.random() < 0.5 else dr
                            self.next_grid[choice] = SAND
                            self.next_grid[idx] = self.grid[choice]
                        elif can_l:
                            self.next_grid[dl] = SAND
                            self.next_grid[idx] = self.grid[dl]
                        elif can_r:
                            self.next_grid[dr] = SAND
                            self.next_grid[idx] = self.grid[dr]

                elif mat == WATER:
                    if self.grid[down] == EMPTY:
                        self.next_grid[down] = WATER
                        self.next_grid[idx] = EMPTY
                    else:
                        dl = down - 1
                        dr = down + 1
                        can_l = x > 0 and self.grid[dl] == EMPTY
                        can_r = x < GRID_W - 1 and self.grid[dr] == EMPTY
                        
                        if can_l and can_r:
                            choice = dl if random.random() < 0.5 else dr
                            self.next_grid[choice] = WATER
                            self.next_grid[idx] = EMPTY
                        elif can_l:
                            self.next_grid[dl] = WATER
                            self.next_grid[idx] = EMPTY
                        elif can_r:
                            self.next_grid[dr] = WATER
                            self.next_grid[idx] = EMPTY
                        else:
                            # Disperse horizontally
                            l = idx - 1
                            r = idx + 1
                            h_can_l = x > 0 and self.grid[l] == EMPTY
                            h_can_r = x < GRID_W - 1 and self.grid[r] == EMPTY
                            
                            if h_can_l and h_can_r:
                                choice = l if random.random() < 0.5 else r
                                self.next_grid[choice] = WATER
                                self.next_grid[idx] = EMPTY
                            elif h_can_l:
                                self.next_grid[l] = WATER
                                self.next_grid[idx] = EMPTY
                            elif h_can_r:
                                self.next_grid[r] = WATER
                                self.next_grid[idx] = EMPTY

        self.grid[:] = self.next_grid[:]
        self.active_cells = active
        super().update(delta)

    def render(self, surface):
        # Using PixelArray for batch memory writes directly to the Pygame Surface without NumPy
        with pygame.PixelArray(self.surface) as pxarray:
            # Flatten grid and map to colors natively in Python.
            # Performance note: For a stress test, processing a 30,000 array dynamically is slow.
            # This pushes the Python execution layer to the limit.
            for y in range(GRID_H):
                row_start = y * GRID_W
                for x in range(GRID_W):
                    pxarray[x, y] = mapped_colors[self.grid[row_start + x]]
                    
        # Scale to virtual viewport
        scaled = pygame.transform.scale(self.surface, (VIRTUAL_W, VIRTUAL_H))
        surface.blit(scaled, (0, 0))
        
        # Debug brush
        mx, my = pygame.mouse.get_pos()
        sw, sh = pygame.display.get_surface().get_size()
        vx = int((mx / sw) * VIRTUAL_W)
        vy = int((my / sh) * VIRTUAL_H)
        pygame.draw.circle(surface, (255, 255, 255), (vx, vy), self.brush_size * CELL_SIZE, 1)

def main():
    global profiler
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 8: Falling Sand (Raw Data & Rendering Throughput)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    sand_sim = SandSimulationNode("Sim")
    root.add_child(sand_sim)
    
    font = pygame.font.SysFont("Arial", 16)
    
    running = True
    fixed_dt = 1/60.0
    accumulator = 0.0
    
    while running:
        dt = clock.tick(60) / 1000.0
        profiler.log_frame(dt)
        accumulator += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                    
        profiler.begin("Simulation")
        while accumulator >= fixed_dt:
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Simulation")
            
        profiler.begin("Render")
        game_surface.fill((20, 20, 20))
        root.render(game_surface)
        
        mats = ["1: Sand", "2: Water", "3: Stone", "4: Erase"]
        curr_mat = mats[sand_sim.current_mat - 1] if sand_sim.current_mat > 0 else mats[3]
        
        sim_time = profiler.timings.get("Simulation", 0)
        ren_time = profiler.timings.get("Render", 0)
        
        hud_lines = [
            f"FPS: {clock.get_fps():.1f}",
            f"Active Cells: {sand_sim.active_cells} / {GRID_W*GRID_H}",
            f"Sim Time: {sim_time:.2f}ms | Render Time: {ren_time:.2f}ms",
            f"Material: {curr_mat}",
            "Left Click to Paint!"
        ]
        
        y = 10
        for line in hud_lines:
            txt = font.render(line, True, (255, 255, 255))
            game_surface.blit(txt, (10, y))
            y += 20
        profiler.end("Render")
            
        scaled = pygame.transform.scale(game_surface, screen.get_size())
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        
    profiler.print_summary()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
