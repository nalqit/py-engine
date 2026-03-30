import 'package:flutter/material.dart';
import 'main_layout.dart';

void main() {
  runApp(const PyEngineApp());
}

class PyEngineApp extends StatelessWidget {
  const PyEngineApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PyEngine 2D',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark(useMaterial3: true).copyWith(
        scaffoldBackgroundColor: const Color(0xFF1E1E1E),
      ),
      home: const MainLayout(),
    );
  }
}
