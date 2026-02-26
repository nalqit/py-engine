from src.pyengine2D import (
    Node2D, RectangleNode, Collider2D, TweenManager, Tween, Easing, PhysicsBody2D
)

# ------------------------------------------------------------------
# Moving Platform Example
# Demonstrates:
# - Using TweenManager to automate hard-coded transform paths
# - Physics engine allowing players to ride "kinematic" style platforms
#   (Because the engine physics body checks collisions, moving a static 
#   collider might push the player around, but true riding needs some help. 
#   For this demo, we'll make a simple moving wall.)
# ------------------------------------------------------------------

class MovingPlatform(Node2D):
    def __init__(self, name, x, y, width, height, move_x, move_y, duration, collision_world):
        super().__init__(name, x, y)
        self.collision_world = collision_world
        
        # 1. Visual
        self.vis = RectangleNode(f"{name}_Vis", 0, 0, width, height, (50, 100, 200))
        self.add_child(self.vis)
        
        # 2. Collider
        self.collider = Collider2D(f"{name}_Col", 0, 0, width, height, is_static=True)
        self.collider.layer = "wall"
        self.add_child(self.collider)
        
        # 3. Movement Logic (Tween)
        # We tween the local_x and local_y of this entire Node. 
        # Since the Collider is a child, it moves with us.
        self.tween_mgr = TweenManager("TweenMgr")
        self.add_child(self.tween_mgr)
        
        start_x, start_y = x, y
        end_x = start_x + move_x
        end_y = start_y + move_y
        
        def move_forward():
            self.tween_mgr.interpolate(self, "local_x", start_x, end_x, duration, Easing.sine_in_out)
            self.tween_mgr.interpolate(self, "local_y", start_y, end_y, duration, Easing.sine_in_out, on_complete=move_backward)
            
        def move_backward():
            self.tween_mgr.interpolate(self, "local_x", end_x, start_x, duration, Easing.sine_in_out)
            self.tween_mgr.interpolate(self, "local_y", end_y, start_y, duration, Easing.sine_in_out, on_complete=move_forward)
            
        move_forward()

    def update(self, delta):
        # Save previous position to calculate delta
        prev_x = self.local_x
        prev_y = self.local_y
        
        # This updates the tweens, changing local_x and local_y
        super().update(delta)
        
        # Ensure transform changes are immediately visible to children and collision logic
        self.update_transforms()
        self._sync_collider()
        
        dx = self.local_x - prev_x
        dy = self.local_y - prev_y
        
        if (dx != 0 or dy != 0) and self.collision_world:
            gx, gy = self.get_global_position()
            width = self.collider.width * self.collider.scale_x
            
            # Create a small trigger zone just above the platform to catch riders
            # Expand it backward by the delta to ensure we don't leave riders behind when moving fast
            test_left = gx - max(0, dx)
            test_top = gy - max(0, dy) - 2
            test_right = gx + width - min(0, dx)
            test_bottom = gy + max(0, -dy) + 2
            
            
            riders = self.collision_world.query_rect(test_left, test_top, test_right, test_bottom, exclude=self.collider)
            
            for rider_col in riders:
                body = rider_col.parent
                if isinstance(body, PhysicsBody2D):
                    # Carry the rider by moving their body directly
                    # A true physics implementation would push/sweep them, 
                    # but simple translation is effective for typical kinematic platforms.
                    body.local_x += dx
                    body.local_y += dy
                    if dy > 0 and body.velocity_y > 0:
                        body.velocity_y = 0.0 # Clear gravity accumulation while sliding down on the platform
                    body.update_transforms()
                    # Also sync the rider's collider cache so their move_and_collide is accurate
                    if hasattr(body, '_refresh_collider_cache'):
                        body._refresh_collider_cache(body)
                    elif hasattr(body, 'collider'):
                         # Manual sync if it's not a PhysicsBody2D with the helper but has a collider
                         bgx, bgy = body.collider.get_global_position()
                         bw = body.collider.width * body.collider.scale_x
                         bh = body.collider.height * body.collider.scale_y
                         self.collision_world._cached_rects[body.collider] = (bgx, bgy, bgx + bw, bgy + bh)

    def _sync_collider(self):
        """Update the collision world's cached rect for this platform's collider."""
        if not self.collision_world: return
        gx, gy = self.collider.get_global_position()
        sw = self.collider.width * self.collider.scale_x
        sh = self.collider.height * self.collider.scale_y
        self.collision_world._cached_rects[self.collider] = (gx, gy, gx + sw, gy + sh)
