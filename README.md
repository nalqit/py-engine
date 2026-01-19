# PyEngine 2D
PyEngine 2D is an experimental 2D game engine built with Python and Pygame.
The project is under active development and not production-ready.

A lightweight, purely Python-based 2D game engine built incrementally using **Pygame**, inspired by Godot’s scene system.

> **Note:** This project focuses on clarity, learning, and extensibility rather than raw performance or feature completeness.

---

## 🟢 Status
**Stable Experimental Prototype**
Core systems (Physics, Collision, Gravity, Push) are now fully functional.
-   Gravity works correctly.
-   Collision events (enter/stay/exit) are reliable.
-   Push mechanics are deterministic.

---

## ✨ Core Features

### 📡 Collision Callbacks (New!)
Entities can receive collision events by implementing these methods:
*   `on_collision_enter(other)`: Called when collision starts.
*   `on_collision_stay(other)`: Called every frame while colliding.
*   `on_collision_exit(other)`: Called when collision ends.
*   *Note:* These are events only and do not affect physics resolution.

### 🌳 Scene System
* **Hierarchical Graph:** `Node` / `Node2D` based structure.
* **Transforms:** Handles Local, Global, and Screen transforms.
* **Recursive Logic:** Parent–child relationships with recursive update & render loops.
* **Debugging:** Built-in `print_tree()` to visualize the scene graph.

### 🍎 Physics & Collision
* **PhysicsBody2D:** Base class for all dynamic entities.
*   **Mechanics:** Gravity, jumping, and basic movement implementation.
*   **Detection:** AABB (Axis-Aligned Bounding Box) collision detection.
*   **Resolution:** Axis-separated collision resolution (X axis first, then Y).
*   **Dynamic vs Dynamic:** Priority-based resolution. Moving bodies push idle bodies; if blocked, movement stops (no overlap).
*   **Ground Detection:** Robust `on_ground` checking.

### 🛡️ Collision System
* **Components:** `Collider2D` nodes attached to entities.
* **CollisionWorld:** Centralized collision checking using spatial logic.
* **Filtering:** Uses **Layers** (what object is) and **Masks** (what it collides with).
* **Debug:** Visual overlay for colliders (color-coded).

### 🔔 Trigger Colliders (New!)
*   **Trigger vs Solid:**
    *   `is_trigger=False` (Default): Solid, blocks movement (Walls, Floors).
    *   `is_trigger=True`: Pass-through, used for zones (Damage, Checkpoints).
*   **Behavior:** Triggers do **not** stop physics bodies but **do** fire collision events (`on_collision_enter`).
*   **Use Cases:** Pickups, damage zones, door sensors.

#### Layers & Masks Examples:
*   **Player:** Collides with Walls, Boxes, NPCs.
*   **Ghost:** Collides with nothing.
*   **Boxes:** Collide with Walls and Entities.

### 🎮 Entities
| Entity | Behavior |
| :--- | :--- |
| **Player** | Input-driven movement, Gravity, Jumping, Full collision response. |
| **NPC** | Autonomous horizontal movement, Gravity, Direction switching on collision. |
| **Box** | Affected by gravity, Blocks Player & NPC, Physical obstacle. |

### 🎥 Camera
* **Camera2D:** Smoothly follows a target node.
* **Viewport:** Clean World-to-Screen transformation handling.

### 🛠️ Debug & Tools
* **Visuals:** Collider debug rendering.
* **Stats HUD:** Displays FPS, Node count, and Scene tree info.
* **Separation:** Strict visual separation between game logic and rendering.

---

## 🎮 Controls

| Key | Action |
| :--- | :--- |
| **Left / Right Arrow** | Move Character |
| **Up Arrow** | Jump |
| **Close Window** | Quit Application |

---

## ⚙️ Setup & Installation

### Requirements
* **Python:** 3.10+
* **Pygame:** 2.6+

### Installation

1.  Clone the repository or download the source code.
2.  Install the dependencies via pip:

```bash
pip install pygame
```

### 🏃 Running the Engine

From the project root directory, run:

```bash
python main.py
```

---

## 📂 Project Structure

```text
src/
├── scene/
│   ├── node.py
│   ├── node2d.py
│   ├── camera2d.py
│   ├── physics/
│   │   └── physics_body_2d.py
│   ├── collision/
│   │   ├── collider2d.py
│   │   └── collision_world.py
│   ├── entities/
│   │   ├── npc.py
│   │   └── box.py
│   ├── ui/
│   │   └── stats_hud.py
│   └── input/
│       └── input_manager.py
├── ecs/               # Optional / legacy ECS system
└── main.py
```

## 🎯 Design Goals

*   **Educational Clarity:** Prioritizing readable code over complex abstractions.
*   **Explicit Systems:** No "magic" code; everything is traceable.
*   **Godot-like Structure:** Familiar node structure without hiding the underlying logic.
*   **Debuggable:** Easy to inspect and extend.

## ⚠️ Current Limitations

*   **Collision Shapes:** Only AABB (Rectangular) collisions are supported.
*   **Physics:** No collision response forces (push logic is currently manual/kinematic).
*   **Editor:** Code-only interface (no visual editor).
*   **Data:** No serialization or scene loading/saving yet.

- [x] Proper push mechanics for boxes.
- [x] Collision callbacks (on_enter / on_exit).
- [ ] Circular collider support.
- [ ] Basic state machine for entities.
- [ ] Tilemap support.
- [ ] Save/Load scene functionality.

---

## 🎮 Controller Architecture

The engine uses a **Controller** system to separate decision-making from physics execution.

*   **Controller (Base):** Abstract class for behavior logic.
*   **InputController:** Translates keyboard input into movement intent for the `Player`.
*   **AIController:** Handles autonomous patrol logic for `NPCs`.
*   **PhysicsBody2D:** Executes the physical movement, gravity, and collision resolution based on the velocity set by the controller.

### Separation of Concerns
1.  **Choice:** Controllers set `velocity_x` and `velocity_y`.
2.  **Physics:** `PhysicsBody2D` applies gravity and uses `move_and_collide` to update position while respecting walls and other entities.

To add new behavior, create a class inheriting from `Controller` and assign it to `body.controller`.

## 📄 License
This project is licensed under the MIT License.
