# Frog Hop Architecture

Frog Hop is a 2D side-scrolling platformer showcasing the engine's physics wrapper, state management, and modular entity design. The game relies heavily on data-driven map parsing and a robust signal-based event system to decouple game objects.

## Core Flow

The main entry point is `FrogHop` in `main.py`. It uses a Finite State Machine tracking one of four modes: `MENU`, `PLAYING`, `GAME_OVER`, and `VICTORY`.

During `PLAYING`, the `update()` loop monitors fruit collection. When all fruits listed in the level's `map_data_*.json` configuration are collected, `build_level` clears the current `World` node, increments the level index, and reinstantiates all dependencies recursively.

## The Signal System

To avoid God Objects or tight coupling, Frog Hop passes key events through the engine's `SignalMixin`.

For instance, when an enemy overlaps the player:

1. `take_damage()` is called on the Player.
2. The Player’s internal health is decremented.
3. The Player executes `emit_signal("on_health_changed")`.
4. `main.py`, which subscribed to this signal during initialization via `lambda **kw: setattr(self.hud, ...)`, catches it and updates the HUD object without the player ever needing a reference to the HUD.

## Physics and Layering

All physical objects (`Player`, `Enemy`, `Trap`) inherit from `PhysicsBody2D` or `Node2D` with attached `Collider2D` components.

The collision logic dictates interaction rules cleanly:

- **Player Layer:** Can collide with `wall` and `pickup`.
- **Enemy Layer:** Has probes targeting the `wall` layer. An enemy reverses direction if a front-placed "wall probe" intersects geometry, or if a bottom-placed "ledge probe" stops intersecting geometry (meaning there is no floor ahead).
- **Trap Layer:** Trigger nodes (like Fire or Spikes) cast `query_rect` bounds searching specifically for the `player` layer.

### Stomp Mechanics

When the player collides with an enemy, the event is analyzed:

- If the player's `velocity_y > 0` (falling) and their Y-coordinate is sufficiently above the enemy, the `Enemy.on_stomp()` method triggers.
- The player is given a `velocity_y = -600`.
- The enemy enters a deferred death state (`_death_timer`) to avoid mid-iteration list removal exceptions.

## Environments

Level geometries construct visually via `TilemapNode` parsing standard JSON mappings, overlaying items and enemies mapped in `level.py`. Parallax depth is faked natively through `BackgroundLayer` nodes running at varied `scroll_factor` values (e.g. `0.2` and `0.5`).
