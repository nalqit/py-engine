"""
SurfaceCache — caches pre-rendered pygame.Surface objects by key.

Used by TilemapNode to bake static tile layers, and by ParallaxLayer
for static imagery.  Invalidation is explicit (caller calls invalidate()).
"""
import pygame


class SurfaceCache:
    """
    Simple key → pygame.Surface cache with optional max entries.

    Usage:
        cache = SurfaceCache()
        if not cache.has("ground_layer"):
            surf = render_my_ground(...)
            cache.store("ground_layer", surf)
        screen.blit(cache.get("ground_layer"), (0, 0))
    """

    def __init__(self, max_entries=64):
        self._surfaces = {}          # key -> pygame.Surface
        self._max_entries = max_entries

    def has(self, key):
        return key in self._surfaces

    def get(self, key):
        """Returns cached surface or None."""
        return self._surfaces.get(key)

    def store(self, key, surface):
        """Store a surface under *key*, evicting oldest entry if at capacity."""
        if len(self._surfaces) >= self._max_entries and key not in self._surfaces:
            oldest = next(iter(self._surfaces))
            del self._surfaces[oldest]
        self._surfaces[key] = surface

    def invalidate(self, key=None):
        """Remove one key, or all keys if key is None."""
        if key is None:
            self._surfaces.clear()
        else:
            self._surfaces.pop(key, None)

    def stats(self):
        return {
            'count': len(self._surfaces),
            'max_entries': self._max_entries,
        }
