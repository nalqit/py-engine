# PyEngine 2D

PyEngine 2D is a lightweight, purely Python-based 2D game engine built with **Pygame**, inspired by Godot's scene and node system. It focuses on architectural clarity, explicit systems, and educational value.

> [!NOTE]
> This project is an experimental prototype focusing on learning and extensibility rather than raw performance.

---

## 🟢 System Status

The engine is built using a **layered architecture**, with each level stabilized before the next is added.

| Level | Layer               | Status |
| :---: | :------------------ | :----: |
|   0   | Runtime Core        |   ✅   |
|   1   | Scene System        |   ✅   |
|   2   | Collision System    |   ✅   |
|   3   | Physics Layer       |   ✅   |
|   4   | Gameplay Systems    |   🔜   |

### Level 0 — Runtime Core
- Game loop, delta timing, base `Node` class, scene tree hierarchy.

### Level 1 — Scene System
- Parent/child transform propagation, local vs global position, update lifecycle.

### Level 2 — Collision System
- **Collider2D**: Pure AABB data — dimensions, layer/mask, static/trigger flags.
- **CollisionResult**: Structured dataclass with collision normal and penetration depth.
- **CollisionWorld**: Float-precision AABB overlap checks with MTV resolution. Layer/mask filtering, trigger support, enter/stay/exit event callbacks.
- **PhysicsBody2D**: Generic body with per-axis move-and-collide resolution.

### Level 3 — Physics Layer *(current)*
- **Gravity**: Engine-level `use_gravity` flag with configurable `gravity` constant (default 800).
- **Impulses**: `apply_impulse(ix, iy)` for instantaneous velocity changes.
- **Direction-based snapping**: Position correction uses movement direction + obstacle edge, not MTV normals — eliminates ambiguity in per-axis resolution.
- **Float-precision collision**: Sub-pixel overlap detection prevents gravity hopping artifacts.

---

## ✨ Core Architecture

### 🌳 Scene System

- **Node-based Hierarchy**: All game objects inherit from `Node` or `Node2D` (found in `src/engine/scene/`).
- **Recursive Logic**: Parents automatically update and render children.
- **Transform System**: Handles local vs global coordinate management.

### �️ Collision System

- **Collider2D**: Axis-Aligned Bounding Box attached as a child node. Computes its world-space rect from the scene tree transform.
- **CollisionResult**: Dataclass describing whether a collision occurred, the hit collider, collision normal (direction to push out), and penetration depth.
- **CollisionWorld**: Walks the scene tree to find colliders. `check_collision(collider, target_x, target_y)` returns a `CollisionResult`. Also runs broad-phase pair detection with `process_collisions()` for enter/stay/exit events.
- **Layers & Masks**: Fine-grained control over which objects interact.
- **Triggers**: Non-blocking colliders that still fire collision events.

### ⚙️ PhysicsBody2D

- Holds `velocity_x`, `velocity_y`.
- Applies gravity acceleration when `use_gravity` is enabled.
- `apply_impulse(ix, iy)` for instant velocity changes (jumps, knockback at higher levels).
- `update(delta)` integrates gravity → computes displacement → calls `move_and_collide(dx, dy)`.
- Resolves X then Y independently — on collision, snaps to obstacle edge and zeroes velocity on the impacted axis only.
- Provides empty `on_collision_enter/stay/exit` hooks for subclasses.
- **Fully generic** — no assumptions about what the body represents.

---

## 📂 Project Structure

```text
src/
├── engine/                # Core engine (reusable)
│   ├── scene/             # Node system, camera, shapes (Node, Node2D, RectangleNode, CircleNode)
│   ├── collision/         # Collider2D, CollisionResult, CollisionWorld
│   ├── physics/           # PhysicsBody2D
│   ├── fsm/               # Finite State Machine (reserved for future levels)
│   ├── input/             # InputManager (reserved for future levels)
│   └── ui/                # StatsHUD and debug UI
│
├── game/                  # Example game / sandbox
│   ├── entities/          # Player, NPC, Box
│   └── main.py            # Game entry point
│
tests/
└── test_collision_system.py  # Level 2 collision tests
```

---

## ⚙️ Setup

1. **Python**: 3.10+
2. **Dependencies**: `pip install pygame`
3. **Run**: `python -m src.game.main`
4. **Test**: `python tests/test_collision_system.py` and `python tests/test_physics_layer.py`

---

## 🚀 Roadmap

### Completed
- [x] Runtime Core (game loop, delta timing, scene tree).
- [x] Scene System (transforms, parent/child propagation).
- [x] Collision System (AABB, CollisionResult, float-precision overlap).
- [x] Layer/mask filtering and trigger support.
- [x] Collision callbacks (enter/stay/exit).
- [x] Generic PhysicsBody2D with axis-separated resolution.
- [x] Engine-level gravity and impulse system.
- [x] Direction-based position snapping.
- [x] Debug collider visualization.
- [x] Integrated performance HUD.

### Up Next (Level 4 — Gameplay Systems)
- [ ] Controller & Intent system (Input, AI).
- [ ] Finite State Machine (Idle / Walk / Fall).
- [ ] Push mechanics between dynamic bodies.

### Future
- [ ] Circular collision support.
- [ ] Tilemap integration.
- [ ] Visual Scene Editor.

## 📄 License

This project is licensed under the MIT License.
