from src.scene.physics.physics_body_2d import PhysicsBody2D


class Box(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)

        self.use_gravity = True
        self.velocity_x = 0
        self.velocity_y = 0
        self.speed = 0  # Boxes don't have autonomous speed
