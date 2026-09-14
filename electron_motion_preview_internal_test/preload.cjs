const { contextBridge, ipcRenderer } = require('electron');

const channels = Object.freeze({
  health: 'jarvis-core-health',
  reconnect: 'jarvis-core-reconnect',
  telemetry: 'jarvis-core-telemetry',
  conversationHistory: 'jarvis-core-conversation-history',
  conversationList: 'jarvis-core-conversation-list',
  conversationOpen: 'jarvis-core-conversation-open',
  createConversation: 'jarvis-core-create-conversation',
  sendMessage: 'jarvis-core-send-message',
  chatStreamStart: 'jarvis-core-chat-stream-start',
  chatStreamCancel: 'jarvis-core-chat-stream-cancel',
  chatStreamEvent: 'jarvis-core-chat-stream-event',
  systemInfo: 'jarvis-core-system-info',
  systemStatus: 'jarvis-core-system-status',
  projects: 'jarvis-core-projects',
  projectGitStatus: 'jarvis-core-project-git-status',
  projectListFiles: 'jarvis-core-project-list-files',
  projectReadFile: 'jarvis-core-project-read-file',
  projectSearch: 'jarvis-core-project-search',
  projectRefresh: 'jarvis-core-project-refresh',
  obsidianVaults: 'jarvis-core-obsidian-vaults',
  obsidianConnect: 'jarvis-core-obsidian-connect',
  obsidianDisconnect: 'jarvis-core-obsidian-disconnect',
  tasks: 'jarvis-core-tasks',
  aiMode: 'jarvis-core-ai-mode',
  aiCheck: 'jarvis-core-ai-check',
  aiUsage: 'jarvis-core-ai-usage',
  aiDisconnect: 'jarvis-core-ai-disconnect',
  aiDirectConfig: 'jarvis-core-ai-direct-config',
  speakReply: 'jarvis-core-speak-reply',
  synthesizeSpeech: 'jarvis-core-synthesize-speech',
  speechSettings: 'jarvis-core-speech-settings',
  speechVoices: 'jarvis-core-speech-voices',
  stopSpeech: 'jarvis-core-stop-speech',
  runtimeSettingsGet: 'jarvis-runtime-settings-get',
  runtimeSettingsSet: 'jarvis-runtime-settings-set',
  updateCheck: 'jarvis-update-check',
  updateOpen: 'jarvis-update-open',
});

async function invoke(channel, payload) {
  const response = await ipcRenderer.invoke(channel, payload);
  if (response && response.ok === false) {
    const failure = new Error(response.error?.message || 'JARVIS Core request failed.');
    failure.code = response.error?.code || 'CORE_REQUEST_FAILED';
    failure.status = response.error?.status || null;
    throw failure;
  }
  return response?.data ?? response;
}

const chatStreamListeners = new Set();
ipcRenderer.on(channels.chatStreamEvent, (_event, payload) => {
  for (const listener of chatStreamListeners) listener(payload);
});

contextBridge.exposeInMainWorld('jarvisCore', Object.freeze({
  health: () => invoke(channels.health),
  reconnect: () => invoke(channels.reconnect),
  telemetry: () => invoke(channels.telemetry),
  conversationHistory: () => invoke(channels.conversationHistory),
  conversationList: () => invoke(channels.conversationList),
  conversationOpen: (conversationId) => invoke(channels.conversationOpen, { conversationId }),
  createConversation: () => invoke(channels.createConversation),
  sendMessage: (message, conversationId, outputLanguage) => invoke(channels.sendMessage, {
    message,
    conversationId,
    outputLanguage,
  }),
  startChatStream: (streamId, message, conversationId, outputLanguage) => invoke(channels.chatStreamStart, {
    streamId,
    message,
    conversationId,
    outputLanguage,
  }),
  cancelChatStream: (streamId) => invoke(channels.chatStreamCancel, { streamId }),
  onChatStream: (listener) => {
    if (typeof listener !== 'function') throw new TypeError('A chat stream listener is required.');
    chatStreamListeners.add(listener);
    return () => chatStreamListeners.delete(listener);
  },
  systemInfo: () => invoke(channels.systemInfo),
  systemStatus: () => invoke(channels.systemStatus),
  projects: () => invoke(channels.projects),
  projectGitStatus: (projectName) => invoke(channels.projectGitStatus, { projectName }),
  projectListFiles: (projectName, relativePath = '.') => invoke(channels.projectListFiles, {
    projectName,
    relativePath,
  }),
  projectReadFile: (projectName, relativePath) => invoke(channels.projectReadFile, {
    projectName,
    relativePath,
  }),
  projectSearch: (projectName, keyword, relativePath = '.') => invoke(channels.projectSearch, {
    projectName,
    keyword,
    relativePath,
  }),
  projectRefresh: () => invoke(channels.projectRefresh),
  obsidianVaults: () => invoke(channels.obsidianVaults),
  obsidianConnect: (config) => invoke(channels.obsidianConnect, config),
  obsidianDisconnect: (vaultId) => invoke(channels.obsidianDisconnect, { vaultId }),
  tasks: () => invoke(channels.tasks),
  aiMode: (mode) => invoke(channels.aiMode, { mode }),
  aiCheck: () => invoke(channels.aiCheck),
  aiUsage: () => invoke(channels.aiUsage),
  aiDisconnect: () => invoke(channels.aiDisconnect),
  aiDirectConfig: (config) => invoke(channels.aiDirectConfig, config),
  speakReply: (text, voice = null) => invoke(channels.speakReply, voice ? { text, voice } : { text }),
  synthesizeSpeech: (text, voice = null) => invoke(channels.synthesizeSpeech, voice ? { text, voice } : { text }),
  speechSettings: () => invoke(channels.speechSettings),
  speechVoices: () => invoke(channels.speechVoices),
  stopSpeech: () => invoke(channels.stopSpeech),
  runtimeSettings: () => invoke(channels.runtimeSettingsGet),
  updateRuntimeSettings: (settings) => invoke(channels.runtimeSettingsSet, settings),
}));

contextBridge.exposeInMainWorld('jarvisUpdate', Object.freeze({
  check: () => invoke(channels.updateCheck),
  open: () => invoke(channels.updateOpen),
}));
