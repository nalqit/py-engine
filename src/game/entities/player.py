from src.engine.physics.physics_body_2d import PhysicsBody2D


class Player(PhysicsBody2D):
    """Player entity — Level 3: physics body with gravity."""

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
