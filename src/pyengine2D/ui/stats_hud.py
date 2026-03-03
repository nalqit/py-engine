from src.pyengine2D.scene.node2d import Node2D

class StatsHUD(Node2D):
    """
    A simple heads-up display to show engine stats like FPS and an optional extra text string.
    """
    def __init__(self, name: str = "StatsHUD"):
        super().__init__(name)
        self.extra_text = ""
        self.show_fps = True
        self.z_index = 1000  # Ensure it renders on top of everything
        self.is_ui = True    # Prevent camera transforms if applicable

    def render(self, surface):
        from src.pyengine2D.core.engine import Engine
        if not Engine.instance or not getattr(Engine.instance, 'debug_mode', False):
            return
            
        renderer = Engine.instance.renderer
        if not renderer:
            return
            
        y_offset = 10
        if self.show_fps:
            fps = Engine.instance.fps
            renderer.draw_text(surface, f"FPS: {int(fps)}", (0, 255, 0), 10, y_offset, size=16, bold=True)
            y_offset += 25
            
        if self.extra_text:
            renderer.draw_text(surface, self.extra_text, (255, 255, 255), 10, y_offset, size=16)

        super().render(surface)
