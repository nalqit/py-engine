from .node2d import Node2D

class Player(Node2D):
    def __init__(self, name, x, y, input_manager, collider, collision_world):
        super().__init__(name, x, y)
        self.input = input_manager
        self.collider = collider
        self.collision_world = collision_world
        self.speed = 200.0

    def update(self, delta):
        dx = dy = 0
        if self.input.is_pressed("move_left"):
            dx -= 1
        if self.input.is_pressed("move_right"):
            dx += 1
        if self.input.is_pressed("move_up"):
            dy -= 1
        if self.input.is_pressed("move_down"):
            dy += 1

        dx *= self.speed * delta
        dy *= self.speed * delta

        if self.collider and self.collision_world:
            # X movement
            if not self.collision_world.check_collision(
                self.collider, self.local_x + dx, self.local_y
            ):
                self.local_x += dx
            # Y movement
            if not self.collision_world.check_collision(
                self.collider, self.local_x, self.local_y + dy
            ):
                self.local_y += dy
        else:
            self.local_x += dx
            self.local_y += dy

        super().update(delta)
