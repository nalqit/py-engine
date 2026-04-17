"""
Breakout — Main entry point.
A classic brick-breaking game where players control a paddle to bounce
a ball and destroy bricks.

Controls: Left/Right arrow keys to move paddle.
"""

from src.pyengine2D import Engine, Node2D, CollisionWorld, Collider2D, Camera2D, StatsHUD, Keys
from src.pyengine2D.scene.circle_node import CircleNode
from src.pyengine2D.scene.rectangle_node import RectangleNode
import math


class Breakout:
    def __init__(self):
        self.engine = Engine("Breakout", 800, 600)
        
        self.root = Node2D("Root")
        
        self.collision_world = CollisionWorld("CollisionWorld")
        self.root.add_child(self.collision_world)
        
        self.game = Node2D("Game")
        self.root.add_child(self.game)
        
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.victory = False
        
        self.paddle_speed = 400
        self.ball_speed = 300
        
        self.create_paddle()
        self.create_ball()
        self.create_bricks()
        self.create_walls()
        
        self.camera = Camera2D("Camera")
        self.root.add_child(self.camera)
        Node2D.camera = self.camera
        
        self.hud = StatsHUD("HUD")
        self.root.add_child(self.hud)
        
    def create_paddle(self):
        paddle_col = Collider2D("Paddle_Col", -60, -15, 120, 30)
        paddle_col.layer = "paddle"
        paddle_col.mask = {"ball"}
        
        self.paddle = RectangleNode("Paddle", 400, 550, 120, 30, (100, 200, 255))
        self.paddle.add_child(paddle_col)
        self.game.add_child(self.paddle)
        
    def create_ball(self):
        ball_col = Collider2D("Ball_Col", -10, -10, 20, 20)
        ball_col.layer = "ball"
        ball_col.mask = {"paddle", "brick", "wall"}
        
        self.ball = CircleNode("Ball", 400, 500, 10, (255, 255, 255))
        self.ball.add_child(ball_col)
        self.game.add_child(self.ball)
        
        self.ball_dx = math.cos(math.pi / 4) * self.ball_speed
        self.ball_dy = -math.sin(math.pi / 4) * self.ball_speed
        
    def create_bricks(self):
        self.bricks = []
        
        rows = 5
        cols = 10
        brick_w = 70
        brick_h = 20
        spacing = 5
        start_x = 85
        start_y = 60
        
        colors = [
            (255, 100, 100),
            (255, 165, 0),
            (255, 255, 100),
            (100, 255, 100),
            (100, 100, 255),
        ]
        
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (brick_w + spacing)
                y = start_y + row * (brick_h + spacing)
                
                brick_col = Collider2D(f"Brick_{row}_{col}", 
                    -brick_w/2, -brick_h/2, brick_w, brick_h)
                brick_col.layer = "brick"
                brick_col.mask = {"ball"}
                
                brick = RectangleNode(f"Brick_{row}_{col}", 
                    x, y, brick_w, brick_h, colors[row])
                brick.add_child(brick_col)
                self.game.add_child(brick)
                self.bricks.append(brick)
                
    def create_walls(self):
        left_col = Collider2D("Left_Wall", -10, 0, 10, 600)
        left_col.layer = "wall"
        left_col.mask = {"ball"}
        left_wall = RectangleNode("LeftWall", 0, 300, 10, 600, (100, 100, 100))
        left_wall.add_child(left_col)
        self.game.add_child(left_wall)
        
        right_col = Collider2D("Right_Wall", 0, 0, 10, 600)
        right_col.layer = "wall"
        right_col.mask = {"ball"}
        right_wall = RectangleNode("RightWall", 800, 300, 10, 600, (100, 100, 100))
        right_wall.add_child(right_col)
        self.game.add_child(right_wall)
        
        top_col = Collider2D("Top_Wall", 0, -10, 800, 10)
        top_col.layer = "wall"
        top_col.mask = {"ball"}
        top_wall = RectangleNode("TopWall", 400, 0, 800, 10, (100, 100, 100))
        top_wall.add_child(top_col)
        self.game.add_child(top_wall)
        
    def update(self, dt):
        if self.game_over or self.victory:
            return
            
        input_system = self.engine.input
        if input_system.is_key_pressed(Keys.LEFT):
            self.paddle.set_position(self.paddle.local_x - self.paddle_speed * dt, self.paddle.local_y)
        if input_system.is_key_pressed(Keys.RIGHT):
            self.paddle.set_position(self.paddle.local_x + self.paddle_speed * dt, self.paddle.local_y)
            
        self.paddle.set_position(max(60, min(740, self.paddle.local_x)), self.paddle.local_y)
        
        self.ball.set_position(self.ball.local_x + self.ball_dx * dt, self.ball.local_y + self.ball_dy * dt)
        
        paddle_col = self.paddle.get_node("Paddle_Col")
        ball_col = self.ball.get_node("Ball_Col")
        
        if paddle_col and ball_col:
            if self.check_collision(ball_col, paddle_col):
                self.ball_dy = abs(self.ball_dy)
                offset = (self.ball.local_x - self.paddle.local_x) / 60
                self.ball_dx = offset * 200 + self.ball_dx * 0.5
                speed = math.sqrt(self.ball_dx**2 + self.ball_dy**2)
                self.ball_dx = (self.ball_dx / speed) * self.ball_speed
                self.ball_dy = (self.ball_dy / speed) * self.ball_speed
                self.ball.set_position(self.ball.local_x, self.paddle.local_y - 25)
                
        if self.ball.local_x <= 15 or self.ball.local_x >= 785:
            self.ball_dx = -self.ball_dx
            self.ball.set_position(max(15, min(785, self.ball.local_x)), self.ball.local_y)
            
        if self.ball.local_y <= 15:
            self.ball_dy = -self.ball_dy
            self.ball.set_position(self.ball.local_x, 15)
            
        if self.ball.local_y > 620:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            else:
                self.ball.set_position(400, 500)
                self.ball_dx = math.cos(math.pi / 4) * self.ball_speed
                self.ball_dy = -math.sin(math.pi / 4) * self.ball_speed
                
        for brick in self.bricks[:]:
            brick_col = brick.get_node(brick.name + "_Col")
            if brick_col and self.check_collision(ball_col, brick_col):
                brick.queue_free()
                self.bricks.remove(brick)
                self.score += 10
                self.ball_dy = -self.ball_dy
                break
                
        if len(self.bricks) == 0:
            self.victory = True
            
        self.hud.extra_text = f"Score: {self.score}  Lives: {self.lives}"
        
    def check_collision(self, col1, col2):
        pos1 = col1.get_global_position() if hasattr(col1, 'get_global_position') else (col1.local_x, col1.local_y)
        pos2 = col2.get_global_position() if hasattr(col2, 'get_global_position') else (col2.local_x, col2.local_y)
        
        return (abs(pos1[0] - pos2[0]) < (col1.width + col2.width) / 2 and
                abs(pos1[1] - pos2[1]) < (col1.height + col2.height) / 2)

    def run(self):
        while self.engine.running:
            dt = self.engine.begin_frame()
            
            self.root.update_transforms()
            self.root.update(dt)
            
            if self.engine.input.is_key_pressed(Keys.ESCAPE):
                self.engine.running = False
                
            self.engine.end_frame()
            
        self.engine.quit()


def main():
    game = Breakout()
    game.run()


if __name__ == "__main__":
    main()