import pygame
import sys
import time
import math

from src.engine.scene.node2d import Node2D
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600
TILE_SIZE = 40

ROOMS_DATA = {
    (0,0): [
        "XXXXXXXXXXXXXXXXXXXX",
        "X                  X",
        "X      P           X",
        "X                  X",
        "X        XXXX       ",
        "X                   ",
        "X                   ",
        "X     X             ",
        "X           XXXXXXXX",
        "X                  X",
        "X                  X",
        "X                  X",
        "X                  X",
        "X                  X",
        "XXXXXXXXXXXXXXXXXXXX"
    ],
    (1,0): [
        "XXXXXXXXXXXXXXXXXXXX",
        "X                  X",
        "X                  X",
        "X                   ",
        "        X           ",
        "           X        ",
        "              X     ",
        "                    ",
        "XXXXXXXXX           ",
        "X                  X",
        "X                  X",
        "X                  X",
        "X                   ",
        "X                   ",
        "XXXXXXXXXXXXXXXXXXXX"
    ],
    (2,0): [
        "XXXXXXXXXXXXXXXXXXXX",
        "X                  X",
        "X                  X",
        "                   X",
        "           XXXX    X",
        "        X          X",
        "     X             X",
        "   X               X",
        "                   X",
        "X                  X",
        "X                  X",
        "X                  X",
        "                   X",
        "                   X",
        "XXXXXXXXXXXXXXXXXXXX"
    ],
    (1,1): [ # Below (1,0)
        "X                  X",
        "X                  X",
        "X                  X",
        "X                   ",
        "                 XXX",
        "                    ",
        "     XXXXXX         ",
        "                    ",
        "X                   ",
        "X                  X",
        "X                  X",
        "X                  X",
        "X                  X",
        "X                  X",
        "XXXXXXXXXXXXXXXXXXXX"
    ],
    (2,1): [ # Below (2,0)
        "                   X",
        "                   X",
        "                   X",
        "                    ",
        "XXX                 ",
        "         X          ",
        "             X      ",
        "                 X  ",
        "X                  X",
        "X                  X",
        "X                  X",
        "X                  X",
        "X                  X",
        "X                  X",
        "XXXXXXXXXXXXXXXXXXXX"
    ]
}

ROOM_W = 20 * TILE_SIZE
ROOM_H = 15 * TILE_SIZE

class MetroidvaniaPlayer(PhysicsBody2D):
    def __init__(self, name, x, y, cw):
        col = Collider2D(name+"Col", 0, 0, 20, 30)
        col.layer = "player"
        col.mask = {"wall"}
        super().__init__(name, x, y, col, cw)
        self.use_gravity = True
        self.gravity = 1200.0
        self.movespeed = 250.0
        self.jumpforce = 500.0
        
        self.add_child(col)
        self.vis = RectangleNode("PVis", 0, 0, 20, 30, (255, 100, 100))
        self.add_child(self.vis)
        
        self.is_grounded = False
        
    def update(self, delta):
        probe = self.collision_world.check_collision(self.collider, self.local_x, self.local_y + 1.0)
        self.is_grounded = probe.collided and probe.normal_y < 0
        
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_SPACE] and self.is_grounded:
            self.velocity_y = -self.jumpforce
            
        move_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_dir += 1
        
        target_vx = move_dir * self.movespeed
        self.velocity_x += (target_vx - self.velocity_x) * 15.0 * delta
        
        super().update(delta)

class WorldManager:
    def __init__(self, root, cw):
        self.root = root
        self.cw = cw
        self.loaded_rooms = {}  # (rx, ry) -> Node2D grouping walls
        
    def load_room(self, rx, ry):
        if (rx, ry) in self.loaded_rooms or (rx, ry) not in ROOMS_DATA:
            return
            
        room_node = Node2D(f"Room_{rx}_{ry}", rx * ROOM_W, ry * ROOM_H)
        
        # Color based on room coords for visual debugging
        r_col = (100 + (rx*30)%100, 100 + (ry*40)%100, 150)
        
        for y, row in enumerate(ROOMS_DATA[(rx, ry)]):
            for x, char in enumerate(row):
                if char == 'X':
                    wall = Node2D(f"W_{x}_{y}", x * TILE_SIZE, y * TILE_SIZE)
                    col = Collider2D(f"WC_{x}_{y}", 0, 0, TILE_SIZE, TILE_SIZE, is_static=True)
                    col.layer = "wall"
                    col.mask = {"player"}
                    wall.add_child(col)
                    wall.add_child(RectangleNode(f"WV_{x}_{y}", 0, 0, TILE_SIZE, TILE_SIZE, r_col))
                    room_node.add_child(wall)
                    
        self.root.add_child(room_node)
        self.loaded_rooms[(rx, ry)] = room_node
        
    def unload_room(self, rx, ry):
        if (rx, ry) in self.loaded_rooms:
            room_node = self.loaded_rooms.pop((rx, ry))
            self.root.remove_child(room_node)
            
    def update_loaded_chunks(self, player_rx, player_ry):
        import time
        start_t = time.perf_counter()
        
        needed = {
            (player_rx, player_ry),
            (player_rx+1, player_ry),
            (player_rx-1, player_ry),
            (player_rx, player_ry+1),
            (player_rx, player_ry-1)
        }
        
        current = set(self.loaded_rooms.keys())
        
        to_load = needed - current
        to_unload = current - needed
        
        for r in to_load: self.load_room(*r)
        for r in to_unload: self.unload_room(*r)
        
        load_time_ms = (time.perf_counter() - start_t) * 1000
        
        if to_load or to_unload:
            # Count nodes
            def count_nodes(n):
                c = 1
                for child in n.children: c += count_nodes(child)
                return c
            total_nodes = count_nodes(self.root)
            print(f"[TRANSITION] Loaded {len(to_load)}, Unloaded {len(to_unload)}. " 
                  f"Time: {load_time_ms:.2f}ms. Total Scene Nodes: {total_nodes}")

def main():
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 6: Metroidvania (Room Chunking & Streaming)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    cw = CollisionWorld("CollisionWorld")
    root.add_child(cw)
    
    world_mgr = WorldManager(root, cw)
    
    player = MetroidvaniaPlayer("Player", 250, 100, cw)
    root.add_child(player)
    
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = camera
    
    font = pygame.font.SysFont("Arial", 16)
    
    running = True
    fixed_dt = 1/60.0
    accumulator = 0.0
    
    current_rx, current_ry = 0, 0
    world_mgr.update_loaded_chunks(current_rx, current_ry)
    
    while running:
        dt = clock.tick(60) / 1000.0
        profiler.log_frame(dt)
        accumulator += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        profiler.begin("Logic")
        while accumulator >= fixed_dt:
            # Check room transition
            prx = math.floor((player.local_x + player.collider.width/2) / ROOM_W)
            pry = math.floor((player.local_y + player.collider.height/2) / ROOM_H)
            
            if (prx, pry) != (current_rx, current_ry):
                current_rx, current_ry = prx, pry
                world_mgr.update_loaded_chunks(current_rx, current_ry)
            
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Logic")
            
        profiler.begin("Render")
        game_surface.fill((20, 20, 30))
        root.render(game_surface)
        
        hud_lines = [
            f"FPS: {clock.get_fps():.1f}",
            f"Current Room: ({current_rx}, {current_ry})",
            f"Loaded Rooms: {len(world_mgr.loaded_rooms)}",
            f"Mem: {profiler.get_memory_mb():.1f} MB",
            "Move across screen boundaries to stream rooms!"
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
