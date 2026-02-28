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
            from src.pyengine2D.core.engine import Engine
            screen_w = Engine.instance.virtual_w if Engine.instance else 800
            screen_h = Engine.instance.virtual_h if Engine.instance else 600
            cx, cy = Node2D.camera.get_global_position()
            # Return as integers to prevent float rounding desync with TilemapNode
            return int(gx - cx + screen_w//2), int(gy - cy + screen_h//2)
        return int(gx), int(gy)

        

