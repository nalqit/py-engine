from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.collision.collider2d import Collider2D
from src.pyengine2D.collision.polygon_collider2d import PolygonCollider2D
from src.pyengine2D.collision.collision_result import CollisionResult
from src.pyengine2D.collision.spatial_grid import UniformGrid
import math


class CollisionWorld(Node2D):
    """
    Manages all colliders in the scene and provides collision queries.
    
    Responsibilities:
        - Walk the scene tree to find Collider2D nodes
        - check_collision(): test a collider at a candidate position,
          return a CollisionResult with penetration and normal
        - process_collisions(): broad-phase pair detection with
          enter/stay/exit event emission

    Performance:
        Uses a UniformGrid spatial partitioning structure so that
        broad-phase pair detection is O(n·k) instead of O(n²).
    """

    def __init__(self, name, cell_size=128):
        super().__init__(name)
        self._last_collisions = set()
        self._cached_colliders = []
        self._cached_rects = {}  # collider -> (l, t, r, b)
        self._grid = UniformGrid(cell_size=cell_size)

    def update(self, delta):
        """Update cache before children update."""
        self._refresh_collider_cache()
        self._refresh_rect_cache()
        self.process_collisions()
        super().update(delta)

    def _refresh_collider_cache(self):
        """Flatten the collider list once per frame to avoid O(N^2) tree walking."""
        root = self._get_root()
        self._cached_colliders = [
            node for node in self._walk(root)
            if isinstance(node, Collider2D)
        ]

    def _refresh_rect_cache(self):
        """Pre-calculate all world-space collider bounds and populate spatial grid."""
        self._cached_rects = {}
        self._grid.clear()
        for col in self._cached_colliders:
            if hasattr(col, 'get_rect'):
                res = col.get_rect()
                if isinstance(res, tuple):
                    rect = res
                else:
                    rect = (res.left, res.top, res.right, res.bottom)
            else:
                gx, gy = col.get_global_position()
                sw = col.width * col.scale_x
                sh = col.height * col.scale_y
                rect = (gx, gy, gx + sw, gy + sh)
            self._cached_rects[col] = rect
            self._grid.insert(col, rect[0], rect[1], rect[2], rect[3])

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

        # Float-precision test bounds (scaled)
        sw = collider.width * collider.scale_x
        sh = collider.height * collider.scale_y
        
        if hasattr(collider, 'radius'):
            rx = collider.radius * collider.scale_x
            ry = collider.radius * collider.scale_y
            test_left = current_parent_gx + move_dx + collider.local_x - rx
            test_top = current_parent_gy + move_dy + collider.local_y - ry
        else:
            test_left = current_parent_gx + move_dx + collider.local_x
            test_top = current_parent_gy + move_dy + collider.local_y
            
        test_right = test_left + sw
        test_bottom = test_top + sh

        best_result = CollisionResult.none()
        smallest_penetration = float('inf')

        # Use spatial grid to get candidates instead of scanning all colliders
        candidates = self._grid.query(test_left, test_top, test_right, test_bottom, exclude=collider)

        for other in candidates:
            # Layer/mask filtering
            if other.layer not in collider.mask:
                continue

            # Triggers don't block movement
            if other.is_trigger:
                continue

            # Other collider bounds (float from cache)
            other_rect = self._cached_rects.get(other)
            if not other_rect:
                continue
            
            other_left, other_top, other_right, other_bottom = other_rect

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

    def query_overlap(self, collider, test_x, test_y):
        """
        Public query: test if a collider at (test_x, test_y) overlaps
        any non-trigger collider visible via layer/mask.

        This is the public API for ground-checks, proximity tests, etc.
        Games should use this instead of accessing _cached_colliders directly.

        Returns: CollisionResult (the shallowest penetration found)
        """
        return self.check_collision(collider, test_x, test_y)
        
    def query_overlap_all(self, collider, test_x, test_y):
        """
        Public query: test if a collider at (test_x, test_y) overlaps
        any non-trigger collider visible via layer/mask.
        Returns ALL overlaps, instead of just the nearest.

        Returns: list of CollisionResult
        """
        current_parent_gx, current_parent_gy = 0.0, 0.0
        if collider.parent:
            current_parent_gx, current_parent_gy = collider.parent.get_global_position()

        move_dx = test_x - current_parent_gx
        move_dy = test_y - current_parent_gy

        sw = collider.width * collider.scale_x
        sh = collider.height * collider.scale_y
        
        if hasattr(collider, 'radius'):
            rx = collider.radius * collider.scale_x
            ry = collider.radius * collider.scale_y
            test_left = current_parent_gx + move_dx + collider.local_x - rx
            test_top = current_parent_gy + move_dy + collider.local_y - ry
        else:
            test_left = current_parent_gx + move_dx + collider.local_x
            test_top = current_parent_gy + move_dy + collider.local_y
            
        test_right = test_left + sw
        test_bottom = test_top + sh

        results = []

        # Use spatial grid for candidates
        candidates = self._grid.query(test_left, test_top, test_right, test_bottom, exclude=collider)

        for other in candidates:
            if other.layer not in collider.mask or other.is_trigger:
                continue

            other_rect = self._cached_rects.get(other)
            if not other_rect:
                continue
            
            other_left, other_top, other_right, other_bottom = other_rect

            if (test_left >= other_right or test_right <= other_left or
                    test_top >= other_bottom or test_bottom <= other_top):
                continue

            # Determine narrow-phase
            is_self_circle = hasattr(collider, 'radius')
            is_other_circle = hasattr(other, 'radius')
            
            pen = 0.0
            nx, ny = 0.0, 0.0
            
            if is_self_circle and is_other_circle:
                # Circle vs Circle exact overlap
                cx1 = test_left + (sw / 2.0)
                cy1 = test_top + (sh / 2.0)
                
                other_w = other.width * other.scale_x
                other_h = other.height * other.scale_y
                cx2 = other_left + (other_w / 2.0)
                cy2 = other_top + (other_h / 2.0)
                
                dx = cx1 - cx2
                dy = cy1 - cy2
                dist = math.hypot(dx, dy)
                r = (collider.radius * collider.scale_x) + (other.radius * other.scale_x)
                
                if dist >= r or dist == 0.0:
                    continue
                    
                pen = r - dist
                nx = dx / dist
                ny = dy / dist
                
            else:
                # Standard AABB MTV
                overlap_left = test_right - other_left
                overlap_right = other_right - test_left
                overlap_top = test_bottom - other_top
                overlap_bottom = other_bottom - test_top
    
                if overlap_left < overlap_right:
                    pen_x, normal_x = overlap_left, -1.0
                else:
                    pen_x, normal_x = overlap_right, 1.0
    
                if overlap_top < overlap_bottom:
                    pen_y, normal_y = overlap_top, -1.0
                else:
                    pen_y, normal_y = overlap_bottom, 1.0
    
                if pen_x < pen_y:
                    pen, nx, ny = pen_x, normal_x, 0.0
                else:
                    pen, nx, ny = pen_y, 0.0, normal_y

            results.append(CollisionResult(
                collided=True, collider=other, normal_x=nx, normal_y=ny, penetration=pen
            ))

        return results

    def query_rect(self, test_left, test_top, test_right, test_bottom, masks=None, exclude=None):
        """Public API: test if any cached collider overlaps the given float rect."""
        results = []

        # Use spatial grid for candidates
        candidates = self._grid.query(test_left, test_top, test_right, test_bottom)

        for col in candidates:
            if exclude and col is exclude:
                continue
            if col.is_trigger:
                continue
            if masks and col.layer not in masks:
                continue
            rect = self._cached_rects.get(col)
            if not rect:
                continue
            
            ol, ot, oright, ob = rect
            if not (test_left >= oright or test_right <= ol or test_top >= ob or test_bottom <= ot):
                results.append(col)
        return results

    def get_collider_count(self):
        """Returns the number of active colliders in the cache."""
        return len(self._cached_colliders)

    # ------------------------------------------------------------------
    # SAT Geometry Helpers
    # ------------------------------------------------------------------

    def _sat_poly_poly(self, pts_a, pts_b):
        """Check SAT narrowphase between two convex polygons. Returns (collided, normal, depth)."""
        overlap = float('inf')
        smallest_axis = (0, 0)

        edges = []
        for i in range(len(pts_a)):
            p1 = pts_a[i]
            p2 = pts_a[(i + 1) % len(pts_a)]
            edges.append((p2[0] - p1[0], p2[1] - p1[1]))
            
        for i in range(len(pts_b)):
            p1 = pts_b[i]
            p2 = pts_b[(i + 1) % len(pts_b)]
            edges.append((p2[0] - p1[0], p2[1] - p1[1]))

        for edge in edges:
            axis = (-edge[1], edge[0])  # Perpendicular normal
            l = math.sqrt(axis[0]**2 + axis[1]**2)
            if l == 0: continue
            axis = (axis[0]/l, axis[1]/l)

            # Project poly A
            min_a, max_a = float('inf'), float('-inf')
            for p in pts_a:
                proj = p[0]*axis[0] + p[1]*axis[1]
                min_a = min(min_a, proj)
                max_a = max(max_a, proj)
                
            # Project poly B
            min_b, max_b = float('inf'), float('-inf')
            for p in pts_b:
                proj = p[0]*axis[0] + p[1]*axis[1]
                min_b = min(min_b, proj)
                max_b = max(max_b, proj)

            # Check gap
            if max_a < min_b or max_b < min_a:
                return False, (0, 0), 0

            # Calculate overlap depth
            axis_depth = min(max_a - min_b, max_b - min_a)
            if axis_depth < overlap:
                overlap = axis_depth
                smallest_axis = axis

        return True, smallest_axis, overlap

    def _sat_poly_circle(self, pts_poly, cx, cy, radius):
        """Check SAT narrowphase between convex polygon and circle."""
        overlap = float('inf')
        smallest_axis = (0, 0)
        
        edges = []
        closest_vertex = None
        min_dist_sq = float('inf')
        
        for i in range(len(pts_poly)):
            p1 = pts_poly[i]
            p2 = pts_poly[(i + 1) % len(pts_poly)]
            edges.append((p2[0] - p1[0], p2[1] - p1[1]))
            
            ds = (p1[0] - cx)**2 + (p1[1] - cy)**2
            if ds < min_dist_sq:
                min_dist_sq = ds
                closest_vertex = p1
                
        # The axis connecting circle center to closest vertex is a potential separating axis
        if closest_vertex:
            v_axis = (closest_vertex[0] - cx, closest_vertex[1] - cy)
            edges.append((-v_axis[1], v_axis[0])) # Convert back to edge format to be pushed to normal
        
        for edge in edges:
            axis = (-edge[1], edge[0])
            l = math.sqrt(axis[0]**2 + axis[1]**2)
            if l == 0: continue
            axis = (axis[0]/l, axis[1]/l)
            
            # Project Poly
            min_a, max_a = float('inf'), float('-inf')
            for p in pts_poly:
                proj = p[0]*axis[0] + p[1]*axis[1]
                min_a = min(min_a, proj)
                max_a = max(max_a, proj)
                
            # Project Circle
            proj_c = cx*axis[0] + cy*axis[1]
            min_b = proj_c - radius
            max_b = proj_c + radius
            
            if max_a < min_b or max_b < min_a:
                return False, (0, 0), 0
                
            axis_depth = min(max_a - min_b, max_b - min_a)
            if axis_depth < overlap:
                overlap = axis_depth
                smallest_axis = axis
                
        return True, smallest_axis, overlap

    # ------------------------------------------------------------------
    # Broad-phase pair detection (enter / stay / exit events)
    # ------------------------------------------------------------------

    def process_collisions(self):
        """Call once per frame to emit collision enter/stay/exit events."""
        current = set()
        checked_pairs = set()

        for a in self._cached_colliders:
            rect_a = self._cached_rects.get(a)
            if not rect_a:
                continue

            # Query spatial grid for potential partners near a
            la, ta, ra, ba = rect_a
            EPS = 0.5
            nearby = self._grid.query(la - EPS, ta - EPS, ra + EPS, ba + EPS, exclude=a)

            for b in nearby:
                # Ensure each pair is checked only once
                pair = tuple(sorted((a, b), key=id))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                a_sees_b = b.layer in a.mask
                b_sees_a = a.layer in b.mask

                if not a_sees_b and not b_sees_a:
                    continue

                rect_b = self._cached_rects.get(b)
                if not rect_b:
                    continue

                lb, tb, rb, bb = rect_b

                # Standard AABB broad-phase overlap check
                broadphase_hit = (la < rb + EPS and ra > lb - EPS and ta < bb + EPS and ba > tb - EPS)
                
                if broadphase_hit:
                    # Narrow-phase circle collision
                    is_a_circle = hasattr(a, 'radius')
                    is_b_circle = hasattr(b, 'radius')
                    is_a_poly = isinstance(a, PolygonCollider2D)
                    is_b_poly = isinstance(b, PolygonCollider2D)
                    
                    narrow_hit = True
                    
                    if is_a_poly or is_b_poly:
                        # Convert AABBs to polygons if needed for SAT verification
                        def _get_pts(col, rect):
                            if isinstance(col, PolygonCollider2D):
                                return col.get_global_points()
                            # AABB to pts
                            l, t, r, b = rect
                            return [(l, t), (r, t), (r, b), (l, b)]
                            
                        # Handle Poly vs Circle
                        if is_a_circle or is_b_circle:
                            circle = a if is_a_circle else b
                            poly = b if is_a_circle else a
                            cx, cy = circle.get_global_position()
                            r = circle.radius * circle.scale_x
                            pts = poly.get_global_points() if isinstance(poly, PolygonCollider2D) else _get_pts(poly, rect_a if poly is a else rect_b)
                            narrow_hit, _, _ = self._sat_poly_circle(pts, cx, cy, r)
                        else:
                            # Poly vs Poly/AABB
                            pts_a = _get_pts(a, rect_a)
                            pts_b = _get_pts(b, rect_b)
                            narrow_hit, _, _ = self._sat_poly_poly(pts_a, pts_b)

                    elif is_a_circle and is_b_circle:
                        # Circle-Circle
                        dx = a.get_global_position()[0] - b.get_global_position()[0]
                        dy = a.get_global_position()[1] - b.get_global_position()[1]
                        r = (a.radius * a.scale_x) + (b.radius * b.scale_x)
                        narrow_hit = (dx*dx + dy*dy) <= (r*r)
                    elif is_a_circle or is_b_circle:
                        # Circle-AABB
                        circle, rect_col = (a, b) if is_a_circle else (b, a)
                        cx_pos, cy_pos = circle.get_global_position()
                        r = circle.radius * circle.scale_x
                        rl, rt, rr, rb_edge = (la, ta, ra, ba) if circle is b else (lb, tb, rb, bb)
                        
                        closest_x = max(rl, min(cx_pos, rr))
                        closest_y = max(rt, min(cy_pos, rb_edge))
                        dx = cx_pos - closest_x
                        dy = cy_pos - closest_y
                        narrow_hit = (dx*dx + dy*dy) <= (r*r)

                    if narrow_hit:
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

    # ------------------------------------------------------------------
    # Raycasting
    # ------------------------------------------------------------------

    def raycast(self, x1, y1, x2, y2, mask=None):
        """
        Casts a ray from (x1, y1) to (x2, y2).
        Returns (hit: bool, hit_x: float, hit_y: float, collider)
        Finds the closest intersection with AABBs.
        mask is a set of layer strings to hit. If None, hits everything except triggers.
        """
        closest_hit = None
        closest_dist = float('inf')
        hit_x = x2
        hit_y = y2

        # Build the ray AABB for spatial grid query
        ray_l = min(x1, x2)
        ray_t = min(y1, y2)
        ray_r = max(x1, x2)
        ray_b = max(y1, y2)
        candidates = self._grid.query(ray_l, ray_t, ray_r, ray_b)

        for col in candidates:
            if mask is not None and col.layer not in mask:
                continue
            if col.is_trigger:
                continue

            rect = self._cached_rects.get(col)
            if not rect:
                continue
                
            l, t, r, b = rect
            
            # 4 edges of the AABB
            edges = [
                ((l, t), (r, t)), # top
                ((r, t), (r, b)), # right
                ((r, b), (l, b)), # bottom
                ((l, b), (l, t))  # left
            ]
            
            for (p3x, p3y), (p4x, p4y) in edges:
                den = (x1 - x2) * (p3y - p4y) - (y1 - y2) * (p3x - p4x)
                if den == 0: 
                    continue
                    
                t_val = ((x1 - p3x) * (p3y - p4y) - (y1 - p3y) * (p3x - p4x)) / den
                u_val = -((x1 - x2) * (y1 - p3y) - (y1 - y2) * (x1 - p3x)) / den
                
                if 0 <= t_val <= 1 and 0 <= u_val <= 1:
                    hx = x1 + t_val * (x2 - x1)
                    hy = y1 + t_val * (y2 - y1)
                    dist = (hx - x1)**2 + (hy - y1)**2
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_hit = col
                        hit_x = hx
                        hit_y = hy
                        
        return (closest_hit is not None, hit_x, hit_y, closest_hit)
