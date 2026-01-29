class Controller:
    """Base class for all controllers that decide movement intent for PhysicsBody2D."""

    def __init__(self, body):
        self.body = body


    def update(self, body, delta):
        pass
