import heapq

class AStarGrid:
    """
    Grid-based A* Pathfinding - Engine Level Utility.
    """
    def __init__(self, width: int, height: int, cell_size: int):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.grid = [[0 for _ in range(height)] for _ in range(width)]
        
    def set_obstacle_world(self, wx, wy, w, h):
        """Marks world coordinates as solid."""
        start_x = max(0, int(wx / self.cell_size))
        start_y = max(0, int(wy / self.cell_size))
        end_x = min(self.width - 1, int((wx + w) / self.cell_size))
        end_y = min(self.height - 1, int((wy + h) / self.cell_size))
        
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                self.grid[x][y] = 1

    def get_path(self, start_world, end_world):
        sx = int(start_world[0] / self.cell_size)
        sy = int(start_world[1] / self.cell_size)
        ex = int(end_world[0] / self.cell_size)
        ey = int(end_world[1] / self.cell_size)
        
        sx = max(0, min(sx, self.width-1))
        sy = max(0, min(sy, self.height-1))
        ex = max(0, min(ex, self.width-1))
        ey = max(0, min(ey, self.height-1))
        
        if self.grid[ex][ey] == 1:
            # Try to find a walkable neighbor for the end goal if it's inside a wall
            found = False
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
                nx, ny = ex + dx, ey + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[nx][ny] == 0:
                    ex, ey = nx, ny
                    found = True
                    break
            if not found:
                return []
                
        open_set = []
        heapq.heappush(open_set, (0, (sx, sy)))
        came_from = {}
        g_score = {(sx, sy): 0}
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == (ex, ey):
                path = []
                while current in came_from:
                    # Return center of the cell
                    path.append((current[0]*self.cell_size + self.cell_size/2.0, 
                                 current[1]*self.cell_size + self.cell_size/2.0))
                    current = came_from[current]
                return path[::-1] # Reverse so path is from start -> end
                
            cx, cy = current
            # 8-way movement
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[nx][ny] == 1: 
                        continue
                    
                    # Prevent cutting corners around walls
                    if dx != 0 and dy != 0:
                        if self.grid[cx+dx][cy] == 1 or self.grid[cx][cy+dy] == 1:
                            continue

                    tentative_g = g_score[current] + (1.414 if dx!=0 and dy!=0 else 1)
                    if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                        came_from[(nx, ny)] = current
                        g_score[(nx, ny)] = tentative_g
                        # Heuristic: Chebyshev + slightly break ties
                        h = max(abs(nx-ex), abs(ny-ey)) * 1.001
                        heapq.heappush(open_set, (tentative_g + h, (nx, ny)))
                        
        return []
