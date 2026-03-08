"""
editor_model.py — Central state manager for the PyEngine2D Editor

Manages:
    - Scene root node
    - Selected node(s)
    - Undo / Redo stack (Command pattern)
    - Change notifications via callbacks (Qt-agnostic)

Thread safety:
    All operations run on the Qt main thread. The QTimer-driven viewport
    only *reads* the model; it never writes. All mutations flow through
    push_command() which is always called from the main thread.
"""

from __future__ import annotations

import copy
from typing import Any, Callable, List, Optional

import os
import sys

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.pyengine2D.scene.node import Node
from src.pyengine2D.scene.node2d import Node2D


# ═══════════════════════════════════════════════════════════════════════════
#  Command base class & concrete commands
# ═══════════════════════════════════════════════════════════════════════════

class Command:
    """Abstract base for reversible editor operations."""

    def execute(self) -> None:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError

    def description(self) -> str:
        return self.__class__.__name__


class AddNodeCommand(Command):
    """Add *child* under *parent*."""

    def __init__(self, parent: Node, child: Node):
        self.parent = parent
        self.child = child

    def execute(self) -> None:
        self.parent.add_child(self.child)

    def undo(self) -> None:
        self.parent.remove_child(self.child)

    def description(self) -> str:
        return f"Add {self.child.name}"


class DeleteNodeCommand(Command):
    """Remove *node* from its parent. Remembers the parent and index for undo."""

    def __init__(self, node: Node):
        self.node = node
        self.parent: Optional[Node] = node.parent
        self.index: int = 0

    def execute(self) -> None:
        self.parent = self.node.parent
        if self.parent:
            try:
                self.index = self.parent.children.index(self.node)
            except ValueError:
                self.index = len(self.parent.children)
            self.parent.remove_child(self.node)

    def undo(self) -> None:
        if self.parent:
            # Re-insert at the original index
            self.node.parent = self.parent
            self.parent.children.insert(self.index, self.node)
            if hasattr(self.node, "set_dirty"):
                self.node.set_dirty()

    def description(self) -> str:
        return f"Delete {self.node.name}"


class TransformCommand(Command):
    """Change a node's local position. Fires undo by reverting to old values."""

    def __init__(self, node: Node2D, old_x: float, old_y: float,
                 new_x: float, new_y: float):
        self.node = node
        self.old_x, self.old_y = old_x, old_y
        self.new_x, self.new_y = new_x, new_y

    def execute(self) -> None:
        self.node.local_x = self.new_x
        self.node.local_y = self.new_y

    def undo(self) -> None:
        self.node.local_x = self.old_x
        self.node.local_y = self.old_y

    def description(self) -> str:
        return f"Move {self.node.name}"


class PropertyChangeCommand(Command):
    """Generic property setter — works for any attribute name."""

    def __init__(self, node, prop_name: str, old_value: Any, new_value: Any):
        self.node = node
        self.prop_name = prop_name
        self.old_value = old_value
        self.new_value = new_value

    def execute(self) -> None:
        setattr(self.node, self.prop_name, self.new_value)

    def undo(self) -> None:
        setattr(self.node, self.prop_name, self.old_value)

    def description(self) -> str:
        return f"Change {self.prop_name} on {self.node.name}"


class ReparentCommand(Command):
    """Move *node* from its current parent to *new_parent*."""

    def __init__(self, node: Node, new_parent: Node, insert_index: int = -1):
        self.node = node
        self.old_parent: Optional[Node] = node.parent
        self.old_index: int = 0
        self.new_parent = new_parent
        self.insert_index = insert_index

    def execute(self) -> None:
        self.old_parent = self.node.parent
        if self.old_parent:
            try:
                self.old_index = self.old_parent.children.index(self.node)
            except ValueError:
                self.old_index = 0
            self.old_parent.remove_child(self.node)
        self.new_parent.add_child(self.node)

    def undo(self) -> None:
        self.new_parent.remove_child(self.node)
        if self.old_parent:
            self.node.parent = self.old_parent
            self.old_parent.children.insert(self.old_index, self.node)
            if hasattr(self.node, "set_dirty"):
                self.node.set_dirty()

    def description(self) -> str:
        return f"Reparent {self.node.name}"


# ═══════════════════════════════════════════════════════════════════════════
#  EditorModel
# ═══════════════════════════════════════════════════════════════════════════

class EditorModel:
    """
    Central state for the editor.

    All panel widgets observe this model via on_change callbacks.
    Mutations go through push_command() to enable undo/redo.

    Attributes:
        scene_root: The root node of the currently open scene.
        selected_node: Currently selected node (or None).
        scene_path: File path of the currently loaded .scene file (or None).
    """

    MAX_UNDO = 200  # cap to prevent unbounded memory growth

    def __init__(self):
        self.scene_root: Optional[Node] = Node2D("Root")
        self.selected_node: Optional[Node] = None
        self.scene_path: Optional[str] = None
        self._dirty: bool = False  # unsaved changes flag

        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []

        # Callback lists — panels register themselves here
        self._on_scene_changed: List[Callable] = []
        self._on_selection_changed: List[Callable] = []

    # ── Observer registration ──────────────────────────────────────────

    def on_scene_changed(self, callback: Callable):
        """Register a callback invoked when scene tree structure changes."""
        self._on_scene_changed.append(callback)

    def on_selection_changed(self, callback: Callable):
        """Register a callback invoked when selected_node changes."""
        self._on_selection_changed.append(callback)

    def _notify_scene_changed(self):
        for cb in self._on_scene_changed:
            cb()

    def _notify_selection_changed(self):
        for cb in self._on_selection_changed:
            cb()

    # ── Selection ──────────────────────────────────────────────────────

    def select_node(self, node: Optional[Node]):
        """Set the selected node and notify observers."""
        if self.selected_node is not node:
            self.selected_node = node
            self._notify_selection_changed()

    # ── Undo / Redo ───────────────────────────────────────────────────

    def push_command(self, cmd: Command) -> None:
        """Execute a command and push it onto the undo stack."""
        cmd.execute()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()
        self._dirty = True
        # Trim to prevent unbounded growth
        if len(self._undo_stack) > self.MAX_UNDO:
            self._undo_stack.pop(0)
        self._notify_scene_changed()

    def undo(self) -> bool:
        """Undo the last command. Returns True if something was undone."""
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        self._dirty = True
        self._notify_scene_changed()
        return True

    def redo(self) -> bool:
        """Redo the last undone command. Returns True if something was redone."""
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        self._dirty = True
        self._notify_scene_changed()
        return True

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    # ── Scene management ──────────────────────────────────────────────

    def new_scene(self):
        """Clear scene and start fresh."""
        self.scene_root = Node2D("Root")
        self.selected_node = None
        self.scene_path = None
        self._dirty = False
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify_scene_changed()
        self._notify_selection_changed()

    def load_scene(self, path: str):
        """Load a .scene file and replace the current scene."""
        from tools.editor.scene_io import SceneSerializer
        self.scene_root = SceneSerializer.load(path)
        self.selected_node = None
        self.scene_path = path
        self._dirty = False
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify_scene_changed()
        self._notify_selection_changed()

    def save_scene(self, path: str):
        """Save the current scene to a .scene file."""
        from tools.editor.scene_io import SceneSerializer
        if self.scene_root:
            SceneSerializer.save(self.scene_root, path)
            self.scene_path = path
            self._dirty = False

    # ── Convenience methods ───────────────────────────────────────────

    def add_node(self, parent: Node, child: Node):
        """Add a child node via undoable command."""
        self.push_command(AddNodeCommand(parent, child))

    def delete_node(self, node: Node):
        """Delete a node via undoable command. Cannot delete scene root."""
        if node is self.scene_root:
            return
        if node is self.selected_node:
            self.select_node(None)
        self.push_command(DeleteNodeCommand(node))

    def change_property(self, node, prop_name: str, old_value, new_value):
        """Change a property via undoable command."""
        self.push_command(PropertyChangeCommand(node, prop_name, old_value, new_value))

    def move_node(self, node: Node2D, old_x, old_y, new_x, new_y):
        """Move a node via undoable command."""
        self.push_command(TransformCommand(node, old_x, old_y, new_x, new_y))
