from src.scene.physics.physics_body_2d import PhysicsBody2D

class NPC(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)

        self.direction = 1
        self.speed = 100
        self.use_gravity = True

    def update(self, delta):
        dx = self.direction * self.speed * delta

        if self.use_gravity:
            self.velocity_y += self.gravity * delta

        dy = self.velocity_y * delta

        # إذا اصطدم، يعكس الاتجاه
        if self.collision_world.check_collision(
            self.collider,
            self.local_x + dx,
            self.local_y
        ):
            self.direction *= -1
            dx = 0

        self.move_and_collide(dx, dy, delta)

        super().update(delta)
