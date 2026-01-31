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

        body.intent_x = dx

    # Jump (نية فقط)
        if self.input.is_pressed("move_up") and body.on_ground:
            body.intent_y = body.jump_force

    # Fast fall (نية فقط)
        if self.input.is_pressed("move_down") and not body.on_ground:
            body.intent_y = body.gravity


