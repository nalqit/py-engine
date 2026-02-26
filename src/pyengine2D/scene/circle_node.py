import pygame
from .node2d import Node2D

class CircleNode(Node2D):
    """A Node that renders a circle."""
    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        radius: int,
        color: tuple
    ):
        super().__init__(name, x, y)
        self.radius = radius
        self.color = color

    def update(self, delta: float) -> None:
        # Logic here if needed
        
        # Recursive update
        super().update(delta)

    def render(self, surface: pygame.Surface) -> None:
        sx, sy = self.get_screen_position()

        from src.pyengine2D.core.engine import Engine
        if Engine.instance:
            Engine.instance.renderer.draw_circle(surface, self.color, sx, sy, self.radius)

        # Recursive render
        super().render(surface)
