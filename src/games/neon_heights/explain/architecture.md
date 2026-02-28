# Neon Heights Architecture

Neon Heights is an endless vertical jumper built using the engine's 2D capabilities. It relies on procedural generation, dynamic camera tracking, and custom wall-jumping mechanics.

## Core Flow

The main game loop in `main.py` revolves around manipulating the camera and generating platforms continuously as the player scales upward.

### Procedural Generation

Instead of loading static maps, the `update()` loop monitors the gap between the player's Y-coordinate and a spawn threshold (`next_spawn_y`):

```python
while self.player.local_y - self.next_spawn_y < 1200:
    # Generate new random platform
    self.next_spawn_y -= self.spawn_interval
```

Simultaneously, older platforms far below the player are destroyed and removed from memory to optimize collision calculations.

## The Rising Void

A dynamic hazard, `RisingVoid`, continuously moves upwards to force player progression.

- Its speed scales dynamically based on the player's maximum achieved height (`self.max_height * 0.5`).
- If the player falls beneath the Void's coordinate threshold, the game resets their position and resets the maximum height.

## Player Mechanics

The player's logic (`entities/player.py`) includes customized platforming specifically for vertical maps:

### Wall Detection & Sliding

Small spatial bounds check the immediate left and right pixels of the player against the `collision_world`.

- If colliding horizontally, `self.is_on_wall` toggles `True`.
- Falling against a wall reduces gravity's effect, capping `velocity_y` at a lower value to simulate wall sliding.

### Wall Jumping

Wall jumps check a state tracker: `self.last_jump_wall_side`.

- Wall jumping applies a strong opposite-X and negative-Y velocity.
- It sets `last_jump_wall_side` to prevent the player from scaling a single vertical wall infinitely; they must bounce back and forth between two walls to climb vertical shafts.

## Dynamic Object Tracking

The "walls" bounding the game area aren't truly infinitely tall. The `update()` orchestrator artificially clamps the `local_y` bounds of `LeftWall` and `RightWall` directly to the `player.local_y`, ensuring the player is always contained regardless of height scale.
