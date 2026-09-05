"""Codex task lifecycle, durable events and request-bound human approvals."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import re
from threading import Event, RLock
from uuid import uuid4

from services.agents.codex import CodexAdapter, codex_command
from services.jarvis_memory import JarvisMemory
from services.memory_store import now
from services.permission_manager import PermissionManager


TERMINAL = {'completed', 'failed', 'cancelled', 'timed_out'}


class CodingService:
    def __init__(self, store, on_complete=None, adapter_factory=CodexAdapter, permission_manager=None):
        self.store, self.on_complete, self.adapter_factory = store, on_complete, adapter_factory
        self.permission_manager = permission_manager or PermissionManager()
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='codex-task')
        self.lock = RLock()
        self.adapters, self.finished = {}, {}
        for task in store.tasks():
            if task['status'] not in TERMINAL:
                task.update(status='failed', error='JARVIS restarted; resume this task explicitly.', pending=[])
                store.save_task(task, 'task.failed', {'error': task['error']})

    def create(self, project, cwd, prompt, resume_id=None):
        with self.lock:
            return self._create(project, cwd, prompt, resume_id)

    def _create(self, project, cwd, prompt, resume_id):
        root = Path(cwd).resolve(strict=True)
        if not root.is_dir():
            raise ValueError('Project directory is unavailable')
        codex_command()
        parent = self.store.task(resume_id) if resume_id else None
        if resume_id and (not parent or parent['status'] not in TERMINAL or parent['cwd'] != str(root) or not parent.get('thread_id')):
            raise ValueError('Only a finished task in the same project can be resumed')
        active = [task for task in self.store.tasks() if task['status'] not in TERMINAL]
        if len(active) >= 8:
            raise ValueError('Coding queue is full; finish or cancel an existing task')
        if parent and any(task.get('thread_id') == parent['thread_id'] for task in active):
            raise ValueError('This Codex thread is already running')
        task = {'id': str(uuid4()), 'project': project, 'cwd': str(root), 'prompt': prompt,
                'created_at': now(), 'updated_at': now(), 'status': 'queued', 'pending': [],
                'thread_id': parent['thread_id'] if parent else None, 'turn_id': None,
                'result': '', 'error': '', 'resume_id': resume_id, 'cancel_requested': False}
        self.store.save_task(task, 'task.queued', {'project': project})
        self.finished[task['id']] = Event()
        self.pool.submit(self._run, task['id'])
        return task

    def _run(self, identifier):
        adapter = self.adapter_factory(lambda message: self.receive(identifier, message))
        with self.lock:
            self.adapters[identifier] = adapter
        try:
            adapter.start()
            with self.lock:
                task = self.store.task(identifier)
                if task['cancel_requested']:
                    self._finish(task, 'cancelled')
                    return
            method = 'thread/resume' if task['thread_id'] else 'thread/start'
            params = {'cwd': task['cwd'], 'sandbox': 'read-only', 'approvalPolicy': 'untrusted', 'approvalsReviewer': 'user'}
            if task['thread_id']:
                params['threadId'] = task['thread_id']
            response = adapter.request(method, params)
            with self.lock:
                task = self.store.task(identifier)
                if task['status'] in TERMINAL:
                    return
                task.update(thread_id=response['thread']['id'], status='running')
                self.store.save_task(task, 'task.started', {'thread_id': task['thread_id']})
                if task['cancel_requested']:
                    self._finish(task, 'cancelled')
                    return
            response = adapter.request('turn/start', {'threadId': task['thread_id'], 'input': [{'type': 'text', 'text': task['prompt']}]})
            with self.lock:
                task = self.store.task(identifier)
                task['turn_id'] = response['turn']['id']
                self.store.save_task(task)
                cancel = task['cancel_requested'] and task['status'] not in TERMINAL
            if cancel:
                adapter.request('turn/interrupt', {'threadId': task['thread_id'], 'turnId': task['turn_id']})
            if not self.finished[identifier].wait(1800):
                with self.lock:
                    self._finish(self.store.task(identifier), 'timed_out', 'Coding task exceeded 30 minutes')
                adapter.close()
        except Exception as error:
            with self.lock:
                task = self.store.task(identifier)
                if task['status'] not in TERMINAL:
                    self._finish(task, 'cancelled' if task['cancel_requested'] else 'failed', str(error))
        finally:
            adapter.close()
            with self.lock:
                self.adapters.pop(identifier, None)
                self.finished.pop(identifier, None)

    def _finish(self, task, status, error=''):
        if task['status'] in TERMINAL:
            return
        task.update(status=status, error=JarvisMemory._safe_text(error), pending=[], updated_at=now())
        self.store.save_task(task, 'task.' + status, {'result': task['result'], 'error': task['error']})
        if task['id'] in self.finished:
            self.finished[task['id']].set()
        if status == 'completed' and self.on_complete:
            self.on_complete(task)

    def receive(self, identifier, message):
        with self.lock:
            task = self.store.task(identifier)
            if not task or task['status'] in TERMINAL:
                return
            method, params = message.get('method', ''), message.get('params', {})
            if params.get('threadId') and task.get('thread_id') and params['threadId'] != task['thread_id']:
                return
            if 'id' in message:
                allowed = {'item/commandExecution/requestApproval', 'item/fileChange/requestApproval', 'item/tool/requestUserInput'}
                if method not in allowed:
                    self.adapters[identifier].send({'id': message['id'], 'error': {'code': -32601, 'message': 'JARVIS does not grant this capability'}})
                    return
                pending = {'id': str(message['id']), 'rpc_id': message['id'], 'method': method, 'params': params}
                if method == 'item/fileChange/requestApproval':
                    pending['params'] = {**params, 'changes': task.get('file_previews', {}).get(params.get('itemId'), [])}
                pending['high_risk'] = self.high_risk(task, pending)
                if not pending['high_risk'] and method == 'item/commandExecution/requestApproval' and self.store.state('grant:' + self._grant_key(task, pending), {}).get('enabled'):
                    self.adapters[identifier].reply(message['id'], {'decision': 'accept'})
                    self.store.save_task(task, 'approval.applied', {'scope': 'previously approved exact command and project'})
                    return
                task['pending'].append(pending)
                task['status'] = 'waiting_input' if method.endswith('requestUserInput') else 'waiting_approval'
                self.store.save_task(task, 'agent.status', {'status': task['status'], 'pending': pending})
                return
            if method == 'turn/started':
                task['turn_id'] = params.get('turn', {}).get('id')
            if method == 'turn/completed':
                turn = params.get('turn', {})
                status = {'completed': 'completed', 'interrupted': 'cancelled'}.get(turn.get('status'), 'failed')
                self._finish(task, status, json.dumps(turn.get('error')) if turn.get('error') else '')
                return
            if method in {'transport/error', 'transport/closed'}:
                self._finish(task, 'failed', params.get('message', 'Codex connection closed'))
                return
            if method == 'serverRequest/resolved':
                task['pending'] = [p for p in task['pending'] if p['rpc_id'] != params.get('requestId')]
                task['status'] = 'running' if not task['pending'] else task['status']
            item = params.get('item', {})
            if item.get('type') == 'fileChange' and method == 'item/started':
                previews = task.setdefault('file_previews', {})
                # Preserve the concrete patch for approval, not just an opaque item ID.
                if len(json.dumps(item.get('changes', []))) <= 100000:
                    previews[item['id']] = item.get('changes', [])
                if len(previews) > 20:
                    del previews[next(iter(previews))]
            event_type = 'agent.status'
            if method == 'item/agentMessage/delta':
                event_type = 'agent.message'
            elif method in {'item/started', 'item/completed'}:
                event_type = 'tool.started' if method.endswith('started') else 'tool.completed'
                if item.get('type') == 'agentMessage' and method.endswith('completed'):
                    task['result'] = JarvisMemory._safe_text(item.get('text', ''))[:24000]
                if item.get('type') == 'fileChange' and method.endswith('completed') and item.get('status') == 'completed':
                    event_type = 'file.changed'
                if item.get('type') == 'commandExecution' and re.search(r'\b(pytest|unittest|test|verify)\b', item.get('command', '')):
                    event_type = 'test.started' if method.endswith('started') else 'test.completed'
            # Persist bounded raw evidence, never manufacture passing-test counts.
            safe = JarvisMemory._safe_text(json.dumps(params, ensure_ascii=False))
            event = {'method': method, 'detail': safe[:12000]}
            self.store.save_task(task, event_type, event)

    @staticmethod
    def high_risk(task, pending):
        params = pending['params']
        if pending['method'].endswith('requestUserInput'):
            return False
        if pending['method'] == 'item/fileChange/requestApproval':
            try:
                Path(params.get('grantRoot') or task['cwd']).resolve().relative_to(Path(task['cwd']))
                if not params.get('changes'):
                    return True
                for change in params['changes']:
                    path = Path(change['path'])
                    path = path if path.is_absolute() else Path(task['cwd']) / path
                    path.resolve().relative_to(Path(task['cwd']).resolve())
                    if change.get('kind', {}).get('type') == 'delete':
                        return True
                return False
            except (ValueError, KeyError, TypeError):
                return True
        if params.get('additionalPermissions') or params.get('networkApprovalContext'):
            return True
        try:
            Path(params.get('cwd') or task['cwd']).resolve().relative_to(Path(task['cwd']).resolve())
        except ValueError:
            return True
        command = params.get('command', '')
        # Only explicit diagnostic/test commands qualify for ordinary approval.
        if re.search(r'[;&|<>`\n]|\$\(|\b(push|reset|clean|rm|del|remove-item|shutdown|restart|sudo|install)\b', command, re.I):
            return True
        return not bool(re.fullmatch(r'(?:git (?:status|diff|log)(?: [\w./-]+)*|(?:python|python3|\.venv[/\\]Scripts[/\\]python.exe) -m (?:pytest|unittest)(?: [\w./-]+)*|(?:npm|flutter) (?:test|analyze)(?: [\w./-]+)*)', command))

    def answer(self, identifier, request_id, decision=None, answers=None):
        with self.lock:
            task = self.store.task(identifier)
            pending = next((p for p in task['pending'] if p['id'] == request_id), None) if task else None
            if not pending or identifier not in self.adapters or task['status'] in TERMINAL:
                raise ValueError('Approval/input is stale or belongs to another task')
            if pending['method'].endswith('requestUserInput'):
                questions = pending['params'].get('questions', [])
                allowed = {q['id'] for q in questions}
                if not answers or set(answers) != allowed or any(not isinstance(v, str) or len(v) > 4000 for v in answers.values()):
                    raise ValueError('Answer each requested question')
                result = {'answers': {key: {'answers': [value]} for key, value in answers.items()}}
            else:
                result = {'decision': self.permission_manager.authorize_codex(decision, pending['high_risk'])}
                if decision == 'always_allow':
                    if pending['method'] != 'item/commandExecution/requestApproval':
                        raise ValueError('Always Allow is limited to an exact diagnostic command in this project')
                    key = self._grant_key(task, pending)
                    self.store.set_state('grant:' + key, {'project': task['project'], 'method': pending['method'], 'params': pending['params'], 'enabled': True})
            self.adapters[identifier].reply(pending['rpc_id'], result)
            task['pending'] = [p for p in task['pending'] if p['id'] != request_id]
            task['status'] = 'running' if not task['pending'] else task['status']
            self.store.save_task(task, 'agent.status', {'status': task['status'], 'decision': decision or 'input_submitted'})

    @staticmethod
    def _grant_key(task, pending):
        scope = [task['cwd'], pending['method'], pending['params'].get('command'), pending['params'].get('grantRoot'), pending['params'].get('cwd')]
        return sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest()

    def cancel(self, identifier):
        with self.lock:
            task = self.store.task(identifier)
            if not task or task['status'] in TERMINAL:
                return task
            task.update(cancel_requested=True, status='cancelling')
            self.store.save_task(task, 'agent.status', {'status': 'cancelling'})
            adapter = self.adapters.get(identifier)
        if adapter and task.get('turn_id'):
            adapter.request('turn/interrupt', {'threadId': task['thread_id'], 'turnId': task['turn_id']})
        return self.store.task(identifier)
