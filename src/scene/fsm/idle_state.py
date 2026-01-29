from src.scene.fsm.state import State


class IdleState(State):
    name="idle"
    def enter(self):
        # State is descriptive, do not force physics
        pass

    def update(self, delta):
        # If not on ground -> Fall
        if not self.body.on_ground:
            from src.scene.fsm.fall_state import FallState

            self.body.state_machine.change_state(FallState(self.body))
            return

        # If moving -> Walk
        if abs(self.body.velocity_x) > 0:
            from src.scene.fsm.walk_state import WalkState

            self.body.state_machine.change_state(WalkState(self.body))
