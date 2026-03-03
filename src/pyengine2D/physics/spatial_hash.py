class SpatialHash:
    """Broadphase collision grid that updates incrementally."""
    def __init__(self, cell_size=128):
        self.cell_size = cell_size
        self.grid = {}
        self.body_cells = {}

    def register(self, node):
        """Register or update a node's position in the grid."""
        gx, gy = node.get_global_position()
        cell = (int(gx // self.cell_size), int(gy // self.cell_size))
        
        old_cell = self.body_cells.get(node)
        if old_cell == cell:
            return
            
        # Remove from old cell
        if old_cell and old_cell in self.grid:
            if node in self.grid[old_cell]:
                self.grid[old_cell].remove(node)
                
        # Add to new cell
        if cell not in self.grid:
            self.grid[cell] = []
        self.grid[cell].append(node)
        self.body_cells[node] = cell

    def remove(self, node):
        old_cell = self.body_cells.get(node)
        if old_cell and old_cell in self.grid:
            if node in self.grid[old_cell]:
                self.grid[old_cell].remove(node)
        if node in self.body_cells:
            del self.body_cells[node]

    def query_nearby(self, node):
        """Returns all other nodes in the same or adjacent 8 cells."""
        cell = self.body_cells.get(node)
        if not cell:
            return []
            
        cx, cy = cell
        results = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                c = (cx + dx, cy + dy)
                if c in self.grid:
                    for other in self.grid[c]:
                        if other is not node:
                            results.append(other)
        return results
