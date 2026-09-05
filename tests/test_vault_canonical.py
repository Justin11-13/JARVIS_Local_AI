from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from services.rag.source_registry import knowledge_sources
from services.rag.obsidian_loader import load_obsidian_documents
from services.rag.knowledge_router import route_knowledge


class VaultCanonicalTests(unittest.TestCase):
    @patch('services.rag.source_registry.load_obsidian_vaults', return_value=[])
    def test_no_implicit_repo_fallback(self, _vaults):
        self.assertEqual(knowledge_sources(), [])

    def test_jarvis_domain_metadata_and_instruction_exclusion(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'JARVIS/Knowledge').mkdir(parents=True)
            note = root / 'JARVIS/Knowledge/Component.md'
            note.write_text('---\njarvis_access: rag\nupdated: 2026-09-05\ncreated: 2026-09-04\ntype: knowledge\nproject: JARVIS\n---\n# Component\nUseful knowledge.', encoding='utf-8')
            (root / 'JARVIS/AGENTS.md.md').write_text('---\njarvis_access: rag\n---\nInstruction data should not be indexed.', encoding='utf-8')
            documents = load_obsidian_documents({'id': 'wiki', 'name': 'Wiki', 'path': root, 'default_access': 'excluded'})
            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0]['knowledge_domain'], 'jarvis')
            self.assertEqual(documents[0]['updated_at'], '2026-09-05')
            self.assertEqual(documents[0]['created_at'], '2026-09-04')
            self.assertEqual(documents[0]['project'], 'JARVIS')
            self.assertIn('jarvis', route_knowledge('JARVIS 现在如何存知识？').domains)
            self.assertIn('jarvis', route_knowledge('我的 Obsidian 笔记').domains)
