/// Lightweight data model representing a node in the PyEngine 2D scene tree.
///
/// This mirrors the engine's node hierarchy. Each node has a [type] string
/// that maps to an engine class name (e.g. 'Node2D', 'SpriteNode') and an
/// ordered list of [children].
class EngineNode {
  EngineNode({
    required this.name,
    required this.type,
    List<EngineNode>? children,
    this.isExpanded = true,
  }) : children = children ?? [];

  final String name;
  final String type;
  final List<EngineNode> children;
  bool isExpanded;

  bool get hasChildren => children.isNotEmpty;
}

// ─────────────────────────────────────────────
// Dummy scene data for testing
// ─────────────────────────────────────────────

/// Returns a sample scene tree that exercises every supported node type.
EngineNode createDummyScene() {
  return EngineNode(
    name: 'Root',
    type: 'Node2D',
    children: [
      EngineNode(
        name: 'MainCamera',
        type: 'Camera2D',
      ),
      EngineNode(
        name: 'Player',
        type: 'PhysicsBody2D',
        children: [
          EngineNode(
            name: 'PlayerSprite',
            type: 'SpriteNode',
          ),
          EngineNode(
            name: 'PlayerCollider',
            type: 'Collider2D',
          ),
        ],
      ),
      EngineNode(
        name: 'Ground',
        type: 'TilemapNode',
      ),
    ],
  );
}
