import math
import random
from src.pyengine2D.scene.node2d import Node2D


class Particle:
    """
    A single particle with position, velocity, lifetime, and color.
    Designed to be pooled — reset() re-initialises without allocation.
    """
    __slots__ = ('x', 'y', 'vx', 'vy', 'initial_lifetime', 'lifetime', 'color', 'alive')

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.initial_lifetime = 1.0
        self.lifetime = 0.0
        self.color = (200, 200, 200)
        self.alive = False

    def init(self, x, y, vx, vy, lifetime, color):
        """Re-initialise this particle for reuse from pool."""
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.initial_lifetime = lifetime
        self.lifetime = lifetime
        self.color = color
        self.alive = True

    def update(self, delta, gravity):
        self.vy += gravity * delta
        self.x += self.vx * delta
        self.y += self.vy * delta
        self.lifetime -= delta
        if self.lifetime <= 0:
            self.alive = False

    def is_dead(self):
        return not self.alive


class ParticleEmitter2D(Node2D):
    """
    A pooled particle emitter for "juice".

    Performance features:
        - Pre-allocated particle pool (no per-frame allocation/GC).
        - In-place partition of alive/dead particles (no list rebuild).
        - Batch rendering (single draw sweep per frame).
    """

    def __init__(self, name="ParticleEmitter", pool_size=256):
        super().__init__(name, 0, 0)
        self.gravity = 200.0
        self.active = True

        # Pre-allocate particle pool
        self._pool = [Particle() for _ in range(pool_size)]
        self._particles = []           # active particles (references into pool)
        self._pool_stack = list(self._pool)  # free particles available for reuse

    def emit(self, x, y, count=10,
             speed_range=(50, 150),
             angle_range=(0, 360),
             lifetime_range=(0.5, 1.0),
             color=(200, 200, 200)):

        for _ in range(count):
            # Acquire from pool (or create new if pool exhausted)
            if self._pool_stack:
                p = self._pool_stack.pop()
            else:
                p = Particle()

            angle = math.radians(random.uniform(*angle_range))
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(*lifetime_range)
            p.init(x, y, vx, vy, lifetime, color)
            self._particles.append(p)

    def update(self, delta: float):
        if not self.active:
            return

        # Update all active particles and partition in-place
        write = 0
        for i in range(len(self._particles)):
            p = self._particles[i]
            p.update(delta, self.gravity)
            if p.alive:
                self._particles[write] = p
                write += 1
            else:
                # Return dead particle to pool
                self._pool_stack.append(p)

        # Truncate the list to only alive particles (no new list alloc)
        del self._particles[write:]

        super().update(delta)

    def render(self, surface):
        # Camera offset
        cx, cy = 0, 0
        if Node2D.camera:
            from src.pyengine2D.core.engine import Engine
            half_w = Engine.instance.virtual_w // 2 if Engine.instance else 400
            half_h = Engine.instance.virtual_h // 2 if Engine.instance else 300
            cx = Node2D.camera.local_x - half_w
            cy = Node2D.camera.local_y - half_h
        else:
            root = self._get_root()
            camera = root.get_node("Camera")
            if camera:
                from src.pyengine2D.core.engine import Engine
                half_w = Engine.instance.virtual_w // 2 if Engine.instance else 400
                half_h = Engine.instance.virtual_h // 2 if Engine.instance else 300
                cx = camera.local_x - half_w
                cy = camera.local_y - half_h

        from src.pyengine2D.core.engine import Engine
        renderer = Engine.instance.renderer if Engine.instance else None

        # Batch render all particles
        for p in self._particles:
            screen_x = int(p.x - cx)
            screen_y = int(p.y - cy)
            size = max(1, int(3 * (p.lifetime / p.initial_lifetime)))
            if renderer:
                renderer.draw_circle(surface, p.color, screen_x, screen_y, size)

        super().render(surface)

    @property
    def particles(self):
        """Backward-compatible property — returns the active particle list."""
        return self._particles

    def _get_root(self):
        root = self
        while root.parent:
            root = root.parent
        return root
