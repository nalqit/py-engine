import pygame
from src.scene.node2d import Node2D

class Collider2D(Node2D):
    def __init__(self, name, x, y, width, height, is_static=False):
        super().__init__(name, x, y)
        self.width = width
        self.height = height
        self.is_static = is_static

    def get_rect(self):
        gx, gy = self.get_global_position()
        return pygame.Rect(int(gx), int(gy), self.width, self.height)
