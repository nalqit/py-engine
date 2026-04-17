# PyEngine 2D

PyEngine 2D is a lightweight, purely Python-based 2D game engine built with **Pygame**, inspired by Godot's scene and node system. It focuses on architectural clarity, explicit systems, and educational value.

> [!NOTE]
> This project is an experimental prototype focusing on learning and extensibility rather than raw performance.

---

## 🟢 System Status

| Level | Layer                   | Status |
| :---: | :---------------------- | :----: |
|   0   | Runtime Core            |   ✅   |
|   1   | Scene System            |   ✅   |
|   2   | Collision System        |   ✅   |
|   3   | Physics Layer           |   ✅   |
|   4   | Gameplay Layer          |   ✅   |
|   5   | State Layer (FSM)       |   ✅   |
|   6   | Juice & Animation Layer |   ✅   |
|   7   | User Interface (UI)     |   ✅   |
|   8   | Tilemap Level           |   ✅   |
|   9   | Audio Layer             |   ✅   |
|  10   | Scene Editor (GUI)      |   ✅   |

### Level 0 — Runtime Core

- Game loop, delta timing, base `Node` class, scene tree hierarchy.

### Level 1 — Scene System

- Parent/child transform propagation, local vs global position, update lifecycle.
- **`TilemapNode`**: Multi-layer tilemap supporting JSON and **TMX** files, baked surfaces, auto-collision generation, viewport streaming, and parallax.

### Level 2 — Collision System

- **Collider2D**: Scale-aware AABB — dimensions, layer/mask, static/trigger flags, optional `visible` debug overlay.
- **CircleCollider2D**: Circle-circle and circle-AABB colliders.
- **PolygonCollider2D**: Convex polygon collisions resolved via SAT (Separating Axis Theorem).
- **CollisionWorld**: Float-precision shape overlap checks with MTV resolution + layer/mask filtering.

### Level 3 — Physics Layer

- **PhysicsBody2D**: Per-axis move-and-collide with float precision (ideal for platformers).
- **RigidBody2D**: Advanced dynamic physics body with mass, coefficient of restitution (bounciness), and true elastic momentum transfer.
- **PhysicsWorld2D**: Independent solver node providing localized simulation **sub-stepping** (e.g., 10 passes per frame) to prevent constraint and tunneling jitters.
- **DistanceConstraint**: Perfect springless rope/anchor simulation utilizing 2D circular tangent projection.
- **Gravity** and **Impulses**: Configurable forces including overlapping mass exchange.

### Level 4 — Gameplay Layer

- **PlayerController**: Engine-agnostic input → physics bridge.
- **Ground Detection**: Non-invasive downward probe check via `CollisionWorld`.

### Level 5 — State Layer (FSM)

- **PlayerStateMachine** with concrete states (`IdleState`, `RunState`, `JumpState`, `FallState`).

### Level 6 — Juice & Animation Layer

- **TweenManager**, **ParticleEmitter2D**, **AnimatedSprite**, **SpriteNode**, parallax backgrounds.

### Level 7 — User Interface (UI)

- **UIControl**, containers (`VBoxContainer`, `HBoxContainer`), `Button`, `Label`.
- Hierarchical event consumption + reactive data binding.

### Level 8 — Tilemap Level Editor

- **`draw2d.py`**: Standalone infinite-canvas 4-quadrant map editor.
- Zoom (scroll wheel), Pan (Space+Click or Middle-click), Draw (Left-click), Erase (Right-click).
- Press **[S]** to save JSON; **[L]** to load. Auto-tiling picks correct Left/Mid/Right/Underground edge tiles.
- Output consumed directly by `TilemapNode.load_from_json()` in-game.

### Level 9 — Audio Layer

- **AudioManager**: Global `pygame.mixer` wrapper serving as a unified interface to load and play SFX (`play_sound`) and stream background music (`play_music`).

### Level 10 — Scene Editor (GUI)

- **The Editor** (`src/the_editor/`): Flutter-based 2D scene editor.
- Dockable panels: Scene Tree, Viewport, Inspector, Bottom Panel.
- `.scene` JSON file format for saving/loading scene trees.

---

## ✨ Core Architecture

### 🗺️ Tilemap & Level Design (Level 8)

- **Infinite 4-Quadrant Canvas**: Draw geometry at any positive or negative coordinates.
- **Engine Integration**: `TilemapNode` reads `offset_x`/`offset_y` to place tiles at exact world-space positions.

### 🍭 Juice & Feel (Level 6)

- **Scale-Aware Hitboxes**: Colliders adapt automatically when nodes are tweened.

### 🎮 Gameplay & Control (Levels 4-5)

- **Engine-Agnostic Controllers**: `PlayerController` never imports `pygame`.
- **FSM**: Decouples behavioral identity from physics movement.

### ⚙️ Physics & Collision (Levels 2-3)

- **Axis-Separated Resolution** with float precision and inclusive epsilon bounds.

---

## 📂 Project Structure

```text
src/
├── pyengine2D/            # Core engine (reusable)
│   ├── benchmark/         # Performance testing harness
│   ├── collision/         # Collider2D, CircleCollider2D, PolygonCollider2D, CollisionWorld
│   ├── core/              # Engine, Input, Renderer, Audio, Signals
│   ├── fsm/               # State, StateMachine, IdleState, WalkState, FallState
│   ├── physics/           # PhysicsBody2D, RigidBody2D, PhysicsWorld2D, DistanceConstraint
│   ├── rendering/          # Renderer2D, BatchRenderer, TextureAtlas, SurfaceCache, PixelGrid
│   ├── scene/             # Node, Node2D, Camera2D, TilemapNode, AnimatedSprite, Particles
│   ├── time/              # MasterClock (fixed timestep scheduling)
│   ├── ui/                # UIControl, Containers, Widgets, EventSystem, DataBinding
│   └── utils/             # Profiler, ObjectPool, AssetManager, Pathfinding
│
└── games/                 # Game examples
    ├── frog_hop/          # Side-scrolling platformer (Ninja Frog + Fruits)
    │   ├── entities/      # Player, Fruit, Enemy, Trap
    │   ├── maps/          # JSON tilemaps
    │   ├── level.py       # Level builder
    │   └── main.py
    ├── neon_heights/
    ├── neon_odyssey/
    ├── neon_tank/
    └── newtons_cradle/    # Rigid body simulation

draw2d.py                  # Infinite 4-Quadrant Map Editor → JSON tilemaps
tests/
└── headless_verify.py     # Headless engine verification test

src/the_editor/            # Flutter-based Scene Editor
lib/
├── main.dart              # Entry point
├── main_layout.dart       # Main editor layout
├── viewport_widget.dart   # Scene viewport
├── scene_tree_widget.dart # Scene tree panel
├── inspector_widget.dart  # Property inspector
├── bottom_panel_widget.dart
└── engine_node.dart       # Engine node definitions
```

---

## ⚙️ Setup

1. **Python**: 3.10+
2. **Dependencies**: `pip install pygame`
3. **Engine Import**: `from src.pyengine2D import *`
4. **Run Frog Hop**: `python -m src.games.frog_hop.main`
5. **Other examples**:
   - `python -m src.games.neon_heights.main`
   - `python -m src.games.neon_odyssey.main`
   - `python -m src.games.neon_tank.main`
   - `python -m src.games.newtons_cradle.main`
6. **Run Tests**: `python tests/headless_verify.py`
7. **Level Editor**: `python draw2d.py` → draw → **[S]** → save to `src/games/frog_hop/maps/`
8. **Scene Editor**: `flutter run -d windows` in `src/the_editor/`

See [ENGINE_USAGE.md](ENGINE_USAGE.md) for a detailed API guide.

---

## 🧪 Testing

Run the headless verification test to verify the engine and games initialize correctly without a display:

```bash
pip install pygame
python tests/headless_verify.py
```

This test:
1. Sets `SDL_VIDEODUMMY=1` for headless operation
2. Imports and initializes the engine core modules
3. Runs both `frog_hop` and `neon_tank` games for 60 frames
4. Reports pass/fail for each component

Expected output:
```
============================================================
Testing engine core imports...
============================================================
[PASS] All core engine modules imported successfully
============================================================
Testing frog_hop...
============================================================
[PASS] frog_hop initialized successfully
[PASS] frog_hop ran 60 frames without errors
============================================================
Testing neon_tank...
============================================================
[PASS] neon_tank initialized successfully
[PASS] neon_tank ran 60 frames without errors

FINAL RESULTS
============================================================
  Engine Core Imports: PASS
  Frog Hop: PASS
  Neon Tank: PASS
============================================================
```

---

## 🚀 Roadmap

### Completed

- [x] Runtime Core & Scene Tree
- [x] AABB Collision System (Layer/Mask, Triggers)
- [x] CircleCollider2D (Circle-AABB & Circle-Circle narrow phase)
- [x] PhysicsBody2D with axis-separation and float precision
- [x] Engine-level Gravity and Impulse support
- [x] Engine-Agnostic Player Controller (Level 4)
- [x] Behavioral State Machine (Level 5)
- [x] Tweening & Easing system (Level 6)
- [x] Particle System & Sprite Rendering (Level 6)
- [x] UI & Event Propagation Framework (Level 7)
- [x] **TilemapNode**: Baked surfaces, auto-collision, streaming, parallax (Level 1)
- [x] **Frog Hop**: Full side-scrolling platformer with JSON-driven tilemap levels
- [x] Sound & Music Layer
- [x] Polygon collision support
- [x] TMX format support in `TilemapNode`

### Up Next

---

## 📄 License

This project is licensed under the MIT License.
