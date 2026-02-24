from src.engine import Node2D

class HUD(Node2D):
    """
    A Custom UI node that listens to Signals from the Player and the Level.
    This demonstrates the Observer pattern: The HUD does not need a reference
    to the Player object every frame, it simply updates its state when signals fire.
    """
    def __init__(self, name):
        super().__init__(name)
        self.score = 0
        self.health = 3
        # UI rendering is done in screen space, so local_x/y aren't used for layout

    # --- Signal Handlers ---

    def on_player_health_changed(self, new_health):
        self.health = new_health
        
    def on_score_added(self, score_value):
        self.score += score_value

    def on_player_died(self):
        self.health = 0
        self.score = 0 # Reset or do Game Over logic

    # --- Rendering ---

    def render(self, surface):
        # Developer Guide Hint: Import Engine locally in render to avoid circular imports
        from src.engine import Engine
        if not Engine.instance:
            return
            
        renderer = Engine.instance.renderer
        
        # The HUD draws directly to the screen (ignoring camera)
        
        # 1. Draw Score
        score_text = f"SCORE: {self.score}"
        renderer.draw_text(surface, score_text, (255, 255, 255), 20, 20, size=24, bold=True)
        
        # 2. Draw Health
        health_text = f"HEALTH: {'♥ ' * max(0, self.health)}"
        renderer.draw_text(surface, health_text, (255, 50, 50), 20, 50, size=24, bold=True)
        
        # We don't call super() because the HUD has no graphical children usually, 
        # but it's safe to do if we add icons later.
        super().render(surface)
