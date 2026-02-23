import pygame
import sys

from src.engine.core.input import InputSystem
from src.engine.core.renderer import Renderer


class EngineEvent:
    """Lightweight event object emitted by the engine runtime."""
    def __init__(self, event_type, **kwargs):
        self.type = event_type
        for k, v in kwargs.items():
            setattr(self, k, v)


class Engine:
    """
    Central game runtime.
    Manages display, timing, input, rendering, and the main loop.
    This is the ONLY place pygame display/event/clock is used.
    Game code interacts exclusively with Engine, InputSystem, and Renderer.
    """
    instance = None

    def __init__(self, title, virtual_w=800, virtual_h=600):
        pygame.init()
        Engine.instance = self
        self.virtual_w = virtual_w
        self.virtual_h = virtual_h
        self._screen = pygame.display.set_mode((virtual_w, virtual_h), pygame.RESIZABLE)
        self.game_surface = pygame.Surface((virtual_w, virtual_h))
        pygame.display.set_caption(title)
        self._clock = pygame.time.Clock()
        self.running = True
        self.fixed_dt = 1.0 / 60.0
        self.dt = 0.0
        self.fps = 0.0
        self.input = InputSystem(self)
        self.renderer = Renderer()
        self.events = []

    def begin_frame(self):
        """Call at the start of each frame. Returns raw dt."""
        self.dt = self._clock.tick(60) / 1000.0
        self.fps = self._clock.get_fps()
        self.events.clear()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.events.append(EngineEvent('key_down', key=event.key))
        self.input._update()
        return self.dt

    def end_frame(self):
        """Scales virtual surface to window and flips display."""
        scaled = pygame.transform.scale(self.game_surface, self._screen.get_size())
        self._screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def get_ticks_ms(self):
        """System ticks in ms — for drift comparison only."""
        return pygame.time.get_ticks()

    def quit(self):
        pygame.quit()
        sys.exit()
