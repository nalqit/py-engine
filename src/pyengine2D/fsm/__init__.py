import warnings

from .state_machine import StateMachine
from .state import State


warnings.warn(
    "pyengine2D.fsm is deprecated and will be removed in a future release. "
    "Prefer game-local FSM implementations.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ['StateMachine', 'State']
