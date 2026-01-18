from src.scene.node2d import Node2D

class PhysicsBody2D(Node2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y)

        self.collider = collider
        self.collision_world = collision_world

        # Movement
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.speed = 200.0

        # Gravity (اختياري)
        self.use_gravity = False
        self.gravity = 800.0
        self.on_ground = False

    def move_and_collide(self, dx, dy, delta):
        # =================
        # X axis
        # =================
        hit = self.collision_world.check_collision(
            self.collider,
            self.local_x + dx,
            self.local_y
        )

        if not hit:
            self.local_x += dx
        else:
            # 🔥 محاولة دفع الجسم
            if not hit.is_static:
                # جرّب تحريك الجسم المصطدم
                if not self.collision_world.check_collision(
                    hit,
                    hit.parent.local_x + dx,
                    hit.parent.local_y
                ):
                    hit.parent.local_x += dx
                    self.local_x += dx

        # =================
        # Y axis
        # =================
        hit = self.collision_world.check_collision(
            self.collider,
            self.local_x,
            self.local_y + dy
        )

        if not hit:
            self.local_y += dy
            self.on_ground = False
        else:
            if dy > 0:
                self.on_ground = True
            self.velocity_y = 0



