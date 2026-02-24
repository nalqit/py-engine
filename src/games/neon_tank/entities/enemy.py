import math
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.core.engine import Engine

class Enemy(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.move_speed = 100.0
        
        # Enemy Visual
        self.vis = RectangleNode(name + "_Vis", -15, -15, 30, 30, (255, 50, 50)) # Red Neon
        self.add_child(self.vis)
        
        self.health = 1

    def update(self, delta):
        # 1. Simple AI: Move towards player
        player = self._find_player()
        if player:
            px, py = player.get_global_position()
            ex, ey = self.get_global_position()
            
            angle = math.atan2(py - ey, px - ex)
            self.velocity_x = math.cos(angle) * self.move_speed
            self.velocity_y = math.sin(angle) * self.move_speed
            
            # Rotate visual towards movement direction
            # self.vis.rotation = angle # Optional
        
        # 2. Integrate Physics
        super().update(delta)

    def _find_player(self):
        # Look for the Player node in the scene tree
        root = self
        while root.parent:
            root = root.parent
        
        # Search for a node named "Player"
        return self._search_node(root, "Player")

    def _search_node(self, current, name):
        if current.name == name:
            return current
        for child in current.children:
            found = self._search_node(child, name)
            if found:
                return found
        return None

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        if self.parent:
            self.parent.remove_child(self)
        print(f"Enemy {self.name} defeated!")

    def on_collision_enter(self, other):
        # Handle collision with bullet
        # The collision logic usually passes the other collider
        pass
