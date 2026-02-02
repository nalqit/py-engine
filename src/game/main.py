import pygame
import sys

from src.engine.scene.node2d import Node2D
from src.engine.scene.rectangle_node import RectangleNode
from src.game.entities.player import Player
from src.game.entities.box import Box
from src.game.entities.npc import NPC
from src.engine.ui.stats_hud import StatsHUD
from src.engine.ui.debug_draw import DebugDraw
from src.engine.input.input_manager import InputManager
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.scene.camera2d import Camera2D
from src.engine.ui.fsm_label import FSMLabel  # ← النص اللي يتبع اللاعب


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("PyEngine 2D - Physics Collision Test")
    clock = pygame.time.Clock()

    # Root
    root = Node2D("Root")

    # Input
    input_manager = InputManager("Input")
    root.add_child(input_manager)

    # Collision World
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    # Visual World
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)

    # ---------------- Player ----------------
    player_col = Collider2D("PlayerCol", 0, 0, 50, 50)
    player_col.layer = "player"
    player_col.mask = {"wall", "box", "npc"}

    player = Player(
        "Player",
        x=100, y=0,
        input_manager=input_manager,
        collider=player_col,
        collision_world=collision_world
    )
    player.use_gravity = True
    visual_world.add_child(player)
    player.add_child(player_col)

    player_vis = RectangleNode("PlayerVis", 0, 0, 50, 50, (255, 0, 0))
    player.add_child(player_vis)

    # FSM Label
    label = FSMLabel("label", player, -10)
    player.add_child(label)

    # ---------------- Walls & Platforms ----------------
    def create_wall(name, x, y, w, h):
        wall = Node2D(name, x, y)
        visual_world.add_child(wall)

        col = Collider2D(name+"Col", 0, 0, w, h, is_static=True)
        col.layer = "wall"
        col.mask = {"player", "box", "npc"}
        wall.add_child(col)

        vis = RectangleNode(name+"Vis", 0, 0, w, h, (100, 100, 100))
        wall.add_child(vis)

    # Ground & Ceiling
    create_wall("Floor", -1000, 500, 2000, 100)
    create_wall("Ceiling", -1000, 0, 2000, 50)

    # Vertical walls
    create_wall("LeftWall", -1000, 0, 50, 600)
    create_wall("RightWall", 950, 0, 50, 600)

    # Platforms
    create_wall("Platform1", 200, 400, 200, 20)
    create_wall("Platform2", 500, 300, 150, 20)
    create_wall("Platform3", 100, 200, 100, 20)

    # Narrow obstacles
    create_wall("ThinVert1", 400, 250, 20, 100)
    create_wall("ThinHoriz1", 600, 450, 50, 10)

    # ---------------- NPCs ----------------
    for i, pos_x in enumerate([300, 600, 750]):
        npc_col = Collider2D(f"NPCCol{i}", 0, 0, 40, 40)
        npc_col.layer = "npc"
        npc_col.mask = {"wall", "player", "box"}

        npc = NPC(
            f"NPC{i}", x=pos_x, y=0,
            collider=npc_col,
            collision_world=collision_world
        )
        npc.use_gravity = True
        visual_world.add_child(npc)
        npc.add_child(npc_col)

        npc_vis = RectangleNode(f"NPCVis{i}", 0, 0, 40, 40, (0, 200, 255))
        npc.add_child(npc_vis)

    # ---------------- Boxes ----------------
    for i, pos_x in enumerate([250, 550, 700]):
        box_col = Collider2D(f"BoxCol{i}", 0, 0, 50, 50, is_static=False)
        box_col.layer = "box"
        box_col.mask = {"wall", "player", "npc", "box"}

        box = Box(
            f"Box{i}", x=pos_x, y=0,
            collider=box_col,
            collision_world=collision_world
        )
        box.use_gravity = True
        visual_world.add_child(box)
        box.add_child(box_col)

        box_vis = RectangleNode(f"BoxVis{i}", 0, 0, 50, 50, (200, 150, 50))
        box.add_child(box_vis)

    # ---------------- Camera ----------------
    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = player

    # ---------------- HUD ----------------
    hud = StatsHUD("HUD", root, clock)
    root.add_child(hud)

    # ---------------- Main Loop ----------------
    root.print_tree()
    running = True
    while running:
        dt = clock.tick(60) / 1000

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update
        root.update(dt)

        # Draw
        screen.fill((30, 30, 30))
        root.render(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
