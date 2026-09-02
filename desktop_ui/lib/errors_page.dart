import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'console_theme.dart';
import 'error_log.dart';
import 'runtime_panel.dart';

/// Deliberately small and independent of inherited themes in a broken subtree.
class InterfaceErrorFallback extends StatelessWidget {
  const InterfaceErrorFallback({super.key});

  @override
  Widget build(BuildContext context) => const Directionality(
    textDirection: TextDirection.ltr,
    child: ColoredBox(
      color: ConsoleColors.panel,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Text(
          'This panel could not be displayed. See Errors for details.',
          maxLines: 3,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: ConsoleColors.muted,
            fontFamily: 'Segoe UI',
            fontSize: 13,
            fontWeight: FontWeight.normal,
            decoration: TextDecoration.none,
          ),
        ),
      ),
    ),
  );
}

class ErrorNotice extends StatelessWidget {
  const ErrorNotice({
    super.key,
    required this.message,
    required this.onOpenErrors,
  });
  final String message;
  final VoidCallback onOpenErrors;

  @override
  Widget build(BuildContext context) => ConsolePanel(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
    child: Row(
      children: [
        const Icon(Icons.info_outline, size: 18, color: ConsoleColors.warning),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            message,
            style: const TextStyle(
              fontSize: 12,
              color: ConsoleColors.muted,
              height: 1.5,
            ),
          ),
        ),
        const SizedBox(width: 8),
        TextButton(onPressed: onOpenErrors, child: const Text('View errors')),
      ],
    ),
  );
}

class ErrorsPage extends StatelessWidget {
  const ErrorsPage({super.key, required this.log});
  final AppErrorLog log;

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: log,
    builder: (context, _) {
      final entries = log.entries;
      return ListView(
        key: const PageStorageKey('errors-page'),
        padding: const EdgeInsets.all(28),
        children: [
          const Text(
            'Error log',
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w500,
              letterSpacing: -.6,
            ),
          ),
          const SizedBox(height: 10),
          const Text(
            'Details stay here, so you can keep your conversation in view.',
            style: TextStyle(color: ConsoleColors.muted, height: 1.6),
          ),
          const SizedBox(height: 22),
          Wrap(
            alignment: WrapAlignment.spaceBetween,
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 20,
            runSpacing: 8,
            children: [
              Text(
                '${entries.length} recorded • This session',
                style: metadataStyle,
              ),
              OutlinedButton.icon(
                onPressed: entries.isEmpty ? null : () => _clear(context),
                icon: const Icon(Icons.delete_outline, size: 18),
                label: const Text('Clear log'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            'UI, request, tool and connection errors • Latest 50 unique reports • Not saved or uploaded',
            style: TextStyle(
              fontSize: 12,
              color: ConsoleColors.dim,
              height: 1.6,
            ),
          ),
          const SizedBox(height: 24),
          if (entries.isEmpty)
            const ConsolePanel(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 28),
                child: Column(
                  children: [
                    Icon(
                      Icons.check_circle_outline,
                      size: 32,
                      color: ConsoleColors.good,
                    ),
                    SizedBox(height: 16),
                    Text('No errors recorded', style: TextStyle(fontSize: 18)),
                    SizedBox(height: 8),
                    Text(
                      'New errors will appear here. Nothing needs your attention.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: ConsoleColors.muted, height: 1.6),
                    ),
                  ],
                ),
              ),
            ),
          for (final entry in entries)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ConsolePanel(
                padding: EdgeInsets.zero,
                child: ExpansionTile(
                  key: PageStorageKey('error-${entry.id}'),
                  shape: const Border(),
                  collapsedShape: const Border(),
                  tilePadding: const EdgeInsets.symmetric(
                    horizontal: 18,
                    vertical: 6,
                  ),
                  title: Text(
                    entry.message,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 14, height: 1.5),
                  ),
                  subtitle: Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Wrap(
                      spacing: 16,
                      runSpacing: 6,
                      children: [
                        Text(
                          entry.source,
                          style: const TextStyle(
                            color: ConsoleColors.warning,
                            fontSize: 12,
                          ),
                        ),
                        Text(clockLabel(entry.lastSeen), style: metadataStyle),
                        if (entry.occurrences > 1)
                          Text(
                            '${entry.occurrences} occurrences',
                            style: metadataStyle,
                          ),
                      ],
                    ),
                  ),
                  childrenPadding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
                  expandedCrossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Divider(),
                    const SizedBox(height: 12),
                    Text(
                      'First seen ${entry.firstSeen.toLocal()}',
                      style: metadataStyle,
                    ),
                    const SizedBox(height: 14),
                    ConstrainedBox(
                      constraints: const BoxConstraints(maxHeight: 320),
                      child: SingleChildScrollView(
                        key: PageStorageKey('error-details-${entry.id}'),
                        child: SelectableText(
                          '${entry.details}'
                          '${entry.stack.isEmpty ? '' : '\n\nStack trace\n${entry.stack}'}',
                          style: metadataStyle.copyWith(height: 1.7),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextButton.icon(
                      onPressed: () => _copy(context, entry),
                      icon: const Icon(Icons.copy_outlined, size: 16),
                      label: const Text('Copy details'),
                    ),
                  ],
                ),
              ),
            ),
        ],
      );
    },
  );

  Future<void> _copy(BuildContext context, AppErrorEntry entry) async {
    try {
      await Clipboard.setData(ClipboardData(text: entry.report));
      if (!context.mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Error details copied.')));
    } catch (_) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Clipboard unavailable. Select the details to copy manually.',
          ),
        ),
      );
    }
  }

  Future<void> _clear(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear this session’s error log?'),
        content: const Text(
          'These reports cannot be restored. This does not fix the errors or delete conversations.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Keep log'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Clear log'),
          ),
        ],
      ),
    );
    if (context.mounted && confirmed == true) log.clear();
  }
}
