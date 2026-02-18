from src.engine.physics.physics_body_2d import PhysicsBody2D


class NPC(PhysicsBody2D):
    """NPC entity — Level 3: physics body with gravity."""

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
