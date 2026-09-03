import 'package:flutter/material.dart';
import 'console_theme.dart';
import 'core_indicator.dart';
import 'jarvis_api.dart';
import 'runtime_monitor.dart';
import 'runtime_panel.dart';

class SessionRun {
  SessionRun(this.prompt) : started = DateTime.now();
  final String prompt;
  final DateTime started;
  DateTime? finished;
  JarvisChatReply? reply;
  String? error;
  bool get working => finished == null;
  static bool resultFailed(Map<String, dynamic> result) =>
      result['success'] == false ||
      (result['error'] != null && result['error'].toString().isNotEmpty);
  bool get toolFailure => reply?.toolResults.any(resultFailed) ?? false;
  String get status => working
      ? 'Working'
      : error != null
      ? 'Failed'
      : toolFailure
      ? 'Review result'
      : 'Replied';
  Color get color => error != null
      ? ConsoleColors.danger
      : toolFailure
      ? ConsoleColors.warning
      : working
      ? ConsoleColors.accent
      : ConsoleColors.good;
}

class WelcomePanel extends StatelessWidget {
  const WelcomePanel({
    super.key,
    required this.monitor,
    required this.solid,
    required this.onPrompt,
  });
  final RuntimeMonitor monitor;
  final bool solid;
  final ValueChanged<String> onPrompt;
  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) => SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(28, 28, 28, 20),
      child: ConstrainedBox(
        constraints: BoxConstraints(
          minHeight: (constraints.maxHeight - 48).clamp(0, double.infinity),
        ),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 720),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                LayoutBuilder(
                  builder: (context, size) {
                    final core = ListenableBuilder(
                      listenable: monitor,
                      builder: (context, _) => CoreIndicator(
                        size: size.maxWidth < 520 ? 114 : 166,
                        online: monitor.online,
                      ),
                    );
                    final title = Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'At your command.',
                          style: TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.w500,
                            letterSpacing: -1.1,
                            height: 1.2,
                          ),
                        ),
                        const SizedBox(height: 14),
                        const Text(
                          'One place to think, build and get things done\non your machine.',
                          style: TextStyle(
                            color: ConsoleColors.muted,
                            fontSize: 14,
                            height: 1.7,
                          ),
                        ),
                        const SizedBox(height: 18),
                        ListenableBuilder(
                          listenable: monitor,
                          builder: (context, _) => StatusLabel(
                            monitor.online
                                ? 'Connected to local JARVIS Core'
                                : 'Waiting for local JARVIS Core',
                            color: monitor.online
                                ? ConsoleColors.good
                                : ConsoleColors.warning,
                          ),
                        ),
                      ],
                    );
                    return size.maxWidth < 520
                        ? Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [core, const SizedBox(height: 24), title],
                          )
                        : Row(
                            children: [
                              core,
                              const SizedBox(width: 30),
                              Expanded(child: title),
                            ],
                          );
                  },
                ),
                const SizedBox(height: 40),
                const Text(
                  'Start with a request',
                  style: TextStyle(fontSize: 12, color: ConsoleColors.muted),
                ),
                const SizedBox(height: 14),
                LayoutBuilder(
                  builder: (context, size) {
                    final width = size.maxWidth < 520
                        ? size.maxWidth
                        : (size.maxWidth - 12) / 2;
                    return Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: [
                        _QuickAction(
                          width: width,
                          icon: Icons.memory_outlined,
                          title: 'Check my system',
                          description: 'CPU and memory usage',
                          solid: solid,
                          onTap: () =>
                              onPrompt('Show my current CPU and memory usage.'),
                        ),
                        _QuickAction(
                          width: width,
                          icon: Icons.folder_open_outlined,
                          title: 'Find a project',
                          description: 'Browse registered workspaces',
                          solid: solid,
                          onTap: () => onPrompt('List my registered projects.'),
                        ),
                        _QuickAction(
                          width: width,
                          icon: Icons.difference_outlined,
                          title: 'Inspect Git status',
                          description: 'Review a project before working',
                          solid: solid,
                          onTap: () => onPrompt('Show Git status for project '),
                        ),
                        _QuickAction(
                          width: width,
                          icon: Icons.manage_search_outlined,
                          title: 'Explore project files',
                          description: 'Read and search safely',
                          solid: solid,
                          onTap: () => onPrompt('List the files in project '),
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 24),
                const Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.shield_outlined,
                      size: 16,
                      color: ConsoleColors.dim,
                    ),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Existing tools. Your routing policy. Confirmation for sensitive actions.',
                        style: TextStyle(
                          color: ConsoleColors.dim,
                          fontSize: 11,
                          height: 1.6,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({
    required this.width,
    required this.icon,
    required this.title,
    required this.description,
    required this.solid,
    required this.onTap,
  });
  final double width;
  final IconData icon;
  final String title;
  final String description;
  final bool solid;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => SizedBox(
    width: width,
    child: ConsolePanel(
      solid: solid,
      padding: EdgeInsets.zero,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(17),
            child: Row(
              children: [
                Icon(icon, size: 21, color: ConsoleColors.accent),
                const SizedBox(width: 13),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontWeight: FontWeight.w500,
                          fontSize: 13,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        description,
                        style: const TextStyle(
                          fontSize: 11,
                          color: ConsoleColors.muted,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 6),
                const Icon(Icons.north_east, size: 14),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

class TasksPage extends StatelessWidget {
  const TasksPage({
    super.key,
    required this.runs,
    required this.onOpenAssistant,
    required this.onOpenErrors,
  });
  final List<SessionRun> runs;
  final VoidCallback onOpenAssistant;
  final VoidCallback onOpenErrors;
  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(28),
    children: [
      const _PageHeading(
        'A clear trail of work.',
        'Requests from this desktop session. Full Core task history is not connected yet.',
      ),
      const SizedBox(height: 28),
      if (runs.isEmpty)
        ConsolePanel(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 28),
            child: Column(
              children: [
                const Icon(
                  Icons.account_tree_outlined,
                  size: 36,
                  color: ConsoleColors.accent,
                ),
                const SizedBox(height: 18),
                const Text(
                  'No requests in this session',
                  style: TextStyle(fontSize: 18),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Start in Assistant. Your requests and responses will appear here.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: ConsoleColors.muted, height: 1.6),
                ),
                const SizedBox(height: 20),
                OutlinedButton(
                  onPressed: onOpenAssistant,
                  child: const Text('Open Assistant'),
                ),
              ],
            ),
          ),
        )
      else ...[
        Text('${runs.length} session requests', style: metadataStyle),
        const SizedBox(height: 16),
        for (final run in runs.reversed)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: ConsolePanel(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      StatusLabel(run.status, color: run.color),
                      const Spacer(),
                      Text(clockLabel(run.started), style: metadataStyle),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SelectableText(
                    run.prompt,
                    style: const TextStyle(fontSize: 14, height: 1.6),
                  ),
                  if (run.error != null || run.toolFailure)
                    TextButton.icon(
                      onPressed: onOpenErrors,
                      icon: const Icon(Icons.info_outline, size: 16),
                      label: const Text('View errors'),
                    ),
                  const SizedBox(height: 10),
                  TextButton.icon(
                    onPressed: onOpenAssistant,
                    icon: const Icon(Icons.arrow_outward, size: 16),
                    label: const Text('View conversation'),
                  ),
                ],
              ),
            ),
          ),
      ],
    ],
  );
}

class DevicePage extends StatelessWidget {
  const DevicePage({
    super.key,
    required this.monitor,
    required this.solid,
    required this.reduceMotion,
    required this.busy,
  });
  final RuntimeMonitor monitor;
  final bool solid;
  final bool reduceMotion;
  final bool busy;
  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(28),
    children: [
      const _PageHeading(
        'Your machine, in view.',
        'Live system readings and desktop capabilities.',
      ),
      const SizedBox(height: 24),
      LayoutBuilder(
        builder: (context, size) {
          final telemetry = ConsolePanel(
            solid: solid,
            child: RuntimePanel(monitor: monitor, expanded: true),
          );
          final companion = Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ConsolePanel(
                key: const ValueKey('device-connection-panel'),
                solid: solid,
                child: Column(
                  children: [
                    ListenableBuilder(
                      listenable: monitor,
                      builder: (context, _) => CoreIndicator(
                        size: 120,
                        online: monitor.online,
                        busy: busy,
                        reduceMotion: reduceMotion,
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Desktop connection',
                      style: TextStyle(fontSize: 18),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'The instrument follows API connection and request activity.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: ConsoleColors.muted,
                        height: 1.6,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              ConsolePanel(
                key: const ValueKey('device-capabilities-panel'),
                solid: solid,
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Desktop capabilities',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    SizedBox(height: 14),
                    _PlannedFeature(
                      Icons.mic_none,
                      'Voice input',
                      'No microphone is recording.',
                    ),
                    _PlannedFeature(
                      Icons.hearing_outlined,
                      'Wake word',
                      'Activation is not connected yet.',
                    ),
                    _PlannedFeature(
                      Icons.blur_circular,
                      'Desktop companion',
                      'Floating companion is planned.',
                    ),
                  ],
                ),
              ),
            ],
          );
          return size.maxWidth < 980
              ? Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [telemetry, const SizedBox(height: 20), companion],
                )
              : Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: telemetry),
                    const SizedBox(width: 20),
                    SizedBox(width: 320, child: companion),
                  ],
                );
        },
      ),
    ],
  );
}

class _PlannedFeature extends StatelessWidget {
  const _PlannedFeature(this.icon, this.title, this.description);
  final IconData icon;
  final String title;
  final String description;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 14),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 10,
                runSpacing: 6,
                children: [
                  Text(title, style: const TextStyle(fontSize: 13)),
                  const Text(
                    'Planned',
                    style: TextStyle(color: ConsoleColors.dim, fontSize: 11),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                description,
                style: const TextStyle(
                  color: ConsoleColors.muted,
                  fontSize: 11,
                  height: 1.6,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class SettingsPage extends StatelessWidget {
  const SettingsPage({
    super.key,
    required this.monitor,
    required this.solid,
    required this.reduceMotion,
    required this.onReduceMotion,
    required this.onReduceTransparency,
    required this.onPermissionPreview,
  });
  final RuntimeMonitor monitor;
  final bool solid;
  final bool reduceMotion;
  final ValueChanged<bool> onReduceMotion;
  final ValueChanged<bool> onReduceTransparency;
  final VoidCallback onPermissionPreview;
  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(28),
    children: [
      const _PageHeading(
        'Make room for your focus.',
        'Appearance and monitoring preferences apply to this session.',
      ),
      const SizedBox(height: 28),
      ConsolePanel(
        solid: solid,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Padding(
              padding: EdgeInsets.all(10),
              child: Text(
                'Appearance',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),
            ),
            SwitchListTile(
              title: const Text(
                'Reduce motion',
                style: TextStyle(fontSize: 14),
              ),
              subtitle: const Text(
                'Keep activity indicators still.',
                style: TextStyle(fontSize: 12),
              ),
              value: reduceMotion,
              onChanged: onReduceMotion,
            ),
            SwitchListTile(
              title: const Text(
                'Reduce transparency',
                style: TextStyle(fontSize: 14),
              ),
              subtitle: const Text(
                'Use solid panel surfaces.',
                style: TextStyle(fontSize: 12),
              ),
              value: solid,
              onChanged: onReduceTransparency,
            ),
          ],
        ),
      ),
      const SizedBox(height: 18),
      ConsolePanel(
        solid: solid,
        child: ListenableBuilder(
          listenable: monitor,
          builder: (context, _) => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Live monitoring',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 16),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text(
                  'Auto-refresh system metrics',
                  style: TextStyle(fontSize: 14),
                ),
                subtitle: const Text(
                  'Pauses while the app is minimized.',
                  style: TextStyle(fontSize: 12),
                ),
                value: monitor.enabled,
                onChanged: monitor.setEnabled,
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<int>(
                key: ValueKey(monitor.intervalSeconds),
                initialValue: monitor.intervalSeconds,
                decoration: const InputDecoration(
                  labelText: 'Refresh interval',
                ),
                items: [
                  for (final seconds in [2, 5, 10])
                    DropdownMenuItem(
                      value: seconds,
                      child: Text(
                        'Every $seconds seconds',
                        style: const TextStyle(fontSize: 13),
                      ),
                    ),
                ],
                onChanged: (seconds) {
                  if (seconds != null) monitor.setInterval(seconds);
                },
              ),
              const SizedBox(height: 14),
              const Text(
                'Read-only samples. No reasoning calls or task-history entries. The chart keeps at most 60 samples in memory.',
                style: TextStyle(
                  fontSize: 12,
                  color: ConsoleColors.muted,
                  height: 1.6,
                ),
              ),
            ],
          ),
        ),
      ),
      const SizedBox(height: 18),
      ConsolePanel(
        solid: solid,
        child: ListenableBuilder(
          listenable: monitor,
          builder: (context, _) => Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Core configuration',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 16),
              RuntimeRow('Brain', monitor.health?.brain ?? 'Not available'),
              RuntimeRow(
                'Routing',
                monitor.health?.routingMode ?? 'Not available',
              ),
              const SizedBox(height: 12),
              const Text(
                'Read from Core. Changing the brain or routing in this UI is not connected yet.',
                style: TextStyle(
                  color: ConsoleColors.muted,
                  fontSize: 12,
                  height: 1.6,
                ),
              ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: onPermissionPreview,
                icon: const Icon(Icons.verified_user_outlined, size: 17),
                label: const Text('Permission preview'),
              ),
            ],
          ),
        ),
      ),
    ],
  );
}

class _PageHeading extends StatelessWidget {
  const _PageHeading(this.title, this.description);
  final String title;
  final String description;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        title,
        style: const TextStyle(
          fontSize: 28,
          height: 1.25,
          letterSpacing: -.8,
          fontWeight: FontWeight.w500,
        ),
      ),
      const SizedBox(height: 12),
      Text(
        description,
        style: const TextStyle(
          color: ConsoleColors.muted,
          height: 1.6,
          fontSize: 13,
        ),
      ),
    ],
  );
}

class SafetyNote extends StatelessWidget {
  const SafetyNote({super.key});
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Row(
        children: [
          Icon(Icons.shield_outlined, color: ConsoleColors.accent, size: 17),
          SizedBox(width: 8),
          Text(
            'Policy protected',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
          ),
        ],
      ),
      const SizedBox(height: 12),
      const Text(
        'Native tools first. Sensitive actions still require confirmation through Core.',
        style: TextStyle(color: ConsoleColors.muted, fontSize: 12, height: 1.7),
      ),
      const SizedBox(height: 16),
      Text(
        'LOCAL EXECUTION',
        style: metadataStyle.copyWith(fontSize: 10, letterSpacing: 1.3),
      ),
    ],
  );
}
