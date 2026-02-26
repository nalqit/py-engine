import math
from src.pyengine2D.collision.area2d import Area2D
from src.pyengine2D.scene.rectangle_node import RectangleNode
from src.pyengine2D.core.engine import Engine

class Bullet(Area2D):
    def __init__(self, name, x, y, angle):
        # Bullet is a small Area2D for triggers
        super().__init__(name, x, y, 10, 10)
        self.speed = 400.0
        self.velocity_x = math.cos(angle) * self.speed
        self.velocity_y = math.sin(angle) * self.speed
        
        # Visual
        self.vis = RectangleNode(name + "_Vis", 0, 0, 10, 10, (255, 255, 0)) # Yellow Neon
        self.add_child(self.vis)
        
        # Collision settings
        self.layer = "bullet"
        self.mask = {"wall", "enemy"}
        
        self.lifetime = 2.0 # Seconds before self-destruct if it doesn't hit anything

    def update(self, delta):
        self.local_x += self.velocity_x * delta
        self.local_y += self.velocity_y * delta
        
        self.lifetime -= delta
        if self.lifetime <= 0:
            self.destroy()
            
        super().update(delta)

    def on_area_entered(self, other):
        # Check if we hit a wall or an enemy
        # In this engine, physics bodies might not be Area2D, so we check the 'layer' attribute
        # usually handled by the collision world emitting signals.
        pass
        
    def on_collision(self, other_col):
        # Handle collision with wall or enemy via layer
        if other_col.layer == "wall":
            self.destroy()
        elif other_col.layer == "enemy":
            # Other entity should handle taking damage
            self.destroy()

    def destroy(self):
        if self.parent:
            self.parent.remove_child(self)
