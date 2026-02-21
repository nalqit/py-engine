import pygame
import sys
import random
from typing import Optional

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.tween import TweenManager
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.collision.area2d import Area2D

class SimplePlayer(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world, on_die_callback):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.speed = 450.0 # Faster for better dodging
        self.on_die = on_die_callback

    def update(self, delta):
        keys = pygame.key.get_pressed()
        move_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir += 1
        self.velocity_x = move_dir * self.speed
        super().update(delta)
        
    def die(self):
        print("PLAYER DIED! Resetting...")
        self.on_die()

class SimpleSpike(Area2D):
    def __init__(self, name, x, y, speed=300.0):
        super().__init__(name, x, y, 40, 40)
        self.speed = speed
        self.collider.mask = {"player"}
        self.add_child(RectangleNode(name + "_Vis", 0, 0, 40, 40, (255, 50, 50)))
        
    def update(self, delta):
        self.local_y += self.speed * delta
        if self.local_y > 700:
            if self.parent:
                self.parent.remove_child(self)
        super().update(delta)

    def on_area_entered(self, body):
        if hasattr(body, "die"):
            body.die()

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Spike Rain (Refined)")
    clock = pygame.time.Clock()

    root = Node2D("Root")
    tween_manager = TweenManager("TweenManager")
    root.add_child(tween_manager)
    
    # Visual World
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)
    
    # ADD COLLISION WORLD AFTER VISUAL WORLD
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    # State
    game_state = {
        "score": 0.0,
        "spawn_timer": 0.0,
        "spawn_rate": 0.7, # Slower start
        "is_game_over": False
    }

    def reset_game():
        game_state["score"] = 0.0
        game_state["spawn_timer"] = 0.0
        game_state["spawn_rate"] = 0.7
        player.local_x = 400
        player.local_y = 500
        player.velocity_x = 0
        player.velocity_y = 0
        player.update_transforms()
        # Remove all spikes
        to_remove = [c for c in visual_world.children if isinstance(c, SimpleSpike)]
        for s in to_remove:
            visual_world.remove_child(s)

    # ---------------- Player ----------------
    player_col = Collider2D("PlayerCol", 0, 0, 40, 40)
    player_col.layer = "player"
    player_col.mask = {"wall", "coin"}
    player = SimplePlayer("Player", 400, 500, player_col, collision_world, reset_game)
    visual_world.add_child(player)
    player.add_child(player_col)
    player.add_child(RectangleNode("PlayerVis", 0, 0, 40, 40, (100, 100, 255)))

    # ---------------- Arena ----------------
    def create_wall(name, x, y, w, h):
        wall = Node2D(name, x, y)
        visual_world.add_child(wall)
        col = Collider2D(name + "Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player"}
        wall.add_child(col)
        wall.add_child(RectangleNode(name + "Vis", 0, 0, w, h, (50, 50, 60)))
        return wall

    create_wall("Floor", 0, 550, 800, 50)
    create_wall("LeftWall", -50, 0, 50, 600)
    create_wall("RightWall", 800, 0, 50, 600)

    # ---------------- Main Loop ----------------
    running = True
    fixed_dt = 1/60.0
    accumulator = 0.0
    while running:
        dt = clock.tick(60) / 1000.0
        accumulator += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        while accumulator >= fixed_dt:
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt
            
            game_state["spawn_timer"] += fixed_dt
            if game_state["spawn_timer"] >= game_state["spawn_rate"]:
                game_state["spawn_timer"] = 0
                game_state["score"] += 1
                spike = SimpleSpike(f"Spike_{int(game_state['score'])}", 
                                    random.randint(0, 760), -50, 
                                    speed=random.randint(150, 350)) # Slower spikes
                visual_world.add_child(spike)
                # MUCH slower difficulty ramp
                game_state["spawn_rate"] = max(0.2, 0.7 - (game_state["score"] * 0.002))

        screen.fill((20, 20, 25)) 
        root.render(screen)
        font = pygame.font.SysFont("Arial", 24)
        score_surf = font.render(f"Score: {int(game_state['score'])}", True, (255, 255, 255))
        screen.blit(score_surf, (10, 50))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
