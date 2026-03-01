from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.physics.rigid_body_2d import RigidBody2D
from src.pyengine2D.physics.distance_constraint import DistanceConstraint

class PhysicsWorld2D(Node2D):
    """
    Acts solely as a sub-stepper scheduling Node for RigidBody2Ds and Constraints.
    Passes execution to the bodies to query the central CollisionWorld natively.
    """
    def __init__(self, name="PhysicsWorld2D", gravity_y=800.0, sub_steps=10):
        super().__init__(name)
        self.gravity_y = gravity_y
        self.sub_steps = sub_steps
        
        self.bodies = []
        self.constraints = []

    def update(self, delta):
        self.bodies.clear()
        self.constraints.clear()
        
        for child in self.children:
            if isinstance(child, RigidBody2D):
                self.bodies.append(child)
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
                b.update_transforms() # Important for CollisionWorld sync
                
            # 2. Constraints (Ropes, Springs, Joints)
            for c in self.constraints:
                c.solve()

            # 2. Native Collision Solving using engine CollisionWorld
            processed_pairs = set()
            for b in self.bodies:
                if not b.is_kinematic:
                    b.solve_collisions(sdt, processed_pairs)

            for b in self.bodies:
                b.update_transforms()
                                
            # 3. Resolve constraints again to ensure lengths aren't stretched
            for c in self.constraints:
                c.solve()
                
            for b in self.bodies:
                b.update_transforms()
                
        super().update(delta)
