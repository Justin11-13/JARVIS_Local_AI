"""Local SQLite source of truth for conversations, curated memory and agent events."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY, project TEXT NOT NULL DEFAULT '', created_at TEXT, ended_at TEXT, summary TEXT NOT NULL DEFAULT '', extracted_until INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS turns(id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL, user TEXT, assistant TEXT, speech TEXT, created_at TEXT);
                CREATE INDEX IF NOT EXISTS turns_conversation ON turns(conversation_id,id);
                CREATE TABLE IF NOT EXISTS memory_items(id TEXT PRIMARY KEY, identity_key TEXT UNIQUE, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS coding_tasks(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, type TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS events_task ON events(task_id,id);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def state(self, key, default=None):
        with self.connect() as db:
            row = db.execute('SELECT body FROM state WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_state(self, key, value):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO state VALUES (?,?)', (key, json.dumps(value, ensure_ascii=False)))

    def conversation(self, project=None):
        active = self.state('active_conversation')
        with self.connect() as db:
            row = db.execute('SELECT * FROM conversations WHERE id=? AND ended_at IS NULL', (active,)).fetchone()
            if row and (project is None or row['project'] == project):
                return active
            identifier = str(uuid4())
            db.execute('INSERT INTO conversations(id,project,created_at) VALUES (?,?,?)', (identifier, project or '', now()))
        self.set_state('active_conversation', identifier)
        return identifier

    def conversation_info(self, identifier):
        with self.connect() as db:
            row = db.execute('SELECT * FROM conversations WHERE id=?', (identifier,)).fetchone()
        return dict(row) if row else None

    def add_turn(self, conversation_id, user, assistant, speech='', created_at=None):
        with self.connect() as db:
            return db.execute('INSERT INTO turns(conversation_id,user,assistant,speech,created_at) VALUES (?,?,?,?,?)',
                              (conversation_id, user, assistant, speech, created_at or now())).lastrowid

    def turns(self, conversation_id, limit=100, after=0, oldest=False):
        with self.connect() as db:
            order = 'ASC' if oldest else 'DESC'
            rows = db.execute(f'SELECT * FROM turns WHERE conversation_id=? AND id>? ORDER BY id {order} LIMIT ?',
                              (conversation_id, after, limit)).fetchall()
        return [dict(row) for row in (rows if oldest else reversed(rows))]

    def end(self, conversation_id):
        with self.connect() as db:
            db.execute('UPDATE conversations SET ended_at=? WHERE id=?', (now(), conversation_id))

    def extracted(self, conversation_id, until, summary):
        with self.connect() as db:
            db.execute('UPDATE conversations SET extracted_until=?,summary=? WHERE id=?', (until, summary, conversation_id))

    def items(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT body FROM memory_items')]

    def save_item(self, item, identity):
        with self.connect() as db:
            db.execute('INSERT INTO memory_items(id,identity_key,body) VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                       (item['id'], identity, json.dumps(item, ensure_ascii=False)))

    def task(self, task_id):
        with self.connect() as db:
            row = db.execute('SELECT body FROM coding_tasks WHERE id=?', (task_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def tasks(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT body FROM coding_tasks ORDER BY rowid DESC LIMIT 100')]

    def save_task(self, task, event_type=None, event=None):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO coding_tasks VALUES (?,?)', (task['id'], json.dumps(task, ensure_ascii=False)))
            if event_type:
                db.execute('INSERT INTO events(task_id,type,body,created_at) VALUES (?,?,?,?)',
                           (task['id'], event_type, json.dumps(event or {}, ensure_ascii=False), now()))

    def events(self, task_id, after=0):
        with self.connect() as db:
            rows = db.execute('SELECT * FROM events WHERE task_id=? AND id>? ORDER BY id LIMIT 200', (task_id, after)).fetchall()
        return [{**dict(row), 'body': json.loads(row['body'])} for row in rows]
