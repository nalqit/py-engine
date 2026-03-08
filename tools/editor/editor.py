"""
editor.py — PyEngine2D Editor Entry Point

Standalone 2D scene editor similar to Godot's 2D editor.
Does NOT modify any engine core code.

Usage:
    python tools/editor/editor.py

Layout:
    ┌──────────────────────────────────────────────────────┐
    │                    Toolbar (Top)                      │
    ├──────────┬──────────────────────────┬────────────────┤
    │ Scene    │    Scene Viewport        │   Inspector    │
    │ Tree     │    (Center)              │   Panel        │
    │ (Left)   │    Pan/Zoom/Select/Drag  │   (Right)      │
    │          │                          │                │
    └──────────┴──────────────────────────┴────────────────┘
"""

import os
import sys

# ── Ensure project root is on sys.path ──
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStyleFactory,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

from tools.editor.editor_model import EditorModel
from tools.editor.viewport_widget import ViewportWidget
from tools.editor.scene_tree_panel import SceneTreePanel
from tools.editor.inspector_panel import InspectorPanel
from tools.editor.toolbar import EditorToolbar


# ═══════════════════════════════════════════════════════════════════════════
#  Dark palette
# ═══════════════════════════════════════════════════════════════════════════

def _apply_dark_palette(app: QApplication):
    """Apply a modern dark palette to the entire application."""
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()

    # Base colours
    bg        = QColor(35, 35, 42)
    bg_alt    = QColor(42, 42, 52)
    fg        = QColor(220, 220, 225)
    accent    = QColor(79, 195, 247)    # light-blue accent
    disabled  = QColor(120, 120, 130)
    highlight = QColor(79, 195, 247, 80)

    palette.setColor(QPalette.Window,          bg)
    palette.setColor(QPalette.WindowText,      fg)
    palette.setColor(QPalette.Base,            bg_alt)
    palette.setColor(QPalette.AlternateBase,   bg)
    palette.setColor(QPalette.ToolTipBase,     bg)
    palette.setColor(QPalette.ToolTipText,     fg)
    palette.setColor(QPalette.Text,            fg)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled)
    palette.setColor(QPalette.Button,          bg_alt)
    palette.setColor(QPalette.ButtonText,      fg)
    palette.setColor(QPalette.BrightText,      accent)
    palette.setColor(QPalette.Link,            accent)
    palette.setColor(QPalette.Highlight,       accent)
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)

    app.setPalette(palette)

    app.setStyleSheet("""
        QDockWidget {
            titlebar-close-icon: none;
            font-weight: bold;
            color: #4FC3F7;
        }
        QDockWidget::title {
            background: #2a2a34;
            padding: 6px;
            border-bottom: 1px solid #444;
        }
        QTreeWidget {
            background: #23232a;
            border: none;
            outline: none;
        }
        QTreeWidget::item {
            padding: 4px 2px;
        }
        QTreeWidget::item:selected {
            background: #4FC3F7;
            color: #111;
        }
        QTreeWidget::item:hover {
            background: #3a3a48;
        }
        QGroupBox {
            border: 1px solid #444;
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            color: #4FC3F7;
        }
        QDoubleSpinBox, QSpinBox, QLineEdit {
            background: #2a2a34;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 3px;
            color: #ddd;
        }
        QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {
            border-color: #4FC3F7;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        QScrollBar:vertical {
            background: #23232a;
            width: 10px;
        }
        QScrollBar::handle:vertical {
            background: #555;
            border-radius: 5px;
            min-height: 20px;
        }
        QMenuBar {
            background: #2b2b33;
            color: #ddd;
        }
        QMenu {
            background: #2b2b33;
            color: #ddd;
            border: 1px solid #444;
        }
        QMenu::item:selected {
            background: #4FC3F7;
            color: #111;
        }
        QStatusBar {
            background: #2a2a34;
            color: #888;
        }
    """)


# ═══════════════════════════════════════════════════════════════════════════
#  Main Window
# ═══════════════════════════════════════════════════════════════════════════

class EditorMainWindow(QMainWindow):
    """PyEngine2D Editor main window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyEngine2D Editor")
        self.setMinimumSize(1200, 700)
        self.resize(1440, 860)

        # ── Central model ──
        self.model = EditorModel()

        # ── Viewport (center) ──
        self.viewport = ViewportWidget(self.model, self)
        self.setCentralWidget(self.viewport)

        # ── Scene Tree (left dock) ──
        self.scene_tree = SceneTreePanel(self.model, self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.scene_tree)

        # ── Inspector (right dock) ──
        self.inspector = InspectorPanel(self.model, self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector)

        # ── Toolbar (top) ──
        self.toolbar = EditorToolbar(self.model, self)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.toolbar.grid_toggled.connect(self.viewport.toggle_grid)

        # ── Status bar ──
        self.statusBar().showMessage("Ready — PyEngine2D Editor")

        # ── Update title on model changes ──
        self.model.on_scene_changed(self._update_title)

    def _update_title(self):
        dirty = "• " if self.model.is_dirty else ""
        name = os.path.basename(self.model.scene_path) if self.model.scene_path else "Untitled"
        self.setWindowTitle(f"{dirty}{name} — PyEngine2D Editor")


# ═══════════════════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    _apply_dark_palette(app)

    window = EditorMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
