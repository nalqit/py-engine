import pygame
from .node2d import Node2D

class RectangleNode(Node2D):
    """A Node that renders a rectangle and handles basic movement."""
    def __init__(self, name: str, x: float, y: float, width: int, height: int, color: tuple):
        super().__init__(name, x, y)
        self.width = width
        self.height = height
        self.color = color
        self.speed = 200.0
        
    def update(self, delta: float) -> None:
        
            
        # Recursive update
        super().update(delta)

    def render(self, surface):
        screen_x, screen_y = self.get_screen_position()
        
        # Apply scaling to width and height
        sw = self.width * self.scale_x
        sh = self.height * self.scale_y
        
        # Center the rectangle based on scale (optional, but better for juice)
        # gx = screen_x - (sw - self.width) / 2
        # gy = screen_y - (sh - self.height) / 2
        
        # For simple squash/stretch from bottom, we offset Y differently
        # Let's just do standard scaling for now
        rect = pygame.Rect(int(screen_x), int(screen_y), int(sw), int(sh))
        pygame.draw.rect(surface, self.color, rect)
        super().render(surface)
