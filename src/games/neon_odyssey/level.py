from src.engine import (
    Node2D, ParallaxBackground, ParallaxLayer, RectangleNode, Collider2D
)

# Neon Odyssey: Level Generation
# This module demonstrates how to build static geometry and Parallax Backgrounds.

class LevelManager(Node2D):
    def __init__(self, name, collision_world):
        super().__init__(name)
        self.collision_world = collision_world
        
        self.build_background()
        self.build_geometry()

    def build_background(self):
        # Developer Guide Note: ParallaxBackground follows the camera and offsets its layers
        pb = ParallaxBackground("Background")
        self.add_child(pb)
        
        # Layer 1: Distant City (Slow moving)
        dist_layer = ParallaxLayer("DistantCity", (0.1, 0.05))
        dist_rect1 = RectangleNode("City1", -500, -300, 2048, 800, (10, 10, 30))
        dist_layer.add_child(dist_rect1)
        pb.add_child(dist_layer)
        
        # Layer 2: Midground Structures (Medium moving)
        mid_layer = ParallaxLayer("Midground", (0.4, 0.2))
        mid_rect1 = RectangleNode("Struct1", 100, -100, 200, 500, (30, 15, 50))
        mid_rect2 = RectangleNode("Struct2", 600, 50, 150, 400, (20, 30, 60))
        mid_layer.add_child(mid_rect1)
        mid_layer.add_child(mid_rect2)
        pb.add_child(mid_layer)

    def build_geometry(self):
        # Developer Guide Note: Static colliders block PhysicsBody2D but don't move.
        
        # Main Floor
        self.create_solid("Floor", -500, 500, 3000, 100, (50, 50, 50))
        
        # Starting Platform
        self.create_solid("Plat1", -100, 350, 300, 20, (50, 200, 100))
        
        # Jump progression
        self.create_solid("Plat2", 350, 250, 150, 20, (50, 200, 100))
        self.create_solid("Plat3", 650, 150, 150, 20, (50, 200, 100))
        
        # High wall
        self.create_solid("Wall1", 900, 0, 50, 500, (40, 40, 40))

    def create_solid(self, name, x, y, w, h, color):
        node = Node2D(name, x, y)
        
        # Visual
        vis = RectangleNode(f"{name}_Vis", 0, 0, w, h, color)
        node.add_child(vis)
        
        # Collider (Notice we don't need a PhysicsBody2D for static walls)
        col = Collider2D(f"{name}_Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        # Since it's static, mask isn't strictly necessary, but good practice
        node.add_child(col)
        
        self.add_child(node)
