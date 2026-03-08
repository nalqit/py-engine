import pygame
import sys

from src.pyengine2D.core.input import InputSystem
from src.pyengine2D.core.renderer import Renderer
from src.pyengine2D.utils.profiler import EngineProfiler
from src.pyengine2D.time.master_clock import MasterClock
from src.pyengine2D.ui.event_system import EventPropagationSystem
from src.pyengine2D.scene.scene_manager import SceneManager
from src.pyengine2D.core.audio_manager import AudioManager


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
        # We implicitly init mixer here too via pygame.init()
        pygame.mixer.pre_init(44100, -16, 2, 512)
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
        self.debug_mode = False
        self.input = InputSystem(self)
        self.renderer = Renderer()
        
        from src.pyengine2D.rendering.renderer2d import Renderer2D
        self.scene_renderer = Renderer2D(None)
        
        self.profiler = EngineProfiler()
        self.master_clock = MasterClock()
        self.events = []
        self.ui_events = EventPropagationSystem(self)
        self.scene_manager = SceneManager(self)
        self.audio = AudioManager()

    def begin_frame(self):
        """Call at the start of each frame. Returns raw dt."""
        self.dt = self._clock.tick(60) / 1000.0
        self.dt = min(self.dt, 0.25)  # Cap to prevent spiral-of-death
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

    def run(self, root=None, on_fixed_update=None, on_render=None):
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
            self.profiler.begin("Frame")
            dt = self.begin_frame()
            
            active_root = root if root is not None else self.scene_manager.current_scene
            
            # Process UI Events once per frame
            if active_root:
                self.ui_events.process_events(active_root)
            
            accumulator += dt
            accumulator = min(accumulator, self.fixed_dt * 8)

            self.profiler.begin("Logic")
            while accumulator >= self.fixed_dt:
                self.master_clock.update(self.fixed_dt)
                if active_root:
                    active_root.update_transforms()
                    active_root.update(self.fixed_dt)
                if on_fixed_update and active_root:
                    on_fixed_update(self, active_root, self.fixed_dt)
                accumulator -= self.fixed_dt
            self.profiler.end("Logic")

            self.profiler.begin("Render")
            self.renderer.fill(self.game_surface, (0, 0, 0))
            if active_root:
                from src.pyengine2D.scene.node2d import Node2D
                self.scene_renderer.camera = Node2D.camera
                self.scene_renderer.debug_mode = self.debug_mode
                self.scene_renderer.draw(active_root, self.game_surface, self)
            if on_render and active_root:
                on_render(self, active_root, self.game_surface)
            self.profiler.end("Render")

            self.scene_manager.process_pending_changes()
            self.profiler.end("Frame")
            self.end_frame()

        self.quit()

    def get_ticks_ms(self):
        """System ticks in ms — for drift comparison only."""
        return pygame.time.get_ticks()

    def quit(self):
        self.profiler.print_summary()
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.quit()
        if not getattr(self, "suppress_exit", False):
            sys.exit()

