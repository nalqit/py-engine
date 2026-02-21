from src.engine.scene.node2d import Node2D
from src.engine.collision.collider2d import Collider2D

class Area2D(Node2D):
    """
    A node for detection overlaps without physical response.
    Triggers 'on_area_entered' and 'on_area_exited' signals.
    """
    def __init__(self, name, x, y, width, height):
        super().__init__(name, x, y)
        self.collider = Collider2D(name + "_AreaCol", 0, 0, width, height, is_static=False)
        self.collider.is_trigger = True
        self.collider.layer = "coin"
        self.collider.mask = {"player"}
        self.add_child(self.collider)
        
        # We'll use these to track overlaps
        self.overlapping_bodies = set()

    def on_collision_enter(self, other):
        body = other.parent
        if body and body not in self.overlapping_bodies:
            self.overlapping_bodies.add(body)
            self.on_area_entered(body)

    def on_collision_exit(self, other):
        body = other.parent
        if body in self.overlapping_bodies:
            self.overlapping_bodies.remove(body)
            self.on_area_exited(body)

    def on_area_entered(self, body):
        """Override this to handle detection."""
        pass

    def on_area_exited(self, body):
        """Override this to handle detection stop."""
        pass
