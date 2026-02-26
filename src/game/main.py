from src.pyengine2D import (
    Engine, Node2D, CollisionWorld, Camera2D, Collider2D
)

def main():
    engine = Engine("PyEngine 2D - Clean Game", 1000, 600)
    
    root = Node2D("Root")
    
    # Core Engine Systems
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)
    
    # World container for scrolling
    world = Node2D("World")
    root.add_child(world)
    
    # Build Map
    from src.game.level import LevelManager
    level = LevelManager("Level", collision_world)
    world.add_child(level)
    
    # Add Player
    from src.game.entities.player import Player
    player_col = Collider2D("Player_Col", -20, -20, 40, 40)
    player_col.layer = "player"
    player_col.mask = {"wall", "box", "pickup", "enemy"}
    
    player = Player("Player", 100, 200, player_col, collision_world)
    player.add_child(player_col)
    world.add_child(player)
    
    # Add Box
    from src.game.entities.box import Box
    box_col = Collider2D("BoxCol", 0, 0, 40, 40)
    box_col.layer = "box"
    box_col.mask = {"wall", "box"}
    box = Box("Box1", 800, 400, box_col, collision_world)
    box.add_child(box_col)
    world.add_child(box)
    
    # Add Enemy
    from src.game.entities.enemy import Enemy
    enemy_col = Collider2D("EnemyCol", -20, -20, 40, 40)
    enemy_col.layer = "enemy"
    enemy_col.mask = {"wall", "player", "box"}
    enemy = Enemy("Bot1", 1400, 450, enemy_col, collision_world, move_dist=300)
    enemy.add_child(enemy_col)
    world.add_child(enemy)
    
    # Add Coins
    from src.game.entities.coin import Coin
    coins_data = [
        ("Coin1", 350, 400),
        ("Coin2", 450, 350),
        ("Coin3", 550, 300),
        ("Coin4", 1500, 400),
    ]
    for c_name, cx, cy in coins_data:
        coin = Coin(c_name, cx, cy)
        world.add_child(coin)
        coin.get_signal("on_collected").connect(lambda score_value, **kwargs: None) # Setup listening below
        
    # Camera
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = camera
    
    # UI
    from src.game.ui.hud import HUD
    hud = HUD("HUD")
    root.add_child(hud)
    
    # Wire up signals
    player.get_signal("on_score_changed").connect(lambda score: hud.on_score_changed(score))
    player.get_signal("on_died").connect(hud.on_died)
    
    def on_fixed_update(eng, scene_root, fixed_dt):
        pass
        
    def on_render(eng, scene_root, surface):
        pass
        
    root.print_tree()
    engine.run(root, on_fixed_update=on_fixed_update, on_render=on_render)

if __name__ == "__main__":
    main()
