from src.engine.collision.area2d import Area2D
from src.engine.scene.particles import ParticleEmitter2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.scene.tween import Easing
import pygame

class Trophy(Area2D):
    """
    The ultimate goal! Touching this wins the level.
    """
    def __init__(self, name, x, y, width=50, height=50):
        super().__init__(name, x, y, width, height)
        # Unique layer just for clarity, though 'coin' overlap works too for triggers
        self.collider.layer = "trophy" 
        self.collider.mask = {"player"}
        
        # Golden Visuals
        self.vis = RectangleNode(name + "_Vis", 0, 0, width, height, (255, 215, 0))
        self.add_child(self.vis)
        
        # Fireworks emitter!
        self.particles = ParticleEmitter2D("Fireworks")
        self.add_child(self.particles)
        
        self.won = False

    def update(self, delta):
        super().update(delta)
        # Make the trophy bob up and down
        if not self.won:
            tm = self._get_tween_manager()
            if tm and not tm.is_tweening(self.vis, "local_y"):
                self.animate_bob()

    def _get_tween_manager(self):
        root = self
        while root.parent:
            root = root.parent
        return root.get_node("TweenManager")

    def animate_bob(self):
        tm = self._get_tween_manager()
        if not tm: return
        duration = 1.0
        
        if not hasattr(self, 'base_y'):
            self.base_y = self.local_y
            
        def bob_down():
            tm.interpolate(self, "local_y", self.base_y - 10.0, self.base_y, duration, Easing.sine_in_out, on_complete=self.animate_bob)

        tm.interpolate(self, "local_y", self.base_y, self.base_y - 10.0, duration, Easing.sine_in_out, on_complete=bob_down)

    def on_area_entered(self, body):
        if not self.won and hasattr(body, "die"):
            self.won = True
            
            # Massive fireworks
            gx, gy = self.get_global_position()
            self.particles.emit(gx + 25, gy + 25, count=100, 
                                speed_range=(50, 300), 
                                angle_range=(0, 360),
                                color=(255, 215, 0)) # Gold fireworks
            
            print("\n" + "="*40)
            print("🏆 YOU WIN! YOU REACHED THE TROPHY! 🏆")
            print("="*40 + "\n")
            
            # Reset player to start after a tiny delay
            # Since we don't have timers built-in natively, we'll just teleport them instantly
            # but leave the fireworks behind.
            body.die()
            
            # Reset the trophy so they can win again
            self.won = False
