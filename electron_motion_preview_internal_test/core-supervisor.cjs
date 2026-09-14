const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { spawn } = require('node:child_process');

const CORE_HOST = '127.0.0.1';
const CORE_PORT = 8765;
const HEALTH_PATH = '/api/health';
const HEALTH_TIMEOUT_MS = 1000;
const START_TIMEOUT_MS = 30000;
const POLL_INTERVAL_MS = 250;
const CREATE_NO_WINDOW = 0x08000000;
const PROJECT_ROOT = path.resolve(__dirname, '..');
const PYTHON_PATH = path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe');
const STARTUP_LOG_PATH = path.join(PROJECT_ROOT, 'tmp', 'electron-core-startup.log');

class CoreSupervisorError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'CoreSupervisorError';
    this.code = code;
  }
}

function readyHealth(body, statusCode) {
  if (statusCode < 200 || statusCode >= 300 || !body || typeof body !== 'object' || Array.isArray(body)) {
    return false;
  }
  return body.core && typeof body.core === 'object' && body.core.status === 'ready';
}

function probeHealth({ requestFactory = http.request, timeoutMs = HEALTH_TIMEOUT_MS } = {}) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (result) => {
      if (settled) return;
      settled = true;
      resolve(result);
    };

    let request;
    try {
      request = requestFactory(
        {
          host: CORE_HOST,
          port: CORE_PORT,
          path: HEALTH_PATH,
          method: 'GET',
          headers: { Accept: 'application/json' },
        },
        (response) => {
          const chunks = [];
          response.setEncoding('utf8');
          response.on('data', (chunk) => chunks.push(chunk));
          response.on('end', () => {
            const bodyText = chunks.join('');
            let body = null;
            try {
              body = bodyText ? JSON.parse(bodyText) : null;
            } catch {
              finish({ state: 'occupied', detail: '127.0.0.1:8765 returned non-JSON health data.' });
              return;
            }
            if (readyHealth(body, response.statusCode || 0)) {
              finish({ state: 'ready', health: body });
              return;
            }
            finish({ state: 'occupied', health: body, detail: '127.0.0.1:8765 is serving a non-ready health response.' });
          });
        },
      );
    } catch (error) {
      finish({ state: 'unavailable', detail: `Health probe could not start: ${error.message}` });
      return;
    }

    request.setTimeout(timeoutMs, () => {
      request.destroy();
      finish({ state: 'occupied', detail: '127.0.0.1:8765 did not answer its health request.' });
    });
    request.on('error', (error) => {
      if (error.code === 'ECONNREFUSED') {
        finish({ state: 'offline', detail: 'No service is listening on 127.0.0.1:8765.' });
        return;
      }
      if (error.code === 'ECONNRESET' || error.code === 'EPIPE') {
        finish({ state: 'occupied', detail: '127.0.0.1:8765 accepted a connection but did not return JARVIS health.' });
        return;
      }
      finish({ state: 'unavailable', detail: `Health probe failed: ${error.message}` });
    });
    request.end();
  });
}

function wait(delayMs) {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}

function startupArguments() {
  return [
    '-m', 'uvicorn', 'app.api:app',
    '--host', CORE_HOST,
    '--port', String(CORE_PORT),
  ];
}

class CoreSupervisor {
  constructor({
    pythonPath = PYTHON_PATH,
    coreExecutable = null,
    coreArguments = [],
    projectRoot = PROJECT_ROOT,
    coreWorkingDirectory = null,
    logPath = STARTUP_LOG_PATH,
    probe = probeHealth,
    spawnProcess = spawn,
    sleep = wait,
    startTimeoutMs = START_TIMEOUT_MS,
    pollIntervalMs = POLL_INTERVAL_MS,
  } = {}) {
    this.pythonPath = pythonPath;
    this.coreExecutable = coreExecutable;
    this.coreArguments = [...coreArguments];
    this.projectRoot = projectRoot;
    this.coreWorkingDirectory = coreWorkingDirectory || projectRoot;
    this.logPath = logPath;
    this.probe = probe;
    this.spawnProcess = spawnProcess;
    this.sleep = sleep;
    this.startTimeoutMs = startTimeoutMs;
    this.pollIntervalMs = pollIntervalMs;
    this.ownedChild = null;
  }

  hasOwnedProcess() {
    return Boolean(this.ownedChild && this.ownedChild.exitCode === null && !this.ownedChild.killed);
  }

  async ensureReady() {
    const existing = await this.probe();
    if (existing.state === 'ready') return { started: false, health: existing.health };
    if (existing.state !== 'offline') {
      throw new CoreSupervisorError(
        'CORE_PORT_OCCUPIED',
        existing.detail || '127.0.0.1:8765 is occupied by a service that did not report JARVIS Core ready.',
      );
    }
    const executable = this.coreExecutable || this.pythonPath;
    if (!fs.existsSync(executable)) {
      throw new CoreSupervisorError(
        this.coreExecutable ? 'CORE_RUNTIME_MISSING' : 'CORE_PYTHON_MISSING',
        `The JARVIS Core runtime was not found at ${executable}.`,
      );
    }

    let child;
    try {
      child = this.startOwnedProcess();
    } catch (error) {
      throw new CoreSupervisorError('CORE_START_FAILED', `The local JARVIS Core process could not start: ${error.message}`);
    }
    this.ownedChild = child;
    try {
      const health = await this.waitForReady(child);
      return { started: this.hasOwnedProcess(), health: health.health };
    } catch (error) {
      await this.stopOwned();
      throw error;
    }
  }

  startOwnedProcess() {
    fs.mkdirSync(path.dirname(this.logPath), { recursive: true });
    const logFd = fs.openSync(this.logPath, 'a');
    try {
      const child = this.spawnProcess(
        this.coreExecutable || this.pythonPath,
        this.coreExecutable ? this.coreArguments : startupArguments(),
        {
          cwd: this.coreWorkingDirectory,
          shell: false,
          windowsHide: true,
          creationFlags: CREATE_NO_WINDOW,
          stdio: ['ignore', logFd, logFd],
        },
      );
      let closed = false;
      const closeLog = () => {
        if (closed) return;
        closed = true;
        try {
          fs.closeSync(logFd);
        } catch {
          // The descriptor may already have been closed by the child runtime.
        }
      };
      child.once('exit', closeLog);
      child.once('close', closeLog);
      child.once('error', closeLog);
      return child;
    } catch (error) {
      fs.closeSync(logFd);
      throw error;
    }
  }

  async waitForReady(child) {
    const deadline = Date.now() + this.startTimeoutMs;
    let childError = null;
    let childExited = false;
    child.once('error', (error) => {
      childError = error;
    });
    child.once('exit', () => {
      childExited = true;
    });

    while (Date.now() < deadline) {
      const health = await this.probe();
      if (health.state === 'ready') return health;
      if (childError) {
        throw new CoreSupervisorError('CORE_START_FAILED', `The local JARVIS Core process failed: ${childError.message}`);
      }
      if (childExited || child.exitCode !== null) {
        const afterExit = await this.probe();
        if (afterExit.state === 'ready') return afterExit;
        if (afterExit.state === 'occupied') {
          throw new CoreSupervisorError(
            'CORE_PORT_OCCUPIED',
            afterExit.detail || '127.0.0.1:8765 became occupied without a ready JARVIS Core.',
          );
        }
        throw new CoreSupervisorError(
          'CORE_START_FAILED',
          `The local JARVIS Core process exited before health became ready. Check ${this.logPath}.`,
        );
      }
      await this.sleep(this.pollIntervalMs);
    }
    throw new CoreSupervisorError(
      'CORE_START_TIMEOUT',
      `JARVIS Core did not become ready within ${this.startTimeoutMs / 1000} seconds. Check ${this.logPath}.`,
    );
  }

  async stopOwned() {
    const child = this.ownedChild;
    this.ownedChild = null;
    if (!child || child.exitCode !== null || child.killed) return;
    child.kill();
    await new Promise((resolve) => {
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        resolve();
      };
      child.once('close', finish);
      setTimeout(() => {
        if (child.exitCode === null && !child.killed) child.kill('SIGKILL');
        finish();
      }, 5000).unref();
    });
  }
}

module.exports = {
  CORE_HOST,
  CORE_PORT,
  CREATE_NO_WINDOW,
  HEALTH_PATH,
  PYTHON_PATH,
  STARTUP_LOG_PATH,
  CoreSupervisor,
  CoreSupervisorError,
  probeHealth,
  startupArguments,
};
