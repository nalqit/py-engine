/// Lightweight data model representing a node in the PyEngine 2D scene tree.
///
/// Each node carries its own transform properties so the Inspector can
/// display and edit them when the node is selected.
class EngineNode {
  EngineNode({
    required this.name,
    required this.type,
    List<EngineNode>? children,
    this.isExpanded = true,
    this.x = 0.0,
    this.y = 0.0,
    this.scaleX = 1.0,
    this.scaleY = 1.0,
    this.rotation = 0.0,
    this.visible = true,
    this.resource,
    this.script,
  }) : children = children ?? [];

  String name;
  final String type;
  final List<EngineNode> children;
  bool isExpanded;

  // ── Transform ──
  double x;
  double y;
  double scaleX;
  double scaleY;
  double rotation;

  // ── Visibility ──
  bool visible;

  // ── Optional metadata from .scene files ──
  final String? resource;
  final String? script;

  bool get hasChildren => children.isNotEmpty;

  // ───────────────────────────────────────────
  // JSON parsing
  // ───────────────────────────────────────────

  /// Recursively parses a scene JSON map into an [EngineNode] tree.
  ///
  /// Expected JSON shape (matches the .scene format):
  /// ```json
  /// {
  ///   "name": "Root",
  ///   "type": "Node2D",
  ///   "properties": { "x": 0, "y": 0, "scale_x": 1, ... },
  ///   "script": "entities/player.py",
  ///   "children": [ ... ]
  /// }
  /// ```
  factory EngineNode.fromJson(Map<String, dynamic> json) {
    final props = (json['properties'] as Map<String, dynamic>?) ?? {};

    final children = (json['children'] as List<dynamic>?)
            ?.map((c) => EngineNode.fromJson(c as Map<String, dynamic>))
            .toList() ??
        [];

    return EngineNode(
      name: (json['name'] as String?) ?? 'Unnamed',
      type: (json['type'] as String?) ?? 'Node2D',
      x: _toDouble(props['x']),
      y: _toDouble(props['y']),
      scaleX: _toDouble(props['scale_x'], fallback: 1.0),
      scaleY: _toDouble(props['scale_y'], fallback: 1.0),
      rotation: _toDouble(props['rotation']),
      resource: props['resource'] as String?,
      script: json['script'] as String?,
      children: children,
    );
  }

  /// Safely converts a JSON number (int or double) to a [double].
  static double _toDouble(dynamic value, {double fallback = 0.0}) {
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? fallback;
    return fallback;
  }
}

// ─────────────────────────────────────────────
// Dummy scene data for testing (fallback)
// ─────────────────────────────────────────────

/// Returns a sample scene tree with varied property values so the
/// Inspector shows different data when each node is selected.
EngineNode createDummyScene() {
  return EngineNode(
    name: 'Root',
    type: 'Node2D',
    x: 0,
    y: 0,
    children: [
      EngineNode(
        name: 'MainCamera',
        type: 'Camera2D',
        x: 640,
        y: 360,
        rotation: 0,
      ),
      EngineNode(
        name: 'Player',
        type: 'PhysicsBody2D',
        x: 120,
        y: 340,
        scaleX: 1.5,
        scaleY: 1.5,
        rotation: 0,
        children: [
          EngineNode(
            name: 'PlayerSprite',
            type: 'SpriteNode',
            x: 0,
            y: 0,
            scaleX: 2.0,
            scaleY: 2.0,
          ),
          EngineNode(
            name: 'PlayerCollider',
            type: 'Collider2D',
            x: 0,
            y: 8,
            scaleX: 1.0,
            scaleY: 1.0,
          ),
        ],
      ),
      EngineNode(
        name: 'Ground',
        type: 'TilemapNode',
        x: 0,
        y: 500,
        scaleX: 1.0,
        scaleY: 1.0,
        rotation: 0,
      ),
    ],
  );
}
