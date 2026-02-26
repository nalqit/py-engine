from typing import List, Optional
from src.pyengine2D.scene.node2d import Node2D

class Scene(Node2D):
    """
    A root node representing a distinct game state (Menu, Level, Benchmark).
    Provides lifecycle hooks managed by the SceneManager.
    """
    def __init__(self, name: str):
        super().__init__(name)
        
    def on_enter(self):
        """Called when this scene becomes the active (top) scene."""
        pass
        
    def on_exit(self):
        """Called when this scene is removed from the active stack."""
        pass
        
    def on_pause(self):
        """Called when another scene is pushed on top of this one."""
        pass
        
    def on_resume(self):
        """Called when scenes above this one are popped, making it active again."""
        pass


class SceneManager:
    """
    Manages a stack of scenes. Only the top scene is updated and rendered
    (unless configured to render scenes below for overlay effects).
    Integrates directly with Engine.run().
    """
    def __init__(self, engine):
        self.engine = engine
        self._stack: List[Scene] = []
        self._pending_switch: Optional[Scene] = None
        self._pending_push: Optional[Scene] = None
        self._pending_pop: bool = False

    @property
    def current_scene(self) -> Optional[Scene]:
        return self._stack[-1] if self._stack else None

    # Defer scene changes to the end of the frame to avoid mutating the tree during update
    
    def switch_scene(self, scene: Scene):
        """Replaces the entire stack with the new scene."""
        self._pending_switch = scene
        self._pending_push = None
        self._pending_pop = False

    def push_scene(self, scene: Scene):
        """Pushes a new scene on top, pausing the current one."""
        self._pending_push = scene
        self._pending_switch = None
        self._pending_pop = False

    def pop_scene(self):
        """Pops the top scene, resuming the one below it."""
        self._pending_pop = True
        self._pending_switch = None
        self._pending_push = None

    def process_pending_changes(self):
        """Called by Engine to apply deferred scene changes."""
        if self._pending_switch:
            while self._stack:
                scene = self._stack.pop()
                scene.on_exit()
                scene.destroy()
                
            self._stack.append(self._pending_switch)
            self._pending_switch.on_enter()
            self._pending_switch = None
            
        elif self._pending_pop and self._stack:
            scene = self._stack.pop()
            scene.on_exit()
            scene.destroy()
            self._pending_pop = False
            
            if self._stack:
                self._stack[-1].on_resume()
                
        elif self._pending_push:
            if self._stack:
                self._stack[-1].on_pause()
            self._stack.append(self._pending_push)
            self._pending_push.on_enter()
            self._pending_push = None

    def update(self, delta: float):
        """Updates ONLY the active scene at the top of the stack."""
        if self.current_scene:
            self.current_scene.update_transforms()
            self.current_scene.update(delta)

    def render(self, surface):
        """Renders ONLY the active scene (could be modified for overlays later)."""
        if self.current_scene:
            self.current_scene.render(surface)
