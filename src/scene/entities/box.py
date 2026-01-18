from src.scene.physics.physics_body_2d import PhysicsBody2D

class Box(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)

        self.use_gravity = True
        self.gravity = 1500
        self.velocity_x = 0
        self.velocity_y = 0

    def update(self, delta):
        # Gravity
        if self.use_gravity:
            self.velocity_y += self.gravity * delta

        dx = self.velocity_x * delta
        dy = self.velocity_y * delta

        self.move_and_collide(dx, dy, delta)

        # احتكاك بسيط
        self.velocity_x *= 0.9

        super().update(delta)
