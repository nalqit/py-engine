import pygame
from src.pyengine2D import Engine, Node2D, CollisionWorld, Camera2D
from src.pyengine2D.collision.polygon_collider2d import PolygonCollider2D
from src.pyengine2D.collision.circle_collider2d import CircleCollider2D

def main():
    engine = Engine("Polygon Test", 800, 600)
    root = Node2D("Root")
    
    world = CollisionWorld("World")
    root.add_child(world)
    
    # Triangle Polygon
    poly = PolygonCollider2D("Triangle", 400, 300, [(0, -50), (50, 50), (-50, 50)], is_static=True, visible=True)
    poly.layer = "wall"
    poly.mask = {"player"}
    world.add_child(poly)
    
    # Player Circle
    player = CircleCollider2D("Player", 100, 100, 30, visible=True)
    player.layer = "player"
    player.mask = {"wall"}
    world.add_child(player)
    
    # We will just drag the circle to the mouse to test collisions visually.
    # The circle should trigger on_collision_enter when touching the triangle.
    class PlayerController(Node2D):
        def update(self, dt):
            mx, my = Engine.instance.input.get_mouse_pos()
            player.local_x = mx
            player.local_y = my
            
        def on_collision_enter(self, other):
            print(f"ENTER: {other.name}")
            
        def on_collision_exit(self, other):
            print(f"EXIT: {other.name}")
            
        def on_collision_stay(self, other):
            pass # print(f"STAY: {other.name}")

    controller = PlayerController("Controller")
    player.add_child(controller)

    # Use root.print_tree() to verify setup
    root.print_tree()

    print("Move the mouse to drag the circle. Watch console for ENTER/EXIT events.")
    
    # Quit after a few frames automatically for automated testing,
    # but the user can run this scripts manually to test gameplay logic interactively.
    frames = 0
    def on_fixed_update(eng, root, dt):
        nonlocal frames
        frames += 1
        if frames > 100:  # Enough time to observe the window if run manually
            eng.running = False
            
    engine.run(root, on_fixed_update=on_fixed_update)

if __name__ == "__main__":
    main()
