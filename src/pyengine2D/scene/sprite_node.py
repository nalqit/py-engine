import pygame
from .node2d import Node2D

class SpriteNode(Node2D):
    """
    A 2D node that renders a static image.
    Supports scaling and can be centered.
    """
    def __init__(self, name: str, image_path: str, x: float = 0.0, y: float = 0.0, centered: bool = False):
        super().__init__(name, x, y)
        self.image = pygame.image.load(image_path).convert_alpha()
        self.width, self.height = self.image.get_size()
        self.centered = centered

    def render(self, surface: pygame.Surface):
        sx, sy = self.get_screen_position()
        
        # Apply scaling
        sw = int(self.width * self.scale_x)
        sh = int(self.height * self.scale_y)
        
        if sw <= 0 or sh <= 0:
            super().render(surface)
            return

        # Scale image if necessary
        if self.scale_x != 1.0 or self.scale_y != 1.0:
            render_img = pygame.transform.scale(self.image, (sw, sh))
        else:
            render_img = self.image

        # Adjust position if centered
        render_x, render_y = sx, sy
        if self.centered:
            render_x -= sw // 2
            render_y -= sh // 2

        surface.blit(render_img, (int(render_x), int(render_y)))
        
        super().render(surface)
