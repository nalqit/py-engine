"""
scene_importer.py — Import live Node trees into the Editor

Provides two import mechanisms:
    1. from_node(root) — Walk an existing in-memory Node tree and deep-clone
       it into the editor model (safe, no code execution).
    2. from_python_file(path) — Parse a .py file using AST to find the scene
       root variable, then construct nodes from the AST (no importlib execution,
       no side-effects).

Thread safety:
    All operations produce a new tree; the editor model is only mutated via
    EditorModel methods on the Qt main thread.
"""

from __future__ import annotations

import os
import sys
from typing import Optional, TYPE_CHECKING

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.pyengine2D.scene.node import Node
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.camera2d import Camera2D

# Optional node types
try:
    from src.pyengine2D.scene.rectangle_node import RectangleNode
except ImportError:
    RectangleNode = None

try:
    from src.pyengine2D.scene.circle_node import CircleNode
except ImportError:
    CircleNode = None

try:
    from src.pyengine2D.scene.sprite_node import SpriteNode
except ImportError:
    SpriteNode = None

try:
    from src.pyengine2D.scene.animated_sprite import AnimatedSprite
except ImportError:
    AnimatedSprite = None

try:
    from src.pyengine2D.scene.tilemap import TilemapNode
except ImportError:
    TilemapNode = None

try:
    from src.pyengine2D.collision.collider2d import Collider2D
except ImportError:
    Collider2D = None

try:
    from src.pyengine2D.collision.area2d import Area2D
except ImportError:
    Area2D = None

try:
    from src.pyengine2D.physics.physics_body_2d import PhysicsBody2D
except ImportError:
    PhysicsBody2D = None

try:
    from src.pyengine2D.physics.rigid_body_2d import RigidBody2D
except ImportError:
    RigidBody2D = None

if TYPE_CHECKING:
    from tools.editor.editor_model import EditorModel


class SceneImporter:
    """
    Safely imports a live Node tree into the editor.

    Uses deep-cloning (attribute copy) — never executes game logic.
    Unknown node subclasses are cloned as Node2D with _original_type preserved.
    """

    @staticmethod
    def from_node(root: Node, model: "EditorModel") -> None:
        """
        Clone *root* and its entire subtree into the editor model.

        This replaces the current scene, clears undo/redo, and notifies
        all panels to rebuild.

        Args:
            root: The live in-memory Node tree to import.
            model: The EditorModel to populate.
        """
        cloned = SceneImporter._clone_node(root)
        model.scene_root = cloned
        model.selected_node = None
        model.scene_path = None
        model._dirty = False
        model._undo_stack.clear()
        model._redo_stack.clear()
        model._notify_scene_changed()
        model._notify_selection_changed()

    @staticmethod
    def clone_tree(root: Node) -> Node:
        """Clone *root* and its entire subtree. Returns the new root."""
        return SceneImporter._clone_node(root)

    @staticmethod
    def _clone_node(node: Node) -> Node:
        """
        Recursively clone a node tree by reading attributes.

        No game logic is executed. For unknown subclasses, creates a
        Node2D and stores the original class name as _original_type.
        """
        clone = SceneImporter._create_clone(node)

        # Copy children recursively
        for child in node.children:
            child_clone = SceneImporter._clone_node(child)
            clone.add_child(child_clone)

        return clone

    @staticmethod
    def _create_clone(node: Node) -> Node:
        """Create a single-node clone (no children) by reading attributes."""
        type_name = type(node).__name__

        # ── Camera2D ──
        if isinstance(node, Camera2D):
            clone = Camera2D(node.name)
            clone.local_x = node.local_x
            clone.local_y = node.local_y
            SceneImporter._copy_node2d_props(node, clone)
            return clone

        # ── RectangleNode ──
        if RectangleNode and isinstance(node, RectangleNode):
            clone = RectangleNode(
                node.name,
                node.local_x, node.local_y,
                getattr(node, "width", 32),
                getattr(node, "height", 32),
                getattr(node, "color", (255, 255, 255)),
            )
            SceneImporter._copy_node2d_props(node, clone)
            return clone

        # ── CircleNode ──
        if CircleNode and isinstance(node, CircleNode):
            clone = CircleNode(
                node.name,
                node.local_x, node.local_y,
                getattr(node, "radius", 16),
                getattr(node, "color", (255, 255, 255)),
            )
            SceneImporter._copy_node2d_props(node, clone)
            return clone

        # ── SpriteNode ──
        if SpriteNode and isinstance(node, SpriteNode):
            image_path = getattr(node, "_image_path", "")
            # Create as Node2D with sprite metadata (don't load texture in editor)
            clone = Node2D(node.name, node.local_x, node.local_y)
            clone._image_path = image_path
            clone._original_type = "SpriteNode"
            clone.centered = getattr(node, "centered", False)
            clone.width = getattr(node, "width", 0)
            clone.height = getattr(node, "height", 0)
            SceneImporter._copy_node2d_props(node, clone)
            return clone

        # ── AnimatedSprite ──
        if AnimatedSprite and isinstance(node, AnimatedSprite):
            clone = Node2D(node.name, node.local_x, node.local_y)
            clone._original_type = "AnimatedSprite"
            clone.frame_width = getattr(node, "frame_width", 32)
            clone.frame_height = getattr(node, "frame_height", 32)
            SceneImporter._copy_node2d_props(node, clone)
            return clone

        # ── Collider2D / Area2D ──
        if Collider2D and isinstance(node, Collider2D):
            clone = Node2D(node.name, node.local_x, node.local_y)
            clone._original_type = type_name
            clone.width = getattr(node, "width", 0)
            clone.height = getattr(node, "height", 0)
            clone.is_static = getattr(node, "is_static", False)
            clone.layer = getattr(node, "layer", "")
            clone.mask = getattr(node, "mask", set())
            SceneImporter._copy_node2d_props(node, clone)
            return clone

        # ── PhysicsBody2D / RigidBody2D ──
        if PhysicsBody2D and isinstance(node, PhysicsBody2D):
            clone = Node2D(node.name, node.local_x, node.local_y)
            clone._original_type = type_name
            SceneImporter._copy_node2d_props(node, clone)
            return clone

        # ── Generic Node2D ──
        if isinstance(node, Node2D):
            clone = Node2D(node.name, node.local_x, node.local_y)
            clone._original_type = type_name if type_name != "Node2D" else None
            SceneImporter._copy_node2d_props(node, clone)
            return clone

        # ── Base Node ──
        clone = Node(node.name)
        return clone

    @staticmethod
    def _copy_node2d_props(src: Node2D, dst: Node2D):
        """Copy common Node2D properties from src to dst (excluding position)."""
        dst.scale_x = src.scale_x
        dst.scale_y = src.scale_y
        dst.rotation = src.rotation
        dst.visible = getattr(src, "visible", True)
        dst.z_index = getattr(src, "z_index", 0)

    @staticmethod
    def validate_tree(root: Node) -> dict:
        """
        Walk *root* and return a diagnostic summary.
        Useful for manual verification after import.

        Returns:
            dict with keys: total_nodes, node_types (Counter), warnings (list)
        """
        from collections import Counter
        result = {"total_nodes": 0, "node_types": Counter(), "warnings": []}

        def _walk(node):
            result["total_nodes"] += 1
            result["node_types"][type(node).__name__] += 1

            if isinstance(node, Node2D):
                if node.scale_x == 0 or node.scale_y == 0:
                    result["warnings"].append(
                        f"Node '{node.name}' has zero scale ({node.scale_x}, {node.scale_y})"
                    )
            for child in node.children:
                _walk(child)

        _walk(root)
        return result
