# Core Game Framework Architecture

The `src/game/` folder demonstrates a decoupled, scalable approach to building an advanced game structure over PyEngine2D. It breaks monolithic classes into smaller, composable units using State Machines and Controllers.

## 1. Composition over Inheritance

Instead of `player.py` containing hundreds of lines governing input, physics, animations, and states, the logic is decoupled into sub-components.

For example, the new `Player` class owns three core delegates:

1. **`PlayerController`:** Handles input ingestion, acceleration calculations, friction algorithms, and physics probes (wall/ground detection).
2. **`PlayerFSM` (Finite State Machine):** An orchestrator that manages transitions between states.
3. **`PlayerState` classes:** Concrete states (`IdleState`, `RunState`, `JumpState`, `FallState`) that own specific branch logic.

### Controller Logic (`player_controller.py`)

`PlayerController` abstracts the raw input state dictionary provided by the engine.

- It applies a smoothing acceleration (`player.velocity_x += move_dir * self.acceleration * delta`) mapped against a `max_speed` cap.
- It applies a deceleration `friction` if no input is detected.
- It runs an optimized spatial `query_rect` beneath the player looking for `wall` or `box` layers to flip `self.is_grounded`.

### State Machine Workflow (`player_states.py`)

The logic branches are kept incredibly lean.
For instance, the `IdleState` simply checks the Controller's ground state. If it falls, it pushes the `FallState` to the FSM. If horizontal velocity passes a baseline threshold, it pushes `RunState`.

```python
class IdleState(PlayerState):
    def update(self, delta):
        if not self.player.controller.is_grounded:
            self.sm.change_state("FallState")
            return

        if abs(self.player.velocity_x) >= 10.0:
            self.sm.change_state("RunState")
```

This prevents the classic problem of deep, nested `if/else` statements handling animations and jump vectors simultaneously.

## 2. Main Module Abstraction

The `main.py` entry point acts merely as an assembly factory.
It defines the `Root` node, registers the `CollisionWorld`, and instantiates `LevelManager`. Dynamic actors like `Coin`, `Enemy`, and `Box` are created and linked to the `World` container. Instead of hard-wiring HUD updates directly into the player loop, `main.py` simply listens to them and applies them via the Engine's `SignalMixin` pattern:

```python
player.get_signal("on_score_changed").connect(lambda score: hud.on_score_changed(score))
```
