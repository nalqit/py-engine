import math

from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.circle_node import CircleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600
BLOCK_SIZE = 40


class DestructibleBlock(PhysicsBody2D):
    def __init__(self, name, x, y, collision_world):
        col = Collider2D(name + "Col", 0, 0, BLOCK_SIZE, BLOCK_SIZE)
        col.layer = "block"
        col.mask = {"wall", "block", "floor"}
        super().__init__(name, x, y, col, collision_world)
        self.use_gravity = True
        self.pushable = True
        self.push_weight = 1.0
        self.max_hp = 100.0
        self.hp = 100.0
        self.vis = RectangleNode(name + "Vis", 0, 0, BLOCK_SIZE, BLOCK_SIZE, (150, 100, 50))
        self.add_child(col)
        self.add_child(self.vis)

    def on_pushed(self, pusher):
        impact = abs(pusher.velocity_x) + abs(pusher.velocity_y)
        if impact > 200:
            self.take_damage(impact * 0.05)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            if self.parent:
                self.parent.remove_child(self)
        else:
            health_pct = self.hp / self.max_hp
            c = int(150 * health_pct)
            self.vis.color = (150, c, c)


class Projectile(PhysicsBody2D):
    def __init__(self, name, x, y, collision_world):
        col = Collider2D(name + "Col", 0, 0, 20, 20)
        col.layer = "projectile"
        col.mask = {"wall", "block", "floor"}
        super().__init__(name, x, y, col, collision_world)
        self.use_gravity = True
        self.can_push = True
        self.push_strength = 10.0
        self.add_child(col)
        self.add_child(CircleNode(name + "Vis", 10, 10, 10, (255, 50, 50)))
        self.state = "idle"
        self.start_x = x
        self.start_y = y

    def update(self, delta):
        inp = Engine.instance.input
        if self.state != "flying":
            self.velocity_x = 0
            self.velocity_y = 0
            mx, my = inp.get_mouse_pos()
            mouse_pressed = inp.is_mouse_pressed(0)

            if self.state == "idle":
                dist = math.hypot(mx - (self.local_x + 10), my - (self.local_y + 10))
                if mouse_pressed and dist < 30:
                    self.state = "dragged"
            elif self.state == "dragged":
                self.local_x = mx - 10
                self.local_y = my - 10
                if not mouse_pressed:
                    self.state = "flying"
                    dx = self.start_x - self.local_x
                    dy = self.start_y - self.local_y
                    self.apply_impulse(dx * 5.0, dy * 5.0)
        super().update(delta)


def build_structure(parent, cw, start_x, start_y, rows, cols):
    for row in range(rows):
        for c in range(cols):
            x = start_x + c * (BLOCK_SIZE + 2)
            y = start_y - (row + 1) * (BLOCK_SIZE + 2)
            parent.add_child(DestructibleBlock(f"Block_{row}_{c}", x, y, cw))


def main():
    engine = Engine("Level 3: Physics Destruction (Stacking & Impulse)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)

    floor_node = Node2D("Floor", -100, VIRTUAL_H - 40)
    fc = Collider2D("FloorCol", 0, 0, 1000, 40, is_static=True)
    fc.layer = "floor"
    fc.mask = {"block", "projectile"}
    floor_node.add_child(fc)
    floor_node.add_child(RectangleNode("FloorVis", 0, 0, 1000, 40, (100, 150, 100)))
    root.add_child(floor_node)

    build_structure(root, cw, 400, VIRTUAL_H - 40, 6, 3)
    build_structure(root, cw, 600, VIRTUAL_H - 40, 4, 4)

    bird = Projectile("Bird", 150, VIRTUAL_H - 200, cw)
    root.add_child(bird)
    root.add_child(RectangleNode("Post", 155, VIRTUAL_H - 190, 10, 150, (100, 50, 0)))

    accumulator = 0.0

    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        for event in engine.events:
            if event.type == 'key_down':
                if event.key == Keys.R:
                    bird.state = "idle"
                    bird.local_x = bird.start_x
                    bird.local_y = bird.start_y
                    bird.velocity_x = 0
                    bird.velocity_y = 0
                elif event.key == Keys.S:
                    build_structure(root, cw, 500, VIRTUAL_H - 40, 3, 2)

        profiler.begin("Logic")
        while accumulator >= engine.fixed_dt:
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Logic")

        profiler.begin("Render")
        r.fill(surface, (135, 206, 235))
        if bird.state == "dragged":
            r.draw_line(surface, (0, 0, 0), 160, VIRTUAL_H - 190, bird.local_x + 10, bird.local_y + 10, 3)
        root.render(surface)

        block_count = sum(1 for c in root.children if isinstance(c, DestructibleBlock))
        hud = [
            f"FPS: {engine.fps:.1f}", f"Blocks: {block_count}",
            "Drag red circle to aim & release", "Press R to reset ball", "Press S to spawn more"
        ]
        y = 10
        for line in hud:
            r.blit(surface, r.render_text_uncached(line, (0, 0, 0)), (10, y))
            y += 20
        profiler.end("Render")

        engine.end_frame()

    profiler.print_summary()
    engine.quit()


if __name__ == "__main__":
    main()
