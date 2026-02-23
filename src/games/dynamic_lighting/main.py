import math
import random

from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.core.renderer import BlendMode
from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600


class PointLight(Node2D):
    def __init__(self, name, x, y, radius, color):
        super().__init__(name, x, y)
        self.radius = radius
        self.color = color
        r = Engine.instance.renderer
        self.texture = r.create_surface(radius * 2, radius * 2, alpha=True)
        rv, gv, bv = color
        for i in range(radius, 0, -2):
            alpha = int(255 * (1 - (i / radius) ** 2))
            r.draw_circle(self.texture, (rv, gv, bv, alpha), radius, radius, i)
        self.light_surface = r.create_surface(radius * 2, radius * 2, alpha=True)


class LightingSystem(Node2D):
    def __init__(self, name, cw):
        super().__init__(name, 0, 0)
        self.collision_world = cw
        self.ambient_color = (40, 40, 60)
        self.light_map = Engine.instance.renderer.create_surface(VIRTUAL_W, VIRTUAL_H)
        self.lights = []

    def add_light(self, light):
        self.lights.append(light)
        self.add_child(light)

    def render(self, surface):
        r = Engine.instance.renderer
        r.fill(self.light_map, self.ambient_color)
        corners = []
        for col, rect in self.collision_world._cached_rects.items():
            if col.layer in ("wall", "cast_shadow"):
                l, t, ri, b = rect
                corners.extend([(l, t), (ri, t), (ri, b), (l, b)])
        corners.extend([(-10, -10), (VIRTUAL_W + 10, -10), (VIRTUAL_W + 10, VIRTUAL_H + 10), (-10, VIRTUAL_H + 10)])

        for light in self.lights:
            lx, ly = light.get_global_position()
            r.fill(light.light_surface, (0, 0, 0, 0))
            r.blit(light.light_surface, light.texture, (0, 0))
            angles = set()
            for cx, cy in corners:
                if math.hypot(cx - lx, cy - ly) > light.radius * 1.5:
                    continue
                angle = math.atan2(cy - ly, cx - lx)
                angles.update([angle - 0.001, angle, angle + 0.001])
            polygon_points = []
            for angle in sorted(angles):
                end_x = lx + math.cos(angle) * light.radius
                end_y = ly + math.sin(angle) * light.radius
                hit, hx, hy, _ = self.collision_world.raycast(lx, ly, end_x, end_y, mask={"wall", "cast_shadow"})
                polygon_points.append((hx, hy) if hit else (end_x, end_y))
            if len(polygon_points) >= 3:
                mask = r.create_surface(VIRTUAL_W, VIRTUAL_H, alpha=True)
                r.fill(mask, (0, 0, 0, 0))
                r.draw_polygon(mask, (255, 255, 255, 255), polygon_points)
                temp = r.create_surface(VIRTUAL_W, VIRTUAL_H, alpha=True)
                r.blit(temp, light.texture, (lx - light.radius, ly - light.radius))
                r.blit(temp, mask, (0, 0), BlendMode.RGBA_MULT)
                r.blit(self.light_map, temp, (0, 0), BlendMode.ADD)
            else:
                r.blit(self.light_map, light.texture, (lx - light.radius, ly - light.radius), BlendMode.ADD)
        r.blit(surface, self.light_map, (0, 0), BlendMode.MULT)


class PlayerController(PhysicsBody2D):
    def __init__(self, name, x, y, cw):
        col = Collider2D(name + "Col", 0, 0, 20, 20)
        col.layer = "cast_shadow"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.speed = 250.0
        self.add_child(col)
        self.add_child(RectangleNode("PVis", 0, 0, 20, 20, (200, 200, 200)))

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


def main():
    engine = Engine("Level 9: Dynamic Lighting (BLEND_ADD, Multipass Shadows)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)

    def wall(x, y, w, h):
        wn = Node2D(f"W_{x}_{y}", x, y)
        col = Collider2D(f"C_{x}_{y}", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        wn.add_child(col)
        wn.add_child(RectangleNode(f"V_{x}_{y}", 0, 0, w, h, (50, 50, 50)))
        root.add_child(wn)

    wall(0, 0, 800, 20); wall(0, 580, 800, 20); wall(0, 0, 20, 600); wall(780, 0, 20, 600)
    wall(200, 200, 50, 50); wall(500, 150, 40, 100); wall(300, 400, 150, 40); wall(650, 450, 60, 60)

    player = PlayerController("Player", 100, 100, cw)
    root.add_child(player)

    lighting = LightingSystem("Lighting", cw)
    player_light = PointLight("PLight", 10, 10, 300, (255, 200, 150))
    player.add_child(player_light)
    lighting.add_light(player_light)
    root.add_child(lighting)

    accumulator = 0.0
    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        for event in engine.events:
            if event.type == 'key_down' and event.key == Keys.L:
                sl = PointLight(f"SL_{random.randint(0,9999)}", random.randint(50, 750), random.randint(50, 550),
                                random.randint(150, 350),
                                (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)))
                root.add_child(sl)
                lighting.add_light(sl)

        profiler.begin("Logic")
        while accumulator >= engine.fixed_dt:
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Logic")

        profiler.begin("Render")
        r.fill(surface, (100, 100, 100))
        for child in root.children:
            if child is not lighting:
                child.render(surface)
        lighting.render(surface)
        hud = [f"FPS: {engine.fps:.1f}", f"Lights: {len(lighting.lights)}", "Press 'L' to spawn lights (Saturation)"]
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
