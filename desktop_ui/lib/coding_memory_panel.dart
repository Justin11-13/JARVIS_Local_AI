// Operate: extend the existing console with evidence, explicit approvals and review.
// Preserve ConsoleColors, native controls and keyboard access; no new visual world.
import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'console_theme.dart';
import 'jarvis_api.dart';

class CodingMemoryPanel extends StatefulWidget {
  const CodingMemoryPanel({super.key, required this.api});
  final JarvisApi api;
  @override
  State<CodingMemoryPanel> createState() => _CodingMemoryPanelState();
}

class _CodingMemoryPanelState extends State<CodingMemoryPanel> {
  final prompt = TextEditingController();
  Timer? timer;
  StreamSubscription<Map<String, dynamic>>? stream;
  List<dynamic> tasks = [], memories = [], projects = [];
  List<Map<String, dynamic>> events = [];
  String? project, selected, error;
  String extraction = 'idle';
  bool busy = false, refreshing = false, connected = false;
  int cursor = 0, streamVersion = 0;
  static const terminal = {'completed', 'failed', 'cancelled', 'timed_out'};

  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(const Duration(seconds: 5), (_) => refresh());
  }

  @override
  void dispose() {
    timer?.cancel();
    stream?.cancel();
    prompt.dispose();
    super.dispose();
  }

  Future<void> refresh() async {
    if (refreshing) return;
    refreshing = true;
    try {
      final responses = await Future.wait([
        widget.api.assistantRequest('GET', '/api/coding/tasks'),
        widget.api.assistantRequest('GET', '/api/memory'),
        widget.api.assistantRequest('GET', '/api/assistant/state'),
      ]);
      if (!mounted) return;
      setState(() {
        tasks = responses[0]['tasks'] as List<dynamic>? ?? [];
        memories = responses[1]['items'] as List<dynamic>? ?? [];
        projects = responses[2]['projects'] as List<dynamic>? ?? [];
        if (project != null && !projects.contains(project)) project = null;
        extraction =
            responses[2]['extraction']?['status']?.toString() ?? 'idle';
      });
      if (selected != null &&
          !connected &&
          !terminal.contains(currentTask?['status'])) {
        listen(selected!, reset: false);
      }
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    } finally {
      refreshing = false;
    }
  }

  Map<String, dynamic>? get currentTask {
    for (final task in tasks) {
      if (task['id'] == selected) return Map<String, dynamic>.from(task as Map);
    }
    return null;
  }

  Future<void> action(Future<void> Function() work) async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await work();
      await refresh();
    } catch (exception) {
      if (mounted) setState(() => error = exception.toString());
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> conversationHistory() => action(() async {
    final response = await widget.api.assistantRequest(
      'GET',
      '/api/conversations',
    );
    if (!mounted) return;
    final rows = response['conversations'] as List<dynamic>? ?? [];
    final identifier = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('Resume a conversation'),
        children: [
          if (rows.isEmpty)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Text('No saved conversations.'),
            ),
          for (final row in rows.where(
            (row) => !row['id'].toString().startsWith('coding:'),
          ))
            SimpleDialogOption(
              onPressed: () => Navigator.pop(context, row['id'].toString()),
              child: Text(
                '${row['project'].toString().isEmpty ? 'Personal' : row['project']} · ${row['created_at']}\n${row['summary'].toString().isEmpty ? 'Saved conversation' : row['summary']}',
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ),
        ],
      ),
    );
    if (identifier != null) {
      await widget.api.assistantRequest(
        'POST',
        '/api/conversations/$identifier/resume',
      );
    }
  });

  Future<void> listen(String id, {bool reset = true}) async {
    final version = ++streamVersion;
    await stream?.cancel();
    if (!mounted || version != streamVersion) return;
    setState(() {
      selected = id;
      connected = true;
      if (reset) {
        events = [];
        cursor = 0;
      }
    });
    stream = widget.api
        .codingEvents(id, cursor)
        .listen(
          (event) {
            if (!mounted || version != streamVersion) return;
            final next = (event['id'] as num).toInt();
            if (next <= cursor) return;
            setState(() {
              cursor = next;
              events.add(event);
              if (events.length > 60) events.removeAt(0);
            });
            if (event['type'].toString().startsWith('task.') ||
                event['type'] == 'agent.status') {
              refresh();
            }
          },
          onError: (Object exception) {
            if (mounted && version == streamVersion) {
              setState(() {
                connected = false;
                error =
                    'Event stream disconnected. Reconnecting automatically. $exception';
              });
            }
          },
          onDone: () {
            if (mounted && version == streamVersion) {
              setState(() => connected = false);
              refresh();
            }
          },
        );
  }

  Future<void> start({bool resume = false}) => action(() async {
    if (project == null || prompt.text.trim().isEmpty) return;
    final task = await widget.api.assistantRequest(
      'POST',
      '/api/coding/tasks',
      body: {
        'project': project,
        'prompt': prompt.text.trim(),
        if (resume) 'resume_id': selected,
      },
    );
    prompt.clear();
    await listen(task['id'] as String);
  });

  Future<void> answerInput(Map<String, dynamic> pending) async {
    final questions = pending['params']['questions'] as List<dynamic>;
    final controls = {
      for (final q in questions) q['id'] as String: TextEditingController(),
    };
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Codex needs your input'),
        content: SizedBox(
          width: 560,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (final question in questions)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: TextField(
                      controller: controls[question['id']],
                      maxLines: 3,
                      decoration: InputDecoration(
                        labelText: question['header']?.toString(),
                        helperText: question['question']?.toString(),
                        helperMaxLines: 6,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Back'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Submit'),
          ),
        ],
      ),
    );
    final answers = {
      for (final entry in controls.entries) entry.key: entry.value.text,
    };
    for (final control in controls.values) {
      control.dispose();
    }
    if (accepted == true) {
      await action(() async {
        await widget.api.assistantRequest(
          'POST',
          '/tasks/$selected/input',
          body: {'request_id': pending['id'], 'answers': answers},
        );
      });
    }
  }

  Future<void> publish(Map<String, dynamic> item) => action(() async {
    final vaults = await widget.api.obsidianVaults();
    if (!mounted) return;
    if (vaults.isEmpty) {
      throw const JarvisApiException(
        'Connect an Obsidian vault in Settings first.',
      );
    }
    final vault = await showDialog<ObsidianVault>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('Choose a vault'),
        children: [
          for (final v in vaults)
            SimpleDialogOption(
              onPressed: () => Navigator.pop(context, v),
              child: Text(v.name),
            ),
        ],
      ),
    );
    if (vault == null) return;
    var preview = await widget.api.assistantRequest(
      'POST',
      '/api/memory/${item['id']}/preview',
      body: {'vault_id': vault.id},
    );
    if (preview['selection_required'] == true && mounted) {
      final path = await showDialog<String>(
        context: context,
        builder: (context) => SimpleDialog(
          title: const Text('Choose the note to merge'),
          children: [
            for (final path in preview['matches'] as List<dynamic>)
              SimpleDialogOption(
                onPressed: () => Navigator.pop(context, path),
                child: Text(path as String),
              ),
          ],
        ),
      );
      if (path == null) return;
      preview = await widget.api.assistantRequest(
        'POST',
        '/api/memory/${item['id']}/preview',
        body: {'vault_id': vault.id, 'relative_path': path},
      );
    }
    if (!mounted) return;
    final approved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Review Obsidian merge'),
        content: SizedBox(
          width: 680,
          child: SingleChildScrollView(
            child: SelectableText(
              '${preview['relative_path']}\n\n${preview['content']}',
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Publish this merge'),
          ),
        ],
      ),
    );
    if (approved == true) {
      await widget.api.assistantRequest(
        'POST',
        '/api/memory/publish/${preview['token']}',
      );
    }
  });

  @override
  Widget build(BuildContext context) {
    final task = currentTask;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Coding & memory',
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        const Text(
          'Choose a project, delegate code work, and review what JARVIS remembers.',
          style: TextStyle(color: ConsoleColors.muted),
        ),
        const SizedBox(height: 16),
        if (error != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: SelectableText(
              error!,
              style: const TextStyle(color: ConsoleColors.danger),
            ),
          ),
        DropdownButtonFormField<String>(
          initialValue: project,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Registered project'),
          items: [
            for (final value in projects)
              DropdownMenuItem(
                value: value as String,
                child: Text(value, overflow: TextOverflow.ellipsis),
              ),
          ],
          onChanged: busy ? null : (value) => setState(() => project = value),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: prompt,
          minLines: 2,
          maxLines: 5,
          decoration: const InputDecoration(
            labelText: 'Coding task',
            hintText: 'Describe the change or investigation.',
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            FilledButton.icon(
              onPressed: busy || project == null ? null : () => start(),
              icon: const Icon(Icons.code),
              label: const Text('Start Codex'),
            ),
            OutlinedButton(
              onPressed:
                  busy ||
                      task == null ||
                      !terminal.contains(task['status']) ||
                      task['thread_id'] == null ||
                      project != task['project']
                  ? null
                  : () => start(resume: true),
              child: const Text('Continue selected task'),
            ),
            TextButton(
              onPressed: busy || project == null
                  ? null
                  : () => action(() async {
                      await widget.api.assistantRequest(
                        'POST',
                        '/api/conversation/project',
                        body: {'project': project},
                      );
                    }),
              child: const Text('Use project in chat'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        for (final row in tasks.take(10))
          ListTile(
            contentPadding: EdgeInsets.zero,
            selected: row['id'] == selected,
            title: Text(
              row['prompt'].toString(),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text(
              '${row['project']} · ${row['status']}',
              style: metadataStyle,
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => listen(row['id'] as String),
          ),
        if (task != null) ...[
          const Divider(),
          Row(
            children: [
              Expanded(
                child: Text(
                  '${task['status']} · ${connected ? 'Live events' : 'Saved events'}',
                  style: metadataStyle,
                ),
              ),
              if (!terminal.contains(task['status']))
                TextButton(
                  onPressed: busy
                      ? null
                      : () => action(() async {
                          await widget.api.assistantRequest(
                            'POST',
                            '/tasks/$selected/cancel',
                          );
                        }),
                  child: const Text('Cancel task'),
                ),
            ],
          ),
          if (task['error'].toString().isNotEmpty)
            SelectableText(
              task['error'].toString(),
              style: const TextStyle(color: ConsoleColors.danger),
            ),
          for (final raw in task['pending'] as List<dynamic>)
            Builder(
              builder: (context) {
                final pending = Map<String, dynamic>.from(raw as Map);
                final high = pending['high_risk'] == true;
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        pending['method'].toString().endsWith(
                              'requestUserInput',
                            )
                            ? 'Your input is needed'
                            : 'Approval requested',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      SelectableText(
                        const JsonEncoder.withIndent(
                          '  ',
                        ).convert(pending['params']),
                        style: metadataStyle,
                      ),
                      if (high)
                        const Text(
                          'High-risk action blocked: authorized voice verification is not configured.',
                          style: TextStyle(color: ConsoleColors.warning),
                        ),
                      if (pending['method'].toString().endsWith(
                        'requestUserInput',
                      ))
                        TextButton(
                          onPressed: busy ? null : () => answerInput(pending),
                          child: const Text('Answer questions'),
                        )
                      else
                        Wrap(
                          spacing: 8,
                          children: [
                            for (final entry in {
                              'allow_once': 'Allow once',
                              if (pending['method'] ==
                                  'item/commandExecution/requestApproval')
                                'always_allow':
                                    'Always allow this command here',
                              'deny': 'Deny',
                            }.entries)
                              OutlinedButton(
                                onPressed: busy || (high && entry.key != 'deny')
                                    ? null
                                    : () => action(() async {
                                        await widget.api.assistantRequest(
                                          'POST',
                                          '/tasks/$selected/approve',
                                          body: {
                                            'request_id': pending['id'],
                                            'decision': entry.key,
                                          },
                                        );
                                      }),
                                child: Text(entry.value),
                              ),
                          ],
                        ),
                    ],
                  ),
                );
              },
            ),
          for (final event in events.reversed.take(15))
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: Text(event['type'].toString(), style: metadataStyle),
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: SelectableText(
                    const JsonEncoder.withIndent('  ').convert(event['body']),
                    style: metadataStyle,
                  ),
                ),
              ],
            ),
          if (task['result'].toString().isNotEmpty)
            SelectableText(task['result'].toString()),
        ],
        const SizedBox(height: 24),
        Text('Long-term memory', style: Theme.of(context).textTheme.titleLarge),
        Text(
          'Extraction: $extraction. Confirming a candidate allows Gemini to use it in future answers.',
          style: const TextStyle(color: ConsoleColors.muted),
        ),
        Wrap(
          spacing: 8,
          children: [
            TextButton(
              onPressed: busy ? null : conversationHistory,
              child: const Text('Resume conversation'),
            ),
            TextButton(
              onPressed: busy
                  ? null
                  : () => action(() async {
                      await widget.api.assistantRequest(
                        'POST',
                        '/api/memory/extract',
                      );
                    }),
              child: const Text('Extract recent conversation'),
            ),
            TextButton(
              onPressed: busy
                  ? null
                  : () => action(() async {
                      await widget.api.assistantRequest(
                        'POST',
                        '/api/conversation/end',
                      );
                    }),
              child: const Text('End conversation'),
            ),
            TextButton(
              onPressed: busy
                  ? null
                  : () => action(() async {
                      await widget.api.assistantRequest(
                        'DELETE',
                        '/api/coding/grants',
                      );
                    }),
              child: const Text('Revoke saved coding approvals'),
            ),
          ],
        ),
        if (memories.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: Text(
              'No durable memories yet. Important conversation details appear here for review.',
            ),
          ),
        for (final raw in memories.take(30))
          Builder(
            builder: (context) {
              final item = Map<String, dynamic>.from(raw as Map);
              return ExpansionTile(
                tilePadding: EdgeInsets.zero,
                title: Text(item['title'].toString()),
                subtitle: Text(
                  '${item['type']} · ${item['status']} · ${item['project']}',
                  style: metadataStyle,
                ),
                children: [
                  Align(
                    alignment: Alignment.centerLeft,
                    child: SelectableText(
                      '${item['summary']}\n\nImportance: ${item['importance']} · Confidence: ${item['confidence']}\nEvidence: ${jsonEncode(item['evidence'])}',
                    ),
                  ),
                  Wrap(
                    spacing: 8,
                    children: [
                      if (item['status'] == 'proposed')
                        FilledButton(
                          onPressed: busy
                              ? null
                              : () => action(() async {
                                  await widget.api.assistantRequest(
                                    'POST',
                                    '/api/memory/${item['id']}/review',
                                    body: {'status': 'confirmed'},
                                  );
                                }),
                          child: const Text('Confirm for AI memory'),
                        ),
                      if (item['status'] != 'rejected')
                        TextButton(
                          onPressed: busy
                              ? null
                              : () => action(() async {
                                  await widget.api.assistantRequest(
                                    'POST',
                                    '/api/memory/${item['id']}/review',
                                    body: {'status': 'rejected'},
                                  );
                                }),
                          child: const Text('Reject / stop using'),
                        ),
                      if (item['status'] == 'confirmed')
                        OutlinedButton(
                          onPressed: busy ? null : () => publish(item),
                          child: const Text('Preview Obsidian merge'),
                        ),
                    ],
                  ),
                ],
              );
            },
          ),
        const SizedBox(height: 28),
      ],
    );
  }
}
