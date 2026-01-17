from src.scene.node2d import Node2D

class CollisionWorld(Node2D):
    def __init__(self, name="CollisionWorld"):
        super().__init__(name)

    def check_collision(self, collider, new_x, new_y):
        test_rect = collider.get_rect().copy()
        test_rect.topleft = (new_x, new_y)

        for child in self.children:
            if child is collider:
                continue
            if child.get_rect().colliderect(test_rect):
                return True
        return False
