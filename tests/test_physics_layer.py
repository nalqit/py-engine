"""
Level 3 — Physics Layer Tests

Tests engine-level physics on top of the Level 2 collision system:
    - Gravity integration
    - Gravity + floor collision (body lands and stops)
    - No-gravity body stays still
    - apply_impulse
    - Axis independence (gravity on Y doesn't bleed into X)
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()

from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.node2d import Node2D
from src.engine.physics.physics_body_2d import PhysicsBody2D


# ======================================================================
# Helpers
# ======================================================================

def make_body(name, x, y, w, h, cw, gravity=False):
    col = Collider2D(name + "Col", 0, 0, w, h)
    col.layer = "player"
    col.mask = {"wall"}
    body = PhysicsBody2D(name, x, y, col, cw)
    body.use_gravity = gravity
    body.add_child(col)
    return body


def make_wall(name, x, y, w, h):
    wall = Node2D(name, x, y)
    col = Collider2D(name + "Col", 0, 0, w, h, is_static=True)
    col.layer = "wall"
    col.mask = {"player"}
    wall.add_child(col)
    return wall


def build_scene_with_floor():
    """
    Body at (100, 100), 50x50, with a floor at y=400 (height 50).
    300px of free space below the body.
    """
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)

    body = make_body("Body", 100, 100, 50, 50, cw, gravity=True)
    root.add_child(body)

    floor = make_wall("Floor", 0, 400, 800, 50)
    root.add_child(floor)

    return root, cw, body


# ======================================================================
# Tests
# ======================================================================

def test_gravity_increases_velocity():
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)
    body = make_body("B", 100, 100, 50, 50, cw, gravity=True)
    root.add_child(body)

    assert body.velocity_y == 0.0
    body.update(0.1)  # gravity = 800 * 0.1 = 80
    assert abs(body.velocity_y - 80.0) < 0.01
    print("[PASS] test_gravity_increases_velocity")


def test_no_gravity_stays_still():
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)
    body = make_body("B", 100, 100, 50, 50, cw, gravity=False)
    root.add_child(body)

    old_x, old_y = body.local_x, body.local_y
    body.update(0.1)
    assert body.local_x == old_x
    assert body.local_y == old_y
    assert body.velocity_y == 0.0
    print("[PASS] test_no_gravity_stays_still")


def test_gravity_stops_at_floor():
    root, cw, body = build_scene_with_floor()

    # Simulate several frames — body should fall and stop at floor
    for _ in range(200):
        body.update(1 / 60)

    # Body bottom (local_y + 50) should not exceed floor top (400)
    assert body.local_y + 50 <= 401  # 1px tolerance for int rects
    # Velocity should be zeroed on Y after landing
    assert body.velocity_y == 0.0
    print("[PASS] test_gravity_stops_at_floor")


def test_apply_impulse():
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)
    body = make_body("B", 100, 100, 50, 50, cw, gravity=False)
    root.add_child(body)

    body.apply_impulse(50, -200)
    assert body.velocity_x == 50.0
    assert body.velocity_y == -200.0
    print("[PASS] test_apply_impulse")


def test_apply_impulse_additive():
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)
    body = make_body("B", 100, 100, 50, 50, cw, gravity=False)
    root.add_child(body)

    body.velocity_x = 100.0
    body.apply_impulse(50, -200)
    assert body.velocity_x == 150.0
    assert body.velocity_y == -200.0
    print("[PASS] test_apply_impulse_additive")


def test_gravity_does_not_affect_x():
    root = Node2D("Root")
    cw = CollisionWorld("CW")
    root.add_child(cw)
    body = make_body("B", 100, 100, 50, 50, cw, gravity=True)
    root.add_child(body)

    body.velocity_x = 0.0
    for _ in range(10):
        body.update(1 / 60)

    assert body.velocity_x == 0.0  # X must be untouched
    assert body.velocity_y > 0.0   # Y increases from gravity
    print("[PASS] test_gravity_does_not_affect_x")


# ======================================================================
# Run all
# ======================================================================

if __name__ == "__main__":
    test_gravity_increases_velocity()
    test_no_gravity_stays_still()
    test_gravity_stops_at_floor()
    test_apply_impulse()
    test_apply_impulse_additive()
    test_gravity_does_not_affect_x()
    print("\n=== ALL LEVEL 3 TESTS PASSED ===")
