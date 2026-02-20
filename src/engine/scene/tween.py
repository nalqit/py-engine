import math
from typing import Callable, Any , Optional
from .node import Node

class Easing:
    """Standard easing functions."""
    @staticmethod
    def linear(t: float) -> float:
        return t
    
    @staticmethod
    def quad_in(t: float) -> float:
        return t * t
    
    @staticmethod
    def quad_out(t: float) -> float:
        return t * (2 - t)
    
    @staticmethod
    def sine_in_out(t: float) -> float:
        return 0.5 * (1 - math.cos(math.pi * t))

class Tween:
    def __init__(self, target: Any, property_name: str, start_val: float, end_val: float, duration: float, easing: Callable[[float], float], on_complete: Optional[Callable] = None):
        self.target = target
        self.property_name = property_name
        self.start_val = start_val
        self.end_val = end_val
        self.duration = duration
        self.easing = easing
        self.on_complete = on_complete
        self.elapsed = 0.0
        self.finished = False

    def update(self, delta: float):
        if self.finished:
            return

        self.elapsed += delta
        t = min(1.0, self.elapsed / self.duration)
        e_t = self.easing(t)
        
        current_val = self.start_val + (self.end_val - self.start_val) * e_t
        setattr(self.target, self.property_name, current_val)

        if t >= 1.0:
            self.finished = True
            if self.on_complete:
                self.on_complete()

class TweenManager(Node):
    """
    A helper node that manages active tweens.
    """
    def __init__(self, name="TweenManager"):
        super().__init__(name)
        self.tweens = []

    def interpolate(self, target: Any, property_name: str, start: float, end: float, duration: float, easing=Easing.linear, on_complete: Optional[Callable] = None):
        tween = Tween(target, property_name, start, end, duration, easing, on_complete)
        self.tweens.append(tween)
        return tween

    def update(self, delta: float):
        # Update all active tweens
        for t in self.tweens:
            t.update(delta)
        
        # Remove finished ones
        self.tweens = [t for t in self.tweens if not t.finished]
        
        super().update(delta)
