import pygame
import sys

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.game.entities.player import Player
from src.game.entities.box import Box
from src.game.entities.npc import NPC
from src.engine.ui.stats_hud import StatsHUD
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.parallax import ParallaxBackground, ParallaxLayer
from src.game.entities.coin import Coin
import random


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("PyEngine 2D - Showcase Level")
    clock = pygame.time.Clock()

    # Root
    root = Node2D("Root")

    # Collision World
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    # ---------------- Parallax Background ----------------
    parallax_bg = ParallaxBackground("Background")
    root.add_child(parallax_bg)

    # Layer 0: Distant Clouds (moves 5%)
    clouds = ParallaxLayer("Clouds", parallax_factor=(0.05, 0.02))
    parallax_bg.add_child(clouds)
    for i in range(-5, 10):
        c = RectangleNode(f"Cloud{i}", i * 500, random.randint(50, 150), 200, 60, (200, 200, 220))
        clouds.add_child(c)

    # Layer 1: Far Mountains (moves 15%)
    mountains = ParallaxLayer("Mountains", parallax_factor=(0.15, 0.05))
    parallax_bg.add_child(mountains)
    for i in range(-5, 10):
        m = RectangleNode(f"Mtn{i}", i * 600, 250, 400, 350, (40, 40, 70))
        mountains.add_child(m)

    # Layer 2: Mid Hills (moves 35%)
    hills = ParallaxLayer("Hills", parallax_factor=(0.35, 0.1))
    parallax_bg.add_child(hills)
    for i in range(-10, 20):
        h = RectangleNode(f"Hill{i}", i * 300, 400, 250, 200, (60, 90, 60))
        hills.add_child(h)

    # Visual World (The Ground Layer)
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)

    # ---------------- Player ----------------
    player_col = Collider2D("PlayerCol", 0, 0, 50, 50)
    player_col.layer = "player"
    player_col.mask = {"wall", "box", "npc", "coin"}

    player = Player(
        "Player",
        x=100, y=100,
        collider=player_col,
        collision_world=collision_world,
    )
    visual_world.add_child(player)
    player.add_child(player_col)

    player_vis = RectangleNode("PlayerVis", 0, 0, 50, 50, (255, 50, 50))
    player.add_child(player_vis)

    # ---------------- Walls & Entities Helper ----------------
    def create_wall(name, x, y, w, h, color=(100, 100, 100)):
        wall = Node2D(name, x, y)
        visual_world.add_child(wall)
        col = Collider2D(name + "Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player", "box", "npc"}
        wall.add_child(col)
        vis = RectangleNode(name + "Vis", 0, 0, w, h, color)
        wall.add_child(vis)

    # 1. THE START AREA
    create_wall("Floor_Start", -500, 500, 1500, 100)
    create_wall("Wall_LeftLimit", -500, -500, 50, 1000)
    
    # 2. THE JUMP CHALLENGE (Floating Platforms)
    create_wall("Plat_Jump1", 400, 350, 150, 20, (150, 100, 50))
    visual_world.add_child(Coin("Coin1", 460, 300))
    
    create_wall("Plat_Jump2", 700, 250, 150, 20, (150, 100, 50))
    visual_world.add_child(Coin("Coin2", 760, 200))
    
    create_wall("Plat_Jump3", 400, 150, 100, 20, (150, 100, 50))
    visual_world.add_child(Coin("Coin3", 440, 100))

    # 3. PHYSICS PLAYGROUND (Boxes & Space)
    create_wall("Floor_Physics", 1200, 450, 1000, 150, (80, 80, 80))
    # Scatter some boxes
    for i in range(5):
        box_col = Collider2D(f"BoxCol{i}", 0, 0, 50, 50, is_static=False)
        box_col.layer = "box"
        box_col.mask = {"wall", "player", "npc", "box"}
        box = Box(f"Box{i}", x=1300 + i*150, y=100, collider=box_col, collision_world=collision_world)
        visual_world.add_child(box)
        box.add_child(box_col)
        box.add_child(RectangleNode(f"BoxVis{i}", 0, 0, 50, 50, (200, 150, 50)))
        visual_world.add_child(Coin(f"BoxCoin{i}", 1320 + i*150, 400))

    # 4. THE NPC VILLAGE
    for i in range(3):
        npc_col = Collider2D(f"NPCCol{i}", 0, 0, 40, 40)
        npc_col.layer = "npc"
        npc_col.mask = {"wall", "player", "box"}
        npc = NPC(f"NPC{i}", x=1500 + i*250, y=350, collider=npc_col, collision_world=collision_world)
        visual_world.add_child(npc)
        npc.add_child(npc_col)
        npc.add_child(RectangleNode(f"NPCVis{i}", 0, 0, 40, 40, (0, 200, 255)))

    # 5. THE PIT & HIGH REWARD
    create_wall("Floor_Far", 2500, 500, 500, 100)
    create_wall("Plat_HighReward", 2600, 100, 200, 20, (255, 215, 0))
    for i in range(5):
        visual_world.add_child(Coin(f"SuperCoin{i}", 2620 + i*30, 50))

    # ---------------- Camera ----------------
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = player

    # ---------------- HUD ----------------
    hud = StatsHUD("HUD", root, clock)
    root.add_child(hud)

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

        screen.fill((30, 30, 40)) # Slightly bluer sky
        root.render(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
