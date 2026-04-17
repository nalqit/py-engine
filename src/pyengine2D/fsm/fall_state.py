from src.pyengine2D.fsm.state import State
from src.pyengine2D.fsm.idle_state import IdleState
from src.pyengine2D.fsm.walk_state import WalkState
import warnings


_DEPRECATION_MESSAGE = (
    "pyengine2D.fsm.FallState is deprecated and will be removed in a future release. "
    "Prefer game-local state implementations."
)


class FallState(State):
    name="fall"
    def __init__(self, body):
        warnings.warn(_DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
        super().__init__(body)

    def update(self, delta):
        # If we touched the ground
        if self.body.on_ground:
            if abs(self.body.velocity_x) > 0:
                self.body.state_machine.change_state(WalkState(self.body))
            else:
                self.body.state_machine.change_state(IdleState(self.body))
