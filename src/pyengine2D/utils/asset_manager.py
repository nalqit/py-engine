"""
AssetManager — load-on-demand asset cache with LRU eviction.

All image/sound loading should go through this singleton to avoid
duplicate loads and enable automatic memory management.
"""
import time
import pygame


class _AssetEntry:
    """Internal wrapper storing an asset with usage metadata."""
    __slots__ = ('asset', 'last_access', 'byte_size', 'ref_count')

    def __init__(self, asset, byte_size):
        self.asset = asset
        self.last_access = time.monotonic()
        self.byte_size = byte_size
        self.ref_count = 0

    def touch(self):
        self.last_access = time.monotonic()
        self.ref_count += 1


class AssetManager:
    """
    Centralised asset cache with load-on-demand and LRU eviction.

    Usage:
        mgr = AssetManager.instance()       # singleton
        img = mgr.load_image("player.png")   # loads once, cached
        mgr.unload("player.png")             # manual eviction
        mgr.unload_unused(max_age_s=30)      # evict assets not used for 30 s

    The manager is single-threaded (Pygame requirement).
    """
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the singleton (useful for tests)."""
        cls._instance = None

    def __init__(self, max_cache_bytes=256 * 1024 * 1024):
        self._cache = {}                   # path -> _AssetEntry
        self._max_cache_bytes = max_cache_bytes
        self._current_bytes = 0

    # ------------------------------------------------------------------ images
    def load_image(self, path, convert_alpha=True):
        """Load (or retrieve cached) image surface."""
        if path in self._cache:
            entry = self._cache[path]
            entry.touch()
            return entry.asset

        surface = pygame.image.load(path)
        if convert_alpha:
            surface = surface.convert_alpha()
        else:
            surface = surface.convert()

        byte_size = surface.get_width() * surface.get_height() * surface.get_bytesize()
        self._store(path, surface, byte_size)
        return surface

    # ------------------------------------------------------------------ sounds
    def load_sound(self, path):
        """Load (or retrieve cached) sound."""
        if path in self._cache:
            entry = self._cache[path]
            entry.touch()
            return entry.asset

        sound = pygame.mixer.Sound(path)
        byte_size = sound.get_length() * 44100 * 2  # rough estimate
        self._store(path, sound, int(byte_size))
        return sound

    # ---------------------------------------------------------------- eviction
    def unload(self, path):
        """Remove a specific asset from the cache."""
        entry = self._cache.pop(path, None)
        if entry:
            self._current_bytes -= entry.byte_size

    def unload_unused(self, max_age_s=60.0):
        """Evict all assets not accessed for *max_age_s* seconds."""
        now = time.monotonic()
        to_remove = [
            p for p, e in self._cache.items()
            if (now - e.last_access) > max_age_s
        ]
        for p in to_remove:
            self.unload(p)

    def clear(self):
        """Evict everything."""
        self._cache.clear()
        self._current_bytes = 0

    # --------------------------------------------------------------- internal
    def _store(self, path, asset, byte_size):
        # Evict oldest entries if over budget
        while self._current_bytes + byte_size > self._max_cache_bytes and self._cache:
            oldest_path = min(self._cache, key=lambda p: self._cache[p].last_access)
            self.unload(oldest_path)

        entry = _AssetEntry(asset, byte_size)
        entry.touch()
        self._cache[path] = entry
        self._current_bytes += byte_size

    # --------------------------------------------------------------- stats
    def stats(self):
        return {
            'cached_count': len(self._cache),
            'current_bytes': self._current_bytes,
            'max_cache_bytes': self._max_cache_bytes,
        }
