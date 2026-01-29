from src.engine.fsm.state import State


class WalkState(State):
    name="walk"
    def update(self, delta):
        # If not on ground -> Fall
        if not self.body.on_ground:
            from src.engine.fsm.fall_state import FallState

            self.body.state_machine.change_state(FallState(self.body))
            return

        if abs(self.body.velocity_x) == 0:
            from src.engine.fsm.idle_state import IdleState

            self.body.state_machine.change_state(IdleState(self.body))
