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
            self.local_x = tx - 400  # نصف عرض الشاشة
            self.local_y = ty - 300  # نصف ارتفاع الشاشة

        super().update(delta)
