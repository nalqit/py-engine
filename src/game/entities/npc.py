from src.engine.physics.physics_body_2d import PhysicsBody2D


class NPC(PhysicsBody2D):
    """NPC entity — Level 2: collision only, no gameplay logic."""

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
