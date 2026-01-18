from .node2d import Node2D

class Camera2D(Node2D):
    def __init__(self, name="Camera2D"):
        super().__init__(name, 0, 0)
        self.target = None  # Node2D to follow

    def follow(self, target: Node2D):
        self.target = target

    def update(self, delta: float):
        if self.target:
            tx, ty = self.target.get_global_position()
            target_x = tx - 400
            target_y = ty - 300
            
            # Smoothly interpolate current position to target position
            smooth_speed = 5.0
            self.local_x += (target_x - self.local_x) * smooth_speed * delta
            self.local_y += (target_y - self.local_y) * smooth_speed * delta

        super().update(delta)
