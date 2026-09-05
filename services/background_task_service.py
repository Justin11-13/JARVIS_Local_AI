from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Event, Lock, Timer
from typing import Callable

from services.notification_service import NotificationService
from services.task_manager import TaskManager


class TaskCancelled(Exception):
    pass


@dataclass
class TaskContext:
    task_id: str
    task_manager: TaskManager
    cancel_event: Event

    def checkpoint(self, progress: int, message: str) -> None:
        if self.cancel_event.is_set() or self.task_manager.is_cancellation_requested(self.task_id):
            raise TaskCancelled()
        self.task_manager.update_progress(self.task_id, progress, message)


Runner = Callable[[TaskContext, dict], str]
Verifier = Callable[[dict, str], tuple[bool, str]]


class BackgroundTaskService:
    """Small local worker pool for declared, permission-controlled jobs."""

    def __init__(
        self,
        task_manager: TaskManager,
        notification_service: NotificationService,
        max_workers: int = 2,
    ):
        self.task_manager = task_manager
        self.notification_service = notification_service
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="jarvis-task")
        self._handlers: dict[str, tuple[Runner, Verifier]] = {}
        self._cancel_events: dict[str, Event] = {}
        self._lock = Lock()

    def register(self, kind: str, runner: Runner, verifier: Verifier) -> None:
        self._handlers[kind] = (runner, verifier)

    def submit(
        self, kind: str, title: str, payload: dict | None = None,
        *, timeout_seconds: int = 300, attempt: int = 1, parent_task_id: str | None = None,
    ) -> dict:
        if kind not in self._handlers:
            raise ValueError(f"Unsupported background task type: {kind}")
        if timeout_seconds < 1 or timeout_seconds > 3600:
            raise ValueError("timeout_seconds must be between 1 and 3600.")

        task = self.task_manager.create_task(
            title=title.strip() or kind, agent="jarvis_background", kind=kind,
            payload=payload or {}, timeout_seconds=timeout_seconds,
            attempt=attempt, parent_task_id=parent_task_id,
        )
        event = Event()
        with self._lock:
            self._cancel_events[task.id] = event
        self._executor.submit(self._run, task.id, event)
        return task.to_dict()

    def _run(self, task_id: str, cancel_event: Event) -> None:
        task = self.task_manager.get_task(task_id)
        if not task:
            return
        runner, verifier = self._handlers[task["kind"]]
        timeout = Timer(task["timeout_seconds"], self._timeout, args=(task_id, cancel_event))
        timeout.daemon = True
        timeout.start()
        try:
            self.task_manager.start_task(task_id)
            context = TaskContext(task_id, self.task_manager, cancel_event)
            context.checkpoint(5, "Preparing task.")
            result = runner(context, task["payload"])
            context.checkpoint(90, "Work finished; preparing verification.")
            self.task_manager.mark_verifying(task_id)
            verified, evidence = verifier(task["payload"], result)
            if cancel_event.is_set():
                current = self.task_manager.get_task(task_id)
                if current and current["status"] == "timed_out":
                    return
                raise TaskCancelled()
            if not verified:
                self.task_manager.fail_task(task_id, evidence, status="verification_failed")
                self._notify(task_id)
                return
            self.task_manager.complete_task(task_id, result=result, verification=evidence)
            self._notify(task_id)
        except TaskCancelled:
            current = self.task_manager.get_task(task_id)
            if current and current["status"] != "timed_out":
                self.task_manager.cancel_task(task_id)
                self._notify(task_id)
        except Exception as error:
            self.task_manager.fail_task(task_id, str(error))
            self._notify(task_id)
        finally:
            timeout.cancel()
            with self._lock:
                self._cancel_events.pop(task_id, None)

    def _timeout(self, task_id: str, event: Event) -> None:
        current = self.task_manager.get_task(task_id)
        if not current or current["status"] not in TaskManager.ACTIVE_STATUSES:
            return
        event.set()
        self.task_manager.fail_task(
            task_id,
            f"Task exceeded its {current['timeout_seconds']} second time limit.",
            status="timed_out",
        )
        self._notify(task_id)

    def cancel(self, task_id: str) -> dict | None:
        task = self.task_manager.request_cancellation(task_id)
        if not task:
            return None
        with self._lock:
            event = self._cancel_events.get(task_id)
        if event:
            event.set()
        else:
            self.task_manager.cancel_task(task_id)
        return self.task_manager.get_task(task_id)

    def retry(self, task_id: str) -> dict | None:
        task = self.task_manager.get_task(task_id)
        if not task or task["status"] in TaskManager.ACTIVE_STATUSES or not task["kind"]:
            return None
        return self.submit(
            task["kind"], task["title"], task["payload"],
            timeout_seconds=task["timeout_seconds"], attempt=task["attempt"] + 1,
            parent_task_id=task_id,
        )

    def _notify(self, task_id: str) -> None:
        task = self.task_manager.get_task(task_id)
        if task:
            message = self.notification_service.notify_task_status(
                status=task["status"], title=task["title"],
                result=task["result"], error=task["error"],
            )
            self.task_manager.update_task(task_id, notification=message)
