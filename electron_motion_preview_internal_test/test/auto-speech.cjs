const assert = require('node:assert/strict');
const test = require('node:test');

const { create } = require('../renderer/auto-speech.js');

const flush = () => new Promise((resolve) => setImmediate(resolve));

test('automatic speech is opt-in and prebuffers current plus next chunk', async () => {
  const synthCalls = [];
  const playCalls = [];
  const synthResolvers = [];
  const playResolvers = [];
  const speech = create({
    synthesize(text) {
      synthCalls.push(text);
      return new Promise((resolve) => synthResolvers.push(resolve));
    },
    play(audio, item) {
      playCalls.push({ audio, id: item.id });
      return new Promise((resolve) => playResolvers.push(resolve));
    },
  });

  assert.equal(await speech.enqueue('chunk-1', 'Not spoken while off.'), false);
  assert.equal(speech.setEnabled(true), true);
  assert.equal(await speech.enqueue('chunk-1', 'First sentence.'), true);
  assert.equal(await speech.enqueue('chunk-2', 'Second sentence.'), true);
  assert.equal(speech.pendingCount(), 2);
  await flush();
  assert.deepEqual(synthCalls, ['First sentence.']);

  synthResolvers.shift()({ audio_base64: 'first' });
  await flush();
  assert.deepEqual(synthCalls, ['First sentence.', 'Second sentence.']);
  assert.deepEqual(playCalls, [{ audio: { audio_base64: 'first' }, id: 'chunk-1' }]);

  playResolvers.shift()();
  await flush();
  assert.equal(speech.snapshot().current.id, 'chunk-2');
  assert.equal(speech.snapshot().current.state, 'synthesizing');
  synthResolvers.shift()({ audio_base64: 'second' });
  await flush();
  assert.deepEqual(playCalls.map((call) => call.id), ['chunk-1', 'chunk-2']);
  playResolvers.shift()();
  await flush();
  assert.equal(speech.pendingCount(), 0);
  assert.equal(speech.snapshot().speaking, false);
});

test('synthesis starts while the response stream is still open', async () => {
  const order = [];
  const speech = create({
    synthesize: async () => {
      order.push('synthesis-start');
      return { audio_base64: 'first' };
    },
    play: async () => {},
  });

  speech.setEnabled(true);
  await speech.enqueue('stream-1', 'The first streamed sentence.');
  order.push('stream-still-generating');
  assert.deepEqual(order, ['synthesis-start', 'stream-still-generating']);
  speech.cancel();
});

test('keeps the language-selected voice with the queued speech item', async () => {
  const calls = [];
  const speech = create({
    synthesize: async (text, voiceId) => {
      calls.push({ text, voiceId });
      return { audio_base64: 'audio' };
    },
    play: async () => {},
  });

  speech.setEnabled(true);
  await speech.enqueue('zh-1', '你好。', { voiceId: 'huihui' });
  await flush();
  assert.deepEqual(calls, [{ text: '你好。', voiceId: 'huihui' }]);
  speech.cancel();
});

test('text-only queued chunks do not block progressive stream delivery', async () => {
  let resolveFirst;
  const speech = create({
    synthesize: () => new Promise((resolve) => { resolveFirst = resolve; }),
    play: async () => {},
  });

  speech.setEnabled(true);
  await speech.enqueue('queue-1', 'First sentence.');
  await speech.enqueue('queue-2', 'Second sentence.');
  const accepted = await speech.enqueue('queue-3', 'Third sentence.');

  assert.equal(accepted, true);
  assert.equal(speech.pendingCount(), 3);
  assert.equal(speech.snapshot().current.id, 'queue-1');
  assert.equal(speech.snapshot().next.id, 'queue-2');
  resolveFirst({ audio_base64: 'first' });
  speech.cancel();
});

test('cancellation stops playback, clears pending work, and ignores late synthesis', async () => {
  let stopCalls = 0;
  const states = [];
  let resolveSynthesis;
  const speech = create({
    synthesize: () => new Promise((resolve) => { resolveSynthesis = resolve; }),
    play: async () => {},
    stop: () => { stopCalls += 1; },
    onState: (state) => states.push(state),
  });

  speech.setEnabled(true);
  await speech.enqueue('cancel-1', 'This will be cancelled.');
  await speech.enqueue('cancel-2', 'This is the next chunk.');
  speech.cancel();
  assert.equal(speech.pendingCount(), 0);
  assert.equal(stopCalls, 1);
  resolveSynthesis({ audio_base64: 'late' });
  await flush();
  assert.equal(speech.pendingCount(), 0);
  assert.ok(states.some((state) => state.state === 'cancelled'));
});

test('synthesis failure is observable and does not reject the text response path', async () => {
  const errors = [];
  const speech = create({
    synthesize: async () => { throw new Error('Windows system voice is unavailable.'); },
    play: async () => {},
    onState: (state) => { if (state.error) errors.push(state.error); },
  });

  speech.setEnabled(true);
  assert.equal(await speech.enqueue('error-1', 'This remains visible as text.'), true);
  await flush();
  assert.deepEqual(errors, ['Windows system voice is unavailable.']);
  assert.equal(speech.pendingCount(), 0);
});
