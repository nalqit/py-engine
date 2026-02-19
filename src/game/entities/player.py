import pygame
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.game.player_controller import PlayerController
from src.game.player_fsm import PlayerStateMachine


class Player(PhysicsBody2D):
    """Player entity — Level 5: with gameplay controller and FSM."""

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.controller = PlayerController()
        self.state_machine = PlayerStateMachine(self)

    def update(self, delta):
        # 1. Capture abstract input (Engine-Agnostic requirement)
        keys = pygame.key.get_pressed()
        input_state = {
            "move_left": keys[pygame.K_LEFT] or keys[pygame.K_a],
            "move_right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            "jump": keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP],
        }

        # 2. Update gameplay logic (Intentions: velocity changes, impulse)
        self.controller.update(self, delta, input_state)

        # 3. Proceed with physics integration (Position resolution, gravity)
        super().update(delta)

        # 4. Update behavioral state (Observation: what am I doing now?)
        self.state_machine.update(delta)

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
