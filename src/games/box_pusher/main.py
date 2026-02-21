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
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.movespeed = 350.0 # Snappy movement
        self.jumpforce = 500.0
        self.intended_vx = 0.0

    def update(self, delta):
        keys = pygame.key.get_pressed()
        move_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir += 1
        
        self.intended_vx = move_dir * self.movespeed
        self.velocity_x = self.intended_vx
        
        # Ground check
        probe_offset = 2.0
        result = self.collision_world.check_collision(self.collider, self.local_x, self.local_y + probe_offset)
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and result.collided and result.normal_y < 0:
            self.velocity_y = -self.jumpforce

        super().update(delta)

    def on_collision_stay(self, other):
        """Forcefully push boxes when touching."""
        body = other.parent
        if isinstance(body, SimpleBox):
            # If we are walking into the box's side
            # Check horizontal distance to be sure we are on the side
            px, py = self.get_global_position()
            bx, by = body.get_global_position()
            
            # Simple side check: if intended move matches relative direction
            is_to_right = bx > px
            if (self.intended_vx > 0 and is_to_right) or (self.intended_vx < 0 and not is_to_right):
                 # Directly match velocity to player for "sticky" pushing
                 body.velocity_x = self.intended_vx

class SimpleBox(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.friction = 800.0 # High friction so it stops quickly when not pushed

    def update(self, delta):
        # Apply friction
        if self.velocity_x > 0:
            self.velocity_x = max(0, self.velocity_x - self.friction * delta)
        elif self.velocity_x < 0:
            self.velocity_x = min(0, self.velocity_x + self.friction * delta)
        super().update(delta)

class SimpleButton(Area2D):
    def __init__(self, name, x, y):
        super().__init__(name, x, y, 60, 10)
        self.is_pressed = False
        self.collider.mask = {"player", "box"}
        self.vis = RectangleNode(name + "_Vis", 0, 0, 60, 10, (150, 50, 50))
        self.add_child(self.vis)
        
    def on_area_entered(self, body):
        self.is_pressed = True
        self.vis.color = (50, 200, 50)
        
    def on_area_exited(self, body):
        if not self.overlapping_bodies:
            self.is_pressed = False
            self.vis.color = (150, 50, 50)

class SimpleTrophy(Area2D):
    def __init__(self, name, x, y):
        super().__init__(name, x, y, 40, 40)
        self.add_child(RectangleNode(name + "_Vis", 0, 0, 40, 40, (255, 215, 0)))
        
    def on_area_entered(self, body):
        print("CONGRATULATIONS! YOU WIN!")

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Box Pusher - Fixed Edition")
    clock = pygame.time.Clock()

    root = Node2D("Root")
    tween_manager = TweenManager("TweenManager")
    root.add_child(tween_manager)
    
    # Order: Visuals then Collision for input-to-event accuracy
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    # ---------------- Arena ----------------
    def create_wall(name, x, y, w, h):
        wall = Node2D(name, x, y)
        visual_world.add_child(wall)
        col = Collider2D(name + "Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player", "box"}
        wall.add_child(col)
        wall.add_child(RectangleNode(name + "Vis", 0, 0, w, h, (60, 60, 70)))
        return wall

    create_wall("Floor", 0, 500, 800, 100)
    create_wall("LeftWall", 0, 0, 20, 600)
    create_wall("RightWall", 780, 0, 20, 600)

    # ---------------- Boxes ----------------
    def spawn_box(name, x, y):
        box_col = Collider2D(name + "Col", 0, 0, 50, 50)
        box_col.layer = "box"
        box_col.mask = {"wall", "box"} # Box doesn't mask player to avoid stopping the push
        box = SimpleBox(name, x, y, box_col, collision_world)
        visual_world.add_child(box)
        box.add_child(box_col)
        box.add_child(RectangleNode(name + "Vis", 0, 0, 50, 50, (220, 170, 70)))
        return box

    box1 = spawn_box("Box1", 300, 400)
    box2 = spawn_box("Box2", 500, 400)

    button1 = SimpleButton("Button1", 600, 490)
    visual_world.add_child(button1)
    button2 = SimpleButton("Button2", 200, 490)
    visual_world.add_child(button2)

    trophy_spawned = False

    # ---------------- Player (Added Last to Update Last) ----------------
    player_col = Collider2D("PlayerCol", 0, 0, 40, 48)
    player_col.layer = "player"
    player_col.mask = {"wall", "box"}
    player = SimplePlayer("Player", 100, 400, player_col, collision_world)
    visual_world.add_child(player)
    player.add_child(player_col)
    player.add_child(RectangleNode("PlayerVis", 0, 0, 40, 48, (255, 100, 100)))

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
            
            if button1.is_pressed and button2.is_pressed and not trophy_spawned:
                trophy_spawned = True
                trophy = SimpleTrophy("WinTrophy", 400, 450)
                visual_world.add_child(trophy)

        screen.fill((25, 25, 30)) 
        root.render(screen)
        font = pygame.font.SysFont("Arial", 20)
        text = "Push both boxes onto red buttons! (WASD to Move)"
        screen.blit(font.render(text, True, (255, 255, 255)), (220, 40))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
