import pygame
import sys
import math

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.circle_node import CircleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.fsm.state_machine import StateMachine
from src.engine.fsm.state import State
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600

class Player(PhysicsBody2D):
    def __init__(self, name, x, y, cw):
        col = Collider2D(name+"Col", 0, 0, 20, 20)
        col.layer = "player"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.speed = 150.0
        
        self.add_child(col)
        self.add_child(CircleNode("PVis", 10, 10, 10, (50, 255, 50)))
        
    def update(self, delta):
        keys = pygame.key.get_pressed()
        mx, my = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: mx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: mx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: my -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: my += 1
        
        # Sneak mode halves speed
        speed = self.speed * 0.5 if keys[pygame.K_LSHIFT] else self.speed
        
        if mx != 0 and my != 0:
            length = math.hypot(mx, my)
            mx /= length; my /= length
            
        self.velocity_x = mx * speed
        self.velocity_y = my * speed
        
        super().update(delta)

# Guard AI FSM
class PatrolState(State):
    def enter(self):
        self.body.vis.color = (50, 50, 255) # Blue = calm
        self.waypoint_idx = 0
        self.wait_timer = 0.0
        
    def update(self, delta):
        if self.body.sees_player:
            self.body.fsm.change_state(AlertState(self.body))
            return
            
        if self.wait_timer > 0:
            self.wait_timer -= delta
            self.body.velocity_x = 0
            self.body.velocity_y = 0
            return
            
        wp = self.body.waypoints[self.waypoint_idx]
        tx, ty = wp
        dx = tx - self.body.local_x
        dy = ty - self.body.local_y
        dist = math.hypot(dx, dy)
        
        if dist < 5.0:
            self.waypoint_idx = (self.waypoint_idx + 1) % len(self.body.waypoints)
            self.wait_timer = 1.0 # wait 1 sec at waypoint
            return
            
        # Move
        self.body.facing_angle = math.atan2(dy, dx)
        speed = 50.0
        self.body.velocity_x = math.cos(self.body.facing_angle) * speed
        self.body.velocity_y = math.sin(self.body.facing_angle) * speed

class AlertState(State):
    def enter(self):
        self.body.vis.color = (255, 255, 50) # Yellow = alert
        self.alert_timer = 1.5
        self.body.velocity_x = 0
        self.body.velocity_y = 0
        
    def update(self, delta):
        if self.body.sees_player:
            self.body.fsm.change_state(ChaseState(self.body))
            return
            
        self.alert_timer -= delta
        if self.alert_timer <= 0:
            self.body.fsm.change_state(PatrolState(self.body))

class ChaseState(State):
    def enter(self):
        self.body.vis.color = (255, 50, 50) # Red = chase
        
    def update(self, delta):
        if not self.body.sees_player:
            self.body.fsm.change_state(AlertState(self.body))
            return
            
        # Move towards last known player pos
        tx, ty = self.body.last_known_player_pos
        dx = tx - self.body.local_x
        dy = ty - self.body.local_y
        dist = math.hypot(dx, dy)
        
        if dist > 5.0:
            self.body.facing_angle = math.atan2(dy, dx)
            speed = 100.0
            self.body.velocity_x = math.cos(self.body.facing_angle) * speed
            self.body.velocity_y = math.sin(self.body.facing_angle) * speed
        else:
            self.body.velocity_x = 0
            self.body.velocity_y = 0

class Guard(PhysicsBody2D):
    def __init__(self, name, waypoints, cw):
        col = Collider2D(name+"Col", 0, 0, 20, 20)
        col.layer = "enemy"
        col.mask = {"wall", "player"}
        start_x, start_y = waypoints[0]
        super().__init__(name, start_x, start_y, col, cw)
        
        self.use_gravity = False
        self.waypoints = waypoints
        self.facing_angle = 0.0
        
        self.sees_player = False
        self.last_known_player_pos = (0, 0)
        
        self.add_child(col)
        self.vis = CircleNode("EVis", 10, 10, 10, (50, 50, 255))
        self.add_child(self.vis)
        
        self.fsm = StateMachine(self)
        self.fsm.change_state(PatrolState(self))
        
        self.vision_polygon = []

    def update(self, delta):
        super().update(delta)
        # Vision cone generation
        gx, gy = self.get_global_position()
        cx, cy = gx + 10, gy + 10
        
        fov_deg = 90
        ray_count = 30
        view_dist = 250.0
        
        angle_start = self.facing_angle - math.radians(fov_deg/2)
        angle_step = math.radians(fov_deg) / max(1, ray_count - 1)
        
        self.vision_polygon = [(cx, cy)]
        
        hit_player = False
        target_pos = None
        
        for i in range(ray_count):
            a = angle_start + i * angle_step
            end_x = cx + math.cos(a) * view_dist
            end_y = cy + math.sin(a) * view_dist
            
            # Engine Raycast
            hit, hx, hy, hit_col = self.collision_world.raycast(cx, cy, end_x, end_y, mask={"wall", "player"})
            
            if hit:
                self.vision_polygon.append((hx, hy))
                if hit_col.layer == "player":
                    hit_player = True
                    target_pos = hit_col.parent.get_global_position()
            else:
                self.vision_polygon.append((end_x, end_y))
                
        self.sees_player = hit_player
        if hit_player and target_pos:
            self.last_known_player_pos = target_pos
            
        self.fsm.update(delta)
        
    def render(self, surface):
        # Draw vision cone
        if len(self.vision_polygon) >= 3:
            s = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            color = (255, 50, 50, 100) if self.sees_player else (255, 255, 50, 100)
            if isinstance(self.fsm.current_state, PatrolState):
                color = (255, 255, 255, 50)
            
            pygame.draw.polygon(s, color, self.vision_polygon)
            surface.blit(s, (0,0))
            
        super().render(surface)

def create_wall(name, x, y, w, h, cw, parent):
    wall = Node2D(name, x, y)
    col = Collider2D(name+"Col", 0, 0, w, h, is_static=True)
    col.layer = "wall"
    col.mask = {"player", "enemy"}
    wall.add_child(col)
    wall.add_child(RectangleNode(name+"Vis", 0, 0, w, h, (100, 100, 100)))
    parent.add_child(wall)

def main():
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 4: Top-Down Stealth (Raycasting & Vision Cones)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)
    
    # Outer walls
    create_wall("WTop", 0, 0, 800, 20, cw, root)
    create_wall("WBot", 0, 580, 800, 20, cw, root)
    create_wall("WLeft", 0, 0, 20, 600, cw, root)
    create_wall("WRight", 780, 0, 20, 600, cw, root)
    
    # Inner maze
    create_wall("M1", 200, 100, 20, 300, cw, root)
    create_wall("M2", 400, 200, 200, 20, cw, root)
    create_wall("M3", 600, 400, 20, 150, cw, root)
    create_wall("M4", 100, 450, 300, 20, cw, root)
    
    # Player
    player = Player("Player", 50, 50, cw)
    root.add_child(player)
    
    # Guards
    g1 = Guard("Guard1", [(100, 100), (700, 100), (700, 350)], cw)
    root.add_child(g1)
    
    g2 = Guard("Guard2", [(500, 500), (200, 500), (200, 300)], cw)
    root.add_child(g2)
    
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
                
        profiler.begin("AI_Logic")
        while accumulator >= fixed_dt:
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("AI_Logic")
            
        profiler.begin("Render")
        game_surface.fill((20, 20, 20))
        root.render(game_surface)
        
        hud_lines = [
            f"FPS: {clock.get_fps():.1f}",
            "WASD to Move, Shift to Sneak",
            "Avoid the vision cones!"
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
