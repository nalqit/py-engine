import sys
import os
import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.node2d import Node2D
from src.game.entities.player import Player

def setup_test_scene():
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)
    
    player_col = Collider2D("PlayerCol", 0, 0, 50, 50)
    player = Player("Player", 100, 450, player_col, cw) # Start near "floor"
    player.add_child(player_col)
    root.add_child(player)
    
    # Floor
    floor = Node2D("Floor", 0, 500)
    floor_col = Collider2D("FloorCol", 0, 0, 800, 50, is_static=True)
    floor_col.layer = "wall"
    floor.add_child(floor_col)
    root.add_child(floor)
    
    return root, cw, player

def test_consistent_jump_height():
    """Verify that jumping results in the same peak height regardless of delta."""
    # 1. Simulate at 60Hz (fixed_dt should match)
    root1, cw1, player1 = setup_test_scene()
    player1.use_gravity = True
    player1.apply_impulse(0, -400) # Initial jump
    
    peak_y_60 = player1.local_y
    # Simulate for 1 second at 60fps
    for _ in range(60):
        dt = 1/60.0
        root1.update_transforms()
        root1.update(dt)
        peak_y_60 = min(peak_y_60, player1.local_y)
        
    # 2. Simulate at 10Hz (very laggy)
    root2, cw2, player2 = setup_test_scene()
    player2.use_gravity = True
    player2.apply_impulse(0, -400)
    
    fixed_dt = 1/60.0
    accumulator = 0.0
    peak_y_accumulator = player2.local_y
    
    # Simulate for 1 second at 10fps
    for _ in range(10):
        dt = 0.1 # 10fps
        accumulator += dt
        while accumulator >= fixed_dt:
            root2.update_transforms()
            root2.update(fixed_dt)
            peak_y_accumulator = min(peak_y_accumulator, player2.local_y)
            accumulator -= fixed_dt
            
    print(f"Peak Y at 60fps: {peak_y_60:.4f}")
    print(f"Peak Y with Accumulator (10fps): {peak_y_accumulator:.4f}")
    
    # They should be IDENTICAL because the same fixed_dt was used in the physics steps
    assert abs(peak_y_60 - peak_y_accumulator) < 0.0001
    print("[PASS] test_consistent_jump_height")

def test_global_position_cache():
    """Ensure cached global positions are correct."""
    root = Node2D("Root", 10, 10)
    child = Node2D("Child", 20, 20)
    root.add_child(child)
    
    # Before update_transforms, cache should be default (local)
    assert child.get_global_position() == (20, 20)
    
    root.update_transforms()
    assert child.get_global_position() == (30, 30)
    
    child.local_x = 50
    # Still 30, 30 because not refreshed
    assert child.get_global_position() == (30, 30)
    
    root.update_transforms()
    assert child.get_global_position() == (60, 30)
    print("[PASS] test_global_position_cache")

if __name__ == "__main__":
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1, 1), pygame.NOFRAME | pygame.HIDDEN)
    
    test_global_position_cache()
    test_consistent_jump_height()
