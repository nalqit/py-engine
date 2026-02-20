import pygame
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.game.player_controller import PlayerController
from src.game.player_fsm import PlayerStateMachine
from src.engine.scene.particles import ParticleEmitter2D


class Player(PhysicsBody2D):
    """Player entity — Level 5: with gameplay controller and FSM."""

    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.controller = PlayerController()
        self.state_machine = PlayerStateMachine(self)
        
        # Add a particle emitter for jump/land effects
        self.particles = ParticleEmitter2D("PlayerParticles")
        self.add_child(self.particles)
        
        self.score = 0

    def jump_effect(self):
        # Emit dust particles at the player's feet
        gx, gy = self.get_global_position()
        self.particles.emit(gx + 25, gy + 50, count=15, 
                            speed_range=(20, 80), 
                            angle_range=(200, 340), # Upwards-ish
                            color=(150, 150, 150))

    def update(self, delta):
        # 1. Capture abstract input (Engine-Agnostic requirement)
        keys = pygame.key.get_pressed()
        input_state = {
            "move_left": keys[pygame.K_LEFT] or keys[pygame.K_a],
            "move_right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            "jump": keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP],
        }

        # 2. Update gameplay logic (Intentions: velocity changes, impulse)
        old_vel_y = self.velocity_y
        self.controller.update(self, delta, input_state)
        
        # Check for jump to trigger effect
        # We check the controller's grounded state
        if input_state["jump"] and self.controller.is_grounded and self.velocity_y < 0:
             self.jump_effect()

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
