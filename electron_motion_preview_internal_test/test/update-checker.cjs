const assert = require('node:assert/strict');
const test = require('node:test');
const {
  UpdateCheckError,
  checkForUpdate,
  compareVersions,
  selectInternalTestRelease,
  trustedReleaseUrl,
} = require('../update-checker.cjs');

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => payload,
  };
}

function release(version, {
  name = `JARVIS Internal Test ${version}`,
  assetName = `JARVIS-Internal-Test-${version}-Setup.exe`,
  releaseUrl = `https://github.com/Justin11-13/JARVIS_Local_AI/releases/tag/v${version}`,
  publishedAt = '2026-09-14T00:00:00Z',
  prerelease = true,
} = {}) {
  return {
    tag_name: `v${version}`,
    name,
    html_url: releaseUrl,
    published_at: publishedAt,
    prerelease,
    draft: false,
    assets: [{ name: assetName, browser_download_url: `${releaseUrl}/download/${assetName}` }],
  };
}

test('semantic version comparison handles stable and prerelease versions', () => {
  assert.equal(compareVersions('0.1.1', '0.1.0'), 1);
  assert.equal(compareVersions('0.1.0', 'v0.1.0'), 0);
  assert.equal(compareVersions('0.1.0', '0.1.0-rc.1'), 1);
  assert.equal(compareVersions('0.1.0-rc.2', '0.1.0-rc.10'), -1);
});

test('selects the newest published Internal Test release with the installer asset', async () => {
  let requestedUrl = '';
  const result = await checkForUpdate({
    currentVersion: '0.1.0',
    fetchImpl: async (url, options) => {
      requestedUrl = url;
      assert.equal(options.method, 'GET');
      assert.equal(options.headers.Accept, 'application/vnd.github+json');
      return response([
        release('0.0.9'),
        release('0.1.2'),
        release('0.1.1', { assetName: 'JARVIS-Development-0.1.1-Setup.exe' }),
      ]);
    },
  });
  assert.match(requestedUrl, /api\.github\.com\/repos\/Justin11-13\/JARVIS_Local_AI\/releases/);
  assert.equal(result.status, 'update_available');
  assert.equal(result.currentVersion, '0.1.0');
  assert.equal(result.latestVersion, '0.1.2');
  assert.equal(result.assetName, 'JARVIS-Internal-Test-0.1.2-Setup.exe');
});

test('reports up to date and no published package without false update success', async () => {
  const current = await checkForUpdate({
    currentVersion: '0.1.2',
    fetchImpl: async () => response([release('0.1.2')]),
  });
  assert.equal(current.status, 'up_to_date');
  assert.equal(current.latestVersion, '0.1.2');

  const absent = await checkForUpdate({
    currentVersion: '0.1.2',
    fetchImpl: async () => response([release('0.1.3', { assetName: 'notes.txt' })]),
  });
  assert.equal(absent.status, 'not_published');
  assert.match(absent.detail, /No Internal Test Windows installer/);
});

test('rejects untrusted release URLs and preserves explicit network failures', async () => {
  assert.equal(trustedReleaseUrl('https://example.com/releases/v0.1.1'), null);
  assert.equal(trustedReleaseUrl('http://github.com/Justin11-13/JARVIS_Local_AI/releases/tag/v0.1.1'), null);
  await assert.rejects(
    checkForUpdate({
      currentVersion: '0.1.0',
      fetchImpl: async () => { throw new Error('offline'); },
    }),
    (error) => error instanceof UpdateCheckError
      && error.code === 'UPDATE_CHECK_NETWORK'
      && /could not reach GitHub Releases/.test(error.message),
  );
});

test('times out a stuck update request within the configured bound', async () => {
  await assert.rejects(
    checkForUpdate({
      currentVersion: '0.1.0',
      timeoutMs: 10,
      fetchImpl: async (_url, { signal }) => new Promise((resolve, reject) => {
        signal.addEventListener('abort', () => {
          const error = new Error('aborted');
          error.name = 'AbortError';
          reject(error);
        });
      }),
    }),
    (error) => error instanceof UpdateCheckError && error.code === 'UPDATE_CHECK_TIMEOUT',
  );
});
