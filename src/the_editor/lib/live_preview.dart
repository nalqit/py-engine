import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Live preview controller that manages communication with the Python game engine
class LivePreviewController extends ChangeNotifier {
  Process? _engineProcess;
  bool _isRunning = false;
  bool _isConnected = false;
  String? _errorMessage;
  int _fps = 0;
  int _frameCount = 0;
  
  final StreamController<String> _outputController = StreamController<String>.broadcast();
  Stream<String> get outputStream => _outputController.stream;
  
  bool get isRunning => _isRunning;
  bool get isConnected => _isConnected;
  String? get errorMessage => _errorMessage;
  int get fps => _fps;

  /// Start the Python engine process
  Future<bool> startEngine({
    required String pythonPath,
    required String mainScriptPath,
    List<String>? arguments,
    String? workingDirectory,
  }) async {
    if (_isRunning) {
      return true; // Already running
    }

    try {
      _errorMessage = null;
      notifyListeners();

      // Start Python process
      _engineProcess = await Process.start(
        pythonPath,
        [mainScriptPath, '--headless', '--preview', ...?arguments],
        workingDirectory: workingDirectory,
      );

      _isRunning = true;
      notifyListeners();

      // Listen to stdout for frame updates
      _engineProcess!.stdout.transform(utf8.decoder).listen((data) {
        _outputController.add(data);
        
        // Parse FPS from output
        if (data.contains('FPS:')) {
          final match = RegExp(r'FPS:\s*(\d+)').firstMatch(data);
          if (match != null) {
            _fps = int.parse(match.group(1)!);
            _frameCount++;
            notifyListeners();
          }
        }
        
        // Check for successful startup
        if (data.contains('Engine started')) {
          _isConnected = true;
          notifyListeners();
        }
      });

      // Listen to stderr for errors
      _engineProcess!.stderr.transform(utf8.decoder).listen((data) {
        _outputController.add('[ERROR] $data');
        _errorMessage = data;
        notifyListeners();
      });

      // Handle process exit
      _engineProcess!.exitCode.then((exitCode) {
        _isRunning = false;
        _isConnected = false;
        if (exitCode != 0) {
          _errorMessage = 'Engine exited with code: $exitCode';
        }
        notifyListeners();
      });

      // Wait a moment for startup
      await Future.delayed(const Duration(seconds: 2));
      
      return _isRunning;
    } catch (e) {
      _errorMessage = 'Failed to start engine: $e';
      _isRunning = false;
      notifyListeners();
      return false;
    }
  }

  /// Send scene JSON to the engine for live preview
  Future<void> sendSceneJson(Map<String, dynamic> sceneJson) async {
    if (!_isRunning || _engineProcess == null) return;
    
    try {
      // Send scene data via stdin
      _engineProcess!.stdin.writeln('SCENE:${jsonEncode(sceneJson)}');
    } catch (e) {
      _errorMessage = 'Failed to send scene: $e';
      notifyListeners();
    }
  }

  /// Send command to engine
  Future<void> sendCommand(String command) async {
    if (!_isRunning || _engineProcess == null) return;
    
    try {
      _engineProcess!.stdin.writeln(command);
    } catch (e) {
      _errorMessage = 'Failed to send command: $e';
      notifyListeners();
    }
  }

  /// Pause the game in preview
  Future<void> pause() => sendCommand('PAUSE');

  /// Resume the game in preview
  Future<void> resume() => sendCommand('RESUME');

  /// Reset the scene
  Future<void> reset() => sendCommand('RESET');

  /// Stop the engine
  Future<void> stopEngine() async {
    if (_engineProcess != null) {
      _engineProcess!.stdin.writeln('QUIT');
      await Future.delayed(const Duration(milliseconds: 500));
      _engineProcess!.kill();
      _engineProcess = null;
    }
    _isRunning = false;
    _isConnected = false;
    notifyListeners();
  }

  @override
  void dispose() {
    stopEngine();
    _outputController.close();
    super.dispose();
  }
}

/// Widget displaying live preview status and controls
class LivePreviewControls extends StatelessWidget {
  final LivePreviewController controller;
  final VoidCallback? onStartPreview;
  final VoidCallback? onStopPreview;

  const LivePreviewControls({
    super.key,
    required this.controller,
    this.onStartPreview,
    this.onStopPreview,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 32,
      color: const Color(0xFF2D2D2D),
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Row(
        children: [
          // Status indicator
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: controller.isConnected 
                  ? Colors.green 
                  : Colors.grey,
            ),
          ),
          const SizedBox(width: 8),
          
          // Status text
          Text(
            controller.isConnected 
                ? 'Live Preview' 
                : 'Not Connected',
            style: const TextStyle(fontSize: 12),
          ),
          
          if (controller.isConnected) ...[
            const SizedBox(width: 16),
            Text(
              'FPS: ${controller.fps}',
              style: const TextStyle(
                fontSize: 11, 
                color: Colors.grey,
              ),
            ),
          ],
          
          const Spacer(),
          
          // Control buttons
          if (!controller.isConnected)
            TextButton.icon(
              onPressed: onStartPreview,
              icon: const Icon(Icons.play_arrow, size: 16),
              label: const Text('Start Preview'),
              style: TextButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                textStyle: const TextStyle(fontSize: 12),
              ),
            )
          else ...[
            IconButton(
              icon: const Icon(Icons.pause, size: 16),
              onPressed: controller.pause,
              tooltip: 'Pause',
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            ),
            IconButton(
              icon: const Icon(Icons.stop, size: 16),
              onPressed: onStopPreview,
              tooltip: 'Stop',
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            ),
            IconButton(
              icon: const Icon(Icons.refresh, size: 16),
              onPressed: controller.reset,
              tooltip: 'Reset',
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 28, minHeight: 28),
            ),
          ],
          
          // Error indicator
          if (controller.errorMessage != null)
            Tooltip(
              message: controller.errorMessage!,
              child: const Icon(
                Icons.warning_amber,
                size: 16,
                color: Colors.orange,
              ),
            ),
        ],
      ),
    );
  }
}

/// Console output widget for showing engine logs
class PreviewConsole extends StatefulWidget {
  final Stream<String> outputStream;

  const PreviewConsole({
    super.key,
    required this.outputStream,
  });

  @override
  State<PreviewConsole> createState() => _PreviewConsoleState();
}

class _PreviewConsoleState extends State<PreviewConsole> {
  final ScrollController _scrollController = ScrollController();
  final List<String> _logs = [];
  static const int _maxLines = 100;

  @override
  void initState() {
    super.initState();
    widget.outputStream.listen((line) {
      setState(() {
        _logs.add(line);
        if (_logs.length > _maxLines) {
          _logs.removeAt(0);
        }
      });
      // Auto-scroll to bottom
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.jumpTo(_scrollController.position.maxScrollHeight);
        }
      });
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF1A1A1A),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(4),
            color: const Color(0xFF252525),
            child: const Row(
              children: [
                Icon(Icons.terminal, size: 14, color: Colors.grey),
                SizedBox(width: 8),
                Text(
                  'Console',
                  style: TextStyle(fontSize: 11, color: Colors.grey),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(4),
              itemCount: _logs.length,
              itemBuilder: (context, index) {
                final line = _logs[index];
                final isError = line.contains('[ERROR]');
                final isWarning = line.contains('[WARN]');
                
                return Text(
                  line,
                  style: TextStyle(
                    fontSize: 10,
                    color: isError 
                        ? Colors.red 
                        : isWarning 
                            ? Colors.orange 
                            : Colors.grey.shade400,
                    fontFamily: 'monospace',
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