from src.pyengine2D import PhysicsBody2D,RectangleNode

class Enemy(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world, move_dist=200):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.gravity = 1500.0
        
        self.move_speed = 100.0
        self.direction = 1
        self.start_x = x
        self.move_dist = move_dist
        
        self.pushable = False
        
        # Red rectangle
        self.vis = RectangleNode(f"{name}_Vis", collider.local_x, collider.local_y,
                                 collider.width, collider.height, (255, 50, 50))
        self.add_child(self.vis)
        
        self.is_dead = False

    def update(self, delta):
        if self.is_dead:
            return
            
        if self.local_x > self.start_x + self.move_dist:
            self.direction = -1
        elif self.local_x < self.start_x:
            self.direction = 1
            
        self.velocity_x = self.move_speed * self.direction
        super().update(delta)

        # Basic horizontal wall collision reversal
        if self.velocity_x == 0:
            self.direction *= -1

    def on_collision_enter(self, other):
        if self.is_dead:
            return
            
        body = other.parent
        if body and body.name == "Player":
            # Check stomp vs touch
            if hasattr(body, "velocity_y") and body.velocity_y > 0 and body.get_global_position()[1] < self.get_global_position()[1]:
                self.die(body)
            else:
                if hasattr(body, "die"):
                    body.die()

    def die(self, player=None):
        self.is_dead = True
        if player:
            player.velocity_y = -600  # bounce
            player.add_score(50)
        if self.parent:
            self.parent.remove_child(self)
