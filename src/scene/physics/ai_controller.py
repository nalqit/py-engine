from src.scene.physics.controller import Controller


class AIController(Controller):
    def __init__(self):
        self.direction = 1

    def update(self, body, delta):
        speed = body.speed
        dx = self.direction * speed * delta

        # Check for collisions ahead to flip direction
        if body.collision_world.check_collision(
            body.collider, body.local_x + dx, body.local_y, margin=(0, -2)
        ):
            self.direction *= -1
            body.velocity_x = 0
        else:
            body.velocity_x = self.direction * speed
