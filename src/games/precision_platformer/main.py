import pygame
import sys

from src.engine.scene.node2d import Node2D
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.fsm.state_machine import StateMachine
from src.engine.fsm.state import State
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600
TILE_SIZE = 32

MAP = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X                               X",
    "X                               X",
    "X       XXXXX                   X",
    "X                               X",
    "X             XXX               X",
    "X    XX                         X",
    "X           XXXX       XX       X",
    "X                               X",
    "X  XXXX                         X",
    "X                               X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]

class PlatformerPlayer(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.gravity = 1200.0
        
        self.movespeed = 250.0
        self.jumpforce = 450.0
        
        # Mechanics
        self.coyote_timer = 0.0
        self.coyote_time_max = 0.1
        self.jump_buffer = 0.0
        self.jump_buffer_max = 0.1
        
        self.fsm = StateMachine(self)
        self.is_grounded = False
        self.was_jump_pressed = False
        
        # Drift tracking
        self.initial_y = None
        self.resting = False

    def update(self, delta):
        # 1. Ground detection probe
        probe = self.collision_world.check_collision(self.collider, self.local_x, self.local_y + 1.0)
        self.is_grounded = probe.collided and probe.normal_y < 0
        
        if self.is_grounded:
            self.coyote_timer = self.coyote_time_max
            # Track drift for the marathon test if strictly stationary
            if abs(self.velocity_x) < 1.0 and self.velocity_y == 0:
                if self.initial_y is None:
                    self.initial_y = self.local_y
                self.resting = True
            else:
                self.resting = False
        else:
            self.coyote_timer -= delta
            self.resting = False
            
        keys = pygame.key.get_pressed()
        jump_wants = keys[pygame.K_SPACE] or keys[pygame.K_w]
        
        if jump_wants and not self.was_jump_pressed:
            self.jump_buffer = self.jump_buffer_max
        elif not jump_wants:
            self.jump_buffer -= delta
            
        self.was_jump_pressed = jump_wants
            
        # 2. Execute Jump
        if self.jump_buffer > 0 and self.coyote_timer > 0:
            self.velocity_y = -self.jumpforce
            self.jump_buffer = 0.0
            self.coyote_timer = 0.0
            self.is_grounded = False
            
        # Variable jump height (release early to hop)
        if not jump_wants and self.velocity_y < 0:
            self.velocity_y *= 0.5
            
        # 3. Horizontal movement
        move_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_dir += 1
        
        target_vx = move_dir * self.movespeed
        # Tight acceleration (avoids ice physics)
        accel = 20.0 if self.is_grounded else 10.0
        self.velocity_x += (target_vx - self.velocity_x) * accel * delta
        
        # The physics update will do move_and_collide
        super().update(delta)
        
        # 4. FSM Logic
        self.fsm.update(delta)

# Engine Level 5 FSM integration
class IdleState(State):
    def update(self, delta):
        if abs(self.body.velocity_x) > 10: 
            self.body.fsm.change_state(RunState(self.body))
        elif not self.body.is_grounded: 
            self.body.fsm.change_state(FallState(self.body))
            
class RunState(State):
    def update(self, delta):
        if abs(self.body.velocity_x) <= 10: 
            self.body.fsm.change_state(IdleState(self.body))
        elif not self.body.is_grounded: 
            self.body.fsm.change_state(FallState(self.body))
            
class FallState(State):
    def update(self, delta):
        if self.body.is_grounded: 
            self.body.fsm.change_state(IdleState(self.body))

def build_tilemap(visual_world, collision_world):
    for y, row in enumerate(MAP):
        for x, char in enumerate(row):
            if char == 'X':
                px, py = x * TILE_SIZE, y * TILE_SIZE
                name = f"Wall_{x}_{y}"
                wall = Node2D(name, px, py)
                col = Collider2D(name+"Col", 0, 0, TILE_SIZE, TILE_SIZE, is_static=True)
                col.layer = "wall"
                col.mask = {"player"}
                
                wall.add_child(col)
                wall.add_child(RectangleNode(name+"Vis", 0, 0, TILE_SIZE, TILE_SIZE, (60, 60, 80)))
                
                visual_world.add_child(wall)

def main():
    pygame.init()
    screen = pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H), pygame.RESIZABLE)
    game_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    pygame.display.set_caption("Level 2: Precision Platformer (Float Drift & FSM)")
    clock = pygame.time.Clock()
    
    profiler = EngineProfiler()
    
    root = Node2D("Root")
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)
    
    # Map
    build_tilemap(visual_world, collision_world)
    
    # Player
    player_col = Collider2D("PlayerCol", 0, 0, 24, 30)
    player_col.layer = "player"
    player_col.mask = {"wall"}
    
    # Start above the floor
    player = PlatformerPlayer("Player", 64, 64, player_col, collision_world)
    player.fsm.change_state(FallState(player))
    visual_world.add_child(player)
    player.add_child(player_col)
    
    vis = RectangleNode("PlayerVis", 0, 0, 24, 30, (50, 200, 200))
    player.add_child(vis)
    
    # Camera
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = camera
    
    font = pygame.font.SysFont("Arial", 16)
    marathon_timer = 0.0
    
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
                
        profiler.begin("Logic")
        while accumulator >= fixed_dt:
            # 60s float drift check
            marathon_timer += fixed_dt
            if marathon_timer >= 60.0:
                marathon_timer = 0.0
                if player.resting and player.initial_y is not None:
                    drift = player.local_y - player.initial_y
                    print(f"[MARATHON] Resting Float Drift over 60s: {drift:.6f} pixels")
                    if abs(drift) > 0.1:
                        print("WARNING: High float drift detected!")
                        
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
        profiler.end("Logic")
            
        profiler.begin("Render")
        game_surface.fill((30, 40, 50))
        root.render(game_surface)
        
        hud_lines = [
            f"FPS: {clock.get_fps():.1f}",
            f"State: {player.fsm.current_state.__class__.__name__ if player.fsm.current_state else 'None'}",
            f"Drift Base Y: {player.initial_y if player.initial_y else 'Wait'}",
            f"Resting?: {player.resting}"
        ]
        
        # Color the player based on state
        if isinstance(player.fsm.current_state, IdleState): vis.color = (50, 200, 50)
        elif isinstance(player.fsm.current_state, RunState): vis.color = (200, 200, 50)
        elif isinstance(player.fsm.current_state, FallState): vis.color = (200, 50, 50)
        
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
