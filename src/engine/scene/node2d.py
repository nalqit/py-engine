from .node import Node

class Node2D(Node):
    """Base class for 2D nodes with position."""
    camera = None
    def __init__(self, name: str = "Node2D", local_x: float = 0.0, local_y: float = 0.0):
        super().__init__(name)
        self.local_x = local_x
        self.local_y = local_y
        self.scale_x = 1.0
        self.scale_y = 1.0
        self._cached_global_x = local_x
        self._cached_global_y = local_y

    def update_transforms(self):
        """Pre-calculate global positions recursively."""
        if not self.parent or not isinstance(self.parent, Node2D):
            self._cached_global_x = self.local_x
            self._cached_global_y = self.local_y
        else:
            pgx, pgy = self.parent.get_global_position()
            self._cached_global_x = pgx + self.local_x
            self._cached_global_y = pgy + self.local_y
        
        # Propagation to children
        super().update_transforms()

    def get_global_position(self):
        """Returns the pre-calculated global position."""
        return self._cached_global_x, self._cached_global_y
    def get_screen_position(self):
        gx, gy = self.get_global_position()
        if Node2D.camera:
            # هذه المرة نحسب offset بحيث اللاعب في منتصف الشاشة
            screen_w, screen_h = 800, 600  # أو أرسل من main
            cx, cy = Node2D.camera.get_global_position()
            return gx - cx + screen_w//2, gy - cy + screen_h//2
        return gx, gy

        

