import 'package:flutter/material.dart';
import 'engine_node.dart';

/// Renders the PyEngine 2D scene hierarchy as an expandable/collapsible tree.
///
/// Each row shows an expand arrow (if the node has children), a type-based
/// icon, and the node name. Clicking a row selects it; clicking the arrow
/// toggles expansion.
class SceneTreeWidget extends StatefulWidget {
  const SceneTreeWidget({super.key});

  @override
  State<SceneTreeWidget> createState() => _SceneTreeWidgetState();
}

class _SceneTreeWidgetState extends State<SceneTreeWidget> {
  late final EngineNode _root;
  EngineNode? _selectedNode;

  @override
  void initState() {
    super.initState();
    _root = createDummyScene();
  }

  @override
  Widget build(BuildContext context) {
    // Flatten the visible tree into a list of (node, depth) pairs so we can
    // use a single ListView.builder for efficient rendering.
    final visible = <_TreeEntry>[];
    _collectVisible(_root, 0, visible);

    return ListView.builder(
      itemCount: visible.length,
      padding: const EdgeInsets.only(top: 4),
      itemExtent: 28, // fixed row height for snappy scrolling
      itemBuilder: (context, index) {
        final entry = visible[index];
        return _buildRow(entry.node, entry.depth);
      },
    );
  }

  // ───────────────────────────────────────────
  // Tree flattening
  // ───────────────────────────────────────────

  /// Recursively collects all nodes that should be visible (i.e. their
  /// ancestors are all expanded) into [out].
  void _collectVisible(EngineNode node, int depth, List<_TreeEntry> out) {
    out.add(_TreeEntry(node, depth));
    if (node.isExpanded) {
      for (final child in node.children) {
        _collectVisible(child, depth + 1, out);
      }
    }
  }

  // ───────────────────────────────────────────
  // Row widget
  // ───────────────────────────────────────────

  Widget _buildRow(EngineNode node, int depth) {
    final bool isSelected = identical(node, _selectedNode);
    const double indentPerLevel = 18.0;

    return GestureDetector(
      onTap: () => setState(() => _selectedNode = node),
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: Container(
          height: 28,
          color: isSelected ? const Color(0xFF37373D) : Colors.transparent,
          padding: EdgeInsets.only(left: 6 + depth * indentPerLevel),
          child: Row(
            children: [
              // ── Expand / collapse arrow ──
              _buildExpandArrow(node),

              const SizedBox(width: 4),

              // ── Type icon ──
              Icon(
                _iconForType(node.type),
                size: 15,
                color: _iconColorForType(node.type),
              ),

              const SizedBox(width: 6),

              // ── Node name ──
              Expanded(
                child: Text(
                  node.name,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12,
                    color: isSelected
                        ? const Color(0xFFE0E0E0)
                        : const Color(0xFFBBBBBB),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ───────────────────────────────────────────
  // Expand arrow
  // ───────────────────────────────────────────

  Widget _buildExpandArrow(EngineNode node) {
    if (!node.hasChildren) {
      // Reserve the same space so names stay aligned.
      return const SizedBox(width: 16);
    }

    return GestureDetector(
      onTap: () {
        setState(() => node.isExpanded = !node.isExpanded);
      },
      child: SizedBox(
        width: 16,
        height: 28,
        child: Center(
          child: Icon(
            node.isExpanded
                ? Icons.arrow_drop_down
                : Icons.arrow_right,
            size: 18,
            color: const Color(0xFF999999),
          ),
        ),
      ),
    );
  }

  // ───────────────────────────────────────────
  // Icon mapping
  // ───────────────────────────────────────────

  /// Maps an engine node type string to a Material icon.
  IconData _iconForType(String type) {
    return switch (type) {
      'Node2D'        => Icons.account_tree_outlined,
      'Camera2D'      => Icons.videocam_outlined,
      'SpriteNode'    => Icons.image_outlined,
      'PhysicsBody2D' => Icons.fitness_center,
      'Collider2D'    => Icons.crop_square_outlined,
      'TilemapNode'   => Icons.grid_view_outlined,
      _               => Icons.circle_outlined,
    };
  }

  /// Gives each node type a subtle distinguishing colour.
  Color _iconColorForType(String type) {
    return switch (type) {
      'Node2D'        => const Color(0xFF8BC34A), // green
      'Camera2D'      => const Color(0xFF64B5F6), // blue
      'SpriteNode'    => const Color(0xFFBA68C8), // purple
      'PhysicsBody2D' => const Color(0xFFFF8A65), // orange
      'Collider2D'    => const Color(0xFF4DD0E1), // cyan
      'TilemapNode'   => const Color(0xFFFFD54F), // amber
      _               => const Color(0xFF999999),
    };
  }
}

// ─────────────────────────────────────────────
// Helper class for the flattened visible tree
// ─────────────────────────────────────────────

class _TreeEntry {
  const _TreeEntry(this.node, this.depth);
  final EngineNode node;
  final int depth;
}
