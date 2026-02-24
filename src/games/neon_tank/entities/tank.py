import math
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode

class Turret(Node2D):
    def __init__(self, name, x, y):
        super().__init__(name, x, y)
        self.rotation = 0.0
        self.color = (50, 255, 50)
        self.width = 30
        self.height = 10

    def render(self, surface):
        from src.engine.core.engine import Engine
        if not Engine.instance:
            return
            
        renderer = Engine.instance.renderer
        sx, sy = self.get_screen_position()
        
        # Calculate rotated corners of the turret rectangle
        # Rectangle centered vertically at -height/2, extending width to the right
        # Muzzle is at (width, 0)
        
        half_h = self.height / 2
        corners = [
            (0, -half_h),
            (self.width, -half_h),
            (self.width, half_h),
            (0, half_h)
        ]
        
        rotated_points = []
        cos_a = math.cos(self.rotation)
        sin_a = math.sin(self.rotation)
        
        for px, py in corners:
            rx = px * cos_a - py * sin_a
            ry = px * sin_a + py * cos_a
            rotated_points.append((sx + rx, sy + ry))
            
        renderer.draw_polygon(surface, self.color, rotated_points)
        super().render(surface)

class PlayerTank(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.move_speed = 200.0
        self.rotation_speed = 5.0
        
        # Tank Body Visual
        self.body_vis = RectangleNode("TankBody", -20, -20, 40, 40, (0, 200, 0)) # Green Body
        self.add_child(self.body_vis)
        
        # Turret Visual (custom rotated node)
        self.turret = Turret("Turret", 0, 0)
        self.add_child(self.turret)
        
        self.fire_rate = 0.5
        self.fire_timer = 0.0

    def update(self, delta):
        inp = Engine.instance.input
        
        # 1. Movement Logic (WASD)
        move_vec_x = 0
        move_vec_y = 0
        if inp.is_key_pressed(Keys.W): move_vec_y -= 1
        if inp.is_key_pressed(Keys.S): move_vec_y += 1
        if inp.is_key_pressed(Keys.A): move_vec_x -= 1
        if inp.is_key_pressed(Keys.D): move_vec_x += 1
        
        # Normalize movement
        mag = math.sqrt(move_vec_x**2 + move_vec_y**2)
        if mag > 1.0:
            move_vec_x /= mag
            move_vec_y /= mag
            
        self.velocity_x = move_vec_x * self.move_speed
        self.velocity_y = move_vec_y * self.move_speed
        
        # 2. Aiming Logic (Mouse)
        mx, my = inp.get_mouse_pos()
        tx, ty = self.get_screen_position()
        
        # Simple screen-space direction
        angle = math.atan2(my - ty, mx - tx)
        self.turret.rotation = angle # Turret points to mouse
        
        # 3. Fire Logic
        self.fire_timer -= delta
        if inp.is_mouse_pressed(0) and self.fire_timer <= 0:
            self.fire(angle)
            self.fire_timer = self.fire_rate

        # 4. Integrate Physics
        super().update(delta)

    def fire(self, angle):
        # Spawn Bullet
        from .bullet import Bullet
        
        # Get global position of the muzzle
        gx, gy = self.get_global_position()
        muzzle_gx = gx + math.cos(angle) * 30
        muzzle_gy = gy + math.sin(angle) * 30
        
        # Convert muzzle global to parent local
        # Bullet will be child of self.parent (Arena)
        pgx, pgy = 0.0, 0.0
        if self.parent and isinstance(self.parent, Node2D):
            pgx, pgy = self.parent.get_global_position()
            
        spawn_x = muzzle_gx - pgx
        spawn_y = muzzle_gy - pgy
        
        bullet = Bullet(f"Bullet_{Engine.instance.get_ticks_ms()}", spawn_x, spawn_y, angle)
        
        # Add to parent of tank (the arena)
        if self.parent:
            self.parent.add_child(bullet)
