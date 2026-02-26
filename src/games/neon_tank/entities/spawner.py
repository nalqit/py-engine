import random
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.collision.collider2d import Collider2D
from .enemy import Enemy

class Spawner(Node2D):
    def __init__(self, name, collision_world):
        super().__init__(name, 0, 0)
        self.collision_world = collision_world
        self.spawn_timer = 2.0
        self.rate = 3.0
        self.enemy_count = 0

    def update(self, delta):
        self.spawn_timer -= delta
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            self.spawn_timer = self.rate
        super().update(delta)

    def spawn_enemy(self):
        # Spawn at random position around the arena boundaries
        # Arena is roughly -500 to 500
        side = random.randint(0, 3)
        x, y = 0, 0
        if side == 0: # Top
            x = random.randint(-400, 400)
            y = -450
        elif side == 1: # Bottom
            x = random.randint(-400, 400)
            y = 450
        elif side == 2: # Left
            x = -450
            y = random.randint(-400, 400)
        else: # Right
            x = 450
            y = random.randint(-400, 400)

        self.enemy_count += 1
        name = f"Enemy_{self.enemy_count}"
        
        # Create collider
        col = Collider2D(name + "_Col", -15, -15, 30, 30)
        col.layer = "enemy"
        col.mask = {"wall", "player", "bullet"}
        
        enemy = Enemy(name, x, y, col, self.collision_world)
        enemy.add_child(col)
        
        if self.parent:
            self.parent.add_child(enemy)
