from src.scene.node2d import Node2D


class PhysicsBody2D(Node2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y)

        self.collider = collider
        self.collision_world = collision_world
        self.controller = None

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

        # 3. Resolve movement & collisions
        dx = self.velocity_x * delta
        dy = self.velocity_y * delta
        self.move_and_collide(dx, dy, delta)

        super().update(delta)

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
                # Dynamic Collision Resolution
                if not hit_x.is_static:
                    body_to_push = hit_x.parent

                    # Check if the pushed body (Box) is blocked by something else (NPC/Wall)
                    blocker = self.collision_world.check_collision(
                        hit_x,
                        body_to_push.local_x + dx,
                        body_to_push.local_y,
                        margin=(0, -2),
                    )

                    can_push = True
                    if blocker:
                        can_push = False

                    if can_push:
                        body_to_push.local_x += dx
                        self.local_x += dx

        # --- Y axis (Vertical) ---
        # Initialize as false, will be set true if we hit floor
        self.on_ground = False

        if dy != 0:
            target_y = self.local_y + dy
            hit_y = self.collision_world.check_collision(
                self.collider, self.local_x, target_y, margin=(-2, 0)
            )

            if not hit_y:
                self.local_y += dy
            else:
                if dy > 0:  # Falling down
                    self.on_ground = True
                    self.velocity_y = 0  # Reset gravity accumulation
                elif dy < 0:  # Jumping up into ceiling
                    self.velocity_y = 0

    def on_collision_enter(self, other):
        pass

    def on_collision_stay(self, other):
        pass

    def on_collision_exit(self, other):
        pass
