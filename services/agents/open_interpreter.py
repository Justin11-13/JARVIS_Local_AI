import shutil
import subprocess
from pathlib import Path


class OpenInterpreterAdapter:
    def __init__(self, timeout: int = 600):
        self.timeout = timeout

    def is_available(self) -> bool:
        return shutil.which("interpreter") is not None

    def run_task(
        self,
        task: str,
        workspace: str,
        skip_git_repo_check: bool = False,
    ) -> dict:
        if not self.is_available():
            return {
                "success": False,
                "status": "unavailable",
                "result": "",
                "error": "Open Interpreter is not installed or not available in PATH.",
            }

        workspace_path = Path(workspace).expanduser().resolve()

        if not workspace_path.exists():
            return {
                "success": False,
                "status": "failed",
                "result": "",
                "error": f"Workspace does not exist: {workspace_path}",
            }

        if not workspace_path.is_dir():
            return {
                "success": False,
                "status": "failed",
                "result": "",
                "error": f"Workspace is not a directory: {workspace_path}",
            }

        command = [
            "interpreter",
            "exec",
        ]

        if skip_git_repo_check:
            command.append("--skip-git-repo-check")

        command.extend(
            [
                "-C",
                str(workspace_path),
                task,
            ]
        )

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8",
                errors="replace",
            )

            success = completed.returncode == 0

            return {
                "success": success,
                "status": "completed" if success else "failed",
                "result": completed.stdout.strip(),
                "log": completed.stderr.strip(),
                "error": "" if success else completed.stderr.strip(),
                "return_code": completed.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "status": "timeout",
                "result": "",
                "error": f"Open Interpreter task exceeded {self.timeout} seconds.",
            }

        except OSError as error:
            return {
                "success": False,
                "status": "failed",
                "result": "",
                "error": str(error),
            }