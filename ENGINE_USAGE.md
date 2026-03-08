# Engine Usage Guide

## Overview

The PyEngine 2D engine provides a layered architecture for building 2D games in pure Python. This guide walks you through using the engine, its core features, and building a simple game step-by-step.

---

## Core Engine Components

- **Engine** – The main entry point. Handles the game loop, timing, and systems.
- **Renderer2D** – Scene-aware renderer supporting frustum culling, z-index sorting, and debug overlays. Used automatically by the `Engine`.
- **Node2D** – Base class for all 2D objects. Handles transform propagation (position, scale).
- **Camera2D** – Viewport controller. Set `Node2D.camera = my_camera` to enable culling.
- **PhysicsBody2D** – Level 3 physics body designed for dynamic character controllers (e.g. platformers).
- **PhysicsWorld2D & RigidBody2D** – Advanced sub-stepped physics simulation components for elastic momentum, mass, and rigid constraints (pendulums).
- **CollisionWorld** – Manages colliders and performs AABB/SAT shape checks.
- **InputSystem** – Accessible via `Engine.instance.input`. Handles keyboard signals.
- **AudioManager** – Accessible via `Engine.instance.audio`. Controls SFX and Music.
- **TweenManager** – Component for property interpolation (juice).
- **ParticleEmitter2D** – Component for visual effects like dust or sparks.
- **UIControl** – Base class for UI elements (`Label`, `Button`, `Containers`).
- **EventSystem** – Hierarchically processes and consumes input events (like clicks).

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
   This launches "The Great Adventure" which showcases all engine layers.

---

## Creating a New Game

### 1. Initialize the Engine

Consolidate all engine imports from the top-level API:

```python
from src.pyengine2D import *

def main():
    engine = Engine("My New Game", 1024, 600)
    root = Node2D("Root")

    # Run the engine
    engine.run(root)

if __name__ == "__main__":
    main()
```

### 2. Add a Player Entity

```python
# Create a player body
player_col = Collider2D("Player_Col", -20, -20, 40, 40)
player = PhysicsBody2D("Player", 100, 300, player_col, collision_world)

# Add visuals
vis = RectangleNode("PlayerVis", -20, -20, 40, 40, (0, 255, 200))
player.add_child(vis)
player.add_child(player_col)

root.add_child(player)
```

### 3. Add Collectibles (Coins)

```python
# Using Area2D for trigger detection
coin = Area2D("Coin", 200, 300, 30, 30)
coin_vis = CircleNode("CoinVis", 0, 0, 15, (255, 215, 0))
coin.add_child(coin_vis)

root.add_child(coin)
```

### 4. Set Up a Simple Level

Create static platforms by using `Collider2D` with `is_static=True`:

```python
platform = Node2D("Platform", 0, 400)
col = Collider2D("Platform_Col", 0, 0, 800, 32, is_static=True)
vis = RectangleNode("Platform_Vis", 0, 0, 800, 32, (100, 100, 100))

platform.add_child(col)
platform.add_child(vis)
root.add_child(platform)
```

### 5. Use the TileMap System

Instead of placing platforms manually, you can use the **`TilemapNode`** to load JSON-driven levels:

```python
from src.pyengine2D.scene.tilemap import TilemapNode

tilemap = TilemapNode("Level")
tilemap.load_from_json("src/games/frog_hop/maps/map_data.json")
# Or load a Tiled TMX file directly:
# tilemap.load_from_tmx("src/games/frog_hop/maps/map_data.tmx")
root.add_child(tilemap)
```

The JSON map file is created using the **`draw2d.py`** map editor:

```
python draw2d.py
```

- **Left-click** to draw tiles, **Right-click** to erase.
- Scroll wheel to **Zoom**, Space+Click or Middle-click to **Pan**.
- Press **[S]** to save your map (File Explorer dialog opens to choose name/path).
- Press **[L]** to load an existing `.json` map.

The exported JSON automatically includes:

- `offset_x` / `offset_y` for correct world-space positioning (supports negative coords).
- Auto-tiled edges (Top-Left, Top-Mid, Top-Right, Underground dirt).
- Tileset reference with `scale` factor for pixel-art upscaling.

### 6. Advanced Simulation (Elastic Physics)

If you aren't building a traditional game and want native Rigid Body simulations (like a Newton's Cradle):

```python
from src.pyengine2D.physics.physics_world_2d import PhysicsWorld2D
from src.pyengine2D.physics.rigid_body_2d import RigidBody2D
from src.pyengine2D.physics.distance_constraint import DistanceConstraint

# 1. Provide an isolated Physics solver set to divide updates into 10 rapid sub-steps for extreme constraint stability
sim_world = PhysicsWorld2D("SimulationWorld", gravity_y=800.0, sub_steps=10)
root.add_child(sim_world)

# 2. Add an anchor point and a hanging pendulum ball
anchor_x, anchor_y = 500, 100
ball_col = CircleCollider2D("BallCol", 0, 0, radius=20)
ball = RigidBody2D("Pendulum", anchor_x, anchor_y + 200, collider=ball_col, collision_world=collision_world, mass=1.0)
rope = DistanceConstraint("Rope", anchor_x, anchor_y, ball, length=200)

sim_world.add_child(ball)
sim_world.add_child(rope)
```

### 7. Add a User Interface

You can build HUDs and Menus using nested UI Container nodes:

```python
# Create a root UI Control to span the screen
ui_root = UIControl("UIRoot", width=1024, height=600)

# Add a vertical box for layout
vbox = VBoxContainer("MainVBox", x=10, y=10, width=200, spacing=10)
ui_root.add_child(vbox)

# Add a label bound to player health using Data Binding
hp_label = Label("HPLabel", text="HP: 100")
hp_label.bind_text(player, "health", formatter=lambda v: f"HP: {v}")
vbox.add_child(hp_label)

# Add a button with a click event
btn = Button("Btn", text="Click Me!", width=120, height=40)
btn.on_pressed.connect(lambda: print("Clicked!"))
vbox.add_child(btn)

root.add_child(ui_root)
```

---

## Asset Loading

Load images directly via `SpriteNode` or `AnimatedSprite`:

```python
# Static Image
player_sprite = SpriteNode("PlayerSprite", "assets/player.png", centered=True)

# Animated Sprite Sheet
anim_sprite = AnimatedSprite("PlayerAnim", "assets/player_sheet.png", 64, 64)
anim_sprite.add_animation("idle", [0, 1, 2, 3], frame_duration=0.2)
anim_sprite.play("idle")
```

---

## Audio and Music

Play sound effects or stream background music seamlessly using the Engine's `audio` manager:

```python
# Load once during setup
Engine.instance.audio.load_sound("jump", "assets/jump.wav")

# Play anywhere
Engine.instance.audio.play_sound("jump")

# Stream background music globally
Engine.instance.audio.play_music("assets/bgm.ogg", loops=-1)
```

---

## Common Patterns

- **State Machines** – Use `StateMachine` to decouple behavior from movement logic.
- **Signals** – Connect to engine hooks like `on_collision_enter` or custom signals using `get_signal("name").connect(callback)`.
- **Debug Visualization** – Press **F1** during runtime to toggle collider outlines.
- **Juice** – Use `TweenManager` to animate properties:
  ```python
  tweens.interpolate(node, "scale_x", 1.0, 1.2, 0.2, Easing.quad_out)
  ```

---

## FAQ

**Q:** My collisions aren't working?
**A:** Ensure your `Collider2D` has the correct `layer` and `mask` set, and is added as a child of a `PhysicsBody2D` or monitored by `CollisionWorld`.

**Q:** How do I handle input?
**A:** Access it via `Engine.instance.input.is_key_pressed(Keys.LEFT)`.

---

## Verification Checklist

- [x] Engine initializes without errors.
- [x] Player can move left/right and jump.
- [x] Coins are collected and emit a signal.
- [x] Platform collision prevents falling through.
- [x] Game runs at a stable frame rate.

---

_This guide is kept up-to-date with the latest engine version. Refer to the source code for deeper implementation details._
