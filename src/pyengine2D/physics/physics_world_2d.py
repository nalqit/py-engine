from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.physics.rigid_body_2d import RigidBody2D
from src.pyengine2D.physics.distance_constraint import DistanceConstraint

class PhysicsWorld2D(Node2D):
    """
    Acts solely as a sub-stepper scheduling Node for RigidBody2Ds and Constraints.
    Passes execution to the bodies to query the central CollisionWorld natively.

    Performance notes:
        - CollisionWorld._refresh_collider_cache() and _refresh_rect_cache()
          run ONCE per frame inside CollisionWorld.update(), which the scene
          tree calls before PhysicsWorld2D.update().  We do NOT repeat that
          expensive walk here.  Inside substeps, each RigidBody2D.solve_collisions()
          patches its own _cached_rects entry (lightweight O(1) per body).
        - update_transforms() is called ONCE at the end of each substep
          (after integration + collision solve + constraints) to keep the
          dirty-transform cache synchronised for the next substep.
    """
    def __init__(self, name="PhysicsWorld2D", gravity_y=800.0, sub_steps=4):
        super().__init__(name)
        self.gravity_y = gravity_y
        self.sub_steps = sub_steps

        self.bodies = []
        self.constraints = []

        from src.pyengine2D.physics.spatial_hash import SpatialHash
        self.spatial_hash = SpatialHash(cell_size=128)

    def update(self, delta):
        # --- Per-frame setup (runs once, NOT per substep) ---
        self.bodies.clear()
        self.constraints.clear()

        for child in self.children:
            if isinstance(child, RigidBody2D):
                self.bodies.append(child)
                self.spatial_hash.register(child)
            elif isinstance(child, DistanceConstraint):
                self.constraints.append(child)

        sdt = delta / max(1, self.sub_steps)

        for _ in range(self.sub_steps):

            # 1. Integrate Forces & Gravity
            for b in self.bodies:
                if b.is_kinematic: continue

                if b.use_gravity:
                    b.vy += self.gravity_y * b.gravity_scale * sdt

                b.vx += (b.force_x * b.inv_mass) * sdt
                b.vy += (b.force_y * b.inv_mass) * sdt

                b.local_x += b.vx * sdt
                b.local_y += b.vy * sdt

                b.clear_forces()

            # Sync transforms & spatial hash ONCE after all bodies moved
            for b in self.bodies:
                b.update_transforms()
                self.spatial_hash.register(b)

            # 2. Constraints (Ropes, Springs, Joints)
            for c in self.constraints:
                c.solve()

            # 3. Collision Solving using engine CollisionWorld + Spatial Hash
            processed_pairs = set()
            for b in self.bodies:
                if not b.is_kinematic:
                    candidates = self.spatial_hash.query_nearby(b)
                    b.solve_collisions(sdt, processed_pairs, spatial_hash_candidates=candidates)

            # 4. Re-solve constraints to ensure lengths aren't stretched
            for c in self.constraints:
                c.solve()

            # 5. Single end-of-substep transform sync
            for b in self.bodies:
                b.update_transforms()

        super().update(delta)

