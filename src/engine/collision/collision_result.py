from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine.collision.collider2d import Collider2D


@dataclass
class CollisionResult:
    """
    Structured result from a collision check.
    
    Attributes:
        collided:    True if an overlap was detected.
        collider:    The Collider2D that was hit (None if no collision).
        normal_x:    X component of the collision normal (-1, 0, or 1).
        normal_y:    Y component of the collision normal (-1, 0, or 1).
        penetration: Overlap depth along the normal axis.
    """
    collided: bool
    collider: Optional['Collider2D']
    normal_x: float
    normal_y: float
    penetration: float

    @staticmethod
    def none() -> 'CollisionResult':
        """Factory for a no-collision result."""
        return CollisionResult(
            collided=False,
            collider=None,
            normal_x=0.0,
            normal_y=0.0,
            penetration=0.0,
        )
