from pathlib import Path
import tempfile
from threading import Event
import unittest
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.assistant_routes import routes
from services.coding_service import CodingService
from services.jarvis_memory import JarvisMemory
from services.memory_store import MemoryStore


class CodingServiceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.store = MemoryStore(self.root / 'state.db')
        self.service = CodingService(self.store)
        self.addCleanup(lambda: self.service.pool.shutdown(wait=True))
        self.adapter = Mock()
        self.task = {'id': 'one', 'project': 'Test', 'cwd': str(self.root), 'prompt': 'Inspect', 'status': 'running',
                     'created_at': '', 'updated_at': '', 'thread_id': 'thread-one', 'turn_id': 'turn-one',
                     'pending': [], 'result': '', 'error': '', 'cancel_requested': False}
        self.store.save_task(self.task)
        self.service.adapters['one'] = self.adapter
        self.service.finished['one'] = Event()

    def approval(self, identifier=1, command='git status', method='item/commandExecution/requestApproval', **params):
        self.service.receive('one', {'id': identifier, 'method': method, 'params': {
            'threadId': 'thread-one', 'turnId': 'turn-one', 'command': command, **params}})

    def test_approval_is_bound_to_request_and_replay_is_rejected(self):
        self.approval()
        self.service.answer('one', '1', decision='allow_once')
        self.adapter.reply.assert_called_once_with(1, {'decision': 'accept'})
        with self.assertRaises(ValueError):
            self.service.answer('one', '1', decision='allow_once')
        with self.assertRaises(ValueError):
            self.service.answer('other', '1', decision='allow_once')

    def test_exact_saved_grant_does_not_apply_to_another_command(self):
        self.approval()
        self.service.answer('one', '1', decision='always_allow')
        self.approval(identifier=2)
        self.adapter.reply.assert_called_with(2, {'decision': 'accept'})
        self.approval(identifier=3, command='git diff')
        self.assertEqual(len(self.store.task('one')['pending']), 1)

    def test_high_risk_and_unknown_requests_fail_closed(self):
        self.approval(command='git push origin main')
        with self.assertRaises(ValueError):
            self.service.answer('one', '1', decision='allow_once')
        self.adapter.reply.assert_not_called()
        self.service.answer('one', '1', decision='deny')
        self.adapter.reply.assert_called_with(1, {'decision': 'decline'})
        self.service.receive('one', {'id': 2, 'method': 'item/permissions/requestApproval', 'params': {}})
        self.assertIn('error', self.adapter.send.call_args.args[0])

    def test_input_requires_exact_question_ids(self):
        self.approval(method='item/tool/requestUserInput', questions=[{'id': 'choice'}])
        with self.assertRaises(ValueError):
            self.service.answer('one', '1', answers={'wrong': 'yes'})
        self.service.answer('one', '1', answers={'choice': 'yes'})
        self.adapter.reply.assert_called_with(1, {'answers': {'choice': {'answers': ['yes']}}})

    def test_file_approval_includes_patch_and_blocks_outside_or_deleted_paths(self):
        changes = [{'path': str(self.root / 'safe.txt'), 'kind': {'type': 'add'}, 'diff': 'hello'}]
        self.service.receive('one', {'method': 'item/started', 'params': {'item': {'id': 'patch', 'type': 'fileChange', 'changes': changes}}})
        self.approval(method='item/fileChange/requestApproval', itemId='patch')
        pending = self.store.task('one')['pending'][0]
        self.assertEqual(pending['params']['changes'], changes)
        self.assertFalse(pending['high_risk'])
        pending['params']['changes'][0]['kind']['type'] = 'delete'
        self.assertTrue(self.service.high_risk(self.task, pending))

    def test_cancel_waits_for_confirmed_terminal_event(self):
        self.service.cancel('one')
        self.assertEqual(self.store.task('one')['status'], 'cancelling')
        self.adapter.request.assert_called_with('turn/interrupt', {'threadId': 'thread-one', 'turnId': 'turn-one'})
        self.service.receive('one', {'method': 'turn/completed', 'params': {'turn': {'status': 'interrupted'}}})
        self.assertEqual(self.store.task('one')['status'], 'cancelled')

    def test_only_successful_file_event_is_a_file_change(self):
        self.service.receive('one', {'method': 'item/completed', 'params': {'item': {'type': 'fileChange', 'status': 'declined'}}})
        self.assertEqual(self.store.events('one')[-1]['type'], 'tool.completed')
        self.service.receive('one', {'method': 'item/completed', 'params': {'item': {'type': 'fileChange', 'status': 'completed'}}})
        self.assertEqual(self.store.events('one')[-1]['type'], 'file.changed')

    def test_sse_replays_after_cursor_without_duplicates(self):
        runtime = Mock()
        runtime.memory = JarvisMemory(database_path=self.root / 'state.db')
        runtime.coding = self.service
        app = FastAPI()
        app.include_router(routes(runtime, lambda: {'Test': {'path': str(self.root)}}))
        client = TestClient(app)
        self.store.save_task(self.task, 'tool.started', {'label': 'first'})
        cursor = self.store.events('one')[-1]['id']
        self.task['status'] = 'completed'
        self.store.save_task(self.task, 'task.completed', {'label': 'second'})
        response = client.get('/tasks/one/events', headers={'Last-Event-ID': str(cursor)})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('"first"', response.text)
        self.assertIn('task.completed', response.text)
        self.assertEqual(client.get('/tasks/unknown').status_code, 404)
        self.assertEqual(client.post('/api/coding/tasks', json={'project': 'unknown', 'prompt': 'change'}).status_code, 400)
        self.assertEqual(client.post('/api/memory/extract', headers={'Origin': 'https://untrusted.example'}).status_code, 403)


if __name__ == '__main__':
    unittest.main()
