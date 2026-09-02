/* finesse · register=product · shell=instrument-triptych · A=steel-cyan
 * B=Segoe-UI+Consolas · C=instrument-triptych · D=state-only-Flutter
 * E=precision-instrument · SOUL=7 SPECTACLE=3 DENSITY=7 */
import 'package:flutter/material.dart';

abstract final class ConsoleColors {
  static const canvas = Color(0xFF0C1014);
  static const rail = Color(0xFF11171D);
  static const panel = Color(0xFF151D24);
  static const raised = Color(0xFF1D2831);
  static const line = Color(0xFF2E3D48);
  static const ink = Color(0xFFEAF1F5);
  static const muted = Color(0xFFA2B2BE);
  static const dim = Color(0xFF879AA8);
  static const accent = Color(0xFF88D4E6);
  static const accentSoft = Color(0xFF203C46);
  static const good = Color(0xFF91D9B8);
  static const warning = Color(0xFFF0C38B);
  static const danger = Color(0xFFF1A0A0);
}

const metadataStyle = TextStyle(
  fontFamily: 'Consolas',
  fontFamilyFallback: ['Segoe UI'],
  fontSize: 12,
  color: ConsoleColors.muted,
  fontFeatures: [FontFeature.tabularFigures()],
);

ThemeData consoleTheme() {
  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    fontFamily: 'Segoe UI',
    fontFamilyFallback: const ['Microsoft YaHei UI'],
    scaffoldBackgroundColor: ConsoleColors.canvas,
    colorScheme: const ColorScheme.dark(
      primary: ConsoleColors.accent,
      onPrimary: ConsoleColors.canvas,
      surface: ConsoleColors.panel,
      onSurface: ConsoleColors.ink,
      onSurfaceVariant: ConsoleColors.muted,
      outline: ConsoleColors.line,
      error: ConsoleColors.danger,
    ),
  );
  return base.copyWith(
    textTheme: base.textTheme.apply(
      bodyColor: ConsoleColors.ink,
      displayColor: ConsoleColors.ink,
    ),
    dividerTheme: const DividerThemeData(
      color: ConsoleColors.line,
      thickness: 1,
    ),
    iconTheme: const IconThemeData(size: 20, color: ConsoleColors.muted),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        minimumSize: const Size(44, 44),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        textStyle: const TextStyle(
          fontFamily: 'Segoe UI',
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: ConsoleColors.ink,
        minimumSize: const Size(44, 44),
        side: const BorderSide(color: ConsoleColors.line),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(minimumSize: const Size(44, 44)),
    ),
    iconButtonTheme: IconButtonThemeData(
      style: IconButton.styleFrom(minimumSize: const Size(44, 44)),
    ),
    inputDecorationTheme: InputDecorationTheme(
      hintStyle: const TextStyle(color: ConsoleColors.dim),
      filled: true,
      fillColor: ConsoleColors.canvas,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: ConsoleColors.line),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: ConsoleColors.accent, width: 2),
      ),
    ),
    snackBarTheme: const SnackBarThemeData(
      backgroundColor: ConsoleColors.raised,
      contentTextStyle: TextStyle(color: ConsoleColors.ink),
      behavior: SnackBarBehavior.floating,
    ),
    tooltipTheme: const TooltipThemeData(
      waitDuration: Duration(milliseconds: 350),
    ),
  );
}

class ConsolePanel extends StatelessWidget {
  const ConsolePanel({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.solid = true,
  });
  final Widget child;
  final EdgeInsetsGeometry padding;
  final bool solid;
  @override
  Widget build(BuildContext context) => Container(
    padding: padding,
    decoration: BoxDecoration(
      color: solid ? ConsoleColors.panel : null,
      gradient: solid
          ? null
          : LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                ConsoleColors.raised.withValues(alpha: .7),
                ConsoleColors.panel.withValues(alpha: .9),
              ],
            ),
      border: Border.all(color: ConsoleColors.line.withValues(alpha: .7)),
      borderRadius: BorderRadius.circular(12),
    ),
    child: child,
  );
}

class StatusLabel extends StatelessWidget {
  const StatusLabel(this.label, {super.key, this.color = ConsoleColors.accent});
  final String label;
  final Color color;
  @override
  Widget build(BuildContext context) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: 6,
        height: 6,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
      ),
      const SizedBox(width: 7),
      Flexible(
        child: Text(
          label,
          maxLines: 2,
          style: TextStyle(
            color: color,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    ],
  );
}
