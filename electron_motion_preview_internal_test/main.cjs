const { app, BrowserWindow, dialog, ipcMain, session, shell } = require('electron');
const { fileURLToPath, pathToFileURL } = require('node:url');
const path = require('node:path');
const {
  CoreRequestError,
  requestCore,
  streamCoreChat,
} = require('./core-bridge.cjs');
const {
  CoreSupervisor,
  CoreSupervisorError,
} = require('./core-supervisor.cjs');
const {
  DEFAULT_RUNTIME_SETTINGS,
  loadRuntimeSettings,
  normalizeRuntimeSettings,
  saveRuntimeSettings,
} = require('./runtime-settings.cjs');
const {
  UpdateCheckError,
  checkForUpdate,
} = require('./update-checker.cjs');

const verifyMode = process.argv.includes('--verify');
const editionArg = process.argv.find((value) => value.startsWith('--edition='));
const requestedEdition = editionArg ? editionArg.slice('--edition='.length) : 'internal-test';
const selectedEdition = new Set(['development', 'internal-test']).has(requestedEdition)
  ? requestedEdition
  : 'development';
const windowTitle = selectedEdition === 'internal-test'
  ? 'JARVIS · 内测版'
  : 'JARVIS · 开发版';
const rendererPath = path.join(__dirname, 'renderer', 'motion.html');
const rendererUrl = pathToFileURL(rendererPath).href;
const preloadPath = path.join(__dirname, 'preload.cjs');
const backgroundStart = process.argv.includes('--background-start');
const appName = selectedEdition === 'internal-test'
  ? 'JARVIS Electron Internal Test'
  : 'JARVIS Electron Development';
app.setName(appName);
const hasSingleInstanceLock = app.requestSingleInstanceLock();
let coreSupervisor = null;
let mainWindow = null;
let shutdownStarted = false;
let appQuitting = false;
let pendingFocus = false;
let runtimeSettings = { ...DEFAULT_RUNTIME_SETTINGS };
let runtimeSettingsError = null;
let coreReconnectInFlight = null;
let latestUpdateUrl = null;
const activeChatStreams = new Map();

function createCoreSupervisor() {
  if (!app.isPackaged) return new CoreSupervisor();

  const coreExecutable = path.join(process.resourcesPath, 'core', 'jarvis-core.exe');
  return new CoreSupervisor({
    coreExecutable,
    coreWorkingDirectory: path.dirname(coreExecutable),
    logPath: path.join(app.getPath('logs'), 'electron-core-startup.log'),
  });
}

function runtimeSettingsSnapshot() {
  return {
    ...runtimeSettings,
    warning: runtimeSettingsError,
  };
}

function loginItemArguments(settings = runtimeSettings) {
  const args = [`--edition=${selectedEdition}`];
  if (settings.backgroundRunning) args.push('--background-start');
  return args;
}

function syncLoginItemSetting(settings = runtimeSettings) {
  if (typeof app.setLoginItemSettings !== 'function') {
    throw new Error('This Electron runtime does not expose Windows login-item settings.');
  }
  app.setLoginItemSettings({
    openAtLogin: settings.startOnLogin,
    args: loginItemArguments(settings),
  });
}

function initializeRuntimeSettings() {
  const loaded = loadRuntimeSettings(app, selectedEdition);
  runtimeSettings = loaded.settings;
  runtimeSettingsError = loaded.error;
  try {
    syncLoginItemSetting(runtimeSettings);
  } catch (error) {
    runtimeSettingsError = [runtimeSettingsError, `Login item could not be synchronized: ${error.message || String(error)}`]
      .filter(Boolean)
      .join(' ');
  }
}

function updateRuntimeSettings(payload) {
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new Error('Runtime settings must be an object.');
  }
  const unknownKeys = Object.keys(payload).filter((key) => !Object.hasOwn(DEFAULT_RUNTIME_SETTINGS, key));
  if (unknownKeys.length) {
    throw new Error(`Unknown runtime setting: ${unknownKeys[0]}.`);
  }
  const next = normalizeRuntimeSettings({
    ...runtimeSettings,
    ...payload,
  });
  const loginItemChanged = next.startOnLogin !== runtimeSettings.startOnLogin
    || (next.startOnLogin && next.backgroundRunning !== runtimeSettings.backgroundRunning);
  if (loginItemChanged) {
    try {
      syncLoginItemSetting(next);
    } catch (error) {
      throw new Error(`Login item could not be updated: ${error.message || String(error)}`);
    }
  }
  try {
    runtimeSettings = saveRuntimeSettings(app, selectedEdition, next);
    runtimeSettingsError = null;
  } catch (error) {
    if (loginItemChanged) {
      try {
        syncLoginItemSetting(runtimeSettings);
      } catch {
        // Preserve the original write failure; the UI will keep the setting
        // visibly unavailable instead of silently changing its meaning.
      }
    }
    throw new Error(`Runtime settings could not be saved: ${error.message || String(error)}`);
  }
  return runtimeSettingsSnapshot();
}

function handleRuntimeSettingsUpdate(payload) {
  try {
    return { ok: true, data: updateRuntimeSettings(payload) };
  } catch (error) {
    return {
      ok: false,
      error: {
        code: 'RUNTIME_SETTINGS_FAILED',
        message: error.message || String(error),
      },
    };
  }
}

function unavailableUpdateResult(detail) {
  return {
    status: 'unavailable',
    channel: 'internal-test',
    currentVersion: app.getVersion(),
    detail,
  };
}

async function handleUpdateCheck() {
  latestUpdateUrl = null;
  if (selectedEdition !== 'internal-test') {
    return { ok: true, data: unavailableUpdateResult('Update checks are only available for the Internal Test edition.') };
  }
  if (!app.isPackaged) {
    return { ok: true, data: unavailableUpdateResult('Update checks are available in a packaged Internal Test build.') };
  }
  try {
    const result = await checkForUpdate({ currentVersion: app.getVersion() });
    if (result.status === 'update_available') latestUpdateUrl = result.releaseUrl;
    return { ok: true, data: result };
  } catch (error) {
    return {
      ok: false,
      error: {
        code: error instanceof UpdateCheckError ? error.code : 'UPDATE_CHECK_FAILED',
        message: error.message || String(error),
      },
    };
  }
}

async function handleUpdateOpen() {
  if (!latestUpdateUrl) {
    return {
      ok: false,
      error: {
        code: 'UPDATE_NOT_READY',
        message: 'Check for an available update before opening the Release page.',
      },
    };
  }
  try {
    await shell.openExternal(latestUpdateUrl);
    return { ok: true, data: { opened: true } };
  } catch (error) {
    return {
      ok: false,
      error: {
        code: 'UPDATE_OPEN_FAILED',
        message: `The Release page could not be opened: ${error.message || String(error)}`,
      },
    };
  }
}

function focusMainWindow() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    pendingFocus = true;
    return;
  }
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.show();
  mainWindow.focus();
}

if (hasSingleInstanceLock) {
  app.on('second-instance', focusMainWindow);
} else {
  app.quit();
}

function isTrustedRendererUrl(candidate) {
  try {
    return fileURLToPath(new URL(candidate)) === rendererPath;
  } catch {
    return false;
  }
}

function configureContents(contents) {
  contents.setWindowOpenHandler(() => ({ action: 'deny' }));
  contents.on('will-attach-webview', (event) => event.preventDefault());
  contents.on('will-frame-navigate', (event) => event.preventDefault());
  contents.on('will-navigate', (event, details) => {
    const candidate = typeof details === 'string' ? details : details.url;
    if (!isTrustedRendererUrl(candidate)) event.preventDefault();
  });
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    show: false,
    backgroundColor: '#050505',
    title: windowTitle,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      preload: preloadPath,
      webSecurity: true,
      allowRunningInsecureContent: false,
      webviewTag: false,
      backgroundThrottling: true,
      spellcheck: false,
    },
  });

  configureContents(window.webContents);
  window.webContents.on('page-title-updated', (event) => {
    event.preventDefault();
    window.setTitle(windowTitle);
  });
  window.once('ready-to-show', () => {
    if (!verifyMode && !(backgroundStart && runtimeSettings.backgroundRunning)) window.show();
    if (pendingFocus) {
      pendingFocus = false;
      focusMainWindow();
    }
  });
  window.on('close', (event) => {
    if (runtimeSettings.backgroundRunning && !appQuitting) {
      event.preventDefault();
      window.hide();
    }
  });
  return window;
}

async function handleCoreRequest(operation, payload) {
  try {
    return { ok: true, data: await requestCore(operation, payload) };
  } catch (error) {
    const failure = error instanceof CoreRequestError
      ? error
      : new CoreRequestError('CORE_REQUEST_FAILED', String(error));
    return {
      ok: false,
      error: {
        code: failure.code,
        message: failure.message,
        status: failure.status,
      },
    };
  }
}

function streamError(error) {
  const failure = error instanceof CoreRequestError
    ? error
    : new CoreRequestError('CORE_REQUEST_FAILED', String(error));
  return {
    code: failure.code,
    message: failure.message,
    status: failure.status,
  };
}

function sendChatStreamEvent(sender, streamId, event) {
  if (!sender || sender.isDestroyed()) return;
  sender.send('jarvis-core-chat-stream-event', { streamId, event });
}

function cancelActiveChatStreams() {
  for (const entry of activeChatStreams.values()) entry.controller?.cancel();
  activeChatStreams.clear();
}

function startChatStream(event, payload) {
  const streamId = typeof payload?.streamId === 'string' ? payload.streamId.trim() : '';
  if (!/^chat-[A-Za-z0-9_-]{1,80}$/.test(streamId)) {
    return { ok: false, error: streamError(new CoreRequestError('INVALID_REQUEST', 'The JARVIS stream ID is invalid.')) };
  }
  activeChatStreams.get(streamId)?.controller?.cancel();
  activeChatStreams.delete(streamId);
  const entry = { controller: null, sender: event.sender };
  activeChatStreams.set(streamId, entry);
  const finish = () => {
    if (activeChatStreams.get(streamId) === entry) activeChatStreams.delete(streamId);
  };
  try {
    entry.controller = streamCoreChat(
      {
        message: payload?.message,
        conversationId: payload?.conversationId,
        outputLanguage: payload?.outputLanguage,
      },
      {
        onEvent: (streamEvent) => sendChatStreamEvent(event.sender, streamId, streamEvent),
        onEnd: () => {
          sendChatStreamEvent(event.sender, streamId, { type: 'end' });
          finish();
        },
        onError: (error) => {
          sendChatStreamEvent(event.sender, streamId, { type: 'error', error: streamError(error) });
          sendChatStreamEvent(event.sender, streamId, { type: 'end' });
          finish();
        },
      },
    );
  } catch (error) {
    finish();
    return { ok: false, error: streamError(error) };
  }
  return { ok: true, data: { streamId } };
}

function cancelChatStream(payload) {
  const streamId = typeof payload?.streamId === 'string' ? payload.streamId.trim() : '';
  if (!/^chat-[A-Za-z0-9_-]{1,80}$/.test(streamId)) {
    return { ok: false, error: streamError(new CoreRequestError('INVALID_REQUEST', 'The JARVIS stream ID is invalid.')) };
  }
  const entry = activeChatStreams.get(streamId);
  if (entry) {
    entry.controller?.cancel();
    activeChatStreams.delete(streamId);
  }
  return { ok: true, data: { streamId, cancelled: Boolean(entry) } };
}

function reconnectCore() {
  if (!coreSupervisor) {
    return Promise.reject(new CoreSupervisorError(
      'CORE_NOT_INITIALIZED',
      'JARVIS Core supervisor is not initialized in this window.',
    ));
  }
  if (coreReconnectInFlight) return coreReconnectInFlight;
  const reconnect = coreSupervisor.ensureReady()
    .then((result) => result.health)
    .finally(() => {
      if (coreReconnectInFlight === reconnect) coreReconnectInFlight = null;
    });
  coreReconnectInFlight = reconnect;
  return reconnect;
}

async function handleCoreReconnect() {
  try {
    return { ok: true, data: await reconnectCore() };
  } catch (error) {
    return {
      ok: false,
      error: {
        code: error?.code || 'CORE_RECONNECT_FAILED',
        message: error?.message || String(error),
        status: error?.status || null,
      },
    };
  }
}

function registerCoreIpc() {
  ipcMain.handle('jarvis-core-health', () => handleCoreRequest('health'));
  ipcMain.handle('jarvis-core-reconnect', () => handleCoreReconnect());
  ipcMain.handle('jarvis-core-telemetry', () => handleCoreRequest('telemetry'));
  ipcMain.handle('jarvis-core-conversation-history', () => handleCoreRequest('conversationHistory'));
  ipcMain.handle('jarvis-core-conversation-list', () => handleCoreRequest('conversationList'));
  ipcMain.handle('jarvis-core-conversation-open', (_event, payload) => handleCoreRequest('conversationOpen', payload));
  ipcMain.handle('jarvis-core-create-conversation', () => handleCoreRequest('createConversation'));
  ipcMain.handle('jarvis-core-send-message', (_event, payload) => handleCoreRequest('sendMessage', payload));
  ipcMain.handle('jarvis-core-chat-stream-start', (event, payload) => startChatStream(event, payload));
  ipcMain.handle('jarvis-core-chat-stream-cancel', (_event, payload) => cancelChatStream(payload));
  ipcMain.handle('jarvis-core-system-info', () => handleCoreRequest('systemInfo'));
  ipcMain.handle('jarvis-core-system-status', () => handleCoreRequest('systemStatus'));
  ipcMain.handle('jarvis-core-projects', () => handleCoreRequest('projects'));
  ipcMain.handle('jarvis-core-project-git-status', (_event, payload) => handleCoreRequest('projectGitStatus', payload));
  ipcMain.handle('jarvis-core-project-list-files', (_event, payload) => handleCoreRequest('projectListFiles', payload));
  ipcMain.handle('jarvis-core-project-read-file', (_event, payload) => handleCoreRequest('projectReadFile', payload));
  ipcMain.handle('jarvis-core-project-search', (_event, payload) => handleCoreRequest('projectSearch', payload));
  ipcMain.handle('jarvis-core-project-refresh', () => handleCoreRequest('projectRefresh'));
  ipcMain.handle('jarvis-core-obsidian-vaults', () => handleCoreRequest('obsidianVaults'));
  ipcMain.handle('jarvis-core-obsidian-connect', (_, payload) => handleCoreRequest('obsidianConnect', payload));
  ipcMain.handle('jarvis-core-obsidian-disconnect', (_, payload) => handleCoreRequest('obsidianDisconnect', payload));
  ipcMain.handle('jarvis-core-tasks', () => handleCoreRequest('tasks'));
  ipcMain.handle('jarvis-core-ai-mode', (_event, payload) => handleCoreRequest('aiMode', payload));
  ipcMain.handle('jarvis-core-ai-check', () => handleCoreRequest('aiCheck'));
  ipcMain.handle('jarvis-core-ai-usage', () => handleCoreRequest('aiUsage'));
  ipcMain.handle('jarvis-core-ai-disconnect', () => handleCoreRequest('aiDisconnect'));
  ipcMain.handle('jarvis-core-ai-direct-config', (_, payload) => handleCoreRequest('aiDirectConfig', payload));
  ipcMain.handle('jarvis-core-speak-reply', (_event, payload) => handleCoreRequest('speakReply', payload));
  ipcMain.handle('jarvis-core-synthesize-speech', (_event, payload) => handleCoreRequest('synthesizeSpeech', payload));
  ipcMain.handle('jarvis-core-speech-settings', () => handleCoreRequest('speechSettings'));
  ipcMain.handle('jarvis-core-speech-voices', () => handleCoreRequest('speechVoices'));
  ipcMain.handle('jarvis-core-stop-speech', () => handleCoreRequest('stopSpeech'));
  ipcMain.handle('jarvis-runtime-settings-get', () => ({ ok: true, data: runtimeSettingsSnapshot() }));
  ipcMain.handle('jarvis-runtime-settings-set', (_event, payload) => handleRuntimeSettingsUpdate(payload));
  ipcMain.handle('jarvis-update-check', () => handleUpdateCheck());
  ipcMain.handle('jarvis-update-open', () => handleUpdateOpen());
}

app.on('child-process-gone', (_event, details) => {
  if (details.type === 'GPU') {
    console.error(`[electron-preview] GPU child exited: ${JSON.stringify(details)}`);
  }
});

function formatStartupFailure(error) {
  const code = error?.code ? ` [${error.code}]` : '';
  const detail = error?.message || String(error);
  const logPath = coreSupervisor?.logPath;
  return `JARVIS Core startup failed${code}: ${detail}${logPath ? `\n\nStartup log:\n${logPath}` : ''}`;
}

async function stopOwnedCoreBeforeExit() {
  cancelActiveChatStreams();
  if (!coreSupervisor || !coreSupervisor.hasOwnedProcess()) return;
  await coreSupervisor.stopOwned();
}

async function verify(window) {
  const snapshot = await window.webContents.executeJavaScript(`
    new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => {
      const byId = (id) => document.getElementById(id);
      const core = byId('core');
      const pause = byId('pause');
      const reduced = byId('reduced');
      const runtime = byId('runtime-state');
      const corePage = document.querySelector('[data-page="core"]');
      const coreView = byId('view-core');
      const tasks = document.querySelector('[data-page="tasks"]');
      const memory = document.querySelector('[data-page="memory"]');
      const knowledge = document.querySelector('[data-page="knowledge"]');
      const theme = document.querySelector('[data-page="theme"]');
      const memoryView = byId('view-memory');
      const knowledgeView = byId('view-knowledge');
      const events = document.querySelector('[data-page="events"]');
      const errors = document.querySelector('[data-page="errors"]');
      const eventsView = byId('view-events');
      const errorsView = byId('view-errors');
      const chatWindow = document.querySelector('.chat-pane');
      const dockWindow = document.querySelector('.dock-zone');
      const internalTestEdition = new URLSearchParams(location.search).get('edition') === 'internal-test';
      if (internalTestEdition) corePage.click();
      else tasks.click();
      const tasksVisible = internalTestEdition || byId('view-tasks').classList.contains('active');
      const inspectorOpen = byId('inspect-panel').classList.contains('open');
      const inspectorVisible = !byId('inspect-panel').hidden;
      const chatAndCoreRemainVisible = byId('view-assistant').classList.contains('active')
        && core.getBoundingClientRect().width > 0
        && core.getBoundingClientRect().height > 0;
      corePage.click();
      const coreVisible = coreView.classList.contains('active')
        && Boolean(byId('core-refresh'))
        && Boolean(byId('core-reconnect'))
        && Boolean(byId('core-connection-checked'))
        && Boolean(byId('core-connection-status'));
      memory.click();
      const memoryVisible = memoryView.classList.contains('active')
        && Boolean(memoryView.querySelector('#history-list'))
        && !memoryView.querySelector('#vault-list');
      knowledge.click();
      const knowledgeVisible = knowledgeView.classList.contains('active')
        && Boolean(knowledgeView.querySelector('#vault-list'))
        && !knowledgeView.querySelector('#history-list');
      events.click();
      const eventsVisible = eventsView.classList.contains('active')
        && Boolean(eventsView.querySelector('#event-list'))
        && !eventsView.querySelector('#error-list');
      errors.click();
      const errorsVisible = errorsView.classList.contains('active')
        && Boolean(errorsView.querySelector('#error-list'))
        && !errorsView.querySelector('#event-list');
      theme.click();
      const themeVisible = byId('view-theme').classList.contains('active')
        && byId('theme-setting').options.length === 4;
      document.querySelector('[data-page="assistant"]').click();
      const inspectorClosed = byId('inspect-panel').hidden
        && byId('inspect-panel').getAttribute('aria-hidden') === 'true';
      const floatingWindows = getComputedStyle(chatWindow).position === 'absolute'
        && getComputedStyle(dockWindow).position === 'absolute'
        && getComputedStyle(byId('inspect-panel')).position === 'absolute';
      pause.click();
      const paused = runtime.textContent === 'Paused';
      pause.click();
      reduced.checked = true;
      reduced.dispatchEvent(new Event('change', { bubbles: true }));
      const reducedMotion = runtime.textContent === 'Low motion';
      reduced.checked = false;
      reduced.dispatchEvent(new Event('change', { bubbles: true }));
      resolve({
        title: document.title,
        hasWebGLConstructor: typeof window.HolographicCore === 'function',
        webglActive: byId('quality').textContent !== '2D fallback',
        canvasSize: [core.width, core.height],
        coreVisible,
        tasksVisible,
        memoryVisible,
        knowledgeVisible,
        eventsVisible,
        errorsVisible,
        themeVisible,
        inspectorOpen,
        inspectorVisible,
        chatAndCoreRemainVisible,
        inspectorClosed,
        floatingWindows,
        paused,
        reducedMotion,
        rendererNodeProcess: typeof window.process,
        rendererRequire: typeof window.require,
      });
    })))
  `);

  if (!snapshot.hasWebGLConstructor || !snapshot.webglActive) {
    throw new Error('WebGL core did not initialize.');
  }
  if (snapshot.canvasSize.some((value) => value <= 0)) {
    throw new Error('WebGL canvas did not receive a drawable size.');
  }
  if (!snapshot.coreVisible || !snapshot.tasksVisible || !snapshot.memoryVisible || !snapshot.knowledgeVisible
    || !snapshot.eventsVisible || !snapshot.errorsVisible || !snapshot.themeVisible
    || !snapshot.inspectorOpen || !snapshot.inspectorVisible
    || !snapshot.chatAndCoreRemainVisible
    || !snapshot.inspectorClosed || !snapshot.floatingWindows
    || !snapshot.paused || !snapshot.reducedMotion) {
    throw new Error('Navigation or motion controls did not retain their expected behavior.');
  }
  if (snapshot.rendererNodeProcess !== 'undefined' || snapshot.rendererRequire !== 'undefined') {
    throw new Error('Renderer unexpectedly exposes Node.js primitives.');
  }
  return snapshot;
}

app.whenReady().then(async () => {
  if (!hasSingleInstanceLock) return;
  registerCoreIpc();
  initializeRuntimeSettings();
  session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  session.defaultSession.setPermissionCheckHandler(() => false);

  try {
    coreSupervisor = createCoreSupervisor();
    // `--verify` is a renderer/WebGL check and must remain runnable without a
    // Core process. Normal preview launches require a real Core health result
    // before the window is shown.
    if (!verifyMode) await coreSupervisor.ensureReady();
    mainWindow = createWindow();
    await mainWindow.loadURL(`${rendererUrl}?edition=${encodeURIComponent(selectedEdition)}`);
    if (verifyMode) {
      const startedAt = performance.now();
      const snapshot = await verify(mainWindow);
      console.log(JSON.stringify({ verification: 'passed', startupMs: Math.round(performance.now() - startedAt), snapshot }));
      mainWindow.destroy();
      app.quit();
    }
  } catch (error) {
    console.error(`[electron-preview] startup/renderer failure: ${error.stack || error}`);
    app.exitCode = 1;
    await stopOwnedCoreBeforeExit();
    if (!verifyMode && app.isReady()) {
      const message = error instanceof CoreSupervisorError
        ? formatStartupFailure(error)
        : `JARVIS preview failed to load or verify: ${error.message || error}`;
      dialog.showErrorBox('JARVIS could not start', message);
    }
    app.exit(1);
  }
});

app.on('before-quit', (event) => {
  appQuitting = true;
  cancelActiveChatStreams();
  if (shutdownStarted || !coreSupervisor?.hasOwnedProcess()) return;
  event.preventDefault();
  shutdownStarted = true;
  void coreSupervisor.stopOwned().finally(() => app.quit());
});

app.on('window-all-closed', () => {
  if (!runtimeSettings.backgroundRunning) app.quit();
});

app.on('activate', focusMainWindow);
