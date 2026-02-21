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

VIRTUAL_W, VIRTUAL_H = 800, 600

def create_radial_gradient(radius, color):
    surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    r, g, b = color
    for i in range(radius, 0, -2):
        alpha = int(255 * (1 - (i/radius)**2)) # quadratic fade
        pygame.draw.circle(surf, (r, g, b, alpha), (radius, radius), i)
    return surf

class PointLight(Node2D):
    def __init__(self, name, x, y, radius, color):
        super().__init__(name, x, y)
        self.radius = radius
        self.color = color
        self.texture = create_radial_gradient(radius, color)
        # Dedicated surface for this light to apply shadows before blending
        self.light_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
class LightingSystem(Node2D):
    def __init__(self, name, cw):
        super().__init__(name, 0, 0)
        self.collision_world = cw
        self.ambient_color = (40, 40, 60)
        self.light_map = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        
        self.lights = []
        
    def add_light(self, light):
        self.lights.append(light)
        self.add_child(light)
        
    def render(self, surface):
        self.light_map.fill(self.ambient_color)
        
        # Collect all wall corners for shadow casting
        # To avoid O(N) corners * Raycasts per light per frame, we'll extract relevant corners
        corners = []
        # Engine collision rects are used as shadow casters
        for col, rect in self.collision_world._cached_rects.items():
            if col.layer == "wall" or col.layer == "cast_shadow":
                l, t, r, b = rect
                corners.extend([(l,t), (r,t), (r,b), (l,b)])
                
        # To ensure shadows hit screen edges, add viewport corners
        corners.extend([(-10,-10), (VIRTUAL_W+10,-10), (VIRTUAL_W+10, VIRTUAL_H+10), (-10, VIRTUAL_H+10)])
        
        for light in self.lights:
            lx, ly = light.get_global_position()
            
            # 1. Prepare Light Surface
            light.light_surface.fill((0,0,0,0))
            light.light_surface.blit(light.texture, (0,0))
            
            # 2. Geometry Shadow Casting
            # We cast rays to corners + slightly offset angles to hit behind objects
            angles = set()
            for cx, cy in corners:
                dist = math.hypot(cx - lx, cy - ly)
                if dist > light.radius * 1.5:
                    continue # Skip corners way out of range
                    
                angle = math.atan2(cy - ly, cx - lx)
                angles.add(angle - 0.001)
                angles.add(angle)
                angles.add(angle + 0.001)
                
            sorted_angles = sorted(list(angles))
            polygon_points = []
            
            for angle in sorted_angles:
                length = light.radius
                end_x = lx + math.cos(angle) * length
                end_y = ly + math.sin(angle) * length
                
                # We could use collision world raycast here, but for raw speed in Python,
                # let's use the engine raycast, but we only hit walls.
                hit, hx, hy, hit_col = self.collision_world.raycast(lx, ly, end_x, end_y, mask={"wall", "cast_shadow"})
                if hit:
                    polygon_points.append((hx, hy))
                else:
                    polygon_points.append((end_x, end_y))
            
            # 3. Apply shadow polygons to light surface
            # We actually need to draw black outside the polygon, which means we draw the
            # bright polygon.
            # But wait: if we draw the polygon white and MULTIPLY against the gradient...
            # The easiest way: draw the texture on light_map, but wait we need the geometry mask.
            # Simpler pure-pygame approach:
            if len(polygon_points) >= 3:
                # Create mask surface
                mask = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
                mask.fill((0,0,0,0)) # fully transparent
                pygame.draw.polygon(mask, (255,255,255,255), polygon_points)
                
                # Draw the gradient centered at light position onto a temp surface
                temp = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
                temp.blit(light.texture, (lx - light.radius, ly - light.radius))
                
                # Multiply logic: only keep gradient where mask is drawn
                temp.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                
                # Add this light's contribution to the global light map
                self.light_map.blit(temp, (0,0), special_flags=pygame.BLEND_RGB_ADD)
            else:
                # No shadows or too few points, just add it directly
                self.light_map.blit(light.texture, (lx - light.radius, ly - light.radius), special_flags=pygame.BLEND_RGB_ADD)
                
        # 4. Multiply LightMap onto Game Surface
        surface.blit(self.light_map, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

class PlayerController(PhysicsBody2D):
    def __init__(self, name, x, y, cw):
        col = Collider2D(name+"Col", 0, 0, 20, 20)
        col.layer = "cast_shadow"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = False
        self.speed = 250.0
        
        self.add_child(col)
        self.add_child(RectangleNode("PVis", 0, 0, 20, 20, (200, 200, 200)))
        
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

def main():
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 9: Dynamic Lighting (BLEND_ADD, Multipass Shadows)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)
    
    # Outer boundaries
    def wall(x,y,w,h):
        w_node = Node2D(f"W_{x}_{y}", x, y)
        col = Collider2D(f"C_{x}_{y}", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        w_node.add_child(col)
        w_node.add_child(RectangleNode(f"V_{x}_{y}", 0, 0, w, h, (50, 50, 50)))
        root.add_child(w_node)
        
    wall(0, 0, 800, 20)
    wall(0, 580, 800, 20)
    wall(0, 0, 20, 600)
    wall(780, 0, 20, 600)
    
    # Pillars
    wall(200, 200, 50, 50)
    wall(500, 150, 40, 100)
    wall(300, 400, 150, 40)
    wall(650, 450, 60, 60)
    
    player = PlayerController("Player", 100, 100, cw)
    root.add_child(player)
    
    # Lighting System
    lighting = LightingSystem("Lighting", cw)
    
    player_light = PointLight("PLight", 10, 10, 300, (255, 200, 150))
    player.add_child(player_light)
    lighting.add_light(player_light)
    
    root.add_child(lighting)
    
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
                if event.key == pygame.K_l:
                    # Saturation test -> spawn static random light
                    x = random.randint(50, 750)
                    y = random.randint(50, 550)
                    r = random.randint(50, 255); g = random.randint(50, 255); b = random.randint(50, 255)
                    sl = PointLight(f"StaticL_{x}_{y}", x, y, random.randint(150, 350), (r, g, b))
                    root.add_child(sl)
                    lighting.add_light(sl)
                    
        profiler.begin("Logic")
        while accumulator >= fixed_dt:
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Logic")
            
        profiler.begin("Render")
        # Base scene render
        # We need to render the standard scene before the lighting overlays it via MULTIPLY
        game_surface.fill((100, 100, 100)) # Under base color
        
        # Render all children EXCEPT the LightingSystem (so they are lit)
        for child in root.children:
            if child is not lighting:
                child.render(game_surface)
                
        # Now render the lighting map on top of the rendered scene
        lighting.render(game_surface)
        
        hud_lines = [
            f"FPS: {clock.get_fps():.1f}",
            f"Lights Count: {len(lighting.lights)}",
            f"Press 'L' to span random lights (Saturation Test)"
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
