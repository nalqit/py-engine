from src.scene.node2d import Node2D
from src.scene.collision.collider2d import Collider2D
import pygame


class CollisionWorld(Node2D):
    def __init__(self, name):
        super().__init__(name)

    def _get_root(self):
        node = self
        while node.parent:
            node = node.parent
        return node

    def _walk(self, node):
        for child in node.children:
            yield child
            yield from self._walk(child)

    def _get_all_colliders(self):
        root = self._get_root()
        for node in self._walk(root):
            if isinstance(node, Collider2D):
                yield node

    def check_collision(self, collider, test_x, test_y):
        test_rect = pygame.Rect(
            test_x,
            test_y,
            collider.width,
            collider.height
        )

        for other in self._get_all_colliders():
            if other is collider:
                continue

            if other.layer not in collider.mask:
                continue

            if test_rect.colliderect(other.get_rect()):
                return other

        return None



