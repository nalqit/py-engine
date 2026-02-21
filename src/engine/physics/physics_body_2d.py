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
        - Supports opt-in direct positional pushing via can_push / pushable

    Does NOT contain:
        - Jump logic, input, FSM, controllers, or gameplay flags
    """

    # Tiny separation after snapping to prevent float-precision ghost overlaps
    SNAP_SEP = 0.01
    # Maximum chain push depth (A pushes B pushes C ...)
    MAX_PUSH_DEPTH = 4

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y)
        self.collider = collider
        self.collision_world = collision_world

        self.velocity_x = 0.0
        self.velocity_y = 0.0

        # Engine-level gravity (Level 3)
        self.use_gravity = False
        self.gravity = 800.0

        # Push system (opt-in)
        self.can_push = False       # This body can push pushable bodies
        self.pushable = False       # This body can be pushed
        self.push_strength = 1.0    # How strong this pusher is
        self.push_weight = 1.0      # Resistance to being pushed

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

    # ------------------------------------------------------------------
    # Push helpers
    # ------------------------------------------------------------------

    def _refresh_collider_cache(self, body):
        """Update the collision world's cached rect for a body's collider."""
        col = body.collider
        gx, gy = col.get_global_position()
        sw = col.width * col.scale_x
        sh = col.height * col.scale_y
        self.collision_world._cached_rects[col] = (gx, gy, gx + sw, gy + sh)

    def _snap_to_obstacle(self, body, obstacle_collider, dx, snap_sep):
        """Snap body flush against an obstacle on X axis."""
        bpgx = 0.0
        if body.parent and isinstance(body.parent, Node2D):
            bpgx, _ = body.parent.get_global_position()

        ogx, _ = obstacle_collider.get_global_position()
        osw = obstacle_collider.width * obstacle_collider.scale_x
        bsw = body.collider.width * body.collider.scale_x

        if dx > 0:
            body.local_x = ogx - bsw - body.collider.local_x - bpgx - snap_sep
        else:
            body.local_x = ogx + osw - body.collider.local_x - bpgx + snap_sep

        body.update_transforms()
        self._refresh_collider_cache(body)

    def _try_push(self, pusher, target, dx, depth=0):
        """
        Recursively try to push target by dx.
        Returns True if the target was moved (even partially against a wall).
        Handles chain reactions: A → B → C up to MAX_PUSH_DEPTH.
        """
        if depth > self.MAX_PUSH_DEPTH:
            return False

        # Strength check
        if pusher.push_strength < target.push_weight:
            return False

        # Calculate target's new position
        tpgx, tpgy = 0.0, 0.0
        if target.parent and isinstance(target.parent, Node2D):
            tpgx, tpgy = target.parent.get_global_position()

        target_new_lx = target.local_x + dx
        result = self.collision_world.check_collision(
            target.collider, tpgx + target_new_lx, tpgy + target.local_y
        )

        if not result.collided:
            # Clear path — move freely
            target.local_x = target_new_lx
            target.update_transforms()
            self._refresh_collider_cache(target)
            target.on_pushed(pusher)
            return True

        # Something is in the way
        hit_body = result.collider.parent
        if isinstance(hit_body, PhysicsBody2D) and hit_body.pushable:
            # Chain reaction: try to push the next body first
            pushed = self._try_push(pusher, hit_body, dx, depth + 1)
            if pushed:
                # Re-check: maybe there's room now
                result2 = self.collision_world.check_collision(
                    target.collider, tpgx + target_new_lx, tpgy + target.local_y
                )
                if not result2.collided:
                    target.local_x = target_new_lx
                    target.update_transforms()
                    self._refresh_collider_cache(target)
                    target.on_pushed(pusher)
                    return True
                else:
                    # Still blocked — snap to whatever is there
                    self._snap_to_obstacle(target, result2.collider, dx, self.SNAP_SEP)
                    target.on_pushed(pusher)
                    return True
            else:
                # Chain blocked — snap target to the immovable obstacle
                self._snap_to_obstacle(target, result.collider, dx, self.SNAP_SEP)
                target.on_pushed(pusher)
                return True
        else:
            # Blocked by a wall or non-pushable — snap to it
            self._snap_to_obstacle(target, result.collider, dx, self.SNAP_SEP)
            target.on_pushed(pusher)
            return True

    # ------------------------------------------------------------------
    # Core movement
    # ------------------------------------------------------------------

    def move_and_collide(self, dx, dy):
        """
        Attempt to move by (dx, dy), resolving collisions per-axis.
        Supports direct positional pushing of pushable bodies.
        """
        # Get parent total offset to convert between local and global space
        pgx, pgy = 0.0, 0.0
        if self.parent and isinstance(self.parent, Node2D):
            pgx, pgy = self.parent.get_global_position()

        # --- X axis ---
        if dx != 0:
            target_lx = self.local_x + dx
            result = self.collision_world.check_collision(
                self.collider, pgx + target_lx, pgy + self.local_y
            )
            if not result.collided:
                self.local_x = target_lx
            else:
                hit_body = result.collider.parent

                # Push logic: if we can push and the hit body is pushable
                if (self.can_push
                        and isinstance(hit_body, PhysicsBody2D)
                        and hit_body.pushable):
                    self._try_push(self, hit_body, dx, depth=0)
                    # Snap self to the pushed body's new edge
                    ogx, _ = hit_body.get_global_position()
                    osw = hit_body.collider.width * hit_body.collider.scale_x
                    sw = self.collider.width * self.collider.scale_x
                    if dx > 0:
                        self.local_x = ogx - sw - self.collider.local_x - pgx - self.SNAP_SEP
                    else:
                        self.local_x = ogx + osw - self.collider.local_x - pgx + self.SNAP_SEP
                else:
                    # Standard wall snap
                    ogx, _ = result.collider.get_global_position()
                    osw = result.collider.width * result.collider.scale_x
                    sw = self.collider.width * self.collider.scale_x
                    if dx > 0:
                        self.local_x = ogx - sw - self.collider.local_x - pgx - self.SNAP_SEP
                    else:
                        self.local_x = ogx + osw - self.collider.local_x - pgx + self.SNAP_SEP
                self.velocity_x = 0.0

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
                ogy = result.collider.get_global_position()[1]
                osh = result.collider.height * result.collider.scale_y
                other_top, other_bottom = ogy, ogy + osh

                sh = self.collider.height * self.collider.scale_y
                if dy > 0:
                    self.local_y = other_top - sh - self.collider.local_y - pgy - self.SNAP_SEP
                else:
                    self.local_y = other_bottom - self.collider.local_y - pgy + self.SNAP_SEP
                self.velocity_y = 0.0

            self.update_transforms()

    # ------------------------------------------------------------------
    # Impulse
    # ------------------------------------------------------------------

    def apply_impulse(self, ix, iy):
        """Add an instantaneous velocity change (e.g. jump, knockback)."""
        self.velocity_x += ix
        self.velocity_y += iy

    # ------------------------------------------------------------------
    # Collision & push event hooks (override in subclasses)
    # ------------------------------------------------------------------

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass

    def on_pushed(self, pusher):
        """Called when this body is pushed by another body. Override for effects."""
        pass

