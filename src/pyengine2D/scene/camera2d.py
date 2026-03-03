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
            
            # Smoothly interpolate current position to target position center
            smooth_speed = 5.0
            t = min(1.0, smooth_speed * delta)
            self.local_x += (tx - self.local_x) * t
            self.local_y += (ty - self.local_y) * t
            # Snap to integer to prevent subpixel jitter between entities and tilemap
            self.local_x = round(self.local_x)
            self.local_y = round(self.local_y)

        super().update(delta)

    def get_viewport_rect(self):
        """Returns a pygame.Rect representing the world space bounds seen by the camera, plus padding."""
        import pygame
        from src.pyengine2D.core.engine import Engine
        engine = Engine.instance
        if not engine:
            return pygame.Rect(0, 0, 0, 0)
            
        gx, gy = self.get_global_position()
        w, h = engine.virtual_w, engine.virtual_h
        padding = 128  # Padding to avoid snapping objects on screen edges out of existence
        
        return pygame.Rect(gx - w // 2 - padding, gy - h // 2 - padding, w + padding * 2, h + padding * 2)
