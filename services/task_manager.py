from dataclasses import asdict, dataclass
from datetime import datetime
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

    @property
    def date(self) -> str:
        return self.created_at.strftime("%Y-%m-%d")

    @property
    def duration_seconds(self) -> Optional[float]:
        if not self.started_at or not self.completed_at:
            return None

        return round(
            (self.completed_at - self.started_at).total_seconds(),
            2,
        )

    def to_dict(self) -> dict:
        data = asdict(self)

        data["created_at"] = self.created_at.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        data["started_at"] = (
            self.started_at.strftime("%Y-%m-%d %H:%M:%S")
            if self.started_at
            else None
        )

        data["completed_at"] = (
            self.completed_at.strftime("%Y-%m-%d %H:%M:%S")
            if self.completed_at
            else None
        )

        data["date"] = self.date
        data["duration_seconds"] = self.duration_seconds

        return data


class TaskManager:
    VALID_STATUSES = {
        "queued",
        "running",
        "waiting_approval",
        "completed",
        "completed_with_warnings",
        "failed",
        "cancelled",
    }

    def __init__(self):
        self.tasks: dict[str, Task] = {}

    def create_task(
        self,
        title: str,
        agent: str,
    ) -> Task:
        task = Task(
            id=f"task_{uuid4().hex[:8]}",
            title=title,
            agent=agent,
            status="queued",
            created_at=datetime.now(),
        )

        self.tasks[task.id] = task

        return task

    def start_task(
        self,
        task_id: str,
    ) -> Optional[Task]:
        task = self.tasks.get(task_id)

        if not task:
            return None

        task.status = "running"
        task.started_at = datetime.now()

        return task

    def complete_task(
        self,
        task_id: str,
        result: str = "",
    ) -> Optional[Task]:
        task = self.tasks.get(task_id)

        if not task:
            return None

        task.status = "completed"
        task.result = result
        task.completed_at = datetime.now()

        return task

    def fail_task(
        self,
        task_id: str,
        error: str,
    ) -> Optional[Task]:
        task = self.tasks.get(task_id)

        if not task:
            return None

        task.status = "failed"
        task.error = error
        task.completed_at = datetime.now()

        return task

    def get_task(
        self,
        task_id: str,
    ) -> Optional[dict]:
        task = self.tasks.get(task_id)

        if not task:
            return None

        return task.to_dict()

    def list_tasks(self) -> list[dict]:
        tasks = sorted(
            self.tasks.values(),
            key=lambda task: task.created_at,
            reverse=True,
        )

        return [
            task.to_dict()
            for task in tasks
        ]