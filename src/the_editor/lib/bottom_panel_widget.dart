import 'package:flutter/material.dart';

/// Tabbed bottom panel containing an Asset Browser (FileSystem) and
/// an Output Console, similar to Godot's bottom dock.
class BottomPanelWidget extends StatefulWidget {
  const BottomPanelWidget({super.key});

  @override
  State<BottomPanelWidget> createState() => _BottomPanelWidgetState();
}

class _BottomPanelWidgetState extends State<BottomPanelWidget> {
  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Column(
        children: [
          // ── Tab bar ──
          Container(
            height: 30,
            color: const Color(0xFF2D2D2D),
            child: const TabBar(
              tabAlignment: TabAlignment.start,
              isScrollable: true,
              labelColor: Color(0xFFDDDDDD),
              unselectedLabelColor: Color(0xFF888888),
              labelStyle: TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
              unselectedLabelStyle: TextStyle(fontSize: 11),
              indicatorColor: Color(0xFF64B5F6),
              indicatorWeight: 2,
              indicatorSize: TabBarIndicatorSize.tab,
              dividerHeight: 0,
              padding: EdgeInsets.zero,
              labelPadding: EdgeInsets.symmetric(horizontal: 14),
              tabs: [
                Tab(
                  height: 30,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.folder_outlined, size: 13),
                      SizedBox(width: 5),
                      Text('FileSystem'),
                    ],
                  ),
                ),
                Tab(
                  height: 30,
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.terminal_outlined, size: 13),
                      SizedBox(width: 5),
                      Text('Console'),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // ── Tab content ──
          const Expanded(
            child: TabBarView(
              children: [
                _FileSystemTab(),
                _ConsoleTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Tab 1: FileSystem (Asset Browser)
// ─────────────────────────────────────────────

class _FileSystemTab extends StatelessWidget {
  const _FileSystemTab();

  static const List<_AssetEntry> _mockAssets = [
    _AssetEntry('entities',       _AssetType.folder,  'res://entities/'),
    _AssetEntry('levels',         _AssetType.folder,  'res://levels/'),
    _AssetEntry('sprites',        _AssetType.folder,  'res://sprites/'),
    _AssetEntry('audio',          _AssetType.folder,  'res://audio/'),
    _AssetEntry('player.png',     _AssetType.image,   'resources/player.png'),
    _AssetEntry('enemy.png',      _AssetType.image,   'resources/enemy.png'),
    _AssetEntry('tileset.png',    _AssetType.image,   'resources/tileset.png'),
    _AssetEntry('main.py',        _AssetType.script,  'entities/main.py'),
    _AssetEntry('player.py',      _AssetType.script,  'entities/player.py'),
    _AssetEntry('level_1.scene',  _AssetType.scene,   'scenes/level_1.scene'),
    _AssetEntry('level_2.scene',  _AssetType.scene,   'scenes/level_2.scene'),
    _AssetEntry('ui_menu.scene',  _AssetType.scene,   'scenes/ui_menu.scene'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Path breadcrumb ──
        Container(
          height: 26,
          color: const Color(0xFF1A1A1A),
          padding: const EdgeInsets.symmetric(horizontal: 10),
          alignment: Alignment.centerLeft,
          child: const Row(
            children: [
              Icon(Icons.arrow_back_ios, size: 10, color: Color(0xFF666666)),
              SizedBox(width: 6),
              Text(
                'res://',
                style: TextStyle(
                  fontSize: 11,
                  fontFamily: 'monospace',
                  color: Color(0xFF64B5F6),
                ),
              ),
              Text(
                'entities/',
                style: TextStyle(
                  fontSize: 11,
                  fontFamily: 'monospace',
                  color: Color(0xFF999999),
                ),
              ),
            ],
          ),
        ),

        // ── File grid ──
        Expanded(
          child: GridView.builder(
            padding: const EdgeInsets.all(8),
            gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
              maxCrossAxisExtent: 86,
              mainAxisSpacing: 4,
              crossAxisSpacing: 4,
              childAspectRatio: 0.85,
            ),
            itemCount: _mockAssets.length,
            itemBuilder: (context, index) {
              final asset = _mockAssets[index];
              return _AssetTile(asset: asset);
            },
          ),
        ),
      ],
    );
  }
}

/// A single tile in the asset grid.
class _AssetTile extends StatefulWidget {
  const _AssetTile({required this.asset});
  final _AssetEntry asset;

  @override
  State<_AssetTile> createState() => _AssetTileState();
}

class _AssetTileState extends State<_AssetTile> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final child = _buildTileContent();

    // Only images and scenes are draggable into the viewport.
    if (!widget.asset.isDraggable) return child;

    return Draggable<String>(
      data: widget.asset.path,
      dragAnchorStrategy: pointerDragAnchorStrategy,
      feedback: _buildDragFeedback(),
      childWhenDragging: Opacity(opacity: 0.3, child: child),
      child: child,
    );
  }

  Widget _buildTileContent() {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: Container(
        decoration: BoxDecoration(
          color: _hovered ? const Color(0xFF2A2D31) : Colors.transparent,
          borderRadius: BorderRadius.circular(4),
        ),
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              widget.asset.icon,
              size: 28,
              color: widget.asset.iconColor,
            ),
            const SizedBox(height: 4),
            Text(
              widget.asset.name,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 9.5, color: Color(0xFFBBBBBB)),
            ),
          ],
        ),
      ),
    );
  }

  /// Semi-transparent chip that follows the cursor while dragging.
  Widget _buildDragFeedback() {
    return Material(
      color: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: const Color(0xDD2A2D31),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: const Color(0xFF64B5F6), width: 1),
          boxShadow: const [
            BoxShadow(
              color: Color(0x44000000),
              blurRadius: 8,
              offset: Offset(0, 3),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(widget.asset.icon, size: 16, color: widget.asset.iconColor),
            const SizedBox(width: 6),
            Text(
              widget.asset.name,
              style: const TextStyle(
                fontSize: 11,
                color: Color(0xFFDDDDDD),
                decoration: TextDecoration.none,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Tab 2: Console (Output Log)
// ─────────────────────────────────────────────

class _ConsoleTab extends StatelessWidget {
  const _ConsoleTab();

  static const List<_LogLine> _mockLog = [
    _LogLine('[INFO]   PyEngine 2D v0.9.1 initialized.',         _LogLevel.info),
    _LogLine('[INFO]   Renderer: Pygame 2.6 (SDL 2.28.5)',       _LogLevel.info),
    _LogLine('[INFO]   Loading project: res://project.pyengine', _LogLevel.info),
    _LogLine('[OK]     Loaded 3 scenes.',                        _LogLevel.ok),
    _LogLine('[OK]     Loaded 7 assets.',                        _LogLevel.ok),
    _LogLine('[INFO]   Loading level_1.scene...',                _LogLevel.info),
    _LogLine('[WARN]   SpriteNode "enemy_3" has no texture.',    _LogLevel.warn),
    _LogLine('[INFO]   Physics world created (gravity: 980).',   _LogLevel.info),
    _LogLine('[OK]     Scene ready. 12 nodes instantiated.',     _LogLevel.ok),
    _LogLine('[INFO]   Game loop started at 60 FPS target.',     _LogLevel.info),
    _LogLine('[ERROR]  Missing script: res://scripts/boss.py',   _LogLevel.error),
    _LogLine('[WARN]   Frame budget exceeded: 22.4ms',           _LogLevel.warn),
    _LogLine('[INFO]   Frame #1024 — dt: 16.7ms',                _LogLevel.info),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF0D0D0D),
      child: Column(
        children: [
          // ── Console toolbar ──
          Container(
            height: 24,
            color: const Color(0xFF1A1A1A),
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: const Row(
              children: [
                Icon(Icons.delete_outline, size: 13, color: Color(0xFF666666)),
                SizedBox(width: 8),
                Text(
                  'Output',
                  style: TextStyle(fontSize: 10, color: Color(0xFF666666)),
                ),
                Spacer(),
                Text(
                  '13 messages',
                  style: TextStyle(fontSize: 10, color: Color(0xFF555555)),
                ),
              ],
            ),
          ),

          // ── Log lines ──
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              itemCount: _mockLog.length,
              itemExtent: 20,
              itemBuilder: (context, index) {
                final log = _mockLog[index];
                return Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    log.text,
                    style: TextStyle(
                      fontSize: 11,
                      fontFamily: 'monospace',
                      color: log.color,
                      height: 1.4,
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Data models
// ─────────────────────────────────────────────

enum _AssetType { folder, image, script, scene }

class _AssetEntry {
  const _AssetEntry(this.name, this.type, this.path);
  final String name;
  final _AssetType type;
  final String path;

  /// Only images and scenes can be dragged into the viewport.
  bool get isDraggable =>
      type == _AssetType.image || type == _AssetType.scene;

  IconData get icon => switch (type) {
        _AssetType.folder => Icons.folder_rounded,
        _AssetType.image  => Icons.image_outlined,
        _AssetType.script => Icons.description_outlined,
        _AssetType.scene  => Icons.account_tree_outlined,
      };

  Color get iconColor => switch (type) {
        _AssetType.folder => const Color(0xFFFFCA28),
        _AssetType.image  => const Color(0xFFBA68C8),
        _AssetType.script => const Color(0xFF64B5F6),
        _AssetType.scene  => const Color(0xFF8BC34A),
      };
}

enum _LogLevel { info, ok, warn, error }

class _LogLine {
  const _LogLine(this.text, this.level);
  final String text;
  final _LogLevel level;

  Color get color => switch (level) {
        _LogLevel.info  => const Color(0xFF999999),
        _LogLevel.ok    => const Color(0xFF81C784),
        _LogLevel.warn  => const Color(0xFFFFB74D),
        _LogLevel.error => const Color(0xFFEF5350),
      };
}
