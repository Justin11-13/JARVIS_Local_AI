import 'package:desktop_ui/speech_controller.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('offers local and cloud speech providers', () {
    expect(SpeechProvider.system.label, 'Windows system voice');
    expect(SpeechProvider.fish.label, 'Fish Audio cloud');
  });
}
