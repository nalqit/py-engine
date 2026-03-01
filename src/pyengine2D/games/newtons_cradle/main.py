import math
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.core.engine import Engine
from src.pyengine2D.physics.rigid_body_2d import RigidBody2D
from src.pyengine2D.physics.physics_world_2d import PhysicsWorld2D
from src.pyengine2D.physics.distance_constraint import DistanceConstraint
from src.pyengine2D.collision.collision_world import CollisionWorld
from src.pyengine2D.collision.circle_collider2d import CircleCollider2D

class Ball(RigidBody2D):
    """
    Visual wrapper around the new core engine RigidBody2D.
    """
    def __init__(self, name, x, y, collider, collision_world, radius=20):
        super().__init__(name, x, y, collider=collider, collision_world=collision_world, mass=1.0)
        self.is_dragged = False
        self.radius = radius

    def render(self, surface):
        if not Engine.instance: return
        renderer = Engine.instance.renderer
        
        gx, gy = self.get_global_position()
        
        # Render ball outline and inner fill
        renderer.draw_circle(surface, (200, 200, 210), int(gx), int(gy), self.radius)
        renderer.draw_circle(surface, (100, 100, 120), int(gx), int(gy), self.radius, 2)
        renderer.draw_circle(surface, (255, 255, 255), int(gx) - 5, int(gy) - 5, 4)

        super().render(surface)


class NewtonCradle(Node2D):
    """
    Scene root that uses PyEngine 2D's internal PhysicsWorld2D and CollisionWorld.
    """
    def __init__(self):
        super().__init__("NewtonCradle")
        
        # 1. Provide the universal collision engine 
        self.collision_world = CollisionWorld("GlobalCollisionWorld", cell_size=128)
        self.add_child(self.collision_world)
        
        # 2. Instantiate the physics solver node (handles constraints and substepping)
        self.physics_world = PhysicsWorld2D("SimulationWorld", gravity_y=800.0, sub_steps=10)
        self.add_child(self.physics_world)
        
        self.balls = []
        self.dragged_ball = None
        
        start_x = 400 - 40 * 2
        for i in range(5):
            pivot_x = start_x + 40 * i
            pivot_y = 100
            ball_x = pivot_x
            ball_y = pivot_y + 250
            
            # The collider is now an engine native CircleCollider2D!
            collider = CircleCollider2D(f"Collider_{i}", 0, 0, radius=20)
            collider.visible = False
            collider.layer = "balls"
            collider.mask.add("balls")
            
            ball = Ball(f"Ball_{i}", ball_x, ball_y, collider=collider, collision_world=self.collision_world, radius=20)
            rope = DistanceConstraint(f"Rope_{i}", pivot_x, pivot_y, ball, length=250)
            
            # Parent the collider to the RigidBody2D so it follows its transform
            ball.add_child(collider)
            
            self.physics_world.add_child(rope)
            self.physics_world.add_child(ball)
            
            self.balls.append(ball)

    def update(self, dt):
        inp = Engine.instance.input
        mx, my = inp.get_mouse_pos()
        
        # Interaction (Drag & Drop)
        if inp.is_mouse_just_pressed(0):
            for ball in self.balls:
                bx, by = ball.get_global_position()
                if math.hypot(mx - bx, my - by) <= ball.radius:
                    self.dragged_ball = ball
                    ball.is_dragged = True
                    ball.is_kinematic = True # Freeze physics integration
                    ball.vx = 0.0
                    ball.vy = 0.0
                    break
                    
        if self.dragged_ball:
            if not inp.is_mouse_pressed(0):
                self.dragged_ball.is_dragged = False
                self.dragged_ball.is_kinematic = False
                self.dragged_ball = None
            else:
                self.dragged_ball.local_x = mx
                self.dragged_ball.local_y = my

        # Engine handles updating collision world cache + solving sub-step physics!
        super().update(dt)

def main():
    engine = Engine("Newton's Cradle Simulation (Unified Engine Physics)", 800, 600)
    cradle_scene = NewtonCradle()
    cradle_scene.print_tree()
    engine.run(cradle_scene)

if __name__ == "__main__":
    main()
