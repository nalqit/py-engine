import 'package:flutter/material.dart';
import 'scene_tree_widget.dart';
import 'inspector_widget.dart';

/// The root IDE skeleton layout with resizable dock panels.
///
/// Layout topology:
///   ┌──────────────────────────────────────────────────┐
///   │                   Toolbar (40px)                  │
///   ├─────────┬─┬──────────────────┬─┬─────────────────┤
///   │  Scene  │▐│                  │▐│   Inspector     │
///   │  Tree   │▐│    Viewport      │▐│                 │
///   │         │▐│   (Expanded)     │▐│                 │
///   ├─────────┴─┴──────────────────┴─┴─────────────────┤
///   │         ═══ horizontal divider ═══               │
///   ├──────────────────────────────────────────────────┤
///   │          Asset Browser / Console                 │
///   └──────────────────────────────────────────────────┘
///
///   ▐ = vertical [DragDivider]
///   ═ = horizontal [DragDivider]
class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  // ── Resizable dock sizes ──
  double leftDockWidth = 250.0;
  double rightDockWidth = 300.0;
  double bottomDockHeight = 200.0;

  // ── Constraints ──
  static const double _minSideDockWidth = 100.0;
  static const double _maxSideDockWidth = 500.0;
  static const double _minBottomHeight = 80.0;
  static const double _maxBottomHeight = 500.0;
  static const double _dividerThickness = 5.0;
  static const double _toolbarHeight = 40.0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // ── Top: Toolbar / Menu Bar ──
          _buildToolbar(),

          // ── Middle row + bottom panel ──
          Expanded(
            child: Column(
              children: [
                // ── Scene Tree | divider | Viewport | divider | Inspector ──
                Expanded(
                  child: Row(
                    children: [
                      _buildSceneTree(),
                      DragDivider(
                        axis: Axis.vertical,
                        thickness: _dividerThickness,
                        onDrag: _onLeftDividerDrag,
                      ),
                      _buildViewport(),
                      DragDivider(
                        axis: Axis.vertical,
                        thickness: _dividerThickness,
                        onDrag: _onRightDividerDrag,
                      ),
                      _buildInspector(),
                    ],
                  ),
                ),

                // ── Horizontal divider ──
                DragDivider(
                  axis: Axis.horizontal,
                  thickness: _dividerThickness,
                  onDrag: _onBottomDividerDrag,
                ),

                // ── Bottom: Asset Browser / Console ──
                _buildBottomPanel(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ───────────────────────────────────────────
  // Drag callbacks
  // ───────────────────────────────────────────

  void _onLeftDividerDrag(double dx) {
    setState(() {
      leftDockWidth = (leftDockWidth + dx).clamp(
        _minSideDockWidth,
        _maxSideDockWidth,
      );
    });
  }

  void _onRightDividerDrag(double dx) {
    setState(() {
      // Dragging right‐side divider to the right → shrink inspector
      rightDockWidth = (rightDockWidth - dx).clamp(
        _minSideDockWidth,
        _maxSideDockWidth,
      );
    });
  }

  void _onBottomDividerDrag(double dy) {
    setState(() {
      // Dragging down → grow bottom panel
      bottomDockHeight = (bottomDockHeight - dy).clamp(
        _minBottomHeight,
        _maxBottomHeight,
      );
    });
  }

  // ───────────────────────────────────────────
  // Dock builders
  // ───────────────────────────────────────────

  Widget _buildToolbar() {
    return Container(
      height: _toolbarHeight,
      color: const Color(0xFF2B2B2B),
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: const Row(
        children: [
          Text(
            'PyEngine 2D',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: Color(0xFFCCCCCC),
              letterSpacing: 0.5,
            ),
          ),
          SizedBox(width: 24),
          Text('File', style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
          SizedBox(width: 16),
          Text('Edit', style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
          SizedBox(width: 16),
          Text('Scene', style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
          SizedBox(width: 16),
          Text('Project', style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
          SizedBox(width: 16),
          Text('Help', style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
        ],
      ),
    );
  }

  Widget _buildSceneTree() {
    return SizedBox(
      width: leftDockWidth,
      child: Container(
        color: const Color(0xFF252526),
        child: const Column(
          children: [
            _DockHeader(label: 'Scene Tree'),
            Expanded(
              child: SceneTreeWidget(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildViewport() {
    return Expanded(
      child: Container(
        color: const Color(0xFF1E1E1E),
        child: const Center(
          child: Text(
            'Viewport\nPlaceholder',
            textAlign: TextAlign.center,
            style: TextStyle(color: Color(0xFF555555), fontSize: 16),
          ),
        ),
      ),
    );
  }

  Widget _buildInspector() {
    return SizedBox(
      width: rightDockWidth,
      child: Container(
        color: const Color(0xFF252526),
        child: const Column(
          children: [
            _DockHeader(label: 'Inspector'),
            Expanded(
              child: InspectorWidget(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomPanel() {
    return SizedBox(
      height: bottomDockHeight,
      child: Container(
        color: const Color(0xFF1F1F1F),
        child: const Column(
          children: [
            _DockHeader(label: 'Asset Browser / Console'),
            Expanded(
              child: Center(
                child: Text(
                  'Asset Browser / Console\nPlaceholder',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Color(0xFF6A6A6A), fontSize: 13),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// DragDivider — a thin, draggable splitter bar
// ─────────────────────────────────────────────

/// A thin bar placed between two dock regions that can be dragged to resize
/// the neighbouring panels.
///
/// [axis] controls the orientation:
///   • [Axis.vertical]   → a narrow **vertical** bar (resizes left / right).
///   • [Axis.horizontal] → a narrow **horizontal** bar (resizes top / bottom).
///
/// [onDrag] fires on every drag‐update frame with the primary‐axis delta
/// (dx for vertical, dy for horizontal).
class DragDivider extends StatefulWidget {
  const DragDivider({
    super.key,
    required this.axis,
    required this.onDrag,
    this.thickness = 5.0,
  });

  final Axis axis;
  final ValueChanged<double> onDrag;
  final double thickness;

  @override
  State<DragDivider> createState() => _DragDividerState();
}

class _DragDividerState extends State<DragDivider> {
  bool _isHovered = false;
  bool _isDragging = false;

  static const Color _defaultColor = Color(0xFF2A2A2A);
  static const Color _hoverColor = Color(0xFF007ACC); // VS Code blue accent
  static const Color _dragColor = Color(0xFF1A9FFF);

  Color get _currentColor {
    if (_isDragging) return _dragColor;
    if (_isHovered) return _hoverColor;
    return _defaultColor;
  }

  MouseCursor get _cursor {
    return widget.axis == Axis.vertical
        ? SystemMouseCursors.resizeLeftRight
        : SystemMouseCursors.resizeUpDown;
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: _cursor,
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onPanStart: (_) => setState(() => _isDragging = true),
        onPanEnd: (_) => setState(() => _isDragging = false),
        onPanCancel: () => setState(() => _isDragging = false),
        onPanUpdate: (details) {
          if (widget.axis == Axis.vertical) {
            widget.onDrag(details.delta.dx);
          } else {
            widget.onDrag(details.delta.dy);
          }
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 120),
          width: widget.axis == Axis.vertical ? widget.thickness : double.infinity,
          height: widget.axis == Axis.horizontal ? widget.thickness : double.infinity,
          color: _currentColor,
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Shared dock header widget
// ─────────────────────────────────────────────

class _DockHeader extends StatelessWidget {
  const _DockHeader({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 28,
      width: double.infinity,
      color: const Color(0xFF333333),
      alignment: Alignment.centerLeft,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          color: Color(0xFFAAAAAA),
          letterSpacing: 0.3,
        ),
      ),
    );
  }
}
