"""Bounded text-only Luna transport through the local Codex App Server."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from queue import Empty, Queue
import subprocess
from tempfile import TemporaryDirectory
from threading import RLock, Thread
from time import monotonic, time
from typing import Any, Callable
from uuid import uuid4

from services.agents.luna_model import DEFAULT_LUNA_MODEL
from services.jarvis_system_prompt import JARVIS_SYSTEM_PROMPT
from services.native_intent import INTENT_PROPOSAL_END, INTENT_PROPOSAL_START


READ_ONLY_PERMISSION_PROFILE = ":read-only"
TRANSPORT_SESSION_OWNER = "jarvis_foreground_luna"
TRANSPORT_SESSION_VERSION = 2
_FORBIDDEN_ITEM_TYPES = frozenset(
    {
        "commandExecution",
        "fileChange",
        "dynamicToolCall",
        "mcpToolCall",
        "webSearch",
        "imageView",
        "enteredReviewMode",
        "exitedReviewMode",
        "collabToolCall",
    }
)
_FORBIDDEN_SERVER_REQUESTS = frozenset(
    {
        "item/permissions/requestApproval",
        "tool/requestUserInput",
        "mcpServer/elicitation/request",
    }
)


@dataclass(frozen=True)
class AppServerState:
    """Safe state for health/UI; it never contains account identity or tokens."""

    status: str
    detail: str = ""
    checked_at: float | None = None


class AppServerError(RuntimeError):
    """A typed, user-safe App Server failure."""

    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


class _JsonRpcSession:
    """Small JSONL client for one isolated, resident App Server session."""

    def __init__(self, process: Any, timeout: int):
        self.process = process
        self.timeout = timeout
        self._messages: Queue[dict[str, Any] | None] = Queue()
        self._pending: deque[dict[str, Any]] = deque()
        self._next_id = 1
        self._reader = Thread(target=self._read_stdout, daemon=True)
        self._reader.start()
        self._stderr_reader: Thread | None = None
        stderr = getattr(self.process, "stderr", None)
        if stderr is not None:
            self._stderr_reader = Thread(
                target=self._drain_stderr,
                args=(stderr,),
                daemon=True,
            )
            self._stderr_reader.start()

    def _read_stdout(self) -> None:
        stream = self.process.stdout
        if stream is None:
            self._messages.put(None)
            return
        for line in stream:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                self._messages.put(payload)
        self._messages.put(None)

    @staticmethod
    def _drain_stderr(stream: Any) -> None:
        """Keep the child stderr pipe flowing without retaining its contents."""
        try:
            for _line in stream:
                pass
        except (OSError, ValueError):
            # Process shutdown can close the pipe while the daemon reader is
            # between iterations. stderr is diagnostic only and is never
            # copied into a JARVIS result or timing record.
            return

    def send(self, method: str, params: dict[str, Any] | None = None) -> int:
        request_id = self._next_id
        self._next_id += 1
        self._write({"method": method, "id": request_id, "params": params or {}})
        return request_id

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._write({"method": method, "params": params or {}})

    def _write(self, payload: dict[str, Any]) -> None:
        stream = self.process.stdin
        if stream is None or self.process.poll() is not None:
            raise AppServerError("unavailable", "Codex App Server is not running.")
        stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
        stream.flush()

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self.send(method, params)
        deadline = monotonic() + self.timeout
        while True:
            # Do not consume `_pending` here: it contains notifications saved for
            # the turn reader. Re-reading one of them would starve the matching
            # JSON-RPC response forever.
            message = self._read_raw(deadline)
            if message.get("id") != request_id:
                self._pending.append(message)
                continue
            if error := message.get("error"):
                text = str(error.get("message", "Codex App Server rejected the request."))
                raise AppServerError("failed", text)
            result = message.get("result")
            if not isinstance(result, dict):
                raise AppServerError("failed", "Codex App Server returned an invalid response.")
            return result

    def next_message(self, deadline: float) -> dict[str, Any]:
        if self._pending:
            return self._pending.popleft()
        return self._read_raw(deadline)

    def _read_raw(self, deadline: float) -> dict[str, Any]:
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise AppServerError("timeout", "Codex App Server did not respond before the timeout.")
        try:
            message = self._messages.get(timeout=remaining)
        except Empty as error:
            raise AppServerError("timeout", "Codex App Server did not respond before the timeout.") from error
        if message is None:
            raise AppServerError("unavailable", "Codex App Server exited before completing the request.")
        return message


class CodexAppServerAdapter:
    """Use managed ChatGPT auth while refusing all model-side capabilities."""

    SYSTEM_INSTRUCTION = JARVIS_SYSTEM_PROMPT

    def __init__(
        self,
        *,
        model: str = DEFAULT_LUNA_MODEL,
        command: str = "codex.cmd",
        timeout: int = 60,
        process_factory: Callable[..., Any] = subprocess.Popen,
    ):
        self.model = model
        self.command = command
        self.timeout = timeout
        self.process_factory = process_factory
        self.state = AppServerState("not_checked")
        # One lifecycle owner protects the resident process, JSON-RPC session,
        # temporary CWD and verified handshake from concurrent initialization
        # or interleaved turns. It is intentionally adapter-local; it does not
        # touch the user's global Codex process/session.
        self._lifecycle_lock = RLock()
        self._process: Any | None = None
        self._session: _JsonRpcSession | None = None
        self._workspace_context: Any | None = None
        self._workspace: str | None = None
        self._permission_profile: str | None = None
        self._auth_context_hash: str | None = None
        self._transport_generation = 0
        self._ready = False

    @property
    def provider(self) -> str:
        return "luna"

    @property
    def active_model(self) -> str:
        return self.model

    def generate_response(
        self,
        user_message: str,
        *,
        transport_session: dict[str, Any] | None = None,
        intent_catalog: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Return one exact-Luna text response, optionally with a proposal contract."""
        request_id = uuid4().hex[:12]
        total_started = monotonic()
        timings = self._new_timings(request_id)
        lock_started = monotonic()

        with self._lifecycle_lock:
            timings["adapter_lock_wait_ms"] = self._elapsed_ms(lock_started)
            try:
                session, workspace, permission_profile, auth_context_hash = self._ensure_ready(timings)
                text, updated_transport_session = self._run_text_turn(
                    session,
                    workspace,
                    permission_profile,
                    user_message,
                    transport_session,
                    auth_context_hash,
                    intent_catalog=intent_catalog,
                    timings=timings,
                )
            except AppServerError as error:
                if self._requires_transport_invalidation(error):
                    self._clear_transport()
                timings["total_ms"] = self._elapsed_ms(total_started)
                self.state = AppServerState(error.status, str(error), time())
                self._emit_timing(timings, error.status)
                return self._error(error.status, str(error), timings)
            except OSError:
                self._clear_transport()
                message = "Codex App Server could not be started. Check the local Codex installation."
                timings["total_ms"] = self._elapsed_ms(total_started)
                self.state = AppServerState("unavailable", message, time())
                self._emit_timing(timings, "unavailable")
                return self._error("unavailable", message, timings)

            timings["total_ms"] = self._elapsed_ms(total_started)
            self.state = AppServerState("available", "Managed subscription transport responded.", time())
            self._emit_timing(timings, "completed")
            return {
                "success": True,
                "status": "completed",
                "result": text,
                "error": "",
                "provider": self.provider,
                "model": self.model,
                "tool_calls": [],
                "transport_session": updated_transport_session,
                "timings": timings,
            }

    def check_ready(self) -> AppServerState:
        """Verify the managed transport without creating or running a turn.

        This is intentionally narrower than ``generate_response``: it only
        establishes the adapter-owned App Server and repeats the existing
        account/model/read-only handshake.  No thread mapping, user message,
        or inference request is created by this method.
        """
        request_id = uuid4().hex[:12]
        total_started = monotonic()
        timings = self._new_timings(request_id, operation="connection_check")
        lock_started = monotonic()

        with self._lifecycle_lock:
            timings["adapter_lock_wait_ms"] = self._elapsed_ms(lock_started)
            try:
                self._ensure_ready(timings)
            except AppServerError as error:
                if self._requires_transport_invalidation(error):
                    self._clear_transport()
                timings["total_ms"] = self._elapsed_ms(total_started)
                self.state = AppServerState(error.status, str(error), time())
                self._emit_timing(timings, error.status)
                return self.state
            except OSError:
                self._clear_transport()
                message = "Codex App Server could not be started. Check the local Codex installation."
                timings["total_ms"] = self._elapsed_ms(total_started)
                self.state = AppServerState("unavailable", message, time())
                self._emit_timing(timings, "unavailable")
                return self.state

            timings["total_ms"] = self._elapsed_ms(total_started)
            self.state = AppServerState(
                "available",
                "Managed subscription transport verified; no inference probe was run.",
                time(),
            )
            self._emit_timing(timings, "verified")
            return self.state

    def close(self) -> None:
        """Stop only the adapter-owned child and temporary workspace."""
        with self._lifecycle_lock:
            self._clear_transport()
            self.state = AppServerState(
                "not_checked",
                "Managed subscription transport is not initialized.",
                time(),
            )

    def invalidate(self) -> None:
        """Explicitly discard verified state after auth/permission context changes."""
        with self._lifecycle_lock:
            self._clear_transport()
            self.state = AppServerState(
                "not_checked",
                "Managed subscription verification must be repeated.",
                time(),
            )

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return round((monotonic() - started) * 1000, 1)

    @staticmethod
    def _new_timings(request_id: str, *, operation: str = "turn") -> dict[str, Any]:
        return {
            "request_id": request_id,
            "operation": operation,
            "adapter_lock_wait_ms": None,
            "transport_reused": False,
            "transport_generation": None,
            "spawn_ms": None,
            "initialize_ms": None,
            "account_ms": None,
            "model_ms": None,
            "permission_profile_ms": None,
            "thread_ms": None,
            "turn_start_ms": None,
            "turn_completion_ms": None,
            "first_token_ms": None,
            "total_ms": None,
        }

    def _emit_timing(self, timings: dict[str, Any], status: str) -> None:
        """Emit bounded phase data without message, account, token or secret content."""
        payload = {
            "event": "luna_transport_timing",
            "status": status,
            **timings,
        }
        print(f"[JARVIS_TIMING] {json.dumps(payload, sort_keys=True)}", flush=True)

    def _transport_alive(self) -> bool:
        if not self._ready or self._process is None or self._session is None:
            return False
        try:
            return self._process.poll() is None
        except (AttributeError, OSError):
            return False

    def _ensure_ready(
        self,
        timings: dict[str, Any],
    ) -> tuple[_JsonRpcSession, str, str, str]:
        if self._transport_alive():
            timings["transport_reused"] = True
            timings["transport_generation"] = self._transport_generation
            return (
                self._session,
                self._workspace,
                self._permission_profile,
                self._auth_context_hash,
            )

        # A dead/partial resident is never reused. This is safe before this
        # request has submitted a turn; failures during a submitted turn are
        # handled by generate_response and are not retried.
        self._clear_transport()
        workspace_context = TemporaryDirectory(prefix="jarvis-codex-chat-")
        self._workspace_context = workspace_context
        self._workspace = workspace_context.name
        try:
            phase_started = monotonic()
            process = self._start_process()
            timings["spawn_ms"] = self._elapsed_ms(phase_started)
            self._process = process
            session = _JsonRpcSession(process, self.timeout)
            self._session = session

            phase_started = monotonic()
            self._initialize(session)
            timings["initialize_ms"] = self._elapsed_ms(phase_started)

            phase_started = monotonic()
            auth_context_hash = self._require_managed_login(session)
            timings["account_ms"] = self._elapsed_ms(phase_started)

            phase_started = monotonic()
            self._require_luna_model(session)
            timings["model_ms"] = self._elapsed_ms(phase_started)

            phase_started = monotonic()
            permission_profile = self._require_read_only_profile(session, self._workspace)
            timings["permission_profile_ms"] = self._elapsed_ms(phase_started)

            self._auth_context_hash = auth_context_hash
            self._permission_profile = permission_profile
            self._ready = True
            self._transport_generation += 1
            timings["transport_generation"] = self._transport_generation
            return session, self._workspace, permission_profile, auth_context_hash
        except BaseException:
            self._clear_transport()
            raise

    def _clear_transport(self) -> None:
        process = self._process
        workspace_context = self._workspace_context
        self._ready = False
        self._process = None
        self._session = None
        self._workspace_context = None
        self._workspace = None
        self._permission_profile = None
        self._auth_context_hash = None
        try:
            if process is not None:
                self._stop_process(process)
        finally:
            if workspace_context is not None:
                workspace_context.cleanup()

    @staticmethod
    def _requires_transport_invalidation(error: AppServerError) -> bool:
        if error.status in {
            "unavailable",
            "timeout",
            "blocked",
            "login_required",
            "auth_context_unavailable",
            "model_unavailable",
            "session_identity_changed",
            "session_unavailable",
        }:
            return True
        if error.status != "failed":
            return False
        detail = str(error).lower()
        return any(
            marker in detail
            for marker in (
                "auth",
                "account",
                "credential",
                "login",
                "permission",
                "profile",
                "protocol",
                "invalid response",
                "did not return",
                "exited",
                "not running",
            )
        )

    def _start_process(self) -> Any:
        # Explicit empty tables prevent user-configured MCP/plugin servers from
        # being available to this isolated text transport.  No API key is read.
        process_options: dict[str, Any] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "encoding": "utf-8",
            "bufsize": 1,
        }
        if os.name == "nt":
            # `codex.cmd` otherwise creates a visible command window for every
            # isolated model turn. The desktop already presents the request and
            # error state; no shell interaction is part of this transport.
            process_options["creationflags"] = subprocess.CREATE_NO_WINDOW
        return self.process_factory(
            [
                self.command,
                "app-server",
                "--stdio",
                "-c",
                "mcp_servers={}",
                "-c",
                "plugins={}",
                "-c",
                "allow_browser_and_computer_use=false",
                "-c",
                "allow_managed_hooks_only=true",
            ],
            **process_options,
        )

    @staticmethod
    def _stop_process(process: Any) -> None:
        if process.poll() is None:
            # `codex.cmd` launches a Node child on Windows.  Terminating only
            # the command-shell parent leaves that child holding the private
            # temporary CWD, which turns an otherwise successful reply into a
            # misleading cleanup failure.  This tree was created exclusively
            # by this adapter; no user process is targeted.
            process_id = getattr(process, "pid", None)
            if os.name == "nt" and isinstance(process_id, int):
                subprocess.run(
                    ["taskkill", "/PID", str(process_id), "/T", "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            try:
                process.terminate()
            except OSError:
                return
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    return
            except OSError:
                return

    @staticmethod
    def _initialize(session: _JsonRpcSession) -> None:
        session.request(
            "initialize",
            {
                "clientInfo": {"name": "jarvis", "title": "JARVIS", "version": "0.1.0"},
                # The installed App Server requires this only to select a
                # runtime read-only permission profile. Dynamic tools remain
                # absent and all other experimental methods are unused.
                "capabilities": {"experimentalApi": True},
            },
        )
        session.notify("initialized")

    @staticmethod
    def _require_managed_login(session: _JsonRpcSession) -> str:
        result = session.request("account/read", {"refreshToken": False})
        account = result.get("account")
        if not isinstance(account, dict) or account.get("type") != "chatgpt":
            raise AppServerError(
                "login_required",
                "Managed ChatGPT login is required in Codex before JARVIS can use Luna.",
            )
        account_identity = next(
            (
                account.get(key)
                for key in ("id", "accountId", "chatgptAccountId", "email")
                if isinstance(account.get(key), str) and account[key].strip()
            ),
            None,
        )
        if not isinstance(account_identity, str):
            raise AppServerError(
                "auth_context_unavailable",
                "Codex did not provide a stable managed-account context; JARVIS will not resume a stored session.",
            )
        return sha256(
            f"jarvis-codex-auth-context-v1:{account_identity}".encode("utf-8")
        ).hexdigest()

    def _require_luna_model(self, session: _JsonRpcSession) -> None:
        result = session.request("model/list", {"limit": 100, "includeHidden": False})
        models = result.get("data")
        if not isinstance(models, list):
            raise AppServerError("failed", "Codex App Server did not return a valid model list.")
        identifiers = {
            value
            for item in models
            if isinstance(item, dict)
            for value in (item.get("id"), item.get("model"))
            if isinstance(value, str)
        }
        if self.model not in identifiers:
            raise AppServerError(
                "model_unavailable",
                f"The signed-in Codex account does not list the required Luna model '{self.model}'.",
            )

    @staticmethod
    def _require_read_only_profile(session: _JsonRpcSession, workspace: str) -> str:
        result = session.request("permissionProfile/list", {"cwd": workspace, "limit": 100})
        profiles = result.get("data")
        if not isinstance(profiles, list):
            raise AppServerError("blocked", "Codex App Server did not return permission profiles for text isolation.")
        if any(
            isinstance(profile, dict)
            and profile.get("id") == READ_ONLY_PERMISSION_PROFILE
            and profile.get("allowed") is True
            for profile in profiles
        ):
            return READ_ONLY_PERMISSION_PROFILE
        raise AppServerError(
            "blocked",
            "Codex App Server cannot enforce the required read-only text-chat permission profile.",
        )

    def _run_text_turn(
        self,
        session: _JsonRpcSession,
        workspace: str,
        permission_profile: str,
        user_message: str,
        transport_session: dict[str, Any] | None,
        auth_context_hash: str,
        timings: dict[str, Any] | None = None,
        *,
        intent_catalog: list[dict[str, Any]] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        phase_started = monotonic()
        if transport_session:
            try:
                thread_id = self._resume_transport_thread(
                    session,
                    workspace,
                    permission_profile,
                    transport_session,
                    auth_context_hash,
                    intent_catalog=intent_catalog,
                )
            except AppServerError as error:
                self._raise_active_writer_conflict(error)
            updated_transport_session = transport_session
        else:
            thread_id = self._start_transport_thread(
                session,
                workspace,
                permission_profile,
                intent_catalog=intent_catalog,
            )
            updated_transport_session = {
                "thread_id": thread_id,
                "owner": TRANSPORT_SESSION_OWNER,
                "version": TRANSPORT_SESSION_VERSION,
                "auth_context_hash": auth_context_hash,
            }
        if timings is not None:
            timings["thread_ms"] = self._elapsed_ms(phase_started)
        phase_started = monotonic()
        try:
            turn = session.request(
                "turn/start",
                {
                    "threadId": thread_id,
                    "input": [{"type": "text", "text": user_message}],
                    "cwd": workspace,
                    "approvalPolicy": "never",
                    "permissions": permission_profile,
                    "model": self.model,
                    "summary": "concise",
                },
            ).get("turn")
        except AppServerError as error:
            self._raise_active_writer_conflict(error)
        finally:
            if timings is not None:
                timings["turn_start_ms"] = self._elapsed_ms(phase_started)
        if not isinstance(turn, dict) or not isinstance(turn.get("id"), str):
            raise AppServerError("failed", "Codex App Server did not start the Luna turn.")
        phase_started = monotonic()
        try:
            text = self._await_turn(session, thread_id, turn["id"])
        finally:
            if timings is not None:
                timings["turn_completion_ms"] = self._elapsed_ms(phase_started)
        return text, updated_transport_session

    def _start_transport_thread(
        self,
        session: _JsonRpcSession,
        workspace: str,
        permission_profile: str,
        *,
        intent_catalog: list[dict[str, Any]] | None = None,
    ) -> str:
        thread = session.request(
            "thread/start",
            {
                "model": self.model,
                "cwd": workspace,
                "approvalPolicy": "never",
                "permissions": permission_profile,
                "serviceName": "jarvis_text_chat",
                "ephemeral": False,
                "developerInstructions": self._text_only_instruction(intent_catalog),
            },
        ).get("thread")
        return self._validated_thread_id(thread, "create")

    def _resume_transport_thread(
        self,
        session: _JsonRpcSession,
        workspace: str,
        permission_profile: str,
        transport_session: dict[str, Any],
        auth_context_hash: str,
        *,
        intent_catalog: list[dict[str, Any]] | None = None,
    ) -> str:
        if (
            transport_session.get("owner") != TRANSPORT_SESSION_OWNER
            or transport_session.get("version") != TRANSPORT_SESSION_VERSION
            or transport_session.get("auth_context_hash") != auth_context_hash
            or not isinstance(transport_session.get("thread_id"), str)
        ):
            raise AppServerError(
                "session_identity_changed",
                "The stored JARVIS session belongs to a different or unverifiable managed account; it was not resumed.",
            )
        thread = session.request(
            "thread/resume",
            {
                "threadId": transport_session["thread_id"],
                "model": self.model,
                "cwd": workspace,
                "approvalPolicy": "never",
                "permissions": permission_profile,
                "developerInstructions": self._text_only_instruction(intent_catalog),
                "excludeTurns": True,
            },
        ).get("thread")
        return self._validated_thread_id(thread, "resume", expected_id=transport_session["thread_id"])

    @staticmethod
    def _raise_active_writer_conflict(error: AppServerError) -> None:
        """Expose a competing Codex writer without making a replacement thread."""
        conflict_markers = (
            "active writer",
            "thread-store conflict",
            "already has an active",
            "already active",
            "active turn",
        )
        if error.status == "failed" and any(
            marker in str(error).lower() for marker in conflict_markers
        ):
            raise AppServerError(
                "session_busy",
                "This JARVIS conversation is active in another Codex client. "
                "Finish or close that client before retrying; JARVIS did not create a new chat.",
            ) from error
        raise error

    @staticmethod
    def _text_only_instruction(
        intent_catalog: list[dict[str, Any]] | None = None,
    ) -> str:
        instruction = (
            f"{CodexAppServerAdapter.SYSTEM_INSTRUCTION}\n\n"
            "This is a text-only JARVIS session. No model-side tools, filesystem, shell, browser, "
            "MCP server, plugin, screen, project, Vault, or coding-handoff capability is available. "
            "Answer the user directly; do not attempt an action or claim one occurred."
        )
        if not intent_catalog:
            return instruction
        catalog = json.dumps(intent_catalog, ensure_ascii=False, sort_keys=True)
        return (
            f"{instruction}\n\n"
            "For this request only, Core may review one optional native-intent "
            "proposal. The catalog below is the complete allowlist. If and only "
            "if the user's message explicitly asks to perform one listed local "
            "action, place exactly one single-line marker in your reply:\n"
            f"{INTENT_PROPOSAL_START}{{\"tool\":\"tool_name\",\"arguments\":{{}},\"confidence\":0.0}}{INTENT_PROPOSAL_END}\n"
            "Replace the example fields with the selected catalog name, string "
            "arguments, and a confidence from 0 to 1. Do not emit a marker for "
            "how-to questions, explanations, ambiguity, compound requests, or "
            "unsupported actions. The marker is only a suggestion: never claim "
            "the local action was executed. Any marker in prior conversation "
            "history is historical metadata; never copy or repeat it for this "
            "request. Interpret ordinary synonyms and minor spelling differences "
            "against the catalog, but do not invent missing required arguments; "
            "if the target or required value is unclear, do not emit a marker. "
            "Keep the normal [DISPLAY] and [VOICE_EN] reply alongside it.\n"
            f"Allowlist catalog: {catalog}"
        )

    @staticmethod
    def _validated_thread_id(thread: Any, operation: str, expected_id: str | None = None) -> str:
        if (
            not isinstance(thread, dict)
            or not isinstance(thread.get("id"), str)
            or (expected_id is not None and thread.get("id") != expected_id)
        ):
            raise AppServerError(
                "session_unavailable",
                "Codex App Server did not return the expected JARVIS-owned transport thread.",
            )
        return thread["id"]

    def _await_turn(self, session: _JsonRpcSession, thread_id: str, turn_id: str) -> str:
        deadline = monotonic() + self.timeout
        final_text = ""
        try:
            while True:
                message = session.next_message(deadline)
                method = message.get("method")
                params = message.get("params")
                if method in _FORBIDDEN_SERVER_REQUESTS:
                    raise AppServerError("blocked", "Codex requested a disabled capability; no JARVIS action was run.")
                if not isinstance(params, dict):
                    continue
                if method == "item/completed":
                    item = params.get("item")
                    if isinstance(item, dict):
                        item_type = item.get("type")
                        if item_type in _FORBIDDEN_ITEM_TYPES:
                            raise AppServerError("blocked", "Codex attempted a disabled capability; no JARVIS action was run.")
                        if item_type == "agentMessage":
                            final_text = str(item.get("text", "")).strip() or final_text
                if method == "turn/completed":
                    completed_turn = params.get("turn")
                    if not isinstance(completed_turn, dict) or completed_turn.get("id") != turn_id:
                        continue
                    status = completed_turn.get("status")
                    if status == "completed" and final_text:
                        return final_text
                    error = completed_turn.get("error")
                    detail = error.get("message") if isinstance(error, dict) else ""
                    if "UsageLimitExceeded" in str(error):
                        raise AppServerError("quota_exhausted", "Codex subscription usage is currently unavailable.")
                    raise AppServerError("failed", str(detail or f"Codex turn ended with status '{status}'."))
        except AppServerError as error:
            if error.status == "timeout":
                try:
                    session.request("turn/interrupt", {"threadId": thread_id, "turnId": turn_id})
                except AppServerError:
                    pass
            raise


    def _error(
        self,
        status: str,
        message: str,
        timings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = {
            "success": False,
            "status": status,
            "result": "",
            "error": message,
            "provider": self.provider,
            "model": self.model,
            "tool_calls": [],
        }
        if timings is not None:
            result["timings"] = timings
        return result
