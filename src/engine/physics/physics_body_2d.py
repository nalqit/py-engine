from src.engine.scene.node2d import Node2D
from src.engine.fsm.state_machine import StateMachine
from src.engine.fsm.idle_state import IdleState
from src.engine.fsm.walk_state import WalkState


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

        # Gravity
        self.use_gravity = False
        self.gravity = 800.0
        self.on_ground = False
        self.hit_ceiling = False
        self.hit_wall_left = False
        self.hit_wall_right = False

    def update(self, delta):
        # Controller logic
        if self.controller:
            self.controller.update(self, delta)

        # Gravity
        if self.use_gravity and not self.on_ground:
            self.velocity_y += self.gravity * delta

        self.velocity_x = self.intent_x * self.speed

        # jump intent
        if self.intent_y != 0:
            self.velocity_y = self.intent_y
        if self.intent_y > 0:
            self.velocity_y += self.gravity * 2 * delta  # fast fall

        # Resolve movement & collisions
        dx = self.velocity_x * delta
        dy = self.velocity_y * delta
        self.move_and_collide(dx, dy, delta)

        super().update(delta)

        # Update FSM
        self.state_machine.update(delta)
        self.intent_y = 0
        self.debug_state_name = self.state_machine.current_state.name

    def move_and_collide(self, dx, dy, delta):
        # Reset flags
        self.on_ground = False
        self.hit_ceiling = False
        self.hit_wall_left = False
        self.hit_wall_right = False

        # --- X axis ---
        target_x = self.local_x + dx
        hit_left = self.collision_world.check_collision(self.collider, self.local_x - 1, self.local_y)
        hit_right = self.collision_world.check_collision(self.collider, self.local_x + 1, self.local_y)

        if hit_left:
            self.hit_wall_left = True
        if hit_right:
            self.hit_wall_right = True

        if dx != 0:
            hit_x = self.collision_world.check_collision(self.collider, target_x, self.local_y, margin=(0, -2))
            if not hit_x:
                self.local_x += dx
            else:
                self.velocity_x = 0
                if dx < 0:
                    self.hit_wall_left = True
                elif dx > 0:
                    self.hit_wall_right = True

        # --- Y axis ---
        target_y = self.local_y + dy
        hit_y_up = self.collision_world.check_collision(self.collider, self.local_x, self.local_y - 1)
        hit_y_down = self.collision_world.check_collision(self.collider, self.local_x, self.local_y + 1)

        if hit_y_down:
            self.on_ground = True
        if hit_y_up:
            self.hit_ceiling = True

        if dy != 0:
            hit_y = self.collision_world.check_collision(self.collider, self.local_x, target_y, margin=(-2, 0))
            if not hit_y:
                self.local_y += dy
            else:
                if dy > 0:
                    self.velocity_y = 0
                    self.on_ground = True
                    self.local_y = hit_y.get_rect().top - self.collider.height
                elif dy < 0:
                    self.velocity_y *= -1
                    self.hit_ceiling = True

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
