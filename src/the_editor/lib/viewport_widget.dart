import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'engine_node.dart';

// ─────────────────────────────────────────────
// Shared type → visual helpers (used by both
// the painter and the hit-testing logic)
// ─────────────────────────────────────────────

double _baseSizeForType(String type) {
  return switch (type) {
    'Node2D'         => 24,
    'Camera2D'       => 60,
    'SpriteNode'     => 48,
    'PhysicsBody2D'  => 56,
    'Collider2D'     => 36,
    'TilemapNode'    => 120,
    'RectangleNode'  => 32,
    _                => 32,
  };
}

Color _colorForType(String type) {
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

/// Canvas origin — (0,0) in world space maps to this point on the
/// 4000×4000 internal canvas.
const Offset _canvasOrigin = Offset(2000, 2000);

// ─────────────────────────────────────────────
// Interaction mode enum
// ─────────────────────────────────────────────

enum _InteractionMode { none, panning, dragging }

// ─────────────────────────────────────────────
// ViewportWidget
// ─────────────────────────────────────────────

/// An interactive 2D viewport that renders the scene tree onto a pannable,
/// zoomable canvas.  Supports:
/// • **Scroll-to-zoom** via [InteractiveViewer]
/// • **Click-to-select** nodes (updates [selectedNodeNotifier])
/// • **Drag-to-move** selected nodes (updates X/Y + repaints)
/// • **Drag empty space to pan** the camera
class ViewportWidget extends StatefulWidget {
  const ViewportWidget({
    super.key,
    required this.rootNodeNotifier,
    required this.selectedNodeNotifier,
    required this.repaintNotifier,
  });

  final ValueNotifier<EngineNode?> rootNodeNotifier;
  final ValueNotifier<EngineNode?> selectedNodeNotifier;
  final ValueNotifier<int> repaintNotifier;

  @override
  State<ViewportWidget> createState() => _ViewportWidgetState();
}

class _ViewportWidgetState extends State<ViewportWidget> {
  final TransformationController _transformCtrl = TransformationController();
  final GlobalKey _viewportKey = GlobalKey();

  _InteractionMode _mode = _InteractionMode.none;
  EngineNode? _draggingNode;
  int _spawnCounter = 0;

  @override
  void dispose() {
    _transformCtrl.dispose();
    super.dispose();
  }

  // ───────────────────────────────────────────
  // Coordinate helpers
  // ───────────────────────────────────────────

  /// Convert a widget-local position (from a pointer event) into the
  /// internal 4000×4000 canvas position by applying the inverse of the
  /// current [InteractiveViewer] transform.
  Offset _widgetToCanvas(Offset widgetPos) {
    final inverse = _transformCtrl.value.clone()..invert();
    // Apply the 4×4 matrix manually (avoids importing vector_math).
    final x = inverse.entry(0, 0) * widgetPos.dx +
        inverse.entry(0, 1) * widgetPos.dy +
        inverse.entry(0, 3);
    final y = inverse.entry(1, 0) * widgetPos.dx +
        inverse.entry(1, 1) * widgetPos.dy +
        inverse.entry(1, 3);
    return Offset(x, y);
  }

  double _currentZoom() => _transformCtrl.value.getMaxScaleOnAxis();

  // ───────────────────────────────────────────
  // Hit testing
  // ───────────────────────────────────────────

  /// Walk the entire node tree in draw-order (depth-first) and return
  /// the **topmost** node whose bounding rect contains [canvasPos].
  EngineNode? _hitTest(Offset canvasPos) {
    final root = widget.rootNodeNotifier.value;
    if (root == null) return null;

    // Collect in draw order (parent first, then children).
    final nodes = <EngineNode>[];
    _collectNodes(root, nodes);

    // Iterate in reverse so the last-drawn (topmost) node wins.
    for (int i = nodes.length - 1; i >= 0; i--) {
      if (_nodeRect(nodes[i]).contains(canvasPos)) {
        return nodes[i];
      }
    }
    return null;
  }

  void _collectNodes(EngineNode node, List<EngineNode> out) {
    out.add(node);
    for (final child in node.children) {
      _collectNodes(child, out);
    }
  }

  /// Bounding rect for a node on the internal canvas.
  Rect _nodeRect(EngineNode node) {
    final base = _baseSizeForType(node.type);
    return Rect.fromCenter(
      center: _canvasOrigin + Offset(node.x, node.y),
      width: base * node.scaleX,
      height: base * node.scaleY,
    );
  }

  // ───────────────────────────────────────────
  // Pointer event handlers
  // ───────────────────────────────────────────
  //
  // We disable InteractiveViewer's built-in panning (panEnabled: false)
  // and handle all pointer interactions manually.  This avoids any
  // gesture-arena conflict between node-dragging and camera-panning.
  //
  // Scroll-to-zoom is still handled by InteractiveViewer internally
  // via PointerSignalEvent, which is independent of panEnabled.

  void _handlePointerDown(PointerDownEvent event) {
    final canvasPos = _widgetToCanvas(event.localPosition);
    final hit = _hitTest(canvasPos);

    if (hit != null) {
      // Tapped on a node → select it and start dragging.
      setState(() {
        _mode = _InteractionMode.dragging;
        _draggingNode = hit;
      });
      widget.selectedNodeNotifier.value = hit;
    } else {
      // Tapped empty space → start panning the camera.
      setState(() => _mode = _InteractionMode.panning);
    }
  }

  void _handlePointerMove(PointerMoveEvent event) {
    switch (_mode) {
      case _InteractionMode.dragging:
        if (_draggingNode == null) return;
        final zoom = _currentZoom();
        _draggingNode!.x += event.delta.dx / zoom;
        _draggingNode!.y += event.delta.dy / zoom;
        // Trigger viewport repaint AND Inspector sync.
        widget.repaintNotifier.value++;
        break;

      case _InteractionMode.panning:
        // Manually translate the InteractiveViewer transform in
        // screen-space (add delta directly to the translation column).
        final m = _transformCtrl.value.clone();
        m.setEntry(0, 3, m.entry(0, 3) + event.delta.dx);
        m.setEntry(1, 3, m.entry(1, 3) + event.delta.dy);
        _transformCtrl.value = m;
        break;

      case _InteractionMode.none:
        break;
    }
  }

  void _handlePointerUp(PointerUpEvent event) {
    if (_mode != _InteractionMode.none) {
      setState(() {
        _mode = _InteractionMode.none;
        _draggingNode = null;
      });
    }
  }

  // ───────────────────────────────────────────
  // Build
  // ───────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return ClipRect(
      key: _viewportKey,
      child: ValueListenableBuilder<EngineNode?>(
        valueListenable: widget.rootNodeNotifier,
        builder: (context, root, _) {
          if (root == null) {
            return DragTarget<String>(
              onAcceptWithDetails: (_) {},
              builder: (context, candidateData, rejectedData) {
                return Center(
                  child: Text(
                    candidateData.isNotEmpty
                        ? 'Load a scene first before\ndropping assets.'
                        : 'No scene loaded.\nLoad a .scene file to visualize nodes.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 12,
                      color: candidateData.isNotEmpty
                          ? const Color(0xFFFF9800)
                          : const Color(0xFF555555),
                    ),
                  ),
                );
              },
            );
          }

          return DragTarget<String>(
            onAcceptWithDetails: (details) =>
                _handleAssetDrop(details, root),
            builder: (context, candidateData, rejectedData) {
              return Stack(
                children: [
                  MouseRegion(
                    cursor: switch (_mode) {
                      _InteractionMode.dragging  => SystemMouseCursors.move,
                      _InteractionMode.panning   => SystemMouseCursors.grabbing,
                      _InteractionMode.none      => SystemMouseCursors.basic,
                    },
                    child: Listener(
                      onPointerDown: _handlePointerDown,
                      onPointerMove: _handlePointerMove,
                      onPointerUp: _handlePointerUp,
                      child: InteractiveViewer(
                        transformationController: _transformCtrl,
                        boundaryMargin: const EdgeInsets.all(double.infinity),
                        minScale: 0.1,
                        maxScale: 5.0,
                        panEnabled: false,
                        scaleEnabled: true,
                        child: SizedBox(
                          width: 4000,
                          height: 4000,
                          child: ValueListenableBuilder<EngineNode?>(
                            valueListenable: widget.selectedNodeNotifier,
                            builder: (context, selectedNode, _) {
                              return ValueListenableBuilder<int>(
                                valueListenable: widget.repaintNotifier,
                                builder: (context, _, __) {
                                  return CustomPaint(
                                    size: const Size(4000, 4000),
                                    painter: _ViewportPainter(
                                      root: root,
                                      selectedNode: selectedNode,
                                    ),
                                  );
                                },
                              );
                            },
                          ),
                        ),
                      ),
                    ),
                  ),

                  // ── Drop highlight overlay ──
                  if (candidateData.isNotEmpty)
                    Positioned.fill(
                      child: IgnorePointer(
                        child: Container(
                          decoration: BoxDecoration(
                            border: Border.all(
                              color: const Color(0xFF64B5F6),
                              width: 2,
                            ),
                            color: const Color(0x1064B5F6),
                          ),
                        ),
                      ),
                    ),
                ],
              );
            },
          );
        },
      ),
    );
  }

  // ───────────────────────────────────────────
  // Drop handler — spawns a new node
  // ───────────────────────────────────────────

  void _handleAssetDrop(DragTargetDetails<String> details, EngineNode root) {
    final assetPath = details.data;

    // 1. Convert the global drop offset to viewport-local coordinates.
    final renderBox =
        _viewportKey.currentContext?.findRenderObject() as RenderBox?;
    if (renderBox == null) return;
    final localPos = renderBox.globalToLocal(details.offset);

    // 2. Convert viewport-local to internal 4000×4000 canvas coordinates.
    final canvasPos = _widgetToCanvas(localPos);

    // 3. Convert canvas coordinates to world coordinates.
    final worldX = canvasPos.dx - _canvasOrigin.dx;
    final worldY = canvasPos.dy - _canvasOrigin.dy;

    // 4. Determine the node type from the file extension.
    final ext = assetPath.split('.').last.toLowerCase();
    final String nodeType;
    final String baseName;
    switch (ext) {
      case 'png' || 'jpg' || 'jpeg' || 'bmp' || 'webp':
        nodeType = 'SpriteNode';
        baseName = assetPath.split('/').last.split('.').first;
        break;
      case 'scene':
        nodeType = 'Node2D';
        baseName = assetPath.split('/').last.split('.').first;
        break;
      default:
        nodeType = 'Node2D';
        baseName = 'NewNode';
    }

    _spawnCounter++;
    final newNode = EngineNode(
      name: '$baseName\_$_spawnCounter',
      type: nodeType,
      x: worldX,
      y: worldY,
      resource: ext == 'scene' ? null : assetPath,
    );

    // 5. Add to the selected node (if it exists) or the scene root.
    final parent = widget.selectedNodeNotifier.value ?? root;
    parent.children.add(newNode);

    // 6. Re-trigger rootNodeNotifier to rebuild the Scene Tree.
    //    Assigning the same reference doesn't fire listeners, so we
    //    null it briefly and then set it back.
    widget.rootNodeNotifier.value = null;
    widget.rootNodeNotifier.value = root;

    // 7. Auto-select the new node.
    widget.selectedNodeNotifier.value = newNode;
    widget.repaintNotifier.value++;
  }
}

// ─────────────────────────────────────────────
// Custom painter — draws grid, nodes, gizmos
// ─────────────────────────────────────────────

class _ViewportPainter extends CustomPainter {
  _ViewportPainter({
    required this.root,
    required this.selectedNode,
  });

  final EngineNode root;
  final EngineNode? selectedNode;

  @override
  void paint(Canvas canvas, Size size) {
    _drawGrid(canvas, size);
    _drawOriginCross(canvas);
    _drawNodeTree(canvas, root);
  }

  @override
  bool shouldRepaint(covariant _ViewportPainter old) => true;

  // ───────────────────────────────────────────
  // Background grid
  // ───────────────────────────────────────────

  void _drawGrid(Canvas canvas, Size size) {
    const double step = 50;
    final paint = Paint()
      ..color = const Color(0xFF1F1F1F)
      ..strokeWidth = 0.5;

    for (double x = 0; x <= size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y <= size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }

    final majorPaint = Paint()
      ..color = const Color(0xFF2A2A2A)
      ..strokeWidth = 1.0;

    for (double x = 0; x <= size.width; x += 200) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), majorPaint);
    }
    for (double y = 0; y <= size.height; y += 200) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), majorPaint);
    }
  }

  // ───────────────────────────────────────────
  // Origin crosshair (0,0)
  // ───────────────────────────────────────────

  void _drawOriginCross(Canvas canvas) {
    const double len = 30;
    canvas.drawLine(
      _canvasOrigin - const Offset(len, 0),
      _canvasOrigin + const Offset(len, 0),
      Paint()
        ..color = const Color(0xAAE06666)
        ..strokeWidth = 1.5,
    );
    canvas.drawLine(
      _canvasOrigin - const Offset(0, len),
      _canvasOrigin + const Offset(0, len),
      Paint()
        ..color = const Color(0xAA6EA86E)
        ..strokeWidth = 1.5,
    );
    canvas.drawCircle(
      _canvasOrigin,
      3,
      Paint()..color = const Color(0xFFCCCCCC),
    );
  }

  // ───────────────────────────────────────────
  // Recursive node drawing
  // ───────────────────────────────────────────

  void _drawNodeTree(Canvas canvas, EngineNode node) {
    _drawNode(canvas, node);
    for (final child in node.children) {
      _drawNodeTree(canvas, child);
    }
  }

  void _drawNode(Canvas canvas, EngineNode node) {
    final double baseW = _baseSizeForType(node.type);
    final double baseH = baseW;
    final double w = baseW * node.scaleX;
    final double h = baseH * node.scaleY;

    final rect = Rect.fromCenter(
      center: _canvasOrigin + Offset(node.x, node.y),
      width: w,
      height: h,
    );

    canvas.save();
    canvas.translate(rect.center.dx, rect.center.dy);
    canvas.rotate(node.rotation * math.pi / 180);
    canvas.translate(-rect.center.dx, -rect.center.dy);

    final color = _colorForType(node.type);
    canvas.drawRRect(
      RRect.fromRectAndRadius(rect, const Radius.circular(3)),
      Paint()..color = color.withAlpha(60),
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(rect, const Radius.circular(3)),
      Paint()
        ..color = color.withAlpha(140)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5,
    );

    // ── Selection gizmo ──
    final bool isSelected = identical(node, selectedNode);
    if (isSelected) {
      final gizmoRect = rect.inflate(4);
      canvas.drawRRect(
        RRect.fromRectAndRadius(gizmoRect, const Radius.circular(5)),
        Paint()
          ..color = const Color(0xFFFF9800)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0,
      );
      const double hs = 5;
      final hp = Paint()..color = const Color(0xFFFF9800);
      for (final c in [
        gizmoRect.topLeft,
        gizmoRect.topRight,
        gizmoRect.bottomLeft,
        gizmoRect.bottomRight,
      ]) {
        canvas.drawRect(
          Rect.fromCenter(center: c, width: hs, height: hs),
          hp,
        );
      }
    }

    // ── Label ──
    final tp = TextPainter(
      text: TextSpan(
        text: node.name,
        style: TextStyle(
          fontSize: 10,
          color: isSelected
              ? const Color(0xFFFF9800)
              : const Color(0xFF888888),
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();

    tp.paint(
      canvas,
      Offset(rect.center.dx - tp.width / 2, rect.bottom + 6),
    );

    canvas.restore();
  }
}
