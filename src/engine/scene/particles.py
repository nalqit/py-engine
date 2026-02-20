import pygame
import random
from src.engine.scene.node2d import Node2D

class Particle:
    def __init__(self, x, y, vx, vy, lifetime, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.initial_lifetime = lifetime
        self.lifetime = lifetime
        self.color = color

    def update(self, delta, gravity):
        self.vy += gravity * delta
        self.x += self.vx * delta
        self.y += self.vy * delta
        self.lifetime -= delta

    def is_dead(self):
        return self.lifetime <= 0

class ParticleEmitter2D(Node2D):
    """
    A simple particle emitter for "juice".
    """
    def __init__(self, name="ParticleEmitter"):
        super().__init__(name, 0, 0)
        self.particles = []
        self.gravity = 200.0
        self.active = True

    def emit(self, x, y, count=10, 
             speed_range=(50, 150), 
             angle_range=(0, 360), 
             lifetime_range=(0.5, 1.0),
             color=(200, 200, 200)):
        
        import math
        for _ in range(count):
            angle = math.radians(random.uniform(*angle_range))
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(*lifetime_range)
            
            self.particles.append(Particle(x, y, vx, vy, lifetime, color))

    def update(self, delta: float):
        if not self.active:
            return

        # Update and filter dead particles
        for p in self.particles:
            p.update(delta, self.gravity)
        
        self.particles = [p for p in self.particles if not p.is_dead()]
        
        super().update(delta)

    def render(self, surface):
        # We need to render particles in screen space
        # Camera is usually set as a static variable on Node2D or we find it
        root = self._get_root()
        camera = root.get_node("Camera")
        cam_x, cam_y = (camera.local_x, camera.local_y) if camera else (0, 0)

        for p in self.particles:
            alpha = int((p.lifetime / p.initial_lifetime) * 255)
            # Use a slightly complex color to respect alpha if needed, 
            # but pygame.draw.circle is simpler
            # We skip real alpha for performance/simplicity in this demo
            color = self._adjust_color_alpha(p.color, alpha)
            
            screen_x = p.x - cam_x
            screen_y = p.y - cam_y
            
            size = max(1, int(3 * (p.lifetime / p.initial_lifetime)))
            pygame.draw.circle(surface, color, (int(screen_x), int(screen_y)), size)

        super().render(surface)

    def _adjust_color_alpha(self, color, alpha):
        # Pygame colors can be (R, G, B) or (R, G, B, A)
        # But draw.circle with alpha requires a surface or special handling.
        # We'll just return the RGB for now to keep it simple and fast.
        return color

    def _get_root(self):
        root = self
        while root.parent:
            root = root.parent
        return root
