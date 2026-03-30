from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.rectangle_node import RectangleNode
from src.pyengine2D.collision.area2d import Area2D

class RisingVoid(Area2D):
    def __init__(self, name, x, y):
        # A very wide Area2D to catch the player
        super().__init__(name, x, y, 2000, 150)

    def ready(self):
        """Called automatically after instantiation to setup loaded graphics."""
        self.layer = "hazard"
        self.mask = {"player"}
        self.speed = 80.0 # Base speed
        
        # Grab visuals from the loaded node tree instead of creating new ones
        from src.pyengine2D.scene.particles import ParticleEmitter2D
        self.particles = None
        for child in self.children:
            if isinstance(child, ParticleEmitter2D):
                self.particles = child
                break

    def update(self, delta):
        # Move upwards
        self.local_y -= self.speed * delta
        
        # Emit bubbles
        import random
        if self.particles:
            gx, gy = self.get_global_position()
            if random.random() < 0.3:
                self.particles.emit(gx + random.randint(-400, 400), gy - 40, count=1, 
                                    speed_range=(20, 50), angle_range=(250, 290), 
                                    color=(120, 0, 220))
        
        super().update(delta)

    def on_area_entered(self, body):
        if body.name == "Player":
            print("Vaporized by the Void!")
            if hasattr(body, "reset_position"):
                body.reset_position()
                # Reset void position too?
                self.local_y = body.local_y + 400
