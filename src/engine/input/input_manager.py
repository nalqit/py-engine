import pygame
from src.engine.scene.node import Node

class InputManager(Node):
    def __init__(self, name="Input"):
        super().__init__(name)
        self.actions = {
            "move_left": False,
            "move_right": False,
            "move_up": False,
            "move_down": False,
        }

    def update(self, delta):
        keys = pygame.key.get_pressed()

        self.actions["move_left"]  = keys[pygame.K_LEFT]
        self.actions["move_right"] = keys[pygame.K_RIGHT]
        self.actions["move_up"]    = keys[pygame.K_UP]
        self.actions["move_down"]  = keys[pygame.K_DOWN]

        super().update(delta)


    def is_pressed(self, action: str) -> bool:
        return self.actions.get(action, False)
