from src.game.player_states import IdleState

class PlayerStateMachine:
    """
    Finite State Machine for managing Player behavioral states.
    Respects Level 5 architectural rules:
    - Observes player state (velocity, grounded) after physics update
    - Transitions between Idle, Run, Jump, and Fall
    - Prevents self-transitions
    """

    def __init__(self, player):
        self.player = player
        self.current_state = IdleState()
        self.current_state.enter(self.player)

    def change_state(self, new_state):
        # Tweak 2: Protect against self-transitions
        if isinstance(self.current_state, type(new_state)):
            return

        # print(f"[DEBUG] {self.player.name} State Transition: {type(self.current_state).__name__} -> {type(new_state).__name__}")
        
        self.current_state.exit(self.player)
        self.current_state = new_state
        self.current_state.enter(self.player)

    def update(self, delta):
        """Runs the current state logic and handles any returned transitions."""
        next_state = self.current_state.update(self.player, delta)
        if next_state:
            self.change_state(next_state)
            
    def get_state_name(self):
        return type(self.current_state).__name__
