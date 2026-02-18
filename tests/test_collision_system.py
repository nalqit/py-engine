"""
Level 2 — Collision System Tests

Tests the core collision architecture in isolation:
    - CollisionResult construction
    - Collider2D AABB rect computation
    - CollisionWorld.check_collision with penetration / normal
    - PhysicsBody2D.move_and_collide axis-independent resolution
"""
import sys
import os

# Ensure project root is on sys.path so `src.*` imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()  # needed for pygame.Rect

from src.engine.collision.collision_result import CollisionResult
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.node2d import Node2D
from src.engine.physics.physics_body_2d import PhysicsBody2D


# ======================================================================
# Helpers
# ======================================================================

def make_static_wall(name, x, y, w, h, collision_world):
    """Create a static wall entity (Node2D + Collider2D child)."""
    wall = Node2D(name, x, y)
    col = Collider2D(name + "Col", 0, 0, w, h, is_static=True)
    col.layer = "wall"
    col.mask = {"player"}
    wall.add_child(col)
    return wall, col


def make_physics_body(name, x, y, w, h, collision_world):
    """Create a PhysicsBody2D with a child Collider2D."""
    col = Collider2D(name + "Col", 0, 0, w, h)
    col.layer = "player"
    col.mask = {"wall"}
    body = PhysicsBody2D(name, x, y, col, collision_world)
    body.add_child(col)
    return body, col


def build_simple_scene():
    """
    Build a minimal scene:
        Root
        ├── CollisionWorld
        ├── Player body at (100, 100), 50x50
        └── Wall at (200, 100), 50x200 (to the right of player)
    """
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)

    body, body_col = make_physics_body("Player", 100, 100, 50, 50, cw)
    root.add_child(body)

    wall, wall_col = make_static_wall("Wall", 200, 100, 50, 200, cw)
    root.add_child(wall)

    return root, cw, body, body_col, wall, wall_col


# ======================================================================
# Tests: CollisionResult
# ======================================================================

def test_collision_result_none():
    r = CollisionResult.none()
    assert r.collided is False
    assert r.collider is None
    assert r.normal_x == 0.0
    assert r.normal_y == 0.0
    assert r.penetration == 0.0
    print("[PASS] test_collision_result_none")


def test_collision_result_populated():
    dummy = Collider2D("dummy", 0, 0, 10, 10)
    r = CollisionResult(
        collided=True, collider=dummy,
        normal_x=-1.0, normal_y=0.0, penetration=5.0
    )
    assert r.collided is True
    assert r.collider is dummy
    assert r.normal_x == -1.0
    assert r.penetration == 5.0
    print("[PASS] test_collision_result_populated")


# ======================================================================
# Tests: Collider2D
# ======================================================================

def test_collider_rect_at_origin():
    parent = Node2D("P", 0, 0)
    col = Collider2D("C", 0, 0, 30, 40)
    parent.add_child(col)
    rect = col.get_rect()
    assert rect.x == 0 and rect.y == 0
    assert rect.width == 30 and rect.height == 40
    print("[PASS] test_collider_rect_at_origin")


def test_collider_rect_with_parent_offset():
    parent = Node2D("P", 100, 200)
    col = Collider2D("C", 5, 10, 30, 40)
    parent.add_child(col)
    rect = col.get_rect()
    assert rect.x == 105 and rect.y == 210
    print("[PASS] test_collider_rect_with_parent_offset")


# ======================================================================
# Tests: CollisionWorld.check_collision
# ======================================================================

def test_no_collision_when_far():
    root, cw, body, body_col, wall, wall_col = build_simple_scene()
    # Player at (100,100), wall at (200,100). Move player to (110,100) — no overlap.
    result = cw.check_collision(body_col, 110, 100)
    assert result.collided is False
    print("[PASS] test_no_collision_when_far")


def test_collision_returns_result_on_overlap():
    root, cw, body, body_col, wall, wall_col = build_simple_scene()
    # Move player to x=160 → player rect right edge = 210, wall left = 200 → overlap 10px
    result = cw.check_collision(body_col, 160, 100)
    assert result.collided is True
    assert result.collider is wall_col
    assert result.penetration > 0
    print("[PASS] test_collision_returns_result_on_overlap")


def test_collision_normal_direction():
    root, cw, body, body_col, wall, wall_col = build_simple_scene()
    # Move player into wall from the left → normal should push left (normal_x = -1)
    result = cw.check_collision(body_col, 170, 100)
    assert result.collided is True
    assert result.normal_x == -1.0
    assert result.normal_y == 0.0
    print("[PASS] test_collision_normal_direction")


# ======================================================================
# Tests: PhysicsBody2D.move_and_collide
# ======================================================================

def test_free_movement():
    root, cw, body, body_col, wall, wall_col = build_simple_scene()
    body.velocity_x = 100.0
    body.velocity_y = 0.0
    # dt=0.1 → dx=10, new x=110 (no collision)
    body.update(0.1)
    assert abs(body.local_x - 110.0) < 0.01
    print("[PASS] test_free_movement")


def test_blocked_movement_x():
    root, cw, body, body_col, wall, wall_col = build_simple_scene()
    body.velocity_x = 1000.0  # large velocity to overshoot into wall
    body.velocity_y = 50.0
    body.update(0.1)
    # X should be corrected (not past wall), velocity_x zeroed
    assert body.velocity_x == 0.0
    # Y should be unaffected by X collision
    assert body.velocity_y == 50.0
    assert abs(body.local_y - 105.0) < 0.01  # 100 + 50*0.1
    print("[PASS] test_blocked_movement_x")


def test_velocity_zeroed_only_on_impact_axis():
    root, cw, body, body_col, wall, wall_col = build_simple_scene()
    body.velocity_x = 2000.0
    body.velocity_y = 200.0
    body.update(0.05)
    assert body.velocity_x == 0.0   # impacted axis
    assert body.velocity_y == 200.0  # free axis preserved
    print("[PASS] test_velocity_zeroed_only_on_impact_axis")


# ======================================================================
# Run all
# ======================================================================

if __name__ == "__main__":
    test_collision_result_none()
    test_collision_result_populated()
    test_collider_rect_at_origin()
    test_collider_rect_with_parent_offset()
    test_no_collision_when_far()
    test_collision_returns_result_on_overlap()
    test_collision_normal_direction()
    test_free_movement()
    test_blocked_movement_x()
    test_velocity_zeroed_only_on_impact_axis()
    print("\n=== ALL TESTS PASSED ===")
