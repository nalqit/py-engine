from src.engine.scene.node2d import Node2D
from src.engine.scene.circle_node import CircleNode
from src.engine.collision.area2d import Area2D
from src.engine.scene.tween import TweenManager, Tween, Easing

# ------------------------------------------------------------------
# Collectible Example
# Demonstrates:
# - Area2D for trigger volumes
# - TweenManager for smooth "floating" animations
# - Signals for decoupling rendering logic from gameplay logic
# ------------------------------------------------------------------

class Collectible(Area2D):
    def __init__(self, name, x, y, collision_world):
        # 1. Setup Trigger Area
        super().__init__(name, x, y, 30, 30)
        self.collision_world = collision_world
        self.remove_child(self.collider) # Remove default AABB
        
        from src.engine.collision.circle_collider2d import CircleCollider2D
        self.collider = CircleCollider2D(name + "_AreaCol", 0, 0, 15, is_static=False, is_trigger=True)
        self.collider.layer = "pickup"
        self.collider.mask = {"player"}
        self.add_child(self.collider)

        
        # 2. Visuals
        # A glowing yellow circle
        self.vis = CircleNode(name + "_Vis", 0, 0, 15, (255, 255, 50))
        self.add_child(self.vis)
        
        # 3. Signals
        # We emit this so the Level or HUD knows to add score
        self.register_signal("on_collected")
        
        # 4. Tween Animation (Floating)
        self.tween_mgr = TweenManager("TweenMgr")
        self.add_child(self.tween_mgr)
        
        self.start_y = y
        self._start_float_animation()

    def _start_float_animation(self):
        # Bob up and down indefinitely
        # Developer Guide Hint: Tweens are great for fire-and-forget animations
        def move_up():
            self.tween_mgr.interpolate(self, "local_y", self.start_y + 10, self.start_y - 10, 1.0, Easing.sine_in_out, on_complete=move_down)
            
        def move_down():
            self.tween_mgr.interpolate(self, "local_y", self.start_y - 10, self.start_y + 10, 1.0, Easing.sine_in_out, on_complete=move_up)
            
        move_up()

    def on_area_entered(self, body):
        # Area2D automatically calls this when a body in our mask overlaps us.
        if body.name == "Player":
            # 1. Notify listeners (like the Score Manager)
            self.emit_signal("on_collected", score_value=50)
            
            # 2. Cleanup: we're collected, so destroy ourselves
            self.destroy()

    def update(self, delta):
        # Allow tweens to change local_y
        super().update(delta)
        # Ensure the collision world and visuals immediately see the new Y position
        self.update_transforms()
        self._sync_collider()

    def _sync_collider(self):
        """Update the collision world's cached rect for this collectible's collider."""
        if not self.collision_world: return
        res = self.collider.get_rect()
        if isinstance(res, tuple):
             self.collision_world._cached_rects[self.collider] = res
        else:
             self.collision_world._cached_rects[self.collider] = (res.left, res.top, res.right, res.bottom)
