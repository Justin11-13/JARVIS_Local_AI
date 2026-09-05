import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.rag.obsidian_loader import load_obsidian_documents
from skills.obsidian import append_obsidian_note, create_obsidian_note, update_obsidian_note, read_obsidian_note, search_obsidian_notes


class ObsidianIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.vault = {
            "id": "test-vault",
            "name": "Test Vault",
            "path": self.root,
            "default_access": "excluded",
        }

    def tearDown(self):
        self.temporary.cleanup()

    @patch("skills.obsidian.load_obsidian_vaults")
    def test_search_then_read_shared_tutorial_and_privacy(self, vaults):
        vaults.return_value = [self.vault]
        for name, access in (("Tutorial", "rag"), ("Private", "local-only"), ("Excluded", "excluded")):
            (self.root / f"{name}.md").write_text(f"---\njarvis_access: {access}\n---\nPython learning content", encoding="utf-8")
        self.assertEqual(search_obsidian_notes("Python"), "test-vault:Tutorial.md")
        self.assertIn("Python learning content", read_obsidian_note("test-vault", "Tutorial.md"))
        for path in ("Private.md", "Excluded.md", "../Outside.md"):
            with self.subTest(path=path), self.assertRaises((ValueError, FileNotFoundError)):
                read_obsidian_note("test-vault", path)

    @patch("skills.obsidian.load_obsidian_vaults")
    def test_read_reports_truncation_and_rejects_oversized_notes(self, vaults):
        vaults.return_value = [self.vault]
        target = self.root / "Long.md"
        target.write_text("---\njarvis_access: rag\n---\n" + "a" * 7000, encoding="utf-8")
        self.assertIn("Truncated", read_obsidian_note("test-vault", "Long.md"))
        target.write_text("a" * 100001, encoding="utf-8")
        with self.assertRaises(ValueError):
            read_obsidian_note("test-vault", "Long.md")

    def test_loader_only_indexes_explicitly_shared_notes(self):
        (self.root / "Shared.md").write_text(
            "---\ntitle: Shared Note\ntags: [python, study]\njarvis_access: rag\n---\n# Shared\nUseful content.",
            encoding="utf-8",
        )
        (self.root / "Private.md").write_text("# Private\nSecret.", encoding="utf-8")
        protected = self.root / ".obsidian"
        protected.mkdir()
        (protected / "Config.md").write_text("---\njarvis_access: rag\n---\nHidden", encoding="utf-8")

        documents = load_obsidian_documents(self.vault)

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["title"], "Shared Note")
        self.assertEqual(documents[0]["tags"], ["python", "study"])
        self.assertNotIn("C:\\", documents[0]["source"])

    @patch("skills.obsidian._refresh_index", return_value=" Index updated.")
    @patch("skills.obsidian.load_obsidian_vaults")
    def test_write_tools_are_vault_bounded_and_never_overwrite(self, vaults, _refresh):
        vaults.return_value = [self.vault]
        result = create_obsidian_note("test-vault", "Inbox/New Note", "Hello")
        self.assertIn("Created", result)
        created = (self.root / "Inbox" / "New Note.md").read_text(encoding="utf-8")
        self.assertIn("title: New Note", created)
        self.assertIn("jarvis_access: rag", created)
        self.assertIn("status: current", created)
        self.assertIn("authority: personal", created)
        self.assertTrue(created.endswith("Hello\n"))
        with self.assertRaises(FileExistsError):
            create_obsidian_note("test-vault", "Inbox/New Note", "Replacement")
        append_obsidian_note("test-vault", "Inbox/New Note", "World")
        self.assertTrue((self.root / "Inbox" / "New Note.md").read_text(encoding="utf-8").endswith("Hello\nWorld\n"))
        update_obsidian_note("test-vault", "Inbox/New Note", "World", "Updated")
        self.assertTrue((self.root / "Inbox" / "New Note.md").read_text(encoding="utf-8").endswith("Hello\nUpdated\n"))
        with self.assertRaises(ValueError):
            create_obsidian_note("test-vault", "../Outside", "Blocked")
        with self.assertRaises(ValueError):
            create_obsidian_note("test-vault", ".obsidian/config", "Blocked")


if __name__ == "__main__":
    unittest.main()
