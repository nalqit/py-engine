import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'engine_node.dart';
import 'scene_tree_widget.dart';
import 'inspector_widget.dart';
import 'viewport_widget.dart';
import 'bottom_panel_widget.dart';

/// The root IDE skeleton layout with resizable dock panels.
///
/// Layout topology:
///   ┌──────────────────────────────────────────────────┐
///   │        Toolbar (path field + Load Scene)         │
///   ├─────────┬─┬──────────────────┬─┬─────────────────┤
///   │  Scene  │▐│                  │▐│   Inspector     │
///   │  Tree   │▐│    Viewport      │▐│                 │
///   │         │▐│   (Expanded)     │▐│                 │
///   ├─────────┴─┴──────────────────┴─┴─────────────────┤
///   │         ═══ horizontal divider ═══               │
///   ├──────────────────────────────────────────────────┤
///   │          Asset Browser / Console                 │
///   └──────────────────────────────────────────────────┘
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

  // ── Scene data ──
  final ValueNotifier<EngineNode?> rootNodeNotifier = ValueNotifier(null);
  final ValueNotifier<EngineNode?> selectedNodeNotifier = ValueNotifier(null);
  final ValueNotifier<int> repaintNotifier = ValueNotifier(0);

  // ── Toolbar path input ──
  final TextEditingController _pathCtrl = TextEditingController();

  // ── Constraints ──
  static const double _minSideDockWidth = 100.0;
  static const double _maxSideDockWidth = 500.0;
  static const double _minBottomHeight = 80.0;
  static const double _maxBottomHeight = 500.0;
  static const double _dividerThickness = 5.0;
  static const double _toolbarHeight = 44.0;

  @override
  void dispose() {
    _pathCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          _buildToolbar(),
          Expanded(
            child: Column(
              children: [
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
                DragDivider(
                  axis: Axis.horizontal,
                  thickness: _dividerThickness,
                  onDrag: _onBottomDividerDrag,
                ),
                _buildBottomPanel(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ───────────────────────────────────────────
  // Scene file loading
  // ───────────────────────────────────────────

  void _loadScene() {
    final path = _pathCtrl.text.trim();
    if (path.isEmpty) {
      _showError('Please enter a file path.');
      return;
    }

    try {
      final file = File(path);
      if (!file.existsSync()) {
        _showError('File not found:\n$path');
        return;
      }

      final jsonString = file.readAsStringSync();
      final jsonMap = jsonDecode(jsonString) as Map<String, dynamic>;
      final root = EngineNode.fromJson(jsonMap);

      // Reset selection and load the new tree.
      selectedNodeNotifier.value = null;
      rootNodeNotifier.value = root;
      repaintNotifier.value++;

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Scene loaded: ${root.name} (${root.type})'),
            backgroundColor: const Color(0xFF2E7D32),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      _showError('Failed to load scene:\n$e');
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message, style: const TextStyle(fontSize: 12)),
        backgroundColor: const Color(0xFFC62828),
        duration: const Duration(seconds: 4),
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
      rightDockWidth = (rightDockWidth - dx).clamp(
        _minSideDockWidth,
        _maxSideDockWidth,
      );
    });
  }

  void _onBottomDividerDrag(double dy) {
    setState(() {
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
      child: Row(
        children: [
          // ── Brand ──
          const Text(
            'PyEngine 2D',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: Color(0xFFCCCCCC),
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(width: 20),

          // ── Separator ──
          Container(
            width: 1,
            height: 20,
            color: const Color(0xFF444444),
          ),
          const SizedBox(width: 12),

          // ── Path field ──
          const Icon(Icons.folder_open_outlined,
              size: 15, color: Color(0xFF888888)),
          const SizedBox(width: 6),
          SizedBox(
            width: 420,
            height: 28,
            child: TextField(
              controller: _pathCtrl,
              style:
                  const TextStyle(fontSize: 11, color: Color(0xFFDDDDDD)),
              cursorHeight: 13,
              cursorColor: const Color(0xFF64B5F6),
              onSubmitted: (_) => _loadScene(),
              decoration: InputDecoration(
                isDense: true,
                filled: true,
                fillColor: const Color(0xFF1E1E1E),
                hintText: 'Paste absolute path to .scene file…',
                hintStyle: const TextStyle(
                    fontSize: 11, color: Color(0xFF555555)),
                contentPadding: const EdgeInsets.symmetric(
                    horizontal: 8, vertical: 6),
                border: OutlineInputBorder(
                  borderSide: const BorderSide(
                      color: Color(0xFF3A3A3A), width: 1),
                  borderRadius: BorderRadius.circular(4),
                ),
                enabledBorder: OutlineInputBorder(
                  borderSide: const BorderSide(
                      color: Color(0xFF3A3A3A), width: 1),
                  borderRadius: BorderRadius.circular(4),
                ),
                focusedBorder: OutlineInputBorder(
                  borderSide: const BorderSide(
                      color: Color(0xFF64B5F6), width: 1),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),

          // ── Load button ──
          SizedBox(
            height: 28,
            child: ElevatedButton.icon(
              onPressed: _loadScene,
              icon: const Icon(Icons.play_arrow_rounded, size: 15),
              label: const Text('Load Scene',
                  style: TextStyle(fontSize: 11)),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2E7D32),
                foregroundColor: Colors.white,
                padding:
                    const EdgeInsets.symmetric(horizontal: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
            ),
          ),

          const Spacer(),

          // ── Menu labels ──
          const Text('File',
              style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
          const SizedBox(width: 16),
          const Text('Edit',
              style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
          const SizedBox(width: 16),
          const Text('Scene',
              style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
          const SizedBox(width: 16),
          const Text('Help',
              style: TextStyle(fontSize: 12, color: Color(0xFF999999))),
        ],
      ),
    );
  }

  Widget _buildSceneTree() {
    return SizedBox(
      width: leftDockWidth,
      child: Container(
        color: const Color(0xFF252526),
        child: Column(
          children: [
            const _DockHeader(label: 'Scene Tree'),
            Expanded(
              child: SceneTreeWidget(
                rootNodeNotifier: rootNodeNotifier,
                selectedNodeNotifier: selectedNodeNotifier,
              ),
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
        child: ViewportWidget(
          rootNodeNotifier: rootNodeNotifier,
          selectedNodeNotifier: selectedNodeNotifier,
          repaintNotifier: repaintNotifier,
        ),
      ),
    );
  }

  Widget _buildInspector() {
    return SizedBox(
      width: rightDockWidth,
      child: Container(
        color: const Color(0xFF252526),
        child: Column(
          children: [
            const _DockHeader(label: 'Inspector'),
            Expanded(
              child: InspectorWidget(
                selectedNodeNotifier: selectedNodeNotifier,
                repaintNotifier: repaintNotifier,
              ),
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
        child: const BottomPanelWidget(),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// DragDivider
// ─────────────────────────────────────────────

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
  static const Color _hoverColor = Color(0xFF007ACC);
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
          width: widget.axis == Axis.vertical
              ? widget.thickness
              : double.infinity,
          height: widget.axis == Axis.horizontal
              ? widget.thickness
              : double.infinity,
          color: _currentColor,
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Shared dock header
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
