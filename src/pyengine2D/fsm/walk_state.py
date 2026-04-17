from src.pyengine2D.fsm.state import State
import warnings


_DEPRECATION_MESSAGE = (
    "pyengine2D.fsm.WalkState is deprecated and will be removed in a future release. "
    "Prefer game-local state implementations."
)


class WalkState(State):
    name="walk"
    def __init__(self, body):
        warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
        super().__init__(body)

    def update(self, delta):
        # If not on ground -> Fall
        if not self.body.on_ground:
            from src.pyengine2D.fsm.fall_state import FallState

            self.body.state_machine.change_state(FallState(self.body))
            return

        if abs(self.body.velocity_x) == 0:
            from src.pyengine2D.fsm.idle_state import IdleState

            self.body.state_machine.change_state(IdleState(self.body))
