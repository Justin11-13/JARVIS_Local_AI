"""Opt-in live probes, synthetic data only; no personal vault or project writes."""
import json
from pathlib import Path
from contextlib import nullcontext
from uuid import uuid4
import time

from services.agents.gemini import GeminiAdapter
from services.coding_service import CodingService, TERMINAL
from services.jarvis_memory import JarvisMemory
from services.memory_manager import MemoryManager


def main():
    scratch = Path(__file__).resolve().parents[1] / 'tmp'
    scratch.mkdir(exist_ok=True)
    # Python's Windows TemporaryDirectory uses owner-only ACLs. Codex runs under
    # a sandbox identity, so inherit the workspace ACL like a real project folder.
    with nullcontext(scratch / ('assistant-live-' + uuid4().hex)) as directory:
        root = Path(directory)
        root.mkdir()
        print('Probe directory:', root, flush=True)
        memory = JarvisMemory(database_path=root / 'probe.sqlite3')
        brain = GeminiAdapter()
        manager = MemoryManager(memory, brain)
        memory.remember('Remember this preference: I prefer concise Chinese explanations with English code identifiers.', 'Understood; concise Chinese explanations with English code identifiers.')
        if manager.trigger(force=True):
            deadline = time.monotonic() + 90
            while manager.pending and time.monotonic() < deadline:
                time.sleep(.2)
            print('Gemini extraction:', json.dumps(memory.store.state('extraction'), ensure_ascii=False), flush=True)
            print('Memory candidates:', len(memory.store.items()), flush=True)
        else:
            print('Gemini extraction unavailable: not configured', flush=True)
        manager.pool.shutdown(wait=True)
        service = CodingService(memory.store)
        try:
            previous = None
            for prompt in ['Reply with exactly JARVIS_PROBE_OK. Do not use tools or read any files.', 'What exact token did you reply with in the preceding turn? Do not use tools.', 'Use apply_patch to create probe.txt in the current directory containing exactly JARVIS_PROBE_OK. Do not run shell commands. Report JARVIS_PROBE_OK after creation.']:
                task = service.create('Synthetic probe', root, prompt, previous)
                deadline = time.monotonic() + 120
                while time.monotonic() < deadline:
                    task = memory.store.task(task['id'])
                    if task['status'] in TERMINAL:
                        break
                    for pending in task['pending']:
                        decision = 'allow_once' if pending['method'] == 'item/fileChange/requestApproval' and not pending['high_risk'] else 'deny'
                        service.answer(task['id'], pending['id'], decision=decision)
                    time.sleep(.2)
                else:
                    service.cancel(task['id'])
                    raise RuntimeError('Live turn did not finish within probe deadline')
                print('Codex live turn:', task['status'], task['result'], task['error'], flush=True)
                assert task['status'] == 'completed', task['error']
                assert 'JARVIS_PROBE_OK' in task['result']
                previous = task['id']
            assert (root / 'probe.txt').read_text().strip() == 'JARVIS_PROBE_OK'
            print('Live approved file creation verified in disposable probe directory.', flush=True)
        finally:
            service.pool.shutdown(wait=True)


if __name__ == '__main__':
    main()
