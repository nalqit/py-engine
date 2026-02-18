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
        """Return the world-space pygame.Rect for this collider."""
        gx, gy = self.get_global_position()
        return pygame.Rect(int(gx), int(gy), self.width, self.height)

    def render(self, surface: pygame.Surface) -> None:
        """Debug draw — transparent overlay + outline."""
        sx, sy = self.get_screen_position()
        screen_rect = pygame.Rect(int(sx), int(sy), self.width, self.height)

        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        color = (0, 0, 255, 128) if self.is_static else (255, 0, 0, 128)
        s.fill(color)
        surface.blit(s, screen_rect)

        pygame.draw.rect(surface, (255, 255, 255), screen_rect, 1)

        super().render(surface)
