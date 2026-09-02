import 'package:flutter/material.dart';

import 'console_theme.dart';
import 'jarvis_api.dart';
import 'runtime_monitor.dart';

String clockLabel(DateTime time) {
  final local = time.toLocal();
  return '${local.hour.toString().padLeft(2, '0')}:'
      '${local.minute.toString().padLeft(2, '0')}:'
      '${local.second.toString().padLeft(2, '0')}';
}

class RuntimePanel extends StatelessWidget {
  const RuntimePanel({super.key, required this.monitor, this.expanded = false});
  final RuntimeMonitor monitor;
  final bool expanded;

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: monitor,
    builder: (context, _) => LayoutBuilder(
      builder: (context, constraints) {
        final data = monitor.sample;
        final stale = monitor.error != null || !monitor.polling;
        final scale = MediaQuery.textScalerOf(context).scale(12) / 12;
        final wide = expanded && constraints.maxWidth >= 540 * scale;
        final cpu = _Metric(
          label: 'CPU',
          value: data?.cpu,
          stale: stale,
          description: 'Overall utilization',
          history: monitor.history,
          memory: false,
          height: expanded ? 72 : 56,
        );
        final memory = _Metric(
          label: 'Memory',
          value: data?.memory,
          stale: stale,
          description: data == null
              ? 'Physical memory'
              : '${(data.usedBytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} / '
                    '${(data.totalBytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GiB',
          history: monitor.history,
          memory: true,
          height: expanded ? 72 : 56,
        );
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.monitor_heart_outlined, size: 19),
                const SizedBox(width: 9),
                const Expanded(
                  child: Text(
                    'System monitor',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                  ),
                ),
                IconButton(
                  tooltip: monitor.enabled
                      ? 'Pause live monitoring'
                      : 'Resume live monitoring',
                  onPressed: () => monitor.setEnabled(!monitor.enabled),
                  icon: Icon(
                    monitor.enabled ? Icons.pause : Icons.play_arrow,
                    size: 18,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 12,
              runSpacing: 8,
              children: [
                StatusLabel(
                  monitor.error != null
                      ? 'Unavailable'
                      : !monitor.polling
                      ? 'Paused'
                      : data == null
                      ? 'Connecting'
                      : 'Live',
                  color: stale ? ConsoleColors.warning : ConsoleColors.good,
                ),
                Text('Every ${monitor.intervalSeconds}s', style: metadataStyle),
              ],
            ),
            const SizedBox(height: 24),
            if (wide)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(child: cpu),
                  const SizedBox(width: 28),
                  Expanded(child: memory),
                ],
              )
            else ...[
              cpu,
              const SizedBox(height: 24),
              memory,
            ],
            if (data != null) ...[
              for (final gpu in data.gpus) ...[
                const SizedBox(height: 24),
                if (expanded) ...[
                  const Divider(height: 1),
                  const SizedBox(height: 20),
                ],
                _GpuMetric(gpu: gpu, stale: stale, horizontal: wide),
              ],
              if (data.gpus.isEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 24),
                  child: Text(
                    data.gpuError ?? 'GPU monitoring is not available.',
                    style: const TextStyle(
                      color: ConsoleColors.muted,
                      fontSize: 12,
                      height: 1.6,
                    ),
                  ),
                ),
            ],
            const SizedBox(height: 18),
            if (data != null)
              Text(
                '${stale ? 'Last sample' : 'Updated'} ${clockLabel(data.sampledAt)}',
                style: metadataStyle.copyWith(fontSize: 11),
              ),
            if (monitor.error != null) ...[
              const SizedBox(height: 12),
              Text(
                monitor.error!,
                style: const TextStyle(
                  color: ConsoleColors.warning,
                  fontSize: 12,
                ),
              ),
              TextButton.icon(
                onPressed: monitor.refresh,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Reconnect'),
              ),
            ],
            const SizedBox(height: 22),
            const Divider(),
            const SizedBox(height: 12),
            const Text(
              'Local runtime',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 14),
            if (wide)
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: _RuntimeField(
                      'API',
                      monitor.online ? 'Connected' : 'Not connected',
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _RuntimeField(
                      'Model',
                      monitor.health?.model ?? 'Not available',
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _RuntimeField(
                      'Routing',
                      monitor.health?.routingMode ?? 'Not available',
                    ),
                  ),
                ],
              )
            else ...[
              RuntimeRow('API', monitor.online ? 'Connected' : 'Not connected'),
              RuntimeRow('Model', monitor.health?.model ?? 'Not available'),
              RuntimeRow(
                'Routing',
                monitor.health?.routingMode ?? 'Not available',
              ),
            ],
            const SizedBox(height: 10),
            const Text('127.0.0.1:8765', style: metadataStyle),
            const SizedBox(height: 10),
            const Text(
              'API connection does not verify model availability.',
              style: TextStyle(
                fontSize: 11,
                color: ConsoleColors.dim,
                height: 1.5,
              ),
            ),
          ],
        );
      },
    ),
  );
}

class _GpuMetric extends StatelessWidget {
  const _GpuMetric({
    required this.gpu,
    required this.stale,
    this.horizontal = false,
  });
  final GpuSample gpu;
  final bool stale;
  final bool horizontal;
  @override
  Widget build(BuildContext context) {
    final used = gpu.usedBytes;
    final total = gpu.totalBytes;
    final memory = used != null && total != null && total > 0;
    final utilization = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            const Expanded(
              child: Text('GPU', style: TextStyle(fontWeight: FontWeight.w600)),
            ),
            Text(
              gpu.utilization?.toStringAsFixed(0) ?? 'N/A',
              style: metadataStyle.copyWith(
                fontSize: 30,
                letterSpacing: -1,
                color: stale ? ConsoleColors.muted : ConsoleColors.ink,
              ),
            ),
            if (gpu.utilization != null) const Text(' %', style: metadataStyle),
          ],
        ),
        const SizedBox(height: 5),
        Text(
          gpu.name,
          style: const TextStyle(
            color: ConsoleColors.muted,
            fontSize: 11,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 14),
        LinearProgressIndicator(
          value: (gpu.utilization ?? 0) / 100,
          minHeight: 3,
          color: stale ? ConsoleColors.dim : ConsoleColors.accent,
          backgroundColor: ConsoleColors.line,
          semanticsLabel: 'GPU utilization',
          semanticsValue: gpu.utilization == null
              ? 'Not available'
              : '${gpu.utilization}%',
        ),
      ],
    );
    final memoryLabel = memory
        ? '${(used / 1073741824).toStringAsFixed(1)} / '
              '${(total / 1073741824).toStringAsFixed(1)} GiB'
        : 'Not available';
    final temperatureLabel = gpu.temperature == null
        ? 'Not available'
        : '${gpu.temperature} °C';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (horizontal)
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(flex: 5, child: utilization),
              const SizedBox(width: 28),
              Expanded(
                flex: 3,
                child: Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Column(
                    children: [
                      RuntimeRow('VRAM', memoryLabel),
                      RuntimeRow('Temp', temperatureLabel),
                    ],
                  ),
                ),
              ),
            ],
          )
        else ...[
          utilization,
          const SizedBox(height: 12),
          RuntimeRow('VRAM', memoryLabel),
          RuntimeRow('Temp', temperatureLabel),
        ],
        const SizedBox(height: 10),
        const Text(
          'NVIDIA driver • NVML',
          style: TextStyle(fontSize: 10, color: ConsoleColors.dim),
        ),
      ],
    );
  }
}

class _RuntimeField extends StatelessWidget {
  const _RuntimeField(this.label, this.value);
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        label,
        style: const TextStyle(color: ConsoleColors.muted, fontSize: 12),
      ),
      const SizedBox(height: 6),
      Text(value, style: metadataStyle.copyWith(color: ConsoleColors.ink)),
    ],
  );
}

class RuntimeRow extends StatelessWidget {
  const RuntimeRow(this.label, this.value, {super.key});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 68,
          child: Text(
            label,
            style: const TextStyle(color: ConsoleColors.muted, fontSize: 12),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: metadataStyle.copyWith(color: ConsoleColors.ink),
          ),
        ),
      ],
    ),
  );
}

class _Metric extends StatelessWidget {
  const _Metric({
    required this.label,
    required this.value,
    required this.description,
    required this.history,
    required this.memory,
    required this.stale,
    required this.height,
  });
  final String label;
  final double? value;
  final String description;
  final List<SystemSample> history;
  final bool memory;
  final bool stale;
  final double height;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(
        crossAxisAlignment: CrossAxisAlignment.baseline,
        textBaseline: TextBaseline.alphabetic,
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          Text(
            value?.toStringAsFixed(1) ?? 'N/A',
            style: metadataStyle.copyWith(
              fontSize: 30,
              letterSpacing: -1,
              color: stale ? ConsoleColors.muted : ConsoleColors.ink,
            ),
          ),
          if (value != null) const Text(' %', style: metadataStyle),
        ],
      ),
      const SizedBox(height: 5),
      Text(
        description,
        style: const TextStyle(color: ConsoleColors.muted, fontSize: 11),
      ),
      const SizedBox(height: 14),
      Semantics(
        label:
            '$label utilization history, 0 to 100 percent, '
            '${history.length} recorded samples',
        child: RepaintBoundary(
          child: SizedBox(
            height: height,
            width: double.infinity,
            child: CustomPaint(
              painter: _TelemetryChart(List.of(history), memory, stale),
            ),
          ),
        ),
      ),
      const SizedBox(height: 6),
      Wrap(
        spacing: 16,
        runSpacing: 4,
        children: [
          Text(
            history.length < 2
                ? 'Collecting samples'
                : '${history.last.sampledAt.difference(history.first.sampledAt).inSeconds}s history',
            style: metadataStyle.copyWith(fontSize: 10),
          ),
          Text('0–100%', style: metadataStyle.copyWith(fontSize: 10)),
        ],
      ),
    ],
  );
}

class _TelemetryChart extends CustomPainter {
  _TelemetryChart(this.samples, this.memory, this.stale);
  final List<SystemSample> samples;
  final bool memory;
  final bool stale;
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = ConsoleColors.line.withValues(alpha: .6)
      ..strokeWidth = 1;
    for (var i = 0; i <= 2; i++) {
      final y = size.height * i / 2;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
    if (samples.isEmpty) return;
    final end = samples.last.sampledAt.millisecondsSinceEpoch;
    final start = samples.first.sampledAt.millisecondsSinceEpoch;
    final span = (end - start).clamp(2000, 0x7fffffff);
    final points = samples
        .map(
          (s) => Offset(
            samples.length == 1
                ? size.width
                : (s.sampledAt.millisecondsSinceEpoch - start) /
                      span *
                      size.width,
            size.height * (1 - (memory ? s.memory : s.cpu) / 100),
          ),
        )
        .toList();
    final color = stale ? ConsoleColors.dim : ConsoleColors.accent;
    if (points.length > 1) {
      final line = Path()..moveTo(points.first.dx, points.first.dy);
      for (final point in points.skip(1)) {
        line.lineTo(point.dx, point.dy);
      }
      final area = Path.from(line)
        ..lineTo(points.last.dx, size.height)
        ..lineTo(points.first.dx, size.height)
        ..close();
      canvas.drawPath(
        area,
        Paint()
          ..shader = LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              color.withValues(alpha: .17),
              color.withValues(alpha: .01),
            ],
          ).createShader(Offset.zero & size),
      );
      canvas.drawPath(
        line,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.5
          ..strokeJoin = StrokeJoin.round,
      );
    }
    canvas.drawCircle(points.last, 2.5, Paint()..color = color);
  }

  @override
  bool shouldRepaint(_TelemetryChart old) =>
      stale != old.stale ||
      memory != old.memory ||
      samples.length != old.samples.length ||
      (samples.isNotEmpty &&
          old.samples.isNotEmpty &&
          samples.last != old.samples.last);
}
