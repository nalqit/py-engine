from src.engine.core.engine import Engine
from src.engine.scene.node2d import Node2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.collision.collider2d import Collider2D
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.ui.stats_hud import StatsHUD
from src.engine.scene.sprite_node import SpriteNode

def main():
    # Initialize Engine (800x600 virtual resolution)
    engine = Engine("Neon Tank Arena", 800, 600)
    
    # Root Node
    root = Node2D("Root")
    
    # Collision World
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)
    
    # Arena Node (container for walls and floor)
    arena = Node2D("Arena")
    root.add_child(arena)
    
    # Floor (Dark colored background)
    floor = RectangleNode("Floor", -1000, -1000, 2000, 2000, (20, 20, 30))
    arena.add_child(floor)
    
    # Arena Walls
    def create_wall(name, x, y, w, h):
        wall = Node2D(name, x, y)
        arena.add_child(wall)
        
        # Physics Collider
        col = Collider2D(name + "_Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player", "enemy", "bullet"}
        wall.add_child(col)
        
        # Neon Wall Visual
        wall.add_child(RectangleNode(name + "_Vis", 0, 0, w, h, (0, 255, 255))) # Cyan Neon
        return wall

    # Boundary Walls (Top, Bottom, Left, Right)
    create_wall("Wall_Top", -500, -500, 1000, 20)
    create_wall("Wall_Bottom", -500, 500, 1000, 20)
    create_wall("Wall_Left", -500, -500, 20, 1000)
    create_wall("Wall_Right", 480, -500, 20, 1000)
    
    # Player Tank
    player_col = Collider2D("Player_Col", -20, -20, 40, 40)
    player_col.layer = "player"
    player_col.mask = {"wall", "enemy"}
    spirit = SpriteNode("Spirit",  "src/games/neon_tank/spaceship1.jpg",-20, -20,)
    
    from .entities.tank import PlayerTank
    player = PlayerTank("Player", 0, 0, player_col, collision_world)
    player.add_child(player_col)
    arena.add_child(player)
    spirit.width = 40
    spirit.height = 40
    player.add_child(spirit)
    # Spawner
    from .entities.spawner import Spawner
    spawner = Spawner("Spawner", collision_world)
    arena.add_child(spawner)
    
    # Camera
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = camera # Set as global camera
    
    # HUD
    hud = StatsHUD("HUD")
    root.add_child(hud)
    
    # Collision Callbacks Logic
    def on_fixed_update(eng, scene_root, fixed_dt):
        # We can handle bullet-enemy collisions here if the engine doesn't automate it via signals
        # For simplicity in this demo, let's check for bullet overlaps manually or rely on signals if available.
        
        # Collect all bullets and enemies
        bullets = []
        enemies = []
        
        from .entities.enemy import Enemy
        from .entities.bullet import Bullet

        def collect_entities(node):
            if isinstance(node, Bullet):
                bullets.append(node)
            elif isinstance(node, Enemy):
                enemies.append(node)
            for child in node.children:
                collect_entities(child)
        
        collect_entities(arena)
        
        for bullet in bullets:
            for enemy in enemies:
                # Basic distance check for collision (simplification)
                bx, by = bullet.get_global_position()
                ex, ey = enemy.get_global_position()
                dist = ((bx - ex)**2 + (by - ey)**2)**0.5
                if dist < 30: # Collision radius
                    enemy.take_damage(1)
                    bullet.destroy()
                    break

        # Check player-enemy collision
        px, py = player.get_global_position()
        for enemy in enemies:
            ex, ey = enemy.get_global_position()
            dist = ((px - ex)**2 + (py - ey)**2)**0.5
            if dist < 40:
                print("Game Over! Restarting...")
                player.local_x = 0
                player.local_y = 0
                # Clear enemies
                for e in enemies:
                    if e.parent:
                        e.parent.remove_child(e)
                break
    root.print_tree()
    print(root.get_screen_position())
    print("Neon Tank Arena Initialized.")
    engine.run(root, on_fixed_update=on_fixed_update)
    
if __name__ == "__main__":
    main()
