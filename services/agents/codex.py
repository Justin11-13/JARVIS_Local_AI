"""Backend-owned Codex App Server JSONL transport. No shell interpolation."""
import json
import os
from pathlib import Path
from queue import Queue, Empty
import shutil
import subprocess
from threading import Lock, Thread


def codex_command():
    configured = os.getenv('JARVIS_CODEX_PATH', '').strip()
    if configured:
        path = Path(configured).resolve(strict=True)
        if path.suffix.lower() != '.exe' and os.name == 'nt':
            raise ValueError('JARVIS_CODEX_PATH must name codex.exe on Windows')
        return [str(path)]
    executable = shutil.which('codex.exe' if os.name == 'nt' else 'codex')
    if executable:
        return [executable]
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA', '')) / 'npm/node_modules/@openai/codex/node_modules/@openai'
        candidates = list(base.glob('codex-win32-*/vendor/*/bin/codex.exe'))
        if candidates:
            return [str(candidates[0])]
    raise ValueError('Codex CLI is not installed; configure JARVIS_CODEX_PATH')


class CodexAdapter:
    def __init__(self, on_message, command=None):
        self.on_message = on_message
        self.command = command
        self.process = None
        self.pending = {}
        self.lock = Lock()
        self.counter = 0

    def start(self):
        self.process = subprocess.Popen(
            (self.command or codex_command()) + ['app-server', '--listen', 'stdio://'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace', bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        Thread(target=self._read, daemon=True).start()
        Thread(target=self._drain_errors, daemon=True).start()
        result = self.request('initialize', {'clientInfo': {'name': 'jarvis', 'version': '1.0.0'}})
        self.send({'method': 'initialized', 'params': {}})
        return result

    def _drain_errors(self):
        for _ in self.process.stderr:
            pass  # Never expose environment or authentication diagnostics to the model/UI.

    def _read(self):
        try:
            for line in self.process.stdout:
                message = json.loads(line)
                if 'id' in message and 'method' not in message:
                    with self.lock:
                        queue = self.pending.get(message['id'])
                    if queue:
                        queue.put(message)
                else:
                    self.on_message(message)
        except Exception as error:
            self.on_message({'method': 'transport/error', 'params': {'message': str(error)}})
        finally:
            with self.lock:
                queues = list(self.pending.values())
            for queue in queues:
                queue.put({'error': {'message': 'Codex App Server disconnected'}})
            self.on_message({'method': 'transport/closed', 'params': {}})

    def send(self, message):
        with self.lock:
            if not self.process or self.process.poll() is not None:
                raise RuntimeError('Codex App Server is not running')
            self.process.stdin.write(json.dumps(message, ensure_ascii=False) + '\n')
            self.process.stdin.flush()

    def request(self, method, params, timeout=45):
        queue = Queue()
        with self.lock:
            self.counter += 1
            identifier = self.counter
            self.pending[identifier] = queue
        try:
            self.send({'id': identifier, 'method': method, 'params': params})
            response = queue.get(timeout=timeout)
            if 'error' in response:
                raise RuntimeError(response['error'].get('message', 'Codex request failed'))
            return response.get('result', {})
        except Empty as error:
            raise TimeoutError(f'Codex {method} timed out') from error
        finally:
            with self.lock:
                self.pending.pop(identifier, None)

    def reply(self, identifier, result):
        self.send({'id': identifier, 'result': result})

    def close(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
