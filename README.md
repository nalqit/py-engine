# PyEngine 2D

PyEngine 2D is a lightweight, purely Python-based 2D game engine built with **Pygame**, inspired by Godot’s scene and node system. It focuses on architectural clarity, explicit systems, and educational value.

> [!NOTE]
> This project is an experimental prototype focusing on learning and extensibility rather than raw performance.

---

## 🟢 System Status

The engine features a stable core with fully integrated physics, collision, and state management systems.

- **Physics**: Deterministic AABB resolution with axis separation.
- **Gravity**: Robust vertical movement and ground detection.
- **Controllers**: Decoupled "Intent-based" movement system.
- **FSM**: Descriptive state machine (Idle / Walk / Fall).
- **Collisions**: Layer-based filtering and collision callbacks (Enter/Stay/Exit).

---

## ✨ Core Architecture

### 🌳 Scene System

- **Node-based Hierarchy**: All game objects inherit from `Node` or `Node2D`.
- **Recursive Logic**: Parents automatically update and render children.
- **Transform System**: Handles local vs global coordinate management.

### � Controller & Intent System

The engine strictly separates "Decision Making" from "Physics Execution":

1. **Controller**: Abstract behavior logic (e.g., `InputController`, `AIController`).
2. **Intent**: Controllers set `intent_x` and `intent_y` (desired direction).
3. **Execution**: `PhysicsBody2D` translates intents into velocity and resolves collisions.

### 🔄 Finite State Machine (FSM)

A **Descriptive FSM** that observes the entity's physical reality rather than driving it:

- **Idle**: Grounded and stationary.
- **Walk**: Grounded and moving horizontally.
- **Fall**: In the air (jumping or falling).
- **Execution Order**: `Controller (Intent)` → `Physics (Resolution)` → `FSM (Observation)`.

### �️ Collision & Physics

- **CollisionWorld**: Centralized manager for spatial queries.
- **Layers & Masks**: Fine-grained control over which objects interact.
- **Push Mechanics**: Moving bodies can push dynamic objects (like Boxes) if they aren't blocked.
- **Callbacks**: `on_collision_enter`, `on_collision_stay`, and `on_collision_exit`.

---

## 📂 Project Structure

```text
src/
├── engine/                # Core engine (reusable)
│   ├── scene/             # Node system, camera, visuals
│   ├── physics/           # PhysicsBody2D, controllers, movement
│   ├── collision/         # Colliders and collision world
│   ├── fsm/               # Finite State Machine (Idle / Walk / Fall)
│   ├── input/             # Input abstraction
│   └── ui/                # Debug & HUD elements
│
├── game/                  # Example game / sandbox
│   ├── entities/          # Player, NPC, Box
│   └── main.py            # Game entry point
```

---

## 🎮 Controls

| Key                    | Action                   |
| :--------------------- | :----------------------- |
| **Arrow Left / Right** | Move Character           |
| **Arrow Up**           | Jump                     |
| **Arrow Down**         | Fast Fall (Experimental) |
| **Close Window**       | Exit Game                |

---

## ⚙️ Setup

1. **Python**: 3.10+
2. **Dependencies**: `pip install pygame`
3. **Run**: `python main.py`

---

## 🚀 Roadmap

- [x] Intent-based Physics Separation.
- [x] Descriptive FSM (Idle / Walk / Fall).
- [x] Axis-separated Collision Resolution.
- [x] Dynamic pushing and blocking.
- [ ] Circular Collider support.
- [ ] Tilemap integration.
- [ ] Visual Scene Editor.

## 📄 License

This project is licensed under the MIT License.
