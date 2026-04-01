import 'package:flutter/material.dart';
import 'engine_node.dart';

/// Renders the PyEngine 2D scene hierarchy as an expandable/collapsible tree.
///
/// Listens to [rootNodeNotifier] to react when a new scene is loaded,
/// and updates [selectedNodeNotifier] when the user taps a node.
class SceneTreeWidget extends StatefulWidget {
  const SceneTreeWidget({
    super.key,
    required this.rootNodeNotifier,
    required this.selectedNodeNotifier,
  });

  final ValueNotifier<EngineNode?> rootNodeNotifier;
  final ValueNotifier<EngineNode?> selectedNodeNotifier;

  @override
  State<SceneTreeWidget> createState() => _SceneTreeWidgetState();
}

class _SceneTreeWidgetState extends State<SceneTreeWidget> {
  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<EngineNode?>(
      valueListenable: widget.rootNodeNotifier,
      builder: (context, root, _) {
        if (root == null) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'No scene loaded.\nPaste a .scene file path\nand click "Load Scene".',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 11,
                  color: Color(0xFF555555),
                  height: 1.5,
                ),
              ),
            ),
          );
        }

        final visible = <_TreeEntry>[];
        _collectVisible(root, 0, visible);

        return ValueListenableBuilder<EngineNode?>(
          valueListenable: widget.selectedNodeNotifier,
          builder: (context, selectedNode, _) {
            return ListView.builder(
              itemCount: visible.length,
              padding: const EdgeInsets.only(top: 4),
              itemExtent: 28,
              itemBuilder: (context, index) {
                final entry = visible[index];
                return _buildRow(entry.node, entry.depth, selectedNode);
              },
            );
          },
        );
      },
    );
  }

  // ───────────────────────────────────────────
  // Tree flattening
  // ───────────────────────────────────────────

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

  Widget _buildRow(EngineNode node, int depth, EngineNode? selectedNode) {
    final bool isSelected = identical(node, selectedNode);
    const double indentPerLevel = 18.0;

    return GestureDetector(
      onTap: () {
        widget.selectedNodeNotifier.value = node;
      },
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        child: Container(
          height: 28,
          color: isSelected ? const Color(0xFF37373D) : Colors.transparent,
          padding: EdgeInsets.only(left: 6 + depth * indentPerLevel),
          child: Row(
            children: [
              _buildExpandArrow(node),
              const SizedBox(width: 4),
              Icon(
                _iconForType(node.type),
                size: 15,
                color: _iconColorForType(node.type),
              ),
              const SizedBox(width: 6),
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
            node.isExpanded ? Icons.arrow_drop_down : Icons.arrow_right,
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

  IconData _iconForType(String type) {
    return switch (type) {
      'Node2D'         => Icons.account_tree_outlined,
      'Camera2D'       => Icons.videocam_outlined,
      'SpriteNode'     => Icons.image_outlined,
      'PhysicsBody2D'  => Icons.fitness_center,
      'Collider2D'     => Icons.crop_square_outlined,
      'TilemapNode'    => Icons.grid_view_outlined,
      'RectangleNode'  => Icons.rectangle_outlined,
      _                => Icons.circle_outlined,
    };
  }

  Color _iconColorForType(String type) {
    return switch (type) {
      'Node2D'         => const Color(0xFF8BC34A),
      'Camera2D'       => const Color(0xFF64B5F6),
      'SpriteNode'     => const Color(0xFFBA68C8),
      'PhysicsBody2D'  => const Color(0xFFFF8A65),
      'Collider2D'     => const Color(0xFF4DD0E1),
      'TilemapNode'    => const Color(0xFFFFD54F),
      'RectangleNode'  => const Color(0xFF90A4AE),
      _                => const Color(0xFF999999),
    };
  }
}

class _TreeEntry {
  const _TreeEntry(this.node, this.depth);
  final EngineNode node;
  final int depth;
}
