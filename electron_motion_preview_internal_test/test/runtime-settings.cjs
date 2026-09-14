const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const {
  DEFAULT_RUNTIME_SETTINGS,
  loadRuntimeSettings,
  normalizeRuntimeSettings,
  saveRuntimeSettings,
} = require('../runtime-settings.cjs');

function makeApp(root) {
  return { getPath: (name) => name === 'userData' ? root : '' };
}

test('runtime settings default to both disabled and are edition-scoped', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'jarvis-runtime-settings-'));
  try {
    const app = makeApp(root);
    const loaded = loadRuntimeSettings(app, 'development');
    assert.deepEqual(loaded.settings, DEFAULT_RUNTIME_SETTINGS);
    assert.equal(loaded.error, null);
    assert.match(loaded.filePath, /jarvis-runtime-development\.json$/);
    assert.notEqual(loaded.filePath, loadRuntimeSettings(app, 'internal-test').filePath);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('runtime settings round-trip only the two bounded booleans', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'jarvis-runtime-settings-'));
  try {
    const app = makeApp(root);
    saveRuntimeSettings(app, 'development', {
      backgroundRunning: true,
      startOnLogin: true,
      ignored: 'not persisted',
    });
    const loaded = loadRuntimeSettings(app, 'development');
    assert.deepEqual(loaded.settings, { backgroundRunning: true, startOnLogin: true });
    assert.equal(JSON.parse(fs.readFileSync(loaded.filePath, 'utf8')).ignored, undefined);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('malformed runtime settings remain explicit and normalize rejects non-booleans', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'jarvis-runtime-settings-'));
  try {
    const app = makeApp(root);
    const loaded = loadRuntimeSettings(app, 'development');
    fs.writeFileSync(loaded.filePath, '{"backgroundRunning":"yes"}', 'utf8');
    const malformed = loadRuntimeSettings(app, 'development');
    assert.deepEqual(malformed.settings, DEFAULT_RUNTIME_SETTINGS);
    assert.match(malformed.error, /backgroundRunning must be boolean/);
    assert.throws(() => normalizeRuntimeSettings({ startOnLogin: 'yes' }), /startOnLogin must be boolean/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
