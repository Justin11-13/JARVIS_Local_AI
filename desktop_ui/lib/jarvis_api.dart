import 'dart:async';
import 'dart:convert';
import 'dart:io';

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
      routingMode: response['routing_mode'] as String? ?? 'unknown',
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
      toolResults: (response['tool_results'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>(),
    );
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
    required this.routingMode,
  });
  final String status;
  final String brain;
  final String routingMode;
}

class JarvisChatReply {
  const JarvisChatReply({required this.reply, required this.toolResults});
  final String reply;
  final List<Map<String, dynamic>> toolResults;
}

class JarvisApiException implements Exception {
  const JarvisApiException(this.message);
  final String message;
}
