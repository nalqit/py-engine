from src.engine.scene.node2d import Node2D
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_result import CollisionResult


class CollisionWorld(Node2D):
    """
    Manages all colliders in the scene and provides collision queries.
    
    Responsibilities:
        - Walk the scene tree to find Collider2D nodes
        - check_collision(): test a collider at a candidate position,
          return a CollisionResult with penetration and normal
        - process_collisions(): broad-phase pair detection with
          enter/stay/exit event emission
    """

    def __init__(self, name):
        super().__init__(name)
        self._last_collisions = set()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _walk(self, node):
        """Recursively yield all descendants of a node."""
        for child in node.children:
            yield child
            yield from self._walk(child)

    def _get_root(self):
        """Walk up to the scene root."""
        root = self
        while root.parent:
            root = root.parent
        return root

    # ------------------------------------------------------------------
    # Collision query
    # ------------------------------------------------------------------

    def check_collision(self, collider, target_x, target_y):
        """
        Test whether moving *collider*'s owner to (target_x, target_y)
        would cause an overlap with any other collider.

        Uses float-precision AABB checks (not integer pygame.Rects)
        to avoid sub-pixel hopping near surfaces.

        Returns a CollisionResult describing the shallowest penetration
        found (i.e. the first axis that should be resolved).
        """
        # Compute the collider's float position at the target.
        # collider.local_x/y is the offset from its parent (the body).
        current_parent_gx, current_parent_gy = 0.0, 0.0
        if collider.parent:
            current_parent_gx, current_parent_gy = (
                collider.parent.get_global_position()
            )

        move_dx = target_x - current_parent_gx
        move_dy = target_y - current_parent_gy

        # Float-precision test bounds
        test_left = current_parent_gx + move_dx + collider.local_x
        test_top = current_parent_gy + move_dy + collider.local_y
        test_right = test_left + collider.width
        test_bottom = test_top + collider.height

        root = self._get_root()

        best_result = CollisionResult.none()
        smallest_penetration = float('inf')

        for node in self._walk(root):
            if not isinstance(node, Collider2D):
                continue

            other = node
            if other is collider:
                continue

            # Layer/mask filtering
            if other.layer not in collider.mask:
                continue

            # Triggers don't block movement
            if other.is_trigger:
                continue

            # Other collider bounds (float from global position)
            ogx, ogy = other.get_global_position()
            other_left = ogx
            other_top = ogy
            other_right = other_left + other.width
            other_bottom = other_top + other.height

            # Float-precision overlap check (strict inequality = no touching)
            if (test_left >= other_right or test_right <= other_left or
                    test_top >= other_bottom or test_bottom <= other_top):
                continue

            # --- Compute penetration on each axis (float) ---
            overlap_left = test_right - other_left
            overlap_right = other_right - test_left
            overlap_top = test_bottom - other_top
            overlap_bottom = other_bottom - test_top

            if overlap_left < overlap_right:
                pen_x = overlap_left
                normal_x = -1.0
            else:
                pen_x = overlap_right
                normal_x = 1.0

            if overlap_top < overlap_bottom:
                pen_y = overlap_top
                normal_y = -1.0
            else:
                pen_y = overlap_bottom
                normal_y = 1.0

            # Choose axis with smallest penetration (MTV)
            if pen_x < pen_y:
                pen = pen_x
                nx, ny = normal_x, 0.0
            else:
                pen = pen_y
                nx, ny = 0.0, normal_y

            if pen < smallest_penetration:
                smallest_penetration = pen
                best_result = CollisionResult(
                    collided=True,
                    collider=other,
                    normal_x=nx,
                    normal_y=ny,
                    penetration=pen,
                )

        return best_result

    # ------------------------------------------------------------------
    # Broad-phase pair detection (enter / stay / exit events)
    # ------------------------------------------------------------------

    def process_collisions(self):
        """Call once per frame to emit collision enter/stay/exit events."""
        root = self._get_root()

        all_colliders = [
            node for node in self._walk(root)
            if isinstance(node, Collider2D)
        ]

        current = set()

        for i, a in enumerate(all_colliders):
            for b in all_colliders[i + 1:]:
                a_sees_b = b.layer in a.mask
                b_sees_a = a.layer in b.mask

                if not a_sees_b and not b_sees_a:
                    continue

                if a.get_rect().colliderect(b.get_rect()):
                    pair = tuple(sorted((a, b), key=id))
                    current.add(pair)

                    if pair not in self._last_collisions:
                        self._emit(a, b, "enter")
                    else:
                        self._emit(a, b, "stay")

        # Exited pairs
        for pair in self._last_collisions - current:
            a, b = pair
            self._emit(a, b, "exit")

        self._last_collisions = current

    def _emit(self, a, b, phase):
        """Notify parent bodies of collision events."""
        for col, other in ((a, b), (b, a)):
            body = col.parent
            if not body:
                continue
            method = f"on_collision_{phase}"
            if hasattr(body, method):
                getattr(body, method)(other)
