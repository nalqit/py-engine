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

        Returns a CollisionResult describing the shallowest penetration
        found (i.e. the first axis that should be resolved).
        """
        # Build a test rect as if the collider's parent were at target_x/y.
        # The collider's local offset relative to its parent is preserved.
        current_parent_gx, current_parent_gy = 0.0, 0.0
        if collider.parent:
            current_parent_gx, current_parent_gy = (
                collider.parent.get_global_position()
            )

        # Delta the parent would move
        dx = target_x - current_parent_gx
        dy = target_y - current_parent_gy

        base_rect = collider.get_rect()
        test_rect = base_rect.move(dx, dy)

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

            other_rect = other.get_rect()

            if not test_rect.colliderect(other_rect):
                continue

            # --- Compute penetration on each axis ---
            overlap_left  = test_rect.right - other_rect.left
            overlap_right = other_rect.right - test_rect.left
            overlap_top   = test_rect.bottom - other_rect.top
            overlap_bottom = other_rect.bottom - test_rect.top

            # Smallest positive overlap per axis gives penetration direction
            if overlap_left < overlap_right:
                pen_x = overlap_left
                normal_x = -1.0  # push left
            else:
                pen_x = overlap_right
                normal_x = 1.0   # push right

            if overlap_top < overlap_bottom:
                pen_y = overlap_top
                normal_y = -1.0  # push up
            else:
                pen_y = overlap_bottom
                normal_y = 1.0   # push down

            # Choose the axis with the smallest penetration (MTV)
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
