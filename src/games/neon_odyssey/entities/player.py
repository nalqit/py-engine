import math
from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.particles import ParticleEmitter2D

# ------------------------------------------------------------------
# Advanced Player Example
# Demonstrates:
# - Physics movement & Jumping
# - Connecting and emitting Signals
# - Particle Emitters (running dust, jump burst)
# ------------------------------------------------------------------

class Player(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.gravity = 1500.0  # Heavy, tight gravity
        self.can_push = True
        
        self.move_speed = 300.0
        self.jump_force = -900.0
        
        # State
        self.health = 3
        
        # 1. Signals
        # Guide: We register signals here so other systems (like HUD) can listen to them
        # without needing a direct reference to the Player instance.
        self.register_signal("on_health_changed")
        self.register_signal("on_died")

        # 2. Visuals
        self.vis = RectangleNode("PlayerVis", -20, -20, 40, 40, (0, 255, 200)) # Neon Cyan
        self.add_child(self.vis)
        
        # 3. Particles
        # We attach these as children so they follow the player automatically.
        self.run_particles = ParticleEmitter2D("RunDust")
        self.add_child(self.run_particles)
        
        self.jump_particles = ParticleEmitter2D("JumpBurst")
        self.add_child(self.jump_particles)

    def update(self, delta):
        inp = Engine.instance.input
        
        # 1. Movement Logic
        move_input = 0
        if inp.is_key_pressed(Keys.A): move_input -= 1
        if inp.is_key_pressed(Keys.D): move_input += 1
        
        self.velocity_x = move_input * self.move_speed
        
        # Guide: To check if we are on the ground, we see if our vertical velocity is exactly 0.
        # PhysicsBody2D handles snapping to the floor when a collision resolves.
        is_grounded = self.velocity_y == 0
        
        # 2. Jumping
        if inp.is_key_just_pressed(Keys.SPACE) and is_grounded:
            self.velocity_y = self.jump_force
            
            # Emit particles when we jump
            gx, gy = self.get_global_position()
            self.jump_particles.emit(gx, gy + 20, count=15, speed_range=(50, 150), 
                                     color=(200, 200, 200)) # Grey dust explosion

        # 3. Running Particles
        # If moving and on the ground, emit dust trails behind us
        if is_grounded and move_input != 0:
            gx, gy = self.get_global_position()
            # Random chance to spawn a particle reduces the density so it looks like a trail
            import random
            if random.random() < 0.4:
                # Offset slightly opposite to movement direction
                offset_x = -move_input * 15
                self.run_particles.emit(gx + offset_x, gy + 20, count=1, 
                                        speed_range=(20, 40), color=(100, 100, 100))
        
        # Let PhysicsBody2D move us and resolve collisions
        super().update(delta)
        
        # Soft kill barrier (falling off level)
        if self.local_y > 1000:
            self.take_damage(1)
            self.reset_position()

    def take_damage(self, amount):
        self.health -= amount
        # Guide: Emit the signal so anyone listening (like HUD) knows we took damage!
        self.emit_signal("on_health_changed", self.health)
        
        if self.health <= 0:
            self.emit_signal("on_died")
            self.destroy()

    def reset_position(self):
        # Stop all momentum
        self.velocity_x = 0
        self.velocity_y = 0
        self.local_x = 200 # Spawn X
        self.local_y = 100 # Spawn Y
        self.update_transforms()
