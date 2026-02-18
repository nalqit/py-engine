from src.engine.physics.physics_body_2d import PhysicsBody2D


class Player(PhysicsBody2D):
    """Player entity — Level 2: collision only, no gameplay logic."""

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
