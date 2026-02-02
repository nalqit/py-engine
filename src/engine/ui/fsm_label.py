import pygame
from src.engine.scene.node2d import Node2D

class FSMLabel(Node2D):
    def __init__(self, name, body, y_offset=-20):
        super().__init__(name, 0, y_offset)
        self.body = body
        self.font = pygame.font.SysFont(None, 16)

    def render(self, surface):
        state_name = self.body.state_machine.current_state.name
        text = self.font.render(state_name, True, (255, 255, 255))

        sx, sy = self.get_screen_position()
        surface.blit(text, (sx, sy))

        super().render(surface)
