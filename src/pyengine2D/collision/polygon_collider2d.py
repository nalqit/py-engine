import pygame
from src.pyengine2D.scene.node2d import Node2D
from typing import List, Tuple

class PolygonCollider2D(Node2D):
    """
    A convex polygon collider defined by a list of local vertices.
    Used for SAT (Separating Axis Theorem) collisions.
    Vertices must be ordered (clockwise or counter-clockwise) and form a convex shape.
    """

    def __init__(self, name: str, x: float, y: float, points: List[Tuple[float, float]], is_static=False, is_trigger=False, visible=False):
        super().__init__(name, x, y)
        if len(points) < 3:
            raise ValueError("PolygonCollider2D requires at least 3 points.")
            
        self.local_points = points
        
        self.is_static = is_static
        self.is_trigger = is_trigger
        self.visible = visible
        self.layer = "default"
        self.mask = set()
        
        # Calculate bounding box width/height conceptually
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        # Abstract bounds mapping
        self.width = max_x - min_x
        self.height = max_y - min_y

    def get_global_points(self) -> List[Tuple[float, float]]:
        """Returns the polygon vertices transformed into global space (factoring rotation/scale)."""
        gx, gy = self.get_global_position()
        
        import math
        cos_a = math.cos(self.rotation)
        sin_a = math.sin(self.rotation)
        
        global_pts = []
        for (px, py) in self.local_points:
            # Scale
            sx = px * self.scale_x
            sy = py * self.scale_y
            # Rotate
            rx = sx * cos_a - sy * sin_a
            ry = sx * sin_a + sy * cos_a
            # Translate
            global_pts.append((gx + rx, gy + ry))
            
        return global_pts

    def get_rect(self) -> Tuple[float, float, float, float]:
        """
        Return the world-space bounding box (AABB) for broadphase grid queries.
        (left, top, right, bottom)
        """
        pts = self.get_global_points()
        min_x = min(p[0] for p in pts)
        max_x = max(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)
        return (min_x, min_y, max_x, max_y)

    def render(self, surface) -> None:
        """Debug draw the polygon."""
        from src.pyengine2D.core.engine import Engine
        r = Engine.instance.renderer if Engine.instance else None
        
        if r and self.visible:
            # We must map global coordinates to the screen using the camera
            pts = self.get_global_points()
            
            cam_x, cam_y = 0, 0
            if Node2D.camera:
                c_gx, c_gy = Node2D.camera.get_global_position()
                half_w = Engine.instance.virtual_w / 2
                half_h = Engine.instance.virtual_h / 2
                cam_x = c_gx - half_w
                cam_y = c_gy - half_h
                
            screen_pts = [(p[0] - cam_x, p[1] - cam_y) for p in pts]
            
            color = (0, 255, 0, 128) if self.is_static else (255, 0, 255, 128)
            r.draw_polygon(surface, color, screen_pts, width=1)

        super().render(surface)
