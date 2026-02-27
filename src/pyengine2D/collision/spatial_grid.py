"""
UniformGrid — spatial partitioning for O(n·k) broad-phase collision.

Each frame the grid is cleared and all colliders are re-inserted.
Queries return only colliders whose cells overlap the query AABB,
dramatically reducing pair-checks compared to the previous O(n²) approach.
"""


class UniformGrid:
    """
    Fixed-cell-size spatial hash for 2-D AABBs.

    Usage:
        grid = UniformGrid(cell_size=128)
        grid.insert(collider, left, top, right, bottom)
        candidates = grid.query(test_l, test_t, test_r, test_b)
        grid.clear()

    Cell coordinates are computed as ``int(coord // cell_size)`` so
    negative world positions work correctly.
    """

    def __init__(self, cell_size=128):
        self.cell_size = cell_size
        self._cells = {}  # (cx, cy) -> set of colliders

    # ---------------------------------------------------------------- insert
    def insert(self, collider, left, top, right, bottom):
        """Insert *collider* into every cell its AABB overlaps."""
        cs = self.cell_size
        min_cx = int(left // cs) if left >= 0 else int(left // cs)
        max_cx = int(right // cs) if right >= 0 else int(right // cs)
        min_cy = int(top // cs) if top >= 0 else int(top // cs)
        max_cy = int(bottom // cs) if bottom >= 0 else int(bottom // cs)

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                key = (cx, cy)
                bucket = self._cells.get(key)
                if bucket is None:
                    bucket = set()
                    self._cells[key] = bucket
                bucket.add(collider)

    # ----------------------------------------------------------------- query
    def query(self, left, top, right, bottom, exclude=None):
        """
        Return a set of colliders whose cells overlap the given AABB.
        *exclude* is an optional collider to omit from the result.
        """
        cs = self.cell_size
        min_cx = int(left // cs)
        max_cx = int(right // cs)
        min_cy = int(top // cs)
        max_cy = int(bottom // cs)

        result = set()
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                bucket = self._cells.get((cx, cy))
                if bucket:
                    result.update(bucket)

        if exclude is not None:
            result.discard(exclude)
        return result

    # ----------------------------------------------------------------- clear
    def clear(self):
        """Remove all entries (call once per frame before re-inserting)."""
        self._cells.clear()

    # ----------------------------------------------------------------- stats
    def stats(self):
        total_entries = sum(len(b) for b in self._cells.values())
        return {
            'cell_count': len(self._cells),
            'total_entries': total_entries,
            'cell_size': self.cell_size,
        }
