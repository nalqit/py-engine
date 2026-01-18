# PyEngine 2D

A lightweight, purely Python-based 2D game engine built incrementally using **Pygame**, inspired by Godot’s scene system.

> **Note:** This project focuses on clarity, learning, and extensibility rather than raw performance or feature completeness.

---

## 🟢 Status
**Stable Experimental Prototype**
All core systems (scene, physics, collision, camera, debug) are functional and integrated.

---

## ✨ Core Features

### 🌳 Scene System
* **Hierarchical Graph:** `Node` / `Node2D` based structure.
* **Transforms:** Handles Local, Global, and Screen transforms.
* **Recursive Logic:** Parent–child relationships with recursive update & render loops.
* **Debugging:** Built-in `print_tree()` to visualize the scene graph.

### 🍎 Physics & Collision
* **PhysicsBody2D:** Base class for all dynamic entities.
* **Mechanics:** Gravity, jumping, and basic movement implementation.
* **Detection:** AABB (Axis-Aligned Bounding Box) collision detection.
* **Resolution:** Axis-separated collision resolution (X axis first, then Y).
* **Ground Detection:** Robust `on_ground` checking.

### 🛡️ Collision System
* **Components:** `Collider2D` nodes attached to entities.
* **CollisionWorld:** Centralized collision checking using spatial logic.
* **Filtering:** Uses **Layers** (what object is) and **Masks** (what it collides with).
* **Debug:** Visual overlay for colliders (color-coded).

#### Layers & Masks Examples:
* **Player:** Collides with Walls, Boxes, NPCs.
* **Ghost:** Collides with nothing.
* **Boxes:** Collide with Walls and Entities.

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

## 🚀 Planned Next Steps

- [ ] Proper push mechanics for boxes.
- [ ] Collision callbacks (on_enter / on_exit).
- [ ] Circular collider support.
- [ ] Basic state machine for entities.
- [ ] Tilemap support.
- [ ] Save/Load scene functionality.