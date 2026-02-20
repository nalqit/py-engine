# PyEngine 2D - Comprehensive Project Overview

This document provides a clear explanation of every file in the project, organized by layer and responsibility.

## 🛠️ Engine Core (`src/engine/`)

The engine is built on a modular "Node" architecture, similar to major game engines like Godot.

### 🌐 Scene Management (`src/engine/scene/`)
- **[node.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/node.py)**: The elemental base class. Handles parent-child relationships and recursive updates/renders.
- **[node2d.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/node2d.py)**: Inherits from `Node`. Adds 2D properties like `local_x`, `local_y`, and scaling. It caches global positions for performance.
- **[rectangle_node.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/rectangle_node.py)**: A basic visual node that draws a colored rectangle.
- **[sprite_node.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/sprite_node.py)**: Renders static PNG images. Supports scaling and centering.
- **[animated_sprite.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/animated_sprite.py)**: Handles frame-based animations from sprite sheets.
- **[camera2d.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/camera2d.py)**: Controls the viewport. It follows a target and offsets the world rendering so the target stays centered.
- **[parallax.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/parallax.py)**: Implements multi-layered backgrounds where layers move at different fractions of the camera's speed to create a sense of depth.
- **[particles.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/particles.py)**: A simple system for spawning and updating short-lived visual effects (like dust or sparks).
- **[tween.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/scene/tween.py)**: A powerful animation tool used to smoothly interpolate properties (like scale or position) over time with easing effects ("Juice").

### 💥 Collision Layer (`src/engine/collision/`)
- **[collider2d.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/collision/collider2d.py)**: Defines the boundaries (AABB) of an object. It is now "scale-aware," meaning its hitbox matches visual squashing/stretching.
- **[collision_world.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/collision/collision_world.py)**: The central manager that checks for overlaps between colliders and resolves penetrations.
- **[area2d.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/collision/area2d.py)**: A special collider that detects overlaps without causing a physical stop (used for coins/triggers).

### ⚙️ Physics Layer (`src/engine/physics/`)
- **[physics_body_2d.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/physics/physics_body_2d.py)**: Provides mass-like behavior, including gravity and velocity-based motion with automatic collision resolution.

### 🖥️ UI Layer (`src/engine/ui/`)
- **[stats_hud.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/engine/ui/stats_hud.py)**: Displays real-time debug information (FPS, entity count) on the screen.

---

## 🎮 Game Logic (`src/game/`)

This directory contains the actual "content" of the game using the engine's tools.

### 🧩 Entities (`src/game/entities/`)
- **[player.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/game/entities/player.py)**: The main character. Orchestrates input, FSM states, particle effects, and "Juice" (squash & stretch).
- **[npc.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/game/entities/npc.py)**: A basic non-player character that stands in the world.
- **[box.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/game/entities/box.py)**: A simple physics-driven object that can be pushed.
- **[coin.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/game/entities/coin.py)**: A collectable item that uses `Area2D` for detection and `TweenManager` for a bobbing animation.

### 🚦 Behaviors & Control
- **[player_controller.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/game/player_controller.py)**: Translates raw keyboard inputs into movement intentions (acceleration, friction, jumping).
- **[player_fsm.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/game/player_fsm.py)**: The Finite State Machine that manages high-level logic (e.g., "Am I in the Idle state or Jump state?").
- **[player_states.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/game/player_states.py)**: Detailed logic for individual player states like Idle, Running, and Jumping.

### 🚀 Entry Point
- **[main.py](file:///c:/Users/dell/Desktop/try3(gpt prompts)/src/game/main.py)**: The "glue" that binds everything. It initializes Pygame, builds the world map, sets up the parallax background, and runs the main loop.

---

## 🧪 Testing & Docs
- **[tests/](file:///c:/Users/dell/Desktop/try3(gpt prompts)/tests/)**: Comprehensive unit tests for physics, collision, and state logic.
- **[README.md](file:///c:/Users/dell/Desktop/try3(gpt prompts)/README.md)**: Quick start and project orientation.
- **[ARCHITECTURAL_LAYERS.md](file:///c:/Users/dell/Desktop/try3(gpt prompts)/ARCHITECTURAL_LAYERS.md)**: Detailed breakdown of the technical design philosophy.
