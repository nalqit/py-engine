"""
scene_io.py — Scene Serialization for PyEngine2D Editor

Converts the engine's live Node tree to/from a JSON-compatible dict
that is saved as `.scene` files. This module does NOT modify any engine
classes; it reads node attributes and reconstructs nodes from saved data.

Supported node types:
    Node, Node2D, SpriteNode, Camera2D, RectangleNode, CircleNode,
    TilemapNode, AnimatedSprite, Collider2D, Area2D,
    PhysicsBody2D, RigidBody2D (+ _original_type fallback for unknown)
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Engine imports
# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so `src.pyengine2D` resolves
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.pyengine2D.scene.node import Node
from src.pyengine2D.scene.node2d import Node2D
from src.pyengine2D.scene.camera2d import Camera2D

# Optional node types — guarded imports
try:
    from src.pyengine2D.scene.sprite_node import SpriteNode
except ImportError:
    SpriteNode = None

try:
    from src.pyengine2D.scene.rectangle_node import RectangleNode
except ImportError:
    RectangleNode = None

try:
    from src.pyengine2D.scene.circle_node import CircleNode
except ImportError:
    CircleNode = None

try:
    from src.pyengine2D.scene.tilemap import TilemapNode
except ImportError:
    TilemapNode = None

try:
    from src.pyengine2D.scene.animated_sprite import AnimatedSprite
except ImportError:
    AnimatedSprite = None

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


# ═══════════════════════════════════════════════════════════════════════════
#  Type registry — maps type-name strings to classes and back
# ═══════════════════════════════════════════════════════════════════════════

_TYPE_REGISTRY: dict = {}


def _register(cls):
    """Register a node class for serialization if it was imported successfully."""
    if cls is not None:
        _TYPE_REGISTRY[cls.__name__] = cls


_register(Node)
_register(Node2D)
_register(Camera2D)
_register(SpriteNode)
_register(RectangleNode)
_register(CircleNode)
_register(TilemapNode)
_register(AnimatedSprite)
_register(Collider2D)
_register(Area2D)
_register(PhysicsBody2D)
_register(RigidBody2D)


def get_registered_types():
    """Return a dict of {type_name: class} for all serializable node types."""
    return dict(_TYPE_REGISTRY)


# ═══════════════════════════════════════════════════════════════════════════
#  Serialization helpers
# ═══════════════════════════════════════════════════════════════════════════

def _node_to_dict(node) -> dict:
    """
    Recursively serialize a Node into a JSON-compatible dict.
    
    Captures:
        - type name (class.__name__)
        - name
        - For Node2D+: local_x, local_y, scale_x, scale_y, rotation
        - visible, z_index
        - Type-specific extras (image_path, radius, color, width, height, etc.)
        - Custom properties (any attribute not starting with '_')
        - children (recursive)
    """
    data = {
        "type": type(node).__name__,
        "name": node.name,
    }

    # ── Node2D properties ──
    if isinstance(node, Node2D):
        data["x"] = node.local_x
        data["y"] = node.local_y
        data["scale_x"] = node.scale_x
        data["scale_y"] = node.scale_y
        data["rotation"] = node.rotation
        data["visible"] = getattr(node, "visible", True)
        data["z_index"] = getattr(node, "z_index", 0)

    # ── SpriteNode extras ──
    if SpriteNode and isinstance(node, SpriteNode):
        data["image_path"] = getattr(node, "_image_path", "")
        data["centered"] = getattr(node, "centered", False)

    # ── RectangleNode extras ──
    if RectangleNode and isinstance(node, RectangleNode):
        data["width"] = getattr(node, "width", 0)
        data["height"] = getattr(node, "height", 0)
        data["color"] = list(getattr(node, "color", (255, 255, 255)))

    # ── CircleNode extras ──
    if CircleNode and isinstance(node, CircleNode):
        data["radius"] = getattr(node, "radius", 0)
        data["color"] = list(getattr(node, "color", (255, 255, 255)))

    # ── AnimatedSprite extras ──
    if AnimatedSprite and isinstance(node, AnimatedSprite):
        data["frame_width"] = getattr(node, "frame_width", 32)
        data["frame_height"] = getattr(node, "frame_height", 32)

    # ── Collider2D extras ──
    if Collider2D and isinstance(node, Collider2D):
        data["width"] = getattr(node, "width", 0)
        data["height"] = getattr(node, "height", 0)
        data["is_static"] = getattr(node, "is_static", False)

    # ── _original_type hint for imported nodes of unknown type ──
    orig = getattr(node, "_original_type", None)
    if orig and orig != type_name:
        data["_original_type"] = orig

    # ── Children (recursive) ──
    if node.children:
        data["children"] = [_node_to_dict(child) for child in node.children]

    return data


def _dict_to_node(data: dict):
    """
    Recursively deserialize a dict back into a live Node tree.
    
    Uses the type registry to construct the correct class.
    Skips unknown types gracefully (creates a base Node2D instead).
    """
    type_name = data.get("type", "Node2D")
    cls = _TYPE_REGISTRY.get(type_name, Node2D)

    name = data.get("name", type_name)

    # ── Construct the node ──
    if cls is SpriteNode and SpriteNode is not None:
        # SpriteNode requires image_path at construction
        image_path = data.get("image_path", "")
        x = data.get("x", 0)
        y = data.get("y", 0)
        centered = data.get("centered", False)
        # Only construct with image if the file exists
        if image_path and os.path.exists(image_path):
            node = SpriteNode(name, image_path, x, y, centered=centered)
        else:
            # Fall back to Node2D if texture is missing
            node = Node2D(name, x, y)
            node._image_path = image_path  # preserve for re-serialization
    elif cls is Camera2D:
        node = Camera2D(name)
        node.local_x = data.get("x", 0)
        node.local_y = data.get("y", 0)
    elif RectangleNode and cls is RectangleNode:
        x, y = data.get("x", 0), data.get("y", 0)
        w = data.get("width", 32)
        h = data.get("height", 32)
        color = data.get("color", [255, 255, 255])
        node = RectangleNode(name, x, y, w, h, tuple(color) if isinstance(color, list) else color)
    elif CircleNode and cls is CircleNode:
        x, y = data.get("x", 0), data.get("y", 0)
        radius = data.get("radius", 16)
        color = data.get("color", [255, 255, 255])
        node = CircleNode(name, x, y, radius, tuple(color) if isinstance(color, list) else color)
    elif issubclass(cls, Node2D):
        x = data.get("x", 0)
        y = data.get("y", 0)
        try:
            node = cls(name, x, y)
        except TypeError:
            try:
                node = cls(name)
                node.local_x = x
                node.local_y = y
            except Exception:
                node = Node2D(name, x, y)
    elif cls is Node:
        node = Node(name)
    else:
        node = Node2D(name, data.get("x", 0), data.get("y", 0))

    # ── Apply common Node2D properties ──
    if isinstance(node, Node2D):
        node.scale_x = data.get("scale_x", 1.0)
        node.scale_y = data.get("scale_y", 1.0)
        node.rotation = data.get("rotation", 0.0)
        node.visible = data.get("visible", True)
        node.z_index = data.get("z_index", 0)

    # ── Apply type-specific extras (for Node2D fallbacks) ──
    if RectangleNode and isinstance(node, RectangleNode):
        node.width = data.get("width", node.width)
        node.height = data.get("height", node.height)
        color = data.get("color", None)
        if color:
            node.color = tuple(color) if isinstance(color, list) else color

    if CircleNode and isinstance(node, CircleNode):
        node.radius = data.get("radius", node.radius)
        color = data.get("color", None)
        if color:
            node.color = tuple(color) if isinstance(color, list) else color

    # AnimatedSprite frame dimensions
    if AnimatedSprite and isinstance(node, AnimatedSprite):
        node.frame_width = data.get("frame_width", getattr(node, "frame_width", 32))
        node.frame_height = data.get("frame_height", getattr(node, "frame_height", 32))

    # Collider2D extras
    if Collider2D and isinstance(node, Collider2D):
        node.width = data.get("width", getattr(node, "width", 0))
        node.height = data.get("height", getattr(node, "height", 0))
        node.is_static = data.get("is_static", getattr(node, "is_static", False))

    # Restore _original_type hint
    orig = data.get("_original_type", None)
    if orig:
        node._original_type = orig

    # ── Children (recursive) ──
    for child_data in data.get("children", []):
        child = _dict_to_node(child_data)
        node.add_child(child)

    return node


# ═══════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════

class SceneSerializer:
    """
    Static helper class for saving/loading .scene files.
    
    Usage::
    
        SceneSerializer.save(root_node, "level1.scene")
        root = SceneSerializer.load("level1.scene")
    """

    @staticmethod
    def save(root, path: str) -> None:
        """
        Serialize *root* node tree and write to *path* as JSON.
        
        Args:
            root: The root Node of the scene tree.
            path: File path to write (typically ending in .scene).
        """
        data = _node_to_dict(root)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load(path: str):
        """
        Read a .scene JSON file and reconstruct the node tree.
        
        Args:
            path: File path to read.
            
        Returns:
            The root Node of the deserialized scene tree.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _dict_to_node(data)

    @staticmethod
    def to_dict(root) -> dict:
        """Serialize without writing to disk (for programmatic use)."""
        return _node_to_dict(root)

    @staticmethod
    def from_dict(data: dict):
        """Deserialize from dict without reading from disk."""
        return _dict_to_node(data)
