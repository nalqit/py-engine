import random

from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.rendering.pixel_grid import PixelGrid
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600
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


class SandSimulationNode(Node2D):
    def __init__(self, name):
        super().__init__(name, 0, 0)
        self.grid = [EMPTY] * (GRID_W * GRID_H)
        self.next_grid = [EMPTY] * (GRID_W * GRID_H)
        self.pixel_grid = PixelGrid(GRID_W, GRID_H)
        for k, c in COLORS.items():
            self.pixel_grid.register_color(k, c)
        self.active_cells = 0
        self.current_mat = SAND
        self.brush_size = 3

    def update(self, delta):
        inp = Engine.instance.input
        mx, my = inp.get_mouse_pos()
        gx = max(0, min(GRID_W - 1, int(mx) // CELL_SIZE))
        gy = max(0, min(GRID_H - 1, int(my) // CELL_SIZE))

        if inp.is_mouse_pressed(0):
            for bx in range(-self.brush_size, self.brush_size + 1):
                for by in range(-self.brush_size, self.brush_size + 1):
                    if bx * bx + by * by <= self.brush_size * self.brush_size:
                        tx, ty = gx + bx, gy + by
                        if 0 <= tx < GRID_W and 0 <= ty < GRID_H:
                            self.grid[ty * GRID_W + tx] = self.current_mat

        if inp.is_key_pressed(Keys.NUM_1): self.current_mat = SAND
        elif inp.is_key_pressed(Keys.NUM_2): self.current_mat = WATER
        elif inp.is_key_pressed(Keys.NUM_3): self.current_mat = STONE
        elif inp.is_key_pressed(Keys.NUM_4): self.current_mat = EMPTY

        self.next_grid[:] = self.grid[:]
        active = 0

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
                        self.next_grid[down] = SAND
                        self.next_grid[idx] = self.grid[down]
                    else:
                        dl = down - 1
                        dr = down + 1
                        can_l = x > 0 and (self.grid[dl] == EMPTY or self.grid[dl] == WATER)
                        can_r = x < GRID_W - 1 and (self.grid[dr] == EMPTY or self.grid[dr] == WATER)
                        if can_l and can_r:
                            choice = dl if random.random() < 0.5 else dr
                        elif can_l: choice = dl
                        elif can_r: choice = dr
                        else: continue
                        self.next_grid[choice] = SAND
                        self.next_grid[idx] = self.grid[choice]
                elif mat == WATER:
                    if self.grid[down] == EMPTY:
                        self.next_grid[down] = WATER; self.next_grid[idx] = EMPTY
                    else:
                        dl = down - 1; dr = down + 1
                        can_l = x > 0 and self.grid[dl] == EMPTY
                        can_r = x < GRID_W - 1 and self.grid[dr] == EMPTY
                        if can_l and can_r: choice = dl if random.random() < 0.5 else dr
                        elif can_l: choice = dl
                        elif can_r: choice = dr
                        else:
                            l = idx - 1; r_idx = idx + 1
                            h_l = x > 0 and self.grid[l] == EMPTY
                            h_r = x < GRID_W - 1 and self.grid[r_idx] == EMPTY
                            if h_l and h_r: choice = l if random.random() < 0.5 else r_idx
                            elif h_l: choice = l
                            elif h_r: choice = r_idx
                            else: continue
                        self.next_grid[choice] = WATER; self.next_grid[idx] = EMPTY

        self.grid[:] = self.next_grid[:]
        self.active_cells = active
        super().update(delta)

    def render(self, surface):
        r = Engine.instance.renderer
        self.pixel_grid.batch_update(self.grid)
        scaled = r.scale_surface(self.pixel_grid.get_surface(), VIRTUAL_W, VIRTUAL_H)
        r.blit(surface, scaled, (0, 0))
        mx, my = Engine.instance.input.get_mouse_pos()
        r.draw_circle(surface, (255, 255, 255), mx, my, self.brush_size * CELL_SIZE, 1)


def main():
    engine = Engine("Level 8: Falling Sand (Raw Data & Rendering Throughput)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    sand_sim = SandSimulationNode("Sim")
    root.add_child(sand_sim)

    accumulator = 0.0
    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        profiler.begin("Simulation")
        while accumulator >= engine.fixed_dt:
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Simulation")

        profiler.begin("Render")
        r.fill(surface, (20, 20, 20))
        root.render(surface)
        mats = ["1: Sand", "2: Water", "3: Stone", "4: Erase"]
        curr = mats[sand_sim.current_mat - 1] if sand_sim.current_mat > 0 else mats[3]
        sim_t = profiler.timings.get("Simulation", 0)
        ren_t = profiler.timings.get("Render", 0)
        hud = [
            f"FPS: {engine.fps:.1f}", f"Active: {sand_sim.active_cells}/{GRID_W * GRID_H}",
            f"Sim: {sim_t:.2f}ms | Render: {ren_t:.2f}ms", f"Material: {curr}", "Left Click to Paint!"
        ]
        y = 10
        for line in hud:
            r.blit(surface, r.render_text_uncached(line, (255, 255, 255)), (10, y))
            y += 20
        profiler.end("Render")
        engine.end_frame()

    profiler.print_summary()
    engine.quit()


if __name__ == "__main__":
    main()
