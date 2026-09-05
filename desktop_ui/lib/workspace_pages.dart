import 'package:flutter/material.dart';
import 'console_theme.dart';
import 'core_indicator.dart';
import 'jarvis_api.dart';
import 'runtime_monitor.dart';
import 'runtime_panel.dart';
import 'speech_controller.dart';
import 'coding_memory_panel.dart';

class SessionRun {
  SessionRun(this.prompt) : started = DateTime.now(), restored = false;
  SessionRun.restored({
    required this.prompt,
    required this.started,
    required JarvisChatReply restoredReply,
  }) : restored = true,
       finished = started,
       reply = restoredReply;
  final String prompt;
  final DateTime started;
  final bool restored;
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
      : restored
      ? 'Archived'
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
                          'J.A.R.V.I.S // LOCAL CONSOLE',
                          style: TextStyle(
                            color: ConsoleColors.accent,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 1.6,
                          ),
                        ),
                        const SizedBox(height: 10),
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
                          'Your local workspace for thinking, building and\ngetting things done on this machine.',
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
                  'Choose a safe starting point',
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
    required this.api,
    required this.monitor,
    required this.runs,
    required this.archivedRuns,
    required this.onOpenAssistant,
    required this.onOpenErrors,
  });
  final JarvisApi api;
  final RuntimeMonitor monitor;
  final List<SessionRun> runs;
  final List<SessionRun> archivedRuns;
  final VoidCallback onOpenAssistant;
  final VoidCallback onOpenErrors;
  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: monitor,
    builder: (context, _) => ListView(
      padding: const EdgeInsets.all(28),
      children: [
        const _PageHeading(
          'Background work.',
          'Run declared local jobs without blocking Assistant. Results are persisted and verified.',
        ),
        const SizedBox(height: 20),
        ExpansionTile(
          tilePadding: EdgeInsets.zero,
          title: const Text('Coding & memory'),
          subtitle: const Text(
            'Delegate coding tasks and review long-term memory.',
          ),
          children: [CodingMemoryPanel(api: api)],
        ),
        const SizedBox(height: 20),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            FilledButton.icon(
              onPressed: monitor.online
                  ? () async {
                      await api.createBackgroundTask('project_scan');
                      await monitor.refresh();
                    }
                  : null,
              icon: const Icon(Icons.folder_open_outlined, size: 18),
              label: const Text('Scan projects'),
            ),
            OutlinedButton.icon(
              onPressed: monitor.online
                  ? () async {
                      await api.createBackgroundTask('knowledge_reindex');
                      await monitor.refresh();
                    }
                  : null,
              icon: const Icon(Icons.auto_awesome_motion_outlined, size: 18),
              label: const Text('Reindex knowledge'),
            ),
          ],
        ),
        const SizedBox(height: 20),
        if (monitor.backgroundTasks.isEmpty)
          const ConsolePanel(
            child: Text(
              'No background tasks yet.',
              style: TextStyle(color: ConsoleColors.muted),
            ),
          )
        else
          for (final task in monitor.backgroundTasks)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ConsolePanel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            task.title,
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        StatusLabel(task.status.replaceAll('_', ' ')),
                      ],
                    ),
                    const SizedBox(height: 12),
                    LinearProgressIndicator(value: task.progress / 100),
                    const SizedBox(height: 10),
                    Text(task.progressMessage, style: metadataStyle),
                    if (task.verification.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Verified: ${task.verification}',
                        style: const TextStyle(
                          color: ConsoleColors.good,
                          fontSize: 12,
                        ),
                      ),
                    ],
                    if (task.notification.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(task.notification, style: metadataStyle),
                    ],
                    if (task.error.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                        task.error,
                        style: const TextStyle(
                          color: ConsoleColors.danger,
                          fontSize: 12,
                        ),
                      ),
                    ],
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Text('Attempt ${task.attempt}', style: metadataStyle),
                        const Spacer(),
                        if (task.active)
                          TextButton.icon(
                            onPressed: () async {
                              await api.cancelBackgroundTask(task.id);
                              await monitor.refresh();
                            },
                            icon: const Icon(
                              Icons.stop_circle_outlined,
                              size: 17,
                            ),
                            label: const Text('Cancel'),
                          )
                        else if (task.status != 'completed')
                          TextButton.icon(
                            onPressed: () async {
                              await api.retryBackgroundTask(task.id);
                              await monitor.refresh();
                            },
                            icon: const Icon(Icons.refresh, size: 17),
                            label: const Text('Retry'),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
        const SizedBox(height: 32),
        const _PageHeading(
          'Conversation archive.',
          'Current requests and earlier Assistant conversations, kept locally on this device.',
        ),
        const SizedBox(height: 28),
        if (runs.isEmpty && archivedRuns.isEmpty)
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
                    'No saved conversations yet',
                    style: TextStyle(fontSize: 18),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Start in Assistant. Current requests appear here, and completed sessions remain available after restart.',
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
          ),
        if (runs.isNotEmpty) ...[
          Text('Current session · ${runs.length}', style: metadataStyle),
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
        if (runs.isNotEmpty && archivedRuns.isNotEmpty)
          const SizedBox(height: 24),
        if (archivedRuns.isNotEmpty) ...[
          Text(
            'Previous sessions · ${archivedRuns.length}',
            style: metadataStyle,
          ),
          const SizedBox(height: 16),
          for (final run in archivedRuns.reversed)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ConsolePanel(
                child: Material(
                  type: MaterialType.transparency,
                  child: ExpansionTile(
                    tilePadding: EdgeInsets.zero,
                    childrenPadding: const EdgeInsets.only(top: 4, bottom: 8),
                    title: Text(
                      run.prompt,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 14, height: 1.5),
                    ),
                    subtitle: Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Row(
                        children: [
                          StatusLabel(run.status, color: run.color),
                          const SizedBox(width: 12),
                          Text(clockLabel(run.started), style: metadataStyle),
                        ],
                      ),
                    ),
                    children: [
                      Align(
                        alignment: Alignment.centerLeft,
                        child: SelectableText(
                          run.reply?.reply ?? 'No reply was saved.',
                          style: const TextStyle(
                            color: ConsoleColors.muted,
                            fontSize: 13,
                            height: 1.7,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ],
    ),
  );
}

class DevicePage extends StatelessWidget {
  const DevicePage({
    super.key,
    required this.monitor,
    required this.solid,
    required this.reduceMotion,
    required this.busy,
    required this.speech,
    required this.speechProvider,
  });
  final RuntimeMonitor monitor;
  final bool solid;
  final bool reduceMotion;
  final bool busy;
  final SpeechController speech;
  final SpeechProvider speechProvider;
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
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Desktop capabilities',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 14),
                    ListenableBuilder(
                      listenable: speech,
                      builder: (context, _) => _PlannedFeature(
                        speech.speaking
                            ? Icons.volume_up_outlined
                            : Icons.record_voice_over_outlined,
                        'Voice output',
                        speech.speaking
                            ? 'Reading the latest response through ${speechProvider.label}.'
                            : speech.error ?? speechProvider.description,
                        state: speech.speaking
                            ? 'Speaking'
                            : speechProvider == SpeechProvider.system
                            ? 'Local'
                            : 'Cloud',
                        color: speech.speaking
                            ? ConsoleColors.good
                            : ConsoleColors.accent,
                      ),
                    ),
                    const _PlannedFeature(
                      Icons.mic_none,
                      'Voice input',
                      'No microphone is recording or routed to Core.',
                    ),
                    const _PlannedFeature(
                      Icons.hearing_outlined,
                      'Wake word',
                      'Activation is not connected yet.',
                    ),
                    const _PlannedFeature(
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
  const _PlannedFeature(
    this.icon,
    this.title,
    this.description, {
    this.state = 'Planned',
    this.color = ConsoleColors.dim,
  });
  final IconData icon;
  final String title;
  final String description;
  final String state;
  final Color color;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 14),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20, color: color),
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
                  Text(state, style: TextStyle(color: color, fontSize: 11)),
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
    required this.api,
    required this.monitor,
    required this.solid,
    required this.reduceMotion,
    required this.onReduceMotion,
    required this.onReduceTransparency,
    required this.onPermissionPreview,
    required this.speechProvider,
    required this.onSpeechProvider,
    required this.autoReadReplies,
    required this.onAutoReadReplies,
  });
  final JarvisApi api;
  final RuntimeMonitor monitor;
  final bool solid;
  final bool reduceMotion;
  final ValueChanged<bool> onReduceMotion;
  final ValueChanged<bool> onReduceTransparency;
  final VoidCallback onPermissionPreview;
  final SpeechProvider speechProvider;
  final ValueChanged<SpeechProvider> onSpeechProvider;
  final bool autoReadReplies;
  final ValueChanged<bool> onAutoReadReplies;
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
      ObsidianVaultPanel(api: api, solid: solid),
      const SizedBox(height: 18),
      ConsolePanel(
        solid: solid,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Voice output',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<SpeechProvider>(
              key: const ValueKey('speech-provider'),
              initialValue: speechProvider,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Read reply provider',
              ),
              items: [
                for (final provider in SpeechProvider.values)
                  DropdownMenuItem(
                    value: provider,
                    child: Text(provider.label),
                  ),
              ],
              onChanged: (provider) {
                if (provider != null) onSpeechProvider(provider);
              },
            ),
            const SizedBox(height: 14),
            Text(
              speechProvider.description,
              style: const TextStyle(
                fontSize: 12,
                color: ConsoleColors.muted,
                height: 1.6,
              ),
            ),
            if (speechProvider == SpeechProvider.system) ...[
              const SizedBox(height: 14),
              const Divider(),
              const SizedBox(height: 12),
              ListenableBuilder(
                listenable: monitor,
                builder: (context, _) {
                  final settings = monitor.speechSettings;
                  final available = settings != null;
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        available ? Icons.sync : Icons.sync_problem_outlined,
                        size: 18,
                        color: available
                            ? ConsoleColors.good
                            : ConsoleColors.warning,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              available
                                  ? '${settings.voice} · Speed ${settings.speed}'
                                  : 'Waiting for Windows Speech settings',
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              available
                                  ? 'Auto-sync from Windows · Every ${monitor.intervalSeconds}s'
                                  : monitor.speechSettingsError ??
                                        'JARVIS will retry automatically.',
                              style: const TextStyle(
                                fontSize: 12,
                                color: ConsoleColors.muted,
                              ),
                            ),
                          ],
                        ),
                      ),
                      StatusLabel(
                        available ? 'Synced' : 'Unavailable',
                        color: available
                            ? ConsoleColors.good
                            : ConsoleColors.warning,
                      ),
                    ],
                  );
                },
              ),
            ],
            if (speechProvider == SpeechProvider.fish) ...[
              const SizedBox(height: 10),
              const Text(
                'Fish Audio needs FISH_API_KEY in the local .env file. The key is never entered into or stored by this UI.',
                style: TextStyle(
                  fontSize: 12,
                  color: ConsoleColors.warning,
                  height: 1.6,
                ),
              ),
            ],
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text(
                'Auto read completed replies',
                style: TextStyle(fontSize: 14),
              ),
              subtitle: Text(
                autoReadReplies
                    ? 'Reply text remains visible while its selected voice starts.'
                    : 'Use Read reply beside an answer to start voice output.',
                style: const TextStyle(fontSize: 12),
              ),
              value: autoReadReplies,
              onChanged: onAutoReadReplies,
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
              const SizedBox(height: 12),
              const Text(
                'Read from Core. Changing the brain in this UI is not connected yet.',
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

class ObsidianVaultPanel extends StatefulWidget {
  const ObsidianVaultPanel({super.key, required this.api, required this.solid});
  final JarvisApi api;
  final bool solid;
  @override
  State<ObsidianVaultPanel> createState() => _ObsidianVaultPanelState();
}

class _ObsidianVaultPanelState extends State<ObsidianVaultPanel> {
  final _name = TextEditingController();
  final _path = TextEditingController();
  List<ObsidianVault> _vaults = const [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _name.dispose();
    _path.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final vaults = await widget.api.obsidianVaults();
      if (mounted) setState(() => _vaults = vaults);
    } on JarvisApiException catch (failure) {
      if (mounted) setState(() => _error = failure.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _idFor(String value) {
    final normalized = value
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9_-]+'), '-')
        .replaceAll(RegExp(r'^-+|-+$'), '');
    return normalized.isEmpty ? 'obsidian-vault' : normalized;
  }

  Future<void> _add() async {
    if (_name.text.trim().isEmpty || _path.text.trim().isEmpty) {
      setState(
        () => _error = 'Enter a vault name and its full Windows folder path.',
      );
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await widget.api.registerObsidianVault(
        id: _idFor(_name.text),
        name: _name.text.trim(),
        path: _path.text.trim(),
      );
      _name.clear();
      _path.clear();
      await _load();
    } on JarvisApiException catch (failure) {
      if (mounted) {
        setState(() {
          _error = failure.message;
          _loading = false;
        });
      }
    }
  }

  Future<void> _remove(ObsidianVault vault) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Disconnect Obsidian vault?'),
        content: Text(
          '${vault.name} will be removed from JARVIS indexing. Your Obsidian files will not be deleted.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Disconnect'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await widget.api.removeObsidianVault(vault.id);
      await _load();
    } on JarvisApiException catch (failure) {
      if (mounted) setState(() => _error = failure.message);
    }
  }

  @override
  Widget build(BuildContext context) => ConsolePanel(
    solid: widget.solid,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Icon(
              Icons.auto_stories_outlined,
              size: 18,
              color: ConsoleColors.accent,
            ),
            SizedBox(width: 10),
            Expanded(
              child: Text(
                'Obsidian knowledge',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        const Text(
          'Only notes marked jarvis_access: rag are sent to Gemini. Vault paths stay inside JARVIS Core.',
          style: TextStyle(
            color: ConsoleColors.muted,
            fontSize: 12,
            height: 1.6,
          ),
        ),
        if (_loading)
          const Padding(
            padding: EdgeInsets.only(top: 14),
            child: LinearProgressIndicator(),
          ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 14),
            child: Text(
              _error!,
              style: const TextStyle(
                color: ConsoleColors.warning,
                fontSize: 12,
              ),
            ),
          ),
        for (final vault in _vaults)
          Padding(
            padding: const EdgeInsets.only(top: 14),
            child: Row(
              children: [
                const Icon(Icons.folder_outlined, size: 18),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        vault.name,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      Text(
                        '${vault.indexedChunks} indexed chunks · default ${vault.defaultAccess}',
                        style: const TextStyle(
                          color: ConsoleColors.muted,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                StatusLabel('Connected', color: ConsoleColors.good),
                IconButton(
                  tooltip: 'Disconnect vault',
                  onPressed: _loading ? null : () => _remove(vault),
                  icon: const Icon(Icons.link_off, size: 18),
                ),
              ],
            ),
          ),
        const SizedBox(height: 16),
        TextField(
          controller: _name,
          decoration: const InputDecoration(labelText: 'Vault name'),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _path,
          decoration: const InputDecoration(
            labelText: 'Full Windows vault path',
            hintText: r'C:\...\My Vault',
          ),
        ),
        const SizedBox(height: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            FilledButton.icon(
              onPressed: _loading ? null : _add,
              icon: const Icon(Icons.add_link, size: 17),
              label: const Text('Connect and index'),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: _loading
                  ? null
                  : () async {
                      try {
                        await widget.api.reindexObsidian();
                        await _load();
                      } on JarvisApiException catch (failure) {
                        if (mounted) setState(() => _error = failure.message);
                      }
                    },
              icon: const Icon(Icons.sync, size: 17),
              label: const Text('Reindex'),
            ),
          ],
        ),
      ],
    ),
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
