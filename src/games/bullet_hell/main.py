import pygame
import sys
import math
import random

from src.engine.scene.node2d import Node2D
from src.engine.scene.circle_node import CircleNode
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.circle_collider2d import CircleCollider2D
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600

class Bullet(Node2D):
    def __init__(self, name, pool):
        super().__init__(name, 0, 0)
        self.pool = pool
        self.vx = 0.0
        self.vy = 0.0
        self.active = False
        
        self.collider = CircleCollider2D(name+"_col", 0, 0, 4, is_trigger=True)
        self.collider.layer = "bullet"
        self.collider.mask = {"player"}
        self.add_child(self.collider)
        
    def fire(self, x, y, vx, vy):
        self.local_x = x
        self.local_y = y
        self.vx = vx
        self.vy = vy
        self.active = True
        
    def update(self, delta):
        if not self.active:
            # Skip updating children (like collider) if inactive to save CPU
            return
            
        self.local_x += self.vx * delta
        self.local_y += self.vy * delta
        
        # Out of bounds recycling
        if self.local_x < -100 or self.local_x > VIRTUAL_W + 100 or \
           self.local_y < -100 or self.local_y > VIRTUAL_H + 100:
            self.deactivate()
            
        super().update(delta)
        
    def render(self, surface):
        if not self.active: return
        sx, sy = self.get_screen_position()
        pygame.draw.circle(surface, (255, 100, 100), (int(sx), int(sy)), 4)
        super().render(surface)
        
    def deactivate(self):
        if self.active:
            self.active = False
            self.pool.recycle(self)
            
    def on_collision_enter(self, other):
        if other.layer == "player":
            self.deactivate()

class BulletPool:
    def __init__(self, size, parent_node):
        self.pool = []
        self.active_count = 0
        self.allocations = 0
        self.recycles = 0
        for i in range(size):
            b = Bullet(f"Bullet_{i}", self)
            parent_node.add_child(b)
            self.pool.append(b)
            
    def get(self):
        if self.pool:
            b = self.pool.pop()
            self.active_count += 1
            self.allocations += 1
            return b
        # If pool runs out, we hit the saturation ceiling.
        return None
        
    def recycle(self, bullet):
        self.pool.append(bullet)
        self.active_count -= 1
        self.recycles += 1

class BulletPlayer(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = False
        self.base_speed = 300.0
        self.focus_speed = 120.0
        self.hp = 100
        
    def update(self, delta):
        keys = pygame.key.get_pressed()
        
        move_x, move_y = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_y += 1
        
        # Normalize
        if move_x != 0 and move_y != 0:
            length = math.hypot(move_x, move_y)
            move_x /= length
            move_y /= length
            
        speed = self.focus_speed if keys[pygame.K_LSHIFT] else self.base_speed
        
        self.velocity_x = move_x * speed
        self.velocity_y = move_y * speed
        
        super().update(delta)
        
        # Clamp to screen
        self.local_x = max(0, min(self.local_x, VIRTUAL_W - self.collider.width))
        self.local_y = max(0, min(self.local_y, VIRTUAL_H - self.collider.height))
        
    def on_collision_enter(self, other):
        if getattr(other, "layer", "") == "bullet":
            self.hp -= 1

class Boss(Node2D):
    def __init__(self, name, x, y, pool):
        super().__init__(name, x, y)
        self.pool = pool
        self.fire_timer = 0.0
        self.base_fire_rate = 0.5
        self.fire_rate_multiplier = 1.0
        self.angle_offset = 0.0
        self.bullet_speed = 200.0
        
    def update(self, delta):
        self.fire_timer -= delta
        self.angle_offset += 45 * delta
        
        if self.fire_timer <= 0:
            rate = self.base_fire_rate / self.fire_rate_multiplier
            self.fire_timer = rate
            self.fire_pattern()
            
        super().update(delta)
        
    def fire_pattern(self):
        # Fire a circular spread
        bullet_count = int(12 * min(self.fire_rate_multiplier, 5))
        angle_step = 360.0 / bullet_count
        
        gx, gy = self.get_global_position()
        for i in range(bullet_count):
            b = self.pool.get()
            if b:
                angle = math.radians(self.angle_offset + i * angle_step)
                vx = math.cos(angle) * self.bullet_speed
                vy = math.sin(angle) * self.bullet_speed
                b.fire(gx, gy, vx, vy)

def main():
    pygame.init()
    # Fixed window for sizing but it's resizable
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 1: Bullet Hell (Saturation & Object Pooling)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)
    
    bullet_layer = Node2D("BulletLayer")
    root.add_child(bullet_layer)
    pool = BulletPool(3000, bullet_layer)  # Pre-allocate 3000 bullets!
    
    # Boss
    boss = Boss("Boss", VIRTUAL_W/2, 100, pool)
    root.add_child(boss)
    boss.add_child(CircleNode("BossVis", 0, 0, 30, (200, 50, 200)))
    
    # Player
    player_col = Collider2D("PlayerCol", 0, 0, 10, 10)
    player_col.layer = "player"
    player_col.mask = {"bullet"}
    player = BulletPlayer("Player", VIRTUAL_W/2, 500, player_col, collision_world)
    root.add_child(player)
    player.add_child(player_col)
    player.add_child(RectangleNode("PlayerVis", 0, 0, 10, 10, (50, 255, 50)))
    
    font = pygame.font.SysFont("Arial", 16)
    
    # Marathon state
    marathon_time = 0.0
    initial_boss_x = boss.local_x
    
    running = True
    fixed_dt = 1/60.0
    accumulator = 0.0
    
    while running:
        dt = clock.tick(60) / 1000.0
        profiler.log_frame(dt)
        accumulator += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    boss.fire_rate_multiplier *= 2.0
                    print(f"Saturation Mode! Multiplier: {boss.fire_rate_multiplier}x")
                    
        profiler.begin("Logic")
        while accumulator >= fixed_dt:
            marathon_time += fixed_dt
            # 10 minute marathon float drift check
            if marathon_time >= 600.0:
                marathon_time = 0.0
                drift = boss.local_x - initial_boss_x
                print(f"[MARATHON] Float Drift over 10min: {drift} pixels")
            
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Logic")
            
        profiler.begin("Render")
        game_surface.fill((20, 20, 30))
        root.render(game_surface)
        
        # Draw HUD to virtual surface
        fps = clock.get_fps()
        hud_lines = [
            f"FPS: {fps:.1f}",
            f"Active Bullets: {pool.active_count} / {len(pool.pool) + pool.active_count}",
            f"Pool Alloc/Recycle: {pool.allocations} / {pool.recycles}",
            f"Boss Multiplier (Press 'S'): {boss.fire_rate_multiplier}x",
            f"Player HP: {player.hp}",
            f"Mem: {profiler.get_memory_mb():.1f} MB"
        ]
        
        y = 10
        for line in hud_lines:
            txt = font.render(line, True, (255, 255, 255))
            game_surface.blit(txt, (10, y))
            y += 20
        profiler.end("Render")
            
        # Scale resolution-independent viewport to actual window size
        scaled = pygame.transform.scale(game_surface, screen.get_size())
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        
    profiler.print_summary()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
