# Project Editing Guide (PyEngine 2D)

This file is a practical, code-first guide to help anyone understand this repository quickly and edit it safely.

## 1) What this project is

- A Python 2D engine built on `pygame`, inspired by Godot-style nodes/scenes.
- Main reusable engine code lives in `src/pyengine2D/`.
- Example games live in `src/game/` and `src/games/`.
- There is also a separate Flutter prototype editor app in `src/the_editor/`.

## 2) Quick run commands

- Install runtime dependency:
  - `pip install pygame`
- Run example games:
  - `python -m src.game.main`
  - `python -m src.games.frog_hop.main`
  - `python -m src.games.neon_heights.main`
  - `python -m src.games.neon_odyssey.main`
  - `python -m src.games.neon_tank.main`
  - `python -m src.games.newtons_cradle.main`
- Run tests:
  - `python -m pytest tests -v`
  - or `python run_all_tests.py`

## 3) Core architecture at a glance

Engine runtime (`src/pyengine2D/core/engine.py`) drives a fixed-timestep loop:

1. Poll input/events (`begin_frame`)  
2. Process UI events (`EventPropagationSystem`)  
3. Run fixed logic steps (`root.update_transforms()` then `root.update(fixed_dt)`)  
4. Render with `Renderer2D` (`scene_renderer.draw`)  
5. Apply scene stack changes (`SceneManager.process_pending_changes`)  

Key layers:

- Scene graph: `Node` -> `Node2D` (`src/pyengine2D/scene/node.py`, `src/pyengine2D/scene/node2d.py`)
- Collision: `Collider2D`, `CollisionWorld` (`src/pyengine2D/collision/`)
- Physics: `PhysicsBody2D` and `RigidBody2D`/`PhysicsWorld2D` (`src/pyengine2D/physics/`)
- Rendering: `Renderer` + high-level `Renderer2D` (`src/pyengine2D/core/renderer.py`, `src/pyengine2D/rendering/renderer2d.py`)
- UI: `UINode`, widgets, layout containers, event propagation (`src/pyengine2D/ui/`)
- Signals/events: `Signal`, `SignalMixin` (`src/pyengine2D/core/signal.py`)

## 4) Where to edit for common changes

### A) Add or change gameplay movement

- Kinematic platformer behavior: edit `src/pyengine2D/physics/physics_body_2d.py`.
- Higher-level player behavior in sample game:
  - `src/game/player_controller.py`
  - `src/game/player_fsm.py`
  - `src/game/player_states.py`
  - `src/game/entities/player.py`

### B) Change collisions/hit detection

- Broad + narrow-phase logic: `src/pyengine2D/collision/collision_world.py`
- Collider shapes:
  - AABB: `src/pyengine2D/collision/collider2d.py`
  - Circle: `src/pyengine2D/collision/circle_collider2d.py`
  - Polygon SAT: `src/pyengine2D/collision/polygon_collider2d.py`

### C) Change rendering/culling/debug overlays

- Main scene traversal/culling/sorting: `src/pyengine2D/rendering/renderer2d.py`
- Primitive/text rendering wrapper: `src/pyengine2D/core/renderer.py`
- Tilemap bake/chunk render: `src/pyengine2D/scene/tilemap.py`

### D) UI work

- Base UI behavior/layout: `src/pyengine2D/ui/ui_node.py`
- Widgets: `src/pyengine2D/ui/widgets.py`
- Containers: `src/pyengine2D/ui/containers.py`
- Event flow and input consume behavior: `src/pyengine2D/ui/event_system.py`
- Data binding: `src/pyengine2D/ui/data_binding.py`

### E) Scene save/load

- Engine serializer: `src/pyengine2D/scene/scene_serializer.py`
- Scene stack transitions: `src/pyengine2D/scene/scene_manager.py`

### F) Level authoring

- Standalone map editor: `draw2d.py`
- Frog Hop level configs and map hookup: `src/games/frog_hop/level.py`
- Frog Hop map data files: `src/games/frog_hop/maps/*.json`

## 5) Example games in this repo

- `src/game/`: "clean game" demo with controller + FSM split.
- `src/games/frog_hop/`: most complete platformer example (multi-level, enemies, traps, tilemap pipeline).
- `src/games/neon_heights/`: procedural vertical jumper, loads from `.scene` and custom types.
- `src/games/neon_odyssey/`: platformer showcase with moving platforms, collectibles, HUD via signals.
- `src/games/neon_tank/`: top-down shooter demo (tank aim/shoot/spawn enemies).
- `src/games/newtons_cradle/`: rigid-body + constraints simulation.
- `src/games/test_game/`: minimal scene-load example.

## 6) Tests and quality checks

The test suite in `tests/` is broad and documents intended behavior:

- Engine/frame/timing/input: `tests/test_engine_features.py`, `tests/test_input_enhanced.py`
- Collision/physics/gameplay/FSM: `tests/test_collision_system.py`, `tests/test_physics_layer.py`, `tests/test_gameplay_layer.py`, `tests/test_state_layer.py`
- Rendering/UI/events: `tests/test_renderer2d.py`, `tests/test_ui_layout.py`, `tests/test_widgets.py`, `tests/test_event_propagation.py`
- Performance/optimization: `tests/test_optimizations.py`, `tests/test_validation_plan.py`, `tests/test_physics_benchmark.py`
- Scene/editor-related tests: `tests/test_scene_io.py`, `tests/test_scene_importer.py`, `tests/test_editor_model.py`

Important repo reality:

- Several tests/docs reference `tools/editor/...`, but that directory is not present in this workspace.
- A separate editor prototype exists under `src/the_editor/` (Flutter), which is different from the PyQt editor docs.

## 7) Practical editing rules for this codebase

- Keep `game`/`games` code engine-facing (most tests enforce architecture boundaries).
- Use layer/mask carefully on colliders; many behaviors depend on exact layer strings.
- After moving objects manually, update transforms/cache where required (several entities do this explicitly).
- Prefer adding gameplay logic in game modules, not in low-level engine modules, unless you are fixing an engine bug.
- When changing engine internals, run targeted tests first, then `pytest tests -v`.

## 8) Fast orientation map (folder purpose)

- `src/pyengine2D/core/`: engine loop, input, rendering wrapper, signals, audio
- `src/pyengine2D/scene/`: nodes, camera, tilemap, tween, particles, scene management/serialization
- `src/pyengine2D/collision/`: collider shapes, world queries, spatial grid
- `src/pyengine2D/physics/`: kinematic + rigid body simulation and constraints
- `src/pyengine2D/ui/`: UI nodes, widgets, containers, event propagation, data binding
- `src/pyengine2D/rendering/`: scene renderer, batch, caches, atlas
- `src/pyengine2D/utils/`: profiler, asset manager, object pooling, pathfinding
- `src/game/` and `src/games/`: gameplay examples
- `tests/`: expected behavior and regressions
- `draw2d.py`: map editor pipeline entrypoint
- `src/the_editor/`: separate Flutter app

## 9) If you are editing this project for the first time

Suggested sequence:

1. Run one game (`frog_hop` is the most representative).  
2. Read `src/pyengine2D/core/engine.py` and `src/pyengine2D/scene/node2d.py`.  
3. Read `src/pyengine2D/collision/collision_world.py` + `src/pyengine2D/physics/physics_body_2d.py`.  
4. Read the specific game module you want to modify.  
5. Run relevant tests for touched area, then full tests.

This keeps edits safe and aligned with current architecture.
