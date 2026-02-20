import pygame
from src.engine.collision.area2d import Area2D
from src.engine.scene.rectangle_node import RectangleNode

class Coin(Area2D):
    """
    A simple collectable coin.
    """
    def __init__(self, name, x, y):
        super().__init__(name, x, y, 20, 20)
        self.vis = RectangleNode(name + "_Vis", 0, 0, 20, 20, (255, 215, 0)) # Gold color
        self.add_child(self.vis)
        self.collected = False
        self.base_vis_y = 0.0
        
        # We will use the global TweenManager if it exists in the tree
        self.tween_started = False

    def update(self, delta):
        if not self.tween_started:
            root = self._get_root()
            tm = root.get_node("TweenManager")
            if tm:
                # Start a simple bobbing animation
                from src.engine.scene.tween import Easing
                # Note: We'd ideally want a 'repeat' or 'yoyo' feature in the tween system.
                # For now, we'll just implement a simple loop.
                self._start_bob(tm)
                self.tween_started = True
        super().update(delta)

    def _start_bob(self, tm):
        from src.engine.scene.tween import Easing
        
        def bob_down():
             tm.interpolate(self.vis, "local_y", -10, 0, 1.2, Easing.sine_in_out, on_complete=bob_up)
             
        def bob_up():
             tm.interpolate(self.vis, "local_y", 0, -10, 1.2, Easing.sine_in_out, on_complete=bob_down)

        bob_up()

    def _get_root(self):
        root = self
        while root.parent:
            root = root.parent
        return root

    def on_area_entered(self, body):
        if self.collected:
            return
            
        # Check if the body is the player
        if body.name == "Player":
            self.collect()

    def collect(self):
        self.collected = True
        # Remove from parent to disappear
        if self.parent:
            self.parent.remove_child(self)
        print(f"Coin {self.name} collected!")
