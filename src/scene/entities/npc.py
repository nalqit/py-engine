from src.scene.physics.physics_body_2d import PhysicsBody2D
from src.scene.physics.ai_controller import AIController


class NPC(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.controller = AIController(self)

        self.use_gravity = True
        self.speed = 100.0
