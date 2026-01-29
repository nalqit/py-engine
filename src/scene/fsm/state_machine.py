class StateMachine:
    def __init__(self, body):
        self.body = body
        self.current_state = None

    def change_state(self, new_state):
        if self.current_state:
            self.current_state.exit()

        self.current_state = new_state

        if self.current_state:
            self.current_state.enter()


    def update(self, delta):
        if self.current_state:
            self.current_state.update(delta)
