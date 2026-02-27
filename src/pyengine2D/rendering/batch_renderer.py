"""
Batch Renderer — accumulates blit operations and flushes them in one pass.

SpriteBatch sorts by source surface id so that Pygame's internal state
switches are minimised.  DirtyRectTracker records changed pixel regions
for optional partial-display updates.
"""
import pygame


class SpriteBatch:
    """
    Accumulate (source_surface, src_rect_or_None, dest_pos) items per frame,
    then flush them all at once, sorted by source surface to minimise context
    switches.

    Usage:
        batch = SpriteBatch()
        batch.add(player_img, None, (100, 200))
        batch.add(atlas.surface, src_rect, (300, 50))
        batch.flush(game_surface)
    """

    def __init__(self):
        self._items = []          # list of (src_surface, src_rect, dest)

    def add(self, source_surface, src_rect, dest_pos):
        """Queue a blit operation."""
        self._items.append((source_surface, src_rect, dest_pos))

    def flush(self, target, clear_color=None):
        """
        Issue all queued blits on *target*, sorted by source surface.
        Optionally fills *target* with *clear_color* first.
        """
        if clear_color is not None:
            target.fill(clear_color)

        # Sort by id of the source surface so blits from the same sheet
        # are consecutive (may improve cache locality).
        self._items.sort(key=lambda item: id(item[0]))

        for src_surface, src_rect, dest in self._items:
            if src_rect is not None:
                target.blit(src_surface, dest, area=src_rect)
            else:
                target.blit(src_surface, dest)

        self._items.clear()

    @property
    def pending_count(self):
        return len(self._items)

    def clear(self):
        self._items.clear()


class DirtyRectTracker:
    """
    Tracks changed rectangular regions per frame for partial display updates.

    Usage:
        tracker = DirtyRectTracker()
        tracker.mark_dirty(pygame.Rect(100, 100, 64, 64))
        ...
        pygame.display.update(tracker.get_dirty_rects())
        tracker.clear()
    """

    def __init__(self):
        self._rects = []

    def mark_dirty(self, rect):
        """Record a dirty region (pygame.Rect or (x, y, w, h) tuple)."""
        if isinstance(rect, tuple):
            rect = pygame.Rect(*rect)
        self._rects.append(rect)

    def get_dirty_rects(self):
        """Return list of dirty rects for this frame."""
        return self._rects

    def clear(self):
        self._rects.clear()
