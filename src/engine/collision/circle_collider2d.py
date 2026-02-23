import pygame
from src.engine.scene.node2d import Node2D

class CircleCollider2D(Node2D):
    """
    Circular collider for narrow-phase collision.
    Seamlessly integrates with AABB broadphase.
    Note: position is the CENTER of the circle.
    """
    def __init__(self, name, x, y, radius, is_static=False, is_trigger=False):
        super().__init__(name, x, y)
        self.radius = radius
        self.is_static = is_static
        self.is_trigger = is_trigger
        self.layer = "default"
        self.mask = set()
        
        # Mock AABB definitions for broadphase compatibility
        self.width = radius * 2
        self.height = radius * 2

    def get_rect(self) -> pygame.Rect:
        """Returns the broad-phase AABB encompassing the circle."""
        gx, gy = self.get_global_position()
        r = self.radius * self.scale_x
        # x, y is the center, so top-left is x-r, y-r
        return pygame.Rect(int(gx - r), int(gy - r), int(r * 2), int(r * 2))

    def render(self, surface) -> None:
        """Debug draw for circle collider."""
        from src.engine.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None
        sx, sy = self.get_screen_position()
        r = self.radius * self.scale_x

        if renderer:
            color = (0, 0, 255, 128) if self.is_static else (255, 0, 0, 128)
            overlay = renderer.create_surface(int(r * 2 + 1), int(r * 2 + 1), alpha=True)
            renderer.draw_circle(overlay, color, int(r), int(r), int(r))
            renderer.blit(surface, overlay, (int(sx - r), int(sy - r)))
            renderer.draw_circle(surface, (255, 255, 255), int(sx), int(sy), int(r), 1)

        super().render(surface)

