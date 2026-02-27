"""
TextureAtlas — packs multiple images into one large surface.

Uses a simple shelf-packing algorithm.  The atlas minimises blit() call
overhead because all sprites share one source surface.
"""
import pygame


class TextureAtlas:
    """
    Pack many small surfaces into one big surface.

    Usage:
        atlas = TextureAtlas(1024, 1024)
        atlas.add_image("player_idle", player_surf)
        atlas.add_image("coin", coin_surf)

        surf, src_rect = atlas.get("player_idle")
        screen.blit(surf, dest, area=src_rect)
    """

    def __init__(self, width=2048, height=2048, padding=1):
        self._width = width
        self._height = height
        self._padding = padding
        self._surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self._entries = {}       # key -> pygame.Rect (src rect on atlas)
        # Shelf packing state
        self._shelf_y = 0       # current shelf top
        self._shelf_h = 0       # tallest item on current shelf
        self._cursor_x = 0      # next free x on current shelf

    def add_image(self, key, surface):
        """
        Add *surface* under *key*.  Returns (atlas_surface, src_rect).
        Raises RuntimeError if there is no room.
        """
        if key in self._entries:
            return self._surface, self._entries[key]

        w, h = surface.get_size()
        pad = self._padding

        # Advance to next shelf if needed
        if self._cursor_x + w + pad > self._width:
            self._shelf_y += self._shelf_h + pad
            self._shelf_h = 0
            self._cursor_x = 0

        if self._shelf_y + h + pad > self._height:
            raise RuntimeError(
                f"TextureAtlas is full ({self._width}x{self._height}). "
                f"Cannot fit '{key}' ({w}x{h})."
            )

        x = self._cursor_x
        y = self._shelf_y
        self._surface.blit(surface, (x, y))
        rect = pygame.Rect(x, y, w, h)
        self._entries[key] = rect
        self._cursor_x += w + pad
        self._shelf_h = max(self._shelf_h, h)
        return self._surface, rect

    def get(self, key):
        """Returns (atlas_surface, src_rect) or None if key not found."""
        rect = self._entries.get(key)
        if rect is None:
            return None
        return self._surface, rect

    def has(self, key):
        return key in self._entries

    @property
    def surface(self):
        return self._surface

    def stats(self):
        return {
            'entry_count': len(self._entries),
            'atlas_size': (self._width, self._height),
            'used_height': self._shelf_y + self._shelf_h,
        }
