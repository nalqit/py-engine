from src.scene.physics.controller import Controller


class InputController(Controller):
    def __init__(self, input_manager):
        self.input = input_manager

    def update(self, body, delta):
        dx = 0
        if self.input.is_pressed("move_left"):
            dx -= 1
        if self.input.is_pressed("move_right"):
            dx += 1

        # Set body horizontal velocity
        body.velocity_x = dx * body.speed

        # Jump logic
        if self.input.is_pressed("move_up") and body.on_ground:
            body.velocity_y = body.jump_force
            body.on_ground = False

        # Super jump / fast fall? (keeping user's recent change)
        if self.input.is_pressed("move_down"):
            body.velocity_y = (-body.jump_force + body.gravity) / 2
