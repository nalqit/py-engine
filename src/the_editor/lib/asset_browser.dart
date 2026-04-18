import 'dart:io';
import 'package:flutter/material.dart';

/// Asset browser panel for managing project assets
class AssetBrowser extends StatefulWidget {
  final String projectPath;
  final ValueChanged<String>? onAssetSelected;
  final List<String>? allowedExtensions;

  const AssetBrowser({
    super.key,
    required this.projectPath,
    this.onAssetSelected,
    this.allowedExtensions,
  });

  @override
  State<AssetBrowser> createState() => _AssetBrowserState();
}

class _AssetBrowserState extends State<AssetBrowser> {
  String _currentPath = '';
  List<FileSystemEntity> _items = [];
  String? _selectedAsset;
  String _searchQuery = '';
  bool _isLoading = false;

  final List<String> _defaultAllowedExtensions = [
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp',
    '.wav', '.mp3', '.ogg',
    '.json', '.scene',
  ];

  List<String> get _extensions => widget.allowedExtensions ?? _defaultAllowedExtensions;

  @override
  void initState() {
    super.initState();
    _loadDirectory(widget.projectPath);
  }

  Future<void> _loadDirectory(String path) async {
    setState(() => _isLoading = true);
    
    try {
      final dir = Directory(path);
      if (await dir.exists()) {
        final items = await dir.list().toList();
        items.sort((a, b) {
          if (a is Directory && b is! Directory) return -1;
          if (b is Directory && a is! Directory) return 1;
          return a.path.toLowerCase().compareTo(b.path.toLowerCase());
        });
        
        setState(() {
          _currentPath = path;
          _items = items.where((item) {
            if (item is Directory) return true;
            final ext = item.path.toLowerCase().split('.').last;
            return _extensions.any((e) => e.substring(1) == ext);
          }).toList();
        });
      }
    } catch (e) {
      debugPrint('Error loading directory: $e');
    }
    
    setState(() => _isLoading = false);
  }

  void _goUp() {
    final parent = Directory(_currentPath).parent.path;
    _loadDirectory(parent);
  }

  List<FileSystemEntity> get _filteredItems {
    if (_searchQuery.isEmpty) return _items;
    return _items.where((item) {
      return item.path.toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();
  }

  IconData _getIconForFile(FileSystemEntity item) {
    if (item is Directory) return Icons.folder;
    
    final ext = item.path.toLowerCase().split('.').last;
    switch (ext) {
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
      case 'bmp':
      case 'webp':
        return Icons.image;
      case 'wav':
      case 'mp3':
      case 'ogg':
        return Icons.audiotrack;
      case 'json':
      case 'scene':
        return Icons.data_object;
      default:
        return Icons.insert_drive_file;
    }
  }

  Color _getIconColor(FileSystemEntity item) {
    if (item is Directory) return const Color(0xFFFFD54F);
    
    final ext = item.path.toLowerCase().split('.').last;
    switch (ext) {
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
      case 'bmp':
      case 'webp':
        return const Color(0xFFBA68C8);
      case 'wav':
      case 'mp3':
      case 'ogg':
        return const Color(0xFF4DD0E1);
      case 'json':
      case 'scene':
        return const Color(0xFF8BC34A);
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Header with path and controls
        Container(
          height: 32,
          color: const Color(0xFF252525),
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            children: [
              IconButton(
                icon: const Icon(Icons.arrow_upward, size: 16),
                onPressed: _currentPath != widget.projectPath ? _goUp : null,
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  _currentPath.replaceFirst(widget.projectPath, ''),
                  style: const TextStyle(fontSize: 11, color: Colors.grey),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              IconButton(
                icon: const Icon(Icons.refresh, size: 16),
                onPressed: () => _loadDirectory(_currentPath),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
              ),
            ],
          ),
        ),
        
        // Search bar
        Container(
          height: 28,
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: TextField(
            style: const TextStyle(fontSize: 12),
            decoration: InputDecoration(
              hintText: 'Search assets...',
              hintStyle: const TextStyle(fontSize: 12),
              prefixIcon: const Icon(Icons.search, size: 16),
              isDense: true,
              contentPadding: const EdgeInsets.symmetric(vertical: 4),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            onChanged: (value) => setState(() => _searchQuery = value),
          ),
        ),
        
        const SizedBox(height: 4),
        
        // Asset grid/list
        Expanded(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _filteredItems.isEmpty
                  ? const Center(
                      child: Text(
                        'No assets found',
                        style: TextStyle(color: Colors.grey),
                      ),
                    )
                  : ListView.builder(
                      itemCount: _filteredItems.length,
                      itemBuilder: (context, index) {
                        final item = _filteredItems[index];
                        final isSelected = item.path == _selectedAsset;
                        final name = item.path.split(Platform.pathSeparator).last;
                        
                        return GestureDetector(
                          onDoubleTap: item is Directory
                              ? () => _loadDirectory(item.path)
                              : null,
                          child: ListTile(
                            dense: true,
                            selected: isSelected,
                            selectedTileColor: const Color(0xFF4CAF50).withOpacity(0.2),
                            leading: Icon(
                              _getIconForFile(item),
                              size: 20,
                              color: _getIconColor(item),
                            ),
                            title: Text(
                              name,
                              style: const TextStyle(fontSize: 12),
                            ),
                            onTap: () {
                              setState(() => _selectedAsset = item.path);
                              widget.onAssetSelected?.call(item.path);
                            },
                          ),
                        );
                      },
                    ),
        ),
        
        // Status bar
        Container(
          height: 24,
          color: const Color(0xFF1E1E1E),
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            children: [
              Text(
                '${_filteredItems.length} items',
                style: const TextStyle(fontSize: 10, color: Colors.grey),
              ),
              if (_selectedAsset != null) ...[
                const Spacer(),
                Text(
                  _selectedAsset!.split(Platform.pathSeparator).last,
                  style: const TextStyle(fontSize: 10, color: Colors.white),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

/// Asset thumbnail grid for visual asset browsing
class AssetThumbnailGrid extends StatelessWidget {
  final List<String> assetPaths;
  final ValueChanged<String>? onAssetSelected;
  final double thumbnailSize;

  const AssetThumbnailGrid({
    super.key,
    required this.assetPaths,
    this.onAssetSelected,
    this.thumbnailSize = 64,
  });

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      padding: const EdgeInsets.all(8),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: (MediaQuery.of(context).size.width / thumbnailSize).floor(),
        crossAxisSpacing: 8,
        mainAxisSpacing: 8,
      ),
      itemCount: assetPaths.length,
      itemBuilder: (context, index) {
        final path = assetPaths[index];
        final name = path.split(Platform.pathSeparator).last;
        
        return InkWell(
          onTap: () => onAssetSelected?.call(path),
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF2D2D2D),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: Colors.grey.shade800),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  _getIconForExtension(path.split('.').last),
                  size: 32,
                  color: Colors.grey,
                ),
                const SizedBox(height: 4),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: Text(
                    name,
                    style: const TextStyle(fontSize: 10),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  IconData _getIconForExtension(String ext) {
    switch (ext.toLowerCase()) {
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
        return Icons.image;
      case 'wav':
      case 'mp3':
        return Icons.audiotrack;
      case 'json':
      case 'scene':
        return Icons.data_object;
      default:
        return Icons.insert_drive_file;
    }
  }
}