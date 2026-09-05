import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from services.jarvis_memory import JarvisMemory
from services.memory_manager import MemoryManager, Extraction
from services.context_builder import build_context


class LongTermMemoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.memory = JarvisMemory(database_path=self.root / 'memory.db', max_turns=6)
        self.brain = Mock()
        self.brain.is_configured.return_value = False
        self.manager = MemoryManager(self.memory, self.brain)
        self.addCleanup(lambda: self.manager.pool.shutdown(wait=True))
        self.vault = {'id': 'test', 'name': 'Test', 'path': self.root / 'vault', 'default_access': 'excluded'}
        self.vault['path'].mkdir()
        self.memory.remember('We might choose SQLite, but this is not a final decision.', 'This is only a proposal.')

    def candidate(self, **changes):
        item = {'type': 'decision', 'title': 'Database choice', 'summary': 'Consider SQLite.',
                'importance': .9, 'confidence': .99, 'facts': [], 'decisions': ['Choose SQLite'],
                'todos': [], 'related': [], 'evidence': [{'turn_id': self.memory.store.turns(self.memory.conversation_id)[0]['id'],
                    'role': 'user', 'quote': 'We might choose SQLite'}]}
        item.update(changes)
        return Extraction.model_validate({'summary': 'A database proposal, not a decision.', 'items': [item]})

    def ingest(self, candidate=None):
        return self.manager.ingest(self.memory.conversation_id, self.memory.store.turns(self.memory.conversation_id), candidate or self.candidate())

    def test_high_confidence_proposal_still_needs_explicit_confirmation(self):
        item = self.ingest()[0]
        self.assertEqual(item['status'], 'proposed')
        context, _ = build_context(self.memory, 'Database', 'question')
        self.assertNotIn('Consider SQLite', context)
        self.manager.review(item['id'], 'confirmed')
        context, _ = build_context(self.memory, 'Database', 'question')
        self.assertIn('Consider SQLite', context)
        self.manager.review(item['id'], 'rejected')
        self.assertNotIn('Consider SQLite', build_context(self.memory, 'Database', 'question')[0])

    def test_restart_restores_project_and_explicit_resume_restores_turns(self):
        self.memory.set_project('Project B')
        self.memory.remember('Current task is migration.', 'Migration remains in progress.')
        identifier = self.memory.conversation_id
        restarted = JarvisMemory(database_path=self.root / 'memory.db')
        self.assertEqual(restarted.conversation_id, identifier)
        self.assertEqual(restarted.store.conversation_info(identifier)['project'], 'Project B')
        restarted.clear()
        restarted.resume(identifier)
        self.assertEqual(restarted.conversation_id, identifier)
        self.assertEqual(restarted.store.turns(identifier)[0]['user'], 'Current task is migration.')

    def test_unsupported_evidence_and_low_value_are_not_saved(self):
        self.assertEqual(self.ingest(self.candidate(importance=.2)), [])
        self.assertEqual(self.ingest(self.candidate(evidence=[{'turn_id': 999, 'role': 'user', 'quote': 'invented evidence'}])), [])
        self.assertEqual(self.ingest(self.candidate(evidence=[{'turn_id': 1, 'role': 'user', 'quote': 'user confirmed this'}])), [])

    def test_deduplication_and_project_isolation(self):
        item = self.ingest()[0]
        self.assertEqual(self.ingest(), [])
        self.memory.set_project('Project B')
        self.memory.remember('We might choose SQLite, but this is not a final decision.', 'Only proposed')
        item_b = self.ingest()[0]
        self.manager.review(item_b['id'], 'confirmed')
        self.memory.set_project('Project C')
        self.assertNotIn(item_b['id'], build_context(self.memory, 'Database', 'question')[0])
        self.assertEqual(item['status'], 'proposed')

    def test_sqlite_preserves_raw_history_and_legacy_json(self):
        legacy = self.root / 'legacy.json'
        original = json.dumps({'turns': [{'user': 'old', 'assistant': 'answer', 'speech': 'answer', 'created_at': '2026-01-01'}]})
        legacy.write_text(original, encoding='utf-8')
        path = self.root / 'migration.db'
        memory = JarvisMemory(storage_path=legacy, database_path=path, max_turns=2)
        identifier = memory.conversation_id
        for i in range(12):
            memory.remember(str(i), 'answer')
        restored = JarvisMemory(storage_path=legacy, database_path=path, max_turns=2)
        self.assertEqual(len(restored.store.turns(identifier)), 13)
        self.assertEqual(len(restored.history()), 2)
        self.assertEqual(legacy.read_text(encoding='utf-8'), original)
        self.assertEqual(restored.conversation_id, identifier)
        self.assertEqual([r['user'] for r in restored.store.turns(identifier, 2, oldest=True)], ['old', '0'])

    def test_context_size_is_bounded(self):
        for _ in range(10):
            self.memory.remember('x' * 10000, 'y' * 10000)
        message, history = build_context(self.memory, 'hello', 'z' * 50000)
        self.assertLessEqual(len(message), 34000)
        self.assertLessEqual(sum(len(t['parts'][0]['text']) for t in history), 24000)

    @patch('skills.obsidian._refresh_index', return_value='Index updated')
    def test_merge_preserves_user_content_is_idempotent_and_blocks_stale_preview(self, _refresh):
        item = self.ingest()[0]
        self.manager.review(item['id'], 'confirmed')
        path = self.vault['path'] / 'Database choice.md'
        path.write_text('---\njarvis_access: rag\n---\n# My original notes\nKeep this text.\n', encoding='utf-8')
        with patch('skills.obsidian.load_obsidian_vaults', return_value=[self.vault]):
            preview = self.manager.preview(item['id'], 'test')
            self.assertEqual(preview['relative_path'], path.name)
            self.manager.publish(preview['token'])
            self.assertIn('Keep this text.', path.read_text(encoding='utf-8'))
            again = self.manager.preview(item['id'], 'test')
            self.manager.publish(again['token'])
            self.assertEqual(path.read_text(encoding='utf-8').count(f"jarvis-memory:{item['id']}:start"), 1)
            stale = self.manager.preview(item['id'], 'test')
            path.write_text(path.read_text(encoding='utf-8') + 'New manual edit', encoding='utf-8')
            with self.assertRaises(ValueError):
                self.manager.publish(stale['token'])
            self.assertIn('New manual edit', path.read_text(encoding='utf-8'))

    def test_private_or_unconfirmed_note_cannot_be_published(self):
        item = self.ingest()[0]
        with self.assertRaises(ValueError):
            self.manager.preview(item['id'], 'test')
        self.manager.review(item['id'], 'confirmed')
        (self.vault['path'] / 'Private.md').write_text('Private data', encoding='utf-8')
        with patch('skills.obsidian.load_obsidian_vaults', return_value=[self.vault]), self.assertRaises(ValueError):
            self.manager.preview(item['id'], 'test', 'Private.md')

    @patch('skills.obsidian._refresh_index', return_value='Index updated')
    def test_published_memory_rereads_canonical_note_and_honors_withdrawal(self, _refresh):
        item = self.ingest()[0]
        self.manager.review(item['id'], 'confirmed')
        with patch('skills.obsidian.load_obsidian_vaults', return_value=[self.vault]):
            preview = self.manager.preview(item['id'], 'test')
            self.assertTrue(preview['relative_path'].startswith('JARVIS/Memory/Decisions/'))
            self.manager.publish(preview['token'])
            path = self.vault['path'] / preview['relative_path']
            path.write_text('---\njarvis_access: rag\nstatus: current\n---\nDatabase is now PostgreSQL.', encoding='utf-8')
            self.assertIn('Database is now PostgreSQL.', build_context(self.memory, 'Database', 'question')[0])
            self.assertNotIn('Consider SQLite', build_context(self.memory, 'Database', 'question')[0])
            path.write_text('---\njarvis_access: local-only\n---\nDatabase is private.', encoding='utf-8')
            self.assertNotIn('Database is private.', build_context(self.memory, 'Database', 'question')[0])
            path.unlink()
            self.assertNotIn('Consider SQLite', build_context(self.memory, 'Database', 'question')[0])

    def test_extraction_errors_are_visible_and_do_not_advance_cursor(self):
        self.brain.generate_json.side_effect = RuntimeError('Provider unavailable')
        identifier = self.memory.conversation_id
        self.manager._extract(identifier, self.memory.store.conversation_info(identifier), self.memory.store.turns(identifier))
        self.assertEqual(self.memory.store.state('extraction')['status'], 'failed')
        self.assertEqual(self.memory.store.conversation_info(identifier)['extracted_until'], 0)


if __name__ == '__main__':
    unittest.main()
