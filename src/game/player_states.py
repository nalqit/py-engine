class PlayerState:
    def __init__(self, state_machine):
        self.sm = state_machine
        self.player = state_machine.player

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self, delta):
        pass


class IdleState(PlayerState):
    def update(self, delta):
        if not self.player.controller.is_grounded:
            self.sm.change_state("FallState")
            return
            
        if abs(self.player.velocity_x) >= 10.0:
            self.sm.change_state("RunState")


class RunState(PlayerState):
    def update(self, delta):
        if not self.player.controller.is_grounded:
            self.sm.change_state("FallState")
            return
            
        if abs(self.player.velocity_x) < 10.0:
            self.sm.change_state("IdleState")


class JumpState(PlayerState):
    def update(self, delta):
        if self.player.velocity_y >= 0:
            self.sm.change_state("FallState")


class FallState(PlayerState):
    def update(self, delta):
        # We wait for the controller to flag is_grounded 
        # indicating we hit the floor
        if self.player.controller.is_grounded:
            if abs(self.player.velocity_x) >= 10.0:
                self.sm.change_state("RunState")
            else:
                self.sm.change_state("IdleState")
