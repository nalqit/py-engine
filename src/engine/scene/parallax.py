from src.engine.scene.node2d import Node2D

class ParallaxBackground(Node2D):
    """
    A container for ParallaxLayer nodes.
    Simplifies management of multiple parallax layers.
    """
    def __init__(self, name="ParallaxBackground"):
        super().__init__(name, 0, 0)

class ParallaxLayer(Node2D):
    """
    A layer that moves at a fraction of the camera's speed.
    """
    def __init__(self, name, parallax_factor=(1.0, 1.0)):
        """
        parallax_factor: (x_factor, y_factor). 
        0.0 means it moves with the camera (stationary background).
        1.0 means it moves 1:1 with the camera (foreground).
        Values < 1.0 create depth.
        """
        super().__init__(name, 0, 0)
        self.parallax_factor_x = parallax_factor[0]
        self.parallax_factor_y = parallax_factor[1]
        self.base_offset_x = 0
        self.base_offset_y = 0

    def update(self, delta: float):
        # We need to know where the camera is.
        # In this engine, Node2D.camera might be used or we can find it in the tree.
        # Looking at main.py, Node2D.camera = player (which is a bit weird as a variable name)
        # but Camera2D is also a node.
        
        # In Camera2D, local_x/y is used to offset the world.
        # However, Camera2D logic in main.py:
        # camera.follow(player)
        # Node2D.camera = player? Wait, main.py L117: Node2D.camera = player
        # And Camera2D L14: target_x = tx - 400
        
        # Let's look for a Camera2D instance in the root.
        root = self._get_root()
        camera = root.get_node("Camera")
        
        if camera:
            # The ParallaxLayer should shift its position based on camera position
            # layer_pos = camera_pos * (1 - factor)
            # This makes 0.0 factor move at 100% camera speed (relative to world), 
            # appearing stationary on screen if offset is 0.
            # Actually, standard parallax: 
            # layer_x = camera_x * parallax_factor
            
            # Since objects are rendered as: screen_pos = world_pos - camera_pos
            # screen_pos = (base_pos + camera_x * factor) - camera_x
            # screen_pos = base_pos + camera_x * (factor - 1)
            
            self.local_x = self.base_offset_x + camera.local_x * (1 - self.parallax_factor_x)
            self.local_y = self.base_offset_y + camera.local_y * (1 - self.parallax_factor_y)

        super().update(delta)

    def _get_root(self):
        root = self
        while root.parent:
            root = root.parent
        return root
