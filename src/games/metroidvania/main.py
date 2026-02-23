import math
import time

from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600
TILE_SIZE = 40
ROOM_W = 20 * TILE_SIZE
ROOM_H = 15 * TILE_SIZE

ROOMS_DATA = {
    (0,0): [
        "XXXXXXXXXXXXXXXXXXXX","X                  X","X      P           X","X                  X",
        "X        XXXX       ","X                   ","X                   ","X     X             ",
        "X           XXXXXXXX","X                  X","X                  X","X                  X",
        "X                  X","X                  X","XXXXXXXXXXXXXXXXXXXX"
    ],
    (1,0): [
        "XXXXXXXXXXXXXXXXXXXX","X                  X","X                  X","X                   ",
        "        X           ","           X        ","              X     ","                    ",
        "XXXXXXXXX           ","X                  X","X                  X","X                  X",
        "X                   ","X                   ","XXXXXXXXXXXXXXXXXXXX"
    ],
    (2,0): [
        "XXXXXXXXXXXXXXXXXXXX","X                  X","X                  X","                   X",
        "           XXXX    X","        X          X","     X             X","   X               X",
        "                   X","X                  X","X                  X","X                  X",
        "                   X","                   X","XXXXXXXXXXXXXXXXXXXX"
    ],
    (1,1): [
        "X                  X","X                  X","X                  X","X                   ",
        "                 XXX","                    ","     XXXXXX         ","                    ",
        "X                   ","X                  X","X                  X","X                  X",
        "X                  X","X                  X","XXXXXXXXXXXXXXXXXXXX"
    ],
    (2,1): [
        "                   X","                   X","                   X","                    ",
        "XXX                 ","         X          ","             X      ","                 X  ",
        "X                  X","X                  X","X                  X","X                  X",
        "X                  X","X                  X","XXXXXXXXXXXXXXXXXXXX"
    ]
}


class MetroidvaniaPlayer(PhysicsBody2D):
    def __init__(self, name, x, y, cw):
        col = Collider2D(name + "Col", 0, 0, 20, 30)
        col.layer = "player"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = True
        self.gravity = 1200.0
        self.movespeed = 250.0
        self.jumpforce = 500.0
        self.add_child(col)
        self.add_child(RectangleNode("PVis", 0, 0, 20, 30, (255, 100, 100)))
        self.is_grounded = False

    def update(self, delta):
        inp = Engine.instance.input
        probe = self.collision_world.check_collision(self.collider, self.local_x, self.local_y + 1.0)
        self.is_grounded = probe.collided and probe.normal_y < 0
        if inp.is_key_pressed(Keys.SPACE) and self.is_grounded:
            self.velocity_y = -self.jumpforce
        move_dir = 0
        if inp.is_key_pressed(Keys.LEFT) or inp.is_key_pressed(Keys.A): move_dir -= 1
        if inp.is_key_pressed(Keys.RIGHT) or inp.is_key_pressed(Keys.D): move_dir += 1
        target_vx = move_dir * self.movespeed
        self.velocity_x += (target_vx - self.velocity_x) * 15.0 * delta
        super().update(delta)


class WorldManager:
    def __init__(self, root):
        self.root = root
        self.loaded_rooms = {}

    def load_room(self, rx, ry):
        if (rx, ry) in self.loaded_rooms or (rx, ry) not in ROOMS_DATA:
            return
        room_node = Node2D(f"Room_{rx}_{ry}", rx * ROOM_W, ry * ROOM_H)
        r_col = (100 + (rx * 30) % 100, 100 + (ry * 40) % 100, 150)
        for y, row in enumerate(ROOMS_DATA[(rx, ry)]):
            for x, char in enumerate(row):
                if char == 'X':
                    wall = Node2D(f"W_{x}_{y}", x * TILE_SIZE, y * TILE_SIZE)
                    col = Collider2D(f"WC_{x}_{y}", 0, 0, TILE_SIZE, TILE_SIZE, is_static=True)
                    col.layer = "wall"
                    col.mask = {"player"}
                    wall.add_child(col)
                    wall.add_child(RectangleNode(f"WV_{x}_{y}", 0, 0, TILE_SIZE, TILE_SIZE, r_col))
                    room_node.add_child(wall)
        self.root.add_child(room_node)
        self.loaded_rooms[(rx, ry)] = room_node

    def unload_room(self, rx, ry):
        if (rx, ry) in self.loaded_rooms:
            self.root.remove_child(self.loaded_rooms.pop((rx, ry)))

    def update_loaded_chunks(self, prx, pry):
        start_t = time.perf_counter()
        needed = {(prx, pry), (prx + 1, pry), (prx - 1, pry), (prx, pry + 1), (prx, pry - 1)}
        current = set(self.loaded_rooms.keys())
        to_load = needed - current
        to_unload = current - needed
        for r in to_load: self.load_room(*r)
        for r in to_unload: self.unload_room(*r)
        load_time_ms = (time.perf_counter() - start_t) * 1000
        if to_load or to_unload:
            def count_nodes(n):
                c = 1
                for child in n.children: c += count_nodes(child)
                return c
            print(f"[TRANSITION] Loaded {len(to_load)}, Unloaded {len(to_unload)}. "
                  f"Time: {load_time_ms:.2f}ms. Total: {count_nodes(self.root)}")


def main():
    engine = Engine("Level 6: Metroidvania (Room Chunking & Streaming)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)

    world_mgr = WorldManager(root)
    player = MetroidvaniaPlayer("Player", 250, 100, cw)
    root.add_child(player)

    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = camera

    current_rx, current_ry = 0, 0
    world_mgr.update_loaded_chunks(current_rx, current_ry)
    accumulator = 0.0

    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        profiler.begin("Logic")
        while accumulator >= engine.fixed_dt:
            prx = math.floor((player.local_x + player.collider.width / 2) / ROOM_W)
            pry = math.floor((player.local_y + player.collider.height / 2) / ROOM_H)
            if (prx, pry) != (current_rx, current_ry):
                current_rx, current_ry = prx, pry
                world_mgr.update_loaded_chunks(current_rx, current_ry)
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Logic")

        profiler.begin("Render")
        r.fill(surface, (20, 20, 30))
        root.render(surface)
        hud = [
            f"FPS: {engine.fps:.1f}", f"Room: ({current_rx}, {current_ry})",
            f"Loaded: {len(world_mgr.loaded_rooms)}", "Move across boundaries to stream rooms!"
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
