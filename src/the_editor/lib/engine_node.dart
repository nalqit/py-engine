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
    this.color,
    this.width,
    this.height,
    this.radius,
    this.texturePath,
    this.frameCount,
    this.frameSpeed,
    this.flipX,
    this.flipY,
    this.anchorX,
    this.anchorY,
    this.opacity,
    this.text,
    this.fontSize,
    this.fontColor,
    this.emission,
    this.lifetime,
    this.rate,
    this.layer,
    this.mask,
    this.gravity,
    this.velocityX,
    this.velocityY,
    this.isStatic,
    this.restitution,
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

  // ── Visual Properties ──
  final int? color;
  final double? width;
  final double? height;
  final double? radius;
  final String? texturePath;
  final int? frameCount;
  final double? frameSpeed;
  final bool? flipX;
  final bool? flipY;
  final double? anchorX;
  final double? anchorY;
  final double? opacity;

  // ── Text Properties ──
  final String? text;
  final double? fontSize;
  final int? fontColor;

  // ── Particle Properties ──
  final double? emission;
  final double? lifetime;
  final double? rate;

  // ── Physics Properties ──
  final String? layer;
  final String? mask;
  final double? gravity;
  final double? velocityX;
  final double? velocityY;
  final bool? isStatic;
  final double? restitution;

  bool get hasChildren => children.isNotEmpty;

  // ───────────────────────────────────────────
  // Node type utilities
  // ───────────────────────────────────────────

  static const Map<String, List<String>> nodeProperties = {
    'Node2D': ['x', 'y', 'scaleX', 'scaleY', 'rotation', 'visible'],
    'Camera2D': ['x', 'y', 'scaleX', 'scaleY', 'rotation'],
    'SpriteNode': ['x', 'y', 'scaleX', 'scaleY', 'rotation', 'texturePath', 'flipX', 'flipY', 'opacity'],
    'AnimatedSprite': ['x', 'y', 'scaleX', 'scaleY', 'texturePath', 'frameCount', 'frameSpeed', 'flipX', 'flipY'],
    'RectangleNode': ['x', 'y', 'scaleX', 'scaleY', 'rotation', 'color', 'width', 'height'],
    'CircleNode': ['x', 'y', 'scaleX', 'scaleY', 'color', 'radius'],
    'Collider2D': ['x', 'y', 'scaleX', 'scaleY', 'width', 'height', 'layer', 'mask', 'isStatic'],
    'PhysicsBody2D': ['x', 'y', 'scaleX', 'scaleY', 'gravity', 'velocityX', 'velocityY', 'restitution'],
    'TilemapNode': ['x', 'y', 'scaleX', 'scaleY', 'resource'],
    'Particles': ['x', 'y', 'texturePath', 'emission', 'lifetime', 'rate', 'color'],
    'LabelNode': ['x', 'y', 'text', 'fontSize', 'fontColor', 'anchorX', 'anchorY'],
  };

  static const Map<String, double> defaultSizes = {
    'SpriteNode': 48,
    'AnimatedSprite': 48,
    'RectangleNode': 32,
    'CircleNode': 24,
    'Collider2D': 36,
    'PhysicsBody2D': 56,
    'TilemapNode': 120,
    'LabelNode': 32,
    'Particles': 40,
  };

  static const Map<String, int> nodeColors = {
    'Node2D': 0xFF8BC34A,
    'Camera2D': 0xFF64B5F6,
    'SpriteNode': 0xFFBA68C8,
    'AnimatedSprite': 0xFFE91E63,
    'RectangleNode': 0xFF90A4AE,
    'CircleNode': 0xFF4DB6AC,
    'Collider2D': 0xFF4DD0E1,
    'PhysicsBody2D': 0xFFFF8A65,
    'TilemapNode': 0xFFFFD54F,
    'Particles': 0xFF00BCD4,
    'LabelNode': 0xFFCDDC39,
  };

  List<String> get availableProperties => nodeProperties[type] ?? nodeProperties['Node2D']!;

  // ───────────────────────────────────────────
  // JSON parsing
  // ───────────────────────────────────────────

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
      visible: props['visible'] ?? true,
      resource: props['resource'] as String?,
      script: json['script'] as String?,
      color: props['color'] as int?,
      width: _toDouble(props['width']),
      height: _toDouble(props['height']),
      radius: _toDouble(props['radius']),
      texturePath: props['texture_path'] as String?,
      frameCount: props['frame_count'] as int?,
      frameSpeed: _toDouble(props['frame_speed']),
      flipX: props['flip_x'] as bool?,
      flipY: props['flip_y'] as bool?,
      anchorX: _toDouble(props['anchor_x']),
      anchorY: _toDouble(props['anchor_y']),
      opacity: _toDouble(props['opacity'], fallback: 1.0),
      text: props['text'] as String?,
      fontSize: _toDouble(props['font_size']),
      fontColor: props['font_color'] as int?,
      emission: _toDouble(props['emission']),
      lifetime: _toDouble(props['lifetime']),
      rate: _toDouble(props['rate']),
      layer: props['layer'] as String?,
      mask: props['mask'] as String?,
      gravity: _toDouble(props['gravity']),
      velocityX: _toDouble(props['velocity_x']),
      velocityY: _toDouble(props['velocity_y']),
      isStatic: props['is_static'] as bool?,
      restitution: _toDouble(props['restitution']),
      children: children,
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> json = {
      'name': name,
      'type': type,
      'properties': {
        'x': x,
        'y': y,
        'scale_x': scaleX,
        'scale_y': scaleY,
        'rotation': rotation,
        'visible': visible,
      },
    };

    if (resource != null) (json['properties'] as Map)['resource'] = resource;
    if (color != null) (json['properties'] as Map)['color'] = color;
    if (width != null) (json['properties'] as Map)['width'] = width;
    if (height != null) (json['properties'] as Map)['height'] = height;
    if (radius != null) (json['properties'] as Map)['radius'] = radius;
    if (texturePath != null) (json['properties'] as Map)['texture_path'] = texturePath;
    if (flipX != null) (json['properties'] as Map)['flip_x'] = flipX;
    if (flipY != null) (json['properties'] as Map)['flip_y'] = flipY;
    if (opacity != null) (json['properties'] as Map)['opacity'] = opacity;
    if (text != null) (json['properties'] as Map)['text'] = text;
    if (fontSize != null) (json['properties'] as Map)['font_size'] = fontSize;
    if (layer != null) (json['properties'] as Map)['layer'] = layer;
    if (mask != null) (json['properties'] as Map)['mask'] = mask;
    if (isStatic != null) (json['properties'] as Map)['is_static'] = isStatic;
    if (script != null) json['script'] = script;
    if (children.isNotEmpty) {
      json['children'] = children.map((c) => c.toJson()).toList();
    }

    return json;
  }

  static double _toDouble(dynamic value, {double fallback = 0.0}) {
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? fallback;
    return fallback;
  }

  // ───────────────────────────────────────────
  // Editing
  // ───────────────────────────────────────────

  EngineNode copyWith({
    String? name,
    double? x,
    double? y,
    double? scaleX,
    double? scaleY,
    double? rotation,
    bool? visible,
  }) {
    final copy = EngineNode(
      name: name ?? this.name,
      type: type,
      x: x ?? this.x,
      y: y ?? this.y,
      scaleX: scaleX ?? this.scaleX,
      scaleY: scaleY ?? this.scaleY,
      rotation: rotation ?? this.rotation,
      visible: visible ?? this.visible,
      resource: resource,
      script: script,
      color: color,
      width: width,
      height: height,
      radius: radius,
      texturePath: texturePath,
      frameCount: frameCount,
      frameSpeed: frameSpeed,
      flipX: flipX,
      flipY: flipY,
      anchorX: anchorX,
      anchorY: anchorY,
      opacity: opacity,
      text: text,
      fontSize: fontSize,
      fontColor: fontColor,
      emission: emission,
      lifetime: lifetime,
      rate: rate,
      layer: layer,
      mask: mask,
      gravity: gravity,
      velocityX: velocityX,
      velocityY: velocityY,
      isStatic: isStatic,
      restitution: restitution,
    );
    copy.children.addAll(children);
    return copy;
  }
}

// ─────────────────────────────────────────────
// Supported node types for the editor
// ─────────────────────────────────────────────

class NodeTypes {
  static const List<String> all = [
    'Node2D',
    'Camera2D',
    'SpriteNode',
    'AnimatedSprite',
    'RectangleNode',
    'CircleNode',
    'Collider2D',
    'PhysicsBody2D',
    'TilemapNode',
    'Particles',
    'LabelNode',
  ];

  static const Map<String, String> descriptions = {
    'Node2D': 'Base 2D node container',
    'Camera2D': 'Viewport camera',
    'SpriteNode': 'Static image sprite',
    'AnimatedSprite': 'Animated sprite with frames',
    'RectangleNode': 'Rectangle shape',
    'CircleNode': 'Circle shape',
    'Collider2D': 'Collision box',
    'PhysicsBody2D': 'Physics-enabled body',
    'TilemapNode': 'Tile map from JSON',
    'Particles': 'Particle emitter',
    'LabelNode': 'Text label',
  };
}

// ─────────────────────────────────────────────
// Dummy scene data for testing (fallback)
// ─────────────────────────────────────────────

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
        gravity: 980,
        isStatic: false,
        children: [
          EngineNode(
            name: 'PlayerSprite',
            type: 'SpriteNode',
            x: 0,
            y: 0,
            scaleX: 2.0,
            scaleY: 2.0,
            texturePath: 'sprites/player.png',
          ),
          EngineNode(
            name: 'PlayerCollider',
            type: 'Collider2D',
            x: 0,
            y: 8,
            width: 32,
            height: 48,
            layer: 'player',
            mask: 'wall',
          ),
        ],
      ),
      EngineNode(
        name: 'Ground',
        type: 'TilemapNode',
        x: 0,
        y: 500,
        resource: 'maps/level1.json',
      ),
      EngineNode(
        name: 'Background',
        type: 'SpriteNode',
        x: 640,
        y: 360,
        scaleX: 2.0,
        scaleY: 2.0,
        texturePath: 'backgrounds/forest.png',
      ),
      EngineNode(
        name: 'ScoreLabel',
        type: 'LabelNode',
        x: 50,
        y: 50,
        text: 'Score: 0',
        fontSize: 24,
        fontColor: 0xFFFFFFFF,
      ),
    ],
  );
}