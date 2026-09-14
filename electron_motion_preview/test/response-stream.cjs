const assert = require('node:assert/strict');
const test = require('node:test');

require('../renderer/response-stream.js');
const {
  DisplayPacer,
  SpeechChunker,
  StreamProjector,
  detectSpeechLanguage,
  isChineseVoice,
  plainSpeechText,
  selectSpeechVoiceForText,
} = globalThis.JarvisResponseStream;

test('display pacer reveals a burst in controlled increments and drains to the target', async () => {
  const updates = [];
  const pacer = new DisplayPacer({ charsPerSecond: 100, tickMs: 16, onUpdate: (text) => updates.push(text) });
  pacer.setTarget('abcdef');
  await pacer.drain();
  assert.ok(updates.length > 1);
  assert.ok(updates.some((text) => text.length > 0 && text !== 'abcdef'));
  assert.equal(updates.at(-1), 'abcdef');
});

test('stream projector exposes visible text for streaming speech and keeps terminal narration', () => {
  const projector = new StreamProjector();
  assert.equal(projector.append('[DIS').display, '');
  const state = projector.append('PLAY]\nVisible text.\n[VOICE_EN]\nHello.');
  assert.equal(state.display, 'Visible text.\n');
  assert.equal(state.speechDelta, 'Visible text.\n');
  assert.equal(projector.finish().speech, 'Hello.');
});

test('stream projector preserves spaces across incremental visible-text deltas', () => {
  const projector = new StreamProjector();
  assert.equal(projector.append('[DISPLAY]\nHello').speechDelta, 'Hello');
  assert.equal(projector.append(' world.').speechDelta, ' world.');
});

test('stream projector hides a partial voice marker until the protocol marker is complete', () => {
  const projector = new StreamProjector();
  assert.equal(projector.append('[DISPLAY]\nVisible text.\n[VOICE_').display, 'Visible text.\n');
  assert.equal(projector.append('EN]\nHello.').display, 'Visible text.\n');
});

test('detects Chinese response language locally without a network request', () => {
  assert.equal(detectSpeechLanguage('请检查系统状态。'), 'zh');
  assert.equal(detectSpeechLanguage('Please check the system status.'), 'en');
  assert.equal(detectSpeechLanguage('请检查 Windows 的系统状态。'), 'zh');
});

test('selects an installed Chinese voice while preserving the selected voice for English', () => {
  const voices = [
    { id: 'george', language: 'en-GB' },
    { id: 'huihui', language: 'zh-CN' },
  ];
  assert.equal(isChineseVoice(voices[1]), true);
  assert.equal(selectSpeechVoiceForText('请打开设置。', voices, 'george'), 'huihui');
  assert.equal(selectSpeechVoiceForText('Please open Settings.', voices, 'george'), 'george');
  assert.equal(selectSpeechVoiceForText('请打开设置。', voices, 'huihui'), 'huihui');
  assert.equal(selectSpeechVoiceForText('中文回复', [{ id: 'george', language: 'en-GB' }], 'george'), 'george');
});

test('speech chunker emits sentence boundaries and flushes the remainder', () => {
  const chunker = new SpeechChunker({ minChars: 5, maxChars: 25 });
  assert.deepEqual(chunker.push('First sentence. Second'), ['First sentence.']);
  assert.deepEqual(chunker.flush(), ['Second']);
});

test('speech chunker reports a short buffered reply before the final flush', () => {
  const chunker = new SpeechChunker();
  assert.equal(chunker.hasPendingText(), false);
  assert.deepEqual(chunker.push('Short reply.'), []);
  assert.equal(chunker.hasPendingText(), true);
  assert.deepEqual(chunker.flush(), ['Short reply.']);
  assert.equal(chunker.hasPendingText(), false);
});

test('speech chunker keeps comma phrases together until a sentence boundary', () => {
  const chunker = new SpeechChunker({ minChars: 5, maxChars: 40 });
  assert.deepEqual(chunker.push('我帮你检查过了，继续处理这个问题。下一步'), ['我帮你检查过了，继续处理这个问题。']);
  assert.deepEqual(chunker.flush(), ['下一步']);
});

test('speech chunker batches short sentences within the natural boundary window', () => {
  const chunker = new SpeechChunker();
  assert.deepEqual(chunker.push('This is the first sentence, and it should stay together. The next sentence is also here. A third sentence keeps the audio chunk complete.'), [
    'This is the first sentence, and it should stay together. The next sentence is also here. A third sentence keeps the audio chunk complete.',
  ]);
  assert.deepEqual(chunker.flush(), []);
});

test('speech chunker uses a bounded whitespace cut only after the maximum', () => {
  const chunker = new SpeechChunker({ minChars: 20, maxChars: 45 });
  const chunks = chunker.push('This deliberately long sentence has no punctuation and must stay bounded while it streams onward.');
  assert.ok(chunks.length >= 1);
  assert.ok(chunks.every((chunk) => chunk.length <= 45));
});

test('plain speech projection removes presentation markdown', () => {
  assert.equal(plainSpeechText('**Ready**\n\n* Check Core'), 'Ready\n\n• Check Core');
});
