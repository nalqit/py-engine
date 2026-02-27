import math
from typing import Callable, Any, Optional
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
    """
    A single tween interpolation.  Designed to be pooled — reset() re-uses
    the same object without allocating a new one.
    """

    __slots__ = (
        'target', 'property_name', 'start_val', 'end_val',
        'duration', 'easing', 'on_complete', 'elapsed', 'finished',
    )

    def __init__(self, target=None, property_name='', start_val=0.0,
                 end_val=0.0, duration=1.0, easing=None, on_complete=None):
        self.target = target
        self.property_name = property_name
        self.start_val = start_val
        self.end_val = end_val
        self.duration = duration
        self.easing = easing or Easing.linear
        self.on_complete = on_complete
        self.elapsed = 0.0
        self.finished = False

    def reset(self, target, property_name, start_val, end_val, duration, easing, on_complete):
        """Re-initialise for reuse from pool."""
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
    A helper node that manages active tweens with object pooling.

    Performance features:
        - Internal pool of pre-allocated Tween objects.
        - In-place update loop (finished tweens moved to pool, no list rebuild).
        - Supports hundreds of simultaneous tweens efficiently.
    """

    def __init__(self, name="TweenManager", pool_size=64):
        super().__init__(name)
        self.tweens = []
        self._tween_pool = [Tween() for _ in range(pool_size)]

    def interpolate(self, target: Any, property_name: str, start: float, end: float,
                    duration: float, easing=Easing.linear,
                    on_complete: Optional[Callable] = None):
        """Create or reuse a Tween and start it."""
        if self._tween_pool:
            tween = self._tween_pool.pop()
            tween.reset(target, property_name, start, end, duration, easing, on_complete)
        else:
            tween = Tween(target, property_name, start, end, duration, easing, on_complete)
        self.tweens.append(tween)
        return tween

    def is_tweening(self, target: Any, property_name: str) -> bool:
        for t in self.tweens:
            if t.target == target and t.property_name == property_name and not t.finished:
                return True
        return False

    def tween_count(self):
        """Return the number of currently active (non-finished) tweens."""
        return len(self.tweens)

    def kill_all(self):
        """Immediately finish and pool all active tweens."""
        for t in self.tweens:
            self._tween_pool.append(t)
        self.tweens.clear()

    def update(self, delta: float):
        # In-place partition: keep alive tweens, return dead ones to pool
        write = 0
        for i in range(len(self.tweens)):
            t = self.tweens[i]
            t.update(delta)
            if not t.finished:
                self.tweens[write] = t
                write += 1
            else:
                self._tween_pool.append(t)

        del self.tweens[write:]

        super().update(delta)
