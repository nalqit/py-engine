from src.pyengine2D import Area2D,CircleCollider2D,CircleNode,TweenManager,Tween,Easing

class Coin(Area2D):
    def __init__(self, name, x, y):
        # 15px radius circle area roughly mapped to a 30x30 bounding box
        super().__init__(name, x, y, 30, 30)
        self.remove_child(self.collider) # remove default AABB
        
        self.collider = CircleCollider2D(name + "_Col", 0, 0, 15, is_static=False, is_trigger=True)
        self.collider.layer = "pickup"
        self.collider.mask = {"player"}
        self.add_child(self.collider)
        
        # We can implement a circle child node simply via Engine
        self.vis = CircleNode(f"{name}_Vis", 0, 0, 15, (255, 215, 0))
        self.add_child(self.vis)
        
        self.collected = False
        self.base_y = y
        self.score_value = 10
        
        self.register_signal("on_collected")

        self.tween_mgr = TweenManager("TweenMgr")
        self.add_child(self.tween_mgr)
        self._start_bob()

    def update(self, delta):
        super().update(delta)
        self.update_transforms()
        if hasattr(self, "collision_world") and self.collision_world:
            res = self.collider.get_rect()
            if isinstance(res, tuple):
                 self.collision_world._cached_rects[self.collider] = res
            else:
                 self.collision_world._cached_rects[self.collider] = (res.left, res.top, res.right, res.bottom)

    def _start_bob(self):
        def bob_down():
             self.tween_mgr.interpolate(self, "local_y", self.base_y - 10, self.base_y, 1.2, Easing.sine_in_out, on_complete=bob_up)
             
        def bob_up():
             self.tween_mgr.interpolate(self, "local_y", self.base_y, self.base_y - 10, 1.2, Easing.sine_in_out, on_complete=bob_down)

        bob_up()

    def on_area_entered(self, body):
        if self.collected:
            return
        if body.name == "Player":
            self.collect(body)

    def collect(self, player):
        self.collected = True
        self.emit_signal("on_collected", score_value=self.score_value)
        # Assuming player has add_score
        player.add_score(self.score_value)
        if self.parent:
            self.parent.remove_child(self)
