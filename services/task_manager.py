import json
from dataclasses import MISSING, asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Optional
from uuid import uuid4


@dataclass
class Task:
    id: str
    title: str
    agent: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: str = ""
    error: str = ""
    kind: str = ""
    payload: dict = field(default_factory=dict)
    progress: int = 0
    progress_message: str = ""
    verification: str = ""
    attempt: int = 1
    parent_task_id: Optional[str] = None
    timeout_seconds: int = 300
    cancellation_requested: bool = False
    notification: str = ""

    @property
    def date(self) -> str:
        return self.created_at.strftime("%Y-%m-%d")

    @property
    def duration_seconds(self) -> Optional[float]:
        if not self.started_at:
            return None
        end = self.completed_at or datetime.now()
        return round((end - self.started_at).total_seconds(), 2)

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("created_at", "started_at", "completed_at"):
            value = data[key]
            data[key] = value.strftime("%Y-%m-%d %H:%M:%S") if value else None
        data["date"] = self.date
        data["duration_seconds"] = self.duration_seconds
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        values = {key: data.get(key) for key in cls.__dataclass_fields__}
        for key in ("created_at", "started_at", "completed_at"):
            values[key] = datetime.strptime(values[key], "%Y-%m-%d %H:%M:%S") if values.get(key) else None
        values["created_at"] = values["created_at"] or datetime.now()
        for key, definition in cls.__dataclass_fields__.items():
            if values.get(key) is not None:
                continue
            if definition.default is not MISSING:
                values[key] = definition.default
            elif definition.default_factory is not MISSING:
                values[key] = definition.default_factory()
        return cls(**values)


class TaskManager:
    ACTIVE_STATUSES = {"queued", "running", "waiting_approval", "cancelling", "verifying"}
    VALID_STATUSES = ACTIVE_STATUSES | {
        "completed", "completed_with_warnings", "failed", "cancelled",
        "verification_failed", "timed_out",
    }

    def __init__(self, storage_path: Path | str | None = None, database_path=None):
        self.tasks: dict[str, Task] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        self._lock = RLock()
        self.store = None
        self._skip_legacy_write = database_path is not None
        self._load()
        if database_path is not None:
            from services.memory_store import MemoryStore
            self.store = MemoryStore(database_path)
            stored = self.store.state('native_tasks')
            if stored is not None:
                self.tasks = {raw['id']: Task.from_dict(raw) for raw in stored}
                for task in self.tasks.values():
                    if task.status in self.ACTIVE_STATUSES:
                        task.status = 'failed'
                        task.error = 'JARVIS restarted before this task finished.'
                        task.completed_at = datetime.now()
            self._save()

    def _load(self) -> None:
        if not self.storage_path or not self.storage_path.exists():
            return
        try:
            raw_tasks = json.loads(self.storage_path.read_text(encoding="utf-8"))
            for raw_task in raw_tasks:
                task = Task.from_dict(raw_task)
                if task.status in self.ACTIVE_STATUSES:
                    task.status = "failed"
                    task.error = "JARVIS restarted before this task finished. Retry it to continue."
                    task.completed_at = datetime.now()
                self.tasks[task.id] = task
            self._save()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.tasks = {}

    def _save(self) -> None:
        if self.store is not None:
            self.store.set_state('native_tasks', [task.to_dict() for task in self.tasks.values()])
            return
        if self._skip_legacy_write:
            return
        if not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.storage_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps([task.to_dict() for task in self.tasks.values()], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self.storage_path)

    def create_task(
        self, title: str, agent: str, *, kind: str = "", payload: dict | None = None,
        timeout_seconds: int = 300, attempt: int = 1, parent_task_id: str | None = None,
    ) -> Task:
        with self._lock:
            task = Task(
                id=f"task_{uuid4().hex[:8]}", title=title, agent=agent, status="queued",
                created_at=datetime.now(), kind=kind, payload=payload or {},
                timeout_seconds=timeout_seconds, attempt=attempt, parent_task_id=parent_task_id,
                progress_message="Waiting for an available worker.",
            )
            self.tasks[task.id] = task
            self._save()
            return task

    def update_task(self, task_id: str, **changes) -> Optional[Task]:
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            for key, value in changes.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self._save()
            return task

    def start_task(self, task_id: str) -> Optional[Task]:
        return self.update_task(
            task_id, status="running", started_at=datetime.now(), progress=1,
            progress_message="Task started.", cancellation_requested=False,
        )

    def update_progress(self, task_id: str, progress: int, message: str) -> Optional[Task]:
        return self.update_task(task_id, progress=max(0, min(100, progress)), progress_message=message)

    def mark_verifying(self, task_id: str, message: str = "Verifying the result.") -> Optional[Task]:
        return self.update_task(task_id, status="verifying", progress=95, progress_message=message)

    def complete_task(self, task_id: str, result: str = "", verification: str = "") -> Optional[Task]:
        return self.update_task(
            task_id, status="completed", result=result, verification=verification,
            progress=100, progress_message="Completed and verified.", completed_at=datetime.now(),
        )

    def fail_task(self, task_id: str, error: str, status: str = "failed") -> Optional[Task]:
        if status not in {"failed", "verification_failed", "timed_out"}:
            status = "failed"
        return self.update_task(
            task_id, status=status, error=error, progress_message=error, completed_at=datetime.now(),
        )

    def request_cancellation(self, task_id: str) -> Optional[Task]:
        with self._lock:
            task = self.tasks.get(task_id)
            if not task or task.status not in self.ACTIVE_STATUSES:
                return None
            task.cancellation_requested = True
            task.status = "cancelling"
            task.progress_message = "Cancellation requested; stopping at the next safe checkpoint."
            self._save()
            return task

    def cancel_task(self, task_id: str) -> Optional[Task]:
        return self.update_task(
            task_id, status="cancelled", cancellation_requested=True,
            progress_message="Task cancelled.", completed_at=datetime.now(),
        )

    def is_cancellation_requested(self, task_id: str) -> bool:
        with self._lock:
            task = self.tasks.get(task_id)
            return bool(task and task.cancellation_requested)

    def get_task(self, task_id: str) -> Optional[dict]:
        with self._lock:
            task = self.tasks.get(task_id)
            return task.to_dict() if task else None

    def list_tasks(self) -> list[dict]:
        with self._lock:
            tasks = sorted(self.tasks.values(), key=lambda task: task.created_at, reverse=True)
            return [task.to_dict() for task in tasks]
