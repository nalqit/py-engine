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
|   4   | Gameplay Layer      |   ✅   |
|   5   | State Layer (FSM)   |   ✅   |

### Level 0 — Runtime Core
- Game loop, delta timing, base `Node` class, scene tree hierarchy.

### Level 1 — Scene System
- Parent/child transform propagation, local vs global position, update lifecycle.

### Level 2 — Collision System
- **Collider2D**: Pure AABB data — dimensions, layer/mask, static/trigger flags.
- **CollisionResult**: Structured dataclass with collision normal and penetration depth.
- **CollisionWorld**: Float-precision AABB overlap checks with MTV resolution. Layer/mask filtering, trigger support.

### Level 3 — Physics Layer
- **PhysicsBody2D**: Generic body with per-axis move-and-collide resolution.
- **Gravity**: Engine-level `use_gravity` flag with configurable `gravity` constant.
- **Impulses**: `apply_impulse(ix, iy)` for instantaneous velocity changes.
- **Direction-based snapping**: Eliminates ambiguity in per-axis resolution.

### Level 4 — Gameplay Layer
- **PlayerController**: Engine-agnostic controller that maps abstract input to physics intentions.
- **Movement**: Acceleration-based horizontal movement with friction and max speed clamping.
- **Ground Detection**: Non-invasive pure probe check (downward offset) via `CollisionWorld`.
- **Architectural Isolation**: Control logic is detached from the physics engine.

### Level 5 — State Layer (FSM) *(current)*
- **PlayerStateMachine**: Manages behavioral states (Idle, Run, Jump, Fall).
- **Lightweight States**: Concrete state objects (`IdleState`, `RunState`, etc.) that handle transitions based on velocity and grounded status.
- **Strict Order**: Input → Physics → FSM execution sequence ensures behavioral consistency.
- **Stability**: Movement thresholds prevent transition flickering.

---

## ✨ Core Architecture

### 🎮 Gameplay & Control (Levels 4-5)

- **Engine-Agnostic Controllers**: The `PlayerController` does not import `pygame`, receiving an abstract `input_state` dictionary instead. This makes the logic testable and portable.
- **Finite State Machine**: Decouples "what the player is doing" (Run, Jump) from "how the player moves" (force, velocity).
- **Non-Invasive Probes**: Ground detection is a side-effect-free collision check, not a mutation of physics state.

### ⚙️ Physics & Collision (Levels 2-3)

- **Axis-Separated Resolution**: X is resolved, then Y. On collision, position is snapped to the obstacle edge and velocity is zeroed on that axis.
- **Float-Precision**: Avoids integer rounding artifacts common in basic AABB engines.
- **Generic Bodies**: `PhysicsBody2D` carries no gameplay assumptions (no "is_player" or "jump_force" flags).

---

## 📂 Project Structure

```text
src/
├── engine/                # Core engine (reusable)
│   ├── scene/             # Node system, camera, shapes
│   ├── collision/         # Collider2D, CollisionResult, CollisionWorld
│   └── physics/           # PhysicsBody2D
│
├── game/                  # Gameplay Layer
│   ├── entities/          # Player, NPC, Box
│   ├── player_controller.py  # Level 4: Input/Movement logic
│   ├── player_fsm.py         # Level 5: State machine manager
│   ├── player_states.py      # Level 5: State definitions (Idle, Run...)
│   └── main.py            # Game entry point
│
├── tests/
│   ├── test_gameplay_layer.py # Level 4 tests
│   ├── test_state_layer.py    # Level 5 tests
│   └── ...
```

---

## ⚙️ Setup

1. **Python**: 3.10+
2. **Dependencies**: `pip install pygame`
3. **Run**: `python -m src.game.main`
4. **Test**: `python tests/test_state_layer.py`

---

## 🚀 Roadmap

### Completed
- [x] Runtime Core & Scene Tree.
- [x] AABB Collision System (Layer/Mask, Triggers).
- [x] Generic PhysicsBody2D with axis-separation.
- [x] Engine-level Gravity and Impulse support.
- [x] Engine-Agnostic Player Controller (Level 4).
- [x] Non-invasive Download Ground Probe.
- [x] Behavioral State Machine (Level 5).
- [x] Threshold-based transition stabilization.

### Up Next (Level 6 — Animation Layer)
- [ ] Spritesheet support.
- [ ] State-bound animation playback.
- [ ] Frame-perfect event hooks.

### Future
- [ ] Circular collision support.
- [ ] Tilemap integration.
- [ ] Visual Scene Editor.

## 📄 License

This project is licensed under the MIT License.
