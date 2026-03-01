from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.collision.collider2d import Collider2D
from src.pyengine2D.physics.physics_body_2d import PhysicsBody2D

class RigidBody2D(Node2D):
    """
    Advanced Physics Body for sub-stepped physics simulation.
    Seamlessly integrates with PyEngine 2D CollisionWorld.
    Supports mass, restitution, continuous integration, and kinematic modes.
    """
    def __init__(self, name, x=0, y=0, collider: Collider2D = None, collision_world=None, mass=1.0, is_kinematic=False):
        super().__init__(name, x, y)
        self.collider = collider
        self.collision_world = collision_world
        
        self.mass = mass
        self.inv_mass = 0.0 if mass == 0.0 or is_kinematic else 1.0 / mass
        
        self.vx = 0.0
        self.vy = 0.0
        
        self.force_x = 0.0
        self.force_y = 0.0
        
        self.restitution = 1.0  # Perfectly elastic default
        
        self.use_gravity = True
        self.gravity_scale = 1.0
        self.is_kinematic = is_kinematic

    def apply_force(self, fx, fy):
        if self.is_kinematic: return
        self.force_x += fx
        self.force_y += fy
        
    def clear_forces(self):
        self.force_x = 0.0
        self.force_y = 0.0

    def solve_collisions(self, sdt, processed_pairs):
        """
        Queries the central CollisionWorld for overlaps and applies elastic 
        momentum transfer or positional hard-stops against other colliders.
        """
        if not self.collider or not self.collision_world:
            return

        pgx, pgy = 0.0, 0.0
        if self.parent and isinstance(self.parent, Node2D):
            pgx, pgy = self.parent.get_global_position()

        target_gx = pgx + self.local_x
        target_gy = pgy + self.local_y

        # FORCE CACHE UPDATE FOR SUB-STEPPING
        # Because we are sub-stepping inside a single engine frame, the collision 
        # world's grid/rect cache for this object is stale. We must update it!
        if self.collider in self.collision_world._cached_colliders:
            rect = self.collider.get_rect()
            if isinstance(rect, tuple):
                self.collision_world._cached_rects[self.collider] = rect
            else:
                self.collision_world._cached_rects[self.collider] = (rect.left, rect.top, rect.right, rect.bottom)
                
            # Note: We don't theoretically need to rebuild the entire UniformGrid, 
            # because query_overlap_all creates a hypothetical test_rect anyway.
            # We just need the _cached_rects to be accurate for bounding boxes.

        # Query central engine CollisionWorld for ALL overlaps at current position
        results = self.collision_world.query_overlap_all(self.collider, target_gx, target_gy)
        
        # Accumulators for simultaneous multi-body resolution
        total_dx = 0.0
        total_dy = 0.0
        total_dvx = 0.0
        total_dvy = 0.0
        
        # We need to apply these to the hit bodies as well
        hit_applications = [] # (hit_body, dx, dy, dvx, dvy)

        for result in results:
            hit_col = result.collider
            hit_body = hit_col.parent
            
            # Prevent double-processing (A hits B, then B hits A in the same pass)
            if hit_body:
                pair = tuple(sorted((id(self), id(hit_body))))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
            
            nx = result.normal_x
            ny = result.normal_y
            pen = result.penetration
            
            w1 = self.inv_mass
            w2 = 0.0 # Default infinite mass for non-rigid bodies
            
            hit_is_rigid = isinstance(hit_body, RigidBody2D)
            hit_is_physics = isinstance(hit_body, PhysicsBody2D)
            
            if hit_is_rigid:
                w2 = hit_body.inv_mass
                
            sum_w = w1 + w2
            if sum_w == 0.0: continue
            
            w1_ratio = w1 / sum_w
            w2_ratio = w2 / sum_w

            # Positional correction - MUST be 1.0 to fully separate objects, otherwise they overlap next frame and bleed momentum
            relax = 1.0
            total_dx += nx * (pen * w1_ratio * relax)
            total_dy += ny * (pen * w1_ratio * relax)
            
            hdx, hdy, hdvx, hdvy = 0.0, 0.0, 0.0, 0.0
            
            if hit_is_rigid and not hit_body.is_kinematic:
                hdx -= nx * (pen * w2_ratio * relax)
                hdy -= ny * (pen * w2_ratio * relax)
                
            # Velocity/Momentum Transfer
            v1n = self.vx * nx + self.vy * ny
            v2n = 0.0
            
            if hit_is_rigid:
                v2n = hit_body.vx * nx + hit_body.vy * ny
            elif hit_is_physics:
                # PhysicsBody2D isn't built for momentum transfer, but we can treat its velocity as immovable
                v2n = hit_body.velocity_x * nx + hit_body.velocity_y * ny
                
            rel_v = v1n - v2n
            if rel_v < 0:  # Converging
                # Calculate combined restitution
                e = self.restitution
                if hit_is_rigid:
                    e *= hit_body.restitution
                else:
                    e *= 0.5 # Default bounce against static walls
                    
                j_impulse = -(1.0 + e) * rel_v / sum_w
                
                # Apply the impulse vector scaled by each body's inverse mass
                total_dvx += j_impulse * w1 * nx
                total_dvy += j_impulse * w1 * ny
                
                if hit_is_rigid and not hit_body.is_kinematic:
                    hdvx -= j_impulse * w2 * nx
                    hdvy -= j_impulse * w2 * ny
                    
            if hit_is_rigid and not hit_body.is_kinematic:
                hit_applications.append((hit_body, hdx, hdy, hdvx, hdvy))
                
        # Apply accumulated changes simultaneously
        self.local_x += total_dx
        self.local_y += total_dy
        self.vx += total_dvx
        self.vy += total_dvy
        
        for hb, hx, hy, hvx, hvy in hit_applications:
            hb.local_x += hx
            hb.local_y += hy
            hb.vx += hvx
            hb.vy += hvy
