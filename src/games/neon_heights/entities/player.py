import math
from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.particles import ParticleEmitter2D

class Player(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
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
        
        # Visuals
        self.vis = RectangleNode("PlayerVis", -15, -15, 30, 30, (0, 255, 255)) # Cyan
        self.add_child(self.vis)
        
        self.particles = ParticleEmitter2D("Particles")
        self.add_child(self.particles)

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
        gx, gy = self.get_global_position()
        self.particles.emit(gx, gy + 15, count=10, speed_range=(50, 100), color=(100, 255, 255))

    def reset_position(self):
        self.local_x = 400
        self.local_y = 500
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_jump_wall_side = 0
        self.update_transforms()
