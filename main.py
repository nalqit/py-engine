import pygame
import sys

from src.scene.node2d import Node2D
from src.scene.rectangle_node import RectangleNode
from src.scene.player import Player
from src.scene.input.input_manager import InputManager
from src.scene.collision.collider2d import Collider2D
from src.scene.collision.collision_world import CollisionWorld


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("PyEngine 2D - Camera + Collision Test")
    clock = pygame.time.Clock()

    # ======================
    # Root Node
    # ======================
    root = Node2D("Root")

    # ======================
    # Input Manager
    # ======================
    input_manager = InputManager("Input")
    root.add_child(input_manager)

    # ======================
    # Collision World
    # ======================
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    # ======================
    # Player Collider
    # ======================
    player_collider = Collider2D(
        name="PlayerCollider",
        x=0, y=0, width=50, height=50
    )
    collision_world.add_child(player_collider)

    # ======================
    # Player Logic
    # ======================
    player = Player(
        name="Player",
        x=100,
        y=100,
        input_manager=input_manager,
        collider=player_collider,
        collision_world=collision_world
    )
    root.add_child(player)
    player.add_child(player_collider)

    # ======================
    # Player Visual
    # ======================
    player_shape = RectangleNode(
        name="PlayerShape",
        x=0, y=0,
        width=50, height=50,
        color=(255, 0, 0)
    )
    player.add_child(player_shape)

    # ======================
    # Test Wall
    # ======================
    wall_collider = Collider2D(
        name="WallCollider",
        x=300, y=200,
        width=100, height=100
    )
    collision_world.add_child(wall_collider)

    wall_shape = RectangleNode(
        name="WallShape",
        x=300, y=200,
        width=100, height=100,
        color=(0, 255, 0)
    )
    root.add_child(wall_shape)

    # ======================
    # Camera
    # ======================
    Node2D.camera = player  # الكاميرا تتبع اللاعب

    # ======================
    # Print Tree
    # ======================
    print("=== Scene Graph Tree ===")
    root.print_tree()
    print("========================")

    # ======================
    # Main Loop
    # ======================
    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update Scene
        root.update(dt)

        # Draw Scene
        screen.fill((30, 30, 30))
        root.render(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
