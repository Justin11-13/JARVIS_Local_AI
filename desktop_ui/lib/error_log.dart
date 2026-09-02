import 'dart:async';
import 'dart:ui';

import 'package:flutter/widgets.dart';

class AppErrorEntry {
  AppErrorEntry({
    required this.id,
    required this.source,
    required this.message,
    required this.details,
    required this.stack,
    required this.firstSeen,
  }) : lastSeen = firstSeen;

  final int id;
  final String source;
  final String message;
  final String details;
  final String stack;
  final DateTime firstSeen;
  DateTime lastSeen;
  int occurrences = 1;

  String get report =>
      '$source: $message\n'
      'First: ${firstSeen.toIso8601String()}\n'
      'Last: ${lastSeen.toIso8601String()}\n'
      'Occurrences: $occurrences\n\n$details'
      '${stack.isEmpty ? '' : '\n\nStack trace\n$stack'}';
}

/// Bounded, session-only diagnostics. Nothing is written to disk or uploaded.
class AppErrorLog extends ChangeNotifier {
  final _entries = <AppErrorEntry>[];
  List<AppErrorEntry> get entries => List.unmodifiable(_entries);
  int _nextId = 0;
  bool _scheduled = false;
  bool _disposed = false;

  bool get hasInterfaceErrors => _entries.any(
    (entry) => entry.source == 'UI' || entry.source == 'Runtime',
  );

  void record({
    required String source,
    required String message,
    String? details,
    StackTrace? stack,
  }) {
    if (_disposed) return;
    // Also bound individual reports; a malformed response must not exhaust RAM.
    String bounded(String text) => text.length <= 32768
        ? text
        : '${text.substring(0, 32768)}\n[Truncated at 32 KiB]';
    final summary = bounded(message);
    final body = bounded(details ?? message);
    final trace = bounded(stack?.toString() ?? '');
    final match = _entries.indexWhere(
      (entry) =>
          entry.source == source &&
          entry.message == summary &&
          entry.details == body &&
          entry.stack == trace,
    );
    if (match >= 0) {
      final entry = _entries.removeAt(match);
      entry.occurrences++;
      entry.lastSeen = DateTime.now();
      _entries.insert(0, entry);
    } else {
      _entries.insert(
        0,
        AppErrorEntry(
          id: _nextId++,
          source: source,
          message: summary,
          details: body,
          stack: trace,
          firstSeen: DateTime.now(),
        ),
      );
      if (_entries.length > 50) _entries.removeLast();
    }
    _changed();
  }

  void clear() {
    _entries.clear();
    _changed();
  }

  void _changed() {
    if (_scheduled || _disposed) return;
    _scheduled = true;
    // Flutter can report an error during build/layout. Notify outside that pass.
    scheduleMicrotask(() {
      _scheduled = false;
      if (!_disposed) notifyListeners();
    });
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}

/// Keep the existing console/IDE handlers; diagnostics must not hide failures.
class AppErrorCapture {
  AppErrorCapture(AppErrorLog log, ErrorWidgetBuilder fallback) {
    _flutterHandler = (details) {
      log.record(
        source: 'UI',
        message: details.exceptionAsString(),
        details:
            '${details.context ?? details.library ?? 'Flutter interface'}\n\n'
            '${details.exceptionAsString()}',
        stack: details.stack,
      );
      (_previousFlutter ?? FlutterError.presentError)(details);
    };
    _runtimeHandler = (error, stack) {
      log.record(source: 'Runtime', message: error.toString(), stack: stack);
      // Returning false retains the engine's normal unhandled-error logging.
      return _previousRuntime?.call(error, stack) ?? false;
    };
    _fallback = fallback;
    FlutterError.onError = _flutterHandler;
    PlatformDispatcher.instance.onError = _runtimeHandler;
    ErrorWidget.builder = _fallback;
  }

  final _previousFlutter = FlutterError.onError;
  final _previousRuntime = PlatformDispatcher.instance.onError;
  final _previousBuilder = ErrorWidget.builder;
  late final void Function(FlutterErrorDetails) _flutterHandler;
  late final bool Function(Object, StackTrace) _runtimeHandler;
  late final ErrorWidgetBuilder _fallback;

  void dispose() {
    if (FlutterError.onError == _flutterHandler) {
      FlutterError.onError = _previousFlutter;
    }
    if (PlatformDispatcher.instance.onError == _runtimeHandler) {
      PlatformDispatcher.instance.onError = _previousRuntime;
    }
    if (ErrorWidget.builder == _fallback) {
      ErrorWidget.builder = _previousBuilder;
    }
  }
}
