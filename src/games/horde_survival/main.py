import pygame
import sys
import math
import random

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.circle_node import CircleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler
from src.engine.utils.pathfinding import AStarGrid

VIRTUAL_W, VIRTUAL_H = 800, 600

class Player(PhysicsBody2D):
    def __init__(self, name, x, y, cw):
        col = Collider2D(name+"Col", 0, 0, 16, 16)
        col.layer = "player"
        col.mask = {"wall", "enemy"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.speed = 200.0
        self.hp = 100
        
        self.add_child(col)
        self.add_child(RectangleNode("PVis", 0, 0, 16, 16, (50, 200, 255)))
        
        self.attack_timer = 0.5
        
    def update(self, delta):
        keys = pygame.key.get_pressed()
        mx, my = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: mx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: mx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: my -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: my += 1
        
        if mx != 0 and my != 0:
            length = math.hypot(mx, my)
            mx /= length; my /= length
            
        self.velocity_x = mx * self.speed
        self.velocity_y = my * self.speed
        
        super().update(delta)
        
        # Auto-attack
        self.attack_timer -= delta
        if self.attack_timer <= 0:
            self.attack_timer = 0.5
            self.auto_attack()
            
    def auto_attack(self):
        root = self.parent
        nearest = None
        min_dist = 150.0  # Range
        
        gx, gy = self.get_global_position()
        
        for c in root.children:
            if isinstance(c, Enemy):
                ex, ey = c.get_global_position()
                dist = math.hypot(ex - gx, ey - gy)
                if dist < min_dist:
                    min_dist = dist
                    nearest = c
                    
        if nearest:
            # visual effect
            eff = RectangleNode("Hit", nearest.local_x, nearest.local_y, 16, 16, (255, 255, 255))
            root.add_child(eff)
            # Remove enemy
            root.remove_child(nearest)

class Enemy(PhysicsBody2D):
    def __init__(self, name, x, y, cw, grid, player):
        col = Collider2D(name+"Col", 0, 0, 14, 14)
        col.layer = "enemy"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.speed = 100.0 + random.uniform(-20, 20)
        self.grid = grid
        self.player = player
        
        self.add_child(col)
        self.add_child(CircleNode("EVis", 7, 7, 7, (255, 50, 50)))
        
        self.path = []
        self.path_timer = random.uniform(0.0, 0.5)
        
    def update(self, delta):
        self.path_timer -= delta
        
        # Only recalculate path twice a second to scale to 100+ enemies
        global profiler
        
        if self.path_timer <= 0:
            self.path_timer = 0.5
            if profiler: profiler.begin("Pathfinding")
            self.path = self.grid.get_path(self.get_global_position(), self.player.get_global_position())
            if profiler: profiler.end("Pathfinding")
            
        if self.path:
            # Move towards next node
            tx, ty = self.path[0]
            gx, gy = self.get_global_position()
            dx = tx - gx
            dy = ty - gy
            dist = math.hypot(dx, dy)
            if dist < 5.0:
                self.path.pop(0)
            else:
                self.velocity_x = (dx/dist) * self.speed
                self.velocity_y = (dy/dist) * self.speed
        else:
            self.velocity_x = 0
            self.velocity_y = 0
            
        super().update(delta)
        
    def on_collision_enter(self, other):
        if other.layer == "player":
            self.player.hp -= 5
            # Bounce away slightly
            self.local_x -= self.velocity_x * 0.1
            self.local_y -= self.velocity_y * 0.1

def create_wall(name, x, y, w, h, cw, parent, grid):
    wall = Node2D(name, x, y)
    col = Collider2D(name+"Col", 0, 0, w, h, is_static=True)
    col.layer = "wall"
    col.mask = {"player", "enemy"}
    wall.add_child(col)
    wall.add_child(RectangleNode(name+"Vis", 0, 0, w, h, (100, 100, 100)))
    parent.add_child(wall)
    
    # Register with navmesh
    grid.set_obstacle_world(x, y, w, h)

profiler = None

def main():
    global profiler
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 5: Horde Survival (Massive AI Pathfinding)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)
    
    # Pathfinding grid
    grid = AStarGrid(int(VIRTUAL_W/20), int(VIRTUAL_H/20), 20)
    
    # Outer walls
    create_wall("WTop", 0, 0, 800, 20, cw, root, grid)
    create_wall("WBot", 0, 580, 800, 20, cw, root, grid)
    create_wall("WLeft", 0, 0, 20, 600, cw, root, grid)
    create_wall("WRight", 780, 0, 20, 600, cw, root, grid)
    
    # Obstacles
    create_wall("Obs1", 200, 200, 100, 200, cw, root, grid)
    create_wall("Obs2", 500, 100, 20, 300, cw, root, grid)
    
    # Player
    player = Player("Player", 100, 100, cw)
    root.add_child(player)
    
    def spawn_enemies(count):
        for i in range(count):
            x = random.choice([50, 700])
            y = random.choice([50, 500])
            e = Enemy(f"Enemy_{random.randint(0,99999)}", x, y, cw, grid, player)
            root.add_child(e)
            
    # Spawn initial horde
    spawn_enemies(20)
    
    font = pygame.font.SysFont("Arial", 16)
    
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
                    spawn_enemies(50)
                    
        profiler.begin("Logic")
        while accumulator >= fixed_dt:
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Logic")
        
        # Cleanup hit markers
        for c in list(root.children):
            if c.name == "Hit":
                root.remove_child(c)
            
        profiler.begin("Render")
        game_surface.fill((40, 50, 40))
        root.render(game_surface)
        
        enemies_count = sum(1 for c in root.children if isinstance(c, Enemy))
        
        p_time = profiler.timings.get("Pathfinding", 0)
        hud_lines = [
            f"FPS: {clock.get_fps():.1f}",
            f"Enemies: {enemies_count}",
            f"Player HP: {player.hp}",
            f"Pathfinding Time: {p_time:.2f}ms",
            f"Mem: {profiler.get_memory_mb():.1f} MB",
            f"Press S to spawn 50 extra enemies! (Saturation Test)"
        ]
        
        y = 10
        for line in hud_lines:
            txt = font.render(line, True, (255, 255, 255))
            game_surface.blit(txt, (10, y))
            y += 20
        profiler.end("Render")
            
        scaled = pygame.transform.scale(game_surface, screen.get_size())
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        
    profiler.print_summary()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
