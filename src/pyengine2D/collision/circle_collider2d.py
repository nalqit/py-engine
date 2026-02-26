import pygame
from src.pyengine2D.collision.collider2d import Collider2D

class CircleCollider2D(Collider2D):
    """
    Circular collider for narrow-phase collision.
    Seamlessly integrates with AABB broadphase.
    Note: position is the CENTER of the circle.
    """
    def __init__(self, name, x, y, radius, is_static=False, is_trigger=False):
        # Initialize the base Collider2D with a bounding box (width/height = radius * 2)
        super().__init__(name, x, y, radius * 2, radius * 2, is_static, is_trigger)
        self.radius = radius

    def get_rect(self):
        """Returns the broad-phase AABB encompassing the circle."""
        gx, gy = self.get_global_position()
        r = self.radius * self.scale_x
        # x, y is the center, so top-left is x-r, y-r
        return (gx - r, gy - r, gx + r, gy + r)

    def render(self, surface) -> None:
        """Debug draw for circle collider."""
        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        sx, sy = self.get_screen_position()
        r = self.radius * self.scale_x

        if renderer:
            color = (0, 0, 255, 128) if self.is_static else (255, 0, 0, 128)
            overlay = renderer.create_surface(int(r * 2 + 1), int(r * 2 + 1), alpha=True)
            renderer.draw_circle(overlay, color, int(r), int(r), int(r))
            renderer.blit(surface, overlay, (int(sx - r), int(sy - r)))
            renderer.draw_circle(surface, (255, 255, 255), int(sx), int(sy), int(r), 1)

        from src.pyengine2D.scene.node2d import Node2D
        Node2D.render(self, surface)

