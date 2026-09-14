const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');

const {
  CORE_HOST,
  CORE_PORT,
  CoreSupervisor,
  CoreSupervisorError,
  probeHealth,
  startupArguments,
} = require('../core-supervisor.cjs');

class FakeChild extends EventEmitter {
  constructor() {
    super();
    this.exitCode = null;
    this.killed = false;
    this.killCalls = [];
  }

  kill(signal) {
    this.killCalls.push(signal);
    this.killed = true;
    this.exitCode = 0;
    queueMicrotask(() => this.emit('close', 0, signal));
  }
}

function tempLog() {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'jarvis-core-supervisor-'));
  return {
    directory,
    path: path.join(directory, 'startup.log'),
  };
}

test('health probe uses only the fixed loopback health endpoint', async () => {
  const calls = [];
  const result = await probeHealth({
    requestFactory(options, callback) {
      calls.push(options);
      const request = new EventEmitter();
      request.setTimeout = () => {};
      request.destroy = () => {};
      request.end = () => {
        const response = new EventEmitter();
        response.statusCode = 200;
        response.setEncoding = () => {};
        callback(response);
        response.emit('data', JSON.stringify({ core: { status: 'ready' } }));
        response.emit('end');
      };
      return request;
    },
  });

  assert.deepEqual(result, { state: 'ready', health: { core: { status: 'ready' } } });
  assert.deepEqual(calls, [{
    host: CORE_HOST,
    port: CORE_PORT,
    path: '/api/health',
    method: 'GET',
    headers: { Accept: 'application/json' },
  }]);
});

test('ready Core is reused without spawning another process', async () => {
  let spawnCount = 0;
  const supervisor = new CoreSupervisor({
    pythonPath: __filename,
    probe: async () => ({ state: 'ready', health: { core: { status: 'ready' } } }),
    spawnProcess: () => {
      spawnCount += 1;
      throw new Error('must not spawn');
    },
  });

  const result = await supervisor.ensureReady();

  assert.equal(result.started, false);
  assert.equal(spawnCount, 0);
  assert.equal(supervisor.hasOwnedProcess(), false);
});

test('cold start owns only its Core child and can stop it', async () => {
  const log = tempLog();
  const child = new FakeChild();
  let probes = 0;
  let spawnCall;
  const supervisor = new CoreSupervisor({
    pythonPath: __filename,
    logPath: log.path,
    probe: async () => {
      probes += 1;
      return probes === 1 || probes === 2
        ? { state: 'offline' }
        : { state: 'ready', health: { core: { status: 'ready' } } };
    },
    spawnProcess: (...args) => {
      spawnCall = args;
      return child;
    },
    sleep: async () => {},
  });

  const result = await supervisor.ensureReady();

  assert.equal(result.started, true);
  assert.equal(supervisor.hasOwnedProcess(), true);
  assert.deepEqual(spawnCall.slice(0, 2), [
    __filename,
    startupArguments(),
  ]);
  assert.equal(spawnCall[2].shell, false);
  assert.equal(spawnCall[2].windowsHide, true);
  assert.equal(spawnCall[2].creationFlags, 0x08000000);
  assert.deepEqual(spawnCall[2].stdio.slice(0, 1), ['ignore']);

  await supervisor.stopOwned();
  assert.deepEqual(child.killCalls, [undefined]);
  assert.equal(supervisor.hasOwnedProcess(), false);
  fs.rmSync(log.directory, { recursive: true, force: true });
});

test('packaged Core executable is launched from its bundled directory', async () => {
  const log = tempLog();
  const child = new FakeChild();
  let probes = 0;
  let spawnCall;
  const workingDirectory = log.directory;
  const supervisor = new CoreSupervisor({
    coreExecutable: __filename,
    coreArguments: ['--packaged-test'],
    coreWorkingDirectory: workingDirectory,
    logPath: log.path,
    probe: async () => {
      probes += 1;
      return probes === 1 || probes === 2
        ? { state: 'offline' }
        : { state: 'ready', health: { core: { status: 'ready' } } };
    },
    spawnProcess: (...args) => {
      spawnCall = args;
      return child;
    },
    sleep: async () => {},
  });

  const result = await supervisor.ensureReady();

  assert.equal(result.started, true);
  assert.deepEqual(spawnCall.slice(0, 2), [__filename, ['--packaged-test']]);
  assert.equal(spawnCall[2].cwd, workingDirectory);
  await supervisor.stopOwned();
  fs.rmSync(log.directory, { recursive: true, force: true });
});

test('a responding non-ready service is an explicit port conflict', async () => {
  const supervisor = new CoreSupervisor({
    probe: async () => ({ state: 'occupied', detail: 'foreign service' }),
    spawnProcess: () => {
      throw new Error('must not spawn');
    },
  });

  await assert.rejects(
    supervisor.ensureReady(),
    (error) => error instanceof CoreSupervisorError
      && error.code === 'CORE_PORT_OCCUPIED'
      && error.message.includes('foreign service'),
  );
});

test('a ready Core that wins a cold-start race is reused without replacement', async () => {
  const log = tempLog();
  const child = new FakeChild();
  let probes = 0;
  const supervisor = new CoreSupervisor({
    pythonPath: __filename,
    logPath: log.path,
    probe: async () => {
      probes += 1;
      if (probes === 1) return { state: 'offline' };
      if (probes === 2) {
        child.exitCode = 1;
        child.emit('exit', 1, null);
        return { state: 'offline' };
      }
      return { state: 'ready', health: { core: { status: 'ready' } } };
    },
    spawnProcess: () => child,
    sleep: async () => {},
  });

  const result = await supervisor.ensureReady();

  assert.equal(result.started, false);
  assert.equal(supervisor.hasOwnedProcess(), false);
  assert.deepEqual(child.killCalls, []);
  fs.rmSync(log.directory, { recursive: true, force: true });
});

test('child failure is reported and does not leave an owned process', async () => {
  const log = tempLog();
  const child = new FakeChild();
  let probes = 0;
  const supervisor = new CoreSupervisor({
    pythonPath: __filename,
    logPath: log.path,
    probe: async () => {
      probes += 1;
      if (probes === 1) return { state: 'offline' };
      child.exitCode = 1;
      child.emit('exit', 1, null);
      return { state: 'offline' };
    },
    spawnProcess: () => child,
    sleep: async () => {},
  });

  await assert.rejects(
    supervisor.ensureReady(),
    (error) => error instanceof CoreSupervisorError && error.code === 'CORE_START_FAILED',
  );
  assert.equal(supervisor.hasOwnedProcess(), false);
  assert.deepEqual(child.killCalls, []);
  fs.rmSync(log.directory, { recursive: true, force: true });
});

test('startup timeout stops the exact child it created', async () => {
  const log = tempLog();
  const child = new FakeChild();
  const supervisor = new CoreSupervisor({
    pythonPath: __filename,
    logPath: log.path,
    probe: async () => ({ state: 'offline' }),
    spawnProcess: () => child,
    startTimeoutMs: 0,
    sleep: async () => {},
  });

  await assert.rejects(
    supervisor.ensureReady(),
    (error) => error instanceof CoreSupervisorError && error.code === 'CORE_START_TIMEOUT',
  );
  assert.deepEqual(child.killCalls, [undefined]);
  assert.equal(supervisor.hasOwnedProcess(), false);
  fs.rmSync(log.directory, { recursive: true, force: true });
});
