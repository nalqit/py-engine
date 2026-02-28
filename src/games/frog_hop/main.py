"""
Frog Hop — Main entry point.
A side-scrolling platformer where Ninja Frog collects fruits across
multiple levels with increasing difficulty and traps.

Level geometry is loaded from src/games/frog_hop/maps/ via TilemapNode.
Collecting all fruits in a level advances the player to the next one.
"""
from src.pyengine2D import (
    Engine, Node2D, CollisionWorld, Collider2D, Camera2D, StatsHUD, Keys
)
from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class FrogHop:
    def __init__(self):
        self.engine = Engine("Frog Hop", 800, 600)

        self.root = Node2D("Root")

        # Collision system
        self.collision_world = CollisionWorld("CollisionWorld")
        self.root.add_child(self.collision_world)

        # World container — rebuilt for each level
        self.world = Node2D("World")
        self.root.add_child(self.world)

        # Level tracking
        from .level import LEVELS
        self.total_levels = len(LEVELS)
        self.current_level = 0
        self.state = GameState.PLAYING

        # Player — created once, reused across levels
        from .entities.player import Player
        player_col = Collider2D("Player_Col", -23, -22, 45, 50)
        player_col.layer = "player"
        player_col.mask = {"wall", "pickup"}
        player_col.visible = True

        self.player = Player("Player", 50, 400, player_col, self.collision_world)
        self.player.add_child(player_col)

        # Camera
        self.camera = Camera2D("Camera")
        self.camera.follow(self.player)
        self.root.add_child(self.camera)
        Node2D.camera = self.camera

        # HUD
        self.hud = StatsHUD("HUD")
        self.root.add_child(self.hud)

        # Pipe signals — use **kw to safely absorb any extra kwargs from emit
        self.player.get_signal("on_score_changed").connect(
            lambda **kw: setattr(self.hud, '_custom_score', kw.get('score', 0))
        )
        self.player.get_signal("on_lives_changed").connect(
            lambda **kw: setattr(self.hud, '_custom_lives', kw.get('lives', 0))
        )
        self.player.get_signal("on_health_changed").connect(
            lambda **kw: setattr(self.hud, '_custom_health', kw.get('health', 0))
        )
        self.player.get_signal("on_died").connect(
            lambda *a, **kw: self._on_player_died()
        )

        # Load the first level
        self.fruits = []
        self.traps = []
        self._level_complete = False
        self._load_level(self.current_level)

    # ── level management ────────────────────────────────────────────

    def _load_level(self, index):
        """Tear down the old world and build a new one for *index*."""
        # Remove old world node and recreate
        if self.world in self.root.children:
            self.root.remove_child(self.world)
        # Also remove player from old world if present
        if self.player.parent:
            self.player.parent.remove_child(self.player)

        self.world = Node2D("World")
        self.root.add_child(self.world)

        from .level import build_level
        self.fruits, self.traps, player_start = build_level(
            self.world, self.collision_world, index
        )

        # Position player at level start
        self.player.local_x, self.player.local_y = player_start
        self.player.spawn_point = player_start
        self.player.velocity_x = 0
        self.player.velocity_y = 0
        self.world.add_child(self.player)

        # Wire fruit signals
        for fruit in self.fruits:
            fruit.get_signal("on_collected").connect(
                lambda *a, f=fruit, **kw: self.player.collect_fruit(10)
            )

        self._level_complete = False

    # ── per-frame hooks ─────────────────────────────────────────────

    def update(self, engine, root, dt):
        if self.state == GameState.PLAYING:
            self._update_playing(engine, root, dt)
        elif self.state == GameState.GAME_OVER:
            self._update_game_over(engine, root, dt)
        elif self.state == GameState.VICTORY:
            self._update_victory(engine, root, dt)

    def _update_playing(self, engine, root, dt):
        score = getattr(self.hud, '_custom_score', self.player.score)
        lives = getattr(self.hud, '_custom_lives', self.player.lives)
        health = getattr(self.hud, '_custom_health', getattr(self.player, 'health', 3))
        level_label = f"Level {self.current_level + 1}/{self.total_levels}"
        self.hud.extra_text = f"{level_label}  |  Score: {score}  |  Lives: {lives}  |  Health: {health}"

        # Check if all fruits collected → advance level
        if not self._level_complete and all(f.collected for f in self.fruits):
            self._level_complete = True
            self.current_level += 1
            if self.current_level < self.total_levels:
                self._load_level(self.current_level)
            else:
                self.state = GameState.VICTORY

    def _update_game_over(self, engine, root, dt):
        self.hud.extra_text = "GAME OVER! Press R to Restart."
        if engine.input.is_key_just_pressed(Keys.R):
            self._restart_game()

    def _update_victory(self, engine, root, dt):
        self.hud.extra_text = f"YOU WIN!  Final Score: {getattr(self.hud, '_custom_score', self.player.score)}  | Press R to Restart"
        if engine.input.is_key_just_pressed(Keys.R):
            self._restart_game()

    def _on_player_died(self):
        self.state = GameState.GAME_OVER

    def _restart_game(self):
        self.current_level = 0
        self.player.score = 0
        self.player.lives = 3
        self.player.health = self.player.max_health
        setattr(self.hud, '_custom_score', 0)
        setattr(self.hud, '_custom_lives', 3)
        setattr(self.hud, '_custom_health', self.player.max_health)
        self.state = GameState.PLAYING
        self._load_level(self.current_level)

    def render(self, engine, root, surface):
        pass

    def run(self):
        self.engine.run(self.root, on_fixed_update=self.update, on_render=self.render)


def main():
    game = FrogHop()
    # game.root.print_tree()
    game.run()


if __name__ == "__main__":
    main()
