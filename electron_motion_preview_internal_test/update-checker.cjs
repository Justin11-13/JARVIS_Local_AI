const UPDATE_CHANNEL = 'internal-test';
const UPDATE_API_URL = 'https://api.github.com/repos/Justin11-13/JARVIS_Local_AI/releases?per_page=20';
const UPDATE_TIMEOUT_MS = 8000;
const RELEASE_ASSET_PATTERN = /^JARVIS-Internal-Test-\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?-Setup\.exe$/i;
const TRUSTED_RELEASE_HOST = 'github.com';
const TRUSTED_RELEASE_PATH = '/Justin11-13/JARVIS_Local_AI/releases/';

class UpdateCheckError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'UpdateCheckError';
    this.code = code;
  }
}

function parseVersion(value) {
  const match = String(value ?? '').trim().match(
    /(?:^|[^0-9])v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?(?=$|[^0-9A-Za-z.-])/i,
  );
  if (!match) return null;
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    prerelease: match[4] ? match[4].split('.') : [],
    value: `${match[1]}.${match[2]}.${match[3]}${match[4] ? `-${match[4]}` : ''}`,
  };
}

function comparePrerelease(left, right) {
  if (!left.length && !right.length) return 0;
  if (!left.length) return 1;
  if (!right.length) return -1;
  const length = Math.max(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    if (index >= left.length) return -1;
    if (index >= right.length) return 1;
    const a = left[index];
    const b = right[index];
    if (a === b) continue;
    const aNumber = /^\d+$/.test(a);
    const bNumber = /^\d+$/.test(b);
    if (aNumber && bNumber) return Number(a) > Number(b) ? 1 : -1;
    if (aNumber !== bNumber) return aNumber ? -1 : 1;
    return a > b ? 1 : -1;
  }
  return 0;
}

function compareVersions(left, right) {
  const a = typeof left === 'string' ? parseVersion(left) : left;
  const b = typeof right === 'string' ? parseVersion(right) : right;
  if (!a || !b) throw new TypeError('Both versions must contain a valid semantic version.');
  for (const key of ['major', 'minor', 'patch']) {
    if (a[key] !== b[key]) return a[key] > b[key] ? 1 : -1;
  }
  return comparePrerelease(a.prerelease, b.prerelease);
}

function trustedReleaseUrl(value) {
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.hostname !== TRUSTED_RELEASE_HOST
      || !url.pathname.startsWith(TRUSTED_RELEASE_PATH)) return null;
    return url.href;
  } catch {
    return null;
  }
}

function selectInternalTestRelease(releases) {
  if (!Array.isArray(releases)) return null;
  const candidates = releases.map((release) => {
    if (!release || release.draft === true || !Array.isArray(release.assets)) return null;
    const version = parseVersion(release.tag_name) || parseVersion(release.name);
    const asset = release.assets.find((candidate) => (
      candidate && typeof candidate.name === 'string' && RELEASE_ASSET_PATTERN.test(candidate.name)
    ));
    const releaseUrl = trustedReleaseUrl(release.html_url);
    if (!version || !asset || !releaseUrl) return null;
    const publishedAt = Date.parse(release.published_at || release.created_at || '') || 0;
    return {
      version: version.value,
      releaseUrl,
      assetName: asset.name,
      releaseName: String(release.name || release.tag_name || '').trim().slice(0, 120),
      publishedAt,
      prerelease: release.prerelease === true,
    };
  }).filter(Boolean);

  candidates.sort((left, right) => (
    compareVersions(right.version, left.version) || right.publishedAt - left.publishedAt
  ));
  return candidates[0] || null;
}

async function fetchJson(url, { fetchImpl, timeoutMs }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetchImpl(url, {
      method: 'GET',
      headers: {
        Accept: 'application/vnd.github+json',
        'User-Agent': 'JARVIS-Internal-Test',
      },
      signal: controller.signal,
    });
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new UpdateCheckError('UPDATE_CHECK_TIMEOUT', `Update check timed out after ${timeoutMs} ms.`);
    }
    throw new UpdateCheckError('UPDATE_CHECK_NETWORK', `Update check could not reach GitHub Releases: ${error.message || String(error)}`);
  } finally {
    clearTimeout(timer);
  }
}

async function checkForUpdate({
  currentVersion,
  channel = UPDATE_CHANNEL,
  apiUrl = UPDATE_API_URL,
  fetchImpl = globalThis.fetch,
  timeoutMs = UPDATE_TIMEOUT_MS,
} = {}) {
  if (channel !== UPDATE_CHANNEL) {
    throw new UpdateCheckError('UPDATE_CHANNEL_UNSUPPORTED', `Update channel is not supported: ${String(channel)}.`);
  }
  const current = parseVersion(currentVersion);
  if (!current) throw new UpdateCheckError('UPDATE_CURRENT_VERSION_INVALID', 'The installed JARVIS version is invalid.');
  if (typeof fetchImpl !== 'function') {
    throw new UpdateCheckError('UPDATE_FETCH_UNAVAILABLE', 'This build does not provide a network fetch implementation.');
  }
  if (!Number.isInteger(timeoutMs) || timeoutMs < 1 || timeoutMs > 60000) {
    throw new UpdateCheckError('UPDATE_TIMEOUT_INVALID', 'Update check timeout must be between 1 and 60000 ms.');
  }

  const response = await fetchJson(apiUrl, { fetchImpl, timeoutMs });
  if (!response || response.ok !== true) {
    throw new UpdateCheckError(
      'UPDATE_CHECK_HTTP',
      `GitHub Releases returned HTTP ${response?.status || 'unknown'}.`,
    );
  }

  let releases;
  try {
    releases = await response.json();
  } catch (error) {
    throw new UpdateCheckError('UPDATE_RESPONSE_INVALID', `GitHub Releases returned invalid JSON: ${error.message || String(error)}`);
  }
  if (!Array.isArray(releases)) {
    throw new UpdateCheckError('UPDATE_RESPONSE_INVALID', 'GitHub Releases returned an unexpected payload.');
  }

  const release = selectInternalTestRelease(releases);
  if (!release) {
    return {
      status: 'not_published',
      channel,
      currentVersion: current.value,
      detail: 'No Internal Test Windows installer release is published yet.',
    };
  }

  const status = compareVersions(release.version, current) > 0 ? 'update_available' : 'up_to_date';
  return {
    status,
    channel,
    currentVersion: current.value,
    latestVersion: release.version,
    releaseUrl: release.releaseUrl,
    assetName: release.assetName,
    releaseName: release.releaseName,
    prerelease: release.prerelease,
  };
}

module.exports = {
  RELEASE_ASSET_PATTERN,
  UPDATE_API_URL,
  UPDATE_CHANNEL,
  UPDATE_TIMEOUT_MS,
  UpdateCheckError,
  checkForUpdate,
  compareVersions,
  parseVersion,
  selectInternalTestRelease,
  trustedReleaseUrl,
};
