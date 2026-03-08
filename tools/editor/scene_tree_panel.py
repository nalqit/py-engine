"""
scene_tree_panel.py — Hierarchical Scene Tree Panel

Displays the node tree in a QTreeWidget inside a QDockWidget.
Selection syncs with EditorModel ↔ Inspector ↔ Viewport.
Context menu: Add Child, Delete, Rename.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from PyQt5.QtWidgets import (
    QDockWidget, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QMenu, QAction, QInputDialog, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

import os, sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.pyengine2D.scene.node import Node
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.camera2d import Camera2D

if TYPE_CHECKING:
    from tools.editor.editor_model import EditorModel


# Node type icons (unicode fallback)
_TYPE_ICONS = {
    "Node": "📦",
    "Node2D": "🔷",
    "SpriteNode": "🖼",
    "Camera2D": "📷",
    "RectangleNode": "⬛",
    "CircleNode": "⚫",
    "TilemapNode": "🗺",
    "AnimatedSprite": "🎞",
    "Collider2D": "⬡",
    "Area2D": "⬡",
    "PhysicsBody2D": "⚡",
    "RigidBody2D": "⚡",
    "Player": "🎮",
}


class SceneTreePanel(QDockWidget):
    """Dockable panel showing the hierarchical scene tree."""

    def __init__(self, model: "EditorModel", parent=None):
        super().__init__("Scene Tree", parent)
        self.model = model
        self.setMinimumWidth(220)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # ── Tree widget ──
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFont(QFont("Segoe UI", 10))
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.currentItemChanged.connect(self._on_item_selected)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tree)
        self.setWidget(container)

        # ── Listen to model changes ──
        self.model.on_scene_changed(self.rebuild)
        self.model.on_selection_changed(self._sync_selection)

        # Internal flag to avoid re-entrant selection signals
        self._updating = False

        self.rebuild()

    # ──────────────────────────────────────────────────────────────────
    # Rebuild the tree from model.scene_root
    # ──────────────────────────────────────────────────────────────────

    def rebuild(self):
        """Re-populate the QTreeWidget from the current scene root."""
        self._updating = True
        self.tree.clear()
        if self.model.scene_root:
            root_item = self._build_item(self.model.scene_root)
            self.tree.addTopLevelItem(root_item)
            self.tree.expandAll()
        self._sync_selection()
        self._updating = False

    def _build_item(self, node: Node) -> QTreeWidgetItem:
        type_name = type(node).__name__
        # Show _original_type for imported nodes (e.g. "Player" cloned as Node2D)
        display_type = getattr(node, "_original_type", None) or type_name
        icon_str = _TYPE_ICONS.get(display_type, _TYPE_ICONS.get(type_name, "📦"))
        item = QTreeWidgetItem([f"{icon_str} {node.name}"])
        item.setData(0, Qt.UserRole, id(node))
        item.setToolTip(0, f"Type: {display_type}")
        # Store reference for quick lookup
        item._node_ref = node  # type: ignore[attr-defined]
        for child in node.children:
            item.addChild(self._build_item(child))
        return item

    # ──────────────────────────────────────────────────────────────────
    # Selection sync
    # ──────────────────────────────────────────────────────────────────

    def _on_item_selected(self, current: Optional[QTreeWidgetItem], previous):
        if self._updating:
            return
        if current and hasattr(current, "_node_ref"):
            node = current._node_ref  # type: ignore[attr-defined]
            self.model.select_node(node)
        else:
            self.model.select_node(None)

    def _sync_selection(self):
        """Highlight the tree item matching model.selected_node."""
        self._updating = True
        sel_node = self.model.selected_node
        if sel_node is None:
            self.tree.clearSelection()
        else:
            item = self._find_item(self.tree.invisibleRootItem(), sel_node)
            if item:
                self.tree.setCurrentItem(item)
        self._updating = False

    def _find_item(self, parent_item, target_node) -> Optional[QTreeWidgetItem]:
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if hasattr(child, "_node_ref") and child._node_ref is target_node:
                return child
            found = self._find_item(child, target_node)
            if found:
                return found
        return None

    # ──────────────────────────────────────────────────────────────────
    # Context menu
    # ──────────────────────────────────────────────────────────────────

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item or not hasattr(item, "_node_ref"):
            return

        node = item._node_ref
        menu = QMenu(self)

        # Add child sub-menu
        add_menu = menu.addMenu("➕ Add Child")
        for type_name in ["Node2D", "SpriteNode", "Camera2D", "RectangleNode", "CircleNode"]:
            action = add_menu.addAction(f"{_TYPE_ICONS.get(type_name, '📦')} {type_name}")
            action.setData(type_name)
            action.triggered.connect(lambda checked, tn=type_name, n=node: self._add_child(n, tn))

        # Delete
        if node is not self.model.scene_root:
            delete_action = menu.addAction("🗑 Delete")
            delete_action.triggered.connect(lambda: self.model.delete_node(node))

        # Rename
        rename_action = menu.addAction("✏ Rename")
        rename_action.triggered.connect(lambda: self._rename_node(node))

        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def _add_child(self, parent: Node, type_name: str):
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
            child = cls(name, 0, 0) if cls is Node2D else cls.__new__(cls)
            if cls is not Node2D:
                # For RectangleNode, CircleNode, etc.
                try:
                    child.__init__(name, 0, 0)
                except TypeError:
                    try:
                        child.__init__(name)
                    except Exception:
                        child = Node2D(name, 0, 0)
        else:
            child = Node2D(name, 0, 0)

        self.model.add_node(parent, child)

    def _rename_node(self, node: Node):
        new_name, ok = QInputDialog.getText(
            self, "Rename Node", "New name:", text=node.name
        )
        if ok and new_name.strip():
            old = node.name
            self.model.change_property(node, "name", old, new_name.strip())

    def _collect_names(self, node, names: set):
        if node:
            names.add(node.name)
            for c in node.children:
                self._collect_names(c, names)
