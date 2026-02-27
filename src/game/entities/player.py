from src.pyengine2D import (
    Engine, Keys, PhysicsBody2D, Node2D, RectangleNode, 
    ParticleEmitter2D, TweenManager, Easing
)
from src.game.player_controller import PlayerController
from src.game.player_fsm import PlayerStateMachine

class Player(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        
        # Physics setup
        self.use_gravity = True
        self.gravity = 1500.0
        self.can_push = True
        self.jump_force = -1200.0
        
        self.controller = PlayerController()
        self.state_machine = PlayerStateMachine(self)
        
        # Visuals
        self.vis = RectangleNode("PlayerVis", -20, -20, 40, 40, (0, 255, 200))
        self.add_child(self.vis)
        
        # Dust particles
        self.particles = ParticleEmitter2D("PlayerParticles")
        self.add_child(self.particles)
        
        self.score = 0
        self.register_signal("on_died")
        self.register_signal("on_score_changed")

    def update(self, delta):
        inp = Engine.instance.input
        if inp:
            input_state = {
                "move_left": inp.is_key_pressed(Keys.A) or inp.is_key_pressed(Keys.LEFT),
                "move_right": inp.is_key_pressed(Keys.D) or inp.is_key_pressed(Keys.RIGHT),
                "jump": inp.is_key_pressed(Keys.W) or inp.is_key_pressed(Keys.UP) or inp.is_key_pressed(Keys.SPACE)
            }
        else:
            input_state = {}
            
        self.controller.update(self, delta, input_state)
        
        super().update(delta)
        
        self.state_machine.update(delta)

        # Fall out of world
        if self.get_global_position()[1] > 1500:
            self.die()

    def jump_effect(self):
        gx, gy = self.get_global_position()
        self.particles.emit(gx, gy + 20, count=15, 
                            speed_range=(20, 80), 
                            angle_range=(200, 340),
                            color=(150, 150, 150))

    def add_score(self, amount):
        self.score += amount
        self.emit_signal("on_score_changed", score=self.score)

    def die(self):
        self.emit_signal("on_died")
        # Respawn logic
        self.local_x = 100
        self.local_y = 300
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.update_transforms()
        self._refresh_collider_cache(self)
