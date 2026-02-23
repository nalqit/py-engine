from src.engine.core.engine import Engine
from src.engine.core.input import Keys
from src.engine.scene.node2d import Node2D
from src.engine.scene.camera2d import Camera2D
from src.engine.scene.rectangle_node import RectangleNode
from src.engine.collision.collider2d import Collider2D
from src.engine.collision.collision_world import CollisionWorld
from src.engine.physics.physics_body_2d import PhysicsBody2D
from src.engine.fsm.state_machine import StateMachine
from src.engine.fsm.state import State
from src.engine.utils.profiler import EngineProfiler

VIRTUAL_W, VIRTUAL_H = 800, 600
TILE_SIZE = 32

MAP = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X                               X",
    "X                               X",
    "X       XXXXX                   X",
    "X                               X",
    "X             XXX               X",
    "X    XX                         X",
    "X           XXXX       XX       X",
    "X                               X",
    "X  XXXX                         X",
    "X                               X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
]


class PlatformerPlayer(PhysicsBody2D):
    def __init__(self, name, x, y, collider, collision_world):
        super().__init__(name, x, y, collider, collision_world)
        self.use_gravity = True
        self.gravity = 1200.0
        self.movespeed = 250.0
        self.jumpforce = 450.0
        self.coyote_timer = 0.0
        self.coyote_time_max = 0.1
        self.jump_buffer = 0.0
        self.jump_buffer_max = 0.1
        self.fsm = StateMachine(self)
        self.is_grounded = False
        self.was_jump_pressed = False
        self.initial_y = None
        self.resting = False

    def update(self, delta):
        inp = Engine.instance.input
        probe = self.collision_world.check_collision(self.collider, self.local_x, self.local_y + 1.0)
        self.is_grounded = probe.collided and probe.normal_y < 0

        if self.is_grounded:
            self.coyote_timer = self.coyote_time_max
            if abs(self.velocity_x) < 1.0 and self.velocity_y == 0:
                if self.initial_y is None:
                    self.initial_y = self.local_y
                self.resting = True
            else:
                self.resting = False
        else:
            self.coyote_timer -= delta
            self.resting = False

        jump_wants = inp.is_key_pressed(Keys.SPACE) or inp.is_key_pressed(Keys.W)
        if jump_wants and not self.was_jump_pressed:
            self.jump_buffer = self.jump_buffer_max
        elif not jump_wants:
            self.jump_buffer -= delta
        self.was_jump_pressed = jump_wants

        if self.jump_buffer > 0 and self.coyote_timer > 0:
            self.velocity_y = -self.jumpforce
            self.jump_buffer = 0.0
            self.coyote_timer = 0.0
            self.is_grounded = False

        if not jump_wants and self.velocity_y < 0:
            self.velocity_y *= 0.5

        move_dir = 0
        if inp.is_key_pressed(Keys.LEFT) or inp.is_key_pressed(Keys.A):
            move_dir -= 1
        if inp.is_key_pressed(Keys.RIGHT) or inp.is_key_pressed(Keys.D):
            move_dir += 1
        target_vx = move_dir * self.movespeed
        accel = 20.0 if self.is_grounded else 10.0
        self.velocity_x += (target_vx - self.velocity_x) * accel * delta
        super().update(delta)
        self.fsm.update(delta)


class IdleState(State):
    def update(self, delta):
        if abs(self.body.velocity_x) > 10:
            self.body.fsm.change_state(RunState(self.body))
        elif not self.body.is_grounded:
            self.body.fsm.change_state(FallState(self.body))


class RunState(State):
    def update(self, delta):
        if abs(self.body.velocity_x) <= 10:
            self.body.fsm.change_state(IdleState(self.body))
        elif not self.body.is_grounded:
            self.body.fsm.change_state(FallState(self.body))


class FallState(State):
    def update(self, delta):
        if self.body.is_grounded:
            self.body.fsm.change_state(IdleState(self.body))


def build_tilemap(visual_world):
    for y, row in enumerate(MAP):
        for x, char in enumerate(row):
            if char == 'X':
                px, py = x * TILE_SIZE, y * TILE_SIZE
                name = f"Wall_{x}_{y}"
                wall = Node2D(name, px, py)
                col = Collider2D(name + "Col", 0, 0, TILE_SIZE, TILE_SIZE, is_static=True)
                col.layer = "wall"
                col.mask = {"player"}
                wall.add_child(col)
                wall.add_child(RectangleNode(name + "Vis", 0, 0, TILE_SIZE, TILE_SIZE, (60, 60, 80)))
                visual_world.add_child(wall)


def main():
    engine = Engine("Level 2: Precision Platformer (Float Drift & FSM)", VIRTUAL_W, VIRTUAL_H)
    profiler = EngineProfiler()
    r = engine.renderer
    surface = engine.game_surface

    root = Node2D("Root")
    visual_world = Node2D("VisualWorld")
    root.add_child(visual_world)
    collision_world = CollisionWorld("CollisionWorld")
    root.add_child(collision_world)

    build_tilemap(visual_world)

    player_col = Collider2D("PlayerCol", 0, 0, 24, 30)
    player_col.layer = "player"
    player_col.mask = {"wall"}
    player = PlatformerPlayer("Player", 64, 64, player_col, collision_world)
    player.fsm.change_state(FallState(player))
    visual_world.add_child(player)
    player.add_child(player_col)
    vis = RectangleNode("PlayerVis", 0, 0, 24, 30, (50, 200, 200))
    player.add_child(vis)

    camera = Camera2D("Camera")
    camera.follow(player)
    root.add_child(camera)
    Node2D.camera = camera

    marathon_timer = 0.0
    accumulator = 0.0

    while engine.running:
        dt = engine.begin_frame()
        profiler.log_frame(dt)
        accumulator += dt

        profiler.begin("Logic")
        while accumulator >= engine.fixed_dt:
            marathon_timer += engine.fixed_dt
            if marathon_timer >= 60.0:
                marathon_timer = 0.0
                if player.resting and player.initial_y is not None:
                    drift = player.local_y - player.initial_y
                    print(f"[MARATHON] Resting Float Drift over 60s: {drift:.6f} pixels")
                    if abs(drift) > 0.1:
                        print("WARNING: High float drift detected!")
            root.update_transforms()
            root.update(engine.fixed_dt)
            accumulator -= engine.fixed_dt
        profiler.end("Logic")

        profiler.begin("Render")
        r.fill(surface, (30, 40, 50))
        root.render(surface)

        state_name = player.fsm.current_state.__class__.__name__ if player.fsm.current_state else 'None'
        if isinstance(player.fsm.current_state, IdleState):
            vis.color = (50, 200, 50)
        elif isinstance(player.fsm.current_state, RunState):
            vis.color = (200, 200, 50)
        elif isinstance(player.fsm.current_state, FallState):
            vis.color = (200, 50, 50)

        hud = [
            f"FPS: {engine.fps:.1f}", f"State: {state_name}",
            f"Drift Base Y: {player.initial_y if player.initial_y else 'Wait'}",
            f"Resting?: {player.resting}"
        ]
        y = 10
        for line in hud:
            r.blit(surface, r.render_text_uncached(line, (255, 255, 255)), (10, y))
            y += 20
        profiler.end("Render")

        engine.end_frame()

    profiler.print_summary()
    engine.quit()


if __name__ == "__main__":
    main()
