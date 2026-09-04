import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'console_theme.dart';

/// A quiet, non-interactive holographic field for the desktop shell.
/// It contains no simulated device or network data.
class HologramBackdrop extends StatelessWidget {
  const HologramBackdrop({super.key});

  @override
  Widget build(BuildContext context) => ExcludeSemantics(
    child: RepaintBoundary(
      child: CustomPaint(
        painter: const _HologramBackdropPainter(),
        child: const SizedBox.expand(),
      ),
    ),
  );
}

class _HologramBackdropPainter extends CustomPainter {
  const _HologramBackdropPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final bounds = Offset.zero & size;
    canvas.drawRect(
      bounds,
      Paint()
        ..shader = const RadialGradient(
          center: Alignment(.18, -.36),
          radius: 1.25,
          colors: [Color(0xFF123F59), ConsoleColors.canvas],
          stops: [0, .68],
        ).createShader(bounds),
    );

    final lines = Paint()
      ..color = ConsoleColors.accent.withValues(alpha: .035)
      ..strokeWidth = 1;
    for (var y = 28.0; y < size.height; y += 48) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), lines);
    }

    final center = Offset(size.width * .72, size.height * .18);
    final rings = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    for (final radius in [72.0, 132.0, 224.0]) {
      rings.color = ConsoleColors.accent.withValues(
        alpha: radius == 132 ? .12 : .06,
      );
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        -math.pi * .82,
        math.pi * 1.18,
        false,
        rings,
      );
    }

    final markers = Paint()
      ..color = ConsoleColors.accent.withValues(alpha: .23);
    for (var index = 0; index < 12; index++) {
      final angle = -math.pi * .8 + index * math.pi * 1.16 / 11;
      final point = center + Offset(math.cos(angle), math.sin(angle)) * 224;
      canvas.drawCircle(point, index.isEven ? 1.6 : .9, markers);
    }
  }

  @override
  bool shouldRepaint(covariant _HologramBackdropPainter oldDelegate) => false;
}
