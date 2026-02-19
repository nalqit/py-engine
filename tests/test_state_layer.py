"""
Level 5 — State Layer (FSM) Tests

Tests:
    - Idle -> Run (threshold)
    - Run -> Idle (friction)
    - Jump -> Fall (peak)
    - Fall -> Idle/Run (landing)
    - No direct velocity modification in states
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.node2d import Node2D
from src.game.entities.player import Player


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

    # Floor at y=400
    floor = Node2D("Floor", 0, 400)
    floor_col = Collider2D("FloorCol", 0, 0, 800, 50, is_static=True)
    floor_col.layer = "wall"
    floor_col.mask = {"player"}
    floor.add_child(floor_col)
    root.add_child(floor)

    return root, cw, player


def test_idle_to_run_transition():
    root, cw, player = build_scene()
    # Ground the player so it doesn't transition to FallState
    player.local_y = 350.0 
    player.controller.update(player, 0.1, {}) 
    assert player.state_machine.get_state_name() == "IdleState"
    
    # Velocity below threshold (10.0)
    player.velocity_x = 5.0
    player.state_machine.update(0.1)
    assert player.state_machine.get_state_name() == "IdleState"
    
    # Velocity above threshold
    player.velocity_x = 15.0
    player.state_machine.update(0.1)
    assert player.state_machine.get_state_name() == "RunState"
    print("[PASS] test_idle_to_run_transition")


def test_run_to_idle_transition():
    root, cw, player = build_scene()
    # Ground the player
    player.local_y = 350.0
    player.controller.update(player, 0.1, {})

    player.velocity_x = 50.0
    player.state_machine.update(0.1) # Transition to Run
    assert player.state_machine.get_state_name() == "RunState", f"Expected RunState, got {player.state_machine.get_state_name()}"
    
    player.velocity_x = 5.0
    player.state_machine.update(0.1)
    assert player.state_machine.get_state_name() == "IdleState", f"Expected IdleState, got {player.state_machine.get_state_name()}"
    print("[PASS] test_run_to_idle_transition")


def test_jump_to_fall_transition():
    root, cw, player = build_scene()
    
    # Start jumping
    player.velocity_y = -100.0
    player.state_machine.update(0.1)
    assert player.state_machine.get_state_name() == "JumpState"
    
    # Peak of jump (velocity becomes positive)
    player.velocity_y = 10.0
    player.state_machine.update(0.1)
    assert player.state_machine.get_state_name() == "FallState"
    print("[PASS] test_jump_to_fall_transition")


def test_fall_to_idle_on_landing():
    root, cw, player = build_scene()
    
    # In air, falling
    player.local_y = 100.0
    player.velocity_y = 50.0
    player.state_machine.update(0.1)
    assert player.state_machine.get_state_name() == "FallState"
    
    # Hit floor
    player.local_y = 350.0
    player.velocity_y = 0.0
    # Must update controller first to set grounded flag for the FSM to see
    player.controller.update(player, 0.1, {}) 
    player.state_machine.update(0.1)
    assert player.state_machine.get_state_name() == "IdleState"
    print("[PASS] test_fall_to_idle_on_landing")


def test_no_direct_velocity_modification_in_states():
    root, cw, player = build_scene()
    player.velocity_x = 100.0
    player.velocity_y = 50.0
    
    old_vx, old_vy = player.velocity_x, player.velocity_y
    player.state_machine.update(0.1)
    
    assert player.velocity_x == old_vx
    assert player.velocity_y == old_vy
    print("[PASS] test_no_direct_velocity_modification_in_states")


if __name__ == "__main__":
    test_idle_to_run_transition()
    test_run_to_idle_transition()
    test_jump_to_fall_transition()
    test_fall_to_idle_on_landing()
    test_no_direct_velocity_modification_in_states()
    print("\n=== ALL LEVEL 5 STATE LAYER TESTS PASSED ===")
