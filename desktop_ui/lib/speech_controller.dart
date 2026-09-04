import 'dart:async';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';

import 'jarvis_api.dart';

enum SpeechProvider { system, fish }

extension SpeechProviderDetails on SpeechProvider {
  String get label => switch (this) {
    SpeechProvider.system => 'Windows system voice',
    SpeechProvider.fish => 'Fish Audio cloud',
  };

  String get description => switch (this) {
    SpeechProvider.system =>
      'Follows the voice and speed selected in Windows Speech settings. Nothing leaves this PC.',
    SpeechProvider.fish =>
      'Sends only the reply text to Fish Audio when you press Read reply.',
  };
}

/// Reads replies through either an installed Windows voice or selected Fish Audio.
class SpeechController extends ChangeNotifier {
  SpeechController(this._api) {
    _complete = _player.onPlayerComplete.listen((_) => _finished());
  }

  final JarvisApi _api;
  final AudioPlayer _player = AudioPlayer();
  late final StreamSubscription<void> _complete;
  bool _speaking = false;
  int _speechRun = 0;
  String? _error;

  bool get speaking => _speaking;
  String? get error => _error;

  Future<void> speak(String text, {required SpeechProvider provider}) async {
    final content = text.trim();
    if (content.isEmpty) return;
    await stop();
    final run = ++_speechRun;
    _speaking = true;
    _error = null;
    notifyListeners();

    if (provider == SpeechProvider.system) {
      await _speakSystem(content, run);
    } else {
      await _speakFish(content, run);
    }
  }

  Future<void> _speakSystem(String content, int run) async {
    try {
      await _api.speakWithWindowsVoice(content);
      if (run == _speechRun) _finished();
    } on JarvisApiException catch (error) {
      if (run != _speechRun) return;
      _speaking = false;
      _error = error.message;
      notifyListeners();
    }
  }

  Future<void> _speakFish(String content, int run) async {
    try {
      final audio = await _api.synthesizeFishSpeech(content);
      if (run != _speechRun) return;
      await _player.play(BytesSource(audio, mimeType: 'audio/wav'));
    } on JarvisApiException catch (error) {
      if (run != _speechRun) return;
      _speaking = false;
      _error = error.message;
      notifyListeners();
    } catch (_) {
      if (run != _speechRun) return;
      _speaking = false;
      _error = 'Fish Audio could not be played on this device.';
      notifyListeners();
    }
  }

  Future<void> stop() async {
    _speechRun++;
    try {
      await _api.stopWindowsVoice();
    } on JarvisApiException {
      // Stopping an already-finished local voice is safe.
    }
    await _player.stop();
    _finished();
  }

  void _finished() {
    if (!_speaking) return;
    _speaking = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _complete.cancel();
    unawaited(_stopWindowsVoiceSilently());
    unawaited(_player.dispose());
    super.dispose();
  }

  Future<void> _stopWindowsVoiceSilently() async {
    try {
      await _api.stopWindowsVoice();
    } on JarvisApiException {
      // Disposal must not report a failed request after the UI is gone.
    }
  }
}
