# Neon Tank Architecture

Neon Tank Area is a top-down, WASD + Mouse Aim shooter demonstrating the engine's 2D math capabilities, collision layers, and dynamic projectile spawning.

## Math & Trigonometry (`entities/tank.py`)

Because the game uses top-down twin-stick style controls, the physics layer employs significant native Python `math` module trigonometric functions:

### Normalizing Diagonal Speed

Diagonal movement (e.g. holding W + D) would normally result in faster movement than strictly horizontal/vertical movement. `PlayerTank` normalizes the input vectors:

```python
mag = math.sqrt(move_vec_x**2 + move_vec_y**2)
if mag > 1.0:
    move_vec_x /= mag
    move_vec_y /= mag
```

### Screen Point aiming

The mouse determines turret rotation in screen-space:

```python
mx, my = inp.get_mouse_pos()
tx, ty = self.get_screen_position()
angle = math.atan2(my - ty, mx - tx)
self.turret.rotation = angle
```

### Rotated Rendering

Rather than a sprite sheet with rotations, the `Turret` node manually draws a rotated polygon targeting the specific mouse `angle` using `math.cos(self.rotation)` and `math.sin(self.rotation)` mapped over 4 coordinate corner vectors.

## Collision Pipeline (`main.py`)

Unlike platformers where `PhysicsBody2D` handles blocking floors intrinsically, collisions in `Neon Tank Arena` trigger specific `on_fixed_update()` logic for top-down elements like projectiles.

A recursion loop gathers all active `Bullet` and `Enemy` instances in the arena, checking scalar distance bounds (`dist = ((bx - ex)**2 + (by - ey)**2)**0.5`).

- If a bullet hits an enemy limit, `enemy.take_damage(1)` is called, and `bullet.destroy()` fires.
- If a player overlaps an enemy distance radius, the player resets.
