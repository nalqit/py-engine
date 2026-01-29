from src.engine.physics.controller import Controller


class InputController(Controller):
    def __init__(self, body, input_manager):
        super().__init__(body)
        self.input = input_manager
        

    def update(self, body, delta):
        dx = 0
        if self.input.is_pressed("move_left"):
            dx -= 1
        if self.input.is_pressed("move_right"):
            dx += 1

        # Set body horizontal velocity
        body.intent_x = dx


        # Jump logic
        if self.input.is_pressed("move_up") and body.on_ground:
            body.velocity_y = body.jump_force
            body.on_ground = False

        # Super jump / fast fall? (keeping user's recent change)
        if self.input.is_pressed("move_down"):
            body.velocity_y += body.gravity * 2 * delta

