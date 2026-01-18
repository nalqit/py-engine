from src.scene.physics.physics_body_2d import PhysicsBody2D

class Player(PhysicsBody2D):

    def __init__(self, name, x, y, input_manager, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)

        self.input = input_manager
        self.use_gravity = True
        self.jump_force = -400.0
        self.collider = collider
        self.collision_world = collision_world
        self.speed = 200.0
        
        # Physics
        self.velocity_y = 0.0
        self.gravity = 800.0
        self.jump_force = -400.0
        self.on_ground = False

    def update(self, delta):
        dx = 0

        if self.input.is_pressed("move_left"):
            dx -= 1
        if self.input.is_pressed("move_right"):
            dx += 1

        dx *= self.speed * delta

        if self.use_gravity:
            self.velocity_y += self.gravity * delta

        if self.input.is_pressed("move_up") and self.on_ground:
            self.velocity_y = self.jump_force
            self.on_ground = False

        dy = self.velocity_y * delta

        self.move_and_collide(dx, dy, delta)

        super().update(delta)

