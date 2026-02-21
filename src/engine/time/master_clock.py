class MasterClock:
    """
    Internal Engine Clock for absolute time tracking.
    Resolves the float-drift and decouples engine time from external biases (like pygame.mixer).
    """
    def __init__(self):
        self.elapsed = 0.0
        
    def update(self, delta: float):
        self.elapsed += delta
        
    def get_time(self) -> float:
        return self.elapsed
