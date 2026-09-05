"""Wire memory and coding to the existing Core without enabling arbitrary executors."""
from services.memory_manager import MemoryManager
from services.coding_service import CodingService


class AssistantRuntime:
    def __init__(self, memory, gemini, permission_manager=None):
        self.memory = memory
        self.memories = MemoryManager(memory, gemini)
        self.coding = CodingService(memory.store, self.coding_complete, permission_manager=permission_manager)

    def coding_complete(self, task):
        # Evidence is archived as assistant output; it cannot confirm a decision.
        store = self.memory.store
        identifier = 'coding:' + task['id']
        with store.connect() as db:
            db.execute('INSERT OR IGNORE INTO conversations(id,project,created_at,ended_at) VALUES (?,?,?,?)',
                       (identifier, task['project'], task['created_at'], task['updated_at']))
        import json
        with store.connect() as db:
            rows = db.execute("SELECT id,type,body FROM events WHERE task_id=? AND type IN ('file.changed','test.completed') ORDER BY id DESC LIMIT 50", (task['id'],)).fetchall()
        evidence = [{'id': row['id'], 'type': row['type'], 'body': json.loads(row['body'])} for row in reversed(rows)]
        store.add_turn(identifier, task['prompt'], task['result'] + '\nEvidence:\n' + json.dumps(evidence, ensure_ascii=False)[:16000])
        self.memories.trigger(identifier, force=True)
