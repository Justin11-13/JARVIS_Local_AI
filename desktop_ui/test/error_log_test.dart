import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:desktop_ui/console_theme.dart';
import 'package:desktop_ui/error_log.dart';
import 'package:desktop_ui/errors_page.dart';

void main() {
  test(
    'error log merges duplicates and retains at most 50 bounded reports',
    () async {
      final log = AppErrorLog();
      var notifications = 0;
      log.addListener(() => notifications++);
      log.record(source: 'UI', message: 'A failure');
      log.record(source: 'UI', message: 'A failure');
      expect(log.entries.single.occurrences, 2);
      expect(log.hasInterfaceErrors, isTrue);
      await Future<void>.delayed(Duration.zero);
      expect(notifications, 1);
      for (var i = 0; i < 60; i++) {
        log.record(source: 'Tool', message: 'Failure $i');
      }
      expect(log.entries.length, 50);
      expect(log.entries.first.message, 'Failure 59');
      log.record(source: 'Tool', message: 'Long report', details: 'x' * 40000);
      expect(log.entries.first.details.length, lessThan(33000));
      expect(log.entries.first.details, contains('[Truncated'));
      log.clear();
      expect(log.entries, isEmpty);
      expect(log.hasInterfaceErrors, isFalse);
      log.dispose(); // Pending notification must not fire after disposal.
      await Future<void>.delayed(Duration.zero);
    },
  );

  testWidgets(
    'framework fallback is compact and preserves original error handlers',
    (tester) async {
      final log = AppErrorLog();
      final originalFlutter = FlutterError.onError;
      final originalRuntime = PlatformDispatcher.instance.onError;
      final originalBuilder = ErrorWidget.builder;
      var consoleReports = 0;
      var runtimeReports = 0;
      FlutterError.onError = (_) => consoleReports++;
      PlatformDispatcher.instance.onError = (_, _) {
        runtimeReports++;
        return true;
      };
      final capture = AppErrorCapture(
        log,
        (_) => const InterfaceErrorFallback(),
      );
      try {
        await tester.pumpWidget(
          MaterialApp(
            theme: consoleTheme(),
            home: Scaffold(
              body: Column(
                children: [
                  const Text('Still usable'),
                  Builder(
                    builder: (_) =>
                        throw StateError('Deliberate render failure'),
                  ),
                  const Text('Other content remains'),
                ],
              ),
            ),
          ),
        );
        await tester.pump();
        expect(consoleReports, 1);
        expect(
          log.entries.single.message,
          contains('Deliberate render failure'),
        );
        expect(log.entries.single.stack, isNotEmpty);
        expect(find.byType(ErrorWidget), findsNothing);
        expect(find.text('Other content remains'), findsOneWidget);
        expect(
          tester.getSize(find.byType(InterfaceErrorFallback)).height,
          lessThan(100),
        );
        expect(
          PlatformDispatcher.instance.onError!(
            StateError('Runtime test'),
            StackTrace.current,
          ),
          isTrue,
        );
        expect(runtimeReports, 1);
        expect(log.entries.first.source, 'Runtime');
      } finally {
        capture.dispose();
        expect(ErrorWidget.builder, originalBuilder);
        FlutterError.onError = originalFlutter;
        PlatformDispatcher.instance.onError = originalRuntime;
        await tester.pumpWidget(const SizedBox());
        log.dispose();
      }
    },
  );

  for (final size in [const Size(1200, 800), const Size(390, 760)]) {
    testWidgets(
      'error details, clipboard and clear confirmation work at $size',
      (tester) async {
        tester.view.physicalSize = size;
        tester.view.devicePixelRatio = 1;
        tester.platformDispatcher.textScaleFactorTestValue = 1.3;
        addTearDown(() {
          tester.view.resetPhysicalSize();
          tester.view.resetDevicePixelRatio();
          tester.platformDispatcher.clearTextScaleFactorTestValue();
        });
        final log = AppErrorLog();
        log.record(
          source: 'UI',
          message: '无法显示工具结果 / ' * 6,
          details: 'Detailed failure for testing.',
          stack: StackTrace.fromString('frame 1\nframe 2'),
        );
        String? clipboard;
        tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
          SystemChannels.platform,
          (call) async {
            if (call.method == 'Clipboard.setData') {
              clipboard = (call.arguments as Map)['text'] as String;
            }
            return null;
          },
        );
        addTearDown(
          () => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
            SystemChannels.platform,
            null,
          ),
        );
        await tester.pumpWidget(
          MaterialApp(
            theme: consoleTheme(),
            home: Scaffold(body: ErrorsPage(log: log)),
          ),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.byType(ExpansionTile));
        await tester.pumpAndSettle();
        expect(
          find.textContaining('Detailed failure for testing.'),
          findsOneWidget,
        );
        await tester.ensureVisible(find.text('Copy details'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Copy details'));
        await tester.pumpAndSettle();
        expect(clipboard, contains('frame 1\nframe 2'));
        expect(tester.takeException(), isNull);
        await tester.ensureVisible(find.text('Clear log'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Clear log'));
        await tester.pumpAndSettle();
        await tester.tap(find.text('Keep log'));
        await tester.pumpAndSettle();
        expect(log.entries.length, 1);
        await tester.tap(find.text('Clear log'));
        await tester.pumpAndSettle();
        await tester.tap(find.widgetWithText(FilledButton, 'Clear log'));
        await tester.pumpAndSettle();
        expect(find.text('No errors recorded'), findsOneWidget);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox());
        log.dispose();
      },
    );
  }
}
