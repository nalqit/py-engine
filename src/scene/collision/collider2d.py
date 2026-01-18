import pygame
from src.scene.node2d import Node2D

class Collider2D(Node2D):
    def __init__(self, name, x, y, width, height, is_static=False, shape="rect"):
        super().__init__(name, x, y)
        self.width = width
        self.height = height
        self.is_static = is_static
        self.body_type = "static" if is_static else "dynamic"
        self.velocity = pygame.Vector2(0, 0)
        self.shape = shape
        self.layer = "default"
        self.mask = set()


    def get_rect(self):
        gx, gy = self.get_global_position()
        return pygame.Rect(
            int(gx),
            int(gy),
            self.width,
            self.height
    )



    def render(self, surface: pygame.Surface) -> None:
        # Debug Draw
        rect = self.get_rect()
        
        # Adjust for camera if exists
        sx, sy = self.get_screen_position()
        screen_rect = pygame.Rect(int(sx), int(sy), self.width, self.height)

        # Transparent overlay
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        color = (0, 0, 255, 128) if self.is_static else (255, 0, 0, 128) # Blue for walls, Red for player
        s.fill(color)
        surface.blit(s, screen_rect)
        
        # Outline
        pygame.draw.rect(surface, (255, 255, 255), screen_rect, 1)
        
        super().render(surface)
    def get_mask_layer():
        
        pass
