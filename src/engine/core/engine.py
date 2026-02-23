import pygame
import sys

from src.engine.core.input import InputSystem
from src.engine.core.renderer import Renderer
from src.engine.utils.profiler import EngineProfiler


class EngineEvent:
    """Lightweight event object emitted by the engine runtime."""
    def __init__(self, event_type, **kwargs):
        self.type = event_type
        for k, v in kwargs.items():
            setattr(self, k, v)


class Engine:
    """
    Central game runtime.
    Manages display, timing, input, rendering, profiling, and the main loop.
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
        self.profiler = EngineProfiler()
        self.events = []

    def begin_frame(self):
        """Call at the start of each frame. Returns raw dt."""
        self.dt = self._clock.tick(60) / 1000.0
        self.fps = self._clock.get_fps()
        self.profiler.log_frame(self.dt)
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

    def run(self, root, on_fixed_update=None, on_render=None):
        """
        Built-in game loop with fixed-timestep accumulator.

        Args:
            root: Scene root Node2D — updated and rendered each frame.
            on_fixed_update: Optional callback(engine, root, fixed_dt) called
                             each physics step after root.update().
            on_render: Optional callback(engine, root, surface) called each
                       frame after root.render() for HUD/overlay drawing.

        Existing begin_frame()/end_frame() remain available for games
        that need fully manual loop control.
        """
        accumulator = 0.0
        while self.running:
            dt = self.begin_frame()
            accumulator += dt

            self.profiler.begin("Logic")
            while accumulator >= self.fixed_dt:
                root.update_transforms()
                root.update(self.fixed_dt)
                if on_fixed_update:
                    on_fixed_update(self, root, self.fixed_dt)
                accumulator -= self.fixed_dt
            self.profiler.end("Logic")

            self.profiler.begin("Render")
            self.renderer.fill(self.game_surface, (0, 0, 0))
            root.render(self.game_surface)
            if on_render:
                on_render(self, root, self.game_surface)
            self.profiler.end("Render")

            self.end_frame()

        self.quit()

    def get_ticks_ms(self):
        """System ticks in ms — for drift comparison only."""
        return pygame.time.get_ticks()

    def quit(self):
        self.profiler.print_summary()
        pygame.quit()
        sys.exit()

