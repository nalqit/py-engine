import pygame
import sys
import math

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.circle_node import CircleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.circle_collider2d import CircleCollider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600
BLOCK_SIZE = 40

class DestructibleBlock(PhysicsBody2D):
    def __init__(self, name, x, y, collision_world):
        col = Collider2D(name+"Col", 0, 0, BLOCK_SIZE, BLOCK_SIZE)
        col.layer = "block"
        col.mask = {"wall", "block", "floor"}
        super().__init__(name, x, y, col, collision_world)
        
        self.use_gravity = True
        self.pushable = True
        self.push_weight = 1.0
        
        self.max_hp = 100.0
        self.hp = 100.0
        
        self.vis = RectangleNode(name+"Vis", 0, 0, BLOCK_SIZE, BLOCK_SIZE, (150, 100, 50))
        self.add_child(col)
        self.add_child(self.vis)
        
    def on_pushed(self, pusher):
        # Calculate impact based on pusher's velocity
        impact = abs(pusher.velocity_x) + abs(pusher.velocity_y)
        if impact > 200:
            damage = impact * 0.05
            self.take_damage(damage)
            
    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            # Destroy self
            if self.parent:
                self.parent.remove_child(self)
        else:
            # Change color based on health
            health_pct = self.hp / self.max_hp
            c = int(150 * health_pct)
            self.vis.color = (150, c, c)

class Projectile(PhysicsBody2D):
    def __init__(self, name, x, y, collision_world):
        # A circle collider so it rolls/bounces better if the engine supported it
        # Actually we can use a small AABB since we don't have true rolling physics in Level 3
        col = Collider2D(name+"Col", 0, 0, 20, 20)
        col.layer = "projectile"
        col.mask = {"wall", "block", "floor"}
        super().__init__(name, x, y, col, collision_world)
        
        self.use_gravity = True
        self.can_push = True
        self.push_strength = 10.0  # High strength to bowl through blocks
        
        self.add_child(col)
        self.add_child(CircleNode(name+"Vis", 10, 10, 10, (255, 50, 50)))
        
        # Slingshot states
        self.state = "idle" # idle, dragged, flying
        self.start_x = x
        self.start_y = y
        self.drag_pos = (x, y)
        
    def update(self, delta):
        # Override gravity if not flying
        if self.state != "flying":
            self.velocity_x = 0
            self.velocity_y = 0
            
            # Simple mouse logic inside update
            mx, my = pygame.mouse.get_pos()
            # Need to map screen to virtual
            # Assuming no scale for the mouse pos right now (we would map it if scaled)
            sw, sh = pygame.display.get_surface().get_size()
            mx = mx * (VIRTUAL_W / sw)
            my = my * (VIRTUAL_H / sh)
            
            mouse_pressed = pygame.mouse.get_pressed()[0]
            
            if self.state == "idle":
                # Check distance to mouse
                dist = math.hypot(mx - (self.local_x + 10), my - (self.local_y + 10))
                if mouse_pressed and dist < 30:
                    self.state = "dragged"
            
            elif self.state == "dragged":
                self.local_x = mx - 10
                self.local_y = my - 10
                if not mouse_pressed:
                    self.state = "flying"
                    # Launch!
                    dx = self.start_x - self.local_x
                    dy = self.start_y - self.local_y
                    self.apply_impulse(dx * 5.0, dy * 5.0)
        
        super().update(delta)

def build_structure(parent, cw, start_x, start_y, rows, cols):
    for r in range(rows):
        for c in range(cols):
            x = start_x + c * (BLOCK_SIZE + 2)
            y = start_y - (r + 1) * (BLOCK_SIZE + 2)
            b = DestructibleBlock(f"Block_{r}_{c}", x, y, cw)
            parent.add_child(b)

def main():
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 3: Physics Destruction (Stacking & Impulse)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)
    
    # Floor
    floor = Node2D("Floor", -100, VIRTUAL_H - 40)
    fc = Collider2D("FloorCol", 0, 0, 1000, 40, is_static=True)
    fc.layer = "floor"
    fc.mask = {"block", "projectile"}
    floor.add_child(fc)
    floor.add_child(RectangleNode("FloorVis", 0, 0, 1000, 40, (100, 150, 100)))
    root.add_child(floor)
    
    # Pyramids
    build_structure(root, cw, 400, VIRTUAL_H - 40, 6, 3)
    build_structure(root, cw, 600, VIRTUAL_H - 40, 4, 4)
    
    # Projectile
    bird = Projectile("Bird", 150, VIRTUAL_H - 200, cw)
    root.add_child(bird)
    
    # Slingshot visual post
    root.add_child(RectangleNode("Post", 155, VIRTUAL_H - 190, 10, 150, (100, 50, 0)))
    
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
                if event.key == pygame.K_r:
                    # Reset bird
                    bird.state = "idle"
                    bird.local_x = bird.start_x
                    bird.local_y = bird.start_y
                    bird.velocity_x = 0
                    bird.velocity_y = 0
                elif event.key == pygame.K_s:
                    # Spawn more blocks
                    build_structure(root, cw, 500, VIRTUAL_H - 40, 3, 2)
                    
        profiler.begin("Logic")
        while accumulator >= fixed_dt:
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Logic")
            
        profiler.begin("Render")
        game_surface.fill((135, 206, 235))
        
        # Draw slingshot band if pulled
        if bird.state == "dragged":
            pygame.draw.line(game_surface, (0,0,0), (160, VIRTUAL_H - 190), (bird.local_x+10, bird.local_y+10), 3)
            
        root.render(game_surface)
        
        # HUD
        block_count = sum(1 for c in root.children if isinstance(c, DestructibleBlock))
        hud_lines = [
            f"FPS: {clock.get_fps():.1f}",
            f"Blocks: {block_count}",
            "Drag red circle to aim & release",
            "Press R to reset ball",
            "Press S to spawn more blocks"
        ]
        
        y = 10
        for line in hud_lines:
            txt = font.render(line, True, (0, 0, 0))
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
