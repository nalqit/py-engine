from src.game.player_states import IdleState, RunState, JumpState, FallState

class PlayerStateMachine:
    def __init__(self, player):
        self.player = player
        self.states = {
            "IdleState": IdleState(self),
            "RunState": RunState(self),
            "JumpState": JumpState(self),
            "FallState": FallState(self)
        }
        self.current_state = self.states["IdleState"]
        self.current_state_name = "IdleState"

    def get_state_name(self):
        return self.current_state_name
        
    def change_state(self, new_state_name):
        if self.current_state:
            self.current_state.exit()
            
        self.current_state_name = new_state_name
        self.current_state = self.states[new_state_name]
        self.current_state.enter()

    def update(self, delta):
        if self.current_state:
            self.current_state.update(delta)
        
        # Automatic jump detection hooks outside the controller loop
        if self.player.velocity_y < 0 and self.current_state_name != "JumpState":
            self.change_state("JumpState")
