import 'dart:async';

import 'package:flutter/widgets.dart';

import 'jarvis_api.dart';

/// Only listeners displaying telemetry rebuild; the conversation is untouched.
class RuntimeMonitor extends ChangeNotifier with WidgetsBindingObserver {
  RuntimeMonitor(this.api);

  final JarvisApi api;
  JarvisHealth? health;
  SystemSample? sample;
  WindowsSpeechSettings? speechSettings;
  String? speechSettingsError;
  final List<SystemSample> history = [];
  String? error;
  bool online = false;
  bool refreshing = false;
  bool enabled = true;
  bool visible = true;
  int intervalSeconds = 2;
  Timer? _timer;
  DateTime? _healthChecked;
  bool _disposed = false;

  bool get polling => enabled && visible;

  void start() {
    WidgetsBinding.instance.addObserver(this);
    refresh();
    _schedule();
  }

  void setEnabled(bool value) {
    enabled = value;
    _schedule();
    notifyListeners();
    if (polling) refresh();
  }

  void setInterval(int seconds) {
    intervalSeconds = seconds;
    _schedule();
    notifyListeners();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Inactive on Windows means unfocused, not minimized: keep sampling there.
    visible =
        state == AppLifecycleState.resumed ||
        state == AppLifecycleState.inactive;
    _schedule();
    notifyListeners();
    if (polling) refresh();
  }

  void _schedule() {
    _timer?.cancel();
    if (polling && !_disposed) {
      _timer = Timer.periodic(
        Duration(seconds: intervalSeconds),
        (_) => refresh(),
      );
    }
  }

  Future<void> refresh() async {
    if (_disposed || refreshing) return;
    refreshing = true;
    try {
      if (_healthChecked == null ||
          !online ||
          DateTime.now().difference(_healthChecked!).inSeconds >= 30) {
        health = await api.health();
        if (_disposed) return;
        online = health!.status == 'ready';
        _healthChecked = DateTime.now();
      }
      final next = await api.telemetry();
      if (_disposed) return;
      try {
        speechSettings = await api.windowsSpeechSettings();
        speechSettingsError = null;
      } on JarvisApiException catch (failure) {
        speechSettings = null;
        speechSettingsError = failure.message;
      }
      if (_disposed) return;
      online = true;
      error = null;
      sample = next;
      if (history.isEmpty || next.sampledAt.isAfter(history.last.sampledAt)) {
        history.add(next);
        if (history.length > 60) history.removeAt(0);
      }
    } on JarvisApiException catch (failure) {
      if (_disposed) return;
      error = failure.message;
      // Do not advertise a live connection while requests are failing.
      online = false;
    } finally {
      refreshing = false;
      if (!_disposed) notifyListeners();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }
}
