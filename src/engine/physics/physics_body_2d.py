from src.engine.scene.node2d import Node2D


class PhysicsBody2D(Node2D):
    """
    Generic 2D physics body — Level 3 (Physics Layer).

    Responsibilities:
        - Holds position (inherited local_x, local_y from Node2D)
        - Holds velocity (velocity_x, velocity_y)
        - Applies gravity when use_gravity is True
        - Supports instantaneous impulses via apply_impulse()
        - Computes motion displacement from velocity * delta
        - Queries CollisionWorld per axis
        - Resolves position using CollisionResult penetration
        - Zeroes velocity only on the axis of impact

    Does NOT contain:
        - Jump logic, input, FSM, controllers, or gameplay flags
    """

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y)
        self.collider = collider
        self.collision_world = collision_world

        self.velocity_x = 0.0
        self.velocity_y = 0.0

        # Engine-level gravity (Level 3)
        self.use_gravity = False
        self.gravity = 800.0

    def update(self, delta):
        # Apply gravity acceleration
        if self.use_gravity:
            self.velocity_y += self.gravity * delta

        # Compute frame displacement from velocity
        dx = self.velocity_x * delta
        dy = self.velocity_y * delta

        # Move with collision resolution
        self.move_and_collide(dx, dy)

        # Propagate update to children (collider, visuals, etc.)
        super().update(delta)

    def move_and_collide(self, dx, dy):
        """
        Attempt to move by (dx, dy), resolving collisions per-axis.
        Fixed to be scale-aware and coordinate-space consistent.
        """
        # Get parent total offset to convert between local and global space
        pgx, pgy = 0.0, 0.0
        if self.parent and isinstance(self.parent, Node2D):
            pgx, pgy = self.parent.get_global_position()

        # --- X axis ---
        if dx != 0:
            target_lx = self.local_x + dx
            # check_collision expects target in GLOBAL space
            result = self.collision_world.check_collision(
                self.collider, pgx + target_lx, pgy + self.local_y
            )
            if not result.collided:
                self.local_x = target_lx
            else:
                other_rect = result.collider.get_rect()
                sw = self.collider.width * self.collider.scale_x
                if dx > 0:
                    # Move right: snap our right edge to obstacle's left
                    self.local_x = other_rect.left - sw - self.collider.local_x - pgx
                else:
                    # Move left: snap our left edge to obstacle's right
                    self.local_x = other_rect.right - self.collider.local_x - pgx
                self.velocity_x = 0.0
            
            # Sync transforms so Y check uses the new, correct X position
            self.update_transforms()

        # --- Y axis (uses updated local_x) ---
        if dy != 0:
            target_ly = self.local_y + dy
            result = self.collision_world.check_collision(
                self.collider, pgx + self.local_x, pgy + target_ly
            )
            if not result.collided:
                self.local_y = target_ly
            else:
                other_rect = result.collider.get_rect()
                sh = self.collider.height * self.collider.scale_y
                if dy > 0:
                    # Move down: snap our bottom edge to obstacle's top
                    self.local_y = other_rect.top - sh - self.collider.local_y - pgy
                else:
                    # Move up: snap our top edge to obstacle's bottom
                    self.local_y = other_rect.bottom - self.collider.local_y - pgy
                self.velocity_y = 0.0
            
            # Sync transforms again
            self.update_transforms()

    # ------------------------------------------------------------------
    # Impulse
    # ------------------------------------------------------------------

    def apply_impulse(self, ix, iy):
        """Add an instantaneous velocity change (e.g. jump, knockback)."""
        self.velocity_x += ix
        self.velocity_y += iy

    # ------------------------------------------------------------------
    # Collision event hooks (override in subclasses or higher layers)
    # ------------------------------------------------------------------

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
