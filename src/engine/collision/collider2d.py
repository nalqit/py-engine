import pygame
from src.engine.scene.node2d import Node2D


class Collider2D(Node2D):
    """
    Axis-Aligned Bounding Box (AABB) collider.
    
    Pure collision data — holds shape dimensions, layer/mask,
    and computes its world-space rect from the scene tree transform.
    """

    def __init__(self, name, x, y, width, height, is_static=False, is_trigger=False):
        super().__init__(name, x, y)
        self.width = width
        self.height = height
        self.is_static = is_static
        self.is_trigger = is_trigger
        self.layer = "default"
        self.mask = set()

    def get_rect(self):
        """Return the world-space pygame.Rect for this collider, accounting for scale."""
        gx, gy = self.get_global_position()
        # We multiply dimensions by the global scale. 
        # In this engine, we'll assume the collider's own scale is what matters most for its shape.
        sw = self.width * self.scale_x
        sh = self.height * self.scale_y
        return pygame.Rect(int(gx), int(gy), int(sw), int(sh))

    def render(self, surface: pygame.Surface) -> None:
        """Debug draw — transparent overlay + outline."""
        sx, sy = self.get_screen_position()
        sw = self.width * self.scale_x
        sh = self.height * self.scale_y
        
        screen_rect = pygame.Rect(int(sx), int(sy), int(sw), int(sh))

        s = pygame.Surface((int(sw), int(sh)), pygame.SRCALPHA)
        color = (0, 0, 255, 128) if self.is_static else (255, 0, 0, 128)
        s.fill(color)
        surface.blit(s, screen_rect)

        pygame.draw.rect(surface, (255, 255, 255), screen_rect, 1)

        super().render(surface)
