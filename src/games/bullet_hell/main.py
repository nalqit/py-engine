import math

from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.scene.circle_node import CircleNode
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.circle_collider2d import CircleCollider2D
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600


class Bullet(Node2D):
    def __init__(self, name, pool):
        super().__init__(name, 0, 0)
        self.pool = pool
        self.vx = 0.0
        self.vy = 0.0
        self.active = False
        self.collider = CircleCollider2D(name + "_col", 0, 0, 4, is_trigger=True)
        self.collider.layer = "bullet"
        self.collider.mask = {"player"}
        self.add_child(self.collider)

    def fire(self, x, y, vx, vy):
        self.local_x = x
        self.local_y = y
        self.vx = vx
        self.vy = vy
        self.active = True

    def update(self, delta):
        if not self.active:
            return
        self.local_x += self.vx * delta
        self.local_y += self.vy * delta
        if self.local_x < -100 or self.local_x > VIRTUAL_W + 100 or \
           self.local_y < -100 or self.local_y > VIRTUAL_H + 100:
            self.deactivate()
        super().update(delta)

    def render(self, surface):
        if not self.active:
            return
        sx, sy = self.get_screen_position()
        Engine.instance.renderer.draw_circle(surface, (255, 100, 100), sx, sy, 4)
        super().render(surface)

    def deactivate(self):
        if self.active:
            self.active = False
            self.pool.recycle(self)

    def on_collision_enter(self, other):
        if other.layer == "player":
            self.deactivate()


class BulletPool:
    def __init__(self, size, parent_node):
        self.pool = []
        self.active_count = 0
        self.allocations = 0
        self.recycles = 0
        for i in range(size):
            b = Bullet(f"Bullet_{i}", self)
            parent_node.add_child(b)
            self.pool.append(b)

    def get(self):
        if self.pool:
            b = self.pool.pop()
            self.active_count += 1
            self.allocations += 1
            return b
        return None

    def recycle(self, bullet):
        self.pool.append(bullet)
        self.active_count -= 1
        self.recycles += 1


class BulletPlayer(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = False
        self.base_speed = 300.0
        self.focus_speed = 120.0
        self.hp = 100

    def update(self, delta):
        inp = Engine.instance.input
        move_x, move_y = 0, 0
        if inp.is_key_pressed(Keys.LEFT) or inp.is_key_pressed(Keys.A):
            move_x -= 1
        if inp.is_key_pressed(Keys.RIGHT) or inp.is_key_pressed(Keys.D):
            move_x += 1
        if inp.is_key_pressed(Keys.UP) or inp.is_key_pressed(Keys.W):
            move_y -= 1
        if inp.is_key_pressed(Keys.DOWN) or inp.is_key_pressed(Keys.S):
            move_y += 1
        if move_x != 0 and move_y != 0:
            length = math.hypot(move_x, move_y)
            move_x /= length
            move_y /= length
        speed = self.focus_speed if inp.is_key_pressed(Keys.LSHIFT) else self.base_speed
        self.velocity_x = move_x * speed
        self.velocity_y = move_y * speed
        super().update(delta)
        self.local_x = max(0, min(self.local_x, VIRTUAL_W - self.collider.width))
        self.local_y = max(0, min(self.local_y, VIRTUAL_H - self.collider.height))

    def on_collision_enter(self, other):
        if getattr(other, "layer", "") == "bullet":
            self.hp -= 1


class Boss(Node2D):
    def __init__(self, name, x, y, pool):
        super().__init__(name, x, y)
        self.pool = pool
        self.fire_timer = 0.0
        self.base_fire_rate = 0.5
        self.fire_rate_multiplier = 1.0
        self.angle_offset = 0.0
        self.bullet_speed = 200.0

    def update(self, delta):
        self.fire_timer -= delta
        self.angle_offset += 45 * delta
        if self.fire_timer <= 0:
            rate = self.base_fire_rate / self.fire_rate_multiplier
            self.fire_timer = rate
            self.fire_pattern()
        super().update(delta)

    def fire_pattern(self):
        bullet_count = int(12 * min(self.fire_rate_multiplier, 5))
        angle_step = 360.0 / bullet_count
        gx, gy = self.get_global_position()
        for i in range(bullet_count):
            b = self.pool.get()
            if b:
                angle = math.radians(self.angle_offset + i * angle_step)
                vx = math.cos(angle) * self.bullet_speed
                vy = math.sin(angle) * self.bullet_speed
                b.fire(gx, gy, vx, vy)


def main():
    engine = Engine("Level 1: Bullet Hell (Saturation & Object Pooling)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    bullet_layer = Node2D("BulletLayer")
    root.add_child(bullet_layer)
    pool = BulletPool(3000, bullet_layer)

    boss = Boss("Boss", VIRTUAL_W / 2, 100, pool)
    root.add_child(boss)
    boss.add_child(CircleNode("BossVis", 0, 0, 30, (200, 50, 200)))

    player_col = Collider2D("PlayerCol", 0, 0, 10, 10)
    player_col.layer = "player"
    player_col.mask = {"bullet"}
    player = BulletPlayer("Player", VIRTUAL_W / 2, 500, player_col, collision_world)
    root.add_child(player)
    player.add_child(player_col)
    player.add_child(RectangleNode("PlayerVis", 0, 0, 10, 10, (50, 255, 50)))

    marathon_time = 0.0
    initial_boss_x = boss.local_x
    accumulator = 0.0

    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        for event in engine.events:
            if event.type == 'key_down' and event.key == Keys.S:
                boss.fire_rate_multiplier *= 2.0
                print(f"Saturation Mode! Multiplier: {boss.fire_rate_multiplier}x")

        profiler.begin("Logic")
        while accumulator >= engine.fixed_dt:
            marathon_time += engine.fixed_dt
            if marathon_time >= 600.0:
                marathon_time = 0.0
                drift = boss.local_x - initial_boss_x
                print(f"[MARATHON] Float Drift over 10min: {drift} pixels")
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Logic")

        profiler.begin("Render")
        r.fill(surface, (20, 20, 30))
        root.render(surface)

        hud_lines = [
            f"FPS: {engine.fps:.1f}",
            f"Active Bullets: {pool.active_count} / {len(pool.pool) + pool.active_count}",
            f"Pool Alloc/Recycle: {pool.allocations} / {pool.recycles}",
            f"Boss Multiplier (Press 'S'): {boss.fire_rate_multiplier}x",
            f"Player HP: {player.hp}",
            f"Mem: {profiler.get_memory_mb():.1f} MB"
        ]
        y = 10
        for line in hud_lines:
            txt = r.render_text_uncached(line, (255, 255, 255))
            r.blit(surface, txt, (10, y))
            y += 20
        profiler.end("Render")

        engine.end_frame()

    profiler.print_summary()
    engine.quit()


if __name__ == "__main__":
    main()
