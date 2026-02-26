from src.pyengine2D import PhysicsBody2D,RectangleNode

class Box(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.gravity = 1500.0
        
        # Pushing settings
        self.pushable = True
        self.push_weight = 1.0

        # Visuals
        # Notice we use the collider's dimensions.
        self.vis = RectangleNode(f"{name}_Vis", collider.local_x, collider.local_y, 
                                 collider.width, collider.height, (200, 130, 50))
        self.add_child(self.vis)
