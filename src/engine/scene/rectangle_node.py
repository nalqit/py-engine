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

    def render(self, surface: pygame.Surface) -> None:
        sx, sy = self.get_screen_position() 
        rect = pygame.Rect(int(sx), int(sy), self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        
        # Recursive render
        super().render(surface)
