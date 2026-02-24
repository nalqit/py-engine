from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.area2d import Area2D

class RisingVoid(Area2D):
    def __init__(self, name, x, y):
        # A very wide Area2D to catch the player
        super().__init__(name, x, y, 2000, 150)
        self.layer = "hazard"
        self.mask = {"player"}
        
        # Visual representation: Purple glowing void
        self.vis = RectangleNode(name + "_Vis", 0, 0, 2000, 150, (150, 0, 255))
        self.add_child(self.vis)
        
        self.speed = 80.0 # Base speed
        
        from src.engine.scene.particles import ParticleEmitter2D
        self.particles = ParticleEmitter2D("VoidParticles")
        self.add_child(self.particles)

    def update(self, delta):
        # Move upwards
        self.local_y -= self.speed * delta
        
        # Emit bubbles
        import random
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
