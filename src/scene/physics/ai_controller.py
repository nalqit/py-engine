from src.scene.physics.controller import Controller


class AIController(Controller):
    def __init__(self, body):
        super().__init__(body)
        self.direction = 1



    def update(self, body, delta):
        dx = self.direction * 1  # مجرد نية

        if body.collision_world.check_collision(
            body.collider,
            body.local_x + dx,
            body.local_y,
            margin=(0, -2),
        ):
            self.direction *= -1

        body.intent_x = self.direction
