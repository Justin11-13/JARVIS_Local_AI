import 'package:flutter/material.dart';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:desktop_ui/coding_memory_panel.dart';
import 'package:desktop_ui/console_theme.dart';
import 'package:desktop_ui/jarvis_api.dart';

class MemoryApi extends JarvisApi {
  final calls = <String>[];
  @override
  Future<Map<String, dynamic>> assistantRequest(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    calls.add('$method $path');
    if (path == '/api/assistant/state') {
      return {
        'projects': ['JARVIS'],
        'extraction': {'status': 'completed'},
      };
    }
    if (path == '/api/memory') return {'items': []};
    return {'tasks': []};
  }
}

void main() {
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    for (final entry in {
      'Segoe UI Variable': 'segoeui.ttf',
      'Segoe UI': 'segoeui.ttf',
      'Consolas': 'consola.ttf',
    }.entries) {
      final file = File('C:/Windows/Fonts/${entry.value}');
      if (file.existsSync()) {
        final loader = FontLoader(entry.key)
          ..addFont(Future.value(ByteData.sublistView(file.readAsBytesSync())));
        await loader.load();
      }
    }
  });
  for (final width in [1100.0, 390.0]) {
    testWidgets('coding memory panel renders and extracts at $width', (
      tester,
    ) async {
      tester.view.physicalSize = Size(width, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final api = MemoryApi();
      await tester.pumpWidget(
        MaterialApp(
          debugShowCheckedModeBanner: false,
          theme: consoleTheme(),
          home: Scaffold(
            body: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: CodingMemoryPanel(api: api),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      final button = find.text('Extract recent conversation');
      await tester.ensureVisible(button);
      await tester.tap(button);
      await tester.pumpAndSettle();
      expect(api.calls, contains('POST /api/memory/extract'));
      expect(tester.takeException(), isNull);
      if (width == 1100) {
        await expectLater(
          find.byType(MaterialApp),
          matchesGoldenFile('goldens/coding_memory.png'),
        );
      }
      await tester.pumpWidget(const SizedBox());
      api.close();
    });
  }
}
