from src.pyengine2D import Node2D,Collider2D,RectangleNode

class LevelManager(Node2D):
    def __init__(self, name, collision_world):
        super().__init__(name, 0, 0)
        self.collision_world = collision_world
        self.build_geometry()

    def build_geometry(self):
        # 1. Main Floor
        self.create_solid("Floor", -500, 500, 3000, 200, (50, 50, 50))
        
        # 2. Starting Stairs
        self.create_solid("Stair1", 300, 450, 100, 50, (60, 80, 70))
        self.create_solid("Stair2", 400, 400, 100, 100, (60, 80, 70))
        self.create_solid("Stair3", 500, 350, 100, 150, (60, 80, 70))
        
        # 3. Pit Challenge
        self.create_solid("Blocker", 800, 0, 50, 600, (80, 40, 40)) # Tall wall
        self.create_solid("Plat1", 850, 300, 150, 20, (100, 150, 200)) # Floating plat
        
        # 4. Arena area
        self.create_solid("ArenaFloor", 1200, 500, 800, 200, (50, 50, 50))
        
        # 5. Wall at end
        self.create_solid("EndWall", 2000, -200, 200, 900, (50, 50, 50))

    def create_solid(self, name, x, y, w, h, color):
        wall = Node2D(name, x, y)
        self.add_child(wall)
        
        col = Collider2D(name + "_Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player", "box", "enemy"}
        wall.add_child(col)
        
        vis = RectangleNode(name + "_Vis", 0, 0, w, h, color)
        wall.add_child(vis)
