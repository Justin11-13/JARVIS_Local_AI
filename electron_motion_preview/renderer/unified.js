const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const themeStorageKey = 'jarvis.ui.theme.v1';
const themeLabels = Object.freeze({
  amber: 'Amber Core',
  cyan: 'Cyan Circuit',
  violet: 'Violet Pulse',
  matrix: 'Matrix Green',
});
const themeKeys = new Set(Object.keys(themeLabels));
const customThemeStorageKey = 'jarvis.ui.theme.custom.v1';
const themePaletteFields = Object.freeze({
  background: Object.freeze({ cssVariable: '--bg', controlId: 'theme-color-background', outputId: 'theme-color-background-value' }),
  surface: Object.freeze({ cssVariable: '--surface', controlId: 'theme-color-surface', outputId: 'theme-color-surface-value' }),
  border: Object.freeze({ cssVariable: '--line', controlId: 'theme-color-border', outputId: 'theme-color-border-value' }),
  accent: Object.freeze({ cssVariable: '--gold', controlId: 'theme-color-accent', outputId: 'theme-color-accent-value' }),
  text: Object.freeze({ cssVariable: '--text', controlId: 'theme-color-text', outputId: 'theme-color-text-value' }),
  muted: Object.freeze({ cssVariable: '--muted', controlId: 'theme-color-muted', outputId: 'theme-color-muted-value' }),
  coreA: Object.freeze({ cssVariable: '--core-color-a', controlId: 'theme-color-core-a', outputId: 'theme-color-core-a-value' }),
  coreB: Object.freeze({ cssVariable: '--core-color-b', controlId: 'theme-color-core-b', outputId: 'theme-color-core-b-value' }),
});
const themePaletteKeys = Object.freeze(Object.keys(themePaletteFields));
const customThemeStyleVariables = Object.freeze([
  '--bg', '--surface', '--surface-2', '--surface-3', '--surface-rgb', '--surface-deep-rgb',
  '--gold', '--gold-hot', '--amber', '--amber-dim', '--line', '--line-soft', '--border-strong',
  '--button-bg', '--button-text', '--surface-hover', '--accent-hot', '--scrollbar', '--message-text',
  '--placeholder', '--composer-bg', '--stage-bg', '--orbit-rgb', '--core-label', '--core-label-muted', '--monitor-bg',
  '--control-label', '--control-border', '--control-bg', '--control-text', '--control-muted',
  '--control-active-border', '--control-active-text', '--nav-text', '--nav-hover-border',
  '--nav-active-border', '--tooltip-bg', '--dock-bg', '--panel-bg-top', '--panel-bg-bottom',
  '--panel-scrollbar', '--detail-label', '--detail-value', '--caption', '--caption-muted', '--quiet',
  '--muted', '--text', '--brand', '--row-hover', '--accent-rgb', '--warm-rgb', '--accent-glow',
  '--tag', '--code-border', '--code-bg', '--code-text', '--readout', '--empty-border', '--select-border',
  '--toggle-border', '--toggle-bg', '--core-color-a', '--core-color-b', '--core-glow', '--composer-border',
]);
const motionStorageKey = 'jarvis.motion.low.v1';
const speechVoiceStorageKey = 'jarvis.auto-speech.voice.v1';
const edition = new URLSearchParams(location.search).get('edition') === 'internal-test'
  ? 'internal-test'
  : 'development';
const internalTestPages = new Set([
  'assistant', 'history', 'core', 'tools', 'context', 'connections', 'usage', 'settings',
  'memory', 'knowledge', 'theme', 'voice', 'events', 'errors',
]);

function readStoredTheme() {
  try {
    const stored = localStorage.getItem(themeStorageKey);
    return themeKeys.has(stored) ? stored : 'amber';
  } catch {
    return 'amber';
  }
}

function normalizeThemeColor(value) {
  const match = String(value || '').trim().match(/^#([0-9a-f]{6})$/i);
  return match ? `#${match[1].toUpperCase()}` : null;
}

function readStoredCustomTheme() {
  try {
    const raw = localStorage.getItem(customThemeStorageKey);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {};
    return themePaletteKeys.reduce((result, key) => {
      const color = normalizeThemeColor(parsed[key]);
      if (color) result[key] = color;
      return result;
    }, {});
  } catch {
    return {};
  }
}

let customThemeOverrides = readStoredCustomTheme();
document.documentElement.dataset.theme = readStoredTheme();
applyCustomThemeOverrides();

const pages = {
  assistant: ['Assistant', 'Personal assistant', 'LIVE · LOOPBACK CORE'],
  history: ['Chat history', 'New launches start a fresh chat; open saved chats here explicitly.', 'WORKSPACE · CHAT HISTORY'],
  core: ['Core connection', 'Refresh or reconnect the local JARVIS Core.', 'CONTROL · CORE'],
  tasks: ['Tasks', 'Review local work before it is acted on.', 'WORKSPACE · TASKS'],
  tools: ['Tool Results', 'Retained outside the chat transcript.', 'WORKSPACE · TOOL RESULTS'],
  context: ['Device', 'Read-only local system information.', 'CONTROL · DEVICE'],
  'working-context': ['Working context', 'Advanced project inspection for development use.', 'DEVELOPER · CONTEXT'],
  connections: ['AI connections', 'Manage the selected transport without inventing account access.', 'CONTROL · AI'],
  usage: ['Token usage', 'Account usage is separate from connection state.', 'OBSERVE · USAGE'],
  settings: ['Settings', 'Local display and voice preferences.', 'CONTROL · SETTINGS'],
  memory: ['Memory', 'Conversation history remains inspectable.', 'UNDERSTAND · MEMORY'],
  knowledge: ['Knowledge', 'Named sources remain inspectable.', 'UNDERSTAND · KNOWLEDGE'],
  theme: ['Theme', 'Local visual system for the Core and floating cards.', 'VISUAL SYSTEM · THEME'],
  voice: ['Voice', 'Choose an installed Windows voice package for automatic speech.', 'CONTROL · VOICE'],
  automation: ['Automation', 'Drafted, reviewable routines only.', 'CONTROL · AUTOMATION'],
  events: ['Events', 'Visible local lifecycle evidence.', 'SAFETY · EVENTS'],
  errors: ['Errors', 'Bridge and Core failures remain explicit.', 'SAFETY · ERRORS'],
  handoff: ['Codex handoff', 'Authorization must remain explicit.', 'SAFETY · HANDOFF'],
};

let active = 'assistant';
const panelIdleStorageKey = 'jarvis.panel.idle-seconds.v1';
const autoSpeechStorageKey = 'jarvis.auto-speech.enabled.v1';
const panelIdleOptions = Object.freeze([5, 10, 25, 30, 60, 0]);
let panelIdleSeconds = 5;
let panelCloseTimer = 0;
let pagesNavigationExpanded = false;
let lowMotionPreference = null;
let tokenUsageOpen = false;
let tokenUsageTransitionToken = 0;

function readLowMotionPreference() {
  try {
    const stored = localStorage.getItem(motionStorageKey);
    return stored === null ? null : stored === 'true';
  } catch {
    return null;
  }
}

function lowMotionEnabled() {
  // Low motion is an explicit local preference; it is never enabled by default.
  return lowMotionPreference === true;
}

function syncMotionControls() {
  const enabled = lowMotionEnabled();
  const hiddenMotionControl = $('#reduced');
  const settingControl = $('#low-motion-setting');
  if (hiddenMotionControl) hiddenMotionControl.checked = enabled;
  if (settingControl) settingControl.checked = enabled;
  setText('motion-status', enabled
    ? 'Low motion · Core rotation continues at a slower pace.'
    : 'Standard motion · Core rotation follows activity.');
}

function saveLowMotionPreference(enabled) {
  lowMotionPreference = enabled === true;
  try {
    localStorage.setItem(motionStorageKey, String(lowMotionPreference));
  } catch (error) {
    recordEvent('error', `Low motion setting could not be saved: ${error.message || 'storage unavailable'}`);
  }
  syncMotionControls();
  sync();
}

function readPanelIdleSeconds() {
  try {
    const stored = Number.parseInt(localStorage.getItem(panelIdleStorageKey) || '', 10);
    return panelIdleOptions.includes(stored) ? stored : 5;
  } catch {
    return 5;
  }
}

function syncPanelIdleSetting() {
  const control = $('#panel-idle-setting');
  if (control) control.value = String(panelIdleSeconds);
  setText('panel-idle-status', panelIdleSeconds === 0
    ? 'Never · panels stay open until you close them.'
    : `${panelIdleSeconds}s · panels close after no interaction.`);
}

function savePanelIdleSeconds(value) {
  const next = Number.parseInt(String(value), 10);
  panelIdleSeconds = panelIdleOptions.includes(next) ? next : 5;
  try {
    localStorage.setItem(panelIdleStorageKey, String(panelIdleSeconds));
  } catch (error) {
    recordEvent('error', `Panel auto-close setting could not be saved: ${error.message || 'storage unavailable'}`);
  }
  syncPanelIdleSetting();
  if (panelIdleSeconds === 0 || active === 'assistant') clearPanelCloseTimer();
  else armPanelCloseTimer();
}

function readAutoSpeechPreference() {
  try {
    return localStorage.getItem(autoSpeechStorageKey) === 'true';
  } catch {
    return false;
  }
}

function saveAutoSpeechPreference(enabled) {
  try {
    localStorage.setItem(autoSpeechStorageKey, enabled ? 'true' : 'false');
  } catch (error) {
    recordEvent('error', `Automatic speech setting could not be saved: ${error.message || 'storage unavailable'}`);
  }
}

const runtimeSettingControls = Object.freeze({
  backgroundRunning: $('#background-running-setting'),
  startOnLogin: $('#start-on-login-setting'),
});

function renderRuntimeSettings(snapshot, error = null) {
  const settings = snapshot && typeof snapshot === 'object' ? snapshot : {};
  const backgroundRunning = settings.backgroundRunning === true;
  const startOnLogin = settings.startOnLogin === true;
  if (runtimeSettingControls.backgroundRunning) runtimeSettingControls.backgroundRunning.checked = backgroundRunning;
  if (runtimeSettingControls.startOnLogin) runtimeSettingControls.startOnLogin.checked = startOnLogin;
  const detail = error?.message || settings.warning;
  setText('runtime-settings-status', detail
    ? `Unavailable · ${detail}`
    : `Background ${backgroundRunning ? 'on' : 'off'} · start on login ${startOnLogin ? 'on' : 'off'}.`);
}

async function refreshRuntimeSettings() {
  if (!coreBridge || typeof coreBridge.runtimeSettings !== 'function') {
    renderRuntimeSettings(null, new Error('This JARVIS build does not expose runtime settings.'));
    return false;
  }
  try {
    renderRuntimeSettings(await coreBridge.runtimeSettings());
    return true;
  } catch (error) {
    renderRuntimeSettings(null, error);
    recordEvent('error', `Runtime settings: ${error.message || 'request failed'}`);
    return false;
  }
}

async function updateRuntimeSetting(key, enabled) {
  if (runtimeSettingsInFlight || !Object.hasOwn(runtimeSettingControls, key)) return false;
  if (!coreBridge || typeof coreBridge.updateRuntimeSettings !== 'function') {
    renderRuntimeSettings(null, new Error('This JARVIS build does not expose runtime settings.'));
    return false;
  }
  const previous = {
    backgroundRunning: runtimeSettingControls.backgroundRunning?.checked === true,
    startOnLogin: runtimeSettingControls.startOnLogin?.checked === true,
  };
  runtimeSettingsInFlight = true;
  Object.values(runtimeSettingControls).forEach((control) => {
    if (control) control.disabled = true;
  });
  try {
    renderRuntimeSettings(await coreBridge.updateRuntimeSettings({ [key]: enabled === true }));
    recordEvent('info', `Runtime setting changed: ${key}=${enabled === true}.`);
    return true;
  } catch (error) {
    renderRuntimeSettings(previous, error);
    recordEvent('error', `Runtime setting ${key}: ${error.message || 'request failed'}`);
    return false;
  } finally {
    runtimeSettingsInFlight = false;
    Object.values(runtimeSettingControls).forEach((control) => {
      if (control) control.disabled = false;
    });
  }
}

panelIdleSeconds = readPanelIdleSeconds();

function clearPanelCloseTimer() {
  if (!panelCloseTimer) return;
  clearTimeout(panelCloseTimer);
  panelCloseTimer = 0;
}

function armPanelCloseTimer() {
  clearPanelCloseTimer();
  if (active === 'assistant' || panelIdleSeconds === 0) return;
  panelCloseTimer = setTimeout(() => {
    panelCloseTimer = 0;
    if (active === 'assistant') return;
    if (modal?.classList.contains('open')) {
      armPanelCloseTimer();
      return;
    }
    openPage('assistant');
  }, panelIdleSeconds * 1000);
}

function syncPagesNavigation() {
  const dock = $('.dock-zone');
  const expanded = pagesNavigationExpanded === true;
  dock?.classList.toggle('pages-collapsed', !expanded);
  dock?.classList.toggle('pages-nav-open', expanded && active !== 'assistant');
  const pagesToggle = $('#pages-toggle');
  const toggleLabel = expanded ? 'Collapse Feature' : 'Expand Feature';
  pagesToggle?.setAttribute('aria-expanded', String(expanded));
  pagesToggle?.setAttribute('aria-label', toggleLabel);
  pagesToggle?.setAttribute('title', toggleLabel);
  const panelToggle = $('#pages-panel-toggle');
  const panelToggleLabel = expanded ? 'Hide Feature' : 'Show Feature';
  panelToggle?.setAttribute('aria-expanded', String(expanded));
  panelToggle?.setAttribute('aria-label', panelToggleLabel);
  panelToggle?.setAttribute('title', panelToggleLabel);
}

function setPagesNavigationExpanded(expanded) {
  pagesNavigationExpanded = expanded === true;
  syncPagesNavigation();
  if (pagesNavigationExpanded) animateFeatureSurface('navigation');
  else cancelFeatureTransition();
  if (active !== 'assistant') {
    if (pagesNavigationExpanded) clearPanelCloseTimer();
    else armPanelCloseTimer();
  }
  requestAnimationFrame(resize);
}

function motionIsReduced() {
  return lowMotionEnabled();
}

function syncTokenUsageNavigation() {
  $$('[data-page]').forEach((button) => {
    button.classList.toggle('active', button.dataset.page === active);
  });
}

function hideTokenUsageCard() {
  tokenUsageTransitionToken += 1;
  tokenUsageOpen = false;
  const card = $('#token-usage-card');
  if (card) {
    card.classList.remove('open');
    card.hidden = true;
  }
  syncTokenUsageNavigation();
}

function showTokenUsageCard({ animate = true } = {}) {
  const card = $('#token-usage-card');
  if (!card) return;
  tokenUsageTransitionToken += 1;
  const token = tokenUsageTransitionToken;
  tokenUsageOpen = true;
  card.hidden = false;
  card.classList.remove('open');
  syncTokenUsageNavigation();
  renderTokenUsageCard();
  if (!animate || motionIsReduced()) {
    card.classList.add('open');
    return;
  }
  requestAnimationFrame(() => {
    if (token !== tokenUsageTransitionToken || !tokenUsageOpen) return;
    card.classList.add('open');
  });
}

function toggleTokenUsageCard(force = null) {
  const next = force === null ? !tokenUsageOpen : force === true;
  if (next) {
    showTokenUsageCard();
  } else {
    hideTokenUsageCard();
  }
}

let pageTransitionToken = 0;
let featureTransitionToken = 0;

function cancelFeatureTransition() {
  featureTransitionToken += 1;
  $$('.action-dock.feature-nav-enter, .inspect-panel.feature-page-enter').forEach((element) => {
    element.getAnimations?.().forEach((animation) => {
      if (animation.animationName === 'feature-nav-enter' || animation.animationName === 'feature-page-enter') animation.cancel();
    });
    element.classList.remove('feature-nav-enter', 'feature-page-enter');
    void element.offsetWidth;
  });
}

function animateFeatureSurface(kind) {
  cancelFeatureTransition();
  if (motionIsReduced()) return;
  const target = kind === 'navigation' ? $('.action-dock') : $('#inspect-panel');
  const className = kind === 'navigation' ? 'feature-nav-enter' : 'feature-page-enter';
  if (!target) return;
  const token = featureTransitionToken;
  requestAnimationFrame(() => {
    if (token !== featureTransitionToken) return;
    target.classList.remove(className);
    void target.offsetWidth;
    let settled = false;
    const settle = () => {
      if (settled) return;
      settled = true;
      target.removeEventListener('animationend', settle);
      target.removeEventListener('animationcancel', settle);
      if (token === featureTransitionToken) target.classList.remove(className);
    };
    target.addEventListener('animationend', settle);
    target.addEventListener('animationcancel', settle);
    target.classList.add(className);
  });
}

function cancelPageViewTransition() {
  pageTransitionToken += 1;
  $$('.panel-view.page-view-enter, .inspect-head.page-header-enter').forEach((element) => {
    element.getAnimations?.().forEach((animation) => {
      if (animation.animationName === 'page-view-enter' || animation.animationName === 'page-header-enter') animation.cancel();
    });
    element.classList.remove('page-view-enter', 'page-header-enter');
    void element.offsetWidth;
  });
}

function animatePageView(view) {
  cancelPageViewTransition();
  if (!view || motionIsReduced()) return;
  const token = pageTransitionToken;
  requestAnimationFrame(() => {
    if (token !== pageTransitionToken || !view.classList.contains('active')) return;
    const header = $('.inspect-head');
    header?.classList.remove('page-header-enter');
    view.classList.remove('page-view-enter');
    if (header) void header.offsetWidth;
    void view.offsetWidth;
    let settled = false;
    const settle = () => {
      if (settled) return;
      settled = true;
      view.removeEventListener('animationend', settle);
      view.removeEventListener('animationcancel', settle);
      header?.removeEventListener('animationend', settle);
      header?.removeEventListener('animationcancel', settle);
      if (token !== pageTransitionToken) return;
      view.classList.remove('page-view-enter');
      header?.classList.remove('page-header-enter');
    };
    view.addEventListener('animationend', settle);
    view.addEventListener('animationcancel', settle);
    header?.addEventListener('animationend', settle);
    header?.addEventListener('animationcancel', settle);
    header?.classList.add('page-header-enter');
    view.classList.add('page-view-enter');
  });
}

function openPage(page, writeHash = true) {
  if (!pages[page] || (edition === 'internal-test' && !internalTestPages.has(page))) page = 'assistant';
  if (page === 'usage') showTokenUsageCard();
  const previousPage = active;
  active = page;
  setPagesNavigationExpanded(false);
  if (typeof syncAiConnectionControls === 'function') syncAiConnectionControls();
  const panelOpen = page !== 'assistant';
  if (panelOpen) armPanelCloseTimer();
  else clearPanelCloseTimer();
  $('#view-assistant')?.classList.add('active');
  $$('.panel-view').forEach((view) => view.classList.toggle('active', panelOpen && view.id === `view-${page}`));
  $$('[data-page]').forEach((button) => button.classList.toggle('active', button.dataset.page === page));
  syncTokenUsageNavigation();
  $('.dock-zone')?.classList.toggle('panel-open', panelOpen);
  const inspector = $('#inspect-panel');
  inspector?.toggleAttribute('hidden', !panelOpen);
  inspector?.classList.toggle('open', panelOpen);
  inspector?.setAttribute('aria-hidden', String(!panelOpen));
  $('#close-panel')?.setAttribute('tabindex', panelOpen ? '0' : '-1');
  const [title, subtitle, kicker] = pages[page];
  $('#page-title').textContent = title;
  $('#page-subtitle').textContent = subtitle;
  $('#page-kicker').textContent = kicker;
  if (!panelOpen) cancelPageViewTransition();
  else if (previousPage !== page) {
    animatePageView($(`#view-${page}`));
    animateFeatureSurface('page');
  }
  if (writeHash && location.hash !== `#${page}`) history.replaceState(null, '', `#${page}`);
  requestAnimationFrame(resize);
  sync();
  refreshPageData(page);
}

const aiActions = $('#ai-connection-actions');
const aiStatusControl = $('#ai-connection-status');
const aiDisconnectControl = $('#ai-disconnect');
const aiReconnectControl = $('#ai-reconnect');
const directProviderControl = $('#ai-direct-provider');
const directProviderRow = $('#ai-direct-provider-row');
const directModelControl = $('#ai-direct-model');
const directModelRow = $('#ai-direct-model-row');
const directBaseUrlControl = $('#ai-direct-base-url');
const directBaseUrlRow = $('#ai-direct-base-url-row');
const directProviderNote = $('#ai-direct-provider-note');
const directCompatibleModels = $('#ai-compatible-models');
const directCompatibleModelsNote = $('#ai-compatible-models-note');
const directCompatibleModelList = $('#ai-compatible-model-list');
const apiKeyInputControl = $('#ai-direct-api-key');
const apiConnectControl = $('#ai-api-connect');
let directProviderDraftDirty = false;
let directModelDraftDirty = false;
const directProviderInfo = Object.freeze({
  openai: Object.freeze({ model: 'gpt-5.6-luna', models: ['gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna'], note: 'OpenAI Responses API. The selected model must be available to this API account.', catalogNote: 'OpenAI Responses text models supported by this adapter. Your API account decides final availability.' }),
  gemini: Object.freeze({ model: 'gemini-3.8-flash', models: ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-3.1-pro-preview', 'gemini-3-flash-preview', 'gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite'], note: 'Google Gemini Interactions API. Text-only; JARVIS sends no tools or local capabilities.', catalogNote: 'Gemini Interactions text models compatible with JARVIS\' text-only request shape. Your API account decides final availability.' }),
  deepseek: Object.freeze({ model: 'deepseek-v4-flash', models: ['deepseek-v4-flash', 'deepseek-v4-pro'], note: 'DeepSeek OpenAI-compatible Chat Completions API. Text-only; JARVIS sends no tools or local capabilities.', catalogNote: 'DeepSeek Chat Completions text models supported by this adapter. Your API account decides final availability.' }),
  openai_compatible: Object.freeze({ model: '', models: [], note: 'Gateway must implement HTTPS OpenAI Chat Completions. Enter its base URL without /chat/completions and its provider-specific model ID.', catalogNote: 'No fixed model list: use only an ID listed by this gateway. JARVIS does not probe a gateway or assume API-key/model compatibility.' }),
});
const aiProviderLabels = Object.freeze({
  chatgpt_subscription: 'ChatGPT subscription',
  openai: 'OpenAI',
  gemini: 'Gemini',
  deepseek: 'DeepSeek',
  openai_compatible: 'OpenAI-compatible gateway',
});
if (aiActions) aiActions.hidden = true;
aiReconnectControl?.addEventListener('click', () => void refreshAiConnectionCheck());
apiConnectControl?.addEventListener('click', async () => {
  const key = apiKeyInputControl?.value.trim() || '';
  const provider = directProviderControl?.value || '';
  const model = directModelControl?.value.trim() || '';
  const baseUrl = directBaseUrlControl?.value.trim() || '';
  if (!key || !provider || !model || !coreOnline || !coreBridge?.aiDirectConfig) {
    setText('ai-connection-status', 'Choose a provider and model, then enter its API key while Core is online.');
    return;
  }
  apiConnectControl.disabled = true;
  try {
    const snapshot = await coreBridge.aiDirectConfig({ apiKey: key, provider, model, baseUrl });
    apiKeyInputControl.value = '';
    directProviderDraftDirty = false;
    directModelDraftDirty = false;
    applyAiConnection(snapshot?.ai || snapshot);
    setText('ai-connection-status', `${provider} configured for this Core session; send a request to verify access.`);
  } catch (error) {
    setText('ai-connection-status', `Direct API configuration failed · ${error.message || 'request failed'}`);
  } finally {
    apiConnectControl.disabled = false;
  }
});
function syncDirectProviderForm({ resetModel = false } = {}) {
  const provider = directProviderControl?.value || 'openai';
  const info = directProviderInfo[provider] || directProviderInfo.openai;
  if (resetModel && directModelControl) directModelControl.value = info.model;
  if ($('#ai-mode-setting')?.value === 'direct_api') {
    setText('ai-model-value', `${aiProviderLabels[provider] || provider} · ${directModelControl?.value.trim() || info.model || 'model ID required'}`);
  }
  if (directProviderNote) directProviderNote.textContent = info.note;
  if (directCompatibleModelsNote) directCompatibleModelsNote.textContent = info.catalogNote;
  if (directCompatibleModelList) {
    directCompatibleModelList.replaceChildren();
    for (const model of info.models) {
      const chip = document.createElement('code');
      chip.className = 'model-chip';
      chip.textContent = model;
      directCompatibleModelList.append(chip);
    }
  }
  if (directBaseUrlRow) directBaseUrlRow.hidden = provider !== 'openai_compatible';
}
directProviderControl?.addEventListener('change', () => {
  directProviderDraftDirty = true;
  directModelDraftDirty = false;
  syncDirectProviderForm({ resetModel: true });
  if (directBaseUrlControl && directProviderControl.value !== 'openai_compatible') directBaseUrlControl.value = '';
});
directModelControl?.addEventListener('input', () => {
  directModelDraftDirty = true;
});
const syncAiConnectionControls = (mode = $('#ai-mode-setting')?.value || 'managed_subscription') => {
  const directMode = mode === 'direct_api';
  if (aiActions) aiActions.hidden = active !== 'connections';
  if (aiReconnectControl) aiReconnectControl.hidden = mode !== 'managed_subscription';
  if (directProviderRow) directProviderRow.hidden = !directMode;
  if (directModelRow) directModelRow.hidden = !directMode;
  if (apiKeyInputControl) apiKeyInputControl.hidden = !directMode;
  if (directProviderNote) directProviderNote.hidden = !directMode;
  if (directCompatibleModels) directCompatibleModels.hidden = !directMode;
  if (apiConnectControl) apiConnectControl.hidden = !directMode;
  if (aiDisconnectControl) aiDisconnectControl.textContent = directMode
    ? 'Disconnect Direct API'
    : 'Disconnect ChatGPT';
  syncDirectProviderForm();
};
syncAiConnectionControls();

const pagesNav = $('.dock-nav');
const settingsPageButton = pagesNav?.querySelector('[data-page="settings"]');
if (pagesNav && settingsPageButton) pagesNav.append(settingsPageButton);
$$('[data-page]').forEach((button) => button.addEventListener('click', () => {
  openPage(button.dataset.page);
}));
$('#pages-toggle')?.addEventListener('click', () => setPagesNavigationExpanded(!pagesNavigationExpanded));
$('#pages-panel-toggle')?.addEventListener('click', () => setPagesNavigationExpanded(true));
if (edition === 'internal-test') {
  $$('[data-page]').forEach((button) => {
    if (!internalTestPages.has(button.dataset.page)) button.hidden = true;
  });
}
syncPagesNavigation();
addEventListener('hashchange', () => openPage(location.hash.slice(1) || 'assistant', false));
$('.dock-zone')?.addEventListener('pointerdown', () => {
  if (active !== 'assistant') armPanelCloseTimer();
});
$('.dock-zone')?.addEventListener('keydown', (event) => {
  if (event.key !== 'Tab' && event.key !== 'Enter' && event.key !== ' ') return;
  if (active !== 'assistant') armPanelCloseTimer();
});
$('.page-stack')?.addEventListener('scroll', () => {
  if (active !== 'assistant') armPanelCloseTimer();
}, { capture: true, passive: true });

let motionState = 'idle';
let paused = false;
let visible = true;
let raf = 0;
let clock = 0;
let last = 0;
let drawAt = 0;
let width = 1;
let height = 1;
let quality = 1;
let slow = 0;

const canvas = $('#core');
const context = canvas.getContext('2d');
const reduced = $('#reduced');
const pauseButton = $('#pause');
const media = matchMedia('(prefers-reduced-motion: reduce)');
lowMotionPreference = readLowMotionPreference();
syncMotionControls();

let hologram;
try {
  hologram = new window.HolographicCore();
} catch (error) {
  $('#quality').textContent = '2D fallback';
  console.warn(error);
}

function themeColorChannels(value) {
  const normalized = normalizeThemeColor(value);
  if (!normalized) return null;
  return [0, 2, 4].map((offset) => parseInt(normalized.slice(offset + 1, offset + 3), 16)).join(', ');
}

function themeColorRgba(value, alpha) {
  const channels = themeColorChannels(value);
  return channels ? `rgba(${channels}, ${alpha})` : null;
}

function cssColorToHex(value) {
  const normalized = normalizeThemeColor(value);
  if (normalized) return normalized;
  const match = String(value || '').trim().match(/^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)/i);
  if (!match) return null;
  const channels = match.slice(1, 4).map((part) => Math.max(0, Math.min(255, Math.round(Number(part)))));
  return `#${channels.map((part) => part.toString(16).padStart(2, '0')).join('').toUpperCase()}`;
}

function applyCustomThemeOverrides() {
  const root = document.documentElement;
  customThemeStyleVariables.forEach((variable) => root.style.removeProperty(variable));
  const set = (variable, value) => {
    if (value) root.style.setProperty(variable, value);
  };
  const background = customThemeOverrides.background;
  if (background) {
    set('--bg', background);
    set('--stage-bg', background);
    set('--panel-bg-bottom', background);
    set('--code-bg', background);
    set('--row-hover', background);
    set('--surface-deep-rgb', themeColorChannels(background));
  }
  const surface = customThemeOverrides.surface;
  if (surface) {
    const surfaceRgb = themeColorChannels(surface);
    set('--surface', surface);
    set('--surface-2', surface);
    set('--surface-3', surface);
    set('--surface-rgb', surfaceRgb);
    set('--button-bg', surface);
    set('--tooltip-bg', surface);
    set('--control-bg', surface);
    set('--toggle-bg', surface);
    set('--surface-hover', surface);
    set('--monitor-bg', themeColorRgba(surface, '.88'));
    set('--dock-bg', themeColorRgba(surface, '.94'));
    set('--panel-bg-top', themeColorRgba(surface, '.92'));
    set('--composer-bg', themeColorRgba(surface, '.96'));
  }
  const border = customThemeOverrides.border;
  if (border) {
    set('--line', border);
    set('--line-soft', themeColorRgba(border, '.38'));
    set('--border-strong', border);
    set('--select-border', border);
    set('--control-border', border);
    set('--nav-hover-border', border);
    set('--empty-border', border);
    set('--toggle-border', border);
    set('--composer-border', border);
    set('--code-border', themeColorRgba(border, '.55'));
  }
  const accent = customThemeOverrides.accent;
  if (accent) {
    const accentRgb = themeColorChannels(accent);
    set('--gold', accent);
    set('--amber', accent);
    set('--amber-dim', themeColorRgba(accent, '.55'));
    set('--accent-hot', accent);
    set('--scrollbar', accent);
    set('--accent-rgb', accentRgb);
    set('--warm-rgb', accentRgb);
    set('--orbit-rgb', accentRgb);
    set('--accent-glow', accent);
    set('--tag', accent);
    set('--control-active-border', accent);
    set('--nav-active-border', accent);
  }
  const text = customThemeOverrides.text;
  if (text) {
    set('--text', text);
    set('--brand', text);
    set('--gold-hot', text);
    set('--button-text', text);
    set('--message-text', text);
    set('--detail-value', text);
    set('--control-text', text);
    set('--control-active-text', text);
    set('--nav-text', text);
    set('--core-label', text);
  }
  const muted = customThemeOverrides.muted;
  if (muted) {
    set('--muted', muted);
    set('--quiet', muted);
    set('--caption', muted);
    set('--placeholder', muted);
    set('--caption-muted', muted);
    set('--detail-label', muted);
    set('--readout', muted);
    set('--control-muted', muted);
    set('--core-label-muted', muted);
    set('--code-text', muted);
  }
  const coreA = customThemeOverrides.coreA;
  const coreB = customThemeOverrides.coreB;
  if (coreA) {
    set('--core-color-a', coreA);
    set('--core-glow', themeColorRgba(coreA, '0'));
  }
  if (coreB) set('--core-color-b', coreB);
}

function cssHexToRgb(value) {
  const normalized = String(value || '').trim().replace(/^#/, '');
  if (!/^(?:[0-9a-f]{3}|[0-9a-f]{6})$/i.test(normalized)) return null;
  const expanded = normalized.length === 3
    ? normalized.split('').map((part) => `${part}${part}`).join('')
    : normalized;
  return [0, 2, 4].map((offset) => parseInt(expanded.slice(offset, offset + 2), 16) / 255);
}

function syncCorePalette() {
  if (!hologram || typeof hologram.setPalette !== 'function') return;
  const styles = getComputedStyle(document.documentElement);
  const first = cssHexToRgb(styles.getPropertyValue('--core-color-a'));
  const second = cssHexToRgb(styles.getPropertyValue('--core-color-b'));
  if (first && second) hologram.setPalette(first, second);
}

syncCorePalette();

function render(time) {
  if (hologram) {
    hologram.draw(context, width, height, time, motionState, quality);
    return;
  }
  context.clearRect(0, 0, width, height);
  const radius = Math.min(width, height) * 0.22;
  const gradient = context.createRadialGradient(width * 0.56, height * 0.55, 0, width * 0.56, height * 0.55, radius);
  const styles = getComputedStyle(document.documentElement);
  gradient.addColorStop(0, styles.getPropertyValue('--core-color-a').trim() || '#fff2c6');
  gradient.addColorStop(0.1, styles.getPropertyValue('--core-color-b').trim() || '#ffbd45');
  gradient.addColorStop(1, styles.getPropertyValue('--core-glow').trim() || '#ff980000');
  context.fillStyle = gradient;
  context.beginPath();
  context.arc(width * 0.56, height * 0.55, radius, 0, Math.PI * 2);
  context.fill();
}

function running() {
  return !paused && visible && !document.hidden;
}

function tick(stamp) {
  raf = 0;
  if (!running()) return;
  if (!last) last = stamp;
  const motionScale = lowMotionEnabled() ? 0.18 : 1;
  clock += Math.min((stamp - last) / 1000, 0.08) * motionScale;
  last = stamp;
  if (stamp - drawAt >= (quality < 1 ? 33 : 22)) {
    const started = performance.now();
    render(clock);
    slow = performance.now() - started > 24 ? slow + 1 : Math.max(0, slow - 1);
    if (slow > 15) {
      quality = 0.6;
      $('#quality').textContent = 'Adaptive low';
    }
    drawAt = stamp;
  }
  raf = requestAnimationFrame(tick);
}

function sync() {
  cancelAnimationFrame(raf);
  raf = 0;
  last = 0;
  $('#runtime-state').textContent = document.hidden || !visible
    ? 'Suspended'
    : paused
      ? 'Paused'
      : reduced.checked
        ? 'Low motion'
        : 'Running';
  render(clock);
  if (running()) raf = requestAnimationFrame(tick);
}

function resize() {
  const box = canvas.getBoundingClientRect();
  width = box.width;
  height = box.height;
  if (!width || !height) return;
  const dpr = Math.min(devicePixelRatio || 1, 1.75);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  context.setTransform(dpr, 0, 0, dpr, 0, 0);
  render(clock);
}

new ResizeObserver(resize).observe(canvas);
addEventListener('resize', resize);
new IntersectionObserver(([entry]) => {
  visible = entry.isIntersecting;
  sync();
}).observe(canvas);
document.addEventListener('visibilitychange', sync);
media.addEventListener('change', (event) => {
  if (lowMotionPreference === null) syncMotionControls();
  sync();
});
reduced.addEventListener('change', () => saveLowMotionPreference(reduced.checked));
pauseButton.addEventListener('click', () => {
  paused = !paused;
  pauseButton.textContent = paused ? 'Resume' : 'Pause';
  pauseButton.setAttribute('aria-pressed', String(paused));
  sync();
});

const motionLabels = {
  idle: ['Ready', 'Ready when you are.'],
  thinking: ['Thinking · local', 'Thinking…'],
  responding: ['Responding · local', 'Rendering the latest Core response.'],
  offline: ['Disconnected', 'JARVIS Core is unavailable.'],
};

function setMotionState(next) {
  if (!motionLabels[next]) next = 'idle';
  motionState = next;
  $('#core-state').textContent = next.toUpperCase();
  $$('[data-state]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.state === motionState)));
  render(clock);
}

$$('[data-state]').forEach((button) => button.addEventListener('click', () => setMotionState(button.dataset.state)));

const coreBridge = window.jarvisCore;
const coreRefreshControl = $('#core-refresh');
const coreReconnectControl = $('#core-reconnect');
const obsidianNameControl = $('#obsidian-vault-name');
const obsidianPathControl = $('#obsidian-vault-path');
const obsidianConnectControl = $('#obsidian-connect');
if (!window.JarvisConversationStore || typeof window.JarvisConversationStore.create !== 'function') {
  throw new Error('JARVIS conversation state is unavailable.');
}
const conversationStore = window.JarvisConversationStore.create();
const conversationElement = $('#messages');
const composer = $('#composer');
const composerInput = $('#prompt');
const composerSubmit = $('#composer button');
const composerBehavior = window.JarvisComposerBehavior;
if (!composerBehavior) throw new Error('JARVIS composer behavior is unavailable.');
const { focusInput, isFocusShortcut, isImeEnter } = composerBehavior;
const autoSpeechBehavior = window.JarvisAutoSpeech;
if (!autoSpeechBehavior || typeof autoSpeechBehavior.create !== 'function') {
  throw new Error('JARVIS automatic speech behavior is unavailable.');
}
const responseStreamBehavior = window.JarvisResponseStream;
if (!responseStreamBehavior
  || typeof responseStreamBehavior.DisplayPacer !== 'function'
  || typeof responseStreamBehavior.StreamProjector !== 'function'
  || typeof responseStreamBehavior.SpeechChunker !== 'function'
  || typeof responseStreamBehavior.detectSpeechLanguage !== 'function'
  || typeof responseStreamBehavior.isChineseVoice !== 'function'
  || typeof responseStreamBehavior.selectSpeechVoiceForText !== 'function') {
  throw new Error('JARVIS response stream behavior is unavailable.');
}
const markdownRenderer = window.JarvisMarkdownRenderer;
if (!markdownRenderer || typeof markdownRenderer.render !== 'function') {
  throw new Error('JARVIS Markdown renderer is unavailable.');
}
const renderMarkdown = markdownRenderer.render;
const normalizedToolStatus = window.JarvisConversationStore.normalizedToolStatus;
const conversationStorageKey = 'jarvis.foreground.conversation.v1';
const conversationDayStorageKey = 'jarvis.foreground.conversation.day.v1';
const clockLocaleStorageKey = 'jarvis.clock.locale.v1';
const responseLanguageStorageKey = 'jarvis.response.language.v1';
const conversationIdPattern = /^jarvis-[0-9a-f-]{36}$/;
let conversationId = null;
let conversationDay = null;
let installedSpeechVoices = [];
let selectedSpeechVoiceId = readSpeechVoicePreference();
let currentSpeechVoiceName = '';
let speechVoicesLoaded = false;
let speechLanguageFallbackNotified = false;
let coreOnline = false;
let healthInFlight = false;
let coreReconnectInFlight = false;
let runtimeSettingsInFlight = false;
let latestAiModeRequest = 0;
let selectedAiMode = 'managed_subscription';
let telemetryInFlight = false;
let sendInFlight = false;
let chatRequestSequence = 0;
let activeChatStream = null;
let activeChatRequest = null;
let currentSpeechAudio = null;
let currentSpeechAudioUrl = null;
let compositionActive = false;
const chatStreamHandlers = new Map();
const speechMetricById = new Map();
const eventRecords = [];
const toolResultRecords = [];
const tokenUsageRecords = [];
const surfaceInFlight = new Set();
let projectRegistry = {};
const rendererEventsStorageKey = `jarvis.foreground.events.v1.${edition}`;
const rendererToolsStorageKey = `jarvis.foreground.tool-results.v1.${edition}`;
const rendererUsageStorageKey = `jarvis.foreground.token-usage.v1.${edition}`;
const rendererAccountUsageStorageKey = `jarvis.foreground.chatgpt-account-usage.v1.${edition}`;
const maxTokenUsageRecords = 120;
const maxAccountUsageBuckets = 366;
let accountUsageSnapshot = null;

function readRendererArray(storageKey) {
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function readRendererObject(storageKey) {
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey) || 'null');
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function persistRendererRecords() {
  try {
    localStorage.setItem(rendererEventsStorageKey, JSON.stringify(eventRecords));
    // Pending confirmation is executable RAM state and must not survive a
    // window/Core restart. Keep only terminal tool records on disk.
    localStorage.setItem(
      rendererToolsStorageKey,
      JSON.stringify(toolResultRecords
        .filter((item) => normalizedToolStatus(item?.toolResult) !== 'awaiting_confirmation')),
    );
    localStorage.setItem(rendererUsageStorageKey, JSON.stringify(tokenUsageRecords));
    if (accountUsageSnapshot?.source === 'chatgpt_account'
      && accountUsageSnapshot.status === 'available') {
      localStorage.setItem(rendererAccountUsageStorageKey, JSON.stringify(accountUsageSnapshot));
    }
  } catch (error) {
    console.warn('JARVIS renderer records could not be persisted.', error);
  }
}

function normalizeTokenUsageCount(value) {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0) return null;
  return value;
}

function normalizeTokenUsageRecord(response, turn = null) {
  const usage = response?.usage;
  if (!usage || typeof usage !== 'object' || usage.source !== 'provider_reported') return null;
  const inputTokens = normalizeTokenUsageCount(usage.input_tokens);
  const outputTokens = normalizeTokenUsageCount(usage.output_tokens);
  const totalTokens = normalizeTokenUsageCount(usage.total_tokens);
  if (inputTokens === null && outputTokens === null && totalTokens === null) return null;
  return {
    at: new Date().toISOString(),
    turnId: typeof turn?.id === 'string' ? turn.id : '',
    provider: displayValue(response.provider, 'provider not reported').slice(0, 80),
    model: displayValue(response.model, 'model not reported').slice(0, 128),
    inputTokens,
    outputTokens,
    totalTokens,
  };
}

function normalizeAccountUsageDate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return '';
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value ? '' : value;
}

function normalizeAccountUsageSnapshot(response) {
  const candidate = response?.usage && typeof response.usage === 'object' && !Array.isArray(response.usage)
    ? response.usage
    : response;
  if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)
    || candidate.source !== 'chatgpt_account') return null;
  const rawStatus = typeof candidate.status === 'string' ? candidate.status.trim().toLowerCase() : '';
  const status = rawStatus === 'completed'
    ? 'available'
    : ['available', 'cached', 'stale', 'not_supported', 'disconnected', 'unavailable', 'failed', 'timeout', 'login_required', 'auth_context_unavailable', 'not_checked'].includes(rawStatus)
      ? rawStatus
      : candidate.success === true ? 'available' : 'unavailable';
  const rawSummary = candidate.summary;
  if (rawSummary !== null && rawSummary !== undefined
    && (typeof rawSummary !== 'object' || Array.isArray(rawSummary))) return null;
  const summary = rawSummary && typeof rawSummary === 'object' ? rawSummary : {};
  const readCount = (...keys) => {
    for (const key of keys) {
      const value = normalizeTokenUsageCount(summary[key]);
      if (value !== null) return value;
    }
    return null;
  };
  const rawBuckets = candidate.daily_usage_buckets ?? candidate.dailyUsageBuckets;
  if (rawBuckets !== null && rawBuckets !== undefined && !Array.isArray(rawBuckets)) return null;
  const seenDates = new Set();
  const dailyUsageBuckets = [];
  (rawBuckets || []).slice(0, maxAccountUsageBuckets).forEach((item) => {
    if (!item || typeof item !== 'object' || Array.isArray(item)) return;
    const startDate = normalizeAccountUsageDate(item.start_date ?? item.startDate);
    const tokens = normalizeTokenUsageCount(item.tokens);
    if (!startDate || tokens === null || seenDates.has(startDate)) return;
    seenDates.add(startDate);
    dailyUsageBuckets.push({ startDate, tokens });
  });
  dailyUsageBuckets.sort((left, right) => left.startDate.localeCompare(right.startDate));
  const checkedAtValue = candidate.checked_at ?? candidate.checkedAt;
  const checkedAt = typeof checkedAtValue === 'string' && !Number.isNaN(Date.parse(checkedAtValue))
    ? checkedAtValue
    : null;
  const detail = displayValue(candidate.detail || candidate.error, status === 'cached'
    ? 'Stored ChatGPT account usage; refresh to verify current values.'
    : 'ChatGPT account usage is unavailable.').slice(0, 320);
  return {
    source: 'chatgpt_account',
    status,
    detail,
    checkedAt,
    summary: {
      lifetimeTokens: readCount('lifetime_tokens', 'lifetimeTokens'),
      peakDailyTokens: readCount('peak_daily_tokens', 'peakDailyTokens'),
      longestRunningTurnSec: readCount('longest_running_turn_sec', 'longestRunningTurnSec'),
      currentStreakDays: readCount('current_streak_days', 'currentStreakDays'),
      longestStreakDays: readCount('longest_streak_days', 'longestStreakDays'),
    },
    dailyUsageBuckets,
  };
}

function restoreAccountUsageSnapshot() {
  const restored = normalizeAccountUsageSnapshot(readRendererObject(rendererAccountUsageStorageKey));
  if (restored && restored.status === 'available') {
    accountUsageSnapshot = {
      ...restored,
      status: 'cached',
      detail: 'Stored ChatGPT account usage; refresh to verify current values.',
    };
  }
}

function restoreTokenUsageRecords() {
  readRendererArray(rendererUsageStorageKey).forEach((record) => {
    if (!record || typeof record !== 'object') return;
    const inputTokens = normalizeTokenUsageCount(record.inputTokens);
    const outputTokens = normalizeTokenUsageCount(record.outputTokens);
    const totalTokens = normalizeTokenUsageCount(record.totalTokens);
    const at = typeof record.at === 'string' && !Number.isNaN(Date.parse(record.at)) ? record.at : '';
    if (!at || (inputTokens === null && outputTokens === null && totalTokens === null)) return;
    tokenUsageRecords.push({
      at,
      turnId: typeof record.turnId === 'string' ? record.turnId.slice(0, 100) : '',
      provider: displayValue(record.provider, 'provider not reported').slice(0, 80),
      model: displayValue(record.model, 'model not reported').slice(0, 128),
      inputTokens,
      outputTokens,
      totalTokens,
    });
  });
  if (tokenUsageRecords.length > maxTokenUsageRecords) {
    tokenUsageRecords.splice(0, tokenUsageRecords.length - maxTokenUsageRecords);
  }
}

function recordTokenUsage(response, turn = null) {
  const record = normalizeTokenUsageRecord(response, turn);
  if (!record) return false;
  if (record.turnId && tokenUsageRecords.some((item) => item.turnId === record.turnId)) return false;
  tokenUsageRecords.push(record);
  if (tokenUsageRecords.length > maxTokenUsageRecords) {
    tokenUsageRecords.splice(0, tokenUsageRecords.length - maxTokenUsageRecords);
  }
  persistRendererRecords();
  renderTokenUsageCard();
  return true;
}

function restoreRendererRecords() {
  const storedEvents = readRendererArray(rendererEventsStorageKey);
  storedEvents.forEach((record) => {
    if (!record || typeof record !== 'object') return;
    const level = typeof record.level === 'string' ? record.level : '';
    const message = typeof record.message === 'string' ? record.message : '';
    const at = typeof record.at === 'string' ? record.at : '';
    if (!['info', 'notice', 'error'].includes(level) || !message || !at) return;
    eventRecords.push({ level, message, at });
  });
  const storedTools = readRendererArray(rendererToolsStorageKey);
  storedTools.forEach((item) => {
    if (!item || typeof item !== 'object' || !item.toolResult || typeof item.toolResult !== 'object') return;
    if (normalizedToolStatus(item.toolResult) === 'awaiting_confirmation') return;
    toolResultRecords.push({
      turnId: typeof item.turnId === 'string' ? item.turnId : 'restored',
      toolResult: item.toolResult,
    });
  });
}

function setText(id, value) {
  const element = $(`#${id}`);
  if (element) element.textContent = value;
}

function displayValue(value, fallback = 'not reported') {
  if (value === null || value === undefined) return fallback;
  const text = String(value).trim();
  return text || fallback;
}

function formatCoreHealthTime() {
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date());
}

function setCoreHealthCheck(value) {
  setText('core-connection-checked', value);
}

function formatSurfaceResult(response) {
  if (!response || typeof response !== 'object') return displayValue(response, 'No result returned.');
  if (typeof response.result === 'string' && response.result.trim()) return response.result;
  if (typeof response.error === 'string' && response.error.trim()) return response.error;
  return JSON.stringify(response, null, 2);
}

function formatTokenUsageCount(value) {
  if (value === null || value === undefined) return '—';
  try {
    return new Intl.NumberFormat(undefined, {
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value);
  } catch {
    return Number(value).toLocaleString();
  }
}

function usageDayKey(value) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

function usageDayLabel(date) {
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

function formatTokenUsageK(value) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) return '—';
  if (value === 0) return '0';
  const kilo = value / 1000;
  if (kilo < 0.1) return '<0.1k';
  if (kilo < 10) return `${kilo.toFixed(1).replace(/\.0$/, '')}k`;
  if (kilo < 1000) return `${Math.round(kilo)}k`;
  const mega = kilo / 1000;
  return `${mega.toFixed(mega >= 10 ? 0 : 1).replace(/\.0$/, '')}M`;
}

function accountUsageDisplaySnapshot() {
  return selectedAiMode === 'managed_subscription'
    && accountUsageSnapshot
    && ['available', 'cached', 'stale'].includes(accountUsageSnapshot.status)
    ? accountUsageSnapshot
    : null;
}

function accountUsageRecords() {
  const snapshot = accountUsageDisplaySnapshot();
  if (!snapshot) return [];
  return snapshot.dailyUsageBuckets.map((bucket) => ({
    at: `${bucket.startDate}T12:00:00`,
    turnId: `account:${bucket.startDate}`,
    provider: 'ChatGPT account',
    model: 'account usage',
    inputTokens: null,
    outputTokens: null,
    totalTokens: bucket.tokens,
  }));
}

function usageRecordsForDisplay() {
  return selectedAiMode === 'managed_subscription'
    ? accountUsageRecords()
    : tokenUsageRecords;
}

function tokenUsageEmptyLabel() {
  return selectedAiMode === 'managed_subscription'
    ? accountUsageDisplaySnapshot() ? 'No ChatGPT account usage yet' : 'ChatGPT account usage unavailable'
    : 'No provider-reported usage yet';
}

function usageSeries(days = 14) {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const dates = Array.from({ length: days }, (_, index) => {
    const date = new Date(now);
    date.setDate(now.getDate() - (days - 1 - index));
    return date;
  });
  const buckets = new Map(dates.map((date) => [usageDayKey(date), {
    input: 0,
    output: 0,
    total: 0,
    hasInput: false,
    hasOutput: false,
    hasTotal: false,
  }]));
  usageRecordsForDisplay().forEach((record) => {
    const bucket = buckets.get(usageDayKey(record.at));
    if (!bucket) return;
    if (record.inputTokens !== null) {
      bucket.input += record.inputTokens;
      bucket.hasInput = true;
    }
    if (record.outputTokens !== null) {
      bucket.output += record.outputTokens;
      bucket.hasOutput = true;
    }
    if (record.totalTokens !== null) {
      bucket.total += record.totalTokens;
      bucket.hasTotal = true;
    }
  });
  return {
    dates,
    input: dates.map((date) => buckets.get(usageDayKey(date))?.input || 0),
    output: dates.map((date) => buckets.get(usageDayKey(date))?.output || 0),
    total: dates.map((date) => buckets.get(usageDayKey(date))?.total || 0),
    hasInput: dates.some((date) => buckets.get(usageDayKey(date))?.hasInput),
    hasOutput: dates.some((date) => buckets.get(usageDayKey(date))?.hasOutput),
    hasTotal: dates.some((date) => buckets.get(usageDayKey(date))?.hasTotal),
  };
}

function createUsageSvgElement(name, attributes = {}) {
  const svgNamespace = 'http' + '://www.w3.org/2000/svg';
  const element = document.createElementNS(svgNamespace, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
  return element;
}

function renderTokenUsageHeatmap(target = '#token-usage-heatmap') {
  const heatmap = typeof target === 'string' ? $(target) : target;
  if (!heatmap) return;
  heatmap.replaceChildren();
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const records = usageRecordsForDisplay();
  const sourceLabel = selectedAiMode === 'managed_subscription' ? 'ChatGPT account' : 'provider-reported';
  const values = [];
  for (let offset = 27; offset >= 0; offset -= 1) {
    const date = new Date(now);
    date.setDate(now.getDate() - offset);
    const key = usageDayKey(date);
    const value = records
      .filter((record) => usageDayKey(record.at) === key)
      .reduce((sum, record) => {
        const reported = record.totalTokens
          ?? ((record.inputTokens ?? 0) + (record.outputTokens ?? 0));
        return sum + reported;
      }, 0);
    values.push({ date, value });
  }
  const max = Math.max(...values.map((item) => item.value), 0);
  values.forEach(({ date, value }) => {
    const cell = document.createElement('span');
    const level = max > 0 && value > 0
      ? Math.min(4, Math.max(1, Math.ceil((value / max) * 4)))
      : 0;
    cell.dataset.level = String(level);
    cell.title = `${usageDayLabel(date)} · ${value ? `${formatTokenUsageCount(value)} reported tokens` : 'No reported usage'}`;
    cell.setAttribute('aria-label', cell.title);
    heatmap.append(cell);
  });
  heatmap.setAttribute('aria-label', max > 0
    ? `${values.filter((item) => item.value > 0).length} days with ${sourceLabel} token activity`
    : `No ${sourceLabel} token activity recorded`);
}

function renderTokenUsageChart(target = '#token-usage-chart') {
  const chart = typeof target === 'string' ? $(target) : target;
  if (!chart) return;
  chart.replaceChildren();
  const series = usageSeries(14);
  const hasComponents = series.hasInput || series.hasOutput;
  const lineSets = hasComponents
    ? [
      series.hasInput ? { values: series.input, className: 'usage-line-input' } : null,
      series.hasOutput ? { values: series.output, className: 'usage-line-output' } : null,
    ].filter(Boolean)
    : series.hasTotal
      ? [{ values: series.total, className: 'usage-line-total' }]
      : [];
  const presentValues = lineSets.flatMap((line) => line.values);
  const max = Math.max(...presentValues, 0);
  const xStart = 18;
  const xEnd = 352;
  const yTop = 10;
  const yBottom = 86;
  [yTop, (yTop + yBottom) / 2, yBottom].forEach((y) => {
    chart.append(createUsageSvgElement('line', {
      class: 'usage-grid',
      x1: xStart,
      x2: xEnd,
      y1: y,
      y2: y,
    }));
  });
  chart.append(createUsageSvgElement('line', {
    class: 'usage-axis',
    x1: xStart,
    x2: xStart,
    y1: yTop,
    y2: yBottom,
  }));
  chart.append(createUsageSvgElement('line', {
    class: 'usage-axis',
    x1: xStart,
    x2: xEnd,
    y1: yBottom,
    y2: yBottom,
  }));
  [
    { y: yTop, value: max },
    { y: (yTop + yBottom) / 2, value: max / 2 },
    { y: yBottom, value: 0 },
  ].forEach(({ y, value }) => {
    const label = createUsageSvgElement('text', {
      class: 'usage-y-label',
      x: xStart - 5,
      y: y + 3,
      'text-anchor': 'end',
    });
    label.textContent = formatTokenUsageK(value);
    chart.append(label);
  });
  if (!lineSets.length || max <= 0) {
    const empty = createUsageSvgElement('text', {
      class: 'usage-empty-label',
      x: (xStart + xEnd) / 2,
      y: 53,
    });
    empty.textContent = tokenUsageEmptyLabel();
    chart.append(empty);
  } else {
    lineSets.forEach(({ values, className }) => {
      const points = values.map((value, index) => {
        const x = xStart + ((xEnd - xStart) * index) / Math.max(values.length - 1, 1);
        const y = yBottom - ((value / max) * (yBottom - yTop));
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      }).join(' ');
      chart.append(createUsageSvgElement('polyline', { class: className, points }));
    });
  }
  [0, 6, 13].forEach((index) => {
    const x = xStart + ((xEnd - xStart) * index) / 13;
    chart.append(createUsageSvgElement('line', {
      class: 'usage-tick',
      x1: x,
      x2: x,
      y1: yBottom,
      y2: yBottom + 3,
    }));
  });
  const tooltip = createUsageSvgElement('g', { class: 'usage-tooltip', hidden: '' });
  const tooltipRect = createUsageSvgElement('rect', {
    class: 'usage-tooltip-bg',
    x: 0,
    y: 0,
    rx: 4,
    ry: 4,
    width: 80,
    height: 17,
  });
  const tooltipText = createUsageSvgElement('text', { class: 'usage-tooltip-text', x: 6, y: 11 });
  tooltip.append(tooltipRect, tooltipText);
  chart.append(tooltip);
  const hidePointTooltip = () => tooltip.setAttribute('hidden', '');
  const showPointTooltip = (label, x, y) => {
    const width = Math.max(64, Math.min(104, label.length * 4.25 + 12));
    const left = Math.max(2, Math.min(360 - width - 2, x - (width / 2)));
    const top = Math.max(1, y - 22);
    tooltipRect.setAttribute('width', String(width));
    tooltipText.textContent = label;
    tooltip.setAttribute('transform', `translate(${left.toFixed(2)} ${top.toFixed(2)})`);
    tooltip.removeAttribute('hidden');
  };
  if (lineSets.length && max > 0) {
    lineSets.forEach(({ values, className }) => {
      values.forEach((value, index) => {
        const x = xStart + ((xEnd - xStart) * index) / Math.max(values.length - 1, 1);
        const y = yBottom - ((value / max) * (yBottom - yTop));
        const label = `${usageDayLabel(series.dates[index])} · ${formatTokenUsageK(value)} tokens`;
        const point = createUsageSvgElement('circle', {
          class: `usage-point ${className.replace('usage-line-', 'usage-point-')}`,
          cx: x,
          cy: y,
          r: 2.5,
          tabindex: 0,
          focusable: 'true',
          'aria-label': label,
        });
        const title = createUsageSvgElement('title');
        title.textContent = label;
        point.append(title);
        point.addEventListener('pointerenter', () => showPointTooltip(label, x, y));
        point.addEventListener('pointerleave', hidePointTooltip);
        point.addEventListener('focus', () => showPointTooltip(label, x, y));
        point.addEventListener('blur', hidePointTooltip);
        chart.append(point);
      });
    });
  }
  [0, 6, 13].forEach((index) => {
    const x = xStart + ((xEnd - xStart) * index) / 13;
    const label = createUsageSvgElement('text', {
      class: 'usage-label',
      x,
      y: 104,
      'text-anchor': index === 0 ? 'start' : index === 13 ? 'end' : 'middle',
    });
    label.textContent = usageDayLabel(series.dates[index]);
    chart.append(label);
  });
  chart.setAttribute('aria-label', lineSets.length && max > 0
    ? `Token trend for the last 14 days; X axis by date; Y axis in tokens; peak ${formatTokenUsageCount(max)} ${selectedAiMode === 'managed_subscription' ? 'account' : 'reported'} tokens; focus a point for its date and value`
    : `No ${selectedAiMode === 'managed_subscription' ? 'ChatGPT account' : 'provider-reported'} token trend recorded`);
}

function formatAccountUsageCheckedAt(snapshot) {
  if (!snapshot?.checkedAt) return 'time unavailable';
  const checked = new Date(snapshot.checkedAt);
  return Number.isNaN(checked.getTime()) ? 'time unavailable' : checked.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function renderTokenUsageCard() {
  const account = accountUsageDisplaySnapshot();
  const displayRecords = usageRecordsForDisplay();
  const jarvisRecords = tokenUsageRecords;
  let totalValue = '—';
  let inputValue = '—';
  let outputValue = '—';
  let status = '';
  let badge = '';

  if (selectedAiMode === 'managed_subscription') {
    totalValue = formatTokenUsageCount(account?.summary?.lifetimeTokens);
    if (account?.status === 'available') {
      badge = 'LIVE · CHATGPT';
      status = `ChatGPT account usage · checked ${formatAccountUsageCheckedAt(account)}`;
    } else if (account) {
      badge = `${account.status.toUpperCase()} · CHATGPT`;
      status = `ChatGPT account usage ${account.status} · ${account.detail}`;
    } else {
      badge = 'UNAVAILABLE';
      status = 'ChatGPT account usage unavailable · Open the Usage page after Core is connected to refresh it.';
    }
  } else {
    const total = displayRecords.reduce((sum, record) => (
      record.totalTokens === null ? sum : sum + record.totalTokens
    ), 0);
    const input = displayRecords.reduce((sum, record) => (
      record.inputTokens === null ? sum : sum + record.inputTokens
    ), 0);
    const output = displayRecords.reduce((sum, record) => (
      record.outputTokens === null ? sum : sum + record.outputTokens
    ), 0);
    totalValue = displayRecords.some((record) => record.totalTokens !== null)
      ? formatTokenUsageCount(total)
      : '—';
    inputValue = displayRecords.some((record) => record.inputTokens !== null)
      ? formatTokenUsageCount(input)
      : '—';
    outputValue = displayRecords.some((record) => record.outputTokens !== null)
      ? formatTokenUsageCount(output)
      : '—';
    badge = displayRecords.length ? 'LIVE · LOCAL' : 'LOCAL · PROVIDER';
    if (!displayRecords.length) {
      status = 'No provider-reported token usage yet · Direct API usage appears after a response.';
    } else {
      const latest = displayRecords[displayRecords.length - 1];
      status = `${displayRecords.length} local request${displayRecords.length === 1 ? '' : 's'} · ${latest.provider} · ${latest.model}`;
    }
  }
  const jarvisTotal = jarvisRecords.reduce((sum, record) => (
    record.totalTokens === null ? sum : sum + record.totalTokens
  ), 0);
  const jarvisInput = jarvisRecords.reduce((sum, record) => (
    record.inputTokens === null ? sum : sum + record.inputTokens
  ), 0);
  const jarvisOutput = jarvisRecords.reduce((sum, record) => (
    record.outputTokens === null ? sum : sum + record.outputTokens
  ), 0);
  const widgetTotalValue = jarvisRecords.some((record) => record.totalTokens !== null)
    ? formatTokenUsageK(jarvisTotal)
    : '—';
  const widgetInputValue = jarvisRecords.some((record) => record.inputTokens !== null)
    ? formatTokenUsageK(jarvisInput)
    : '—';
  const widgetOutputValue = jarvisRecords.some((record) => record.outputTokens !== null)
    ? formatTokenUsageK(jarvisOutput)
    : '—';
  const widgetStatus = jarvisRecords.length
    ? `${jarvisRecords.length} JARVIS request${jarvisRecords.length === 1 ? '' : 's'} · provider-reported usage`
    : 'No JARVIS provider-reported usage yet';
  setText('token-usage-total', widgetTotalValue);
  setText('token-usage-input', widgetInputValue);
  setText('token-usage-output', widgetOutputValue);
  setText('token-usage-status', widgetStatus);
  setText('token-usage-page-total', totalValue);
  setText('token-usage-page-input', inputValue);
  setText('token-usage-page-output', outputValue);
  setText('usage-live-badge', badge);
  setText('token-usage-page-status', status);
  renderTokenUsageHeatmap('#token-usage-page-heatmap');
  renderTokenUsageChart('#token-usage-page-chart');
}

function accountUsageFailure(status, detail) {
  const existing = accountUsageSnapshot && ['available', 'cached', 'stale'].includes(accountUsageSnapshot.status)
    ? accountUsageSnapshot
    : null;
  if (existing) {
    return {
      ...existing,
      status: 'stale',
      detail: `Refresh failed · ${detail}`.slice(0, 320),
    };
  }
  return {
    source: 'chatgpt_account',
    status,
    detail: displayValue(detail, 'ChatGPT account usage is unavailable.').slice(0, 320),
    checkedAt: null,
    summary: {
      lifetimeTokens: null,
      peakDailyTokens: null,
      longestRunningTurnSec: null,
      currentStreakDays: null,
      longestStreakDays: null,
    },
    dailyUsageBuckets: [],
  };
}

async function refreshAccountUsage({ manual = false } = {}) {
  renderTokenUsageCard();
  if (selectedAiMode !== 'managed_subscription') return false;
  if (!coreOnline || !coreBridge || typeof coreBridge.aiUsage !== 'function') {
    accountUsageSnapshot = accountUsageFailure('unavailable', 'Core bridge is unavailable.');
    renderTokenUsageCard();
    if (manual) setText('token-usage-page-status', `ChatGPT account usage unavailable · ${accountUsageSnapshot.detail}`);
    return false;
  }
  if (surfaceInFlight.has('aiUsage')) return false;
  surfaceInFlight.add('aiUsage');
  const control = $('#usage-refresh');
  if (control) control.disabled = true;
  if (manual) setText('token-usage-page-status', 'Reading ChatGPT account usage…');
  try {
    const response = await coreBridge.aiUsage();
    const normalized = normalizeAccountUsageSnapshot(response?.usage || response);
    if (!normalized) throw new Error('Core returned an invalid account usage response.');
    accountUsageSnapshot = normalized;
    if (normalized.status === 'available') persistRendererRecords();
    renderTokenUsageCard();
    if (manual && normalized.status !== 'available') {
      recordEvent('notice', `ChatGPT account usage: ${normalized.detail}`);
    }
    return normalized.status === 'available';
  } catch (error) {
    accountUsageSnapshot = accountUsageFailure('unavailable', error.message || 'request failed');
    renderTokenUsageCard();
    recordEvent('error', `ChatGPT account usage: ${error.message || 'request failed'}`);
    return false;
  } finally {
    surfaceInFlight.delete('aiUsage');
    if (control) control.disabled = false;
  }
}

function formatDeviceStatus(response) {
  if (!response || typeof response !== 'object') return displayValue(response, 'No device status returned.');
  if (response.data && typeof response.data === 'object' && !Array.isArray(response.data)) {
    return JSON.stringify(response.data, null, 2);
  }
  return formatSurfaceResult(response);
}

function formatDeviceMetric(value, unit = '') {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'Unavailable';
  return `${value.toLocaleString()}${unit ? ` ${unit}` : ''}`;
}

function renderDeviceBattery(response) {
  const data = response?.data && typeof response.data === 'object' && !Array.isArray(response.data)
    ? response.data
    : null;
  const availability = data?.battery_available;
  setText(
    'device-battery-availability',
    availability === true ? 'Detected' : availability === false ? 'Not detected' : 'Unavailable',
  );
  setText(
    'device-battery-remaining-capacity',
    formatDeviceMetric(data?.battery_remaining_capacity_mwh, 'mWh'),
  );
  setText(
    'device-battery-full-charge-capacity',
    formatDeviceMetric(data?.battery_full_charge_capacity_mwh, 'mWh'),
  );
  setText(
    'device-battery-design-capacity',
    formatDeviceMetric(data?.battery_design_capacity_mwh, 'mWh'),
  );
  setText(
    'device-battery-cycle-count',
    formatDeviceMetric(data?.battery_cycle_count, 'cycles'),
  );

  let detailStatus = 'Detailed battery data is unavailable.';
  if (!data) {
    detailStatus = 'Battery details were not returned by Core.';
  } else if (availability === false) {
    detailStatus = 'No battery was detected on this computer.';
  } else if (data.battery_capacity_units === 'relative') {
    detailStatus = 'Windows reported relative battery units; mWh capacity is unavailable.';
  } else if (data.battery_capacity_available && data.battery_cycle_count_available) {
    detailStatus = 'Capacity and cycle count read through the Windows battery interface.';
  } else if (data.battery_capacity_available) {
    detailStatus = 'Remaining capacity is available; cycle count is not reported by this battery.';
  } else if (data.battery_cycle_count_available) {
    detailStatus = 'Cycle count is available; mWh capacity is not reported by this battery.';
  } else if (availability === true) {
    detailStatus = 'Basic battery state is available; detailed capacity and cycle count are unavailable.';
  }
  setText('device-battery-detail-status', detailStatus);
}

function renderEventList(listId, records, emptyText) {
  const list = $(`#${listId}`);
  if (!list) return;
  list.replaceChildren();
  if (!records.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = emptyText;
    list.append(empty);
    return;
  }
  records.slice().reverse().forEach((record) => {
    const article = document.createElement('article');
    article.className = 'instrument event-record';
    const readout = document.createElement('div');
    readout.className = 'readout';
    const title = document.createElement('strong');
    title.textContent = `${record.level.toUpperCase()} · ${record.message}`;
    const time = document.createElement('span');
    time.textContent = record.at;
    readout.append(title, time);
    article.append(readout);
    list.append(article);
  });
}

function renderEventRecords() {
  renderEventList('event-list', eventRecords.filter((record) => record.level !== 'error'), 'No runtime event recorded.');
}

function renderErrorRecords() {
  renderEventList('error-list', eventRecords.filter((record) => record.level === 'error'), 'No runtime error recorded.');
}

function renderEventSurfaces() {
  renderEventRecords();
  renderErrorRecords();
}

function recordEvent(level, message) {
  const normalized = displayValue(message, 'Unknown runtime event.');
  if (eventRecords.some((record) => record.level === level && record.message === normalized)) return;
  eventRecords.push({
    level,
    message: normalized,
    at: new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date()),
  });
  persistRendererRecords();
  renderEventSurfaces();
}

function renderToolResultsPage() {
  const list = $('#tool-results-list');
  const empty = $('#tool-results-empty');
  if (!list) return;
  list.replaceChildren();
  if (!toolResultRecords.length) {
    const placeholder = empty || document.createElement('div');
    placeholder.id = 'tool-results-empty';
    placeholder.className = 'empty';
    placeholder.textContent = 'No tool result has been recorded in this window.';
    list.append(placeholder);
    return;
  }
  toolResultRecords.slice().reverse().forEach(({ turnId, toolResult }) => {
    const status = normalizedToolStatus(toolResult);
    const card = document.createElement('details');
    card.className = 'tool-result live-tool-result';
    card.open = status === 'awaiting_confirmation';
    const summary = document.createElement('summary');
    summary.textContent = `Tool result · ${status} · ${displayValue(toolResult?.tool_name, 'Core tool')}`;
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(toolResult ?? {}, null, 2);
    const meta = document.createElement('small');
    meta.textContent = `Conversation turn ${turnId}`;
    card.append(summary, pre, meta);
    list.append(card);
  });
}

function renderHistory(payload, error = null) {
  const list = $('#history-list');
  if (!list) return;
  list.replaceChildren();
  const turns = Array.isArray(payload?.turns) ? payload.turns : [];
  setText('history-status', error
    ? `Unavailable · ${error.message || 'Core history could not be loaded.'}`
    : `${turns.length} stored ${turns.length === 1 ? 'turn' : 'turns'} · local Core memory`);
  if (error || !turns.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = error ? 'Core history is unavailable.' : 'No stored conversation history.';
    list.append(empty);
    return;
  }
  turns.slice().reverse().forEach((turn) => {
    const article = document.createElement('article');
    article.className = 'history-row';
    const user = document.createElement('strong');
    user.textContent = `You · ${displayValue(turn.created_at, 'time not reported')}`;
    const question = document.createElement('p');
    question.textContent = displayValue(turn.user, 'No user text.');
    const answer = document.createElement('p');
    answer.className = 'history-answer';
    answer.textContent = `JARVIS · ${displayValue(turn.assistant, 'No assistant text.')}`;
    article.append(user, question, answer);
    list.append(article);
  });
}

function renderConversationList(payload, error = null) {
  const list = $('#conversation-list');
  if (!list) return;
  list.replaceChildren();
  // The shared Core also keeps the legacy `primary` transcript for Flutter.
  // Electron can only open its own opaque foreground IDs, so do not render a
  // row that this renderer cannot safely reopen through the fixed bridge.
  const conversations = Array.isArray(payload?.conversations)
    ? payload.conversations.filter((conversation) => conversationIdPattern.test(String(conversation?.id || '')))
    : [];
  const detail = error?.message || 'Saved chats could not be loaded.';
  const versionMismatch = error && /No handler registered/i.test(detail);
  setText('conversations-status', error
    ? versionMismatch
      ? 'UI/Core version mismatch · close all JARVIS windows and reopen this shortcut.'
      : 'Unavailable · saved chats could not be loaded.'
    : `${conversations.length} saved ${conversations.length === 1 ? 'chat' : 'chats'} · local Core storage`);
  const status = $('#conversations-status');
  if (status) {
    status.title = error ? detail : '';
    if (error) status.setAttribute('aria-label', `History error: ${detail}`);
    else status.removeAttribute('aria-label');
  }
  if (error || !conversations.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = error ? 'Saved chats are unavailable.' : 'No saved chats yet. Send a message to create one.';
    list.append(empty);
    return;
  }
  conversations.forEach((conversation) => {
    const row = document.createElement('article');
    row.className = 'conversation-row';
    row.dataset.conversationId = displayValue(conversation.id, '');
    const title = document.createElement('h3');
    title.textContent = displayValue(conversation.title, 'JARVIS chat');
    const preview = document.createElement('p');
    preview.textContent = displayValue(conversation.last_preview, 'No assistant preview.');
    const meta = document.createElement('small');
    meta.textContent = `${Number(conversation.turn_count) || 0} turns · ${displayValue(conversation.updated_at, 'time not reported')}`;
    const open = document.createElement('button');
    open.className = 'button primary';
    open.type = 'button';
    open.textContent = 'Open chat';
    open.addEventListener('click', () => void openStoredConversation(conversation.id, open));
    row.append(title, preview, meta, open);
    list.append(row);
  });
}

function obsidianVaultIdFor(value) {
  const normalized = String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return normalized || 'obsidian-vault';
}

function renderVaults(payload, error = null) {
  const list = $('#vault-list');
  if (!list) return;
  list.replaceChildren();
  const vaults = Array.isArray(payload?.vaults) ? payload.vaults : [];
  setText('vault-status', error
    ? `Unavailable · ${error.message || 'Obsidian metadata could not be loaded.'}`
    : `${vaults.length} registered ${vaults.length === 1 ? 'vault' : 'vaults'} · metadata only`);
  setText('obsidian-connection-status', error
    ? `Unavailable · ${error.message || 'Obsidian connection check failed.'}`
    : vaults.length
      ? `Connected · ${vaults.length} registered ${vaults.length === 1 ? 'vault' : 'vaults'}.`
      : 'Not connected · enter a vault name and full folder path to reconnect.');
  if (error || !vaults.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = error ? 'Obsidian vault metadata is unavailable.' : 'No Obsidian vault has been registered.';
    list.append(empty);
    return;
  }
  vaults.forEach((vault) => {
    const row = document.createElement('div');
    row.className = 'readout';
    const name = document.createElement('strong');
    name.textContent = displayValue(vault.name, displayValue(vault.id, 'Unnamed vault'));
    const value = document.createElement('span');
    value.textContent = `${vault.enabled === false ? 'disabled' : 'enabled'} · ${Number(vault.indexed_chunks) || 0} chunks`;
    const disconnect = document.createElement('button');
    disconnect.className = 'button';
    disconnect.type = 'button';
    disconnect.textContent = 'Disconnect';
    disconnect.addEventListener('click', async () => {
      if (!coreBridge?.obsidianDisconnect) return;
      disconnect.disabled = true;
      try {
        await coreBridge.obsidianDisconnect(vault.id);
        setText('vault-status', `${displayValue(vault.name, vault.id)} disconnected · files were not deleted.`);
        setText('obsidian-connection-status', `${displayValue(vault.name, vault.id)} disconnected · enter its name and full folder path to reconnect.`);
        void refreshVaults();
      } catch (error) {
        disconnect.disabled = false;
        setText('vault-status', `Disconnect failed · ${error.message || 'request failed'}`);
        setText('obsidian-connection-status', `Disconnect failed · ${error.message || 'request failed'}`);
      }
    });
    row.append(name, value, disconnect);
    list.append(row);
  });
}

async function connectObsidianVault() {
  if (surfaceInFlight.has('vaults:connect')) return false;
  if (!coreOnline || !coreBridge?.obsidianConnect) {
    setText('obsidian-connection-status', coreOnline
      ? 'Core bridge unavailable; reconnect cannot start.'
      : 'Core is offline; reconnect Core before connecting Obsidian.');
    return false;
  }
  const name = obsidianNameControl?.value.trim() || '';
  const path = obsidianPathControl?.value.trim() || '';
  if (!name || !path) {
    setText('obsidian-connection-status', 'Enter a vault name and full folder path to connect or reconnect.');
    return false;
  }
  surfaceInFlight.add('vaults:connect');
  if (obsidianConnectControl) obsidianConnectControl.disabled = true;
  setText('obsidian-connection-status', 'Connecting Obsidian through Core…');
  try {
    await coreBridge.obsidianConnect({
      vaultId: obsidianVaultIdFor(name),
      name,
      path,
      defaultAccess: 'excluded',
    });
    if (obsidianNameControl) obsidianNameControl.value = '';
    if (obsidianPathControl) obsidianPathControl.value = '';
    setText('obsidian-connection-status', 'Obsidian registered · checking the live Core connection…');
    const refreshed = await refreshVaults();
    if (refreshed) recordEvent('info', 'Obsidian connection checked and registered.');
    return refreshed;
  } catch (error) {
    setText('obsidian-connection-status', `Connect failed · ${error.message || 'request failed'}`);
    recordEvent('error', `Obsidian connection: ${error.message || 'request failed'}`);
    return false;
  } finally {
    surfaceInFlight.delete('vaults:connect');
    if (obsidianConnectControl) obsidianConnectControl.disabled = false;
  }
}

function renderTasks(payload, error = null) {
  const list = $('#task-list');
  if (!list) return;
  list.replaceChildren();
  const tasks = Array.isArray(payload?.tasks) ? payload.tasks : [];
  setText('tasks-status', error
    ? `Unavailable · ${error.message || 'Task records could not be loaded.'}`
    : `${tasks.length} in-process ${tasks.length === 1 ? 'task' : 'tasks'} · read-only`);
  if (error || !tasks.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = error ? 'Core task records are unavailable.' : 'No task has been created in this Core session.';
    list.append(empty);
    return;
  }
  tasks.forEach((task) => {
    const row = document.createElement('article');
    row.className = 'task-row';
    const dot = document.createElement('i');
    dot.className = `dot ${task.status === 'completed' ? 'good' : ['failed', 'denied'].includes(task.status) ? 'dim' : ''}`;
    const body = document.createElement('div');
    const title = document.createElement('h3');
    title.textContent = displayValue(task.title, 'Untitled task');
    const detail = document.createElement('p');
    detail.textContent = `${displayValue(task.agent, 'Core')} · ${displayValue(task.created_at, 'time not reported')}`;
    body.append(title, detail);
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = displayValue(task.status, 'unknown').toUpperCase();
    row.append(dot, body, tag);
    if (task.error || task.result) {
      const result = document.createElement('p');
      result.className = 'task-result-copy';
      result.textContent = displayValue(task.error || task.result);
      row.append(result);
    }
    list.append(row);
  });
}

function renderProjects(payload, error = null) {
  const list = $('#project-list');
  const selector = $('#project-selector');
  if (!list || !selector) return;
  list.replaceChildren();
  selector.replaceChildren();
  projectRegistry = payload?.projects && typeof payload.projects === 'object' ? payload.projects : {};
  const names = Object.keys(projectRegistry).sort((a, b) => a.localeCompare(b));
  setText('projects-status', error
    ? `Unavailable · ${error.message || 'Project registry could not be loaded.'}`
    : `${names.length} registered ${names.length === 1 ? 'project' : 'projects'} · read-only actions`);
  if (error || !names.length) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = error ? 'Project registry is unavailable.' : 'No registered project is available.';
    list.append(empty);
    return;
  }
  names.forEach((name, index) => {
    const project = projectRegistry[name] || {};
    const row = document.createElement('div');
    row.className = 'readout';
    const label = document.createElement('strong');
    label.textContent = name;
    const value = document.createElement('span');
    value.textContent = `${displayValue(project.framework, 'Unknown')} · ${project.git ? 'Git' : 'no Git'}`;
    row.append(label, value);
    list.append(row);
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    if (index === 0) option.selected = true;
    selector.append(option);
  });
}

function applyAiConnection(snapshot) {
  const ai = snapshot && typeof snapshot === 'object' ? snapshot : {};
  const mode = displayValue(ai.mode, 'not_checked');
  const status = displayValue(ai.status, 'not_checked');
  const providerId = displayValue(ai.provider, mode === 'direct_api' ? 'not selected' : 'chatgpt_subscription');
  const provider = aiProviderLabels[providerId] || providerId;
  const model = displayValue(ai.model, 'not reported');
  setText('ai-model-value', `${provider} · ${model}`);
  setText('managed-ai-status', mode === 'managed_subscription' ? status : 'not selected');
  setText('direct-ai-status', mode === 'direct_api'
    ? status
    : ai.key_configured === true ? 'configured · not selected' : 'not configured');
  const modeControl = $('#ai-mode-setting');
  if (modeControl && ['managed_subscription', 'direct_api'].includes(mode)) {
    modeControl.value = mode;
    selectedAiMode = mode;
  }
  const canAdoptCoreDirectConfig = !directProviderDraftDirty && !directModelDraftDirty;
  if (mode === 'direct_api' && canAdoptCoreDirectConfig && directProviderControl && directProviderInfo[ai.provider]) {
    directProviderControl.value = ai.provider;
    if (directModelControl) directModelControl.value = model;
  }
  syncAiConnectionControls(mode);
  const detail = displayValue(ai.detail, 'Core has not checked this transport.');
  const connected = status === 'ready' || status === 'available';
  const explicitlyDisconnected = ai.user_disconnected === true;
  const currentState = explicitlyDisconnected
    ? `disconnected by you · ${mode}`
    : connected
    ? `connected · ${provider}`
    : mode === 'direct_api' && ai.key_configured === true
      ? `${provider} API key configured · access not verified`
      : `not connected · ${mode}`;
  setText('ai-connection-state', currentState);
  setText('ai-connection-status', `${mode} · ${detail}`);
  renderTokenUsageCard();
}

function applyAiStatus(snapshot) {
  const ai = snapshot && typeof snapshot === 'object' ? snapshot : null;
  const aiStatus = ai && typeof ai.status === 'string' && ai.status.trim() ? ai.status : 'not_checked';
  const model = ai && typeof ai.model === 'string' && ai.model.trim() ? ai.model : 'not reported';
  applyAiConnection(ai);
  setText('ai-status', aiStatus);
  setText('model-value', model);
  const ready = aiStatus === 'ready' || aiStatus === 'available';
  $('#ai-status').classList.toggle('ready', ready);
  $('#ai-status').classList.toggle('offline', !ready);
  const aiRow = $('#ai-status').closest('.status');
  aiRow?.classList.toggle('ready', ready);
  aiRow?.classList.toggle('offline', !ready);
  return ai;
}

async function refreshSurface(name, operation, apply, { statusId = '', label = 'Core' } = {}) {
  if (surfaceInFlight.has(name) || !coreBridge || typeof coreBridge[operation] !== 'function') {
    if (!coreBridge && statusId) setText(statusId, `${label} bridge unavailable.`);
    return false;
  }
  surfaceInFlight.add(name);
  try {
    const response = await coreBridge[operation]();
    apply(response);
    return true;
  } catch (error) {
    apply(null, error);
    recordEvent('error', `${label}: ${error.message || 'request failed'}`);
    return false;
  } finally {
    surfaceInFlight.delete(name);
  }
}

function refreshHistory() {
  return refreshSurface('history', 'conversationHistory', renderHistory, { label: 'Conversation history' });
}

function refreshConversationList() {
  return refreshSurface('conversation-list', 'conversationList', renderConversationList, { label: 'Saved chat history' });
}

function refreshVaults() {
  return refreshSurface('vaults', 'obsidianVaults', renderVaults, { label: 'Obsidian metadata' });
}

function refreshTasks() {
  return refreshSurface('tasks', 'tasks', renderTasks, { statusId: 'tasks-status', label: 'Task records' });
}

function refreshProjects() {
  return refreshSurface('projects', 'projects', renderProjects, { statusId: 'projects-status', label: 'Project registry' });
}

async function refreshProjectRegistry() {
  if (surfaceInFlight.has('projects:rescan') || !coreBridge || typeof coreBridge.projectRefresh !== 'function') {
    if (!coreBridge) setText('projects-status', 'Core bridge unavailable.');
    return false;
  }
  surfaceInFlight.add('projects:rescan');
  setText('projects-status', 'Rescanning registered roots through Core…');
  try {
    const response = await coreBridge.projectRefresh();
    if (response?.success === false) throw Object.assign(new Error(formatSurfaceResult(response)), { code: 'CORE_PROJECT_REFRESH_FAILED' });
    setText('projects-status', 'Registry refreshed · loading current projects…');
    await refreshProjects();
    recordEvent('info', 'Project registry refreshed.');
    return true;
  } catch (error) {
    setText('projects-status', `Unavailable · ${error.message || 'project registry refresh failed'}`);
    recordEvent('error', `Project registry: ${error.message || 'request failed'}`);
    return false;
  } finally {
    surfaceInFlight.delete('projects:rescan');
  }
}

async function refreshSystemInfo() {
  if (surfaceInFlight.has('systemInfo') || !coreBridge || typeof coreBridge.systemStatus !== 'function') {
    if (!coreBridge) setText('system-info-status', 'Core bridge unavailable.');
    return false;
  }
  surfaceInFlight.add('systemInfo');
  setText('system-info-status', 'Reading device status…');
  try {
    const response = await coreBridge.systemStatus();
    renderDeviceBattery(response);
    setText('system-info-result', formatDeviceStatus(response));
    setText('system-info-status', 'Read-only result · Core completed.');
    return true;
  } catch (error) {
    setText('system-info-result', formatCoreFailure(error));
    setText('system-info-status', 'Unavailable · no system result was reported.');
    recordEvent('error', `System info: ${error.message || 'request failed'}`);
    return false;
  } finally {
    surfaceInFlight.delete('systemInfo');
  }
}

async function runProjectAction(action) {
  const selector = $('#project-selector');
  const projectName = selector?.value || '';
  if (!projectName || !coreBridge) return;
  const path = $('#project-path')?.value?.trim() || '.';
  const keyword = $('#project-keyword')?.value?.trim() || '';
  const operation = {
    git: 'projectGitStatus',
    files: 'projectListFiles',
    read: 'projectReadFile',
    search: 'projectSearch',
  }[action];
  if (!operation || surfaceInFlight.has(`project:${action}`)) return;
  if ((action === 'read' && path === '.') || (action === 'search' && !keyword)) {
    setText('projects-status', action === 'read' ? 'Enter a project-relative file path.' : 'Enter a search keyword.');
    return;
  }
  surfaceInFlight.add(`project:${action}`);
  setText('projects-status', `Running ${action} through Core…`);
  try {
    const response = action === 'git'
      ? await coreBridge[operation](projectName)
      : action === 'files'
        ? await coreBridge[operation](projectName, path)
        : action === 'read'
          ? await coreBridge[operation](projectName, path)
          : await coreBridge[operation](projectName, keyword, path);
    setText('project-result', formatSurfaceResult(response));
    setText('projects-status', `Core completed · ${projectName}`);
  } catch (error) {
    setText('project-result', formatCoreFailure(error));
    setText('projects-status', `Unavailable · ${error.message || 'project action failed'}`);
    recordEvent('error', `Project ${action}: ${error.message || 'request failed'}`);
  } finally {
    surfaceInFlight.delete(`project:${action}`);
  }
}

function readSpeechVoicePreference() {
  try {
    return localStorage.getItem(speechVoiceStorageKey) || '';
  } catch {
    return '';
  }
}

function saveSpeechVoicePreference(voiceId) {
  selectedSpeechVoiceId = typeof voiceId === 'string' ? voiceId.trim() : '';
  try {
    if (selectedSpeechVoiceId) localStorage.setItem(speechVoiceStorageKey, selectedSpeechVoiceId);
    else localStorage.removeItem(speechVoiceStorageKey);
  } catch (error) {
    recordEvent('error', `Windows voice selection could not be saved: ${error.message || 'storage unavailable'}`);
  }
  syncSpeechVoiceSelection();
}

function selectedSpeechVoiceForRequest() {
  return selectedSpeechVoiceId || null;
}

function automaticSpeechVoiceForText(text) {
  const language = responseStreamBehavior.detectSpeechLanguage(text);
  const voiceId = responseStreamBehavior.selectSpeechVoiceForText(
    text,
    installedSpeechVoices,
    selectedSpeechVoiceId,
  );
  const hasChineseVoice = installedSpeechVoices.some((voice) => responseStreamBehavior.isChineseVoice(voice));
  if (language === 'zh' && speechVoicesLoaded && !hasChineseVoice && !speechLanguageFallbackNotified) {
    speechLanguageFallbackNotified = true;
    recordEvent(
      'error',
      'Chinese response detected, but no Chinese Windows voice package is installed; the selected voice remains active.',
    );
  }
  return voiceId;
}

function selectedSpeechVoiceLabel() {
  const selected = installedSpeechVoices.find((voice) => voice.id === selectedSpeechVoiceId);
  return selected?.name || (selectedSpeechVoiceId ? 'Unavailable voice package' : 'Windows default');
}

function syncSpeechVoiceSelection() {
  const select = $('#voice-package-setting');
  if (select) {
    select.value = selectedSpeechVoiceId;
    if (select.value !== selectedSpeechVoiceId) select.value = '';
  }
  const selectedLabel = selectedSpeechVoiceLabel();
  setText('voice-output-value', selectedSpeechVoiceId
    ? `${selectedLabel} · selected here`
    : `${currentSpeechVoiceName || 'Windows default'} · Windows default`);
}

function renderSpeechVoices(payload) {
  const rawVoices = Array.isArray(payload)
    ? payload
    : Array.isArray(payload?.voices)
      ? payload.voices
      : [];
  const seen = new Set();
  installedSpeechVoices = rawVoices
    .filter((voice) => voice && typeof voice === 'object')
    .map((voice) => ({
      id: typeof voice.id === 'string' ? voice.id.trim() : '',
      name: typeof voice.name === 'string' ? voice.name.trim() : '',
      language: typeof voice.language === 'string' ? voice.language.trim() : '',
    }))
    .filter((voice) => voice.id && voice.name && !seen.has(voice.id) && seen.add(voice.id));
  speechVoicesLoaded = true;
  speechLanguageFallbackNotified = false;

  const select = $('#voice-package-setting');
  if (select) {
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = currentSpeechVoiceName
      ? `Use Windows default · ${currentSpeechVoiceName}`
      : 'Use Windows default';
    select.replaceChildren(defaultOption);
    installedSpeechVoices.forEach((voice) => {
      const option = document.createElement('option');
      option.value = voice.id;
      option.textContent = voice.language ? `${voice.name} · ${voice.language}` : voice.name;
      select.append(option);
    });
    if (selectedSpeechVoiceId && !installedSpeechVoices.some((voice) => voice.id === selectedSpeechVoiceId)) {
      const unavailable = document.createElement('option');
      unavailable.value = selectedSpeechVoiceId;
      unavailable.textContent = 'Unavailable · refresh voice packages';
      select.append(unavailable);
    }
  }
  syncSpeechVoiceSelection();
  const chineseVoiceCount = installedSpeechVoices.filter((voice) => responseStreamBehavior.isChineseVoice(voice)).length;
  setText('voice-package-status', installedSpeechVoices.length
    ? `${installedSpeechVoices.length} Windows voice package${installedSpeechVoices.length === 1 ? '' : 's'} available.${chineseVoiceCount
      ? ' Chinese replies use an installed zh-CN voice automatically.'
      : ' No Chinese voice package was reported; the selected voice remains active.'}`
    : 'No Windows voice packages were reported. Chinese replies will use the selected voice.');
}

async function refreshSpeechSettings() {
  if (surfaceInFlight.has('speechSettings') || !coreBridge || typeof coreBridge.speechSettings !== 'function') {
    if (!coreBridge) setText('speech-settings-status', 'Core bridge unavailable.');
    return false;
  }
  surfaceInFlight.add('speechSettings');
  setText('speech-settings-status', 'Reading current Windows voice settings…');
  try {
    const settings = await coreBridge.speechSettings();
    currentSpeechVoiceName = displayValue(settings?.voice, 'not reported');
    const speed = settings?.speed === null || settings?.speed === undefined ? 'not reported' : String(settings.speed);
    const source = displayValue(settings?.source, 'Windows Speech');
    setText('speech-settings-value', `${currentSpeechVoiceName} · speed ${speed}`);
    setText('voice-source-value', source);
    syncSpeechVoiceSelection();
    setText('speech-settings-status', 'Core completed · current Windows voice settings loaded.');
    setText('voice-status', 'Core completed · Windows voice settings loaded.');
    return true;
  } catch (error) {
    setText('speech-settings-value', 'unavailable');
    setText('voice-output-value', 'unavailable');
    setText('voice-source-value', 'unavailable');
    setText('speech-settings-status', `Unavailable · ${error.message || 'voice settings failed'}`);
    setText('voice-status', `Unavailable · ${error.message || 'voice settings failed'}`);
    recordEvent('error', `Speech settings: ${error.message || 'request failed'}`);
    return false;
  } finally {
    surfaceInFlight.delete('speechSettings');
  }
}

async function refreshSpeechVoices() {
  if (surfaceInFlight.has('speechVoices') || !coreBridge || typeof coreBridge.speechVoices !== 'function') {
    setText('voice-package-status', coreBridge ? 'This JARVIS build does not expose Windows voice packages.' : 'Core bridge unavailable.');
    return false;
  }
  surfaceInFlight.add('speechVoices');
  setText('voice-package-status', 'Reading installed Windows voice packages…');
  try {
    const voices = await coreBridge.speechVoices();
    renderSpeechVoices(voices);
    setText('voice-status', 'Core completed · installed Windows voice packages loaded.');
    return true;
  } catch (error) {
    setText('voice-package-status', `Unavailable · ${error.message || 'voice packages failed'}`);
    setText('voice-status', `Unavailable · ${error.message || 'voice packages failed'}`);
    recordEvent('error', `Speech voices: ${error.message || 'request failed'}`);
    return false;
  } finally {
    surfaceInFlight.delete('speechVoices');
  }
}

async function previewSpeechVoice() {
  if (!coreBridge || typeof coreBridge.speakReply !== 'function') {
    setText('voice-package-status', 'Core speech bridge unavailable.');
    return false;
  }
  const control = $('#voice-test');
  if (control) control.disabled = true;
  setText('voice-package-status', `Testing ${selectedSpeechVoiceLabel()}…`);
  try {
    await coreBridge.speakReply('This is a Windows voice package preview.', selectedSpeechVoiceForRequest());
    setText('voice-package-status', `Core completed · ${selectedSpeechVoiceLabel()} preview started.`);
    return true;
  } catch (error) {
    setText('voice-package-status', `Unavailable · ${error.message || 'voice preview failed'}`);
    recordEvent('error', `Voice preview: ${error.message || 'request failed'}`);
    return false;
  } finally {
    if (control) control.disabled = false;
  }
}

function refreshPageData(page) {
  if (page === 'usage') {
    renderTokenUsageCard();
    void refreshAccountUsage({ manual: true });
    return;
  }
  if (page === 'core') {
    void refreshHealth();
    return;
  }
  if (!coreOnline) return;
  if (page === 'tasks') void refreshTasks();
  if (page === 'context') {
    void refreshSystemInfo();
  }
  if (page === 'working-context') {
    void refreshProjects();
  }
  if (page === 'history') void refreshConversationList();
  if (page === 'memory') void refreshHistory();
  if (page === 'knowledge') void refreshVaults();
  if (page === 'settings' || page === 'voice') {
    void refreshSpeechSettings();
    void refreshSpeechVoices();
  }
  if (page === 'settings') void refreshRuntimeSettings();
  if (page === 'events' || page === 'errors') renderEventSurfaces();
}

function normalizeTelemetryPercent(value) {
  if (value === null || value === undefined || value === '') return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) && numeric >= 0 && numeric <= 100 ? numeric : null;
}

function setTelemetryMetric(id, value) {
  const element = $(`#${id}`);
  if (!element) return;
  element.textContent = value === null ? '—' : `${value.toFixed(1)}%`;
}

function applyTelemetry(snapshot, error = null) {
  const data = snapshot && typeof snapshot === 'object' ? snapshot : null;
  const cpu = normalizeTelemetryPercent(data?.cpu_percent);
  const memory = normalizeTelemetryPercent(data?.memory_percent);
  const gpuValues = Array.isArray(data?.gpus)
    ? data.gpus.map((gpu) => normalizeTelemetryPercent(gpu?.utilization_percent)).filter((value) => value !== null)
    : [];
  const gpu = gpuValues.length
    ? gpuValues.reduce((total, value) => total + value, 0) / gpuValues.length
    : null;

  setTelemetryMetric('cpu-value', cpu);
  setTelemetryMetric('gpu-value', gpu);
  setTelemetryMetric('memory-value', memory);

  const hasTelemetry = cpu !== null || memory !== null || gpu !== null;
  const state = error || !hasTelemetry
    ? 'UNAVAILABLE'
    : gpu === null
      ? 'LIVE · GPU UNAVAILABLE'
      : 'LIVE · TELEMETRY';
  setText('telemetry-state', state);
  const monitor = $('.system-monitor-card');
  if (monitor) {
    monitor.dataset.telemetry = hasTelemetry ? (gpu === null ? 'partial' : 'live') : 'unavailable';
    monitor.title = error?.message || (gpu === null ? data?.gpu_error || '' : '');
  }
}

function markResponseMetric(metrics, key, value = null) {
  if (metrics && metrics[key] === null) {
    metrics[key] = Number.isFinite(value) ? value : performance.now();
  }
}

function updateAutoSpeechStatus(state) {
  const speechMetric = state?.current?.id ? speechMetricById.get(state.current.id) : null;
  if (speechMetric && state.current.state === 'ready') {
    markResponseMetric(speechMetric, 'firstTtsAudioReadyAt', state.current.audioReadyAt);
  }
  if (speechMetric && state.current.state === 'playing') {
    markResponseMetric(speechMetric, 'firstAudioPlaybackAt', state.current.playbackStartedAt);
  }
  const status = state?.error
    ? `Error · ${state.error}`
    : state?.state === 'off'
      ? 'Off · new replies stay text-only.'
      : ['buffering', 'synthesizing'].includes(state?.state)
        ? 'On · preparing the streamed response.'
        : state?.state === 'playing'
          ? 'On · reading the streamed response.'
          : state?.state === 'cancelled'
            ? 'On · speech cancelled for the latest response.'
        : state?.state === 'queued'
          ? `On · ${state.pending} speech chunk${state.pending === 1 ? '' : 's'} queued.`
          : 'On · streamed responses will be read automatically.';
  setText('auto-speak-status', status);
  setText('voice-auto-speech-status', status);
  const controls = [$('#auto-speak-setting'), $('#voice-auto-speech-setting')].filter(Boolean);
  controls.forEach((control) => {
    control.checked = state?.enabled === true;
    control.setAttribute('aria-label', state?.enabled ? 'Automatic speech on' : 'Automatic speech off');
  });
}

function stopSpeechPlayback() {
  const audio = currentSpeechAudio;
  currentSpeechAudio = null;
  if (audio) {
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
  }
  if (currentSpeechAudioUrl) {
    URL.revokeObjectURL(currentSpeechAudioUrl);
    currentSpeechAudioUrl = null;
  }
}

function playSpeechAudio(payload) {
  const encoded = payload?.audio_base64;
  const mimeType = typeof payload?.mime_type === 'string' && payload.mime_type
    ? payload.mime_type
    : 'audio/wav';
  if (typeof encoded !== 'string' || !encoded) {
    return Promise.reject(new Error('Automatic speech returned no audio data.'));
  }
  stopSpeechPlayback();
  const binary = atob(encoded);
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: mimeType }));
  const audio = new Audio(url);
  audio.preload = 'auto';
  currentSpeechAudio = audio;
  currentSpeechAudioUrl = url;
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (error = null) => {
      if (settled) return;
      settled = true;
      if (currentSpeechAudio === audio) {
        currentSpeechAudio = null;
        audio.removeAttribute('src');
        audio.load();
      }
      if (currentSpeechAudioUrl === url) {
        currentSpeechAudioUrl = null;
        URL.revokeObjectURL(url);
      }
      if (error) reject(error);
      else resolve();
    };
    audio.addEventListener('ended', () => finish());
    audio.addEventListener('error', () => finish(new Error('Automatic speech audio could not be played.')));
    Promise.resolve(audio.play()).catch((error) => finish(error));
  });
}

const autoSpeech = autoSpeechBehavior.create({
  synthesize: coreBridge && typeof coreBridge.synthesizeSpeech === 'function'
    ? (text, voiceId) => coreBridge.synthesizeSpeech(text, voiceId || selectedSpeechVoiceForRequest())
    : null,
  play: playSpeechAudio,
  stop: coreBridge && typeof coreBridge.stopSpeech === 'function'
    ? () => {
      stopSpeechPlayback();
      return coreBridge.stopSpeech();
    }
    : null,
  onState: updateAutoSpeechStatus,
});

function saveConversationId(value) {
  if (!conversationIdPattern.test(value)) throw new Error('JARVIS Core returned an invalid conversation ID.');
  try {
    localStorage.setItem(conversationStorageKey, value);
  } catch {
    throw new Error('This window could not persist the JARVIS conversation ID.');
  }
  conversationId = value;
}

function loadConversationId() {
  try {
    const value = localStorage.getItem(conversationStorageKey);
    return typeof value === 'string' && conversationIdPattern.test(value) ? value : null;
  } catch {
    return null;
  }
}

function localDayKey(value = new Date()) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function saveConversationDay(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error('JARVIS conversation day is invalid.');
  conversationDay = value;
  try {
    localStorage.setItem(conversationDayStorageKey, value);
  } catch (error) {
    console.warn(error);
  }
}

function loadConversationDay() {
  try {
    const value = localStorage.getItem(conversationDayStorageKey);
    return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : null;
  } catch {
    return null;
  }
}

function initializeConversationDay() {
  // Every Electron launch starts a fresh active chat. Saved IDs remain
  // available only through the explicit History -> Open chat action.
  conversationId = null;
  conversationDay = null;
}

initializeConversationDay();

function restorableConversationRecords(records) {
  return records.filter((record) => {
    if (!record || typeof record !== 'object') return false;
    if (record.status === 'awaiting_confirmation') return false;
    const toolResults = Array.isArray(record.tool_results) ? record.tool_results : [];
    return !toolResults.some((toolResult) => normalizedToolStatus(toolResult) === 'awaiting_confirmation');
  });
}

let conversationRestoreToken = 0;

function animateConversationRestore() {
  if (!conversationElement) return;
  conversationRestoreToken += 1;
  conversationElement.classList.remove('conversation-restore');
  if (motionIsReduced()) return;
  const token = conversationRestoreToken;
  requestAnimationFrame(() => {
    if (token !== conversationRestoreToken) return;
    conversationElement.classList.add('conversation-restore');
    conversationElement.addEventListener('animationend', () => {
      if (token === conversationRestoreToken) conversationElement.classList.remove('conversation-restore');
    }, { once: true });
  });
}

function restoreConversationView(payload, { preserveConversationId = true } = {}) {
  const records = Array.isArray(payload?.turns) ? payload.turns : [];
  const terminalRecords = restorableConversationRecords(records);
  conversationStore.restore(records);
  conversationElement.replaceChildren();
  conversationFollowTail = true;
  const restoredTurns = conversationStore.list();
  terminalRecords.forEach((record, index) => {
    const turn = restoredTurns[index];
    if (!turn) return;
    turn.userMessage = appendMessage('user', displayValue(record?.user, 'No user text.'), '', turn.id);
    turn.assistantMessage = appendMessage(
      'assistant',
      displayValue(record?.assistant, 'No assistant text.'),
      turn.assistant.label,
      turn.id,
    );
    if (Number.isFinite(Number(record?.response_time_ms))) {
      setResponseTime(turn.assistantMessage, Number(record.response_time_ms));
    }
    const storedResults = Array.isArray(record?.tool_results) ? record.tool_results : [];
    storedResults.forEach((toolResult) => {
      if (normalizedToolStatus(toolResult) === 'awaiting_confirmation') return;
      appendPersistedToolResult(toolResult, turn.id);
    });
  });
  if (!records.length) {
    appendInitialMessage('Core is ready. Send a message to begin.', '● Ready');
  }
  renderToolResultsPage();
  scheduleConversationScroll({ force: true });
  animateConversationRestore();
  if (!preserveConversationId) {
    conversationId = null;
    conversationDay = null;
  }
}

function appendPersistedToolResult(toolResult, turnId = 'restored') {
  if (!toolResult || typeof toolResult !== 'object') return false;
  if (normalizedToolStatus(toolResult) === 'awaiting_confirmation') return false;
  const serialized = JSON.stringify(toolResult);
  if (toolResultRecords.some((item) => item.turnId === turnId && JSON.stringify(item.toolResult) === serialized)) {
    return false;
  }
  toolResultRecords.push({ turnId, toolResult });
  return true;
}

async function openStoredConversation(id, trigger = null) {
  const normalizedId = typeof id === 'string' ? id.trim() : '';
  if (!conversationIdPattern.test(normalizedId) || !coreOnline || !coreBridge?.conversationOpen) return false;
  if (sendInFlight || conversationStore.hasPendingConfirmation()) {
    setText('conversations-status', 'Resolve the active request before opening another chat.');
    return false;
  }
  if (surfaceInFlight.has('conversation-open')) return false;
  surfaceInFlight.add('conversation-open');
  const openingRow = trigger?.closest('.conversation-row');
  const originalTriggerLabel = trigger?.textContent || 'Open chat';
  if (trigger) {
    trigger.disabled = true;
    trigger.textContent = 'Opening…';
  }
  openingRow?.classList.add('is-opening');
  try {
    const payload = await coreBridge.conversationOpen(normalizedId);
    saveConversationId(normalizedId);
    saveConversationDay(localDayKey());
    restoreConversationView(payload);
    openPage('assistant');
    recordEvent('info', 'Saved chat opened from History.');
    return true;
  } catch (error) {
    setText('conversations-status', `Open failed · ${error.message || 'saved chat could not be opened.'}`);
    recordEvent('error', `Saved chat open: ${error.message || 'request failed'}`);
    return false;
  } finally {
    trigger?.removeAttribute('disabled');
    if (trigger) trigger.textContent = originalTriggerLabel;
    openingRow?.classList.remove('is-opening');
    surfaceInFlight.delete('conversation-open');
  }
}

function startNewConversation() {
  if (sendInFlight || conversationStore.hasPendingConfirmation()) {
    setText('conversations-status', 'Resolve the active request before starting another chat.');
    return false;
  }
  conversationStore.newConversation();
  conversationElement.replaceChildren();
  conversationId = null;
  conversationDay = null;
  try {
    localStorage.removeItem(conversationStorageKey);
    localStorage.removeItem(conversationDayStorageKey);
  } catch (error) {
    recordEvent('error', `New chat state could not be cleared: ${error.message || 'storage unavailable'}`);
  }
  appendInitialMessage('Core is ready. Send a message to begin a new chat.', '● Ready');
  openPage('assistant');
  recordEvent('info', 'Started a new local chat.');
  return true;
}

function conversationAtBottom() {
  const distance = conversationElement.scrollHeight
    - conversationElement.scrollTop
    - conversationElement.clientHeight;
  return conversationElement.scrollHeight <= conversationElement.clientHeight || distance <= 32;
}

let conversationScrollFrame = 0;
let conversationFollowTail = true;

function cancelConversationScroll() {
  if (!conversationScrollFrame) return;
  cancelAnimationFrame(conversationScrollFrame);
  conversationScrollFrame = 0;
}

function scrollConversationToLatest() {
  const target = Math.max(0, conversationElement.scrollHeight - conversationElement.clientHeight);
  conversationElement.scrollTop = target;
  // Keep the native scroll API as a second path for Chromium builds where a
  // direct scrollTop assignment is coalesced during layout.
  conversationElement.scrollTo({ top: conversationElement.scrollHeight, behavior: 'auto' });
}

function scheduleConversationScroll({ force = false } = {}) {
  if (force) conversationFollowTail = true;
  cancelConversationScroll();
  conversationScrollFrame = requestAnimationFrame(() => {
    conversationScrollFrame = 0;
    if (!conversationFollowTail) return;
    scrollConversationToLatest();
    // A confirmation card or a newly measured reply can change the layout in
    // the first frame. Settle once more after that layout pass.
    conversationScrollFrame = requestAnimationFrame(() => {
      conversationScrollFrame = 0;
      if (conversationFollowTail) scrollConversationToLatest();
    });
  });
}

conversationElement.addEventListener('scroll', () => {
  if (conversationAtBottom()) {
    conversationFollowTail = true;
    return;
  }
  conversationFollowTail = false;
  cancelConversationScroll();
}, { passive: true });

function appendConversationNode(node, { force = false } = {}) {
  // Preserve the user's bottom anchor across a batch of synchronous DOM
  // inserts. The first insert can make the container overflow before its
  // scheduled frame runs; treating that pending follow state as authoritative
  // prevents the next insert from incorrectly disabling auto-scroll.
  const follow = force || conversationFollowTail || conversationAtBottom();
  conversationFollowTail = follow;
  conversationElement.append(node);
  if (follow) scheduleConversationScroll({ force });
}

function createJarvisAvatar() {
  const source = $('.brand svg');
  if (!source) throw new Error('JARVIS logo is unavailable.');
  const avatar = document.createElement('span');
  avatar.className = 'avatar assistant-avatar';
  avatar.setAttribute('aria-hidden', 'true');
  avatar.append(source.cloneNode(true));
  return avatar;
}

function appendMessage(role, text, stateLabel = '', turnId = '') {
  const article = document.createElement('article');
  article.className = `message ${role === 'user' ? 'from-user' : 'from-jarvis'}`;
  if (turnId) article.dataset.turnId = turnId;
  const body = document.createElement('div');
  const strong = document.createElement('strong');
  strong.textContent = role === 'user' ? 'You' : 'JARVIS';
  const state = document.createElement('span');
  state.textContent = stateLabel;
  const paragraph = document.createElement('div');
  paragraph.className = 'message-content';
  renderMarkdown(paragraph, text);
  const responseTime = document.createElement('small');
  responseTime.className = 'response-time';
  responseTime.hidden = true;
  body.append(strong, state, paragraph, responseTime);
  if (role !== 'user') article.append(createJarvisAvatar());
  article.append(body);
  appendConversationNode(article);
  return { element: article, paragraph, state, responseTime };
}

function setResponseTime(message, elapsedMs) {
  if (!message?.responseTime || !Number.isFinite(elapsedMs)) return;
  message.responseTime.hidden = false;
  message.responseTime.textContent = `Response time ${(Math.max(0, elapsedMs) / 1000).toFixed(1)}s`;
}

function updateMessage(message, text, stateLabel, status = '') {
  if (!message) return;
  message.state.textContent = stateLabel;
  renderMarkdown(message.paragraph, text);
  if (status) message.element.dataset.status = status;
  if (conversationFollowTail) scheduleConversationScroll();
}

function removeInitialMessage() {
  conversationElement.querySelector('.initial-message')?.remove();
}

function appendInitialMessage(text, stateLabel) {
  const message = appendMessage('assistant', text, stateLabel);
  message.element.classList.add('initial-message');
  message.state.id = 'reply-state';
  message.paragraph.id = 'reply';
  return message;
}

function createTurn(message) {
  removeInitialMessage();
  // Sending a new turn is an explicit request to see its latest response;
  // historical reading remains stable until the next user turn arrives.
  conversationFollowTail = true;
  const turn = conversationStore.begin(message);
  turn.userMessage = appendMessage('user', message, '', turn.id);
  turn.assistantMessage = appendMessage(
    'assistant',
    turn.assistant.text,
    turn.assistant.label,
    turn.id,
  );
  turn.confirmationControls = [];
  turn.confirmationCard = null;
  return turn;
}

function updateTurnAssistant(turn, text, stateLabel, status) {
  if (!conversationStore.isCurrent(turn)) return false;
  updateMessage(turn.assistantMessage, text, stateLabel, status);
  return true;
}

function appendToolResult(toolResult, turn) {
  if (!conversationStore.isCurrent(turn)) return null;
  const status = normalizedToolStatus(toolResult);
  appendPersistedToolResult(toolResult, turn.id);
  persistRendererRecords();
  renderToolResultsPage();
  recordEvent(status === 'completed' ? 'info' : 'notice', `Tool result ${status}.`);

  // Keep audit JSON in the dedicated Tool Results page, but keep the chat
  // transcript focused on the user-facing reply and required decision.
  if (status === 'denied') return null;

  if (status === 'awaiting_confirmation') {
    turn.confirmationCard?.remove();
    turn.confirmationCard = null;
    turn.confirmationControls = [];

    const card = document.createElement('div');
    card.className = 'confirmation-actions-only instrument';
    card.dataset.turnId = turn.id;
    card.dataset.status = status;
    card.setAttribute('role', 'group');
    card.setAttribute('aria-label', 'Confirmation actions');
    const actions = document.createElement('div');
    actions.className = 'confirmation-actions';
    const yes = document.createElement('button');
    yes.className = 'button primary';
    yes.type = 'button';
    yes.dataset.confirm = 'yes';
    yes.textContent = 'Yes, continue';
    const no = document.createElement('button');
    no.className = 'button';
    no.type = 'button';
    no.dataset.confirm = 'no';
    no.textContent = 'No, cancel';
    const decide = (decision) => {
      if (sendInFlight || !conversationStore.beginConfirmation(turn, decision)) return;
      setConfirmationControlsDisabled(turn, true);
      void sendCoreMessage(decision, { confirmationDecision: true, turn });
    };
    yes.addEventListener('click', () => {
      decide('yes');
    });
    no.addEventListener('click', () => {
      decide('no');
    });
    turn.confirmationControls.push(yes, no);
    actions.append(yes, no);
    card.append(actions);
    turn.confirmationCard = card;
    appendConversationNode(card, { force: true });
    updateComposerState();
    return card;
  }

  // Terminal tool details belong to the dedicated Tool Results page. Keeping
  // them out of the conversation preserves the assistant reply as the main
  // reading flow while the record above remains available for audit.
  return null;
}

function setConfirmationControlsDisabled(turn, disabled) {
  (turn?.confirmationControls || []).forEach((button) => {
    button.disabled = disabled;
  });
}

function clearConfirmationCard(turn) {
  if (!turn) return;
  turn.confirmationCard?.remove();
  turn.confirmationCard = null;
  turn.confirmationControls = [];
}

function formatCoreFailure(error) {
  const code = error?.code ? ` [${error.code}]` : '';
  return `Core request failed${code}: ${error?.message || 'Unknown Core error.'}`;
}

function applyHealth(snapshot) {
  const coreReady = snapshot && snapshot.core && snapshot.core.status === 'ready';
  const wasCoreOnline = coreOnline;
  coreOnline = coreReady;
  if (coreReady) recordEvent('info', 'Core health ready.');
  else recordEvent('error', 'Core health is unavailable.');
  setText('core-status', coreReady ? 'ready' : 'disconnected');
  setText('connection-value', coreReady ? 'loopback ready' : 'not connected');
  setText('core-connection-state', coreReady ? 'ready' : 'disconnected');
  setText('core-connection-status', coreReady
    ? 'Connected · local JARVIS Core is ready.'
    : 'Core is disconnected.');
  $('#core-status').classList.toggle('ready', coreReady);
  $('#core-status').classList.toggle('offline', !coreReady);
  const coreRow = $('#core-status').closest('.status');
  coreRow?.classList.toggle('ready', coreReady);
  coreRow?.classList.toggle('offline', !coreReady);

  const ai = snapshot && snapshot.ai && typeof snapshot.ai === 'object' ? snapshot.ai : null;
  applyAiStatus(ai);

  if (!coreReady) {
    setMotionState('offline');
    setText('reply-state', '● Disconnected');
    setText('reply', 'JARVIS Core is unavailable; no message was sent.');
  } else if (!conversationStore.list().length && !sendInFlight) {
    setMotionState('idle');
    setText('reply-state', '● Ready');
    setText('reply', 'Core is ready. Send a message to begin.');
  }
  updateComposerState();
  if (coreReady && !wasCoreOnline) {
    void refreshSpeechVoices();
  }
  if (coreReady && !wasCoreOnline && ai?.user_disconnected !== true) {
    refreshPageData(active);
    void refreshAiConnectionCheck();
    if (ai?.mode === 'managed_subscription') void refreshAccountUsage();
  }
}

async function refreshAiConnectionCheck() {
  if (!coreOnline || surfaceInFlight.has('aiCheck') || !coreBridge
    || typeof coreBridge.aiCheck !== 'function') {
    return false;
  }
  surfaceInFlight.add('aiCheck');
  updateComposerState();
  setText('ai-status', 'checking');
  $('#ai-status').classList.remove('ready', 'offline');
  $('#ai-status').closest('.status')?.classList.remove('ready', 'offline');
  const selectedMode = $('#ai-mode-setting')?.value;
  setText('ai-connection-status', selectedMode === 'direct_api'
    ? 'Direct API automatic check is not run; an explicit request is required.'
    : 'Checking managed AI transport…');
  setText('managed-ai-status', selectedMode === 'direct_api' ? 'not selected' : 'checking…');
  try {
    const response = await coreBridge.aiCheck();
    const ai = applyAiStatus(response?.ai || response);
    if (response?.verification === 'direct_api_inference_not_run') {
      setText('ai-connection-status', `${displayValue(ai?.provider, 'Direct API')} · automatic check skipped; send an explicit request to verify.`);
    } else {
      setText('ai-connection-status', `${displayValue(ai?.mode, 'managed_subscription')} · ${displayValue(ai?.detail, 'transport check completed.')}`);
    }
    recordEvent('info', 'AI transport check completed without an inference probe.');
    return true;
  } catch (error) {
    setText('managed-ai-status', 'unavailable');
    setText('ai-connection-status', `Unavailable · ${error.message || 'AI transport check failed.'}`);
    recordEvent('error', `AI transport check: ${error.message || 'request failed'}`);
    return false;
  } finally {
    surfaceInFlight.delete('aiCheck');
    updateComposerState();
  }
}

async function refreshHealth({ manual = false } = {}) {
  if (coreReconnectInFlight && !manual) return false;
  if (healthInFlight || !coreBridge || typeof coreBridge.health !== 'function') {
    if (manual && healthInFlight) setText('core-connection-status', 'Core health check is already running.');
    if (!coreBridge) {
      setCoreHealthCheck('unavailable');
      applyHealth(null);
      setText('reply', 'The approved Core bridge is unavailable.');
      setText('core-connection-status', 'Refresh unavailable · the approved Core bridge is missing.');
    }
    return false;
  }
  healthInFlight = true;
  setCoreHealthCheck('checking…');
  if (manual) setText('core-connection-status', 'Refreshing local Core health…');
  try {
    const snapshot = await coreBridge.health();
    const wasCoreOnline = coreOnline;
    applyHealth(snapshot);
    if (manual) {
      setText('core-connection-status', coreOnline
        ? 'Connected · local JARVIS Core is ready.'
        : 'Refresh completed · Core is disconnected.');
    }
    if (coreOnline) {
      if (!wasCoreOnline) void refreshConversationList();
      // Keep the managed transport status self-healing on launch/reconnect.
      // The Core endpoint performs only its existing non-inference handshake;
      // Direct API remains explicitly unverified until a user request.
      const aiStatus = snapshot?.ai?.status;
      if (aiStatus !== 'ready' && aiStatus !== 'available'
        && snapshot?.ai?.user_disconnected !== true) {
        void refreshAiConnectionCheck();
      }
    }
  } catch (error) {
    coreOnline = false;
    applyHealth(null);
    setText('reply', formatCoreFailure(error));
    setText('core-connection-status', `Refresh failed · ${error.message || 'request failed'}`);
    recordEvent('error', `Core health: ${error.message || 'request failed'}`);
    return false;
  } finally {
    healthInFlight = false;
    setCoreHealthCheck(formatCoreHealthTime());
  }
  return true;
}

async function reconnectCoreFromUi() {
  if (coreReconnectInFlight) return false;
  if (healthInFlight) {
    setText('core-connection-status', 'Core health check is already running; try Reconnect again when it finishes.');
    return false;
  }
  if (!coreBridge || typeof coreBridge.reconnect !== 'function') {
    setCoreHealthCheck('unavailable');
    setText('core-connection-status', 'Reconnect unavailable · this build does not expose Core reconnect.');
    recordEvent('error', 'Core reconnect bridge is unavailable.');
    return false;
  }
  coreReconnectInFlight = true;
  setCoreHealthCheck('reconnecting…');
  if (coreRefreshControl) coreRefreshControl.disabled = true;
  if (coreReconnectControl) {
    coreReconnectControl.disabled = true;
    coreReconnectControl.textContent = 'Reconnecting…';
  }
  setText('core-connection-status', 'Reconnecting local Core…');
  try {
    const snapshot = await coreBridge.reconnect();
    applyHealth(snapshot);
    if (snapshot?.core?.status !== 'ready') {
      setText('core-connection-status', 'Reconnect returned a non-ready Core state.');
      recordEvent('error', 'Core reconnect returned a non-ready health snapshot.');
      return false;
    }
    setText('core-connection-status', 'Reconnected · local JARVIS Core is ready.');
    recordEvent('info', 'Core reconnect completed.');
    return true;
  } catch (error) {
    coreOnline = false;
    applyHealth(null);
    setText('reply', formatCoreFailure(error));
    setText('core-connection-status', `Reconnect failed · ${error.message || 'request failed'}`);
    recordEvent('error', `Core reconnect: ${error.message || 'request failed'}`);
    return false;
  } finally {
    coreReconnectInFlight = false;
    setCoreHealthCheck(formatCoreHealthTime());
    if (coreRefreshControl) coreRefreshControl.disabled = false;
    if (coreReconnectControl) {
      coreReconnectControl.disabled = false;
      coreReconnectControl.textContent = 'Reconnect Core';
    }
  }
}

async function refreshTelemetry() {
  if (telemetryInFlight || !coreBridge || typeof coreBridge.telemetry !== 'function') {
    if (!coreBridge) applyTelemetry(null, new Error('The approved Core bridge is unavailable.'));
    return;
  }
  telemetryInFlight = true;
  try {
    applyTelemetry(await coreBridge.telemetry());
  } catch (error) {
    applyTelemetry(null, error);
    recordEvent('error', `Telemetry: ${error.message || 'request failed'}`);
    console.warn(error);
  } finally {
    telemetryInFlight = false;
  }
}

async function createCoreConversation() {
  if (!coreOnline) throw Object.assign(new Error('JARVIS Core is offline.'), { code: 'CORE_OFFLINE' });
  const created = await coreBridge.createConversation();
  const id = created && typeof created.conversation_id === 'string'
    ? created.conversation_id
    : created && typeof created.id === 'string'
      ? created.id
      : '';
  saveConversationId(id);
  return id;
}

async function ensureConversation() {
  if (conversationId) return conversationId;
  const id = await createCoreConversation();
  saveConversationDay(localDayKey());
  return id;
}

function createResponseMetrics() {
  return {
    requestReceivedAt: performance.now(),
    firstModelTokenAt: null,
    firstTextRenderedAt: null,
    firstSpeechChunkCreatedAt: null,
    firstTtsAudioReadyAt: null,
    firstAudioPlaybackAt: null,
    responseCompletedAt: null,
  };
}

function responseMetricsSnapshot(metrics) {
  const snapshot = { ...metrics };
  const delta = (from, to) => (
    Number.isFinite(snapshot[from]) && Number.isFinite(snapshot[to])
      ? Math.max(0, snapshot[to] - snapshot[from])
      : null
  );
  snapshot.timeToFirstModelTokenMs = delta('requestReceivedAt', 'firstModelTokenAt');
  snapshot.timeToFirstTextRenderedMs = delta('requestReceivedAt', 'firstTextRenderedAt');
  snapshot.timeToFirstSpeechChunkCreatedMs = delta('requestReceivedAt', 'firstSpeechChunkCreatedAt');
  snapshot.timeToFirstTtsAudioReadyMs = delta('requestReceivedAt', 'firstTtsAudioReadyAt');
  snapshot.timeToFirstAudioPlaybackMs = delta('requestReceivedAt', 'firstAudioPlaybackAt');
  snapshot.modelTokenToTextRenderedMs = delta('firstModelTokenAt', 'firstTextRenderedAt');
  snapshot.textRenderedToSpeechChunkMs = delta('firstTextRenderedAt', 'firstSpeechChunkCreatedAt');
  snapshot.speechChunkToTtsReadyMs = delta('firstSpeechChunkCreatedAt', 'firstTtsAudioReadyAt');
  snapshot.ttsReadyToAudioPlaybackMs = delta('firstTtsAudioReadyAt', 'firstAudioPlaybackAt');
  snapshot.totalResponseMs = delta('requestReceivedAt', 'responseCompletedAt');
  return snapshot;
}

function renderStreamDisplay(stream, text) {
  if (stream.cancelled || stream.settled || activeChatStream !== stream || text === stream.lastDisplay) return false;
  stream.lastDisplay = text;
  if (!updateTurnAssistant(stream.turn, text || 'Thinking…', '● Responding · streaming', 'streaming')) return false;
  stream.hasRenderedDisplay = Boolean(text);
  markResponseMetric(stream.metrics, 'firstTextRenderedAt');
  return true;
}

function queueStreamDisplay(stream, text) {
  if (stream.cancelled || stream.settled || activeChatStream !== stream) return;
  stream.displayPacer.setTarget(text);
}

function cancelStreamDisplayFrame(stream) {
  if (!stream) return;
  if (stream.displayFrame !== null) {
    cancelAnimationFrame(stream.displayFrame);
    stream.displayFrame = null;
  }
  stream.pendingDisplay = '';
  stream.displayPacer?.cancel();
}

async function enqueueStreamSpeech(stream, speechText, { flush = false } = {}) {
  if (!autoSpeech.isEnabled() || stream.cancelled) return;
  const chunks = speechText ? stream.chunker.push(speechText) : [];
  if (flush) chunks.push(...stream.chunker.flush());
  for (const chunk of chunks) {
    if (stream.cancelled || !autoSpeech.isEnabled()) return;
    const speechId = `${stream.turn.id}:speech:${++stream.speechSequence}`;
    speechMetricById.set(speechId, stream.metrics);
    markResponseMetric(stream.metrics, 'firstSpeechChunkCreatedAt');
    try {
      await autoSpeech.enqueue(speechId, chunk, { voiceId: stream.speechVoiceId });
    } catch (error) {
      // Speech is deliberately isolated from the text stream. The visible
      // response remains valid when one synthesis/playback request fails.
      recordEvent('error', `Automatic speech: ${error.message || 'chunk failed'}`);
    }
  }
}

function resolveStreamSpeechVoice(stream, text) {
  if (stream.speechVoiceResolved || !String(text || '').trim()) return stream.speechVoiceId;
  stream.speechVoiceId = automaticSpeechVoiceForText(text);
  stream.speechVoiceResolved = true;
  return stream.speechVoiceId;
}

function streamEventError(event) {
  const detail = typeof event?.error === 'string'
    ? event.error
    : event?.error?.message || 'JARVIS Core ended the response stream.';
  const error = new Error(detail);
  error.code = event?.error?.code || event?.status || 'CORE_STREAM_FAILED';
  error.status = event?.error?.status || null;
  return error;
}

async function handleChatStreamEvent(stream, event) {
  if (stream.cancelled || stream.settled || activeChatStream !== stream) return;
  if (!event || typeof event !== 'object') throw new Error('JARVIS Core returned an invalid stream event.');

  if (event.type === 'start') return;
  if (event.type === 'delta') {
    if (typeof event.text !== 'string' || !event.text) return;
    markResponseMetric(stream.metrics, 'firstModelTokenAt');
    const projected = stream.projector.append(event.text);
    queueStreamDisplay(stream, projected.display);
    resolveStreamSpeechVoice(stream, projected.display);
    await enqueueStreamSpeech(stream, projected.speechDelta);
    return;
  }
  if (event.type === 'error') throw streamEventError(event);
  if (event.type === 'end') {
    if (!stream.completed) throw new Error('JARVIS Core ended the response stream without a response.');
    return;
  }
  if (event.type !== 'complete') throw new Error('JARVIS Core returned an unknown stream event.');

  const response = event.response;
  if (!response || typeof response !== 'object') throw new Error('JARVIS Core returned an invalid completed response.');
  const projected = stream.projector.finish();
  queueStreamDisplay(stream, projected.display);
  resolveStreamSpeechVoice(stream, projected.display || response.reply || response.speech);
  const outcome = renderChatResponse(response, stream.turn, { speak: false, updateAssistant: false });
  if (!outcome) {
    throw new Error('JARVIS returned a completed response for an inactive turn.');
  }
  markResponseMetric(stream.metrics, 'responseCompletedAt');
  response.timings = {
    ...(response.timings || {}),
    stream_metrics: responseMetricsSnapshot(stream.metrics),
  };
  setResponseTime(stream.turn.assistantMessage, stream.metrics.responseCompletedAt - stream.metrics.requestReceivedAt);
  stream.completed = true;
  const hasBufferedSpeech = typeof stream.chunker.hasPendingText === 'function'
    && stream.chunker.hasPendingText();
  const terminalSpeech = stream.speechSequence === 0
    && !hasBufferedSpeech
    && typeof response.speech === 'string'
    && response.speech.trim()
    ? response.speech
    : projected.speechDelta;
  await enqueueStreamSpeech(stream, terminalSpeech, { flush: true });
  await stream.displayPacer.drain();
  if (stream.cancelled || stream.settled) return;
  updateTurnAssistant(stream.turn, outcome.reply, outcome.label, outcome.awaiting
    ? 'awaiting_confirmation'
    : outcome.denied
      ? 'denied'
      : outcome.failed
        ? 'failed'
        : outcome.completed
          ? 'completed'
          : 'replied');
  response.timings.stream_metrics = responseMetricsSnapshot(stream.metrics);
  stream.resolve(response);
}

function consumeChatStream(turn, message, id, metrics, outputLanguage = resolveResponseLanguage()) {
  const stream = {
    id: `chat-${crypto.randomUUID?.() || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`}`,
    turn,
    message,
    conversationId: id,
    metrics,
    projector: new responseStreamBehavior.StreamProjector(),
    chunker: new responseStreamBehavior.SpeechChunker(),
    displayPacer: null,
    lastDisplay: '',
    pendingDisplay: '',
    displayFrame: null,
    hasRenderedDisplay: false,
    speechSequence: 0,
    speechVoiceId: null,
    speechVoiceResolved: false,
    eventChain: Promise.resolve(),
    settled: false,
    completed: false,
    cancelled: false,
  };
  stream.displayPacer = new responseStreamBehavior.DisplayPacer({
    charsPerSecond: 42,
    tickMs: 50,
    onUpdate: (text) => renderStreamDisplay(stream, text),
  });
  let resolveStream;
  let rejectStream;
  stream.promise = new Promise((resolve, reject) => {
    resolveStream = resolve;
    rejectStream = reject;
  });
  stream.resolve = (value) => {
    if (stream.settled) return;
    stream.settled = true;
    chatStreamHandlers.delete(stream.id);
    if (activeChatStream === stream) activeChatStream = null;
    resolveStream(value);
  };
  stream.reject = (error) => {
    if (stream.settled) return;
    cancelStreamDisplayFrame(stream);
    stream.settled = true;
    chatStreamHandlers.delete(stream.id);
    if (activeChatStream === stream) activeChatStream = null;
    rejectStream(error);
  };
  activeChatStream = stream;
  chatStreamHandlers.set(stream.id, (event) => {
    stream.eventChain = stream.eventChain
      .then(() => handleChatStreamEvent(stream, event))
      .catch((error) => stream.reject(error));
  });
  Promise.resolve()
    .then(() => coreBridge.startChatStream(stream.id, message, id, outputLanguage))
    .catch((error) => stream.reject(error));
  return stream;
}

if (coreBridge && typeof coreBridge.onChatStream === 'function') {
  coreBridge.onChatStream((payload) => {
    const streamId = payload?.streamId;
    const handler = typeof streamId === 'string' ? chatStreamHandlers.get(streamId) : null;
    if (handler) handler(payload.event);
  });
}

async function cancelActiveResponseForNewMessage() {
  const stream = activeChatStream;
  if (autoSpeech.isEnabled()) autoSpeech.cancel('Speech cancelled for the latest response.');
  if (stream) {
    stream.cancelled = true;
    cancelStreamDisplayFrame(stream);
    stream.reject(new Error('Response cancelled for a newer message.'));
    if (coreBridge && typeof coreBridge.cancelChatStream === 'function') {
      try {
        await coreBridge.cancelChatStream(stream.id);
      } catch (error) {
        recordEvent('error', `Cancel response: ${error.message || 'request failed'}`);
      }
    }
  }
}

function markTurnCancelled(turn) {
  if (!turn || !conversationStore.isCurrent(turn)) return;
  const outcome = conversationStore.applyCancellation(turn);
  if (!outcome.accepted) return;
  updateTurnAssistant(turn, outcome.text || 'This response was cancelled for a newer message.', '● Cancelled', 'cancelled');
  setConfirmationControlsDisabled(turn, true);
}

function renderChatResponse(response, turn, { speak = true, updateAssistant = true } = {}) {
  const outcome = conversationStore.applyResponse(turn, response);
  if (!outcome.accepted) return false;
  recordTokenUsage(response, turn);
  if (selectedAiMode === 'managed_subscription' && coreOnline) void refreshAccountUsage();
  if (!outcome.awaiting) {
    setConfirmationControlsDisabled(turn, true);
    clearConfirmationCard(turn);
  }
  const textReplyCompleted = outcome.toolResults.length === 0
    && typeof response?.reply === 'string'
    && Boolean(response.reply.trim());
  const shouldSpeak = (outcome.completed || textReplyCompleted || outcome.awaiting)
    && !outcome.failed
    && !outcome.denied;
  if (shouldSpeak && speak) {
    const speechText = typeof response?.speech === 'string' && response.speech.trim()
      ? response.speech
      : outcome.reply;
    const speechKey = `${turn.id}:${outcome.awaiting ? 'confirmation' : 'reply'}`;
    void autoSpeech.enqueue(speechKey, speechText, {
      voiceId: automaticSpeechVoiceForText(outcome.reply || speechText),
    });
  }
  if (updateAssistant) {
    updateTurnAssistant(turn, outcome.reply, outcome.label, outcome.awaiting
      ? 'awaiting_confirmation'
      : outcome.denied
        ? 'denied'
        : outcome.failed
          ? 'failed'
          : outcome.completed
            ? 'completed'
            : 'replied');
  }
  outcome.toolResults.forEach((toolResult) => appendToolResult(toolResult, turn));
  if (!outcome.awaiting && coreOnline) void refreshConversationList();
  // A response (especially a confirmation card) is the newest content. Keep
  // the controls reachable even when the prior transcript was scrolled up.
  scheduleConversationScroll({ force: true });
  if (outcome.awaiting) {
    setMotionState('thinking');
  } else if (outcome.failed || outcome.denied) {
    setMotionState('idle');
  } else {
    setMotionState('responding');
  }
  updateComposerState();
  return outcome;
}

function updateComposerState() {
  const input = composerInput;
  const submit = composerSubmit;
  const pending = conversationStore.hasPendingConfirmation();
  const checkingAi = surfaceInFlight.has('aiCheck');
  // Keep the draft field editable while a request is in flight; only the send action is gated.
  input.disabled = pending;
  submit.disabled = !coreOnline || pending || checkingAi;
  input.placeholder = coreOnline
    ? 'Ask a question or describe a task…'
    : 'Core disconnected — draft here; reconnect before sending…';
  submit.title = checkingAi
    ? 'Wait for the AI connection check to finish'
    : !coreOnline
    ? 'Connect JARVIS Core first'
    : pending
      ? 'Resolve the pending confirmation first'
      : '';
}

function showTurnFailure(turn, message, preserveConfirmation = false) {
  const outcome = conversationStore.applyFailure(turn, message, { preserveConfirmation });
  if (!outcome.accepted) return false;
  updateTurnAssistant(turn, message, '● Review result', 'failed');
  setConfirmationControlsDisabled(turn, !outcome.preserveConfirmation);
  scheduleConversationScroll({ force: true });
  return true;
}

async function sendCoreMessage(message, options = {}) {
  const normalized = typeof message === 'string' ? message.trim() : '';
  if (!normalized || (!options.confirmationDecision && surfaceInFlight.has('aiCheck'))) return;
  let turn = options.turn || null;
  let requestToken = null;
  if (options.confirmationDecision) {
    if (!conversationStore.isCurrent(turn) || !turn.confirmationInFlight) return;
  } else {
    if (conversationStore.hasPendingConfirmation()) return;
    requestToken = ++chatRequestSequence;
    const previousRequest = activeChatRequest;
    if (previousRequest && !previousRequest.finished) {
      previousRequest.superseded = true;
      markTurnCancelled(previousRequest.turn);
    }
    await cancelActiveResponseForNewMessage();
    if (requestToken !== chatRequestSequence) return;
    turn = createTurn(normalized);
    activeChatRequest = { token: requestToken, turn, finished: false, superseded: false };
  }
  sendInFlight = true;
  if (options.confirmationDecision) {
    conversationFollowTail = true;
    turn.confirmationDecisionMessage = appendMessage('user', normalized, '', turn.id);
  }
  setMotionState('thinking');
  updateComposerState();
  if (!coreOnline) {
    showTurnFailure(
      turn,
      'Core request failed [CORE_OFFLINE]: JARVIS Core is offline. Start the existing JARVIS Core shortcut and try again.',
      Boolean(options.confirmationDecision),
    );
    setMotionState('idle');
    sendInFlight = false;
    updateComposerState();
    return;
  }
  const requestStartedAt = performance.now();
  const metrics = createResponseMetrics();
  try {
    const id = await ensureConversation();
    if (requestToken !== null && requestToken !== chatRequestSequence) return;
    const stream = consumeChatStream(turn, normalized, id, metrics, resolveResponseLanguage());
    if (requestToken !== null && activeChatRequest) activeChatRequest.stream = stream;
    const response = await stream.promise;
    if (requestToken !== null && requestToken !== chatRequestSequence) return;
    if (!response?.timings?.stream_metrics) {
      response.timings = {
        ...(response.timings || {}),
        stream_metrics: responseMetricsSnapshot(metrics),
      };
    }
    const measuredResponseMs = response?.timings?.stream_metrics?.totalResponseMs;
    setResponseTime(
      turn.assistantMessage,
      Number.isFinite(measuredResponseMs) ? measuredResponseMs : performance.now() - requestStartedAt,
    );
  } catch (error) {
    if (requestToken !== null && requestToken !== chatRequestSequence) return;
    showTurnFailure(turn, formatCoreFailure(error), Boolean(options.confirmationDecision));
    setResponseTime(turn.assistantMessage, performance.now() - requestStartedAt);
    setMotionState('idle');
  } finally {
    if (requestToken === null || requestToken === chatRequestSequence) sendInFlight = false;
    if (requestToken !== null && activeChatRequest?.token === requestToken) {
      activeChatRequest.finished = true;
      activeChatRequest = null;
    }
    updateComposerState();
  }
}

composerInput.addEventListener('compositionstart', () => {
  compositionActive = true;
});
composerInput.addEventListener('compositionend', () => {
  compositionActive = false;
});
composerInput.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter') return;
  if (isImeEnter(event, compositionActive)) {
    event.preventDefault();
    return;
  }
  event.preventDefault();
  composer.requestSubmit();
});

composer.addEventListener('submit', (event) => {
  event.preventDefault();
  if (compositionActive) return;
  const input = composerInput;
  const value = input.value.trim();
  if (!value || conversationStore.hasPendingConfirmation()
    || surfaceInFlight.has('aiCheck')) return;
  if (!coreOnline) {
    setMotionState('offline');
    // The draft is kept in the composer while Core is offline.
    setText('reply-state', '● Disconnected');
    setText('reply', 'JARVIS Core is unavailable; reconnect before sending. Your draft remains in the composer.');
    return;
  }
  input.value = '';
  sendCoreMessage(value);
});

const modal = $('#demo-modal');

function resolveClockLocale() {
  try {
    return localStorage.getItem(clockLocaleStorageKey) === 'zh-CN' ? 'zh-CN' : 'en-US';
  } catch {
    return 'en-US';
  }
}

function refreshLocalClock() {
  const now = new Date();
  const time = new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(now);
  const date = new Intl.DateTimeFormat(resolveClockLocale(), {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(now);
  setText('local-time', time);
  setText('local-date', date);
}

function syncLocaleSetting() {
  const control = $('#locale-setting');
  if (!control) return;
  const locale = resolveClockLocale();
  control.value = locale;
  setText('locale-status', locale === 'zh-CN'
    ? '中文日期格式 · saved locally.'
    : 'English date format · active.');
}

function resolveResponseLanguage() {
  try {
    return localStorage.getItem(responseLanguageStorageKey) === 'zh-CN' ? 'zh-CN' : 'en';
  } catch {
    return 'en';
  }
}

function syncResponseLanguageSetting() {
  const control = $('#response-language-setting');
  if (!control) return;
  const language = resolveResponseLanguage();
  control.value = language;
  setText('response-language-status', language === 'zh-CN'
    ? 'Chinese replies · active for new messages.'
    : 'English replies · active for new messages.');
}

function syncThemeSetting() {
  const control = $('#theme-setting');
  if (!control) return;
  const theme = themeKeys.has(document.documentElement.dataset.theme)
    ? document.documentElement.dataset.theme
    : 'amber';
  control.value = theme;
  setText('theme-status', `${themeLabels[theme]} · active in this window.`);
  syncThemePaletteControls();
}

function applyTheme(value) {
  const theme = themeKeys.has(value) ? value : 'amber';
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(themeStorageKey, theme);
  } catch (error) {
    console.warn(error);
  }
  applyCustomThemeOverrides();
  syncCorePalette();
  syncThemeSetting();
  sync();
}

function themePaletteValue(key) {
  const field = themePaletteFields[key];
  if (!field) return '#000000';
  if (customThemeOverrides[key]) return customThemeOverrides[key];
  return cssColorToHex(getComputedStyle(document.documentElement).getPropertyValue(field.cssVariable)) || '#000000';
}

function syncThemePaletteControls() {
  const overrideCount = Object.keys(customThemeOverrides).length;
  themePaletteKeys.forEach((key) => {
    const field = themePaletteFields[key];
    const value = themePaletteValue(key);
    const control = $(`#${field.controlId}`);
    const output = $(`#${field.outputId}`);
    if (control) control.value = value.toLowerCase();
    if (output) output.textContent = value;
  });
  setText('theme-custom-status', overrideCount
    ? `Custom palette · ${overrideCount} override${overrideCount === 1 ? '' : 's'} active.`
    : 'Preset palette active · choose any color to customize.');
}

function persistCustomTheme() {
  try {
    if (Object.keys(customThemeOverrides).length) {
      localStorage.setItem(customThemeStorageKey, JSON.stringify(customThemeOverrides));
    } else {
      localStorage.removeItem(customThemeStorageKey);
    }
    return true;
  } catch (error) {
    console.warn(error);
    return false;
  }
}

function saveCustomThemeColor(key, value) {
  if (!themePaletteFields[key]) return;
  const normalized = normalizeThemeColor(value);
  if (!normalized) {
    setText('theme-custom-status', 'Choose a valid six-digit color.');
    return;
  }
  customThemeOverrides = { ...customThemeOverrides, [key]: normalized };
  const saved = persistCustomTheme();
  applyCustomThemeOverrides();
  syncCorePalette();
  syncThemeSetting();
  sync();
  if (!saved) setText('theme-custom-status', 'Color changed for this session but could not be saved locally.');
}

function resetCustomTheme() {
  customThemeOverrides = {};
  const saved = persistCustomTheme();
  applyCustomThemeOverrides();
  syncCorePalette();
  syncThemeSetting();
  sync();
  if (!saved) setText('theme-custom-status', 'Preset restored for this session but could not be saved locally.');
}

function saveClockLocale(value) {
  const locale = value === 'zh-CN' ? 'zh-CN' : 'en-US';
  try {
    localStorage.setItem(clockLocaleStorageKey, locale);
    refreshLocalClock();
    syncLocaleSetting();
  } catch (error) {
    setText('locale-status', 'Could not save the date language in this window.');
    console.warn(error);
  }
}

function saveResponseLanguage(value) {
  const language = value === 'zh-CN' ? 'zh-CN' : 'en';
  try {
    localStorage.setItem(responseLanguageStorageKey, language);
    syncResponseLanguageSetting();
  } catch (error) {
    setText('response-language-status', 'Could not save the response language in this window.');
    console.warn(error);
  }
}

refreshLocalClock();
syncLocaleSetting();
syncResponseLanguageSetting();
syncThemeSetting();
setInterval(refreshLocalClock, 1000);

$('#locale-setting')?.addEventListener('change', (event) => {
  saveClockLocale(event.currentTarget.value);
});
$('#response-language-setting')?.addEventListener('change', (event) => {
  saveResponseLanguage(event.currentTarget.value);
});
$('#theme-setting')?.addEventListener('change', (event) => {
  applyTheme(event.currentTarget.value);
});
$$('[data-theme-color]').forEach((control) => {
  control.addEventListener('input', (event) => {
    saveCustomThemeColor(event.currentTarget.dataset.themeColor, event.currentTarget.value);
  });
});
$('#theme-reset-custom')?.addEventListener('click', () => resetCustomTheme());
$('#panel-idle-setting')?.addEventListener('change', (event) => {
  savePanelIdleSeconds(event.currentTarget.value);
});
function handleAutoSpeechToggle(control) {
  const enabled = autoSpeech.setEnabled(control.checked);
  saveAutoSpeechPreference(enabled);
  updateAutoSpeechStatus({ enabled, state: enabled ? 'ready' : 'off', pending: autoSpeech.pendingCount() });
}
$('#auto-speak-setting')?.addEventListener('change', (event) => handleAutoSpeechToggle(event.currentTarget));
$('#voice-auto-speech-setting')?.addEventListener('change', (event) => handleAutoSpeechToggle(event.currentTarget));
$('#low-motion-setting')?.addEventListener('change', (event) => saveLowMotionPreference(event.currentTarget.checked));
$('#voice-package-setting')?.addEventListener('change', (event) => {
  saveSpeechVoicePreference(event.currentTarget.value);
  setText('voice-package-status', `Selected ${selectedSpeechVoiceLabel()} for future automatic replies.`);
});
runtimeSettingControls.backgroundRunning?.addEventListener('change', (event) => {
  void updateRuntimeSetting('backgroundRunning', event.currentTarget.checked);
});
runtimeSettingControls.startOnLogin?.addEventListener('change', (event) => {
  void updateRuntimeSetting('startOnLogin', event.currentTarget.checked);
});
$('#ai-mode-setting')?.addEventListener('change', async (event) => {
  const mode = event.currentTarget.value;
  const requestId = ++latestAiModeRequest;
  const previousMode = selectedAiMode;
  syncAiConnectionControls(mode);
  if (!coreOnline || !coreBridge || typeof coreBridge.aiMode !== 'function') {
    event.currentTarget.value = previousMode;
    syncAiConnectionControls(previousMode);
    setText('ai-connection-status', 'Core is offline; AI mode was not changed.');
    return;
  }
  setText('ai-connection-status', `Selecting ${mode}…`);
  try {
    const snapshot = await coreBridge.aiMode(mode);
    if (requestId !== latestAiModeRequest) return;
    applyAiConnection(snapshot?.ai || snapshot);
    setText('ai-connection-status', `${displayValue(snapshot?.ai?.mode || snapshot?.mode, mode)} selected · verification remains explicit.`);
    recordEvent('info', `AI mode selected: ${mode}.`);
    if (mode === 'managed_subscription') {
      void refreshAiConnectionCheck();
      if (coreOnline) void refreshAccountUsage();
    }
  } catch (error) {
    if (requestId !== latestAiModeRequest) return;
    setText('ai-connection-status', `Unavailable · ${error.message || 'AI mode was not changed.'}`);
    recordEvent('error', `AI mode: ${error.message || 'request failed'}`);
    await refreshHealth();
  }
});
$('#ai-disconnect')?.addEventListener('click', async () => {
  if (!coreOnline || !coreBridge?.aiDisconnect) return;
  try {
    const snapshot = await coreBridge.aiDisconnect();
    applyAiConnection(snapshot?.ai || snapshot);
    setText('ai-connection-status', 'Disconnected from JARVIS. Shared account remains signed in.');
  } catch (error) {
    setText('ai-connection-status', `Disconnect failed · ${error.message || 'request failed'}`);
  }
});
coreRefreshControl?.addEventListener('click', () => void refreshHealth({ manual: true }));
coreReconnectControl?.addEventListener('click', () => void reconnectCoreFromUi());
$('#tasks-refresh')?.addEventListener('click', () => void refreshTasks());
  $('#memory-refresh')?.addEventListener('click', () => void refreshHistory());
  $('#history-refresh')?.addEventListener('click', () => void refreshConversationList());
  $('#history-new')?.addEventListener('click', () => startNewConversation());
$('#knowledge-refresh')?.addEventListener('click', () => void refreshVaults());
$('#obsidian-connect')?.addEventListener('click', () => void connectObsidianVault());
$('#system-info-refresh')?.addEventListener('click', () => void refreshSystemInfo());
$('#projects-refresh')?.addEventListener('click', () => void refreshProjects());
$('#projects-rescan')?.addEventListener('click', () => void refreshProjectRegistry());
$('#voice-refresh')?.addEventListener('click', () => {
  void refreshSpeechSettings();
  void refreshSpeechVoices();
});
$('#voice-test')?.addEventListener('click', () => void previewSpeechVoice());
$('#usage-refresh')?.addEventListener('click', () => void refreshAccountUsage({ manual: true }));
$('#project-git-status')?.addEventListener('click', () => void runProjectAction('git'));
$('#project-list-files')?.addEventListener('click', () => void runProjectAction('files'));
$('#project-read-file')?.addEventListener('click', () => void runProjectAction('read'));
$('#project-search')?.addEventListener('click', () => void runProjectAction('search'));
$('#tools-clear')?.addEventListener('click', () => {
  toolResultRecords.length = 0;
  persistRendererRecords();
  renderToolResultsPage();
});
$('#events-clear')?.addEventListener('click', () => {
  for (let index = eventRecords.length - 1; index >= 0; index -= 1) {
    if (eventRecords[index].level !== 'error') eventRecords.splice(index, 1);
  }
  persistRendererRecords();
  renderEventSurfaces();
});
$('#errors-clear')?.addEventListener('click', () => {
  for (let index = eventRecords.length - 1; index >= 0; index -= 1) {
    if (eventRecords[index].level === 'error') eventRecords.splice(index, 1);
  }
  persistRendererRecords();
  renderEventSurfaces();
});
syncPanelIdleSetting();
syncMotionControls();
void refreshRuntimeSettings();
const savedAutoSpeech = readAutoSpeechPreference();
const autoSpeechControls = [$('#auto-speak-setting'), $('#voice-auto-speech-setting')].filter(Boolean);
autoSpeechControls.forEach((control) => { control.checked = savedAutoSpeech; });
if (savedAutoSpeech) autoSpeech.setEnabled(true);
else updateAutoSpeechStatus({ enabled: false, state: 'off', pending: 0 });
addEventListener('beforeunload', () => {
  if (autoSpeech.isEnabled()) autoSpeech.setEnabled(false);
});

$$('[data-demo]').forEach((button) => button.addEventListener('click', () => {
  const label = button.dataset.demo;
  $('#modal-title').textContent = label;
  $('#modal-copy').textContent = 'This is a local prototype interaction only. It does not access JARVIS, Codex, devices, accounts, SQLite, Obsidian, APIs, or system tools.';
  modal.classList.add('open');
}));
$$('[data-close]').forEach((button) => button.addEventListener('click', () => modal.classList.remove('open')));
$('#close-panel')?.addEventListener('click', () => openPage('assistant'));
modal.addEventListener('click', (event) => {
  if (event.target === modal) modal.classList.remove('open');
});
document.addEventListener('keydown', (event) => {
  if (modal.classList.contains('open')) {
    if (event.key === 'Escape') modal.classList.remove('open');
    return;
  }
  if (isFocusShortcut(event)) {
    if (focusInput(composerInput)) event.preventDefault();
    return;
  }
  if (event.key !== 'Escape') return;
  if (active !== 'assistant') openPage('assistant');
});

restoreRendererRecords();
restoreTokenUsageRecords();
restoreAccountUsageSnapshot();
renderEventSurfaces();
renderToolResultsPage();
renderTokenUsageCard();
showTokenUsageCard({ animate: false });
setInterval(refreshHealth, 2000);
setInterval(refreshTelemetry, 2000);
refreshHealth();
refreshTelemetry();
openPage(location.hash.slice(1) || 'assistant', false);
resize();
sync();
