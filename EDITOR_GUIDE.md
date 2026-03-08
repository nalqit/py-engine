# PyEngine2D Editor Guide

A standalone 2D scene editor for PyEngine2D, inspired by Godot's 2D editor.
Create, edit, and save `.scene` files with a full GUI — without touching the engine core.

---

## Quick Start

```bash
# Install dependency (one-time)
pip install PyQt5

# Launch the editor
cd "path/to/project"
python tools/editor/editor.py
```

---

## Window Layout

```
┌──────────────────────────────────────────────────────┐
│                    Toolbar (Top)                      │
│  New  Open  Save  Import │  + Add  Del  │  Undo Redo │
├──────────┬──────────────────────────┬────────────────┤
│ Scene    │    Scene Viewport        │   Inspector    │
│ Tree     │    (Center)              │   Panel        │
│ (Left)   │    Pan/Zoom/Select/Drag  │   (Right)      │
│          │                          │                │
└──────────┴──────────────────────────┴────────────────┘
```

---

## Panel Descriptions

### Scene Tree (Left)

- Displays all nodes in a hierarchical tree view.
- Clicking a node selects it in all panels.
- Shows `_original_type` for imported game nodes (e.g. "Player" shows with 🎮 icon).
- **Right-click** context menu:
  - **Add Child** → sub-menu with Node2D, SpriteNode, Camera2D, RectangleNode, CircleNode
  - **Delete** → remove the selected node (undoable)
  - **Rename** → change the node name (undoable)

### Scene Viewport (Center)

- Visual representation of the scene in 2D space.
- Dark background with grid overlay and world axes (red = X, green = Y).
- **Node shapes are type-accurate:**
  - `CircleNode` → true circle with actual color
  - `RectangleNode` → filled rect with actual color
  - `SpriteNode` → scaled texture (or pink placeholder if missing)
  - `Camera2D` → gold camera icon
  - `Collider2D` → green outlined rect
  - `TilemapNode` → dashed bounding rect
  - `AnimatedSprite` → purple framed rect
  - Unknown → blue dashed 32×32 rect
- **Scale is applied**: `width × scale_x` and `height × scale_y` are factored into rendered size.
- **Controls:**
  | Action | Input |
  |---|---|
  | **Pan camera** | Middle-click drag |
  | **Zoom** | Scroll wheel |
  | **Move camera** | W/A/S/D keys |
  | **Select node** | Left-click on a node |
  | **Move node** | Left-drag a selected node |
  | **Toggle grid** | G key or toolbar button |
- Selected node is highlighted with an orange outline and corner handles.

### Inspector (Right)

- Shows editable properties for the selected node.
- Properties auto-update the scene in real-time.
- **Common properties** (all Node2D types):
  | Property | Type | Description |
  |---|---|---|
  | Name | String | Node name |
  | X, Y | Float | Local position |
  | Scale X, Scale Y | Float | Scale factors |
  | Rotation | Float | Rotation in degrees |
  | Visible | Bool | Whether the node is rendered |
  | Z Index | Int | Draw order (lower = behind) |
- **SpriteNode extras:** Image Path, Centered
- **RectangleNode extras:** Width, Height
- **CircleNode extras:** Radius

### Toolbar (Top)

| Button     | Shortcut | Action                            |
| ---------- | -------- | --------------------------------- |
| New        | Ctrl+N   | Create a new empty scene          |
| Open       | Ctrl+O   | Open a `.scene` file              |
| Save       | Ctrl+S   | Save the current scene            |
| Import     | Ctrl+I   | Import scene from game `.py` file |
| + Add Node | —        | Add a child to the selected node  |
| Delete     | Delete   | Delete the selected node          |
| Undo       | Ctrl+Z   | Undo last action                  |
| Redo       | Ctrl+Y   | Redo last undone action           |
| # Grid     | —        | Toggle grid overlay               |

---

## Importing from Game Code

Many games build their scene trees in Python code instead of `.scene` files. The editor can import these live scenes.

### How It Works

1. Click **Import** (or Ctrl+I).
2. Select a game's `.py` file (e.g. `src/games/neon_heights/main.py`).
3. The editor:
   - Patches `Engine.run` to a no-op (prevents the game loop from starting).
   - Loads the module and scans for:
     - A `build_scene()` function that returns a `Node`
     - A class with a `self.root` attribute (e.g. `NeonHeights().root`)
     - Module-level `Node` variables
   - Deep-clones the found root tree into the editor model.
4. The scene tree populates with all imported nodes.
5. You can now edit, rearrange, and save as a `.scene` file.

### Safety

- **No game loop execution** — `Engine.run` is replaced with a no-op before import.
- **Deep cloning** — imported nodes are copied by value, not by reference. The original game objects are not mutated.
- **Unknown types** — game subclasses (e.g. `Player`, `RisingVoid`) are imported as `Node2D` with `_original_type` preserved for display.

### Post-Import Validation

After import, a summary dialog shows:

- Total number of imported nodes
- Breakdown by type
- Warnings (e.g. nodes with zero scale)

---

## Node Drawing Reference

The viewport renders each node type with its correct shape:

| Node Type        | Shape                                    | Color          | Scale                                |
| ---------------- | ---------------------------------------- | -------------- | ------------------------------------ |
| `Node2D`         | Small cross + name label                 | Blue           | —                                    |
| `RectangleNode`  | Filled rectangle                         | Node's color   | `width×scale_x`, `height×scale_y`    |
| `CircleNode`     | Filled circle                            | Node's color   | `radius×max(scale_x,scale_y)`        |
| `SpriteNode`     | Scaled texture (or pink ✕ placeholder)   | Texture / pink | `width×scale_x`, `height×scale_y`    |
| `AnimatedSprite` | Framed rectangle with film-strip accents | Purple         | `frame_w×scale_x`, `frame_h×scale_y` |
| `Camera2D`       | Camera body + lens icon                  | Gold           | —                                    |
| `TilemapNode`    | Dashed bounding rectangle                | Green          | —                                    |
| `Collider2D`     | Semi-transparent outlined rectangle      | Green          | `width×scale_x`, `height×scale_y`    |
| Unknown          | Dashed rectangle                         | Blue           | 32×32 default                        |

### Extending the Registry

To add a custom drawer for a new node type:

```python
# In viewport_widget.py
from my_game.custom_node import CustomNode

@register_draw(CustomNode)
def _draw_custom(surf, node, sx, sy, zoom, font):
    # Draw your custom shape
    w = int(node.width * node.scale_x * zoom)
    h = int(node.height * node.scale_y * zoom)
    pygame.draw.rect(surf, (255, 0, 255), (int(sx), int(sy), w, h), 2)
    return w, h
```

---

## Scaling in the Editor

### How Scale Works

- Every node has `scale_x` and `scale_y` (default: 1.0).
- The viewport multiplies pixel dimensions by `scale_x/scale_y` **and** `cam_zoom`.
- Changing scale in the Inspector immediately updates the viewport.
- Scale changes are fully undoable (Ctrl+Z).

### Examples

| Node                        | scale_x | scale_y | Visual Effect                 |
| --------------------------- | ------- | ------- | ----------------------------- |
| `RectangleNode(w=80, h=30)` | 2.0     | 1.0     | 160px × 30px in viewport      |
| `CircleNode(r=20)`          | 3.0     | 3.0     | 60px radius circle            |
| `SpriteNode`                | 0.5     | 0.5     | Texture rendered at half size |

---

## Node Types

| Type               | Description       | Key Properties                             |
| ------------------ | ----------------- | ------------------------------------------ |
| **Node2D**         | Base 2D node      | Position, Scale, Rotation                  |
| **SpriteNode**     | Static image      | Image path, Centered                       |
| **Camera2D**       | Viewport camera   | Position (follow target only at runtime)   |
| **RectangleNode**  | Colored rectangle | Width, Height, Color                       |
| **CircleNode**     | Colored circle    | Radius, Color                              |
| **TilemapNode**    | Tile-based map    | Loaded from map data (read-only in editor) |
| **AnimatedSprite** | Animated frames   | Frame width, Frame height                  |
| **Collider2D**     | Collision shape   | Width, Height, Static flag                 |

---

## Scene File Format (.scene)

`.scene` files are human-readable JSON:

```json
{
  "type": "Node2D",
  "name": "Root",
  "x": 0, "y": 0,
  "scale_x": 1, "scale_y": 1,
  "rotation": 0,
  "visible": true,
  "z_index": 0,
  "children": [
    {
      "type": "Camera2D",
      "name": "MainCamera",
      "x": 400, "y": 300,
      ...
    },
    {
      "type": "RectangleNode",
      "name": "Platform",
      "x": 100, "y": 500,
      "width": 200, "height": 30,
      "color": [100, 200, 50],
      ...
    }
  ]
}
```

Nodes imported from game code include `_original_type` when the actual class differs:

```json
{
  "type": "Node2D",
  "name": "Player",
  "_original_type": "Player",
  "x": 400,
  "y": 500
}
```

---

## Undo / Redo

All editor operations are fully reversible:

- Add Node → undo removes it
- Delete Node → undo restores it (at original position)
- Move Node → undo reverts position
- Property Change → undo reverts value (including scale)
- Rename → undo reverts name

The undo stack supports up to 200 operations.

---

## Architecture

```
tools/editor/
├── editor.py           # Entry point + QMainWindow
├── editor_model.py     # Central state + undo/redo (Command pattern)
├── viewport_widget.py  # Pygame-in-Qt viewport with draw registry
├── scene_tree_panel.py # Hierarchical tree panel (QDockWidget)
├── inspector_panel.py  # Property inspector (QDockWidget)
├── toolbar.py          # Toolbar actions (including Import)
├── scene_io.py         # Scene serialization (.scene JSON)
├── scene_importer.py   # Safe game scene import (deep-clone)
└── __init__.py
```

**Key design principles:**

- **Zero engine modifications** — all editor code lives under `tools/editor/`
- **Thread-safe** — all mutations run on the Qt main thread via `push_command()`
- **QTimer singleShot chaining** — viewport render never overlaps
- **Observer pattern** — model emits callbacks, panels subscribe
- **Draw registry pattern** — each node type has its own drawing function, extensible via `@register_draw`

---

## Known Limitations

1. **SpriteNode texture preview** — works when SDL can find the file; falls back to pink placeholder otherwise.
2. **TilemapNode** — displayed as a dashed bounding box. Full tilemap rendering requires the engine runtime.
3. **Multi-select** — not yet implemented (single selection only).
4. **Rotation/Scale handles** — not yet implemented as interactive gizmos. Use the Inspector fields.
5. **Game import** — only works if the module can be loaded without side-effects beyond `Engine.run`.

---

## Testing

```bash
# Run all editor tests (headless, no display needed)
python -m pytest tests/test_editor_model.py tests/test_scene_io.py tests/test_scene_importer.py -v

# Run ALL tests including engine tests (to verify no regressions)
python -m pytest tests/ -v
```
