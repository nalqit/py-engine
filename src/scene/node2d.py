from .node import Node

class Node2D(Node):
    """Base class for 2D nodes with position."""
    camera = None
    def __init__(self, name: str = "Node2D", local_x: float = 0.0, local_y: float = 0.0):
        super().__init__(name)
        self.local_x = local_x
        self.local_y = local_y

    def get_global_position(self):
        if not self.parent:
            return self.local_x, self.local_y
        else:
            parent_pos = self.parent.get_global_position()
            return parent_pos[0] + self.local_x, parent_pos[1] + self.local_y
    def get_screen_position(self):
        gx, gy = self.get_global_position()
        if Node2D.camera:
            # هذه المرة نحسب offset بحيث اللاعب في منتصف الشاشة
            screen_w, screen_h = 800, 600  # أو أرسل من main
            cx, cy = Node2D.camera.get_global_position()
            return gx - cx + screen_w//2, gy - cy + screen_h//2
        return gx, gy

        

