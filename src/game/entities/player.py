from src.engine import (
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
        
        # Animations & tweens
        self.tween_mgr = TweenManager("TweenMgr")
        self.add_child(self.tween_mgr)
        
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
            
        was_grounded = self.controller.is_grounded
        
        self.controller.update(self, delta, input_state)
        
        if input_state.get("jump", False) and was_grounded and self.velocity_y < 0:
            self.apply_juice(0.7, 1.3)
            self.jump_effect()

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

    def apply_juice(self, sx, sy, duration=0.2):
        if self.tween_mgr.is_tweening(self.vis, "scale_y"):
            return
            
        def get_offsets(ts_x, ts_y):
            ox = 40 * (1 - ts_x) / 2
            oy = 40 * (1 - ts_y)
            return ox, oy
            
        def reset_scale():
            self.tween_mgr.interpolate(self.vis, "scale_x", self.vis.scale_x, 1.0, duration, Easing.quad_out)
            self.tween_mgr.interpolate(self.vis, "scale_y", self.vis.scale_y, 1.0, duration, Easing.quad_out)
            self.tween_mgr.interpolate(self.vis, "local_x", self.vis.local_x, -20.0, duration, Easing.quad_out)
            self.tween_mgr.interpolate(self.vis, "local_y", self.vis.local_y, -20.0, duration, Easing.quad_out)
            
            self.tween_mgr.interpolate(self.collider, "scale_x", self.collider.scale_x, 1.0, duration, Easing.quad_out)
            self.tween_mgr.interpolate(self.collider, "scale_y", self.collider.scale_y, 1.0, duration, Easing.quad_out)
            self.tween_mgr.interpolate(self.collider, "local_x", self.collider.local_x, -20.0, duration, Easing.quad_out)
            self.tween_mgr.interpolate(self.collider, "local_y", self.collider.local_y, -20.0, duration, Easing.quad_out)

        ox, oy = get_offsets(sx, sy)
        self.tween_mgr.interpolate(self.vis, "scale_x", 1.0, sx, duration/2, Easing.quad_out, on_complete=reset_scale)
        self.tween_mgr.interpolate(self.vis, "scale_y", 1.0, sy, duration/2, Easing.quad_out)
        self.tween_mgr.interpolate(self.vis, "local_x", -20.0, -20.0 + ox, duration/2, Easing.quad_out)
        self.tween_mgr.interpolate(self.vis, "local_y", -20.0, -20.0 + oy, duration/2, Easing.quad_out)
        
        self.tween_mgr.interpolate(self.collider, "scale_x", 1.0, sx, duration/2, Easing.quad_out)
        self.tween_mgr.interpolate(self.collider, "scale_y", 1.0, sy, duration/2, Easing.quad_out)
        self.tween_mgr.interpolate(self.collider, "local_x", -20.0, -20.0 + ox, duration/2, Easing.quad_out)
        self.tween_mgr.interpolate(self.collider, "local_y", -20.0, -20.0 + oy, duration/2, Easing.quad_out)

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
