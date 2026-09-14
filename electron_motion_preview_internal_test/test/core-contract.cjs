const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const Module = require('node:module');
const test = require('node:test');

let behavior = { statusCode: 200, body: '{}', errorCode: null };
const calls = [];

const fakeHttp = {
  request(options, callback) {
    calls.push({ options, request: null });
    const request = new EventEmitter();
    calls[calls.length - 1].request = request;
    request.body = '';
    request.setTimeout = (timeout, handler) => {
      request.timeout = timeout;
      request.timeoutHandler = handler;
    };
    request.write = (body) => {
      request.body += body;
    };
    request.destroy = () => {};
    request.end = () => {
      queueMicrotask(() => {
        if (behavior.errorCode) {
          request.emit('error', { code: behavior.errorCode, message: behavior.errorCode });
          return;
        }
        const response = new EventEmitter();
        response.statusCode = behavior.statusCode;
        response.setEncoding = () => {};
        callback(response);
        if (behavior.body) response.emit('data', behavior.body);
        response.emit('end');
      });
    };
    return request;
  },
};

const originalLoad = Module._load;
Module._load = function load(request, parent, isMain) {
  if (request === 'node:http') return fakeHttp;
  return originalLoad.call(this, request, parent, isMain);
};
const bridge = require('../core-bridge.cjs');
Module._load = originalLoad;

test('Core operations remain fixed to the loopback allowlist', () => {
  assert.deepEqual(bridge.CORE_OPERATIONS, {
    health: { method: 'GET', path: '/api/health' },
    telemetry: { method: 'GET', path: '/api/telemetry' },
    conversationHistory: { method: 'GET', path: '/api/chat/history' },
    conversationList: { method: 'GET', path: '/api/chat/conversations' },
    conversationOpen: { method: 'POST', path: '/api/chat/history/open' },
    createConversation: { method: 'POST', path: '/api/chat/session' },
    sendMessage: { method: 'POST', path: '/api/chat', timeoutMs: 65000 },
    systemInfo: { method: 'GET', path: '/api/system-info' },
    systemStatus: { method: 'GET', path: '/api/system-status' },
    projects: { method: 'GET', path: '/api/projects' },
    projectGitStatus: { method: 'POST', path: '/api/projects/git-status' },
    projectListFiles: { method: 'POST', path: '/api/projects/list-files' },
    projectReadFile: { method: 'POST', path: '/api/projects/read-file' },
    projectSearch: { method: 'POST', path: '/api/projects/search' },
    projectRefresh: { method: 'POST', path: '/api/projects/refresh' },
    obsidianVaults: { method: 'GET', path: '/api/obsidian/vaults' },
    obsidianConnect: { method: 'POST', path: '/api/obsidian/vaults', timeoutMs: 15000 },
    obsidianDisconnect: { method: 'POST', path: '/api/obsidian/disconnect', timeoutMs: 15000 },
    tasks: { method: 'GET', path: '/api/tasks' },
    aiMode: { method: 'POST', path: '/api/settings/ai/mode' },
    aiCheck: { method: 'POST', path: '/api/settings/ai/check', timeoutMs: 65000 },
    aiUsage: { method: 'GET', path: '/api/settings/ai/usage', timeoutMs: 65000 },
    aiDisconnect: { method: 'POST', path: '/api/settings/ai/disconnect', timeoutMs: 65000 },
    aiDirectConfig: { method: 'POST', path: '/api/settings/ai/direct-config', timeoutMs: 15000 },
  });
  assert.equal(bridge.CORE_OPERATIONS.health.path, '/api/health');
  assert.equal(bridge.CORE_OPERATIONS.telemetry.path, '/api/telemetry');
  assert.equal(bridge.CORE_OPERATIONS.conversationHistory.path, '/api/chat/history');
  assert.equal(bridge.CORE_OPERATIONS.conversationList.path, '/api/chat/conversations');
  assert.equal(bridge.CORE_OPERATIONS.conversationOpen.path, '/api/chat/history/open');
  assert.equal(bridge.CORE_OPERATIONS.createConversation.path, '/api/chat/session');
  assert.equal(bridge.CORE_OPERATIONS.sendMessage.path, '/api/chat');
  assert.equal(bridge.CORE_OPERATIONS.systemInfo.path, '/api/system-info');
  assert.equal(bridge.CORE_OPERATIONS.systemStatus.path, '/api/system-status');
  assert.equal(bridge.CORE_OPERATIONS.obsidianVaults.path, '/api/obsidian/vaults');
  assert.equal(bridge.CORE_OPERATIONS.obsidianConnect.path, '/api/obsidian/vaults');
  assert.equal(bridge.CORE_OPERATIONS.obsidianDisconnect.path, '/api/obsidian/disconnect');
  assert.equal(bridge.CORE_OPERATIONS.tasks.path, '/api/tasks');
  assert.equal(bridge.CORE_OPERATIONS.aiMode.path, '/api/settings/ai/mode');
  assert.equal(bridge.CORE_OPERATIONS.aiCheck.path, '/api/settings/ai/check');
  assert.equal(bridge.CORE_OPERATIONS.aiUsage.path, '/api/settings/ai/usage');
  assert.equal(bridge.CORE_OPERATIONS.aiDisconnect.path, '/api/settings/ai/disconnect');
  assert.equal(bridge.CORE_OPERATIONS.aiDirectConfig.path, '/api/settings/ai/direct-config');
  assert.deepEqual(
    bridge.validateDirectConfigPayload({
      apiKey: ' key-test ', provider: 'deepseek', model: 'deepseek-v4-flash', baseUrl: '', ignored: true,
    }),
    { api_key: 'key-test', provider: 'deepseek', model: 'deepseek-v4-flash', base_url: null },
  );
  assert.throws(
    () => bridge.validateDirectConfigPayload({ apiKey: 'key', provider: 'unknown', model: 'x' }),
    (error) => error.code === 'INVALID_REQUEST',
  );
  assert.deepEqual(
    bridge.validateObsidianConnectPayload({
      vaultId: 'jarvis-wiki', name: ' JARVIS Wiki ', path: ' C:\\Users\\ongzh\\JARVIS Wiki ', ignored: true,
    }),
    {
      vault_id: 'jarvis-wiki',
      name: 'JARVIS Wiki',
      path: 'C:\\Users\\ongzh\\JARVIS Wiki',
      default_access: 'excluded',
    },
  );
  assert.throws(
    () => bridge.validateObsidianConnectPayload({ vaultId: 'jarvis-wiki', name: 'JARVIS Wiki', path: 'C:\\Vault', defaultAccess: 'public' }),
    (error) => error.code === 'INVALID_REQUEST',
  );
  assert.deepEqual(
    bridge.validateConversationOpenPayload({ conversationId: 'jarvis-01234567-89ab-cdef-0123-456789abcdef', ignored: true }),
    { conversation_id: 'jarvis-01234567-89ab-cdef-0123-456789abcdef' },
  );
  assert.throws(
    () => bridge.validateConversationOpenPayload({ conversationId: 'primary' }),
    (error) => error.code === 'INVALID_REQUEST',
  );
});

test('speech operations reuse only the fixed local Windows voice endpoints', () => {
  assert.deepEqual(bridge.SPEECH_OPERATIONS, {
    speakReply: { method: 'POST', path: '/api/system-speech' },
    synthesizeSpeech: { method: 'POST', path: '/api/system-speech/synthesize', timeoutMs: 65000 },
    speechSettings: { method: 'GET', path: '/api/system-speech/settings' },
    speechVoices: { method: 'GET', path: '/api/system-speech/voices' },
    stopSpeech: { method: 'POST', path: '/api/system-speech/stop' },
  });
  assert.deepEqual(
    bridge.validateSpeechPayload({ text: '  Ready.  ', ignored: true }),
    { text: 'Ready.' },
  );
  assert.deepEqual(
    bridge.validateSpeechPayload({ text: 'Ready.', voice: 'voice-id' }),
    { text: 'Ready.', voice: 'voice-id' },
  );
  assert.throws(
    () => bridge.validateSpeechPayload({ text: '' }),
    (error) => error.code === 'INVALID_REQUEST',
  );
});

test('chat payload is bounded and mapped to the Core contract', async () => {
  assert.deepEqual(
    bridge.validateChatPayload({
      message: '  read this  ',
      conversationId: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
    }),
    {
      message: 'read this',
      conversation_id: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
      output_language: 'en',
    },
  );
  assert.deepEqual(
    bridge.validateChatPayload({
      message: '  read this  ',
      conversationId: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
      outputLanguage: 'zh-CN',
    }),
    {
      message: 'read this',
      conversation_id: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
      output_language: 'zh-CN',
    },
  );
  assert.throws(
    () => bridge.validateChatPayload({
      message: 'read this',
      conversationId: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
      outputLanguage: 'fr',
    }),
    (error) => error.code === 'INVALID_REQUEST',
  );
  assert.throws(
    () => bridge.validateChatPayload({ message: 'read this', conversationId: 'primary' }),
    (error) => error.code === 'INVALID_REQUEST',
  );
  await assert.rejects(
    () => bridge.requestCore('arbitrary', {}),
    (error) => error.code === 'INVALID_OPERATION',
  );
});

test('read-only surface payloads stay bounded and project requests map to Core fields', () => {
  assert.deepEqual(
    bridge.validateProjectPayload({ projectName: 'JARVIS', relativePath: 'app/api.py' }, { file: true }),
    { project_name: 'JARVIS', relative_path: 'app/api.py' },
  );
  assert.deepEqual(
    bridge.validateProjectPayload({ projectName: 'JARVIS', keyword: 'health' }, { keyword: true }),
    { project_name: 'JARVIS', relative_path: '.', keyword: 'health' },
  );
  assert.deepEqual(bridge.validateAiModePayload({ mode: 'direct_api', ignored: true }), { mode: 'direct_api' });
  assert.throws(
    () => bridge.validateProjectPayload({ projectName: 'JARVIS' }, { file: true }),
    (error) => error.code === 'INVALID_REQUEST',
  );
  assert.throws(
    () => bridge.validateAiModePayload({ mode: 'gemini' }),
    (error) => error.code === 'INVALID_REQUEST',
  );
});

test('health uses the fixed loopback request and preserves JSON', async () => {
  behavior = { statusCode: 200, body: '{"core":{"status":"ready"}}', errorCode: null };
  calls.length = 0;
  const response = await bridge.requestCore('health');
  assert.deepEqual(response, { core: { status: 'ready' } });
  assert.equal(calls[0].options.host, '127.0.0.1');
  assert.equal(calls[0].options.port, 8765);
  assert.equal(calls[0].options.path, '/api/health');
  assert.equal(calls[0].options.method, 'GET');
});

test('telemetry uses the fixed loopback endpoint and preserves availability fields', async () => {
  behavior = {
    statusCode: 200,
    body: JSON.stringify({
      cpu_percent: 12.5,
      memory_percent: 38.7,
      gpus: [],
      gpu_error: 'No NVIDIA GPU detected.',
    }),
    errorCode: null,
  };
  calls.length = 0;
  const response = await bridge.requestCore('telemetry');
  assert.equal(response.cpu_percent, 12.5);
  assert.equal(response.memory_percent, 38.7);
  assert.deepEqual(response.gpus, []);
  assert.equal(calls[0].options.host, '127.0.0.1');
  assert.equal(calls[0].options.port, 8765);
  assert.equal(calls[0].options.path, '/api/telemetry');
  assert.equal(calls[0].options.method, 'GET');
  assert.equal(calls[0].request.body, '');
});

test('existing read-only Core surfaces stay on fixed loopback endpoints', async () => {
  const cases = [
    ['conversationHistory', '/api/chat/history'],
    ['conversationList', '/api/chat/conversations'],
    ['systemInfo', '/api/system-info'],
    ['systemStatus', '/api/system-status'],
    ['projects', '/api/projects'],
    ['obsidianVaults', '/api/obsidian/vaults'],
    ['tasks', '/api/tasks'],
  ];
  for (const [operation, path] of cases) {
    behavior = { statusCode: 200, body: '{}', errorCode: null };
    calls.length = 0;
    await bridge.requestCore(operation);
    assert.equal(calls[0].options.host, '127.0.0.1');
    assert.equal(calls[0].options.port, 8765);
    assert.equal(calls[0].options.path, path);
    assert.equal(calls[0].options.method, 'GET');
    assert.equal(calls[0].request.body, '');
  }
});

test('project inspection and AI mode requests use bounded POST payloads', async () => {
  behavior = { statusCode: 200, body: '{"success":true,"status":"completed"}', errorCode: null };
  calls.length = 0;
  await bridge.requestCore('projectSearch', {
    projectName: 'JARVIS',
    keyword: 'health',
    relativePath: 'app',
    ignored: 'discarded',
  });
  assert.equal(calls[0].options.path, '/api/projects/search');
  assert.equal(calls[0].options.method, 'POST');
  assert.deepEqual(JSON.parse(calls[0].request.body), {
    project_name: 'JARVIS',
    relative_path: 'app',
    keyword: 'health',
  });

  calls.length = 0;
  await bridge.requestCore('aiMode', { mode: 'managed_subscription', ignored: true });
  assert.equal(calls[0].options.path, '/api/settings/ai/mode');
  assert.deepEqual(JSON.parse(calls[0].request.body), { mode: 'managed_subscription' });

  calls.length = 0;
  await bridge.requestCore('aiCheck');
  assert.equal(calls[0].options.path, '/api/settings/ai/check');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].request.body, '');
  assert.equal(calls[0].request.timeout, 65000);

  calls.length = 0;
  await bridge.requestCore('aiUsage');
  assert.equal(calls[0].options.path, '/api/settings/ai/usage');
  assert.equal(calls[0].options.method, 'GET');
  assert.equal(calls[0].request.body, '');
  assert.equal(calls[0].request.timeout, 65000);
});

test('Obsidian registration uses the explicit Core endpoint and bounded fields', async () => {
  behavior = { statusCode: 200, body: '{"id":"jarvis-wiki","enabled":true}', errorCode: null };
  calls.length = 0;
  await bridge.requestCore('obsidianConnect', {
    vaultId: 'jarvis-wiki',
    name: 'JARVIS Wiki',
    path: 'C:\\Users\\ongzh\\JARVIS Wiki',
    defaultAccess: 'excluded',
    ignored: 'discarded',
  });
  assert.equal(calls[0].options.path, '/api/obsidian/vaults');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].request.timeout, 15000);
  assert.deepEqual(JSON.parse(calls[0].request.body), {
    vault_id: 'jarvis-wiki',
    name: 'JARVIS Wiki',
    path: 'C:\\Users\\ongzh\\JARVIS Wiki',
    default_access: 'excluded',
  });
});

test('createConversation uses the fixed session endpoint', async () => {
  behavior = {
    statusCode: 200,
    body: '{"conversation_id":"jarvis-01234567-89ab-cdef-0123-456789abcdef"}',
    errorCode: null,
  };
  calls.length = 0;
  const response = await bridge.requestCore('createConversation');
  assert.equal(response.conversation_id, 'jarvis-01234567-89ab-cdef-0123-456789abcdef');
  assert.equal(calls[0].options.path, '/api/chat/session');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].request.body, '');
});

test('conversationOpen serializes only the approved opaque ID', async () => {
  behavior = {
    statusCode: 200,
    body: JSON.stringify({ id: 'jarvis-01234567-89ab-cdef-0123-456789abcdef', turns: [] }),
    errorCode: null,
  };
  calls.length = 0;
  await bridge.requestCore('conversationOpen', {
    conversationId: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
    ignored: 'discarded',
  });
  assert.equal(calls[0].options.path, '/api/chat/history/open');
  assert.equal(calls[0].options.method, 'POST');
  assert.deepEqual(JSON.parse(calls[0].request.body), {
    conversation_id: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
  });
});

test('sendMessage serializes only the approved chat fields', async () => {
  behavior = { statusCode: 200, body: '{"reply":"ready","tool_results":[]}', errorCode: null };
  calls.length = 0;
  const response = await bridge.requestCore('sendMessage', {
    message: '  Reply with READY. ',
    conversationId: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
    outputLanguage: 'zh-CN',
    extra: 'discarded',
  });
  assert.deepEqual(response, { reply: 'ready', tool_results: [] });
  assert.equal(calls[0].options.path, '/api/chat');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].request.timeout, 65000);
  assert.deepEqual(JSON.parse(calls[0].request.body), {
    message: 'Reply with READY.',
    conversation_id: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
    output_language: 'zh-CN',
  });
});

test('chat stream forwards newline-delimited events from the fixed Core endpoint', async () => {
  behavior = {
    statusCode: 200,
    body: '{"type":"start"}\n{"type":"delta","text":"Hello"}\n{"type":"complete","response":{"reply":"Hello"}}\n',
    errorCode: null,
  };
  calls.length = 0;
  const events = [];
  let ended = false;
  await new Promise((resolve, reject) => {
    bridge.streamCoreChat(
      {
        message: 'Hello',
        conversationId: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
        outputLanguage: 'zh-CN',
      },
      {
        onEvent: (event) => events.push(event),
        onEnd: () => { ended = true; resolve(); },
        onError: reject,
      },
    );
  });
  assert.equal(calls[0].options.path, '/api/chat/stream');
  assert.equal(calls[0].options.method, 'POST');
  assert.deepEqual(JSON.parse(calls[0].request.body), {
    message: 'Hello',
    conversation_id: 'jarvis-01234567-89ab-cdef-0123-456789abcdef',
    output_language: 'zh-CN',
  });
  assert.deepEqual(events.map((event) => event.type), ['start', 'delta', 'complete']);
  assert.equal(ended, true);
});

test('speech requests serialize bounded text and optional voice, while stop and voice list use fixed endpoints', async () => {
  behavior = { statusCode: 204, body: '', errorCode: null };
  calls.length = 0;
  const spoken = await bridge.requestCore('speakReply', { text: '  Ready.  ', voice: 'voice-id', extra: 'discarded' });
  assert.deepEqual(spoken, {});
  assert.equal(calls[0].options.path, '/api/system-speech');
  assert.equal(calls[0].options.method, 'POST');
  assert.deepEqual(JSON.parse(calls[0].request.body), { text: 'Ready.', voice: 'voice-id' });

  behavior = { statusCode: 200, body: '{"audio_base64":"UklGRg==","mime_type":"audio/wav"}', errorCode: null };
  calls.length = 0;
  const synthesized = await bridge.requestCore('synthesizeSpeech', { text: '  Chunk.  ', voice: 'voice-id' });
  assert.deepEqual(synthesized, { audio_base64: 'UklGRg==', mime_type: 'audio/wav' });
  assert.equal(calls[0].options.path, '/api/system-speech/synthesize');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].request.timeout, 65000);

  behavior = { statusCode: 204, body: '', errorCode: null };
  calls.length = 0;
  const voices = await bridge.requestCore('speechVoices');
  assert.deepEqual(voices, {});
  assert.equal(calls[0].options.path, '/api/system-speech/voices');
  assert.equal(calls[0].options.method, 'GET');
  assert.equal(calls[0].request.body, '');

  calls.length = 0;
  const stopped = await bridge.requestCore('stopSpeech');
  assert.deepEqual(stopped, {});
  assert.equal(calls[0].options.path, '/api/system-speech/stop');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].request.body, '');
});

test('Core HTTP failures stay explicit', async () => {
  behavior = { statusCode: 503, body: '{"detail":"AI unavailable"}', errorCode: null };
  await assert.rejects(
    () => bridge.requestCore('health'),
    (error) => error.code === 'CORE_HTTP_ERROR'
      && error.status === 503
      && error.message === 'AI unavailable',
  );
  behavior = { statusCode: 200, body: '{not-json', errorCode: null };
  await assert.rejects(
    () => bridge.requestCore('health'),
    (error) => error.code === 'CORE_INVALID_RESPONSE'
      && error.status === 200,
  );
});

test('Core disconnect maps to an explicit offline error', async () => {
  behavior = { statusCode: 200, body: '{}', errorCode: 'ECONNREFUSED' };
  await assert.rejects(
    () => bridge.requestCore('health'),
    (error) => error.code === 'CORE_OFFLINE'
      && /offline/i.test(error.message),
  );
});
