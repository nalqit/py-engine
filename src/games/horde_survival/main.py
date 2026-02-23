import math
import random

from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.circle_node import CircleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler
from src.engine.utils.pathfinding import AStarGrid

VIRTUAL_W, VIRTUAL_H = 800, 600
profiler = None


class Player(PhysicsBody2D):
    def __init__(self, name, x, y, cw):
        col = Collider2D(name + "Col", 0, 0, 16, 16)
        col.layer = "player"
        col.mask = {"wall", "enemy"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.speed = 200.0
        self.hp = 100
        self.add_child(col)
        self.add_child(RectangleNode("PVis", 0, 0, 16, 16, (50, 200, 255)))
        self.attack_timer = 0.5

    def update(self, delta):
        inp = Engine.instance.input
        mx, my = 0, 0
        if inp.is_key_pressed(Keys.LEFT) or inp.is_key_pressed(Keys.A): mx -= 1
        if inp.is_key_pressed(Keys.RIGHT) or inp.is_key_pressed(Keys.D): mx += 1
        if inp.is_key_pressed(Keys.UP) or inp.is_key_pressed(Keys.W): my -= 1
        if inp.is_key_pressed(Keys.DOWN) or inp.is_key_pressed(Keys.S): my += 1
        if mx != 0 and my != 0:
            length = math.hypot(mx, my)
            mx /= length; my /= length
        self.velocity_x = mx * self.speed
        self.velocity_y = my * self.speed
        super().update(delta)
        self.attack_timer -= delta
        if self.attack_timer <= 0:
            self.attack_timer = 0.5
            self.auto_attack()

    def auto_attack(self):
        root = self.parent
        nearest = None
        min_dist = 150.0
        gx, gy = self.get_global_position()
        for c in root.children:
            if isinstance(c, Enemy):
                ex, ey = c.get_global_position()
                dist = math.hypot(ex - gx, ey - gy)
                if dist < min_dist:
                    min_dist = dist
                    nearest = c
        if nearest:
            root.remove_child(nearest)


class Enemy(PhysicsBody2D):
    def __init__(self, name, x, y, cw, grid, player):
        col = Collider2D(name + "Col", 0, 0, 14, 14)
        col.layer = "enemy"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.speed = 100.0 + random.uniform(-20, 20)
        self.grid = grid
        self.player = player
        self.add_child(col)
        self.add_child(CircleNode("EVis", 7, 7, 7, (255, 50, 50)))
        self.path = []
        self.path_timer = random.uniform(0.0, 0.5)

    def update(self, delta):
        global profiler
        self.path_timer -= delta
        if self.path_timer <= 0:
            self.path_timer = 0.5
            if profiler: profiler.begin("Pathfinding")
            self.path = self.grid.get_path(self.get_global_position(), self.player.get_global_position())
            if profiler: profiler.end("Pathfinding")
        if self.path:
            tx, ty = self.path[0]
            gx, gy = self.get_global_position()
            dx = tx - gx
            dy = ty - gy
            dist = math.hypot(dx, dy)
            if dist < 5.0:
                self.path.pop(0)
            else:
                self.velocity_x = (dx / dist) * self.speed
                self.velocity_y = (dy / dist) * self.speed
        else:
            self.velocity_x = 0; self.velocity_y = 0
        super().update(delta)

    def on_collision_enter(self, other):
        if other.layer == "player":
            self.player.hp -= 5


def create_wall(name, x, y, w, h, cw, parent, grid):
    wall = Node2D(name, x, y)
    col = Collider2D(name + "Col", 0, 0, w, h, is_static=True)
    col.layer = "wall"
    col.mask = {"player", "enemy"}
    wall.add_child(col)
    wall.add_child(RectangleNode(name + "Vis", 0, 0, w, h, (100, 100, 100)))
    parent.add_child(wall)
    grid.set_obstacle_world(x, y, w, h)


def main():
    global profiler
    engine = Engine("Level 5: Horde Survival (Massive AI Pathfinding)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)
    grid = AStarGrid(int(VIRTUAL_W / 20), int(VIRTUAL_H / 20), 20)

    create_wall("WTop", 0, 0, 800, 20, cw, root, grid)
    create_wall("WBot", 0, 580, 800, 20, cw, root, grid)
    create_wall("WLeft", 0, 0, 20, 600, cw, root, grid)
    create_wall("WRight", 780, 0, 20, 600, cw, root, grid)
    create_wall("Obs1", 200, 200, 100, 200, cw, root, grid)
    create_wall("Obs2", 500, 100, 20, 300, cw, root, grid)

    player = Player("Player", 100, 100, cw)
    root.add_child(player)

    def spawn_enemies(count):
        for _ in range(count):
            x = random.choice([50, 700])
            y = random.choice([50, 500])
            root.add_child(Enemy(f"Enemy_{random.randint(0, 99999)}", x, y, cw, grid, player))

    spawn_enemies(20)
    accumulator = 0.0

    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        for event in engine.events:
            if event.type == 'key_down' and event.key == Keys.S:
                spawn_enemies(50)

        profiler.begin("Logic")
        while accumulator >= engine.fixed_dt:
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Logic")

        profiler.begin("Render")
        r.fill(surface, (40, 50, 40))
        root.render(surface)
        enemies_count = sum(1 for c in root.children if isinstance(c, Enemy))
        p_time = profiler.timings.get("Pathfinding", 0)
        hud = [
            f"FPS: {engine.fps:.1f}", f"Enemies: {enemies_count}", f"Player HP: {player.hp}",
            f"Pathfinding Time: {p_time:.2f}ms", f"Press S to spawn 50 extra enemies!"
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
