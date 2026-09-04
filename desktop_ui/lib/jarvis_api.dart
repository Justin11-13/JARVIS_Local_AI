import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

class JarvisApi {
  JarvisApi({HttpClient? client}) : _client = client ?? HttpClient() {
    _client.connectionTimeout = const Duration(seconds: 3);
  }

  final HttpClient _client;
  final Uri _base = Uri(scheme: 'http', host: '127.0.0.1', port: 8765);

  void close() => _client.close(force: true);

  Future<SystemSample> telemetry() async =>
      SystemSample.fromJson(await _request('GET', '/api/telemetry'));

  Future<JarvisHealth> health() async {
    final response = await _request('GET', '/api/health');
    return JarvisHealth(
      status: response['status'] as String? ?? 'unknown',
      brain: response['brain'] as String? ?? 'unknown',
    );
  }

  Future<String> systemInfo() async {
    final response = await _request('GET', '/api/system-info');
    return response['result'] as String? ??
        response['error'] as String? ??
        'System information is unavailable.';
  }

  Future<JarvisChatReply> sendMessage(String message) async {
    final response = await _request(
      'POST',
      '/api/chat',
      body: {'message': message},
    );
    return JarvisChatReply(
      reply: response['reply'] as String? ?? 'No response was returned.',
      speech:
          response['speech'] as String? ??
          response['reply'] as String? ??
          'No response was returned.',
      toolResults: (response['tool_results'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>(),
      citations: (response['citations'] as List<dynamic>? ?? const [])
          .map(
            (item) => ObsidianCitation.fromJson(item as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  Future<List<ObsidianVault>> obsidianVaults() async {
    final response = await _request('GET', '/api/obsidian/vaults');
    return (response['vaults'] as List<dynamic>? ?? const [])
        .map((item) => ObsidianVault.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<void> registerObsidianVault({
    required String id,
    required String name,
    required String path,
  }) async {
    await _request(
      'POST',
      '/api/obsidian/vaults',
      body: {
        'vault_id': id,
        'name': name,
        'path': path,
        'default_access': 'excluded',
      },
    );
  }

  Future<void> removeObsidianVault(String id) async {
    await _request('DELETE', '/api/obsidian/vaults/$id');
  }

  Future<void> reindexObsidian() async {
    await _request('POST', '/api/obsidian/reindex');
  }

  Future<void> openObsidianNote(String vaultId, String relativePath) async {
    await _request(
      'POST',
      '/api/obsidian/open',
      body: {'vault_id': vaultId, 'relative_path': relativePath},
    );
  }

  Future<List<JarvisHistoryTurn>> conversationHistory() async {
    final response = await _request('GET', '/api/chat/history');
    return (response['turns'] as List<dynamic>? ?? const [])
        .map((turn) => JarvisHistoryTurn.fromJson(turn as Map<String, dynamic>))
        .toList();
  }

  Future<Uint8List> synthesizeFishSpeech(String text) async {
    try {
      final request = await _client.openUrl(
        'POST',
        _base.replace(path: '/api/speech'),
      );
      request.headers.contentType = ContentType.json;
      request.write(jsonEncode({'text': text}));
      final response = await request.close();
      final bytes = await response.fold<List<int>>(
        [],
        (value, chunk) => value..addAll(chunk),
      );
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final message = utf8.decode(bytes, allowMalformed: true);
        final decoded = message.isEmpty
            ? <String, dynamic>{}
            : jsonDecode(message) as Map<String, dynamic>;
        throw JarvisApiException(
          decoded['detail'] as String? ?? 'Fish Audio speech is unavailable.',
        );
      }
      return Uint8List.fromList(bytes);
    } on SocketException {
      throw const JarvisApiException(
        'JARVIS Core is offline. Start it with .\\run-desktop.ps1.',
      );
    } on HttpException catch (error) {
      throw JarvisApiException('Fish Audio speech failed: ${error.message}');
    } on FormatException {
      throw const JarvisApiException(
        'Fish Audio returned an invalid response.',
      );
    }
  }

  Future<void> speakWithWindowsVoice(String text) =>
      _sendSpeechCommand('/api/system-speech', body: {'text': text});

  Future<WindowsSpeechSettings> windowsSpeechSettings() async =>
      WindowsSpeechSettings.fromJson(
        await _request('GET', '/api/system-speech/settings'),
      );

  Future<void> stopWindowsVoice() =>
      _sendSpeechCommand('/api/system-speech/stop');

  Future<void> _sendSpeechCommand(
    String path, {
    Map<String, dynamic>? body,
  }) async {
    try {
      final request = await _client.openUrl('POST', _base.replace(path: path));
      request.headers.contentType = ContentType.json;
      if (body != null) request.write(jsonEncode(body));
      final response = await request.close();
      final bytes = await response.fold<List<int>>(
        [],
        (value, chunk) => value..addAll(chunk),
      );
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final decoded = bytes.isEmpty
            ? <String, dynamic>{}
            : jsonDecode(utf8.decode(bytes, allowMalformed: true))
                  as Map<String, dynamic>;
        throw JarvisApiException(
          decoded['detail'] as String? ??
              'Windows system voice is unavailable.',
        );
      }
    } on SocketException {
      throw const JarvisApiException(
        'JARVIS Core is offline. Start it with .\\run-desktop.ps1.',
      );
    } on HttpException catch (error) {
      throw JarvisApiException('Windows system voice failed: ${error.message}');
    } on FormatException {
      throw const JarvisApiException(
        'Windows system voice returned an invalid response.',
      );
    }
  }

  Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    try {
      final request = await _client.openUrl(method, _base.replace(path: path));
      request.headers.contentType = ContentType.json;
      if (body != null) request.write(jsonEncode(body));
      // Chat may legitimately take a long time. Monitoring must never pile up.
      final timeout = method == 'GET' ? const Duration(seconds: 3) : null;
      final pending = request.close();
      final response = timeout == null
          ? await pending
          : await pending.timeout(
              timeout,
              onTimeout: () {
                request.abort();
                throw TimeoutException('Local API timed out.');
              },
            );
      final reading = utf8.decoder.bind(response).join();
      final content = timeout == null
          ? await reading
          : await reading.timeout(
              timeout,
              onTimeout: () {
                request.abort();
                throw TimeoutException('Local API timed out.');
              },
            );
      final decoded = content.isEmpty
          ? <String, dynamic>{}
          : jsonDecode(content) as Map<String, dynamic>;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw JarvisApiException(
          decoded['detail'] as String? ??
              'JARVIS API returned ${response.statusCode}.',
        );
      }
      return decoded;
    } on SocketException {
      throw JarvisApiException(
        'JARVIS Core is offline. Start it with .\\run-desktop.ps1.',
      );
    } on HttpException catch (error) {
      throw JarvisApiException('JARVIS Core request failed: ${error.message}');
    } on FormatException {
      throw JarvisApiException('JARVIS Core returned an invalid response.');
    } on TimeoutException {
      throw JarvisApiException(
        'JARVIS Core did not respond. Retrying automatically.',
      );
    }
  }
}

class SystemSample {
  const SystemSample({
    required this.cpu,
    required this.memory,
    required this.usedBytes,
    required this.totalBytes,
    required this.sampledAt,
    this.gpus = const [],
    this.gpuError,
  });

  factory SystemSample.fromJson(Map<String, dynamic> json) {
    final cpu = (json['cpu_percent'] as num?)?.toDouble();
    final memory = (json['memory_percent'] as num?)?.toDouble();
    final date = DateTime.tryParse(json['sampled_at'] as String? ?? '');
    if (cpu == null ||
        memory == null ||
        date == null ||
        !cpu.isFinite ||
        !memory.isFinite ||
        cpu < 0 ||
        cpu > 100 ||
        memory < 0 ||
        memory > 100) {
      throw const JarvisApiException(
        'Telemetry is unavailable. Restart JARVIS Core.',
      );
    }
    return SystemSample(
      cpu: cpu,
      memory: memory,
      usedBytes: (json['memory_used_bytes'] as num?)?.toInt() ?? 0,
      totalBytes: (json['memory_total_bytes'] as num?)?.toInt() ?? 0,
      sampledAt: date,
      gpus: (json['gpus'] as List<dynamic>? ?? const [])
          .map((gpu) => GpuSample.fromJson(gpu as Map<String, dynamic>))
          .toList(),
      gpuError: json['gpu_error'] as String?,
    );
  }

  final double cpu;
  final double memory;
  final int usedBytes;
  final int totalBytes;
  final DateTime sampledAt;
  final List<GpuSample> gpus;
  final String? gpuError;
}

class GpuSample {
  const GpuSample({
    required this.id,
    required this.name,
    this.utilization,
    this.usedBytes,
    this.totalBytes,
    this.temperature,
  });
  factory GpuSample.fromJson(Map<String, dynamic> json) {
    final utilization = (json['utilization_percent'] as num?)?.toDouble();
    return GpuSample(
      id: json['id']?.toString() ?? '0',
      name: json['name'] as String? ?? 'NVIDIA GPU',
      utilization:
          utilization != null &&
              utilization.isFinite &&
              utilization >= 0 &&
              utilization <= 100
          ? utilization
          : null,
      usedBytes: (json['memory_used_bytes'] as num?)?.toInt(),
      totalBytes: (json['memory_total_bytes'] as num?)?.toInt(),
      temperature: (json['temperature_c'] as num?)?.toInt(),
    );
  }
  final String id;
  final String name;
  final double? utilization;
  final int? usedBytes;
  final int? totalBytes;
  final int? temperature;
}

class JarvisHealth {
  const JarvisHealth({
    required this.status,
    required this.brain,
  });
  final String status;
  final String brain;
}

class JarvisChatReply {
  const JarvisChatReply({
    required this.reply,
    String? speech,
    required this.toolResults,
    this.citations = const [],
  }) : speech = speech ?? reply;
  final String reply;
  final String speech;
  final List<Map<String, dynamic>> toolResults;
  final List<ObsidianCitation> citations;
}

class ObsidianCitation {
  const ObsidianCitation({
    required this.title,
    required this.sourcePath,
    required this.section,
    required this.uri,
    required this.vaultId,
  });
  factory ObsidianCitation.fromJson(Map<String, dynamic> json) =>
      ObsidianCitation(
        title: json['title'] as String? ?? 'Obsidian note',
        sourcePath: json['source_path'] as String? ?? '',
        section: json['section'] as String? ?? '',
        uri: json['obsidian_uri'] as String? ?? '',
        vaultId: json['vault_id'] as String? ?? '',
      );
  final String title;
  final String sourcePath;
  final String section;
  final String uri;
  final String vaultId;
}

class ObsidianVault {
  const ObsidianVault({
    required this.id,
    required this.name,
    required this.indexedChunks,
    required this.defaultAccess,
  });
  factory ObsidianVault.fromJson(Map<String, dynamic> json) => ObsidianVault(
    id: json['id'] as String? ?? '',
    name: json['name'] as String? ?? 'Vault',
    indexedChunks: (json['indexed_chunks'] as num?)?.toInt() ?? 0,
    defaultAccess: json['default_access'] as String? ?? 'excluded',
  );
  final String id;
  final String name;
  final int indexedChunks;
  final String defaultAccess;
}

class JarvisHistoryTurn {
  const JarvisHistoryTurn({
    required this.user,
    required this.assistant,
    required this.speech,
    required this.createdAt,
  });

  factory JarvisHistoryTurn.fromJson(Map<String, dynamic> json) {
    final assistant = json['assistant'] as String? ?? '';
    return JarvisHistoryTurn(
      user: json['user'] as String? ?? '',
      assistant: assistant,
      speech: json['speech'] as String? ?? assistant,
      createdAt:
          DateTime.tryParse(json['created_at'] as String? ?? '')?.toLocal() ??
          DateTime.now(),
    );
  }

  final String user;
  final String assistant;
  final String speech;
  final DateTime createdAt;
}

class WindowsSpeechSettings {
  const WindowsSpeechSettings({
    required this.voice,
    required this.speed,
    required this.source,
  });

  factory WindowsSpeechSettings.fromJson(Map<String, dynamic> json) =>
      WindowsSpeechSettings(
        voice: json['voice'] as String? ?? 'Unknown Windows voice',
        speed: (json['speed'] as num?)?.toInt() ?? 0,
        source: json['source'] as String? ?? 'Windows Speech settings',
      );

  final String voice;
  final int speed;
  final String source;
}

class JarvisApiException implements Exception {
  const JarvisApiException(this.message);
  final String message;
}
