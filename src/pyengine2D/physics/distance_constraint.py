import math
from src.pyengine2D.scene.node2d import Node2D

class DistanceConstraint(Node2D):
    """
    Enforces a strict distance between a root origin and a RigidBody2D's center.
    Automatically solved by PhysicsWorld2D.
    """
    def __init__(self, name, anchor_x, anchor_y, body_a, length):
        super().__init__(name, anchor_x, anchor_y)
        self.body_a = body_a
        self.length = length

    def solve(self):
        """Pulls/Pushes body_a to exactly length from the anchor."""
        dx = self.body_a.local_x - self.local_x
        dy = self.body_a.local_y - self.local_y
        dist = math.hypot(dx, dy)
        
        if dist > 0.0001:
            diff = dist - self.length
            nx = dx / dist
            ny = dy / dist
            
            # Positional correction - since anchor is immovable, fully move body_a
            self.body_a.local_x -= nx * diff
            self.body_a.local_y -= ny * diff
            
            # Velocity correction:
            # Instead of destroying velocity, we project the velocity onto the tangent 
            # of the circular arc, preserving its absolute momentum perfectly!
            tx = -ny
            ty = nx
            
            # Dot product of velocity and tangent
            v_tangent = self.body_a.vx * tx + self.body_a.vy * ty
            
            # Reapply velocity strictly along the tangent (circular path)
            self.body_a.vx = tx * v_tangent
            self.body_a.vy = ty * v_tangent

    def render(self, surface):
        from src.pyengine2D.core.engine import Engine
        if not Engine.instance: return
        renderer = Engine.instance.renderer
        
        sx, sy = self.get_global_position()
        bx, by = self.body_a.get_global_position()
        
        renderer.draw_line(surface, (150, 150, 150), int(sx), int(sy), int(bx), int(by), 2)
        renderer.draw_circle(surface, (80, 80, 80), int(sx), int(sy), 4)
        
        super().render(surface)
