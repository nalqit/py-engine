"""
toolbar.py — Editor Toolbar

Provides:
    - New / Open / Save scene
    - Add Node (drop-down: Node2D, SpriteNode, Camera2D, RectangleNode, CircleNode)
    - Delete selected node
    - Undo / Redo
    - Grid toggle
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import (
    QToolBar, QAction, QMenu, QFileDialog, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence

import os, sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.camera2d import Camera2D

if TYPE_CHECKING:
    from tools.editor.editor_model import EditorModel


class EditorToolbar(QToolBar):
    """Main toolbar for the PyEngine2D Editor."""

    grid_toggled = pyqtSignal(bool)

    def __init__(self, model: "EditorModel", parent=None):
        super().__init__("Editor Toolbar", parent)
        self.model = model
        self.setMovable(False)
        self.setStyleSheet("""
            QToolBar {
                spacing: 6px;
                padding: 4px 8px;
                background: #2b2b33;
                border-bottom: 1px solid #444;
            }
            QToolButton {
                background: #3c3c4a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px 12px;
                color: #ddd;
                font-size: 12px;
            }
            QToolButton:hover {
                background: #505068;
                border-color: #4FC3F7;
            }
            QToolButton:pressed {
                background: #4FC3F7;
                color: #222;
            }
        """)

        # ── New Scene ──
        self._act_new = QAction("📄 New", self)
        self._act_new.setShortcut(QKeySequence("Ctrl+N"))
        self._act_new.setToolTip("New Scene (Ctrl+N)")
        self._act_new.triggered.connect(self._on_new)
        self.addAction(self._act_new)

        # ── Open Scene ──
        self._act_open = QAction("📂 Open", self)
        self._act_open.setShortcut(QKeySequence("Ctrl+O"))
        self._act_open.setToolTip("Open Scene (Ctrl+O)")
        self._act_open.triggered.connect(self._on_open)
        self.addAction(self._act_open)

        # ── Save Scene ──
        self._act_save = QAction("💾 Save", self)
        self._act_save.setShortcut(QKeySequence("Ctrl+S"))
        self._act_save.setToolTip("Save Scene (Ctrl+S)")
        self._act_save.triggered.connect(self._on_save)
        self.addAction(self._act_save)

        self.addSeparator()

        # ── Add Node (drop-down) ──
        self._act_add = QAction("➕ Add Node", self)
        self._act_add.setToolTip("Add a child node to the selected node")
        add_menu = QMenu(self)
        for type_name in ["Node2D", "SpriteNode", "Camera2D", "RectangleNode", "CircleNode"]:
            action = add_menu.addAction(type_name)
            action.triggered.connect(lambda checked, tn=type_name: self._on_add_node(tn))
        self._act_add.setMenu(add_menu)
        # Clicking the button itself adds a Node2D (most common)
        self._act_add.triggered.connect(lambda: self._on_add_node("Node2D"))
        self.addAction(self._act_add)

        # ── Delete ──
        self._act_delete = QAction("🗑 Delete", self)
        self._act_delete.setShortcut(QKeySequence("Delete"))
        self._act_delete.setToolTip("Delete selected node (Delete)")
        self._act_delete.triggered.connect(self._on_delete)
        self.addAction(self._act_delete)

        self.addSeparator()

        # ── Undo / Redo ──
        self._act_undo = QAction("↩ Undo", self)
        self._act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        self._act_undo.setToolTip("Undo (Ctrl+Z)")
        self._act_undo.triggered.connect(self._on_undo)
        self.addAction(self._act_undo)

        self._act_redo = QAction("↪ Redo", self)
        self._act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self._act_redo.setToolTip("Redo (Ctrl+Y)")
        self._act_redo.triggered.connect(self._on_redo)
        self.addAction(self._act_redo)

        self.addSeparator()

        # ── Grid toggle ──
        self._act_grid = QAction("# Grid", self)
        self._act_grid.setCheckable(True)
        self._act_grid.setChecked(True)
        self._act_grid.setToolTip("Toggle grid overlay (G)")
        self._act_grid.toggled.connect(self.grid_toggled.emit)
        self.addAction(self._act_grid)

    # ──────────────────────────────────────────────────────────────────
    # Action handlers
    # ──────────────────────────────────────────────────────────────────

    def _on_new(self):
        if self.model.is_dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Current scene has unsaved changes. Create new scene anyway?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        self.model.new_scene()

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Scene", "",
            "Scene Files (*.scene);;JSON Files (*.json);;All Files (*)"
        )
        if path:
            try:
                self.model.load_scene(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load scene:\n{e}")

    def _on_save(self):
        path = self.model.scene_path
        if not path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Scene", "untitled.scene",
                "Scene Files (*.scene);;JSON Files (*.json);;All Files (*)"
            )
        if path:
            try:
                self.model.save_scene(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save scene:\n{e}")

    def _on_add_node(self, type_name: str):
        parent = self.model.selected_node or self.model.scene_root
        if parent is None:
            return

        from tools.editor.scene_io import get_registered_types
        types = get_registered_types()
        cls = types.get(type_name, Node2D)

        # Generate unique name
        base = type_name
        count = 1
        existing = set()
        self._collect_names(self.model.scene_root, existing)
        name = base
        while name in existing:
            name = f"{base}_{count}"
            count += 1

        if cls is Camera2D:
            child = cls(name)
        elif issubclass(cls, Node2D):
            try:
                child = cls(name, 0, 0)
            except TypeError:
                try:
                    child = cls(name)
                except Exception:
                    child = Node2D(name, 0, 0)
        else:
            child = Node2D(name, 0, 0)

        self.model.add_node(parent, child)
        self.model.select_node(child)

    def _on_delete(self):
        node = self.model.selected_node
        if node and node is not self.model.scene_root:
            self.model.delete_node(node)

    def _on_undo(self):
        self.model.undo()

    def _on_redo(self):
        self.model.redo()

    def _collect_names(self, node, names: set):
        if node:
            names.add(node.name)
            for c in node.children:
                self._collect_names(c, names)
