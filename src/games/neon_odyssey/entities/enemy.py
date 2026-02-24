from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.scene.rectangle_node import RectangleNode

class Enemy(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world, move_dist=200):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.gravity = 1500.0
        
        self.move_speed = 100.0
        self.direction = 1
        self.start_x = x
        self.move_dist = move_dist
        
        # We can't be pushed
        self.pushable = False
        
        # Visuals
        self.vis = RectangleNode(f"{name}_Vis", collider.local_x, collider.local_y,
                                 collider.width, collider.height, (255, 50, 50))
        self.add_child(self.vis)

    def update(self, delta):
        # Prevent falling off dynamically if we wanted to, but for simple patrol:
        if self.local_x > self.start_x + self.move_dist:
            self.direction = -1
        elif self.local_x < self.start_x:
            self.direction = 1
            
        self.velocity_x = self.move_speed * self.direction
        super().update(delta)

    def on_collision_enter(self, other):
        body = other.parent
        # The enemy's own mask doesn't need to specifically hunt the player,
        # but if the player bumps into us or we bump into them, 
        # CollisionWorld sends this event using the engine hook.
        if body and body.name == "Player":
            # Direct hit
            if hasattr(body, "take_damage"):
                body.take_damage(1)
