from src.pyengine2D.fsm.state import State
import warnings


_DEPRECATION_MESSAGE = (
    "pyengine2D.fsm.IdleState is deprecated and will be removed in a future release. "
    "Prefer game-local state implementations."
)


class IdleState(State):
    name="idle"
    def __init__(self, body):
        warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
        super().__init__(body)

    def enter(self):
        # State is descriptive, do not force physics
        pass

    def update(self, delta):
        # If not on ground -> Fall
        if not self.body.on_ground:
            from src.pyengine2D.fsm.fall_state import FallState

            self.body.state_machine.change_state(FallState(self.body))
            return

        # If moving -> Walk
        if abs(self.body.velocity_x) > 0:
            from src.pyengine2D.fsm.walk_state import WalkState

            self.body.state_machine.change_state(WalkState(self.body))
