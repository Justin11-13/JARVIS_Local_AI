import tempfile
import time
import unittest
from pathlib import Path

from services.background_task_service import BackgroundTaskService
from services.notification_service import NotificationService
from services.task_manager import TaskManager


class BackgroundTaskTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "tasks.json"
        self.manager = TaskManager(self.path)
        self.service = BackgroundTaskService(
            self.manager, NotificationService(), max_workers=1
        )

    def tearDown(self):
        self.temporary.cleanup()

    def wait_for_terminal_status(self, task_id: str, timeout: float = 2) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            task = self.manager.get_task(task_id)
            if task["status"] not in TaskManager.ACTIVE_STATUSES:
                return task
            time.sleep(0.01)
        self.fail("Background task did not finish in time.")

    def test_task_completes_only_after_verification(self):
        self.service.register(
            "example",
            lambda context, payload: (
                context.checkpoint(60, "Work complete.") or "done"
            ),
            lambda payload, result: (result == "done", "result equals done"),
        )

        created = self.service.submit("example", "Example")
        task = self.wait_for_terminal_status(created["id"])

        self.assertEqual(task["status"], "completed")
        self.assertEqual(task["progress"], 100)
        self.assertEqual(task["verification"], "result equals done")
        self.assertIn("任务已完成", task["notification"])

    def test_failed_verification_has_distinct_status(self):
        self.service.register(
            "bad-result",
            lambda context, payload: "unexpected",
            lambda payload, result: (False, "expected output was missing"),
        )

        created = self.service.submit("bad-result", "Bad result")
        task = self.wait_for_terminal_status(created["id"])

        self.assertEqual(task["status"], "verification_failed")
        self.assertIn("expected output", task["error"])
        self.assertIn("结果验证失败", task["notification"])

    def test_running_task_can_be_cancelled(self):
        def runner(context, payload):
            for step in range(100):
                time.sleep(0.005)
                context.checkpoint(step, "Working")
            return "done"

        self.service.register("slow", runner, lambda payload, result: (True, "ok"))
        created = self.service.submit("slow", "Slow task")
        time.sleep(0.03)
        self.service.cancel(created["id"])
        task = self.wait_for_terminal_status(created["id"])

        self.assertEqual(task["status"], "cancelled")

    def test_retry_creates_a_linked_new_attempt(self):
        self.service.register(
            "fails", lambda context, payload: (_ for _ in ()).throw(RuntimeError("boom")),
            lambda payload, result: (True, "ok"),
        )
        first = self.service.submit("fails", "Retry me")
        failed = self.wait_for_terminal_status(first["id"])
        retried = self.service.retry(failed["id"])

        self.assertIsNotNone(retried)
        self.assertEqual(retried["attempt"], 2)
        self.assertEqual(retried["parent_task_id"], first["id"])

    def test_tasks_are_loaded_from_disk(self):
        task = self.manager.create_task("Persist me", "test", kind="example")
        self.manager.complete_task(task.id, "saved", "verified")

        restored = TaskManager(self.path).get_task(task.id)

        self.assertEqual(restored["status"], "completed")
        self.assertEqual(restored["verification"], "verified")


if __name__ == "__main__":
    unittest.main()
