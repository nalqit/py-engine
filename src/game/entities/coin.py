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
