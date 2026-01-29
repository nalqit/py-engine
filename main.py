import pygame
import sys

from src.scene.node2d import Node2D
from src.scene.rectangle_node import RectangleNode
from src.scene.player import Player
from src.scene.entities.box import Box
from src.scene.entities.npc import NPC
from src.scene.ui.stats_hud import StatsHUD

from src.scene.input.input_manager import InputManager
from src.scene.collision.collider2d import Collider2D
from src.scene.collision.collision_world import CollisionWorld
from src.scene.camera2d import Camera2D


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("PyEngine 2D - Physics CLEAN")
    clock = pygame.time.Clock()

    # ======================
    # Root
    # ======================
    root = Node2D("Root")

    # ======================
    # Input
    # ======================
    input_manager = InputManager("Input")
    root.add_child(input_manager)

    # ======================
    # Collision World (NO COLLIDERS HERE)
    # ======================
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    # ======================
    # Visual World
    # ======================
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)

    # ======================
    # Player
    # ======================
    player_col = Collider2D("PlayerCol", 0, 0, 50, 50)
    player_col.layer = "player"
    player_col.mask = {"wall", "box", "npc"}

    player = Player(
        "Player",
        x=100,
        y=0,
        input_manager=input_manager,
        collider=player_col,
        collision_world=collision_world
    )
    visual_world.add_child(player)
    player.add_child(player_col)

    player_vis = RectangleNode("PlayerVis", 0, 0, 50, 50, (255, 0, 0))
    player.add_child(player_vis)

    # ======================
    # Walls (Static)
    # ======================
    def create_wall(name, x, y, w, h):
        wall = Node2D(name, x, y)
        visual_world.add_child(wall)

        col = Collider2D(name+"Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player", "box", "npc"}
        wall.add_child(col)

        vis = RectangleNode(name+"Vis", 0, 0, w, h, (100, 100, 100))
        wall.add_child(vis)

    create_wall("Floor", -1000, 500, 2000, 100)
    create_wall("Wall1", -1000, 420, 80, 80)
    create_wall("Wall1", 1000, 420, 80, 80)

    # ======================
    # NPC
    # ======================
    npc_col = Collider2D("NPCCol", 0, 0, 40, 40)
    npc_col.layer = "npc"
    npc_col.mask = {"wall", "player", "box"}

    npc = NPC(
        "NPC",
        x=300,
        y=0,
        collider=npc_col,
        collision_world=collision_world
    )
    visual_world.add_child(npc)
    npc.add_child(npc_col)

    npc_vis = RectangleNode("NPCVis", 0, 0, 40, 40, (0, 200, 255))
    npc.add_child(npc_vis)

    # ======================
    # Box (Pushable)
    # ======================
    box_col = Collider2D(
    "BoxCol",
    0, 0,
    50, 50,
    is_static=False   # ❗ مهم
)

    box_col.layer = "box"
    box_col.mask = {"wall", "player", "box","npc"}

    box = Box(
        "Box",
        x=250,
        y=0,
        collider=box_col,
        collision_world=collision_world
    )
    visual_world.add_child(box)
    box.add_child(box_col)

    box_vis = RectangleNode("BoxVis", 0, 0, 50, 50, (200, 150, 50))
    box.add_child(box_vis)

    # ======================
    # Ghost (No Collision)
    # ======================
    # ghost = Node2D("Ghost", 200, 450)
    # root.add_child(ghost)

    # ghost_col = Collider2D("GhostCol", 0, 0, 50, 50)
    # ghost_col.layer = "ghost"
    # ghost_col.mask = set()
    # ghost.add_child(ghost_col)

    # ghost_vis = RectangleNode("GhostVis", 0, 0, 50, 50, (150, 0, 150))
    # ghost.add_child(ghost_vis)

    # ======================
    # Camera
    # ======================
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = player

    hud = StatsHUD("HUD",root,clock)
    root.add_child(hud)

    # ======================
    # Loop
    # ======================
    root.print_tree()
    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        root.update(dt)
        collision_world.process_collisions()

        screen.fill((30, 30, 30))
        root.render(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
