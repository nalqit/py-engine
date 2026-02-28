import sys
import os
import json

sys.path.append(os.path.abspath(r"c:\Users\dell\Desktop\try3(gpt prompts)\src"))
from games.frog_hop.level import LEVELS

s = ""
for idx, cfg in enumerate(LEVELS):
    s += f"\n--- Level {idx+1} ---\n"
    map_path = os.path.join(r"c:\Users\dell\Desktop\try3(gpt prompts)\src\games\frog_hop\maps", cfg["map"])
    
    with open(map_path) as f:
        m = json.load(f)
        
    terrain = [l for l in m["layers"] if l["name"] == "Terrain"][0]
    tiles = terrain["tiles"]
    offset_x = terrain.get("offset_x", 0)
    offset_y = terrain.get("offset_y", 0)

    rows = len(tiles)
    cols = len(tiles[0])
    
    grid = [[" " for _ in range(cols)] for _ in range(rows)]
    for y in range(rows):
        for x in range(cols):
            if tiles[y][x] > 0:
                grid[y][x] = "#"
                
    def put(ch, gx, gy):
        global s
        tx = int(gx // 32) - offset_x
        ty = int(gy // 32) - offset_y
        
        if 0 <= ty < rows and 0 <= tx < cols:
            b = grid[ty][tx]
            if b == "#":
                grid[ty][tx] = f"[{ch}]" # Inside wall!
            else:
                grid[ty][tx] = ch
        else:
            s += f"OUT OF BOUNDS: {ch} at {gx:.0f}, {gy:.0f} (tile {tx}, {ty})\n"

    px, py = cfg.get("player_start", (0,0))
    put("P", px, py)
    
    for f in cfg.get("fruits", []):
        put("F", f[0], f[1])
        
    for t in cfg.get("traps", []):
        put("T", t[1], t[2])

    for y in range(rows):
        row_str = ""
        for x in range(cols):
            cell = grid[y][x]
            if len(cell) > 1:
                row_str += cell
            else:
                row_str += cell
        if any(c != " " for c in row_str):
            s += f"{y:02d}: {row_str}\n"

with open(r"c:\Users\dell\Desktop\try3(gpt prompts)\grid_out.txt", "w", encoding="utf-8") as f:
    f.write(s)
