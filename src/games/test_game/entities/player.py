"""
PlayerEntity — minimal behavior script for the Player node.

Attached to the "Player" SpriteNode via the scene file.
Demonstrates that per-node game logic can be defined in
standalone Python files and loaded by the engine at runtime.
"""


class PlayerEntity:
    """Behavior component attached to a SpriteNode."""

    def __init__(self, node):
        """
        Args:
            node: The SpriteNode this script is attached to.
                  Provides access to x, y, rotation, etc.
        """
        self.node = node
        self.speed = 100.0  # pixels per second

    def update(self, delta: float) -> None:
        """Called once per frame by the engine.

        Args:
            delta: Time elapsed since the last frame, in seconds.
        """
        self.node.x += self.speed * delta

        # Wrap around when the player moves off the right edge.
        if self.node.x > 850:
            self.node.x = -50
