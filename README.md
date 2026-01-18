# PyEngine 2D

A lightweight, purely Python-based 2D game engine built incrementally.

## Features
- **Node System**: Godot-like hierarchical scene graph (`Node`, `Node2D`).
- **Entity Component System (ECS)**: Included in `src/ecs` (optional/legacy).
- **Physics**: Vertical gravity, jumping, and AABB collision detection.
- **Camera**: Smooth 2D camera following the player.
- **Debug Tools**: Visual overlay for colliders and Stats HUD (FPS, Object count).

## Setup
1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install pygame
   ```

## Running
Execute the main script:
```bash
python main.py
```

## Controls
- **Arrow Keys**: Move Left/Right.
- **Up Arrow**: Jump.
- **Esc/Close Window**: Quit.

## Project Structure
- `src/scene`: Core Node system classes.
- `src/scene/collision`: Collision detection logic.
- `src/scene/ui`: User Interface elements.
- `src/components`, `src/systems`: ECS implementation (unused in main demo).
