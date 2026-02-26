import random
from src.pyengine2D.core.engine import Engine
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.collision.collision_world import CollisionWorld
from src.pyengine2D.collision.collider2d import Collider2D
from src.pyengine2D.scene.camera2d import Camera2D
from src.pyengine2D.scene.rectangle_node import RectangleNode
from src.pyengine2D.ui.stats_hud import StatsHUD

from .entities.player import Player

class NeonHeights:
    def __init__(self):
        self.engine = Engine("Neon Heights", 800, 600)
        self.root = Node2D("Root")
        
        self.collision_world = CollisionWorld("CollisionWorld")
        self.root.add_child(self.collision_world)
        
        self.world = Node2D("World")
        self.root.add_child(self.world)
        
        # Player
        p_col = Collider2D("PlayerCol", -15, -15, 30, 30)
        p_col.layer = "player"
        p_col.mask = {"wall"}
        self.player = Player("Player", 400, 500, p_col, self.collision_world)
        self.player.add_child(p_col)
        self.world.add_child(self.player)
        
        # Camera
        self.camera = Camera2D("Camera")
        self.camera.follow(self.player)
        self.root.add_child(self.camera)
        Node2D.camera = self.camera
        
        # Platforms
        self.platforms = []
        self.next_spawn_y = 400
        self.spawn_interval = 120
        
        # Base floor
        self.create_platform("Floor", 400, 580, 800, 40)
        # Static boundaries
        self.create_platform("LeftWall", 10, 300, 20, 2000)
        self.create_platform("RightWall", 790, 300, 20, 2000)
        
        # HUD
        self.hud = StatsHUD("HUD")
        self.root.add_child(self.hud)
        
        # Hazard: Rising Void
        from .entities.hazard import RisingVoid
        self.void = RisingVoid("Void", -400, 700)
        self.world.add_child(self.void)
        
        self.max_height = 0
        self.game_over = False

    def create_platform(self, name, x, y, w, h):
        plat = Node2D(name, x, y)
        col = Collider2D(name + "_Col", -w/2, -h/2, w, h, is_static=True)
        col.layer = "wall"
        plat.add_child(col)
        
        # Neon highlight color
        color = (100, 100, 200) if "Plat" in name else (80, 80, 100)
        plat.add_child(RectangleNode(name + "_Vis", -w/2, -h/2, w, h, color))
        self.world.add_child(plat)
        self.platforms.append(plat)
        return plat

    def update(self, engine, root, dt):
        if self.game_over:
            return

        # Procedural spawn: Increase window to 1200 for stability
        while self.player.local_y - self.next_spawn_y < 1200:
            px = random.randint(150, 650)
            pw = random.randint(80, 200)
            self.create_platform(f"Plat_{len(self.platforms)}", px, self.next_spawn_y, pw, 20)
            self.next_spawn_y -= self.spawn_interval
            
        # Update walls to follow player height roughly
        left_wall = root.get_node("LeftWall")
        right_wall = root.get_node("RightWall")
        if left_wall: 
            left_wall.local_y = self.player.local_y
            left_wall.update_transforms()
        if right_wall: 
            right_wall.local_y = self.player.local_y
            right_wall.update_transforms()

        # Update score
        current_height = int((-self.player.local_y + 500) / 10)
        if current_height > self.max_height:
            self.max_height = current_height

        # Cleanup platforms far below: Increase window to 1500 to prevent blinking
        for plat in self.platforms[:]:
            if plat.local_y > self.player.local_y + 1500:
                if plat.name not in ["Floor", "LeftWall", "RightWall"]:
                    self.world.remove_child(plat)
                    self.platforms.remove(plat)

        # Dynamic Void Speed: Slower scaling (0.5 instead of 2.0)
        self.void.speed = 80.0 + (self.max_height * 0.5)
        
        # Reset Logic if player falls too far below void
        if self.player.local_y > self.void.local_y + 100:
             print("Fell into the abyss!")
             self.player.reset_position()
             self.void.local_y = self.player.local_y + 200 # Reset relative to player
             self.max_height = 0
             self.next_spawn_y = self.player.local_y - 100

    def render_overlay(self, engine, root, surface):
        renderer = engine.renderer
        renderer.draw_text(surface, f"HEIGHT: {self.max_height}", (255, 255, 255), 350, 10, size=24, bold=True)

    def run(self):
        self.engine.run(self.root, on_fixed_update=self.update, on_render=self.render_overlay)

def main():
    
    game = NeonHeights()
    game.root.print_tree()
    game.run()

if __name__ == "__main__":
    main()
