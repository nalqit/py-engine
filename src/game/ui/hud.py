from src.pyengine2D import Node, Engine

class HUD(Node):
    def __init__(self, name="HUD"):
        super().__init__(name)
        self.score = 0
        self.lives = 3
        self.fps = 0

    def update(self, delta):
        # Could read FPS explicitly from engine
        if Engine.instance:
            self.fps = int(Engine.instance.fps)
            
    def on_score_changed(self, score):
        self.score = score
        
    def on_died(self):
        self.lives -= 1

    def render(self, surface) -> None:
        if not Engine.instance:
            return
            
        r = Engine.instance.renderer
        
        # Draw stats
        r.draw_text(surface, f"FPS: {self.fps}", (0, 255, 0), 10, 10)
        r.draw_text(surface, f"Score: {self.score}", (255, 215, 0), 10, 40)
        r.draw_text(surface, f"Lives: {self.lives}", (255, 50, 50), 10, 70)
        
        # Engine diagnostics
        p = Engine.instance.profiler
        r.draw_text(surface, f"Logic: {p.get_average('Logic'):.1f}ms", (200, 200, 200), 10, 100)
        r.draw_text(surface, f"Render: {p.get_average('Render'):.1f}ms", (200, 200, 200), 10, 130)
