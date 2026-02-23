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
        
        from src.engine.core.engine import Engine
        if Engine.instance:
            Engine.instance.renderer.draw_rect(surface, self.color, screen_x, screen_y, sw, sh)
        super().render(surface)
