"""
Level 4 — Gameplay Layer Tests

Tests:
    - Horizontal acceleration & max speed clamping
    - Friction (velocity reduces to zero)
    - Ground detection (pure probe check)
    - Jump (only works when grounded + impulse applied)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.node2d import Node2D
from src.game.entities.player import Player


# ======================================================================
# Helpers
# ======================================================================

def build_scene():
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)

    col = Collider2D("PlayerCol", 0, 0, 50, 50)
    col.layer = "player"
    col.mask = {"wall"}
    
    player = Player("Player", 100, 100, col, cw)
    player.add_child(col)
    root.add_child(player)

    # Floor
    floor = Node2D("Floor", 0, 400)
    floor_col = Collider2D("FloorCol", 0, 0, 800, 50, is_static=True)
    floor_col.layer = "wall"
    floor_col.mask = {"player"}
    floor.add_child(floor_col)
    root.add_child(floor)

    return root, cw, player


# ======================================================================
# Tests
# ======================================================================

def test_horizontal_acceleration():
    root, cw, player = build_scene()
    player.use_gravity = False # simplify
    
    # Move right
    input_state = {"move_left": False, "move_right": True, "jump": False}
    
    # 0.1s update
    player.controller.update(player, 0.1, input_state)
    # acc=1200, 1200 * 0.1 = 120
    assert player.velocity_x == 120.0
    
    # Continue moving right
    for _ in range(10):
        player.controller.update(player, 0.1, input_state)
    
    # must clamp to max_speed (400)
    assert player.velocity_x == 400.0
    print("[PASS] test_horizontal_acceleration")


def test_friction():
    root, cw, player = build_scene()
    player.use_gravity = False
    player.velocity_x = 200.0
    
    # No input
    input_state = {"move_left": False, "move_right": False, "jump": False}
    
    # friction=800, 200 / 800 = 0.25s to stop
    player.controller.update(player, 0.1, input_state)
    assert player.velocity_x == 200.0 - (800.0 * 0.1)
    
    # Wait until stopped
    for _ in range(5):
        player.controller.update(player, 0.1, input_state)
        
    assert player.velocity_x == 0.0
    print("[PASS] test_friction")


def test_ground_detection():
    root, cw, player = build_scene()
    
    # 1. Player in air (y=100, floor at y=400)
    player.controller.update(player, 0.1, {})
    assert player.controller.is_grounded == False
    
    # 2. Player touching ground
    # Player rect is 50x50. If y=350, bottom is 400.
    player.local_y = 350.0
    player.controller.update(player, 0.1, {})
    assert player.controller.is_grounded == True
    
    # 3. Slighly above
    player.local_y = 345.0
    player.controller.update(player, 0.1, {})
    # probe is 2.0px. 400 - (345+50) = 5px. Should be False.
    assert player.controller.is_grounded == False
    
    print("[PASS] test_ground_detection")


def test_jump_logic():
    root, cw, player = build_scene()
    player.use_gravity = False
    
    # 1. Try jump while in air
    player.local_y = 100.0
    input_state = {"jump": True}
    player.controller.update(player, 0.1, input_state)
    assert player.velocity_y == 0.0 # No jump
    
    # 2. Try jump while grounded
    player.local_y = 350.0
    player.controller.update(player, 0.1, input_state)
    # jump_force = 450. velocity_y should be -450
    assert player.velocity_y == -450.0
    assert player.controller.is_grounded == False # Instant exit
    
    print("[PASS] test_jump_logic")


if __name__ == "__main__":
    test_horizontal_acceleration()
    test_friction()
    test_ground_detection()
    test_jump_logic()
    print("\n=== ALL LEVEL 4 GAMEPLAY TESTS PASSED ===")
