from .node import Node

class Node2D(Node):
    """Base class for 2D nodes with position (Optimized with Dirty Transforms)."""
    camera = None
    def __init__(self, name: str = "Node2D", local_x: float = 0.0, local_y: float = 0.0):
        super().__init__(name)
        self._local_x = local_x
        self._local_y = local_y
        self._scale_x = 1.0
        self._scale_y = 1.0
        self._rotation = 0.0
        
        self._dirty = True
        self._cached_global_x = local_x
        self._cached_global_y = local_y

    @property
    def local_x(self): return self._local_x
    @local_x.setter
    def local_x(self, value):
        if self._local_x != value:
            self._local_x = value
            self.set_dirty()

    @property
    def local_y(self): return self._local_y
    @local_y.setter
    def local_y(self, value):
        if self._local_y != value:
            self._local_y = value
            self.set_dirty()
            
    @property
    def scale_x(self): return self._scale_x
    @scale_x.setter
    def scale_x(self, value):
        if self._scale_x != value:
            self._scale_x = value
            self.set_dirty()
            
    @property
    def scale_y(self): return self._scale_y
    @scale_y.setter
    def scale_y(self, value):
        if self._scale_y != value:
            self._scale_y = value
            self.set_dirty()

    @property
    def rotation(self): return self._rotation
    @rotation.setter
    def rotation(self, value):
        if self._rotation != value:
            self._rotation = value
            self.set_dirty()

    def set_position(self, x: float, y: float):
        if self._local_x != x or self._local_y != y:
            self._local_x = x
            self._local_y = y
            self.set_dirty()
            
    def set_scale(self, sx: float, sy: float):
        if self._scale_x != sx or self._scale_y != sy:
            self._scale_x = sx
            self._scale_y = sy
            self.set_dirty()
            
    def set_rotation(self, angle: float):
        if self._rotation != angle:
            self._rotation = angle
            self.set_dirty()

    def set_dirty(self):
        """Recursively marks this node and all children as dirty."""
        if not self._dirty:
            self._dirty = True
            for child in self.children:
                if isinstance(child, Node2D):
                    child.set_dirty()

    def update_transforms(self):
        """
        Calculates only if dirty, removing redundant math per frame.
        Triggered from the Engine's main loop.
        """
        if self._dirty:
            self._update_global_calculations()
        # Still need to propagate the update_transforms loop to children 
        # because some Nodes might be UI/Controllers needing logic ticks,
        # but the transform math is skipped via the _dirty check above for children too.
        super().update_transforms()

    def _update_global_calculations(self):
        if not self.parent or not isinstance(self.parent, Node2D):
            self._cached_global_x = self._local_x
            self._cached_global_y = self._local_y
        else:
            pgx, pgy = self.parent.get_global_position()
            self._cached_global_x = pgx + self._local_x
            self._cached_global_y = pgy + self._local_y
        self._dirty = False

    def get_global_position(self):
        """Returns the lazily evaluated pre-calculated global position."""
        if self._dirty:
            self._update_global_calculations()
        return self._cached_global_x, self._cached_global_y

    def get_screen_position(self):
        gx, gy = self.get_global_position()
        if Node2D.camera:
            from src.pyengine2D.core.engine import Engine
            screen_w = Engine.instance.virtual_w if Engine.instance else 800
            screen_h = Engine.instance.virtual_h if Engine.instance else 600
            cx, cy = Node2D.camera.get_global_position()
            # Return as integers to prevent float rounding desync with TilemapNode
            return int(gx - cx + screen_w//2), int(gy - cy + screen_h//2)
        return int(gx), int(gy)

        

