"""
Frog Hop — Main entry point.
A side-scrolling platformer where Ninja Frog collects fruits across
a hand-crafted tilemap level designed with the draw2d.py map editor.

Level geometry is loaded from src/games/frog_hop/maps/map_data.json
via TilemapNode — no hardcoded platforms.
"""
from src.pyengine2D import (
    Engine, Node2D, CollisionWorld, Collider2D, Camera2D, StatsHUD
)

class FrogHop:
    def __init__(self):
        self.engine = Engine("Frog Hop", 800, 600)

        self.root = Node2D("Root")

        # Collision system
        self.collision_world = CollisionWorld("CollisionWorld")
        self.root.add_child(self.collision_world)

        # World container
        self.world = Node2D("World")
        self.root.add_child(self.world)

        # Build level (background + TilemapNode from maps/map_data.json + fruits)
        from .level import build_level
        self.fruits = build_level(self.world, self.collision_world)

        # Player — AABB collider offset to align with sprite feet
        from .entities.player import Player
        player_col = Collider2D("Player_Col", -23, -22, 45, 50)
        player_col.layer = "player"
        player_col.mask = {"wall", "pickup"}
        player_col.visible = False

        self.player = Player("Player", 50, 400, player_col, self.collision_world)
        self.player.add_child(player_col)
        self.world.add_child(self.player)

        # Wire fruit signals — collecting any fruit gives +10 score
        for fruit in self.fruits:
            fruit.get_signal("on_collected").connect(lambda f=fruit: self.player.collect_fruit(10))

        # Camera follows the player
        self.camera = Camera2D("Camera")
        self.camera.follow(self.player)
        self.root.add_child(self.camera)
        Node2D.camera = self.camera

        # HUD
        self.hud = StatsHUD("HUD")
        self.root.add_child(self.hud)

        # Pipe player score/lives into HUD
        self.player.get_signal("on_score_changed").connect(
            lambda score: setattr(self.hud, '_custom_score', score)
        )
        self.player.get_signal("on_lives_changed").connect(
            lambda lives: setattr(self.hud, '_custom_lives', lives)
        )

    def update(self, engine, root, dt):
        score = getattr(self.hud, '_custom_score', self.player.score)
        lives = getattr(self.hud, '_custom_lives', self.player.lives)
        self.hud.extra_text = f"Score: {score}  |  Lives: {lives}"

    def render(self, engine, root, surface):
        pass

    def run(self):
        self.engine.run(self.root, on_fixed_update=self.update, on_render=self.render)


def main():
    game = FrogHop()
    game.run()


if __name__ == "__main__":
    main()
