import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'console_theme.dart';

/// A connection instrument, not a fabricated utilization gauge.
/// Its only continuous movement denotes an actual outstanding chat request.
class CoreIndicator extends StatefulWidget {
  const CoreIndicator({
    super.key,
    this.size = 168,
    this.online = true,
    this.busy = false,
    this.reduceMotion = false,
    this.label = true,
  });
  final double size;
  final bool online;
  final bool busy;
  final bool reduceMotion;
  final bool label;

  @override
  State<CoreIndicator> createState() => _CoreIndicatorState();
}

class _CoreIndicatorState extends State<CoreIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _turn = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 4),
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _sync();
  }

  @override
  void didUpdateWidget(covariant CoreIndicator oldWidget) {
    super.didUpdateWidget(oldWidget);
    _sync();
  }

  void _sync() {
    final animate =
        widget.busy &&
        !widget.reduceMotion &&
        !MediaQuery.disableAnimationsOf(context);
    if (animate && !_turn.isAnimating) _turn.repeat();
    if (!animate) _turn.stop();
  }

  @override
  void dispose() {
    _turn.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = widget.online ? ConsoleColors.accent : ConsoleColors.dim;
    return Semantics(
      label: widget.busy
          ? 'Request in progress'
          : widget.online
          ? 'Local API connected'
          : 'Local API disconnected',
      child: RepaintBoundary(
        child: SizedBox.square(
          dimension: widget.size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Positioned.fill(
                child: CustomPaint(
                  painter: _InstrumentPainter(
                    turn: _turn,
                    color: color,
                    detailed: widget.size > 90,
                  ),
                ),
              ),
              if (widget.label && widget.size > 90)
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      widget.busy ? Icons.bolt : Icons.memory_outlined,
                      color: color,
                      size: 27,
                    ),
                    const SizedBox(height: 10),
                    Text(
                      widget.busy
                          ? 'WORKING'
                          : widget.online
                          ? 'READY'
                          : 'OFFLINE',
                      style: metadataStyle.copyWith(
                        color: color,
                        fontSize: 10,
                        letterSpacing: 2,
                      ),
                    ),
                  ],
                )
              else
                Icon(Icons.bolt, color: color, size: widget.size * .42),
            ],
          ),
        ),
      ),
    );
  }
}

class _InstrumentPainter extends CustomPainter {
  _InstrumentPainter({
    required this.turn,
    required this.color,
    required this.detailed,
  }) : super(repaint: turn);
  final Animation<double> turn;
  final Color color;
  final bool detailed;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final r = size.shortestSide / 2;
    final paint = Paint()..style = PaintingStyle.stroke;
    paint
      ..color = color.withValues(alpha: .16)
      ..strokeWidth = 1;
    canvas.drawCircle(center, r * .73, paint);
    canvas.drawCircle(center, r * .9, paint);
    if (detailed) {
      for (var i = 0; i < 48; i++) {
        final angle = i * math.pi * 2 / 48;
        final unit = Offset(math.cos(angle), math.sin(angle));
        paint.color = color.withValues(alpha: i % 4 == 0 ? .6 : .23);
        canvas.drawLine(
          center + unit * r * .95,
          center + unit * r * (i % 4 == 0 ? .88 : .92),
          paint,
        );
      }
    }
    paint
      ..color = color
      ..strokeWidth = detailed ? 2 : 1.5;
    final rect = Rect.fromCircle(center: center, radius: r * .8);
    for (var i = 0; i < 3; i++) {
      canvas.drawArc(
        rect,
        turn.value * math.pi * 2 + i * math.pi * 2 / 3,
        math.pi * .38,
        false,
        paint,
      );
    }
    paint
      ..color = color.withValues(alpha: .28)
      ..strokeWidth = 1;
    canvas.drawCircle(center, r * .62, paint);
  }

  @override
  bool shouldRepaint(_InstrumentPainter old) =>
      old.color != color || old.detailed != detailed || old.turn != turn;
}
