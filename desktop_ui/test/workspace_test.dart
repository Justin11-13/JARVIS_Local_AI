import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:desktop_ui/main.dart';
import 'package:desktop_ui/jarvis_api.dart';
import 'package:desktop_ui/runtime_monitor.dart';
import 'package:desktop_ui/error_log.dart';

class FakeApi extends JarvisApi {
  int reads = 0;
  int chats = 0;
  final messages = <String>[];
  List<JarvisHistoryTurn> history = const [];
  bool offline = false;
  Completer<SystemSample>? pending;
  Completer<JarvisChatReply>? chatReply;
  @override
  Future<JarvisHealth> health() async {
    if (offline) throw const JarvisApiException('Core is offline.');
    return const JarvisHealth(status: 'ready', brain: 'codex');
  }

  @override
  Future<SystemSample> telemetry() async {
    reads++;
    if (offline) throw const JarvisApiException('Core is offline.');
    if (pending != null) return pending!.future;
    return SystemSample(
      cpu: 12.5,
      memory: 40,
      usedBytes: 12 * 1073741824,
      totalBytes: 32 * 1073741824,
      sampledAt: DateTime(2026, 9, 3).add(Duration(seconds: reads * 2)),
      gpus: const [
        GpuSample(
          id: '0',
          name: 'NVIDIA test GPU',
          utilization: 23,
          usedBytes: 1073741824,
          totalBytes: 6 * 1073741824,
          temperature: 54,
        ),
      ],
    );
  }

  @override
  Future<WindowsSpeechSettings> windowsSpeechSettings() async =>
      const WindowsSpeechSettings(
        voice: 'Microsoft George',
        speed: 0,
        source: 'Windows Speech settings',
      );

  @override
  Future<JarvisChatReply> sendMessage(String message) async {
    chats++;
    messages.add(message);
    if (chatReply != null) return chatReply!.future;
    return const JarvisChatReply(reply: 'Connected response.', toolResults: []);
  }

  @override
  Future<List<JarvisHistoryTurn>> conversationHistory() async => history;

  @override
  Future<List<ObsidianVault>> obsidianVaults() async => const [];

  @override
  Future<List<BackgroundTask>> backgroundTasks() async => const [];
}

void main() {
  Future<void> mount(
    WidgetTester tester,
    FakeApi api,
    Size size, {
    double scale = 1,
    AppErrorLog? errorLog,
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    tester.platformDispatcher.textScaleFactorTestValue = scale;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
      tester.platformDispatcher.clearTextScaleFactorTestValue();
      api.close();
    });
    await tester.pumpWidget(JarvisApp(api: api, errorLog: errorLog));
    await tester.pump();
  }

  Future<void> unmount(WidgetTester tester) async =>
      tester.pumpWidget(const SizedBox());

  for (final size in [
    const Size(1440, 900),
    const Size(960, 720),
    const Size(600, 720),
    const Size(390, 760),
  ]) {
    testWidgets('all pages render at $size without overflow', (tester) async {
      final api = FakeApi();
      await mount(tester, api, size);
      expect(find.text('At your command.'), findsOneWidget);
      expect(tester.takeException(), isNull);
      for (var page = 1; page < 5; page++) {
        if (size.width < 600) {
          await tester.tap(find.byType(NavigationDestination).at(page));
        } else {
          await tester.tap(find.byKey(ValueKey('nav-$page')));
        }
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull, reason: 'page $page at $size');
      }
      await unmount(tester);
    });
  }
  testWidgets('text scaling remains usable', (tester) async {
    await mount(tester, FakeApi(), const Size(1280, 900), scale: 1.3);
    expect(tester.takeException(), isNull);
    await tester.tap(find.byKey(const ValueKey('nav-3')));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });
  testWidgets('header identifies the assistant and active model', (
    tester,
  ) async {
    await mount(tester, FakeApi(), const Size(1440, 900));
    await tester.pumpAndSettle();
    expect(find.text('Personal assistant'), findsOneWidget);
    expect(find.text('MODEL · CODEX'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });
  testWidgets('persistent conversation is archived outside Assistant', (
    tester,
  ) async {
    final api = FakeApi()
      ..history = [
        JarvisHistoryTurn(
          user: 'Remember this question',
          assistant: 'Restored answer',
          speech: 'Restored spoken answer',
          createdAt: DateTime(2026, 9, 4, 12),
        ),
      ];

    await mount(tester, api, const Size(1440, 900));
    await tester.pumpAndSettle();

    expect(find.text('At your command.'), findsOneWidget);
    expect(find.text('Remember this question'), findsNothing);
    await tester.tap(find.byKey(const ValueKey('nav-1')));
    await tester.pumpAndSettle();
    expect(find.text('Remember this question'), findsOneWidget);
    expect(find.text('Archived'), findsOneWidget);
    await tester.tap(find.text('Remember this question'));
    await tester.pumpAndSettle();
    expect(find.text('Restored answer'), findsOneWidget);
    expect(find.textContaining('Response time'), findsNothing);
    await unmount(tester);
  });
  testWidgets('settings offers an explicit reply voice provider', (
    tester,
  ) async {
    await mount(tester, FakeApi(), const Size(1440, 900));
    await tester.tap(find.byKey(const ValueKey('nav-3')));
    await tester.pumpAndSettle();
    expect(find.text('Windows system voice'), findsOneWidget);
    expect(find.text('Microsoft George · Speed 0'), findsOneWidget);
    expect(find.text('Synced'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('speech-provider')));
    await tester.pumpAndSettle();
    expect(find.text('Fish Audio cloud'), findsOneWidget);
    expect(find.text('Auto read completed replies'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });
  for (final size in [const Size(1440, 900), const Size(1920, 1080)]) {
    testWidgets('Device groups metrics and aligns support panels at $size', (
      tester,
    ) async {
      await mount(tester, FakeApi(), size);
      await tester.tap(find.byKey(const ValueKey('nav-2')));
      await tester.pumpAndSettle();
      final cpu = tester.getTopLeft(find.text('CPU'));
      final memory = tester.getTopLeft(find.text('Memory'));
      expect(memory.dy, closeTo(cpu.dy, 1));
      expect(memory.dx, greaterThan(cpu.dx));
      expect(
        tester.getBottomRight(find.text('Temp')).dy,
        lessThan(size.height - 24),
      );
      final connection = tester.getRect(
        find.byKey(const ValueKey('device-connection-panel')),
      );
      final capabilities = tester.getRect(
        find.byKey(const ValueKey('device-capabilities-panel')),
      );
      expect(connection.left, closeTo(capabilities.left, 1));
      expect(connection.width, closeTo(capabilities.width, 1));
      expect(capabilities.top - connection.bottom, closeTo(20, 1));
      expect(tester.takeException(), isNull);
      await unmount(tester);
    });
  }
  testWidgets('Device keeps enlarged text and pause control usable', (
    tester,
  ) async {
    final api = FakeApi();
    await mount(tester, api, const Size(1280, 900), scale: 1.3);
    await tester.tap(find.byKey(const ValueKey('nav-2')));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tester.tap(find.byTooltip('Pause live monitoring'));
    await tester.pumpAndSettle();
    final reads = api.reads;
    await tester.pump(const Duration(seconds: 5));
    expect(api.reads, reads);
    expect(find.text('Paused'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });
  testWidgets('Ctrl+Enter sends once and keeps session history', (
    tester,
  ) async {
    final api = FakeApi()..chatReply = Completer<JarvisChatReply>();
    await mount(tester, api, const Size(1440, 900));
    await tester.enterText(
      find.byKey(const ValueKey('prompt')),
      'Show system status',
    );
    await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
    await tester.pump();
    expect(api.chats, 1);
    api.chatReply!.complete(
      const JarvisChatReply(reply: 'A real reply.', toolResults: []),
    );
    await tester.pumpAndSettle();
    expect(find.text('A real reply.'), findsOneWidget);
    expect(find.text('Read reply'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('nav-1')));
    await tester.pumpAndSettle();
    expect(find.text('Show system status'), findsOneWidget);
    await unmount(tester);
  });
  testWidgets('voice input is visible but stays unconnected', (tester) async {
    await mount(tester, FakeApi(), const Size(1440, 900));
    await tester.tap(find.byKey(const ValueKey('voice-input')));
    await tester.pumpAndSettle();
    expect(
      find.text(
        'Voice input is planned. No microphone audio is being recorded.',
      ),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });
  testWidgets('offline UI never labels old readings as live', (tester) async {
    final api = FakeApi()..offline = true;
    await mount(tester, api, const Size(1440, 900));
    expect(find.text('Core not connected'), findsOneWidget);
    expect(find.text('Live'), findsNothing);
    expect(find.text('Unavailable'), findsOneWidget);
    await unmount(tester);
  });
  testWidgets(
    'tool evidence does not read the conversation scroll offset as a bool',
    (tester) async {
      final api = FakeApi()..chatReply = Completer<JarvisChatReply>();
      await mount(tester, api, const Size(1440, 900));
      await tester.enterText(
        find.byKey(const ValueKey('prompt')),
        'Test tool result display',
      );
      await tester.tap(find.byKey(const ValueKey('send')));
      await tester.pump();
      // Exercise the same scroll persistence path as a real scroll gesture.
      final conversation = find.byKey(const PageStorageKey('conversation'));
      final scrollable = find
          .descendant(of: conversation, matching: find.byType(Scrollable))
          .first;
      final position = tester.state<ScrollableState>(scrollable).position;
      position.jumpTo(1);
      final context = tester.element(conversation);
      expect(PageStorage.of(context).readState(context), isA<double>());
      api.chatReply!.complete(
        const JarvisChatReply(
          reply: 'Tool finished.',
          toolResults: [
            {
              'tool_name': 'open_app',
              'success': true,
              'status': 'completed',
              'result': 'Chrome opened successfully.',
            },
          ],
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(find.text('open_app'), findsOneWidget);
      await tester.tap(find.text('open_app'));
      await tester.pumpAndSettle();
      expect(PageStorage.of(context).readState(context), isA<double>());
      expect(
        find.textContaining('Chrome opened successfully.'),
        findsOneWidget,
      );
      await tester.tap(find.byKey(const ValueKey('nav-1')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('nav-0')));
      await tester.pumpAndSettle();
      expect(
        find.textContaining('Chrome opened successfully.'),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
      await unmount(tester);
    },
  );
  testWidgets('composer grows upward from one line and stops at five', (
    tester,
  ) async {
    await mount(tester, FakeApi(), const Size(1440, 900));
    final composer = find.byKey(const ValueKey('composer'));
    final prompt = find.byKey(const ValueKey('prompt'));
    final single = tester.getRect(composer);
    expect(single.height, lessThan(80));
    await tester.enterText(prompt, 'One line');
    await tester.pump();
    expect(tester.getRect(composer).height, single.height);
    await tester.enterText(prompt, 'Automatically wrapping content ' * 10);
    await tester.pump();
    expect(tester.getRect(composer).height, greaterThan(single.height));
    await tester.enterText(prompt, 'Line one\nLine two');
    await tester.pump();
    final doubleLine = tester.getRect(composer);
    expect(doubleLine.top, lessThan(single.top));
    expect(doubleLine.bottom, closeTo(single.bottom, .1));
    await tester.enterText(prompt, '1\n2\n3\n4\n5');
    await tester.pump();
    final five = tester.getRect(composer);
    await tester.enterText(prompt, '1\n2\n3\n4\n5\n6\n7');
    await tester.pump();
    expect(tester.getRect(composer).height, five.height);
    await tester.enterText(prompt, '');
    await tester.pump();
    expect(tester.getRect(composer), single);
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });

  testWidgets('double Enter sends once, Shift Enter and IME never send', (
    tester,
  ) async {
    final api = FakeApi()..chatReply = Completer<JarvisChatReply>();
    await mount(tester, api, const Size(1440, 900));
    final prompt = find.byKey(const ValueKey('prompt'));
    await tester.enterText(prompt, '你好');
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
    expect(api.chats, 0);
    expect(tester.widget<TextField>(prompt).controller!.text, '你好\n\n');

    tester.testTextInput.updateEditingValue(
      const TextEditingValue(
        text: 'nihao',
        selection: TextSelection.collapsed(offset: 5),
        composing: TextRange(start: 0, end: 5),
      ),
    );
    await tester.pump();
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    expect(api.chats, 0);
    expect(tester.widget<TextField>(prompt).controller!.text, 'nihao');

    await tester.enterText(prompt, '你好');
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    expect(api.chats, 0);
    expect(tester.widget<TextField>(prompt).controller!.text, '你好\n');
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.pump();
    expect(api.messages, ['你好']);
    api.chatReply!.complete(
      const JarvisChatReply(reply: 'Received.', toolResults: []),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });

  testWidgets('typing between Enter presses resets double Enter', (
    tester,
  ) async {
    final api = FakeApi();
    await mount(tester, api, const Size(1440, 900));
    final prompt = find.byKey(const ValueKey('prompt'));
    await tester.enterText(prompt, 'First');
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.enterText(prompt, 'First\nSecond');
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    expect(api.chats, 0);
    expect(
      tester.widget<TextField>(prompt).controller!.text,
      'First\nSecond\n',
    );
    await tester.sendKeyEvent(LogicalKeyboardKey.enter);
    await tester.pumpAndSettle();
    expect(api.messages, ['First\nSecond']);
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });

  testWidgets(
    'request failures go to Errors without dumping details into chat',
    (tester) async {
      final log = AppErrorLog();
      addTearDown(log.dispose);
      final api = FakeApi()..chatReply = Completer<JarvisChatReply>();
      await mount(tester, api, const Size(1440, 900), errorLog: log);
      await tester.enterText(
        find.byKey(const ValueKey('prompt')),
        'Test request',
      );
      await tester.tap(find.byKey(const ValueKey('send')));
      await tester.pump();
      api.chatReply!.completeError(
        const JarvisApiException('Internal request diagnostic.'),
        StackTrace.fromString('test request stack'),
      );
      await tester.pumpAndSettle();
      expect(log.entries.single.source, 'Request');
      expect(find.text('Internal request diagnostic.'), findsNothing);
      expect(find.text('Failed'), findsOneWidget);
      await tester.tap(find.text('View errors'));
      await tester.pumpAndSettle();
      expect(find.text('Error log'), findsOneWidget);
      expect(find.text('Internal request diagnostic.'), findsOneWidget);
      await tester.tap(find.text('Internal request diagnostic.'));
      await tester.pumpAndSettle();
      expect(find.textContaining('test request stack'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await unmount(tester);
    },
  );

  testWidgets(
    'failed tool details are collected while successful evidence remains',
    (tester) async {
      final log = AppErrorLog();
      addTearDown(log.dispose);
      final api = FakeApi()..chatReply = Completer<JarvisChatReply>();
      await mount(tester, api, const Size(1440, 900), errorLog: log);
      await tester.enterText(
        find.byKey(const ValueKey('prompt')),
        'Test tools',
      );
      await tester.tap(find.byKey(const ValueKey('send')));
      await tester.pump();
      api.chatReply!.complete(
        const JarvisChatReply(
          reply: 'Review the failed tool.',
          toolResults: [
            {
              'tool_name': 'open_app',
              'success': true,
              'result': 'first evidence',
            },
            {
              'tool_name': 'open_app',
              'success': true,
              'result': 'second evidence',
            },
            {
              'tool_name': 'inspect_files',
              'success': false,
              'error': 'File could not be read.',
            },
          ],
        ),
      );
      await tester.pumpAndSettle();
      expect(log.entries.single.source, 'Tool');
      expect(log.entries.single.details, contains('File could not be read.'));
      expect(find.text('Review result'), findsOneWidget);
      final first = find.byKey(const PageStorageKey('tool-result-0-0'));
      await tester.tap(
        find.descendant(of: first, matching: find.text('open_app')),
      );
      await tester.pumpAndSettle();
      expect(find.textContaining('first evidence'), findsOneWidget);
      expect(find.textContaining('second evidence'), findsNothing);
      await tester.tap(find.byKey(const ValueKey('nav-4')));
      await tester.pumpAndSettle();
      expect(find.text('inspect_files failed'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('nav-0')));
      await tester.pumpAndSettle();
      expect(find.textContaining('first evidence'), findsOneWidget);
      expect(find.textContaining('second evidence'), findsNothing);
      expect(tester.takeException(), isNull);
      await unmount(tester);
    },
  );

  testWidgets('connection errors record transitions instead of every poll', (
    tester,
  ) async {
    final log = AppErrorLog();
    addTearDown(log.dispose);
    final api = FakeApi()..offline = true;
    await mount(tester, api, const Size(1440, 900), errorLog: log);
    await tester.pump(const Duration(seconds: 2));
    await tester.pump(const Duration(seconds: 2));
    expect(log.entries.single.source, 'Connection');
    expect(log.entries.single.occurrences, 1);
    api.offline = false;
    await tester.pump(const Duration(seconds: 2));
    api.offline = true;
    await tester.pump(const Duration(seconds: 2));
    expect(log.entries.single.occurrences, 2);
    expect(tester.takeException(), isNull);
    await unmount(tester);
  });

  testWidgets('monitor pauses, resumes and caps history', (tester) async {
    final api = FakeApi();
    final monitor = RuntimeMonitor(api)..start();
    await tester.pump();
    expect(api.reads, 1);
    await tester.pump(const Duration(seconds: 2));
    expect(api.reads, 2);
    monitor.didChangeAppLifecycleState(AppLifecycleState.hidden);
    await tester.pump(const Duration(seconds: 10));
    expect(api.reads, 2);
    monitor.didChangeAppLifecycleState(AppLifecycleState.resumed);
    await tester.pump();
    expect(api.reads, 3);
    monitor.setEnabled(false);
    await tester.pump(const Duration(seconds: 10));
    expect(api.reads, 3);
    for (var i = 0; i < 65; i++) {
      await monitor.refresh();
    }
    expect(monitor.history.length, 60);
    monitor.dispose();
    api.close();
  });
  testWidgets('monitor never overlaps slow requests', (tester) async {
    final api = FakeApi()..pending = Completer<SystemSample>();
    final monitor = RuntimeMonitor(api)..start();
    await tester.pump();
    await tester.pump(const Duration(seconds: 10));
    expect(api.reads, 1);
    monitor.dispose();
    api.pending!.complete(
      SystemSample(
        cpu: 1,
        memory: 1,
        usedBytes: 1,
        totalBytes: 100,
        sampledAt: DateTime.now(),
      ),
    );
    await tester.pump();
    api.close();
    expect(tester.takeException(), isNull);
  });
}
