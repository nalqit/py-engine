import math
from src.pyengine2D.core.engine import Engine
from src.pyengine2D.core.input import Keys
from src.pyengine2D.physics.physics_body_2d import PhysicsBody2D
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.rectangle_node import RectangleNode
from src.pyengine2D.scene.particles import ParticleEmitter2D

class Player(PhysicsBody2D):
    def __init__(self, name, x, y, collider=None, collision_world=None):
        super().__init__(name, x, y, collider, collision_world)

    def ready(self):
        """Called after scene load to initialize state."""
        self.use_gravity = True
        self.gravity = 1200.0  # Snappy gravity
        self.move_speed = 250.0
        self.jump_force = -600.0
        self.wall_jump_force_x = 400.0
        self.wall_jump_force_y = -450.0
        
        # State
        self.is_on_wall = False
        self.wall_side = 0 # -1 for left wall, 1 for right wall
        self.last_jump_wall_side = 0 # To prevent same-wall infinite jump
        
        # Visuals (expected to be loaded from .scene)
        self.vis = self._get_node_by_type(RectangleNode)
        self.particles = self._get_node_by_type(ParticleEmitter2D)
        
    def _get_node_by_type(self, cls):
        for c in self.children:
            if isinstance(c, cls):
                return c
        return None

    def update(self, delta):
        inp = Engine.instance.input
        
        # Ground check via velocity (physics body snaps to 0 on floor)
        is_grounded = self.velocity_y == 0
        if is_grounded:
            self.last_jump_wall_side = 0

        # 1. Horizontal Movement
        move_input = 0
        if inp.is_key_pressed(Keys.A): move_input -= 1
        if inp.is_key_pressed(Keys.D): move_input += 1
        
        self.velocity_x = move_input * self.move_speed
        
        # 2. Wall Detection (simplified check)
        self.is_on_wall = False
        self.wall_side = 0
        
        # Check walls via collision world (small probe)
        pgx, pgy = 0, 0
        if self.parent and isinstance(self.parent, Node2D):
            pgx, pgy = self.parent.get_global_position()
            
        res_left = self.collision_world.check_collision(self.collider, pgx + self.local_x - 2, pgy + self.local_y)
        res_right = self.collision_world.check_collision(self.collider, pgx + self.local_x + 2, pgy + self.local_y)
        
        if res_left.collided:
            self.is_on_wall = True
            self.wall_side = -1
        elif res_right.collided:
            self.is_on_wall = True
            self.wall_side = 1
            
        # 3. Wall Slide
        if self.is_on_wall and self.velocity_y > 0:
            self.velocity_y = min(self.velocity_y, 100.0) # Slow slide
            
        # 4. Jumping
        if inp.is_key_just_pressed(Keys.SPACE) or inp.is_key_just_pressed(Keys.W):
            if is_grounded:
                self.velocity_y = self.jump_force
                self._emit_jump_particles()
            elif self.is_on_wall and self.wall_side !=self.last_jump_wall_side:
                # Wall Jump: Only if it's a DIFFERENT wall than last jump
                self.velocity_x = -self.wall_side * self.wall_jump_force_x
                self.velocity_y = self.wall_jump_force_y
                self.last_jump_wall_side = self.wall_side
                self._emit_jump_particles()

        super().update(delta)
        
        # Death check (falling off bottom)
        if self.local_y > 1000:
            self.reset_position()

    def _emit_jump_particles(self):
        if self.particles:
            gx, gy = self.get_global_position()
            self.particles.emit(gx, gy + 15, count=10, speed_range=(50, 100), color=(100, 255, 255))

    def reset_position(self):
        self.local_x = 400
        self.local_y = 500
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_jump_wall_side = 0
        self.update_transforms()
