import random
from src.engine.core.engine import Engine
from src.engine.scene.node2d import Node2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.collision.collider2d import Collider2D
from src.engine.scene.camera2d import Camera2D

# Neon Odyssey: PyEngine Showcase Demo
# This logic serves to initialize the engine and the core scene hierarchy.
# Developer Guide Note: This is an example of Step 1 and 2 from the Guide.

class NeonOdyssey:
    def __init__(self):
        # 1. Initialize the Engine
        self.engine = Engine("Neon Odyssey", 1024, 600)
        
        # 2. Setup the Scene Root
        self.root = Node2D("Root")
        
        # 3. Setup the Collision System
        self.collision_world = CollisionWorld("CollisionWorld")
        self.root.add_child(self.collision_world)
        
        # 4. Setup the Game World Node (everything level-related goes here)
        self.world = Node2D("World")
        self.root.add_child(self.world)
        
        # 5. Build Environment (Level & Background)
        from .level import LevelManager
        self.level = LevelManager("Level", self.collision_world)
        self.world.add_child(self.level)
        
        # 6. Build Entities: Player
        from .entities.player import Player
        player_col = Collider2D("Player_Col", -20, -20, 40, 40)
        player_col.layer = "player"
        player_col.mask = {"wall", "pickup", "box", "enemy"}
        
        self.player = Player("Player", -300, 300, player_col, self.collision_world)
        self.player.add_child(player_col)
        self.player.pushable = True
        
        self.world.add_child(self.player)
        
        # 7. Add moving Platforms
        from .entities.moving_platform import MovingPlatform
        plat_up = MovingPlatform("Elevator", 1000, 300, 100, 20, 0, -300, 2.5, self.collision_world)
        self.world.add_child(plat_up)
        
        plat_side = MovingPlatform("Ferry", 1200, 0, 150, 20, 300, 0, 3.0, self.collision_world)
        self.world.add_child(plat_side)
        
        # 7.5 Add pushable boxes and enemies
        from .entities.box import Box
        box_col = Collider2D("BoxCol1", 0, 0, 40, 40)
        box_col.layer = "box"
        box_col.mask = {"wall", "box"}
        box1 = Box("Box1", -50, 450, box_col, self.collision_world)
        box1.add_child(box_col)
        self.world.add_child(box1)

        box_col2 = Collider2D("BoxCol2", 0, 0, 40, 40)
        box_col2.layer = "box"
        box_col2.mask = {"wall", "box"}
        box2 = Box("Box2", 0, 450, box_col2, self.collision_world)
        box2.add_child(box_col2)
        self.world.add_child(box2)
        
        from .entities.enemy import Enemy
        ene_col = Collider2D("EnemyCol1", -20, -20, 40, 40)
        ene_col.layer = "enemy"
        ene_col.mask = {"wall", "player", "box"}
        enemy1 = Enemy("Bot1", 100, 450, ene_col, self.collision_world, move_dist=200)
        enemy1.add_child(ene_col)
        enemy1.can_push = True
        self.world.add_child(enemy1)
        
        # 8. Add Collectibles (Area2D)
        from .entities.collectible import Collectible
        self.spawns = [
            (-100, 300), (350, 200), (650, 100), (1050, 0), (1350, -50), (1600, -50)
        ]
        
        # 9. Setup UI and Signals
        from .ui.hud import HUD
        self.hud = HUD("HUD")
        # Give HUD starting values
        self.hud.health = self.player.health 
        self.root.add_child(self.hud)
        
        # Connect Player signals to HUD Observer
        self.player.get_signal("on_health_changed").connect(self.hud.on_player_health_changed)
        self.player.get_signal("on_died").connect(self.hud.on_player_died)
        
        # Spawn collectibles and connect signals
        self._spawn_gems()

        # 10. Setup the Camera
        self.camera = Camera2D("Camera")
        self.camera.follow(self.player)
        self.root.add_child(self.camera)
        Node2D.camera = self.camera # Global camera reference for rendering
        
    def _spawn_gems(self):
        from .entities.collectible import Collectible
        for i, (gx, gy) in enumerate(self.spawns):
            gem = Collectible(f"Gem_{i}", gx, gy, self.collision_world)
            # Connect Observer
            gem.get_signal("on_collected").connect(self.hud.on_score_added)
            self.world.add_child(gem)

    def update(self, engine, root, dt):
        """Called every fixed physics step."""
        # Simple win condition reset
        if self.hud.score >= len(self.spawns) * 50:
            print("YOU WIN! Resetting...")
            self.hud.score = 0
            self.player.reset_position()
            # In a real game we would respawn gems, but this is just a reset.
        
    def render(self, engine, root, surface):
        """Called every frame for screen-space rendering (like UI)."""
        pass

    def run(self):
        """Start the main game loop."""
        self.engine.run(self.root, on_fixed_update=self.update, on_render=self.render)

def main():
    game = NeonOdyssey()
    game.run()

if __name__ == "__main__":
    main()
