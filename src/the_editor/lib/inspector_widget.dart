import 'package:flutter/material.dart';
import 'engine_node.dart';

/// A Godot-style property inspector that dynamically displays the properties
/// of the currently selected [EngineNode].
///
/// Listens to [selectedNodeNotifier] and rebuilds whenever the selection
/// changes. Edits in the text fields write back to the node object.
class InspectorWidget extends StatelessWidget {
  const InspectorWidget({
    super.key,
    required this.selectedNodeNotifier,
    required this.repaintNotifier,
  });

  final ValueNotifier<EngineNode?> selectedNodeNotifier;
  final ValueNotifier<int> repaintNotifier;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<EngineNode?>(
      valueListenable: selectedNodeNotifier,
      builder: (context, node, _) {
        if (node == null) {
          return const Center(
            child: Text(
              'Select a node to\nedit its properties',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                color: Color(0xFF555555),
              ),
            ),
          );
        }
        return _InspectorBody(
          key: ValueKey(node.name + node.type),
          node: node,
          notifier: selectedNodeNotifier,
          repaintNotifier: repaintNotifier,
        );
      },
    );
  }
}

// ─────────────────────────────────────────────
// Inner stateful body (owns TextEditingControllers)
// ─────────────────────────────────────────────

class _InspectorBody extends StatefulWidget {
  const _InspectorBody({
    super.key,
    required this.node,
    required this.notifier,
    required this.repaintNotifier,
  });

  final EngineNode node;
  final ValueNotifier<EngineNode?> notifier;
  final ValueNotifier<int> repaintNotifier;

  @override
  State<_InspectorBody> createState() => _InspectorBodyState();
}

class _InspectorBodyState extends State<_InspectorBody> {
  late final TextEditingController _nameCtrl;
  late final TextEditingController _posXCtrl;
  late final TextEditingController _posYCtrl;
  late final TextEditingController _scaleXCtrl;
  late final TextEditingController _scaleYCtrl;
  late final TextEditingController _rotCtrl;

  late double _rotation;
  late bool _visible;

  /// Guard flag — true while we're programmatically updating controllers
  /// from an external source (viewport drag). Prevents the controller
  /// listeners from re-writing the same values back and bumping the
  /// repaint notifier again.
  bool _isUpdatingFromExternal = false;

  EngineNode get _node => widget.node;

  @override
  void initState() {
    super.initState();
    _nameCtrl   = TextEditingController(text: _node.name);
    _posXCtrl   = TextEditingController(text: _node.x.toStringAsFixed(1));
    _posYCtrl   = TextEditingController(text: _node.y.toStringAsFixed(1));
    _scaleXCtrl = TextEditingController(text: _node.scaleX.toStringAsFixed(1));
    _scaleYCtrl = TextEditingController(text: _node.scaleY.toStringAsFixed(1));
    _rotCtrl    = TextEditingController(text: _node.rotation.toStringAsFixed(1));
    _rotation   = _node.rotation;
    _visible    = _node.visible;

    // Two-way binding: text field edits → node properties → viewport repaint.
    _nameCtrl.addListener(_onPropertyChanged);
    _posXCtrl.addListener(_onPropertyChanged);
    _posYCtrl.addListener(_onPropertyChanged);
    _scaleXCtrl.addListener(_onPropertyChanged);
    _scaleYCtrl.addListener(_onPropertyChanged);
    _rotCtrl.addListener(_onPropertyChanged);

    // Listen for external property changes (e.g. viewport node dragging)
    // so we can refresh the text fields in real-time.
    widget.repaintNotifier.addListener(_onExternalPropertyChange);
  }

  /// Called when the viewport (or another source) bumps [repaintNotifier].
  /// Reads the current node values and updates the text controllers.
  void _onExternalPropertyChange() {
    if (!mounted || _isUpdatingFromExternal) return;
    _isUpdatingFromExternal = true;

    _posXCtrl.text   = _node.x.toStringAsFixed(1);
    _posYCtrl.text   = _node.y.toStringAsFixed(1);
    _scaleXCtrl.text = _node.scaleX.toStringAsFixed(1);
    _scaleYCtrl.text = _node.scaleY.toStringAsFixed(1);
    _rotCtrl.text    = _node.rotation.toStringAsFixed(1);

    setState(() {
      _rotation = _node.rotation;
      _visible  = _node.visible;
    });

    _isUpdatingFromExternal = false;
  }

  void _onPropertyChanged() {
    if (_isUpdatingFromExternal) return;
    _node.name     = _nameCtrl.text;
    _node.x        = double.tryParse(_posXCtrl.text) ?? _node.x;
    _node.y        = double.tryParse(_posYCtrl.text) ?? _node.y;
    _node.scaleX   = double.tryParse(_scaleXCtrl.text) ?? _node.scaleX;
    _node.scaleY   = double.tryParse(_scaleYCtrl.text) ?? _node.scaleY;
    _node.rotation = double.tryParse(_rotCtrl.text) ?? _node.rotation;
    widget.repaintNotifier.value++;
  }

  @override
  void dispose() {
    widget.repaintNotifier.removeListener(_onExternalPropertyChange);
    _nameCtrl.dispose();
    _posXCtrl.dispose();
    _posYCtrl.dispose();
    _scaleXCtrl.dispose();
    _scaleYCtrl.dispose();
    _rotCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildNodeHeader(),
          const _Separator(),
          _buildPropertyRow('Name', Expanded(child: _compactField(_nameCtrl))),
          const SizedBox(height: 4),
          const _Separator(),
          _buildSection(
            title: 'Transform',
            icon: Icons.open_with_rounded,
            initiallyExpanded: true,
            children: [
              _buildVectorRow('Position', _posXCtrl, _posYCtrl),
              const SizedBox(height: 6),
              _buildVectorRow('Scale', _scaleXCtrl, _scaleYCtrl),
              const SizedBox(height: 6),
              _buildRotationRow(),
            ],
          ),
          const _Separator(),
          _buildSection(
            title: 'Visibility',
            icon: Icons.visibility_outlined,
            initiallyExpanded: true,
            children: [
              _buildSwitchRow('Visible', _visible, (v) {
                setState(() {
                  _visible = v;
                  _node.visible = v;
                });
                widget.repaintNotifier.value++;
              }),
              const SizedBox(height: 6),
              _buildColorRow('Modulate', Colors.white),
            ],
          ),
        ],
      ),
    );
  }

  // ───────────────────────────────────────────
  // Header
  // ───────────────────────────────────────────

  Widget _buildNodeHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      child: Row(
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: const Color(0xFF3C3C3C),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Icon(
              _iconForType(_node.type),
              size: 15,
              color: _iconColorForType(_node.type),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            _node.type,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: Color(0xFFDDDDDD),
            ),
          ),
        ],
      ),
    );
  }

  // ───────────────────────────────────────────
  // Collapsible section
  // ───────────────────────────────────────────

  Widget _buildSection({
    required String title,
    required IconData icon,
    required bool initiallyExpanded,
    required List<Widget> children,
  }) {
    return Theme(
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        initiallyExpanded: initiallyExpanded,
        tilePadding: const EdgeInsets.symmetric(horizontal: 10),
        childrenPadding: const EdgeInsets.only(left: 10, right: 10, bottom: 8),
        dense: true,
        visualDensity: VisualDensity.compact,
        collapsedIconColor: const Color(0xFF888888),
        iconColor: const Color(0xFF888888),
        title: Row(
          children: [
            Icon(icon, size: 14, color: const Color(0xFF888888)),
            const SizedBox(width: 6),
            Text(
              title,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: Color(0xFFAAAAAA),
                letterSpacing: 0.4,
              ),
            ),
          ],
        ),
        children: children,
      ),
    );
  }

  // ───────────────────────────────────────────
  // Property rows
  // ───────────────────────────────────────────

  Widget _buildPropertyRow(String label, Widget value) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 62,
            child: Text(
              label,
              style: const TextStyle(fontSize: 11, color: Color(0xFF999999)),
            ),
          ),
          value,
        ],
      ),
    );
  }

  Widget _buildVectorRow(
    String label,
    TextEditingController xCtrl,
    TextEditingController yCtrl,
  ) {
    return Row(
      children: [
        SizedBox(
          width: 62,
          child: Text(
            label,
            style: const TextStyle(fontSize: 11, color: Color(0xFF999999)),
          ),
        ),
        _axisLabel('X', const Color(0xFFE06666)),
        const SizedBox(width: 3),
        Expanded(child: _compactField(xCtrl)),
        const SizedBox(width: 8),
        _axisLabel('Y', const Color(0xFF6EA86E)),
        const SizedBox(width: 3),
        Expanded(child: _compactField(yCtrl)),
      ],
    );
  }

  Widget _buildRotationRow() {
    return Row(
      children: [
        const SizedBox(
          width: 62,
          child: Text(
            'Rotation',
            style: TextStyle(fontSize: 11, color: Color(0xFF999999)),
          ),
        ),
        SizedBox(width: 52, child: _compactField(_rotCtrl)),
        const SizedBox(width: 4),
        Expanded(
          child: SliderTheme(
            data: SliderThemeData(
              trackHeight: 2,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 5),
              activeTrackColor: const Color(0xFF64B5F6),
              inactiveTrackColor: const Color(0xFF3A3A3A),
              thumbColor: const Color(0xFF64B5F6),
              overlayShape: const RoundSliderOverlayShape(overlayRadius: 10),
            ),
            child: Slider(
              value: _rotation.clamp(-180, 180),
              min: -180,
              max: 180,
              onChanged: (v) {
                setState(() {
                  _rotation = v;
                  _node.rotation = v;
                  _rotCtrl.text = v.toStringAsFixed(1);
                });
                widget.repaintNotifier.value++;
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSwitchRow(
    String label,
    bool value,
    ValueChanged<bool> onChanged,
  ) {
    return Row(
      children: [
        SizedBox(
          width: 62,
          child: Text(
            label,
            style: const TextStyle(fontSize: 11, color: Color(0xFF999999)),
          ),
        ),
        SizedBox(
          height: 22,
          child: FittedBox(
            child: Switch(
              value: value,
              onChanged: onChanged,
              activeColor: const Color(0xFF64B5F6),
              inactiveTrackColor: const Color(0xFF444444),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildColorRow(String label, Color color) {
    final hex = '#${color.value.toRadixString(16).substring(2).toUpperCase()}';
    return Row(
      children: [
        SizedBox(
          width: 62,
          child: Text(
            label,
            style: const TextStyle(fontSize: 11, color: Color(0xFF999999)),
          ),
        ),
        Container(
          width: 22,
          height: 22,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(3),
            border: Border.all(color: const Color(0xFF555555), width: 1),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          hex,
          style: const TextStyle(
            fontSize: 11,
            fontFamily: 'monospace',
            color: Color(0xFFBBBBBB),
          ),
        ),
      ],
    );
  }

  // ───────────────────────────────────────────
  // Shared small widgets
  // ───────────────────────────────────────────

  Widget _axisLabel(String letter, Color color) {
    return Text(
      letter,
      style: TextStyle(
        fontSize: 10,
        fontWeight: FontWeight.w700,
        color: color,
      ),
    );
  }

  Widget _compactField(TextEditingController controller) {
    return SizedBox(
      height: 24,
      child: TextField(
        controller: controller,
        style: const TextStyle(fontSize: 11, color: Color(0xFFDDDDDD)),
        cursorHeight: 13,
        cursorColor: const Color(0xFF64B5F6),
        decoration: InputDecoration(
          isDense: true,
          filled: true,
          fillColor: const Color(0xFF1E1E1E),
          contentPadding: const EdgeInsets.symmetric(horizontal: 6, vertical: 5),
          border: OutlineInputBorder(
            borderSide: const BorderSide(color: Color(0xFF3A3A3A), width: 1),
            borderRadius: BorderRadius.circular(3),
          ),
          enabledBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: Color(0xFF3A3A3A), width: 1),
            borderRadius: BorderRadius.circular(3),
          ),
          focusedBorder: OutlineInputBorder(
            borderSide: const BorderSide(color: Color(0xFF64B5F6), width: 1),
            borderRadius: BorderRadius.circular(3),
          ),
        ),
      ),
    );
  }

  // ───────────────────────────────────────────
  // Icon helpers (same as SceneTree)
  // ───────────────────────────────────────────

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

  Color _iconColorForType(String type) {
    return switch (type) {
      'Node2D'        => const Color(0xFF8BC34A),
      'Camera2D'      => const Color(0xFF64B5F6),
      'SpriteNode'    => const Color(0xFFBA68C8),
      'PhysicsBody2D' => const Color(0xFFFF8A65),
      'Collider2D'    => const Color(0xFF4DD0E1),
      'TilemapNode'   => const Color(0xFFFFD54F),
      _               => const Color(0xFF999999),
    };
  }
}

// ─────────────────────────────────────────────
// Separator
// ─────────────────────────────────────────────

class _Separator extends StatelessWidget {
  const _Separator();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 1,
      margin: const EdgeInsets.symmetric(vertical: 2),
      color: const Color(0xFF2A2A2A),
    );
  }
}
