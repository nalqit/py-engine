from src.scene.fsm.state import State
from src.scene.fsm.idle_state import IdleState
from src.scene.fsm.walk_state import WalkState


class FallState(State):
    name="fall"
    def update(self, delta):
        # If we touched the ground
        if self.body.on_ground:
            if abs(self.body.velocity_x) > 0:
                self.body.state_machine.change_state(WalkState(self.body))
            else:
                self.body.state_machine.change_state(IdleState(self.body))
