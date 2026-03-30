import math
from src.pyengine2D import Node2D,Engine,RigidBody2D,PhysicsWorld2D,DistanceConstraint,CollisionWorld,CircleCollider2D

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
        
        from src.pyengine2D.scene.scene_serializer import SceneSerializer
        import os
        
        custom_types = {"NewtonCradle": NewtonCradle, "Ball": Ball}
        scene_path = os.path.join(os.path.dirname(__file__), "newtons_cradle.scene")
        
        # We load the entire scene as the master tree
        loaded_scene = SceneSerializer.load(scene_path, custom_types)
        
        # Adopt children into self so 'NewtonCradle' maintains its game loop
        for child in list(loaded_scene.children):
            self.add_child(child)
        
        self.collision_world = self.get_node("GlobalCollisionWorld")
        self.physics_world = self.get_node("SimulationWorld")
        
        self.balls = []
        self.dragged_ball = None
        
        # Link up the loaded balls and constraints since SceneSerializer bypassed __init__
        for i in range(5):
            ball = self.get_node(f"Ball_{i}")
            if getattr(ball, "collider", None) is None:
                # Fallback link
                ball.collider = ball.get_node(f"Collider_{i}")
                ball.collision_world = self.collision_world
            
            # ── Crucial Physics Setup for Newton's Cradle ──
            # 1. Newton's cradle requires 100% elastic collisions to transfer full energy
            ball.restitution = 1.0
            
            # 2. Collider mask must include "default" layer, else balls pass through each other completely 
            if "default" not in ball.collider.mask:
                ball.collider.mask.add("default")
                
            if getattr(ball, "radius", None) is None:
                ball.radius = 20
                
            self.balls.append(ball)
            
            # DistanceConstraints might need their `body_a` re-linked
            rope = self.get_node(f"Rope_{i}")
            if rope and getattr(rope, "_body_name", "") == ball.name:
                rope.body_a = ball

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
