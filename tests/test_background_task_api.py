import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api import (
    BackgroundTaskRequest,
    cancel_background_task,
    create_background_task,
    get_background_task,
    retry_background_task,
)


class BackgroundTaskApiTests(unittest.TestCase):
    @patch("app.api.background_tasks.submit")
    def test_declared_task_can_be_created(self, submit):
        submit.return_value = {"id": "task_1", "status": "queued"}

        result = create_background_task(BackgroundTaskRequest(kind="project_scan"))

        self.assertEqual(result["status"], "queued")
        submit.assert_called_once()

    def test_arbitrary_task_type_is_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            create_background_task(BackgroundTaskRequest(kind="shell"))

        self.assertEqual(raised.exception.status_code, 400)

    @patch("app.api.task_manager.get_task", return_value=None)
    def test_unknown_task_returns_not_found(self, _get_task):
        with self.assertRaises(HTTPException) as raised:
            get_background_task("missing")

        self.assertEqual(raised.exception.status_code, 404)

    @patch("app.api.background_tasks.cancel", return_value=None)
    def test_inactive_task_cannot_be_cancelled(self, _cancel):
        with self.assertRaises(HTTPException) as raised:
            cancel_background_task("finished")

        self.assertEqual(raised.exception.status_code, 409)

    @patch("app.api.background_tasks.retry", return_value=None)
    def test_active_task_cannot_be_retried(self, _retry):
        with self.assertRaises(HTTPException) as raised:
            retry_background_task("running")

        self.assertEqual(raised.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
