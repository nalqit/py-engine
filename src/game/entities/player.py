from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.physics.input_controller import InputController


class Player(PhysicsBody2D):
    def __init__(self, name, x, y, input_manager, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.controller = InputController(self,input_manager)

        self.use_gravity = True
        self.speed = 200.0
        self.jump_force = -400.0

    def on_collision_enter(self, other):
        
        if other.layer == "box":
            print("Player started pushing box")
