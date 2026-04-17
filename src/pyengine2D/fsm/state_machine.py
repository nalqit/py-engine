import warnings


_DEPRECATION_MESSAGE = (
    "pyengine2D.fsm.StateMachine is deprecated and will be removed in a future release. "
    "Prefer game-local FSM implementations."
)


class StateMachine:
    def __init__(self, body):
        warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
        self.body = body
        self.current_state = None

    def change_state(self, new_state):
        if self.current_state:
            self.current_state.exit()

        self.current_state = new_state

        if self.current_state:
            self.current_state.enter()


    def update(self, delta):
        if self.current_state:
            self.current_state.update(delta)
