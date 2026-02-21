import pygame
import sys
import random
from typing import Optional

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.game.entities.player import Player
from src.game.entities.box import Box
from src.game.entities.npc import NPC
from src.engine.ui.stats_hud import StatsHUD
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.tween import TweenManager
from src.engine.scene.sprite_node import SpriteNode
from src.game.entities.coin import Coin
from src.game.entities.patrol_enemy import PatrolEnemy
from src.game.entities.spring import Spring
from src.game.entities.spike import Spike

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("PyEngine 2D - The Great Adventure")
    clock = pygame.time.Clock()

    # Root
    root = Node2D("Root")
    
    # Tween Manager (Global)
    tween_manager = TweenManager("TweenManager")
    root.add_child(tween_manager)

    # Collision World
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    # ---------------- Background ----------------
    # One large background image for the entire world
    bg = SpriteNode("Background", "src/game/background_layer_1.png", 0, 0)
    bg.scale_x = 10.0 # Make it very wide
    bg.scale_y = 2.0
    root.add_child(bg)

    # Visual World
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)

    # ---------------- Player ----------------
    player_col = Collider2D("PlayerCol", 0, 0, 50, 50)
    player_col.layer = "player"
    player_col.mask = {"wall", "box", "npc", "coin"}

    player = Player("Player", 100, 400, player_col, collision_world)
    visual_world.add_child(player)
    player.add_child(player_col)
    player.add_child(RectangleNode("PlayerVis", 0, 0, 50, 50, (255, 50, 50)))

    # ---------------- Helpers ----------------
    def create_wall(name, x, y, w, h, color=(80, 80, 90)):
        wall = Node2D(name, x, y)
        visual_world.add_child(wall)
        col = Collider2D(name + "Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player", "box", "npc"}
        wall.add_child(col)
        wall.add_child(RectangleNode(name + "Vis", 0, 0, w, h, color))
        return wall

    def spawn_coin(name, x, y):
        coin = Coin(name, x, y)
        visual_world.add_child(coin)
        return coin

    # ---------------- Map Design ----------------
    def spawn_enemy(name, x, y):
        enemy_col = Collider2D(name + "Col", 0, 0, 40, 40)
        enemy_col.layer = "enemy"
        enemy_col.mask = {"wall", "player", "box"}
        enemy = PatrolEnemy(name, x, y, enemy_col, collision_world, speed=60.0)
        visual_world.add_child(enemy)
        enemy.add_child(enemy_col)
        enemy.add_child(RectangleNode(name + "Vis", 0, 0, 40, 40, (200, 50, 200)))
        return enemy

    def spawn_spring(name, x, y):
        spring = Spring(name, x, y)
        spring.get_node(name + "_Col").mask = {"player", "box", "npc"}
        visual_world.add_child(spring)
        spring.add_child(RectangleNode(name + "_Vis", 0, 0, 40, 20, (50, 200, 50)))
        return spring
        
    def spawn_spike(name, x, y):
        spike = Spike(name, x, y, 40, 40)
        visual_world.add_child(spike)
        # Visual representation: Red square for now
        spike.add_child(RectangleNode(name + "_Vis", 0, 0, 40, 40, (255, 0, 0)))
        return spike

    # 1. HUGE FLOOR
    create_wall("Ground", -1000, 500, 5000, 200)
    
    # 2. INTRO AREA (Coins spread out)
    spawn_coin("Coin_Start1", 300, 450)
    spawn_coin("Coin_Start2", 500, 450)
    spawn_coin("Coin_Start3", 700, 450)
    
    # Spawn first enemy patrolling the start area
    spawn_enemy("Enemy1", 600, 450)

    # 3. VERTICAL CHALLENGE
    create_wall("Wall_Blocker", 900, 400, 50, 100)
    create_wall("Plat_1", 1000, 350, 200, 20)
    spawn_coin("Coin_Plat1", 1080, 300)
    
    create_wall("Plat_2", 1300, 250, 200, 20)
    spawn_coin("Coin_Plat2", 1380, 200)
    
    create_wall("Plat_3", 1050, 150, 150, 20)
    spawn_coin("Coin_Plat3", 1100, 100)

    # 4. NPC OUTPOST
    # Enemy guarding the NPC
    spawn_enemy("Enemy2", 1500, 450)

    # Some spikes before the village
    spawn_spike("SpikeGap1", 1300, 460)
    spawn_spike("SpikeGap2", 1340, 460)
    spawn_spike("SpikeGap3", 1380, 460)

    npc_col = Collider2D("VillageNPCCol", 0, 0, 40, 40)
    npc_col.layer = "npc"
    npc_col.mask = {"wall", "player", "box"}
    npc = NPC("VillageNPC", 1800, 460, npc_col, collision_world)
    visual_world.add_child(npc)
    npc.add_child(npc_col)
    npc.add_child(RectangleNode("NPCVis", 0, 0, 40, 40, (0, 200, 255)))
    
    create_wall("Roof", 1700, 350, 300, 20, (120, 100, 80))
    spawn_coin("RoofCoin", 1840, 300)
    
    # A spring to bounce up to the roof
    spawn_spring("RoofSpring", 1600, 480)

    # 5. PHYSICS PLAYGROUND (Boxes far from coins)
    for i in range(3):
        box_col = Collider2D(f"BoxCol{i}", 0, 0, 50, 50)
        box_col.layer = "box"
        box_col.mask = {"wall", "player", "box"}
        box = Box(f"Box{i}", 2200 + i*200, 400, box_col, collision_world)
        visual_world.add_child(box)
        box.add_child(box_col)
        box.add_child(RectangleNode(f"BoxVis{i}", 0, 0, 50, 50, (200, 150, 50)))

    # ---------------- Camera ----------------
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = camera 

    # ---------------- HUD ----------------
    hud = StatsHUD("HUD", root, clock)
    root.add_child(hud)

    # ---------------- Main Loop ----------------
    running = True
    fixed_dt = 1/60.0
    accumulator = 0.0
    debug_colliders = False
    root.print_tree()
    while running:
        dt = clock.tick(60) / 1000.0
        accumulator += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    debug_colliders = not debug_colliders

        while accumulator >= fixed_dt:
            root.update_transforms()
            root.update(fixed_dt)
            accumulator -= fixed_dt

        screen.fill((30, 30, 40)) 
        root.render(screen)
        
        if debug_colliders:
            for col in collision_world._cached_colliders:
                col.render(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
