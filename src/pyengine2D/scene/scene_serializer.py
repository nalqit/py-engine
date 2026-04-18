"""
scene_serializer.py — Scene Serialization for PyEngine2D

Converts the engine's live Node tree to/from a JSON-compatible dict
that is saved as `.scene` files.

Supported node types:
    Node, Node2D, SpriteNode, Camera2D, RectangleNode, CircleNode,
    TilemapNode, AnimatedSprite, Collider2D, Area2D,
    PhysicsBody2D, RigidBody2D (+ _original_type fallback for unknown)
"""

import json
import os
import sys
import uuid

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
    from src.pyengine2D.collision.circle_collider2d import CircleCollider2D
except ImportError:
    Collider2D = None
    CircleCollider2D = None

try:
    from src.pyengine2D.collision.area2d import Area2D
except ImportError:
    Area2D = None

try:
    from src.pyengine2D.collision.polygon_collider2d import PolygonCollider2D
except ImportError:
    PolygonCollider2D = None

try:
    from src.pyengine2D.physics.physics_body_2d import PhysicsBody2D
except ImportError:
    PhysicsBody2D = None

try:
    from src.pyengine2D.physics.rigid_body_2d import RigidBody2D
except ImportError:
    RigidBody2D = None

try:
    from src.pyengine2D.collision.collision_world import CollisionWorld
except ImportError:
    CollisionWorld = None

try:
    from src.pyengine2D.physics.physics_world_2d import PhysicsWorld2D
except ImportError:
    PhysicsWorld2D = None

try:
    from src.pyengine2D.physics.distance_constraint import DistanceConstraint
except ImportError:
    DistanceConstraint = None


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
_register(CollisionWorld)
_register(PhysicsWorld2D)
_register(CircleCollider2D)
if DistanceConstraint: _register(DistanceConstraint)


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
    props = {}
    data = {
        "id": getattr(node, "_editor_id", str(uuid.uuid4())),
        "type": type(node).__name__,
        "name": node.name,
        "properties": props,
    }
    node._editor_id = data["id"]

    # ── Node2D properties ──
    if isinstance(node, Node2D):
        props["x"] = node.local_x
        props["y"] = node.local_y
        props["scale_x"] = node.scale_x
        props["scale_y"] = node.scale_y
        props["rotation"] = node.rotation
        props["visible"] = getattr(node, "visible", True)
        props["z_index"] = getattr(node, "z_index", 0)

    # ── SpriteNode extras ──
    if SpriteNode and isinstance(node, SpriteNode):
        props["image_path"] = getattr(node, "_image_path", "")
        props["centered"] = getattr(node, "centered", False)

    # ── RectangleNode extras ──
    if RectangleNode and isinstance(node, RectangleNode):
        props["width"] = getattr(node, "width", 0)
        props["height"] = getattr(node, "height", 0)
        props["color"] = list(getattr(node, "color", (255, 255, 255)))

    # ── CircleNode extras ──
    if CircleNode and isinstance(node, CircleNode):
        props["radius"] = getattr(node, "radius", 0)
        props["color"] = list(getattr(node, "color", (255, 255, 255)))

    # ── AnimatedSprite extras ──
    if AnimatedSprite and isinstance(node, AnimatedSprite):
        props["frame_width"] = getattr(node, "frame_width", 32)
        props["frame_height"] = getattr(node, "frame_height", 32)

    # ── Collider2D extras ──
    if Collider2D and isinstance(node, Collider2D):
        props["width"] = getattr(node, "width", 0)
        props["height"] = getattr(node, "height", 0)
        props["is_static"] = getattr(node, "is_static", False)
        props["is_trigger"] = getattr(node, "is_trigger", False)
        props["layer"] = getattr(node, "layer", "default")
        props["mask"] = list(getattr(node, "mask", []))

    # ── PhysicsBody2D extras ──
    if PhysicsBody2D and isinstance(node, PhysicsBody2D):
        props["vx"] = getattr(node, "vx", 0.0)
        props["vy"] = getattr(node, "vy", 0.0)
        props["use_gravity"] = getattr(node, "use_gravity", True)
        
    if RigidBody2D and isinstance(node, RigidBody2D):
        props["vx"] = getattr(node, "vx", 0.0)
        props["vy"] = getattr(node, "vy", 0.0)
        props["use_gravity"] = getattr(node, "use_gravity", True)
        props["gravity_scale"] = getattr(node, "gravity_scale", 1.0)
        props["mass"] = getattr(node, "mass", 1.0)
        props["is_kinematic"] = getattr(node, "is_kinematic", False)
        props["friction"] = getattr(node, "friction", 0.2)
        props["restitution"] = getattr(node, "restitution", 0.5)

    # ── CollisionWorld extras ──
    if CollisionWorld and isinstance(node, CollisionWorld):
        props["cell_size"] = getattr(node._grid, "cell_size", 128) if hasattr(node, "_grid") else 128

    # ── PhysicsWorld2D extras ──
    if PhysicsWorld2D and isinstance(node, PhysicsWorld2D):
        props["gravity_y"] = getattr(node, "gravity_y", 800.0)
        props["sub_steps"] = getattr(node, "sub_steps", 1)

    # ── Constraints ──
    if DistanceConstraint and isinstance(node, DistanceConstraint):
        props["pivot_x"] = getattr(node, "local_x", 0)  # constraint position is anchor x/y
        props["pivot_y"] = getattr(node, "local_y", 0)
        props["length"] = getattr(node, "length", 100)
        props["body_name"] = node.body_a.name if getattr(node, "body_a", None) else ""
        
    # ── Ball (Newton's Cradle) ──
    from src.games.newtons_cradle.main import Ball
    if Ball and isinstance(node, Ball):
        props["radius"] = getattr(node, "radius", 20)

    # ── CircleCollider2D extras ──
    if CircleCollider2D and isinstance(node, CircleCollider2D):
        props["radius"] = getattr(node, "radius", 16)

    # ── PolygonCollider2D extras ──
    if PolygonCollider2D and isinstance(node, PolygonCollider2D):
        props["points"] = [list(p) for p in getattr(node, "local_points", [])]

    script_value = getattr(node, "script", None)
    if script_value:
        data["script"] = script_value

    # ── _original_type hint for imported nodes of unknown type ──
    orig = getattr(node, "_original_type", None)
    type_name = type(node).__name__
    if orig and orig != type_name:
        data["_original_type"] = orig

    # ── Children (recursive) ──
    if node.children:
        data["children"] = [_node_to_dict(child) for child in node.children]

    return data


def _dict_to_node(data: dict, custom_types: dict = None):
    """
    Recursively deserialize a dict back into a live Node tree.
    
    Uses the type registry to construct the correct class.
    Skips unknown types gracefully (creates a base Node2D instead).
    """
    custom_types = custom_types or {}
    type_name = data.get("type", "Node2D")
    node_id = data.get("id")
    properties = data.get("properties")
    if isinstance(properties, dict):
        payload = dict(properties)
    else:
        payload = {}
        for key, value in data.items():
            if key in {"id", "type", "name", "children", "script", "_original_type"}:
                continue
            payload[key] = value
    
    # Check original type for custom subclass injection
    orig_type = data.get("_original_type", None)
    
    # Try to resolve class from custom_types, then fall back to the main registry
    cls = None
    if orig_type and orig_type in custom_types:
        cls = custom_types[orig_type]
    elif type_name in custom_types:
        cls = custom_types[type_name]
    else:
        cls = _TYPE_REGISTRY.get(type_name, Node2D)

    name = data.get("name", type_name)

    # ── Construct the node ──
    if cls is SpriteNode and SpriteNode is not None:
        # SpriteNode requires image_path at construction
        image_path = payload.get("image_path", "")
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        centered = payload.get("centered", False)
        # Only construct with image if the file exists
        if image_path and os.path.exists(image_path):
            node = SpriteNode(name, image_path, x, y, centered=centered)
        else:
            # Fall back to Node2D if texture is missing
            node = Node2D(name, x, y)
            node._image_path = image_path  # preserve for re-serialization
    elif cls is Camera2D:
        node = Camera2D(name)
        node.local_x = payload.get("x", 0)
        node.local_y = payload.get("y", 0)
    elif RectangleNode and cls is RectangleNode:
        x, y = payload.get("x", 0), payload.get("y", 0)
        w = payload.get("width", 32)
        h = payload.get("height", 32)
        color = payload.get("color", [255, 255, 255])
        node = RectangleNode(name, x, y, w, h, tuple(color) if isinstance(color, list) else color)
    elif CircleNode and cls is CircleNode:
        x, y = payload.get("x", 0), payload.get("y", 0)
        radius = payload.get("radius", 16)
        color = payload.get("color", [255, 255, 255])
        node = CircleNode(name, x, y, radius, tuple(color) if isinstance(color, list) else color)
    elif CollisionWorld and cls is CollisionWorld:
        # CollisionWorld doesn't take x,y, it takes cell_size
        node = CollisionWorld(name, cell_size=payload.get("cell_size", 128))
    elif PhysicsWorld2D and cls is PhysicsWorld2D:
        node = PhysicsWorld2D(
            name,
            gravity_y=payload.get("gravity_y", 800.0),
            sub_steps=payload.get("sub_steps", 1)
        )
    elif DistanceConstraint and cls is DistanceConstraint:
        node = DistanceConstraint(
            name, 
            payload.get("pivot_x", 0), 
            payload.get("pivot_y", 0), 
            None, # Will need body linked in ready() or via custom_types mapping
            payload.get("length", 100)
        )
        node._body_name = payload.get("body_name", "") # store hint for later reference resolving
    elif CircleCollider2D and cls is CircleCollider2D:
        node = CircleCollider2D(
            name,
            payload.get("x", 0),
            payload.get("y", 0),
            payload.get("radius", 16)
        )
    elif PolygonCollider2D and cls is PolygonCollider2D:
        points = payload.get("points", [(0,0), (10,0), (0,10)])
        node = PolygonCollider2D(
            name,
            payload.get("x", 0),
            payload.get("y", 0),
            [tuple(p) for p in points]
        )
    elif issubclass(cls, Node2D):
        x = payload.get("x", 0)
        y = payload.get("y", 0)
        # Attempt minimal instantiation. If custom class requires arguments (like colliders),
        # we bypass __init__ using __new__ to ensure it always reconstructs from JSON
        # without crashing, then manually apply positioning.
        try:
            node = cls(name, x, y)
        except TypeError:
            try:
                node = cls.__new__(cls)
                # Mimic Node.__init__ setup for basic functionality
                node.name = name
                node.parent = None
                node.children = []
                node._engine = None
                
                # Hidden properties required by Node2D's getters/setters
                node._local_x = x
                node._local_y = y
                node._scale_x = 1.0
                node._scale_y = 1.0
                node._rotation = 0.0
                node._dirty = True
                node._global_transform = (0, 0, 1, 1, 0)
                
                node.visible = True
                node.z_index = 0
                
                if Collider2D and isinstance(node, Collider2D):
                    node.width = 32
                    node.height = 32
                    node.is_static = False
                    node.is_trigger = False
                    node.layer = "default"
                    node.mask = set()
                    
                if PhysicsBody2D and isinstance(node, PhysicsBody2D):
                    node.vx = 0.0
                    node.vy = 0.0
                    node.use_gravity = True
                if RigidBody2D and isinstance(node, RigidBody2D):
                    node.vx = 0.0
                    node.vy = 0.0
                    node.force_x = 0.0
                    node.force_y = 0.0
                    node.use_gravity = True
                    node.gravity_scale = 1.0
                    node.mass = 1.0
                    node.inv_mass = 1.0
                    node.is_kinematic = False
                    node.friction = 0.2
                    node.restitution = 0.5
                    
                    # Ball specific fallback
                    from src.games.newtons_cradle.main import Ball
                    if isinstance(node, Ball):
                        node.radius = 20
                        node.is_dragged = False
                    
            except Exception as e:
                import traceback
                print(f"Failed to rebuild {cls} via __new__: {e}")
                traceback.print_exc()
                node = Node2D(name, x, y)
    elif cls is Node:
        node = Node(name)
    else:
        node = Node2D(name, payload.get("x", 0), payload.get("y", 0))

    # ── Apply common Node2D properties ──
    if isinstance(node, Node2D):
        node.scale_x = payload.get("scale_x", 1.0)
        node.scale_y = payload.get("scale_y", 1.0)
        node.rotation = payload.get("rotation", 0.0)
        node.visible = payload.get("visible", True)
        node.z_index = payload.get("z_index", 0)

    # ── PhysicsBody2D extras ──
    if PhysicsBody2D and isinstance(node, PhysicsBody2D):
        node.vx = payload.get("vx", getattr(node, "vx", 0.0))
        node.vy = payload.get("vy", getattr(node, "vy", 0.0))
        node.use_gravity = payload.get("use_gravity", getattr(node, "use_gravity", True))

    if RigidBody2D and isinstance(node, RigidBody2D):
        node.vx = payload.get("vx", getattr(node, "vx", 0.0))
        node.vy = payload.get("vy", getattr(node, "vy", 0.0))
        node.use_gravity = payload.get("use_gravity", getattr(node, "use_gravity", True))
        node.gravity_scale = payload.get("gravity_scale", getattr(node, "gravity_scale", 1.0))
        node.mass = payload.get("mass", getattr(node, "mass", 1.0))
        node.inv_mass = 1.0 / node.mass if node.mass > 0 else 0.0
        node.is_kinematic = payload.get("is_kinematic", getattr(node, "is_kinematic", False))
        node.friction = payload.get("friction", getattr(node, "friction", 0.2))
        node.restitution = payload.get("restitution", getattr(node, "restitution", 0.5))
        
    # ── Ball extras ──
    from src.games.newtons_cradle.main import Ball
    if Ball and isinstance(node, Ball):
        node.radius = payload.get("radius", 20)
        node.is_dragged = False

    # ── Type-specific extras (for Node2D fallbacks) ──
    if Collider2D and isinstance(node, Collider2D):
        node.width = payload.get("width", getattr(node, "width", 32))
        node.height = payload.get("height", getattr(node, "height", 32))
        node.is_static = payload.get("is_static", getattr(node, "is_static", False))
        node.is_trigger = payload.get("is_trigger", getattr(node, "is_trigger", False))
        node.layer = payload.get("layer", getattr(node, "layer", "default"))
        node.mask = set(payload.get("mask", getattr(node, "mask", [])))

    if RectangleNode and isinstance(node, RectangleNode):
        node.width = payload.get("width", node.width)
        node.height = payload.get("height", node.height)
        color = payload.get("color", None)
        if color:
            node.color = tuple(color) if isinstance(color, list) else color

    if CircleNode and isinstance(node, CircleNode):
        node.radius = payload.get("radius", node.radius)
        color = payload.get("color", None)
        if color:
            node.color = tuple(color) if isinstance(color, list) else color

    # AnimatedSprite frame dimensions
    if AnimatedSprite and isinstance(node, AnimatedSprite):
        node.frame_width = payload.get("frame_width", getattr(node, "frame_width", 32))
        node.frame_height = payload.get("frame_height", getattr(node, "frame_height", 32))



    if CircleCollider2D and isinstance(node, CircleCollider2D):
        node.radius = payload.get("radius", getattr(node, "radius", 16))

    if PolygonCollider2D and isinstance(node, PolygonCollider2D):
        points = payload.get("points", None)
        if points:
            node.local_points = [tuple(p) for p in points]

    node._editor_id = node_id or str(uuid.uuid4())
    script_value = data.get("script", payload.get("script", None))
    if script_value:
        node.script = script_value

    # Restore _original_type hint
    orig = data.get("_original_type", None)
    if orig:
        node._original_type = orig

    # ── Children (recursive) ──
    for child_data in data.get("children", []):
        child = _dict_to_node(child_data, custom_types)
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
    def load(path: str, custom_types: dict = None):
        """
        Read a .scene JSON file and reconstruct the node tree.
        
        Args:
            path: File path to read.
            custom_types: Dict mapping type strings to node classes (e.g. `{"Player": Player}`).
            
        Returns:
            The root Node of the deserialized scene tree.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        root = _dict_to_node(data, custom_types)
        SceneSerializer._resolve_references(root)
        SceneSerializer._call_ready(root)
        return root

    @staticmethod
    def _call_ready(node):
        """Recursively call .ready() on all nodes that implement it."""
        if hasattr(node, "ready") and callable(node.ready):
            node.ready()
        for child in node.children:
            SceneSerializer._call_ready(child)

    @staticmethod
    def to_dict(root) -> dict:
        """Serialize without writing to disk (for programmatic use)."""
        return _node_to_dict(root)

    @staticmethod
    def from_dict(data: dict, custom_types: dict = None):
        """Deserialize from dict without reading from disk."""
        root = _dict_to_node(data, custom_types)
        SceneSerializer._resolve_references(root)
        SceneSerializer._call_ready(root)
        return root

    @staticmethod
    def _resolve_references(root):
        """Walk the tree and resolve name-based references (e.g. DistanceConstraint.body_a)."""
        # 1. Build an index of names to nodes
        name_map = {}
        def _collect(node):
            if node.name:
                name_map[node.name] = node
            for child in node.children:
                _collect(child)
        _collect(root)

        # 2. Resolve known reference properties
        def _apply(node):
            # DistanceConstraint.body_a
            body_name = getattr(node, "_body_name", None)
            if body_name and body_name in name_map:
                if hasattr(node, "body_a"):
                    node.body_a = name_map[body_name]
            
            # RigidBody2D.collider / collision_world (if they were named)
            # Actually they are usually children or handled via __init__

            for child in node.children:
                _apply(child)
        _apply(root)
