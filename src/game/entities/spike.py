from src.engine.collision.area2d import Area2D

class Spike(Area2D):
    """
    A hazard that kills the player on contact.
    Built as a trigger area so players can pass into it fully.
    """
    def __init__(self, name, x, y, width=40, height=40):
        # Spike acts as a trigger area
        super().__init__(name, x, y, width, height)
        # Override the defaults in Area2D
        self.collider.layer = "hazard"
        self.collider.mask = {"player"}

    def on_area_entered(self, body):
        # We know body is player because of the mask, but check for safety
        if hasattr(body, "die"):
            body.die()
