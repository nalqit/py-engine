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
|   8   | Tilemap Level Editor    |   ✅   |

### Level 0 — Runtime Core

- Game loop, delta timing, base `Node` class, scene tree hierarchy.

### Level 1 — Scene System

- Parent/child transform propagation, local vs global position, update lifecycle.
- **`TilemapNode`**: Multi-layer tilemap with cached baked surfaces, auto-collision generation, viewport streaming, and parallax support.

### Level 2 — Collision System

- **Collider2D**: Scale-aware AABB — dimensions, layer/mask, static/trigger flags, optional `visible` debug overlay.
- **CircleCollider2D**: Circle-circle and circle-AABB colliders.
- **CollisionWorld**: Float-precision AABB overlap checks with MTV resolution + layer/mask filtering.

### Level 3 — Physics Layer

- **PhysicsBody2D**: Per-axis move-and-collide with float precision.
- **Gravity** and **Impulses**: `apply_impulse(ix, iy)` for instantaneous velocity changes.

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
│   ├── collision/         # Collider2D, CircleCollider2D, CollisionWorld
│   ├── core/              # Engine, Events, Input
│   ├── fsm/               # Finite State Machine base classes
│   ├── physics/           # PhysicsBody2D
│   ├── rendering/         # Renderer, SurfaceCache
│   ├── scene/             # Node, Node2D, Camera2D, TilemapNode, AnimatedSprite
│   ├── time/              # DeltaTime, Scheduling
│   ├── ui/                # UIControl, Containers, Widgets, Data Binding
│   └── utils/             # Helper structures
│
└── games/                 # Game examples
    ├── frog_hop/          # Side-scrolling platformer (Ninja Frog + Fruits)
    │   ├── entities/      # Player, Fruit
    │   ├── maps/          # JSON tilemaps created with draw2d.py
    │   ├── level.py       # Level builder (loads TilemapNode from maps/)
    │   └── main.py
    ├── neon_heights/
    ├── neon_odyssey/
    └── neon_tank/

draw2d.py                  # Infinite 4-Quadrant Map Editor → JSON tilemaps
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
6. **Level Editor**: `python draw2d.py` → draw → **[S]** → save to `src/games/frog_hop/maps/`

See [ENGINE_USAGE.md](ENGINE_USAGE.md) for a detailed API guide.

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
- [x] **draw2d.py**: Infinite 4-quadrant map editor with Zoom, Pan, Save/Load (Level 8)
- [x] **Frog Hop**: Full side-scrolling platformer with JSON-driven tilemap levels

### Up Next

- [ ] Sound & Music Layer
- [ ] Polygon collision support
- [ ] TMX format support in `TilemapNode`

---

## 📄 License

This project is licensed under the MIT License.
