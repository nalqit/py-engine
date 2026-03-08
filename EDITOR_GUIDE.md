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
│  📄 New  📂 Open  💾 Save  │  ➕ Add  🗑 Del  │ ↩↪ │
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
- **Right-click** context menu:
  - **Add Child** → sub-menu with Node2D, SpriteNode, Camera2D, RectangleNode, CircleNode
  - **Delete** → remove the selected node (undoable)
  - **Rename** → change the node name (undoable)

### Scene Viewport (Center)

- Visual representation of the scene in 2D space.
- Dark background with grid overlay and world axes (red = X, green = Y).
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

| Button      | Shortcut | Action                           |
| ----------- | -------- | -------------------------------- |
| 📄 New      | Ctrl+N   | Create a new empty scene         |
| 📂 Open     | Ctrl+O   | Open a `.scene` file             |
| 💾 Save     | Ctrl+S   | Save the current scene           |
| ➕ Add Node | —        | Add a child to the selected node |
| 🗑 Delete   | Delete   | Delete the selected node         |
| ↩ Undo      | Ctrl+Z   | Undo last action                 |
| ↪ Redo      | Ctrl+Y   | Redo last undone action          |
| # Grid      | —        | Toggle grid overlay              |

---

## Node Types

| Type              | Description       | Key Properties                             |
| ----------------- | ----------------- | ------------------------------------------ |
| **Node2D**        | Base 2D node      | Position, Scale, Rotation                  |
| **SpriteNode**    | Static image      | Image path, Centered                       |
| **Camera2D**      | Viewport camera   | Position (follow target only at runtime)   |
| **RectangleNode** | Colored rectangle | Width, Height, Color                       |
| **CircleNode**    | Colored circle    | Radius, Color                              |
| **TilemapNode**   | Tile-based map    | Loaded from map data (read-only in editor) |

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
      "type": "SpriteNode",
      "name": "Player",
      "x": 100, "y": 200,
      "image_path": "assets/player.png",
      "centered": true,
      ...
    }
  ]
}
```

---

## Undo / Redo

All editor operations are fully reversible:

- Add Node → undo removes it
- Delete Node → undo restores it (at original position)
- Move Node → undo reverts position
- Property Change → undo reverts value
- Rename → undo reverts name

The undo stack supports up to 200 operations.

---

## Architecture

```
tools/editor/
├── editor.py           # Entry point + QMainWindow
├── editor_model.py     # Central state + undo/redo (Command pattern)
├── viewport_widget.py  # Pygame-in-Qt viewport (QImage bridge)
├── scene_tree_panel.py # Hierarchical tree panel (QDockWidget)
├── inspector_panel.py  # Property inspector (QDockWidget)
├── toolbar.py          # Toolbar actions
├── scene_io.py         # Scene serialization (.scene JSON)
└── __init__.py
```

**Key design principles:**

- **Zero engine modifications** — all editor code lives under `tools/editor/`
- **Thread-safe** — all mutations run on the Qt main thread via `push_command()`
- **QTimer singleShot chaining** — viewport render never overlaps
- **Observer pattern** — model emits callbacks, panels subscribe

---

## Known Limitations

1. **SpriteNode texture preview** — the viewport shows placeholder rectangles instead of actual textures (Pygame runs with SDL dummy driver in the editor).
2. **TilemapNode** — displayed as a placeholder in the editor. Full tilemap rendering requires the engine runtime.
3. **Multi-select** — not yet implemented (single selection only).
4. **Rotation/Scale handles** — not yet implemented as interactive gizmos. Use the Inspector fields.
5. **Plugin system** — planned but not yet available.

---

## Testing

```bash
# Run editor tests (headless, no display needed)
python -m pytest tests/test_editor_model.py tests/test_scene_io.py -v

# Run ALL tests including engine tests (to verify no regressions)
python -m pytest tests/ -v
```
