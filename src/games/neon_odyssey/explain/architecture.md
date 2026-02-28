# Neon Odyssey Architecture

Neon Odyssey is a showcase of PyEngine's platforming physics wrapper, signals, and entity systems acting on top of static collision bodies like moving platforms. The design pattern focuses on a linear, object-heavy environment.

## 1. Scene Initialization Flow (`main.py`)

The `NeonOdyssey` class is designed sequentially as a developer tutorial structure, numbered by configuration steps:

1. Initialize the `Engine`.
2. Setup the `Root`, `CollisionWorld`, and `World` node hierarchy.
3. Delegate static mapping to a `LevelManager`.
4. Spawn dynamic entities (Player, Moving Platforms, Boxes, Enemies).
5. Load collectibles (`Collectible` / Gems).
6. Setup HUD Observers mapped to `Player` and `Collectible` signals.
7. Tell `Camera2D` to track the `Player` node.

## 2. Dynamic Physics & Entities

The game combines several physics concepts beyond standard static colliders:

- **Pushable Objects:** The `Player` and `Enemy` objects have flags `.pushable = True` or `.can_push = True`, interacting with `Box` objects assigned a `box` layer mask. This pushes physical simulation resolution onto the engine seamlessly.
- **Moving Platforms:** Kinematic bodies that translate horizontally or vertically using an alternating sine wave/timer logic. The engine's collision resolution natively handles the player standing on or pushing against them.

## 3. Signal & Observer Implementation

Neon Odyssey heavily favors observer patterns specifically for UI metrics (Score/Health).

- `player.py` registers `"on_health_changed"` and `"on_died"`.
- `main.py` directly binds `HUD.on_player_health_changed` to these signals via `.connect()`.
- Variables like `health` never need to be directly polled in an `update()` loop. Instead, `take_damage()` selectively fires a push update:

```python
self.health -= amount
self.emit_signal("on_health_changed", self.health)
```

## 4. Particles Effects

Players utilize PyEngine's `ParticleEmitter2D` components.

- A `RunDust` emitter creates small gray trails by rolling a random chance per frame (`< 0.4`) when moving horizontally on solid ground.
- A `JumpBurst` emits a concentrated burst of gray particles straight down when the `SPACEBAR` jump event triggers.
