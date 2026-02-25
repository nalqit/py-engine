# PyEngine 2D

PyEngine 2D is a lightweight, purely Python-based 2D game engine built with **Pygame**, inspired by Godot's scene and node system. It focuses on architectural clarity, explicit systems, and educational value.

> [!NOTE]
> This project is an experimental prototype focusing on learning and extensibility rather than raw performance.

---

## 🟢 System Status

The engine is built using a **layered architecture**, with each level stabilized before the next is added.

| Level | Layer                   | Status |
| :---: | :---------------------- | :----: |
|   0   | Runtime Core            |   ✅   |
|   1   | Scene System            |   ✅   |
|   2   | Collision System        |   ✅   |
|   3   | Physics Layer           |   ✅   |
|   4   | Gameplay Layer          |   ✅   |
|   5   | State Layer (FSM)       |   ✅   |
|   6   | Juice & Animation Layer |   ✅   |

### Level 0 — Runtime Core

- Game loop, delta timing, base `Node` class, scene tree hierarchy.

### Level 1 — Scene System

- Parent/child transform propagation, local vs global position, update lifecycle.

### Level 2 — Collision System

- **Collider2D**: Scale-aware AABB data — dimensions, layer/mask, static/trigger flags.
- **CollisionResult**: Structured dataclass with collision normal and penetration depth.
- **CollisionWorld**: Float-precision AABB overlap checks with MTV resolution. Layer/mask filtering, trigger support, and epsilon-inclusive edge detection.

### Level 3 — Physics Layer

- **PhysicsBody2D**: Generic body with per-axis move-and-collide float-precision resolution.
- **Gravity**: Engine-level `use_gravity` flag with configurable `gravity` constant.
- **Impulses**: `apply_impulse(ix, iy)` for instantaneous velocity changes.
- **Coordinate-Space Consistency**: Precise conversion between local and global spaces during resolution.

### Level 4 — Gameplay Layer

- **PlayerController**: Engine-agnostic controller that maps abstract input to physics intentions.
- **Movement**: Acceleration-based horizontal movement with friction and max speed clamping.
- **Ground Detection**: Non-invasive pure probe check (downward offset) via `CollisionWorld`.

### Level 5 — State Layer (FSM)

- **PlayerStateMachine**: Manages behavioral states (Idle, Run, Jump, Fall).
- **Lightweight States**: Concrete state objects (`IdleState`, `RunState`, etc.).

### Level 6 — Juice & Animation Layer

- **Tween System**: Powerful property interpolation with Easing functions for smooth "Juice."
- **Particle System**: `ParticleEmitter2D` for visual effects like jump dust or sparks.
- **Sprite Animation**: `SpriteNode` for static assets and `AnimatedSprite` for frame-based sheets.
- **Parallax Backgrounds**: Multi-layered backgrounds for environmental depth.
- **Unified Engine API**: Consolidated engine submodules into a single top-level entry point with explicit export management for zero-dependency style game development.

---

## ✨ Core Architecture

### 🍭 Juice & Feel (Level 6)

- **Tweening Engine**: Smoothly animate any property (scale, position, alpha) using `TweenManager`.
- **Scale-Aware Hitboxes**: Physics and Collisions automatically adapt when objects squash or stretch.
- **Visual Polish**: Procedural effects (bobbing coins, landing dust) integrated directly into game logic.

### 🎮 Gameplay & Control (Levels 4-5)

- **Engine-Agnostic Controllers**: The `PlayerController` does not import `pygame`, receiving an abstract `input_state` dictionary instead.
- **Finite State Machine**: Decouples "what the player is doing" from "how the player moves."

### ⚙️ Physics & Collision (Levels 2-3)

- **Axis-Separated Resolution**: X is resolved, then Y, with forced transform synchronization between steps.
- **Coordinate Integrity**: Robust handling of local-to-global translations to prevent "teleportation" glitches.
- **Float Precision**: Uses exact float boundaries and inclusive epsilon bounds for reliable contact detection (e.g., box pushing, springs).

---

## 📂 Project Structure

For a detailed breakdown of every file, see **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)**.

```text
src/
├── engine/                # Core engine (reusable)
│   ├── scene/             # Node system, Camera, Tween, Particles, Sprites
│   ├── collision/         # Collider2D, Area2D, CollisionWorld
│   ├── physics/           # PhysicsBody2D
│   └── ui/                # StatsHUD
│
├── game/                  # Main Game Example ("The Great Adventure")
│   ├── entities/          # Player, NPC, Box, Coin
│   ├── player_controller.py
│   ├── player_fsm.py
│   ├── player_states.py
│   └── main.py
│
├── games/                 # Minimal Engine-Only Examples
│   ├── spring_bounce/     # Vertical Platformer (Trigger/Spring mechanics)
│   ├── spike_rain/        # Survival Game (Falling hazards, Game loop reset)
│   └── box_pusher/        # Puzzle Game (Robust Box Pushing mechanics)
│
├── tests/                 # Unit tests for all layers
```

---

## ⚙️ Setup

1. **Python**: 3.10+
2. **Dependencies**: `pip install pygame`
3. **Engine Import Strategy**: Games can now use `from src.engine import *` to access all engine systems from a single, consolidated entry point.
4. **Run Main Game**: `python -m src.game.main`
5. **Run Examples**:
   - `python -m src.games.spring_bounce.main`
   - `python -m src.games.spike_rain.main`
   - `python -m src.games.box_pusher.main`
6. **Debug**: Press **F1** in-game to toggle collider visualization.

## Engine Usage Guide

See [ENGINE_USAGE.md](ENGINE_USAGE.md) for a detailed guide on using the engine and building games.

---

## 🚀 Roadmap

### Completed

- [x] Runtime Core & Scene Tree.
- [x] AABB Collision System (Layer/Mask, Triggers).
- [x] Generic PhysicsBody2D with axis-separation and float precision.
- [x] Engine-level Gravity and Impulse support.
- [x] Engine-Agnostic Player Controller (Level 4).
- [x] Behavioral State Machine (Level 5).
- [x] Tweening & Easing system (Level 6).
- [x] Particle System & Sprite Rendering (Level 6).
- [x] Scale-Aware Physics Sync.
- [x] World Overhaul (Structured Map & Unified Background).
- [x] **Engine-Only Examples**: Created minimal isolated games to prove engine independence.
- [x] **Circular Collision Support**: Implemented `CircleCollider2D` with Circle-Circle and Circle-AABB narrow-phase resolution.
- [x] **Main Game Refactor**: Rebuilt "The Great Adventure" to use clean architecture (FSM, Controllers, localized TweenManagers).
- [x] **Unified Engine API**: Consolidated engine submodules into a single top-level entry point (`src/engine/__init__.py`) with explicit export management.

### Up Next

- [ ] Sound & Music Layer.
- [ ] Polygon collision support.
- [ ] Tilemap level loader (JSON/TMX).

---

## 📄 License

This project is licensed under the MIT License.
