from src.engine.scene.node2d import Node2D
from src.engine.collision.collider2d import Collider2D
from src.engine.scene.tween import Easing

class Spring(Node2D):
    """
    A bouncy object that launches the player upward when landed upon.
    """
    def __init__(self, name, x, y, width=40, height=20, boost=-900.0):
        super().__init__(name, x, y)
        self.boost = boost
        
        # We need a solid collider so the player doesn't fall through
        self.collider = Collider2D(name + "_Col", 0, 0, width, height, is_static=True)
        self.collider.layer = "wall"  # Pretend to be a wall so physics body collides
        self.collider.mask = {"player", "box", "npc"}
        self.add_child(self.collider)

        # Build a multi-part visual so it doesn't look like a "green mass"
        from src.engine.scene.rectangle_node import RectangleNode
        self.vis = Node2D(name + "_Vis", 0, 0)
        self.vis.add_child(RectangleNode("Base", 0, height*0.75, width, height*0.25, (100, 100, 100)))
        self.vis.add_child(RectangleNode("Coil", 5, 5, width-10, height*0.75, (180, 180, 180)))
        self.vis.add_child(RectangleNode("Top", 0, 0, width, 5, (255, 60, 60)))
        self.add_child(self.vis)

    def _get_tween_manager(self):
        root = self
        while root.parent:
            root = root.parent
        return root.get_node("TweenManager")

    def animate_bounce(self):
        """Squash and stretch the spring visually."""
        tm = self._get_tween_manager()
        if not tm:
            return
            
        # Get the visual node (assuming one is added named Vis)
        vis = self.get_node(self.name + "_Vis")
        if not vis:
            return
            
        duration = 0.15
        
        # Original scales
        orig_sx = 1.0
        orig_sy = 1.0
        
        def reset():
            tm.interpolate(vis, "scale_y", vis.scale_y, orig_sy, duration, Easing.quad_out)
        
        # Quick squash then stretch
        tm.interpolate(vis, "scale_y", orig_sy, 0.3, duration/2, Easing.quad_out, on_complete=lambda:
            tm.interpolate(vis, "scale_y", 0.3, 1.5, duration/2, Easing.quad_out, on_complete=reset)
        )

    def on_collision_enter(self, other):
        """When something hits the spring."""
        if not other.parent:
            return
            
        body = other.parent
        
        # If the body is coming down onto the spring (velocity_y > 0)
        # Check if they are actually above it physically
        if hasattr(body, "velocity_y") and body.velocity_y > 0:
            # We add a slight positioning check: body's bottom should be near spring's top
            # but simple velocity_y is usually enough for a platformer spring.
            body.velocity_y = self.boost
            self.animate_bounce()
