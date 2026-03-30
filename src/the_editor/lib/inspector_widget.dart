import 'package:flutter/material.dart';

/// A Godot-style property inspector panel for the selected node.
///
/// Currently uses mocked state for a "Player" SpriteNode. Once global
/// state management is added, this will bind to the Scene Tree selection.
class InspectorWidget extends StatefulWidget {
  const InspectorWidget({super.key});

  @override
  State<InspectorWidget> createState() => _InspectorWidgetState();
}

class _InspectorWidgetState extends State<InspectorWidget> {
  // ── Mocked property state ──
  final TextEditingController _nameCtrl =
      TextEditingController(text: 'Player');
  final TextEditingController _posXCtrl =
      TextEditingController(text: '120.0');
  final TextEditingController _posYCtrl =
      TextEditingController(text: '340.0');
  final TextEditingController _scaleXCtrl =
      TextEditingController(text: '1.0');
  final TextEditingController _scaleYCtrl =
      TextEditingController(text: '1.0');
  final TextEditingController _rotCtrl =
      TextEditingController(text: '0.0');

  double _rotation = 0.0;
  bool _visible = true;
  Color _modulateColor = Colors.white;

  @override
  void dispose() {
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
          // ── Node type header ──
          _buildNodeHeader(),

          const _Separator(),

          // ── Name field ──
          _buildPropertyRow(
            'Name',
            Expanded(child: _compactField(_nameCtrl)),
          ),

          const SizedBox(height: 4),
          const _Separator(),

          // ── Transform section ──
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

          // ── Visibility section ──
          _buildSection(
            title: 'Visibility',
            icon: Icons.visibility_outlined,
            initiallyExpanded: true,
            children: [
              _buildSwitchRow('Visible', _visible, (v) {
                setState(() => _visible = v);
              }),
              const SizedBox(height: 6),
              _buildColorRow('Modulate', _modulateColor),
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
            child: const Icon(
              Icons.image_outlined,
              size: 15,
              color: Color(0xFFBA68C8),
            ),
          ),
          const SizedBox(width: 8),
          const Text(
            'SpriteNode',
            style: TextStyle(
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
      // Remove the default divider lines from ExpansionTile.
      data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
      child: ExpansionTile(
        initiallyExpanded: initiallyExpanded,
        tilePadding: const EdgeInsets.symmetric(horizontal: 10),
        childrenPadding:
            const EdgeInsets.only(left: 10, right: 10, bottom: 8),
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

  /// Generic label + value row.
  Widget _buildPropertyRow(String label, Widget value) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 62,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 11,
                color: Color(0xFF999999),
              ),
            ),
          ),
          value,
        ],
      ),
    );
  }

  /// A row with a label and two compact X / Y text fields.
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

  /// Rotation: label + text field + mini slider.
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
        SizedBox(
          width: 52,
          child: _compactField(_rotCtrl),
        ),
        const SizedBox(width: 4),
        Expanded(
          child: SliderTheme(
            data: SliderThemeData(
              trackHeight: 2,
              thumbShape:
                  const RoundSliderThumbShape(enabledThumbRadius: 5),
              activeTrackColor: const Color(0xFF64B5F6),
              inactiveTrackColor: const Color(0xFF3A3A3A),
              thumbColor: const Color(0xFF64B5F6),
              overlayShape:
                  const RoundSliderOverlayShape(overlayRadius: 10),
            ),
            child: Slider(
              value: _rotation,
              min: -180,
              max: 180,
              onChanged: (v) {
                setState(() {
                  _rotation = v;
                  _rotCtrl.text = v.toStringAsFixed(1);
                });
              },
            ),
          ),
        ),
      ],
    );
  }

  /// A row with a label and a Switch.
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

  /// A row displaying a colored swatch + hex string.
  Widget _buildColorRow(String label, Color color) {
    final hex =
        '#${color.value.toRadixString(16).substring(2).toUpperCase()}';
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

  /// A tiny colored axis label (e.g. red "X", green "Y").
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

  /// A compact, dense text field matching the dark IDE theme.
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
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 6, vertical: 5),
          border: OutlineInputBorder(
            borderSide:
                const BorderSide(color: Color(0xFF3A3A3A), width: 1),
            borderRadius: BorderRadius.circular(3),
          ),
          enabledBorder: OutlineInputBorder(
            borderSide:
                const BorderSide(color: Color(0xFF3A3A3A), width: 1),
            borderRadius: BorderRadius.circular(3),
          ),
          focusedBorder: OutlineInputBorder(
            borderSide:
                const BorderSide(color: Color(0xFF64B5F6), width: 1),
            borderRadius: BorderRadius.circular(3),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Shared tiny separator line
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
