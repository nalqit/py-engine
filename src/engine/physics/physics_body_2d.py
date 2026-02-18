from src.engine.scene.node2d import Node2D


class PhysicsBody2D(Node2D):
    """
    Generic 2D physics body — Level 2 (Collision System).

    Responsibilities:
        - Holds position (inherited local_x, local_y from Node2D)
        - Holds velocity (velocity_x, velocity_y)
        - Computes motion displacement from velocity * delta
        - Queries CollisionWorld per axis
        - Resolves position using CollisionResult penetration
        - Zeroes velocity only on the axis of impact
    """

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y)
        self.collider = collider
        self.collision_world = collision_world

        self.velocity_x = 0.0
        self.velocity_y = 0.0

    def update(self, delta):
        # Compute frame displacement from velocity
        dx = self.velocity_x * delta
        dy = self.velocity_y * delta

        # Move with collision resolution
        self.move_and_collide(dx, dy)

        # Propagate update to children (collider, visuals, etc.)
        super().update(delta)

    def move_and_collide(self, dx, dy):
        # --- X axis ---
        if dx != 0:
            target_x = self.local_x + dx
            result = self.collision_world.check_collision(self.collider, target_x, self.local_y)
            if not result.collided:
                self.local_x = target_x
            else:
                # تصحيح الموضع على محور X فقط
                if result.normal_x > 0:
                    self.local_x = target_x - result.penetration
                elif result.normal_x < 0:
                    self.local_x = target_x + result.penetration
                self.velocity_x = 0.0

        # --- Y axis ---
        if dy != 0:
            target_y = self.local_y + dy
            result = self.collision_world.check_collision(self.collider, self.local_x, target_y)
            if not result.collided:
                self.local_y = target_y
            else:
                if result.normal_y > 0:
                    self.local_y = target_y - result.penetration
                elif result.normal_y < 0:
                    self.local_y = target_y + result.penetration
                self.velocity_y = 0.0

    # ------------------------------------------------------------------
    # Collision event hooks (override in subclasses or higher layers)
    # ------------------------------------------------------------------

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
