import 'package:flutter/material.dart';
import 'engine_node.dart';

/// Tool types available in the editor
enum EditorTool {
  select,
  move,
  scale,
  rotate,
}

/// Controller for editor tools and transformations
class EditorToolController extends ChangeNotifier {
  EditorTool _currentTool = EditorTool.select;
  bool _snapToGrid = false;
  double _gridSize = 16.0;
  bool _showGrid = true;
  
  // Multi-selection
  final Set<EngineNode> _selectedNodes = {};
  
  EditorTool get currentTool => _currentTool;
  bool get snapToGrid => _snapToGrid;
  double get gridSize => _gridSize;
  bool get showGrid => _showGrid;
  Set<EngineNode> get selectedNodes => _selectedNodes;
  
  void setTool(EditorTool tool) {
    _currentTool = tool;
    notifyListeners();
  }
  
  void toggleSnapToGrid() {
    _snapToGrid = !_snapToGrid;
    notifyListeners();
  }
  
  void setGridSize(double size) {
    _gridSize = size;
    notifyListeners();
  }
  
  void toggleGrid() {
    _showGrid = !_showGrid;
    notifyListeners();
  }
  
  void selectNode(EngineNode node) {
    _selectedNodes.clear();
    _selectedNodes.add(node);
    notifyListeners();
  }
  
  void addToSelection(EngineNode node) {
    _selectedNodes.add(node);
    notifyListeners();
  }
  
  void clearSelection() {
    _selectedNodes.clear();
    notifyListeners();
  }
  
  void moveSelection(double dx, double dy) {
    for (final node in _selectedNodes) {
      node.x += dx;
      node.y += dy;
      if (_snapToGrid) {
        node.x = (node.x / _gridSize).round() * _gridSize;
        node.y = (node.y / _gridSize).round() * _gridSize;
      }
    }
    notifyListeners();
  }
  
  void scaleSelection(double scaleX, double scaleY) {
    for (final node in _selectedNodes) {
      node.scaleX = (node.scaleX * scaleX).clamp(0.1, 10.0);
      node.scaleY = (node.scaleY * scaleY).clamp(0.1, 10.0);
    }
    notifyListeners();
  }
  
  void rotateSelection(double angle) {
    for (final node in _selectedNodes) {
      node.rotation += angle;
    }
    notifyListeners();
  }
}

/// Toolbar widget for selecting editor tools
class EditorToolbar extends StatelessWidget {
  final EditorToolController toolController;
  final VoidCallback? onAddNode;
  final VoidCallback? onDelete;
  final VoidCallback? onSave;
  final VoidCallback? onLoad;

  const EditorToolbar({
    super.key,
    required this.toolController,
    this.onAddNode,
    this.onDelete,
    this.onSave,
    this.onLoad,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 36,
      color: const Color(0xFF2D2D2D),
      child: Row(
        children: [
          const SizedBox(width: 8),
          _toolButton(EditorTool.select, Icons.near_me, 'Select (V)'),
          _toolButton(EditorTool.move, Icons.open_with, 'Move (M)'),
          _toolButton(EditorTool.scale, Icons.zoom_in, 'Scale (S)'),
          _toolButton(EditorTool.rotate, Icons.rotate_right, 'Rotate (R)'),
          const VerticalDivider(width: 16),
          _actionButton(Icons.add, 'Add Node', onAddNode),
          _actionButton(Icons.delete_outline, 'Delete', onDelete),
          const VerticalDivider(width: 16),
          _toggleButton(
            toolController.snapToGrid,
            Icons.grid_on,
            'Snap to Grid',
            toolController.toggleSnapToGrid,
          ),
          _toggleButton(
            toolController.showGrid,
            Icons.grid_4x4,
            'Show Grid',
            toolController.toggleGrid,
          ),
          const Spacer(),
          _actionButton(Icons.save, 'Save', onSave),
          _actionButton(Icons.folder_open, 'Load', onLoad),
          const SizedBox(width: 8),
        ],
      ),
    );
  }

  Widget _toolButton(EditorTool tool, IconData icon, String tooltip) {
    final isSelected = toolController.currentTool == tool;
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: () => toolController.setTool(tool),
        child: Container(
          width: 32,
          height: 32,
          margin: const EdgeInsets.symmetric(horizontal: 2),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF4CAF50) : Colors.transparent,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Icon(icon, size: 18, color: isSelected ? Colors.white : Colors.grey),
        ),
      ),
    );
  }

  Widget _actionButton(IconData icon, String tooltip, VoidCallback? onTap) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onTap,
        child: Container(
          width: 32,
          height: 32,
          margin: const EdgeInsets.symmetric(horizontal: 2),
          child: Icon(icon, size: 18, color: Colors.grey),
        ),
      ),
    );
  }

  Widget _toggleButton(bool isOn, IconData icon, String tooltip, VoidCallback onToggle) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onToggle,
        child: Container(
          width: 32,
          height: 32,
          margin: const EdgeInsets.symmetric(horizontal: 2),
          decoration: BoxDecoration(
            color: isOn ? const Color(0xFF4CAF50).withOpacity(0.3) : Colors.transparent,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Icon(icon, size: 18, color: isOn ? Colors.white : Colors.grey),
        ),
      ),
    );
  }
}

/// Dialog for adding a new node to the scene
class AddNodeDialog extends StatefulWidget {
  const AddNodeDialog({super.key});

  @override
  State<AddNodeDialog> createState() => _AddNodeDialogState();
}

class _AddNodeDialogState extends State<AddNodeDialog> {
  String _selectedType = 'Node2D';
  final _nameController = TextEditingController(text: 'NewNode');

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Node'),
      content: SizedBox(
        width: 300,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(labelText: 'Name'),
            ),
            const SizedBox(height: 16),
            const Text('Type:', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: NodeTypes.all.map((type) {
                final isSelected = type == _selectedType;
                return ChoiceChip(
                  label: Text(type),
                  selected: isSelected,
                  onSelected: (_) => setState(() => _selectedType = type),
                );
              }).toList(),
            ),
            const SizedBox(height: 8),
            Text(
              NodeTypes.descriptions[_selectedType] ?? '',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () => Navigator.pop(context, {
            'name': _nameController.text,
            'type': _selectedType,
          }),
          child: const Text('Add'),
        ),
      ],
    );
  }
}

/// Confirmation dialog for deleting nodes
class DeleteConfirmationDialog extends StatelessWidget {
  final int nodeCount;

  const DeleteConfirmationDialog({super.key, required this.nodeCount});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Delete Nodes'),
      content: Text(
        'Are you sure you want to delete $nodeCount node(s)? This action cannot be undone.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
          onPressed: () => Navigator.pop(context, true),
          child: const Text('Delete'),
        ),
      ],
    );
  }
}

/// Property input widget for editing node properties
class PropertyInput extends StatelessWidget {
  final String label;
  final dynamic value;
  final ValueChanged<dynamic> onChanged;
  final String? hint;

  const PropertyInput({
    super.key,
    required this.label,
    required this.value,
    required this.onChanged,
    this.hint,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ),
          Expanded(
            child: _buildInput(context),
          ),
        ],
      ),
    );
  }

  Widget _buildInput(BuildContext context) {
    if (value is bool) {
      return Switch(
        value: value,
        onChanged: onChanged,
      );
    }
    
    if (value is int || value is double) {
      return TextFormField(
        initialValue: value.toString(),
        keyboardType: TextInputType.number,
        style: const TextStyle(fontSize: 12),
        decoration: InputDecoration(
          isDense: true,
          contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          border: const OutlineInputBorder(),
          hintText: hint,
        ),
        onFieldSubmitted: (text) {
          final num? parsed = num.tryParse(text);
          if (parsed != null) {
            onChanged(parsed is int ? parsed : parsed.toDouble());
          }
        },
      );
    }
    
    if (value is String) {
      return TextFormField(
        initialValue: value,
        style: const TextStyle(fontSize: 12),
        decoration: InputDecoration(
          isDense: true,
          contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          border: const OutlineInputBorder(),
          hintText: hint,
        ),
        onFieldSubmitted: onChanged,
      );
    }
    
    return Text(value.toString());
  }
}

/// Color picker widget for color properties
class ColorPickerWidget extends StatefulWidget {
  final int initialColor;
  final ValueChanged<int> onColorChanged;

  const ColorPickerWidget({
    super.key,
    required this.initialColor,
    required this.onColorChanged,
  });

  @override
  State<ColorPickerWidget> createState() => _ColorPickerWidgetState();
}

class _ColorPickerWidgetState extends State<ColorPickerWidget> {
  late int _color;

  @override
  void initState() {
    super.initState();
    _color = widget.initialColor;
  }

  static const List<int> _presetColors = [
    0xFFFFFFFF, 0xFF000000, 0xFFFF0000, 0xFF00FF00, 0xFF0000FF,
    0xFFFFFF00, 0xFFFF00FF, 0xFF00FFFF, 0xFF808080, 0xFF8BC34A,
    0xFF64B5F6, 0xFFBA68C8, 0xFFFF8A65, 0xFF4DD0E1, 0xFFFFD54F,
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 4,
          runSpacing: 4,
          children: _presetColors.map((color) {
            final isSelected = color == _color;
            return InkWell(
              onTap: () {
                setState(() => _color = color);
                widget.onColorChanged(color);
              },
              child: Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: Color(color),
                  border: Border.all(
                    color: isSelected ? Colors.white : Colors.grey,
                    width: isSelected ? 2 : 1,
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }
}