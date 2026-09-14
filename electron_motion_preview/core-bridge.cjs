const http = require('node:http');

const CORE_HOST = '127.0.0.1';
const CORE_PORT = 8765;
const CORE_TIMEOUT_MS = 15000;
const CHAT_TIMEOUT_MS = 65000;
const AI_CHECK_TIMEOUT_MS = 65000;
const CONVERSATION_ID_PATTERN = /^jarvis-[0-9a-f-]{36}$/;
const OUTPUT_LANGUAGES = new Set(['en', 'zh-CN']);

const CORE_OPERATIONS = Object.freeze({
  health: Object.freeze({ method: 'GET', path: '/api/health' }),
  telemetry: Object.freeze({ method: 'GET', path: '/api/telemetry' }),
  conversationHistory: Object.freeze({ method: 'GET', path: '/api/chat/history' }),
  conversationList: Object.freeze({ method: 'GET', path: '/api/chat/conversations' }),
  conversationOpen: Object.freeze({ method: 'POST', path: '/api/chat/history/open' }),
  createConversation: Object.freeze({ method: 'POST', path: '/api/chat/session' }),
  sendMessage: Object.freeze({ method: 'POST', path: '/api/chat', timeoutMs: CHAT_TIMEOUT_MS }),
  systemInfo: Object.freeze({ method: 'GET', path: '/api/system-info' }),
  systemStatus: Object.freeze({ method: 'GET', path: '/api/system-status' }),
  projects: Object.freeze({ method: 'GET', path: '/api/projects' }),
  projectGitStatus: Object.freeze({ method: 'POST', path: '/api/projects/git-status' }),
  projectListFiles: Object.freeze({ method: 'POST', path: '/api/projects/list-files' }),
  projectReadFile: Object.freeze({ method: 'POST', path: '/api/projects/read-file' }),
  projectSearch: Object.freeze({ method: 'POST', path: '/api/projects/search' }),
  projectRefresh: Object.freeze({ method: 'POST', path: '/api/projects/refresh' }),
  obsidianVaults: Object.freeze({ method: 'GET', path: '/api/obsidian/vaults' }),
  obsidianConnect: Object.freeze({ method: 'POST', path: '/api/obsidian/vaults', timeoutMs: CORE_TIMEOUT_MS }),
  obsidianDisconnect: Object.freeze({ method: 'POST', path: '/api/obsidian/disconnect', timeoutMs: 15000 }),
  tasks: Object.freeze({ method: 'GET', path: '/api/tasks' }),
  aiMode: Object.freeze({ method: 'POST', path: '/api/settings/ai/mode' }),
  aiCheck: Object.freeze({ method: 'POST', path: '/api/settings/ai/check', timeoutMs: AI_CHECK_TIMEOUT_MS }),
  aiUsage: Object.freeze({ method: 'GET', path: '/api/settings/ai/usage', timeoutMs: AI_CHECK_TIMEOUT_MS }),
  aiDisconnect: Object.freeze({ method: 'POST', path: '/api/settings/ai/disconnect', timeoutMs: AI_CHECK_TIMEOUT_MS }),
  aiDirectConfig: Object.freeze({ method: 'POST', path: '/api/settings/ai/direct-config', timeoutMs: CORE_TIMEOUT_MS }),
});

const CHAT_STREAM_OPERATION = Object.freeze({
  method: 'POST',
  path: '/api/chat/stream',
  timeoutMs: CHAT_TIMEOUT_MS,
});

const SPEECH_OPERATIONS = Object.freeze({
  speakReply: Object.freeze({ method: 'POST', path: '/api/system-speech' }),
  synthesizeSpeech: Object.freeze({ method: 'POST', path: '/api/system-speech/synthesize', timeoutMs: CHAT_TIMEOUT_MS }),
  speechSettings: Object.freeze({ method: 'GET', path: '/api/system-speech/settings' }),
  speechVoices: Object.freeze({ method: 'GET', path: '/api/system-speech/voices' }),
  stopSpeech: Object.freeze({ method: 'POST', path: '/api/system-speech/stop' }),
});

class CoreRequestError extends Error {
  constructor(code, message, status = null) {
    super(message);
    this.name = 'CoreRequestError';
    this.code = code;
    this.status = status;
  }
}

function validateChatPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    throw new CoreRequestError('INVALID_REQUEST', 'A JARVIS chat request is required.');
  }
  const message = typeof payload.message === 'string' ? payload.message.trim() : '';
  if (!message || message.length > 12000) {
    throw new CoreRequestError('INVALID_REQUEST', 'The JARVIS message must contain 1–12000 characters.');
  }
  const conversationId = payload.conversationId;
  if (
    typeof conversationId !== 'string'
    || !CONVERSATION_ID_PATTERN.test(conversationId)
  ) {
    throw new CoreRequestError('INVALID_REQUEST', 'The JARVIS conversation ID is invalid.');
  }
  const outputLanguage = payload.outputLanguage === undefined ? 'en' : payload.outputLanguage;
  if (typeof outputLanguage !== 'string' || !OUTPUT_LANGUAGES.has(outputLanguage)) {
    throw new CoreRequestError('INVALID_REQUEST', 'The JARVIS output language is invalid.');
  }
  return { message, conversation_id: conversationId, output_language: outputLanguage };
}

function validateConversationOpenPayload(payload) {
  const conversationId = typeof payload?.conversationId === 'string'
    ? payload.conversationId.trim()
    : '';
  if (!CONVERSATION_ID_PATTERN.test(conversationId)) {
    throw new CoreRequestError('INVALID_REQUEST', 'The JARVIS conversation ID is invalid.');
  }
  return { conversation_id: conversationId };
}

function validateSpeechPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    throw new CoreRequestError('INVALID_REQUEST', 'A JARVIS speech request is required.');
  }
  const text = typeof payload.text === 'string' ? payload.text.trim() : '';
  if (!text || text.length > 12000) {
    throw new CoreRequestError('INVALID_REQUEST', 'The JARVIS speech text must contain 1–12000 characters.');
  }
  const voice = typeof payload.voice === 'string' ? payload.voice.trim() : '';
  if (voice.length > 500 || /[\u0000-\u001F\u007F]/.test(voice)) {
    throw new CoreRequestError('INVALID_REQUEST', 'The Windows voice ID is invalid.');
  }
  return voice ? { text, voice } : { text };
}

function validateProjectPayload(payload, { keyword = false, file = false } = {}) {
  if (!payload || typeof payload !== 'object') {
    throw new CoreRequestError('INVALID_REQUEST', 'A registered JARVIS project is required.');
  }
  const projectName = typeof payload.projectName === 'string' ? payload.projectName.trim() : '';
  if (!projectName || projectName.length > 200) {
    throw new CoreRequestError('INVALID_REQUEST', 'The project name must contain 1–200 characters.');
  }
  const relativePath = typeof payload.relativePath === 'string' && payload.relativePath.trim()
    ? payload.relativePath.trim()
    : '.';
  if (relativePath.length > 500) {
    throw new CoreRequestError('INVALID_REQUEST', 'The project-relative path is too long.');
  }
  if (file && relativePath === '.') {
    throw new CoreRequestError('INVALID_REQUEST', 'A project-relative file path is required.');
  }
  if (keyword) {
    const normalizedKeyword = typeof payload.keyword === 'string' ? payload.keyword.trim() : '';
    if (!normalizedKeyword || normalizedKeyword.length > 500) {
      throw new CoreRequestError('INVALID_REQUEST', 'A search keyword must contain 1–500 characters.');
    }
    return {
      project_name: projectName,
      relative_path: relativePath,
      keyword: normalizedKeyword,
    };
  }
  return {
    project_name: projectName,
    relative_path: relativePath,
  };
}

function validateAiModePayload(payload) {
  if (!payload || typeof payload !== 'object') {
    throw new CoreRequestError('INVALID_REQUEST', 'An AI connection mode is required.');
  }
  const mode = typeof payload.mode === 'string' ? payload.mode.trim() : '';
  if (!['managed_subscription', 'direct_api'].includes(mode)) {
    throw new CoreRequestError('INVALID_REQUEST', 'The requested AI connection mode is not supported.');
  }
  return { mode };
}

function validateDirectConfigPayload(payload) {
  const apiKey = typeof payload?.apiKey === 'string' ? payload.apiKey.trim() : '';
  const provider = typeof payload?.provider === 'string' ? payload.provider.trim() : '';
  const model = typeof payload?.model === 'string' ? payload.model.trim() : '';
  const baseUrl = typeof payload?.baseUrl === 'string' ? payload.baseUrl.trim() : '';
  if (!apiKey || apiKey.length > 500) {
    throw new CoreRequestError('INVALID_REQUEST', 'A valid Direct API key is required.');
  }
  if (!['openai', 'gemini', 'deepseek', 'openai_compatible'].includes(provider)) {
    throw new CoreRequestError('INVALID_REQUEST', 'The Direct API provider is not supported.');
  }
  if (!/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$/.test(model)) {
    throw new CoreRequestError('INVALID_REQUEST', 'The Direct API model ID is invalid.');
  }
  if (baseUrl.length > 250) {
    throw new CoreRequestError('INVALID_REQUEST', 'The gateway base URL is too long.');
  }
  return {
    api_key: apiKey,
    provider,
    model,
    base_url: baseUrl || null,
  };
}

function validateObsidianConnectPayload(payload) {
  if (!payload || typeof payload !== 'object') {
    throw new CoreRequestError('INVALID_REQUEST', 'Obsidian vault connection details are required.');
  }
  const vaultId = typeof payload.vaultId === 'string' ? payload.vaultId.trim() : '';
  const name = typeof payload.name === 'string' ? payload.name.trim() : '';
  const vaultPath = typeof payload.path === 'string' ? payload.path.trim() : '';
  const defaultAccess = typeof payload.defaultAccess === 'string' ? payload.defaultAccess.trim() : 'excluded';
  if (!vaultId || !/^[A-Za-z0-9_-]{1,80}$/.test(vaultId)) {
    throw new CoreRequestError('INVALID_REQUEST', 'A valid Obsidian vault ID is required.');
  }
  if (!name || name.length > 200) {
    throw new CoreRequestError('INVALID_REQUEST', 'The Obsidian vault name must contain 1–200 characters.');
  }
  if (!vaultPath || vaultPath.length > 1000) {
    throw new CoreRequestError('INVALID_REQUEST', 'The Obsidian vault path must contain 1–1000 characters.');
  }
  if (!['rag', 'local-only', 'excluded'].includes(defaultAccess)) {
    throw new CoreRequestError('INVALID_REQUEST', 'The Obsidian vault access mode is not supported.');
  }
  return {
    vault_id: vaultId,
    name,
    path: vaultPath,
    default_access: defaultAccess,
  };
}

function validateOperationPayload(operation, payload) {
  if (operation === 'sendMessage') return validateChatPayload(payload);
  if (operation === 'conversationOpen') return validateConversationOpenPayload(payload);
  if (operation === 'speakReply') return validateSpeechPayload(payload);
  if (operation === 'synthesizeSpeech') return validateSpeechPayload(payload);
  if (operation === 'projectGitStatus') return validateProjectPayload(payload);
  if (operation === 'projectListFiles') return validateProjectPayload(payload);
  if (operation === 'projectReadFile') return validateProjectPayload(payload, { file: true });
  if (operation === 'projectSearch') return validateProjectPayload(payload, { keyword: true });
  if (operation === 'aiMode') return validateAiModePayload(payload);
  if (operation === 'aiDirectConfig') return validateDirectConfigPayload(payload);
  if (operation === 'obsidianConnect') return validateObsidianConnectPayload(payload);
  if (operation === 'obsidianDisconnect') {
    const vaultId = typeof payload?.vaultId === 'string' ? payload.vaultId.trim() : '';
    if (!vaultId || !/^[A-Za-z0-9_-]{1,80}$/.test(vaultId)) {
      throw new CoreRequestError('INVALID_REQUEST', 'A valid Obsidian vault ID is required.');
    }
    return { vault_id: vaultId };
  }
  if (
    operation === 'health'
    || operation === 'telemetry'
    || operation === 'conversationHistory'
    || operation === 'conversationList'
    || operation === 'createConversation'
    || operation === 'systemInfo'
    || operation === 'systemStatus'
    || operation === 'projects'
    || operation === 'projectRefresh'
    || operation === 'obsidianVaults'
    || operation === 'tasks'
    || operation === 'aiCheck'
    || operation === 'aiUsage'
    || operation === 'aiDisconnect'
    || operation === 'aiDirectConfig'
    || operation === 'speechSettings'
    || operation === 'speechVoices'
    || operation === 'stopSpeech'
  ) return null;
  throw new CoreRequestError('INVALID_OPERATION', 'The requested Core operation is not allowlisted.');
}

function parseResponseBody(statusCode, body) {
  let decoded;
  try {
    decoded = body ? JSON.parse(body) : {};
  } catch {
    throw new CoreRequestError(
      'CORE_INVALID_RESPONSE',
      'JARVIS Core returned invalid JSON.',
      statusCode,
    );
  }
  if (statusCode < 200 || statusCode >= 300) {
    const detail = typeof decoded.detail === 'string' && decoded.detail.trim()
      ? decoded.detail.trim()
      : `JARVIS Core returned HTTP ${statusCode}.`;
    throw new CoreRequestError('CORE_HTTP_ERROR', detail, statusCode);
  }
  if (!decoded || typeof decoded !== 'object' || Array.isArray(decoded)) {
    throw new CoreRequestError('CORE_INVALID_RESPONSE', 'JARVIS Core returned an invalid response.', statusCode);
  }
  return decoded;
}

function requestCore(operation, payload) {
  const endpoint = CORE_OPERATIONS[operation] || SPEECH_OPERATIONS[operation];
  if (!endpoint) {
    return Promise.reject(
      new CoreRequestError('INVALID_OPERATION', 'The requested Core operation is not allowlisted.'),
    );
  }

  let body = null;
  try {
    body = validateOperationPayload(operation, payload);
  } catch (error) {
    return Promise.reject(error);
  }

  return new Promise((resolve, reject) => {
    const request = http.request(
      {
        host: CORE_HOST,
        port: CORE_PORT,
        path: endpoint.path,
        method: endpoint.method,
        headers: body
          ? {
              'Content-Type': 'application/json',
              Accept: 'application/json',
            }
          : { Accept: 'application/json' },
      },
      (response) => {
        const chunks = [];
        response.setEncoding('utf8');
        response.on('data', (chunk) => chunks.push(chunk));
        response.on('end', () => {
          try {
            resolve(parseResponseBody(response.statusCode || 0, chunks.join('')));
          } catch (error) {
            reject(error);
          }
        });
      },
    );

    request.setTimeout(endpoint.timeoutMs || CORE_TIMEOUT_MS, () => {
      request.destroy();
      reject(new CoreRequestError('CORE_TIMEOUT', 'JARVIS Core did not respond before the timeout.'));
    });
    request.on('error', (error) => {
      if (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET' || error.code === 'EPIPE') {
        reject(new CoreRequestError('CORE_OFFLINE', 'JARVIS Core is offline. Start the existing Core shortcut.'));
        return;
      }
      reject(new CoreRequestError('CORE_NETWORK_ERROR', `JARVIS Core request failed: ${error.message}`));
    });
    if (body) request.write(JSON.stringify(body));
    request.end();
  });
}

function streamCoreChat(payload, { onEvent, onEnd, onError } = {}) {
  const body = validateChatPayload(payload);
  const endpoint = CHAT_STREAM_OPERATION;
  let cancelled = false;
  let settled = false;
  let buffer = '';

  const fail = (error) => {
    if (settled || cancelled) return;
    settled = true;
    if (typeof onError === 'function') onError(error);
  };

  const request = http.request(
    {
      host: CORE_HOST,
      port: CORE_PORT,
      path: endpoint.path,
      method: endpoint.method,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/x-ndjson',
      },
    },
    (response) => {
      response.setEncoding('utf8');
      response.on('data', (chunk) => {
        buffer += chunk;
        if (response.statusCode < 200 || response.statusCode >= 300) return;
        let newlineIndex = buffer.indexOf('\n');
        while (newlineIndex >= 0) {
          const line = buffer.slice(0, newlineIndex).trim();
          buffer = buffer.slice(newlineIndex + 1);
          newlineIndex = buffer.indexOf('\n');
          if (!line) continue;
          try {
            const event = JSON.parse(line);
            if (!event || typeof event !== 'object' || Array.isArray(event)) {
              throw new CoreRequestError('CORE_INVALID_RESPONSE', 'JARVIS Core returned an invalid stream event.');
            }
            if (typeof onEvent === 'function') onEvent(event);
          } catch (error) {
            request.destroy();
            fail(error instanceof CoreRequestError
              ? error
              : new CoreRequestError('CORE_INVALID_RESPONSE', 'JARVIS Core returned invalid stream JSON.'));
            return;
          }
        }
      });
      response.on('end', () => {
        if (settled || cancelled) return;
        if (response.statusCode < 200 || response.statusCode >= 300) {
          try {
            parseResponseBody(response.statusCode || 0, buffer);
          } catch (error) {
            fail(error);
          }
          return;
        }
        const tail = buffer.trim();
        if (tail) {
          try {
            const event = JSON.parse(tail);
            if (!event || typeof event !== 'object' || Array.isArray(event)) {
              throw new CoreRequestError('CORE_INVALID_RESPONSE', 'JARVIS Core returned an invalid stream event.');
            }
            if (typeof onEvent === 'function') onEvent(event);
          } catch (error) {
            fail(error instanceof CoreRequestError
              ? error
              : new CoreRequestError('CORE_INVALID_RESPONSE', 'JARVIS Core returned invalid stream JSON.'));
            return;
          }
        }
        settled = true;
        if (typeof onEnd === 'function') onEnd();
      });
    },
  );

  request.setTimeout(endpoint.timeoutMs, () => {
    request.destroy();
    fail(new CoreRequestError('CORE_TIMEOUT', 'JARVIS Core did not respond before the timeout.'));
  });
  request.on('error', (error) => {
    if (cancelled) return;
    if (error.code === 'ECONNREFUSED' || error.code === 'ECONNRESET' || error.code === 'EPIPE') {
      fail(new CoreRequestError('CORE_OFFLINE', 'JARVIS Core is offline. Start the existing Core shortcut.'));
      return;
    }
    fail(new CoreRequestError('CORE_NETWORK_ERROR', `JARVIS Core stream failed: ${error.message}`));
  });
  request.write(JSON.stringify(body));
  request.end();

  return Object.freeze({
    cancel() {
      if (settled || cancelled) return;
      cancelled = true;
      request.destroy();
    },
  });
}

module.exports = {
  CONVERSATION_ID_PATTERN,
  CORE_OPERATIONS,
  CHAT_STREAM_OPERATION,
  CoreRequestError,
  SPEECH_OPERATIONS,
  requestCore,
  streamCoreChat,
  validateDirectConfigPayload,
  validateAiModePayload,
  validateObsidianConnectPayload,
  validateChatPayload,
  validateConversationOpenPayload,
  validateProjectPayload,
  validateSpeechPayload,
};
