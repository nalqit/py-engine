from src.engine.scene.node2d import Node2D
from src.engine.fsm.state_machine import StateMachine
from src.engine.fsm.idle_state import IdleState


class PhysicsBody2D(Node2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y)

        self.collider = collider
        self.collision_world = collision_world
        self.controller = None
        self.intent_x = 0
        self.intent_y = 0
        self.debug_state_name = ""

        # FSM
        self.state_machine = StateMachine(self)
        self.state_machine.change_state(IdleState(self))

        # Movement
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.speed = 200.0
        self.jump_force = -400.0

        # Gravity (اختياري)
        self.use_gravity = False
        self.gravity = 800.0
        self.on_ground = False

    def update(self, delta):
        # 1. Controller logic
        if self.controller:
            self.controller.update(self, delta)

        # 2. Physics execution logic (Gravity)
        if self.use_gravity and not self.on_ground:
            self.velocity_y += self.gravity * delta

        self.velocity_x = self.intent_x * self.speed

        # jump intent (مرة واحدة)
        if self.intent_y != 0:
            self.velocity_y = self.intent_y

        # 3. Resolve movement & collisions
        dx = self.velocity_x * delta
        dy = self.velocity_y * delta
        self.move_and_collide(dx, dy, delta)

        super().update(delta)

        # 4. Update FSM (After Physics)
        # FSM is descriptive: it looks at what happened (velocity, on_ground)
        # and updates the state accordingly.
        self.state_machine.update(delta)
        self.intent_y = 0
        self.debug_state_name = self.state_machine.current_state.name

    def _check_ground(self):
        return self.collision_world.check_collision(
            self.collider,
            self.local_x,
            self.local_y + 1,
            margin=(-2, 0),
        )

    def move_and_collide(self, dx, dy, delta):
        # --- X axis (Horizontal) ---
        if dx != 0:
            target_x = self.local_x + dx
            hit_x = self.collision_world.check_collision(
                self.collider, target_x, self.local_y, margin=(0, -2)
            )

            if not hit_x:
                self.local_x += dx
            else:
                # Collision detected: Stop movement
                self.velocity_x = 0

        # --- Y axis (Vertical) ---
        # Resolve Y independently.

        # Reset on_ground to False by default (assume air)
        # We will only set it to True if we hit the floor.
        self.on_ground = False

        if dy != 0:
            target_y = self.local_y + dy
            hit_y = self.collision_world.check_collision(
                self.collider, self.local_x, target_y, margin=(-2, 0)
            )

            if not hit_y:
                self.local_y += dy
            else:
                if dy > 0:
                    # Falling and hit floor
                    self.velocity_y = 0
                    self.on_ground = True
                elif dy < 0:
                    # Jumping and hit ceiling
                    self.velocity_y *= -1
                    # on_ground remains False

        # Final ground check
        # Only check if we are NOT jumping (dy >= 0)
        # This prevents on_ground sticking when starting a jump
        if dy >= 0 and self._check_ground():
            self.on_ground = True

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
