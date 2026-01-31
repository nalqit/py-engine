import pygame
import sys

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.game.entities.player import Player
from src.game.entities.box import Box
from src.game.entities.npc import NPC
from src.engine.ui.stats_hud import StatsHUD
# from src.engine.physics.ai_controller import AIController
from src.engine.ui.debug_draw import DebugDraw

from src.engine.input.input_manager import InputManager
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.camera2d import Camera2D


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


    #======================
    # Player 2
    #======================
    # player2_col = Collider2D("Player2Col", 0, 0, 50, 50)
    # player2_col.layer = "player2"
    # player2_col.mask = {"wall", "box", "npc","player"}

    # player2 = Player(
    #     "Player2",
    #     x=0,
    #     y=0,
    #     input_manager=input_manager,
    #     collider=player2_col,
    #     collision_world=collision_world
    # )
    # visual_world.add_child(player2)
    # player2.add_child(player2_col)

    # player2_vis = RectangleNode("Player2Vis", 0, 0, 50, 50, (255, 0, 0))
    # player2.controller = AIController(player2)
    # player2.add_child(player2_vis)

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
    create_wall("platform",0,150,200,200)



    # ======================
    # NPC
    # ======================
    npc_col = Collider2D("NPCCol", 0, 0, 40, 40)
    npc_col.layer = "npc"
    npc_col.mask = {"wall", "player", "box"}

    npc = NPC(
        "NPC",
        x=500,
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
    box_col.mask = {"wall", "player", "box2","npc"}

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

    #======================
    #box2
    #======================
#     box2_col = Collider2D(
#     "Box2Col",
#     0, 0,
#     50, 50,
#     is_static=False   # ❗ مهم
# )

    # box2_col.layer = "box2"
    



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
        dt = clock.tick(60) / 1000

        # UPDATE
        root.update(dt)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # DRAW
        screen.fill((30, 30, 30))

        root.render(screen)   # ← ترسم العالم
        print(player.velocity_y)
        # ===== هنا ترسم الـ FSM TEXT =====
        font = pygame.font.SysFont(None, 16)

        text = font.render(player.state_machine.current_state.name, True, (255, 255, 255))
        screen.blit(
            text,
            (
                player.local_x - camera.local_x,
                player.local_y - 20 - camera.local_y
            )
        )
        # =================================
        

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
