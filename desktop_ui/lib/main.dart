import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'console_theme.dart';
import 'core_indicator.dart';
import 'error_log.dart';
import 'errors_page.dart';
import 'hologram_backdrop.dart';
import 'jarvis_api.dart';
import 'runtime_monitor.dart';
import 'runtime_panel.dart';
import 'speech_controller.dart';
import 'workspace_pages.dart';

void main() => runApp(const JarvisApp());

class JarvisApp extends StatefulWidget {
  const JarvisApp({super.key, this.api, this.errorLog});
  final JarvisApi? api;
  final AppErrorLog? errorLog;
  @override
  State<JarvisApp> createState() => _JarvisAppState();
}

class _JarvisAppState extends State<JarvisApp> {
  late final AppErrorLog _errors = widget.errorLog ?? AppErrorLog();
  late final AppErrorCapture _capture;

  @override
  void initState() {
    super.initState();
    _capture = AppErrorCapture(_errors, (_) => const InterfaceErrorFallback());
  }

  @override
  void dispose() {
    _capture.dispose();
    if (widget.errorLog == null) _errors.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'JARVIS',
    debugShowCheckedModeBanner: false,
    theme: consoleTheme(),
    home: DesktopWorkspace(api: widget.api, errorLog: _errors),
  );
}

class DesktopWorkspace extends StatefulWidget {
  const DesktopWorkspace({super.key, this.api, required this.errorLog});
  final JarvisApi? api;
  final AppErrorLog errorLog;
  @override
  State<DesktopWorkspace> createState() => _DesktopWorkspaceState();
}

class _DesktopWorkspaceState extends State<DesktopWorkspace> {
  late final JarvisApi _api = widget.api ?? JarvisApi();
  late final RuntimeMonitor _monitor = RuntimeMonitor(_api);
  late final SpeechController _speech = SpeechController(_api);
  final _prompt = TextEditingController();
  final _promptFocus = FocusNode();
  final _scroll = ScrollController();
  final _scaffold = GlobalKey<ScaffoldState>();
  final _runs = <SessionRun>[];
  final _archivedRuns = <SessionRun>[];
  int _page = 0;
  bool _reduceTransparency = false;
  bool _reduceMotion = false;
  SpeechProvider _speechProvider = SpeechProvider.system;
  bool _autoReadReplies = false;
  bool _submitting = false;
  String? _lastMonitorError;
  TextEditingValue? _enterValue;
  Duration? _enterTime;

  @override
  void initState() {
    super.initState();
    _monitor.addListener(_recordMonitorError);
    _monitor.start();
    unawaited(_loadConversationArchive());
  }

  Future<void> _loadConversationArchive() async {
    try {
      final history = await _api.conversationHistory();
      if (!mounted || history.isEmpty) return;
      setState(() {
        _archivedRuns.addAll(
          history.map(
            (turn) => SessionRun.restored(
              prompt: turn.user,
              started: turn.createdAt,
              restoredReply: JarvisChatReply(
                reply: turn.assistant,
                speech: turn.speech,
                toolResults: const [],
              ),
            ),
          ),
        );
      });
    } on JarvisApiException {
      // RuntimeMonitor already reports connection failures and retries.
    }
  }

  void _recordMonitorError() {
    final error = _monitor.error;
    if (error != null && error != _lastMonitorError) {
      widget.errorLog.record(source: 'Connection', message: error);
    }
    // Only record a transition, not a duplicate on every two-second poll.
    _lastMonitorError = error;
  }

  @override
  void dispose() {
    _monitor.dispose();
    _speech.dispose();
    if (widget.api == null) _api.close();
    _prompt.dispose();
    _promptFocus.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => CallbackShortcuts(
    bindings: {
      const SingleActivator(LogicalKeyboardKey.enter, control: true):
          _submitPrompt,
    },
    child: LayoutBuilder(
      builder: (context, constraints) {
        final narrow = constraints.maxWidth < 600;
        final inspector =
            constraints.maxWidth >= 1280 && _page != 2 && _page != 4;
        final headerCompact =
            inspector ||
            constraints.maxWidth < 1600 ||
            MediaQuery.textScalerOf(context).scale(13) / 13 > 1.0;
        return Scaffold(
          key: _scaffold,
          endDrawer: Drawer(
            width: 320,
            backgroundColor: ConsoleColors.monitor,
            child: SafeArea(
              child: ListView(
                padding: const EdgeInsets.all(22),
                children: [
                  Align(
                    alignment: Alignment.centerRight,
                    child: IconButton(
                      tooltip: 'Close system monitor',
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close),
                    ),
                  ),
                  RuntimePanel(monitor: _monitor),
                  const SizedBox(height: 28),
                  const SafetyNote(),
                ],
              ),
            ),
          ),
          bottomNavigationBar: narrow
              ? ListenableBuilder(
                  listenable: widget.errorLog,
                  builder: (context, _) => NavigationBar(
                    selectedIndex: _page,
                    onDestinationSelected: _selectPage,
                    backgroundColor: ConsoleColors.rail,
                    indicatorColor: ConsoleColors.accentSoft,
                    height: 72,
                    destinations: [
                      for (final entry in _destinations)
                        NavigationDestination(
                          icon: Badge(
                            isLabelVisible:
                                entry.$1 == 'Errors' &&
                                widget.errorLog.entries.isNotEmpty,
                            child: Icon(entry.$2),
                          ),
                          label: entry.$1,
                        ),
                    ],
                  ),
                )
              : null,
          body: Stack(
            children: [
              const Positioned.fill(child: HologramBackdrop()),
              SafeArea(
                child: Row(
                  children: [
                    if (!narrow)
                      ListenableBuilder(
                        listenable: widget.errorLog,
                        builder: (context, _) => _Sidebar(
                          selected: _page,
                          onSelect: _selectPage,
                          compact: constraints.maxWidth < 1020,
                          monitor: _monitor,
                          runs: _runs,
                          archivedCount: _archivedRuns.length,
                          busy: _submitting,
                          errorCount: widget.errorLog.entries.length,
                        ),
                      ),
                    Expanded(
                      child: Column(
                        children: [
                          _Header(
                            page: _page,
                            compact: headerCompact,
                            monitor: _monitor,
                            showMonitor: !inspector,
                            onMonitor: () =>
                                _scaffold.currentState!.openEndDrawer(),
                          ),
                          ListenableBuilder(
                            listenable: widget.errorLog,
                            builder: (context, _) =>
                                _page != 4 && widget.errorLog.hasInterfaceErrors
                                ? Padding(
                                    padding: const EdgeInsets.fromLTRB(
                                      24,
                                      12,
                                      24,
                                      0,
                                    ),
                                    child: ErrorNotice(
                                      message:
                                          'An interface error was recorded. Some content may be unavailable.',
                                      onOpenErrors: () => _selectPage(4),
                                    ),
                                  )
                                : const SizedBox.shrink(),
                          ),
                          Expanded(child: _buildPage()),
                        ],
                      ),
                    ),
                    if (inspector)
                      Container(
                        width: 286,
                        decoration: const BoxDecoration(
                          color: ConsoleColors.monitor,
                          border: Border(
                            left: BorderSide(color: ConsoleColors.line),
                          ),
                        ),
                        child: ListView(
                          padding: const EdgeInsets.fromLTRB(22, 18, 22, 24),
                          children: [
                            RuntimePanel(monitor: _monitor),
                            const SizedBox(height: 28),
                            const SafetyNote(),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    ),
  );

  Widget _buildPage() => switch (_page) {
    1 => TasksPage(
      runs: _runs,
      archivedRuns: _archivedRuns,
      onOpenAssistant: () => _selectPage(0),
      onOpenErrors: () => _selectPage(4),
    ),
    2 => DevicePage(
      monitor: _monitor,
      solid: _reduceTransparency,
      reduceMotion: _reduceMotion,
      busy: _submitting,
      speech: _speech,
      speechProvider: _speechProvider,
    ),
    3 => SettingsPage(
      monitor: _monitor,
      solid: _reduceTransparency,
      reduceMotion: _reduceMotion,
      onReduceMotion: (value) => setState(() => _reduceMotion = value),
      onReduceTransparency: (value) =>
          setState(() => _reduceTransparency = value),
      speechProvider: _speechProvider,
      onSpeechProvider: (provider) =>
          setState(() => _speechProvider = provider),
      autoReadReplies: _autoReadReplies,
      onAutoReadReplies: (value) => setState(() => _autoReadReplies = value),
      onPermissionPreview: _showPermissionPreview,
    ),
    4 => ErrorsPage(log: widget.errorLog),
    _ => Column(
      children: [
        Expanded(
          child: _runs.isEmpty
              ? WelcomePanel(
                  monitor: _monitor,
                  solid: _reduceTransparency,
                  onPrompt: _fillPrompt,
                )
              : ListView.builder(
                  key: const PageStorageKey('conversation'),
                  controller: _scroll,
                  padding: const EdgeInsets.fromLTRB(28, 24, 28, 16),
                  itemCount: _runs.length,
                  itemBuilder: (context, index) => _RunView(
                    run: _runs[index],
                    runIndex: index,
                    reduceMotion: _reduceMotion,
                    onOpenErrors: () => _selectPage(4),
                    speech: _speech,
                    speechProvider: _speechProvider,
                  ),
                ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 12, 24, 18),
          child: _Composer(
            controller: _prompt,
            focusNode: _promptFocus,
            busy: _submitting,
            onSend: _submitPrompt,
            onKeyEvent: _composerKeyEvent,
            onVoiceInput: () => _toast(
              'Voice input is planned. No microphone audio is being recorded.',
            ),
          ),
        ),
      ],
    ),
  };

  void _selectPage(int value) {
    _enterValue = null;
    setState(() => _page = value);
  }

  KeyEventResult _composerKeyEvent(FocusNode node, KeyEvent event) {
    if (event is KeyUpEvent) return KeyEventResult.ignored;
    final enter =
        event.logicalKey == LogicalKeyboardKey.enter ||
        event.logicalKey == LogicalKeyboardKey.numpadEnter;
    final keyboard = HardwareKeyboard.instance;
    final composing = _prompt.value.composing;
    if (!enter ||
        keyboard.isControlPressed ||
        keyboard.isAltPressed ||
        keyboard.isMetaPressed ||
        (composing.isValid && !composing.isCollapsed)) {
      _enterValue = null;
      return KeyEventResult.ignored;
    }
    if (_submitting || event is KeyRepeatEvent) return KeyEventResult.handled;
    final value = _prompt.value;
    if (!keyboard.isShiftPressed &&
        value == _enterValue &&
        _enterTime != null &&
        event.timeStamp - _enterTime! <= const Duration(milliseconds: 600) &&
        value.text.trim().isNotEmpty) {
      _enterValue = null;
      _submitPrompt();
      return KeyEventResult.handled;
    }
    final selection = value.selection;
    final start = selection.isValid ? selection.start : value.text.length;
    final end = selection.isValid ? selection.end : value.text.length;
    _prompt.value = TextEditingValue(
      text: value.text.replaceRange(start, end, '\n'),
      selection: TextSelection.collapsed(offset: start + 1),
    );
    _enterValue = keyboard.isShiftPressed ? null : _prompt.value;
    _enterTime = event.timeStamp;
    return KeyEventResult.handled;
  }

  void _fillPrompt(String text) {
    _prompt.text = text;
    _prompt.selection = TextSelection.collapsed(offset: text.length);
    _promptFocus.requestFocus();
  }

  void _scrollToLatest() => WidgetsBinding.instance.addPostFrameCallback((_) {
    if (!mounted || !_scroll.hasClients) return;
    if (_reduceMotion || MediaQuery.disableAnimationsOf(context)) {
      _scroll.jumpTo(_scroll.position.maxScrollExtent);
    } else {
      _scroll.animateTo(
        _scroll.position.maxScrollExtent,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
      );
    }
  });
  Future<void> _submitPrompt() async {
    if (_submitting || _page != 0) return;
    final text = _prompt.text.trim();
    if (text.isEmpty) {
      _toast('Write a request before sending it.');
      _promptFocus.requestFocus();
      return;
    }
    if (text.length > 12000) {
      _toast('Keep your request under 12,000 characters.');
      return;
    }
    final run = SessionRun(text);
    setState(() {
      _runs.add(run);
      _submitting = true;
      _prompt.clear();
    });
    _scrollToLatest();
    try {
      final reply = await _api.sendMessage(text);
      if (!mounted) return;
      setState(() => run.reply = reply);
      if (_autoReadReplies) {
        unawaited(_speech.speak(reply.speech, provider: _speechProvider));
      }
      for (final result in reply.toolResults) {
        if (SessionRun.resultFailed(result)) {
          widget.errorLog.record(
            source: 'Tool',
            message: '${result['tool_name'] ?? 'Tool'} failed',
            details: const JsonEncoder.withIndent('  ').convert(result),
          );
        }
      }
    } catch (error, stack) {
      if (!mounted) return;
      final message = error is JarvisApiException
          ? error.message
          : error.toString();
      widget.errorLog.record(source: 'Request', message: message, stack: stack);
      setState(() => run.error = message);
    } finally {
      if (mounted) {
        setState(() {
          run.finished = DateTime.now();
          _submitting = false;
        });
        _scrollToLatest();
        _promptFocus.requestFocus();
      }
    }
  }

  void _showPermissionPreview() => showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('Permission preview'),
      content: const SizedBox(
        width: 400,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            StatusLabel('Demonstration only', color: ConsoleColors.warning),
            SizedBox(height: 20),
            Text(
              'A request to run project tests would show its workspace, risk and action before approval.',
            ),
            SizedBox(height: 16),
            Text(
              'This preview does not authorize or execute anything. Real confirmations still go through the existing conversation and TaskRouter.',
              style: TextStyle(color: ConsoleColors.muted, height: 1.6),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Close'),
        ),
        FilledButton(
          onPressed: () {
            Navigator.pop(context);
            _toast('Preview confirmed. Nothing was executed.');
          },
          child: const Text('Try preview'),
        ),
      ],
    ),
  );
  void _toast(String message) => ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(message)));
}

const _destinations = [
  ('Assistant', Icons.chat_bubble_outline),
  ('Tasks', Icons.account_tree_outlined),
  ('Device', Icons.developer_board_outlined),
  ('Settings', Icons.tune),
  ('Errors', Icons.bug_report_outlined),
];

class _Sidebar extends StatelessWidget {
  const _Sidebar({
    required this.selected,
    required this.onSelect,
    required this.compact,
    required this.monitor,
    required this.runs,
    required this.archivedCount,
    required this.busy,
    required this.errorCount,
  });
  final int selected;
  final ValueChanged<int> onSelect;
  final bool compact;
  final RuntimeMonitor monitor;
  final List<SessionRun> runs;
  final int archivedCount;
  final bool busy;
  final int errorCount;
  @override
  Widget build(BuildContext context) => Container(
    width: compact
        ? 80
        : 216 *
              (MediaQuery.textScalerOf(context).scale(13) / 13).clamp(1.0, 1.6),
    decoration: const BoxDecoration(
      color: ConsoleColors.rail,
      border: Border(right: BorderSide(color: ConsoleColors.line)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: EdgeInsets.fromLTRB(compact ? 21 : 22, 26, 18, 30),
          child: Row(
            children: [
              const CoreIndicator(size: 34, label: false),
              if (!compact) ...[
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    'J.A.R.V.I.S',
                    maxLines: 1,
                    overflow: TextOverflow.fade,
                    softWrap: false,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
        if (!compact)
          const Padding(
            padding: EdgeInsets.fromLTRB(24, 0, 20, 12),
            child: Text(
              'WORKSPACE',
              style: TextStyle(
                color: ConsoleColors.dim,
                fontSize: 10,
                letterSpacing: 1.7,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        for (var i = 0; i < _destinations.length; i++)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
            child: Tooltip(
              message: _destinations[i].$1,
              child: Material(
                color: selected == i
                    ? ConsoleColors.accentSoft
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(8),
                child: InkWell(
                  key: ValueKey('nav-$i'),
                  onTap: () => onSelect(i),
                  borderRadius: BorderRadius.circular(8),
                  child: Semantics(
                    selected: selected == i,
                    button: true,
                    label: compact ? _destinations[i].$1 : null,
                    child: Padding(
                      padding: EdgeInsets.symmetric(
                        horizontal: compact ? 16 : 13,
                        vertical: 14,
                      ),
                      child: Row(
                        children: [
                          Badge(
                            isLabelVisible: compact && i == 4 && errorCount > 0,
                            child: Icon(
                              _destinations[i].$2,
                              size: 20,
                              color: selected == i
                                  ? ConsoleColors.accent
                                  : ConsoleColors.muted,
                            ),
                          ),
                          if (!compact) ...[
                            const SizedBox(width: 12),
                            Text(
                              _destinations[i].$1,
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: selected == i
                                    ? FontWeight.w600
                                    : FontWeight.w400,
                                color: selected == i
                                    ? ConsoleColors.ink
                                    : ConsoleColors.muted,
                              ),
                            ),
                            const Spacer(),
                            if (i == 1 && runs.length + archivedCount > 0)
                              Text(
                                '${runs.length + archivedCount}',
                                style: metadataStyle,
                              ),
                            if (i == 4 && errorCount > 0)
                              Text(
                                '$errorCount',
                                style: metadataStyle.copyWith(
                                  color: ConsoleColors.warning,
                                ),
                              ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        const Spacer(),
        if (!compact)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'This session',
                  style: TextStyle(color: ConsoleColors.muted, fontSize: 12),
                ),
                const SizedBox(height: 12),
                Text(
                  busy
                      ? 'Request in progress'
                      : runs.isEmpty
                      ? 'No requests yet'
                      : '${runs.length} request${runs.length == 1 ? '' : 's'}',
                  style: const TextStyle(fontSize: 13),
                ),
                const SizedBox(height: 8),
                Text(
                  busy
                      ? 'View the response in Assistant.'
                      : 'Your workspace stays on this device.',
                  style: const TextStyle(
                    color: ConsoleColors.dim,
                    fontSize: 11,
                    height: 1.6,
                  ),
                ),
                const SizedBox(height: 24),
                const Divider(),
              ],
            ),
          ),
        Padding(
          padding: EdgeInsets.all(compact ? 26 : 24),
          child: ListenableBuilder(
            listenable: monitor,
            builder: (context, _) => compact
                ? Tooltip(
                    message: monitor.online
                        ? 'Core connected'
                        : 'Core not connected',
                    child: Icon(
                      Icons.lan_outlined,
                      color: monitor.online
                          ? ConsoleColors.good
                          : ConsoleColors.warning,
                    ),
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      StatusLabel(
                        monitor.online
                            ? 'Core connected'
                            : 'Core not connected',
                        color: monitor.online
                            ? ConsoleColors.good
                            : ConsoleColors.warning,
                      ),
                      const SizedBox(height: 7),
                      const Text(
                        'Local-first • Windows',
                        style: TextStyle(
                          color: ConsoleColors.dim,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ],
    ),
  );
}

class _Header extends StatelessWidget {
  const _Header({
    required this.page,
    required this.monitor,
    required this.compact,
    required this.showMonitor,
    required this.onMonitor,
  });
  final int page;
  final RuntimeMonitor monitor;
  final bool compact;
  final bool showMonitor;
  final VoidCallback onMonitor;
  @override
  Widget build(BuildContext context) {
    final showIdentity =
        MediaQuery.sizeOf(context).width >= 820 &&
        MediaQuery.textScalerOf(context).scale(13) / 13 <= 1.15;
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 18 : 28,
        vertical: 14,
      ),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: ConsoleColors.line)),
      ),
      child: Row(
        children: [
          Text(
            _destinations[page].$1,
            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
          ),
          if (showIdentity) ...[
            const SizedBox(width: 14),
            Container(width: 1, height: 15, color: ConsoleColors.line),
            const SizedBox(width: 14),
            const Text(
              'Personal assistant',
              style: TextStyle(color: ConsoleColors.dim, fontSize: 12),
            ),
          ],
          const Spacer(),
          if (showIdentity)
            ListenableBuilder(
              listenable: monitor,
              builder: (context, _) {
                final model = monitor.health?.brain;
                return Text(
                  model == null
                      ? 'MODEL · UNAVAILABLE'
                      : 'MODEL · ${model.toUpperCase()}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: metadataStyle.copyWith(
                    color: model == null
                        ? ConsoleColors.dim
                        : ConsoleColors.accent,
                    fontSize: 10,
                    letterSpacing: .8,
                  ),
                );
              },
            ),
          if (!compact)
            ListenableBuilder(
              listenable: monitor,
              builder: (context, _) => StatusLabel(
                monitor.online ? 'Core link online' : 'Core link offline',
                color: monitor.online
                    ? ConsoleColors.good
                    : ConsoleColors.warning,
              ),
            ),
          if (!compact) const SizedBox(width: 18),
          if (!compact) const _LiveClock(),
          if (!compact)
            ListenableBuilder(
              listenable: monitor,
              builder: (context, _) => Text(
                monitor.health?.brain ?? 'Codex',
                style: metadataStyle.copyWith(fontSize: 11),
              ),
            ),
          if (showMonitor) ...[
            const SizedBox(width: 8),
            IconButton(
              tooltip: 'Open system monitor',
              onPressed: onMonitor,
              icon: const Icon(Icons.monitor_heart_outlined, size: 20),
            ),
          ] else
            const SizedBox(height: 44),
        ],
      ),
    );
  }
}

class _LiveClock extends StatefulWidget {
  const _LiveClock();

  @override
  State<_LiveClock> createState() => _LiveClockState();
}

class _LiveClockState extends State<_LiveClock> {
  late final Timer _timer = Timer.periodic(
    const Duration(seconds: 1),
    (_) => mounted ? setState(() {}) : null,
  );

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Text(
    clockLabel(DateTime.now()),
    style: metadataStyle.copyWith(color: ConsoleColors.accent, fontSize: 11),
  );
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.focusNode,
    required this.busy,
    required this.onSend,
    required this.onKeyEvent,
    required this.onVoiceInput,
  });
  final TextEditingController controller;
  final FocusNode focusNode;
  final bool busy;
  final VoidCallback onSend;
  final FocusOnKeyEventCallback onKeyEvent;
  final VoidCallback onVoiceInput;
  @override
  Widget build(BuildContext context) => ConsolePanel(
    key: const ValueKey('composer'),
    padding: const EdgeInsets.all(8),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Focus(
            canRequestFocus: false,
            skipTraversal: true,
            onKeyEvent: onKeyEvent,
            child: TextField(
              key: const ValueKey('prompt'),
              controller: controller,
              focusNode: focusNode,
              minLines: 1,
              maxLines: 5,
              readOnly: busy,
              style: const TextStyle(fontSize: 14, height: 1.5),
              textCapitalization: TextCapitalization.sentences,
              keyboardType: TextInputType.multiline,
              textInputAction: TextInputAction.newline,
              decoration: const InputDecoration(
                hintText: 'Ask a question or describe a task…',
                hintMaxLines: 1,
                filled: false,
                border: InputBorder.none,
                enabledBorder: InputBorder.none,
                focusedBorder: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 12,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        IconButton(
          key: const ValueKey('voice-input'),
          tooltip: 'Voice input is planned. No microphone audio is recorded.',
          onPressed: busy ? null : onVoiceInput,
          icon: const Icon(Icons.mic_none, size: 19),
        ),
        IconButton.filled(
          key: const ValueKey('send'),
          tooltip: busy
              ? 'Waiting for Core. No live cancellation is available.'
              : 'Send · Ctrl + Enter or double Enter\nShift + Enter for a new line',
          onPressed: busy ? null : onSend,
          icon: Icon(busy ? Icons.hourglass_top : Icons.arrow_upward, size: 17),
        ),
      ],
    ),
  );
}

class _RunView extends StatelessWidget {
  const _RunView({
    required this.run,
    required this.runIndex,
    required this.reduceMotion,
    required this.onOpenErrors,
    required this.speech,
    required this.speechProvider,
  });
  final SessionRun run;
  final int runIndex;
  final bool reduceMotion;
  final VoidCallback onOpenErrors;
  final SpeechController speech;
  final SpeechProvider speechProvider;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 30),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              'You',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
            ),
            const SizedBox(width: 12),
            Text(
              clockLabel(run.started),
              style: metadataStyle.copyWith(fontSize: 10),
            ),
          ],
        ),
        const SizedBox(height: 10),
        SelectableText(
          run.prompt,
          style: const TextStyle(fontSize: 14, height: 1.7),
        ),
        const SizedBox(height: 22),
        Row(
          children: [
            CoreIndicator(
              size: 30,
              label: false,
              busy: run.working,
              reduceMotion: reduceMotion,
            ),
            const SizedBox(width: 10),
            const Text(
              'JARVIS',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(width: 14),
            StatusLabel(run.status, color: run.color),
          ],
        ),
        const SizedBox(height: 12),
        if (run.working)
          const Text(
            'Processing with the configured reasoning backend and routing policy.\nThe response and tool evidence will appear here.',
            style: TextStyle(
              color: ConsoleColors.muted,
              fontSize: 13,
              height: 1.7,
            ),
          ),
        if (run.error != null)
          ErrorNotice(
            message: 'Request failed. Check Errors before trying again.',
            onOpenErrors: onOpenErrors,
          ),
        if (run.reply != null) ...[
          Align(
            alignment: Alignment.centerRight,
            child: ListenableBuilder(
              listenable: speech,
              builder: (context, _) => TextButton.icon(
                onPressed: speech.speaking
                    ? speech.stop
                    : () async {
                        await speech.speak(
                          run.reply!.speech,
                          provider: speechProvider,
                        );
                        if (!context.mounted || speech.error == null) return;
                        ScaffoldMessenger.of(
                          context,
                        ).showSnackBar(SnackBar(content: Text(speech.error!)));
                      },
                icon: Icon(
                  speech.speaking
                      ? Icons.stop_circle_outlined
                      : Icons.volume_up_outlined,
                  size: 17,
                ),
                label: Text(speech.speaking ? 'Stop reading' : 'Read reply'),
              ),
            ),
          ),
          SelectableText(
            run.reply!.reply,
            style: const TextStyle(fontSize: 14, height: 1.8),
          ),
          for (final (index, result) in run.reply!.toolResults.indexed)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: SessionRun.resultFailed(result)
                  ? ErrorNotice(
                      message:
                          '${result['tool_name'] ?? 'Tool'} failed. Details are in Errors.',
                      onOpenErrors: onOpenErrors,
                    )
                  : _ToolEvidence(
                      result,
                      storageKey: PageStorageKey(
                        'tool-result-$runIndex-$index',
                      ),
                    ),
            ),
        ],
        if (run.finished != null && !run.restored)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(
              'Response time ${(run.finished!.difference(run.started).inMilliseconds / 1000).toStringAsFixed(1)}s',
              style: metadataStyle.copyWith(fontSize: 10),
            ),
          ),
        const SizedBox(height: 22),
        const Divider(),
      ],
    ),
  );
}

class _ToolEvidence extends StatelessWidget {
  const _ToolEvidence(this.result, {required this.storageKey});
  final Map<String, dynamic> result;
  final PageStorageKey<String> storageKey;
  @override
  Widget build(BuildContext context) {
    return ConsolePanel(
      padding: EdgeInsets.zero,
      child: ExpansionTile(
        // Do not share the conversation's double scroll offset with a bool.
        key: storageKey,
        shape: const Border(),
        collapsedShape: const Border(),
        leading: Icon(Icons.terminal, size: 18, color: ConsoleColors.accent),
        title: Text(
          result['tool_name']?.toString() ?? 'Tool result',
          style: metadataStyle,
        ),
        subtitle: Text(
          result['status']?.toString() ?? 'Returned by Core',
          style: const TextStyle(fontSize: 11, color: ConsoleColors.muted),
        ),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: SelectableText(
              key: PageStorageKey('${storageKey.value}-text'),
              const JsonEncoder.withIndent('  ').convert(result),
              style: metadataStyle.copyWith(height: 1.7, fontSize: 11),
            ),
          ),
        ],
      ),
    );
  }
}
