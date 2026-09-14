const fs = require('node:fs');
const path = require('node:path');

const DEFAULT_RUNTIME_SETTINGS = Object.freeze({
  backgroundRunning: false,
  startOnLogin: false,
});

function settingsPath(app, edition) {
  return path.join(app.getPath('userData'), `jarvis-runtime-${edition}.json`);
}

function normalizeRuntimeSettings(value) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('JARVIS runtime settings must be an object.');
  }
  for (const key of Object.keys(DEFAULT_RUNTIME_SETTINGS)) {
    if (value[key] !== undefined && typeof value[key] !== 'boolean') {
      throw new Error(`JARVIS runtime setting ${key} must be boolean.`);
    }
  }
  return {
    backgroundRunning: value.backgroundRunning === true,
    startOnLogin: value.startOnLogin === true,
  };
}

function loadRuntimeSettings(app, edition) {
  const filePath = settingsPath(app, edition);
  if (!fs.existsSync(filePath)) {
    return { settings: { ...DEFAULT_RUNTIME_SETTINGS }, error: null, filePath };
  }
  try {
    const payload = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    return {
      settings: normalizeRuntimeSettings(payload),
      error: null,
      filePath,
    };
  } catch (error) {
    return {
      settings: { ...DEFAULT_RUNTIME_SETTINGS },
      error: `Runtime settings could not be loaded: ${error.message || String(error)}`,
      filePath,
    };
  }
}

function saveRuntimeSettings(app, edition, settings) {
  const normalized = normalizeRuntimeSettings(settings);
  const filePath = settingsPath(app, edition);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const temporaryPath = `${filePath}.tmp`;
  fs.writeFileSync(
    temporaryPath,
    `${JSON.stringify({ version: 1, ...normalized }, null, 2)}\n`,
    'utf8',
  );
  fs.renameSync(temporaryPath, filePath);
  return normalized;
}

module.exports = {
  DEFAULT_RUNTIME_SETTINGS,
  loadRuntimeSettings,
  normalizeRuntimeSettings,
  saveRuntimeSettings,
  settingsPath,
};
