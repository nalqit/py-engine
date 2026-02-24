# Engine Usage Guide

## Overview

The PyEngine 2D engine provides a layered architecture for building 2D games in pure Python. This guide walks you through using the engine, its core features, and building a simple game step‑by‑step.

---

## Core Engine Components

- **Renderer** – Handles drawing sprites, animated sprites, and particles.
- **PhysicsBody2D** – Generic physics body with gravity, impulses, and collision resolution.
- **CollisionWorld** – Manages colliders, performs AABB checks, and returns `CollisionResult`.
- **InputManager** – Abstracts keyboard/gamepad input into a simple dictionary.
- **TweenManager** – Property interpolation for smooth animations (juice).
- **ParticleEmitter2D** – Emits particles for effects like dust or sparks.

---

## Getting Started

1. **Install dependencies**
   ```bash
   pip install pygame
   ```
2. **Run the example game**
   ```bash
   python -m src.game.main
   ```
   This launches the "Great Adventure" demo which showcases all engine layers.

---

## Creating a New Game

### 1. Initialise the Engine

```python
from engine.scene import Scene
from engine.runtime import Engine

engine = Engine()
scene = Scene()
engine.set_root(scene)
```

### 2. Add a Player Entity

```python
from src.game.entities.player import Player
from src.game.player_controller import PlayerController

player = Player()
controller = PlayerController()
player.add_controller(controller)
scene.add_child(player)
```

### 3. Add Collectibles (Coins)

```python
from src.game.entities.coin import Coin

for i in range(5):
    coin = Coin(position=(i*64, 200))
    scene.add_child(coin)
```

### 4. Set Up a Simple Level

Create a `Level` node that contains static platforms:

```python
from engine.collision import Collider2D
from engine.scene import Node2D

platform = Node2D()
platform.position = (0, 400)
platform.add_component(Collider2D(size=(800, 32), static=True))
scene.add_child(platform)
```

### 5. Run the Game Loop

```python
engine.run()
```

The engine will handle delta‑time, physics updates, rendering, and input automatically.

---

## Asset Loading

Place image files in `assets/` and load them via the `ResourceManager`:

```python
from engine.resources import ResourceManager
player_sprite = ResourceManager.load_image('assets/player.png')
```

---

## Common Patterns

- **State Machines** – Use `PlayerStateMachine` to separate behaviour from movement.
- **Event Signals** – Connect to `on_pushed` or `on_collect` signals for custom reactions.
- **Debug Visualisation** – Press **F1** during runtime to toggle collider outlines.

---

## FAQ

**Q:** My sprite doesn’t appear?
**A:** Ensure the image path is correct and the node has a `SpriteNode` component attached.

**Q:** Collisions feel jittery?
**A:** Verify that `use_gravity` is enabled and that you’re not manually moving the node outside the physics step.

---

## Verification Checklist

- [ ] Engine initialises without errors.
- [ ] Player can move left/right and jump.
- [ ] Coins are collected and emit a signal.
- [ ] Platform collision prevents falling through.
- [ ] Game runs at a stable frame rate.

---

_This guide is kept up‑to‑date with the latest engine version. Refer to the source code for deeper implementation details._
