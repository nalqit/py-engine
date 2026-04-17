import warnings


_DEPRECATION_MESSAGE = (
    "pyengine2D.fsm.State is deprecated and will be removed in a future release. "
    "Prefer game-local FSM base classes."
)


class State:
    """
    Base class for all states.
    States control *behavior*, not physics.
    """

    def __init__(self, body):
        warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
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
