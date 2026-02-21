import pygame
import sys
import random
from typing import Optional

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.tween import TweenManager, Easing
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.collision.area2d import Area2D

class SimplePlayer(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.movespeed = 350.0 # Slightly faster
        self.jumpforce = 500.0

    def update(self, delta):
        keys = pygame.key.get_pressed()
        move_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir += 1
        
        self.velocity_x = move_dir * self.movespeed
        
        # Ground check for jump
        probe_offset = 2.0
        result = self.collision_world.check_collision(
            self.collider,
            self.local_x,
            self.local_y + probe_offset
        )
        is_grounded = result.collided and result.normal_y < 0
        
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and is_grounded:
            self.velocity_y = -self.jumpforce

        super().update(delta)

class SimpleSpring(Area2D):
    def __init__(self, name, x, y, width=40, height=20, boost=-1100.0):
        super().__init__(name, x, y, width, height)
        self.boost = boost
        self.collider.layer = "spring"
        self.collider.mask = {"player"}
        
        self.vis = Node2D(name + "_Vis", 0, 0)
        self.vis.add_child(RectangleNode("Base", 0, height*0.75, width, height*0.25, (100, 100, 100)))
        self.vis.add_child(RectangleNode("Top", 0, 0, width, height*0.5, (255, 60, 60)))
        self.add_child(self.vis)

    def on_area_entered(self, body):
        if hasattr(body, "velocity_y"):
            # Trigger jump if landing on spring
            if body.velocity_y >= -100: 
                body.velocity_y = self.boost

class SimpleTrophy(Area2D):
    def __init__(self, name, x, y):
        super().__init__(name, x, y, 40, 40)
        self.add_child(RectangleNode(name + "_Vis", 0, 0, 40, 40, (255, 215, 0)))
        
    def on_area_entered(self, body):
        print("YOU WIN!")

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Mega-Spring Bounce (Refined)")
    clock = pygame.time.Clock()

    root = Node2D("Root")
    tween_manager = TweenManager("TweenManager")
    root.add_child(tween_manager)
    
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)
    
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    # ---------------- Player ----------------
    player_col = Collider2D("PlayerCol", 0, 0, 40, 40)
    player_col.layer = "player"
    player_col.mask = {"wall", "spring"}
    player = SimplePlayer("Player", 400, 500, player_col, collision_world)
    visual_world.add_child(player)
    player.add_child(player_col)
    player.add_child(RectangleNode("PlayerVis", 0, 0, 40, 40, (50, 255, 50)))

    # ---------------- Helpers ----------------
    def create_platform(name, x, y, w, h):
        plat = Node2D(name, x, y)
        visual_world.add_child(plat)
        col = Collider2D(name + "Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player"}
        plat.add_child(col)
        plat.add_child(RectangleNode(name + "Vis", 0, 0, w, h, (100, 100, 120)))
        return plat

    def spawn_spring(name, x, y, boost=-1100.0):
        spring = SimpleSpring(name, x, y, boost=boost)
        visual_world.add_child(spring)
        return spring

    # ---------------- Level Design ----------------
    create_platform("Ground", 0, 580, 800, 20)
    for i in range(10):
        y_pos = 400 - i * 350
        x_pos = 200 if i % 2 == 0 else 550
        spawn_spring(f"Spring_{i}", x_pos, y_pos)
        create_platform(f"Plat_{i}", x_pos - 50, y_pos + 50, 150, 10)

    spawn_spring("MegaLaunch", 400, -3200, boost=-2200.0)
    create_platform("GoalPlatform", 300, -3500, 200, 20)
    trophy = SimpleTrophy("WinTrophy", 380, -3550)
    visual_world.add_child(trophy)

    # ---------------- Camera ----------------
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = camera 

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

        if player.local_y > 800:
            player.local_y = 500
            player.local_x = 400
            player.velocity_y = 0

        screen.fill((10, 10, 15)) 
        root.render(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
