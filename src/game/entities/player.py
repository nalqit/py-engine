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
        self.was_grounded = False # Added was_grounded state
        
        # Add a particle emitter for jump/land effects
        self.particles = ParticleEmitter2D("PlayerParticles")
        self.add_child(self.particles)
        
    def _get_tween_manager(self):
        root = self
        while root.parent:
            root = root.parent
        return root.get_node("TweenManager")

    def apply_juice(self, sx, sy, duration=0.2):
        tm = self._get_tween_manager()
        if not tm: return

        vis = self.get_node("PlayerVis")
        if not vis: return

        # Prevent overlapping tweens from fighting and ruining the shape
        if tm.is_tweening(vis, "scale_y"):
            return

        from src.engine.scene.tween import Easing
        
        # Calculate offsets to keep bottom-center anchored
        # Base dimensions are 50x50
        def get_offsets(ts_x, ts_y):
            ox = 50 * (1 - ts_x) / 2
            oy = 50 * (1 - ts_y)
            return ox, oy

        # Squash/Stretch then return to normal
        def reset_scale():
            # Reset Visuals
            tm.interpolate(vis, "scale_x", vis.scale_x, 1.0, duration, Easing.quad_out)
            tm.interpolate(vis, "scale_y", vis.scale_y, 1.0, duration, Easing.quad_out)
            tm.interpolate(vis, "local_x", vis.local_x, 0.0, duration, Easing.quad_out)
            tm.interpolate(vis, "local_y", vis.local_y, 0.0, duration, Easing.quad_out)
            # Reset Collider
            tm.interpolate(self.collider, "scale_x", self.collider.scale_x, 1.0, duration, Easing.quad_out)
            tm.interpolate(self.collider, "scale_y", self.collider.scale_y, 1.0, duration, Easing.quad_out)
            tm.interpolate(self.collider, "local_x", self.collider.local_x, 0.0, duration, Easing.quad_out)
            tm.interpolate(self.collider, "local_y", self.collider.local_y, 0.0, duration, Easing.quad_out)

        ox, oy = get_offsets(sx, sy)
        # Tween Visuals
        tm.interpolate(vis, "scale_x", 1.0, sx, duration/2, Easing.quad_out, on_complete=reset_scale)
        tm.interpolate(vis, "scale_y", 1.0, sy, duration/2, Easing.quad_out)
        tm.interpolate(vis, "local_x", 0.0, ox, duration/2, Easing.quad_out)
        tm.interpolate(vis, "local_y", 0.0, oy, duration/2, Easing.quad_out)
        # Tween Collider
        tm.interpolate(self.collider, "scale_x", 1.0, sx, duration/2, Easing.quad_out)
        tm.interpolate(self.collider, "scale_y", 1.0, sy, duration/2, Easing.quad_out)
        tm.interpolate(self.collider, "local_x", 0.0, ox, duration/2, Easing.quad_out)
        tm.interpolate(self.collider, "local_y", 0.0, oy, duration/2, Easing.quad_out)

        self.score = 0

    def jump_effect(self):
        # Emit dust particles at the player's feet
        gx, gy = self.get_global_position()
        self.particles.emit(gx + 25, gy + 50, count=15, 
                            speed_range=(20, 80), 
                            angle_range=(200, 340), # Upwards-ish
                            color=(150, 150, 150))
                            
    def dash_effect(self):
        gx, gy = self.get_global_position()
        # Emit horizontal streaks behind the player
        angle = (180, 200) if self.controller.facing_right else (340, 360)
        self.particles.emit(gx + 25, gy + 25, count=2, 
                            speed_range=(100, 200), 
                            angle_range=angle,
                            color=(200, 255, 255))

    def update(self, delta):
        # 1. Capture abstract input (Engine-Agnostic requirement)
        keys = pygame.key.get_pressed()
        input_state = {
            "move_left": keys[pygame.K_LEFT] or keys[pygame.K_a],
            "move_right": keys[pygame.K_RIGHT] or keys[pygame.K_d],
            "jump": keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP],
            "dash": keys[pygame.K_LSHIFT] or keys[pygame.K_z] or keys[pygame.K_x]
        }

        # 2. Update gameplay logic (Intentions: velocity changes, impulse)
        old_vel_y = self.velocity_y
        was_grounded = self.controller.is_grounded
        
        self.controller.update(self, delta, input_state)
        
        # Squash & Stretch Logic
        # 2. JUMP STRETCH
        if input_state["jump"] and was_grounded and self.velocity_y < 0:
             self.jump_effect()
             self.apply_juice(0.7, 1.3) # Stretch

        self.was_grounded = self.controller.is_grounded

        # 3. Proceed with physics integration (Position resolution, gravity)
        super().update(delta)

        # 4. Out-of-bounds check (Kill plane)
        if self.get_global_position()[1] > 2000:
            self.die()

        # 5. Update behavioral state (Observation: what am I doing now?)
        self.state_machine.update(delta)

    def die(self):
        # Drop the player back to the starting point
        self.local_x = 100
        self.local_y = 400
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.update_transforms()

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
