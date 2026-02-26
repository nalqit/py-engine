class State:
    """
    Base class for all states.
    States control *behavior*, not physics.
    """

    def __init__(self, body):
        self.body = body  # PhysicsBody2D owner

    def enter(self):
        """Called once when state is entered"""
        pass

    def update(self, delta):
        """Called every frame"""
        pass

    def exit(self):
        """Called once when leaving state"""
        pass
