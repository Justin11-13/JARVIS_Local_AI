import io
from queue import Queue
import subprocess
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import MagicMock, patch

from services.agents.codex_app_server import (
    AppServerError,
    CodexAppServerAdapter,
    DEFAULT_LUNA_MODEL,
    READ_ONLY_PERMISSION_PROFILE,
    TRANSPORT_SESSION_OWNER,
    TRANSPORT_SESSION_VERSION,
    _JsonRpcSession,
)


class FakeSession:
    def __init__(self, responses=None, messages=None):
        self.responses = responses or {}
        self.messages = list(messages or [])
        self.calls = []
        self.notifications = []

    def request(self, method, params=None):
        self.calls.append((method, params or {}))
        response = self.responses.get(method)
        if isinstance(response, Exception):
            raise response
        return response or {}

    def notify(self, method, params=None):
        self.notifications.append((method, params or {}))

    def next_message(self, deadline):
        if not self.messages:
            raise AppServerError("timeout", "Timed out.")
        message = self.messages.pop(0)
        if isinstance(message, Exception):
            raise message
        return message


def _resident_session(messages=None):
    return FakeSession(
        {
            "initialize": {"ok": True},
            "account/read": {"account": {"type": "chatgpt", "id": "account-1"}},
            "model/list": {"data": [{"id": DEFAULT_LUNA_MODEL}]},
            "permissionProfile/list": {
                "data": [{"id": READ_ONLY_PERMISSION_PROFILE, "allowed": True}],
            },
            "thread/start": {"thread": {"id": "thread-1"}},
            "thread/resume": {"thread": {"id": "thread-1"}},
            "turn/start": {"turn": {"id": "turn-1"}},
            "turn/interrupt": {},
        },
        messages=messages,
    )


def _completed_messages(*replies):
    messages = []
    for reply in replies:
        messages.extend(
            [
                {
                    "method": "item/completed",
                    "params": {"item": {"type": "agentMessage", "text": reply}},
                },
                {
                    "method": "turn/completed",
                    "params": {"turn": {"id": "turn-1", "status": "completed"}},
                },
            ]
        )
    return messages


class CodexAppServerAdapterTests(unittest.TestCase):
    def test_connection_check_verifies_handshake_without_creating_a_turn(self):
        process = MagicMock()
        process.poll.return_value = None
        session = _resident_session()
        adapter = CodexAppServerAdapter(process_factory=MagicMock(return_value=process))

        with patch.object(adapter, "_start_process", return_value=process) as start_process, patch(
            "services.agents.codex_app_server._JsonRpcSession",
            return_value=session,
        ):
            first = adapter.check_ready()
            second = adapter.check_ready()

        self.assertEqual(first.status, "available")
        self.assertIn("no inference probe", first.detail)
        self.assertEqual(second.status, "available")
        self.assertEqual(start_process.call_count, 1)
        methods = [method for method, _params in session.calls]
        self.assertEqual(methods.count("initialize"), 1)
        self.assertEqual(methods.count("account/read"), 1)
        self.assertEqual(methods.count("model/list"), 1)
        self.assertEqual(methods.count("permissionProfile/list"), 1)
        self.assertNotIn("thread/start", methods)
        self.assertNotIn("thread/resume", methods)
        self.assertNotIn("turn/start", methods)
        adapter.close()

    def test_concurrent_connection_checks_share_one_handshake_owner(self):
        process = MagicMock()
        process.poll.return_value = None
        session = _resident_session()
        adapter = CodexAppServerAdapter(process_factory=MagicMock(return_value=process))

        with patch.object(adapter, "_start_process", return_value=process) as start_process, patch(
            "services.agents.codex_app_server._JsonRpcSession",
            return_value=session,
        ):
            with ThreadPoolExecutor(max_workers=2) as executor:
                states = list(executor.map(lambda _value: adapter.check_ready(), (1, 2)))

        self.assertEqual([state.status for state in states], ["available", "available"])
        self.assertEqual(start_process.call_count, 1)
        self.assertEqual(
            [method for method, _params in session.calls].count("initialize"),
            1,
        )
        adapter.close()

    def test_connection_check_revalidates_after_the_owned_child_dies(self):
        first_process = MagicMock()
        first_process.poll.return_value = None
        replacement_process = MagicMock()
        replacement_process.poll.return_value = None
        first_session = _resident_session()
        replacement_session = _resident_session()
        factory = MagicMock(side_effect=[first_process, replacement_process])
        adapter = CodexAppServerAdapter(process_factory=factory)

        with patch(
            "services.agents.codex_app_server._JsonRpcSession",
            side_effect=[first_session, replacement_session],
        ):
            self.assertEqual(adapter.check_ready().status, "available")
            first_process.poll.return_value = 1
            self.assertEqual(adapter.check_ready().status, "available")

        self.assertEqual(factory.call_count, 2)
        self.assertEqual(
            [method for method, _params in first_session.calls].count("initialize"),
            1,
        )
        self.assertEqual(
            [method for method, _params in replacement_session.calls].count("initialize"),
            1,
        )
        adapter.close()

    def test_connection_check_preserves_explicit_handshake_failure(self):
        process = MagicMock()
        process.poll.return_value = None
        session = FakeSession(
            {
                "initialize": {},
                "account/read": {"account": None},
            }
        )
        adapter = CodexAppServerAdapter(process_factory=MagicMock(return_value=process))

        with patch("services.agents.codex_app_server._JsonRpcSession", return_value=session):
            state = adapter.check_ready()

        self.assertEqual(state.status, "login_required")
        self.assertIn("Managed ChatGPT login", state.detail)
        methods = [method for method, _params in session.calls]
        self.assertEqual(methods, ["initialize", "account/read"])
        self.assertNotIn("thread/start", methods)
        adapter.close()

    def test_resident_lifecycle_reuses_child_and_verified_handshake(self):
        process = MagicMock()
        process.poll.return_value = None
        session = _resident_session(_completed_messages("First", "Second"))
        adapter = CodexAppServerAdapter(process_factory=MagicMock(return_value=process))

        with patch.object(adapter, "_start_process", return_value=process) as start_process, patch(
            "services.agents.codex_app_server._JsonRpcSession",
            return_value=session,
        ):
            first = adapter.generate_response("First")
            second = adapter.generate_response(
                "Second",
                transport_session=first["transport_session"],
            )

        self.assertTrue(first["success"])
        self.assertTrue(second["success"])
        self.assertFalse(first["timings"]["transport_reused"])
        self.assertTrue(second["timings"]["transport_reused"])
        self.assertEqual(first["timings"]["transport_generation"], 1)
        self.assertEqual(second["timings"]["transport_generation"], 1)
        self.assertEqual(start_process.call_count, 1)
        methods = [method for method, _params in session.calls]
        self.assertEqual(methods.count("initialize"), 1)
        self.assertEqual(methods.count("account/read"), 1)
        self.assertEqual(methods.count("model/list"), 1)
        self.assertEqual(methods.count("permissionProfile/list"), 1)
        self.assertEqual(methods.count("thread/start"), 1)
        self.assertEqual(methods.count("thread/resume"), 1)
        self.assertEqual(methods.count("turn/start"), 2)
        self.assertIsNone(process.terminate.call_args)

        adapter.close()
        process.terminate.assert_called_once()
        self.assertEqual(adapter.state.status, "not_checked")

    def test_concurrent_requests_share_one_initialization_owner(self):
        process = MagicMock()
        process.poll.return_value = None
        session = _resident_session(_completed_messages("First", "Second"))
        adapter = CodexAppServerAdapter(process_factory=MagicMock(return_value=process))

        with patch.object(adapter, "_start_process", return_value=process) as start_process, patch(
            "services.agents.codex_app_server._JsonRpcSession",
            return_value=session,
        ):
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(adapter.generate_response, ("First", "Second")))

        self.assertEqual([result["status"] for result in results], ["completed", "completed"])
        self.assertEqual(start_process.call_count, 1)
        self.assertEqual(
            [method for method, _params in session.calls].count("initialize"),
            1,
        )
        adapter.close()

    def test_child_failure_invalidates_resident_without_resending_turn(self):
        first_process = MagicMock()
        first_process.poll.return_value = None
        second_process = MagicMock()
        second_process.poll.return_value = None
        failed_session = _resident_session()
        failed_session.messages = [
            AppServerError("unavailable", "Codex App Server exited before completing the request.")
        ]
        healthy_session = _resident_session(_completed_messages("Recovered"))
        factory = MagicMock(side_effect=[first_process, second_process])
        adapter = CodexAppServerAdapter(process_factory=factory)

        with patch(
            "services.agents.codex_app_server._JsonRpcSession",
            side_effect=[failed_session, healthy_session],
        ):
            failed = adapter.generate_response("First")
            recovered = adapter.generate_response("Second")

        self.assertEqual(failed["status"], "unavailable")
        self.assertTrue(recovered["success"])
        self.assertEqual(
            [method for method, _params in failed_session.calls].count("turn/start"),
            1,
        )
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(
            [method for method, _params in healthy_session.calls].count("initialize"),
            1,
        )
        adapter.close()

    def test_protocol_capability_failure_invalidates_resident(self):
        first_process = MagicMock()
        first_process.poll.return_value = None
        second_process = MagicMock()
        second_process.poll.return_value = None
        blocked_session = _resident_session(
            [
                {
                    "method": "item/completed",
                    "params": {"item": {"type": "commandExecution"}},
                }
            ]
        )
        healthy_session = _resident_session(_completed_messages("After protocol failure"))
        factory = MagicMock(side_effect=[first_process, second_process])
        adapter = CodexAppServerAdapter(process_factory=factory)

        with patch(
            "services.agents.codex_app_server._JsonRpcSession",
            side_effect=[blocked_session, healthy_session],
        ):
            blocked = adapter.generate_response("First")
            recovered = adapter.generate_response("Second")

        self.assertEqual(blocked["status"], "blocked")
        self.assertTrue(recovered["success"])
        self.assertEqual(factory.call_count, 2)
        adapter.close()

    def test_timeout_unknown_result_is_not_resent(self):
        first_process = MagicMock()
        first_process.poll.return_value = None
        second_process = MagicMock()
        second_process.poll.return_value = None
        timed_out_session = _resident_session()
        healthy_session = _resident_session(_completed_messages("After timeout"))
        factory = MagicMock(side_effect=[first_process, second_process])
        adapter = CodexAppServerAdapter(process_factory=factory, timeout=1)

        with patch(
            "services.agents.codex_app_server._JsonRpcSession",
            side_effect=[timed_out_session, healthy_session],
        ):
            timed_out = adapter.generate_response("First")
            recovered = adapter.generate_response("Second")

        self.assertEqual(timed_out["status"], "timeout")
        self.assertTrue(recovered["success"])
        timed_out_methods = [method for method, _params in timed_out_session.calls]
        self.assertEqual(timed_out_methods.count("turn/start"), 1)
        self.assertEqual(timed_out_methods.count("turn/interrupt"), 1)
        self.assertEqual(factory.call_count, 2)
        adapter.close()

    def test_authentication_failure_invalidates_then_revalidates(self):
        process = MagicMock()
        process.poll.return_value = None
        replacement_process = MagicMock()
        replacement_process.poll.return_value = None
        first_session = _resident_session(_completed_messages("First"))
        # The warm request reaches the existing child but the account context
        # is rejected by the server; the next request must perform the full
        # verification again instead of reusing stale state.
        first_session.responses["thread/resume"] = AppServerError(
            "failed", "authentication expired"
        )
        replacement_session = _resident_session(_completed_messages("Revalidated"))
        factory = MagicMock(side_effect=[process, replacement_process])
        adapter = CodexAppServerAdapter(process_factory=factory)

        with patch(
            "services.agents.codex_app_server._JsonRpcSession",
            side_effect=[first_session, replacement_session],
        ):
            first = adapter.generate_response("First")
            first_mapping = first["transport_session"]
            failed = adapter.generate_response("Second", transport_session=first_mapping)
            recovered = adapter.generate_response("Third", transport_session=first_mapping)

        self.assertTrue(first["success"])
        self.assertEqual(failed["status"], "failed")
        self.assertTrue(recovered["success"])
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(
            [method for method, _params in replacement_session.calls].count("account/read"),
            1,
        )
        adapter.close()
    def test_json_rpc_request_advances_past_notifications_to_its_response(self):
        process = MagicMock()
        process.stdin = io.StringIO()
        process.stdout = io.StringIO()
        process.stderr = io.StringIO("diagnostic\n")
        process.poll.return_value = None
        session = _JsonRpcSession(process, timeout=1)
        session._messages = Queue()
        session._messages.put({"method": "remoteControl/status/changed", "params": {}})
        session._messages.put({"id": 1, "result": {"ok": True}})

        self.assertEqual(session.request("initialize"), {"ok": True})
        self.assertEqual(session._pending.popleft()["method"], "remoteControl/status/changed")
        self.assertIsNotNone(session._stderr_reader)
        session._stderr_reader.join(timeout=1)
        self.assertFalse(session._stderr_reader.is_alive())

    def test_luna_model_is_exact_target_not_a_default_substitute(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession({"model/list": {"data": [{"id": "gpt-5.6-sol"}]}})

        with self.assertRaisesRegex(AppServerError, DEFAULT_LUNA_MODEL):
            adapter._require_luna_model(session)

    def test_managed_chatgpt_login_is_required_not_api_key_auth(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession({"account/read": {"account": {"type": "apiKey"}}})

        with self.assertRaisesRegex(AppServerError, "Managed ChatGPT login"):
            adapter._require_managed_login(session)

    def test_managed_login_returns_a_non_reversible_context_hash(self):
        session = FakeSession({"account/read": {"account": {"type": "chatgpt", "id": "account-1"}}})

        context_hash = CodexAppServerAdapter._require_managed_login(session)

        self.assertEqual(len(context_hash), 64)
        self.assertNotIn("account-1", context_hash)

    def test_text_turn_uses_empty_workspace_and_restricted_read_only_policy(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession(
            {
                "thread/start": {"thread": {"id": "thread-1"}},
                "turn/start": {"turn": {"id": "turn-1"}},
            }
        )
        adapter._await_turn = MagicMock(return_value="Hello from Luna.")

        result = adapter._run_text_turn(
            session,
            "C:/temp/jarvis-chat",
            READ_ONLY_PERMISSION_PROFILE,
            "Hello",
            None,
            "context-hash",
        )

        self.assertEqual(result[0], "Hello from Luna.")
        self.assertEqual(result[1]["thread_id"], "thread-1")
        _, thread_params = session.calls[0]
        _, turn_params = session.calls[1]
        self.assertEqual(thread_params["cwd"], "C:/temp/jarvis-chat")
        self.assertEqual(turn_params["approvalPolicy"], "never")
        self.assertEqual(thread_params["permissions"], READ_ONLY_PERMISSION_PROFILE)
        self.assertEqual(turn_params["permissions"], READ_ONLY_PERMISSION_PROFILE)
        self.assertNotIn("dynamicTools", thread_params)
        self.assertNotIn("dynamicTools", turn_params)

    def test_optional_intent_catalog_changes_only_the_turn_instruction(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession({"thread/start": {"thread": {"id": "thread-1"}}})
        catalog = [
            {
                "name": "shutdown_computer",
                "description": "Shut down Windows.",
                "required_arguments": [],
                "optional_arguments": [],
            }
        ]

        adapter._start_transport_thread(
            session,
            "C:/temp/jarvis-chat",
            READ_ONLY_PERMISSION_PROFILE,
            intent_catalog=catalog,
        )

        instruction = session.calls[0][1]["developerInstructions"]
        self.assertIn("[JARVIS_INTENT]", instruction)
        self.assertIn("shutdown_computer", instruction)
        self.assertIn("never claim the local action was executed", instruction)
        self.assertIn("never copy or repeat it", instruction)
        self.assertIn("ordinary synonyms and minor spelling differences", instruction)
        self.assertIn("do not invent missing required arguments", instruction)

    def test_resume_reuses_owned_thread_without_starting_another(self):
        adapter = CodexAppServerAdapter()
        mapping = {
            "thread_id": "thread-1",
            "owner": TRANSPORT_SESSION_OWNER,
            "version": TRANSPORT_SESSION_VERSION,
            "auth_context_hash": "context-hash",
        }
        session = FakeSession(
            {
                "thread/resume": {"thread": {"id": "thread-1"}},
                "turn/start": {"turn": {"id": "turn-2"}},
            }
        )
        adapter._await_turn = MagicMock(return_value="Second reply.")

        result = adapter._run_text_turn(
            session,
            "C:/temp/new-empty-workspace",
            READ_ONLY_PERMISSION_PROFILE,
            "Second question",
            mapping,
            "context-hash",
        )

        self.assertEqual(result[0], "Second reply.")
        self.assertEqual(session.calls[0][0], "thread/resume")
        self.assertNotIn("thread/start", [method for method, _ in session.calls])
        self.assertEqual(session.calls[1][1]["input"], [{"type": "text", "text": "Second question"}])

    def test_changed_account_context_refuses_resume_without_starting_a_thread(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession()
        mapping = {
            "thread_id": "thread-1",
            "owner": TRANSPORT_SESSION_OWNER,
            "version": TRANSPORT_SESSION_VERSION,
            "auth_context_hash": "old-context",
        }

        with self.assertRaisesRegex(AppServerError, "different or unverifiable"):
            adapter._resume_transport_thread(
                session,
                "C:/temp/new-empty-workspace",
                READ_ONLY_PERMISSION_PROFILE,
                mapping,
                "new-context",
            )

        self.assertEqual(session.calls, [])

    def test_active_writer_conflict_is_explicit_and_never_starts_a_replacement_thread(self):
        adapter = CodexAppServerAdapter()
        mapping = {
            "thread_id": "thread-1",
            "owner": TRANSPORT_SESSION_OWNER,
            "version": TRANSPORT_SESSION_VERSION,
            "auth_context_hash": "context-hash",
        }
        session = FakeSession(
            {
                "thread/resume": AppServerError(
                    "failed", "thread-store conflict: thread already has an active writer"
                )
            }
        )

        with self.assertRaisesRegex(AppServerError, "another Codex client") as error:
            adapter._run_text_turn(
                session,
                "C:/temp/new-empty-workspace",
                READ_ONLY_PERMISSION_PROFILE,
                "Second question",
                mapping,
                "context-hash",
            )

        self.assertEqual(error.exception.status, "session_busy")
        self.assertEqual([method for method, _ in session.calls], ["thread/resume"])
        self.assertNotIn("thread/start", [method for method, _ in session.calls])

    def test_active_writer_conflict_after_resume_is_explicit_without_a_replacement_thread(self):
        adapter = CodexAppServerAdapter()
        mapping = {
            "thread_id": "thread-1",
            "owner": TRANSPORT_SESSION_OWNER,
            "version": TRANSPORT_SESSION_VERSION,
            "auth_context_hash": "context-hash",
        }
        session = FakeSession(
            {
                "thread/resume": {"thread": {"id": "thread-1"}},
                "turn/start": AppServerError(
                    "failed", "thread already has an active writer"
                ),
            }
        )

        with self.assertRaisesRegex(AppServerError, "another Codex client") as error:
            adapter._run_text_turn(
                session,
                "C:/temp/new-empty-workspace",
                READ_ONLY_PERMISSION_PROFILE,
                "Second question",
                mapping,
                "context-hash",
            )

        self.assertEqual(error.exception.status, "session_busy")
        self.assertEqual(
            [method for method, _ in session.calls], ["thread/resume", "turn/start"]
        )
        self.assertNotIn("thread/start", [method for method, _ in session.calls])

    def test_new_thread_does_not_claim_an_unsupported_cloud_project_binding(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession({"thread/start": {"thread": {"id": "thread-1"}}})

        adapter._start_transport_thread(session, "C:/temp/jarvis-chat", READ_ONLY_PERMISSION_PROFILE)

        self.assertNotIn("projectId", session.calls[0][1])

    def test_missing_read_only_profile_fails_closed(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession({"permissionProfile/list": {"data": [{"id": ":workspace", "allowed": True}]}})

        with self.assertRaisesRegex(AppServerError, "read-only"):
            adapter._require_read_only_profile(session, "C:/temp/jarvis-chat")

    def test_capability_item_is_blocked_before_any_text_is_returned(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession(
            messages=[
                {"method": "item/completed", "params": {"item": {"type": "commandExecution"}}},
            ]
        )

        with self.assertRaisesRegex(AppServerError, "disabled capability"):
            adapter._await_turn(session, "thread-1", "turn-1")

    def test_completed_agent_message_returns_text(self):
        adapter = CodexAppServerAdapter()
        session = FakeSession(
            messages=[
                {
                    "method": "item/completed",
                    "params": {"item": {"type": "agentMessage", "text": "[DISPLAY]\\nHello"}},
                },
                {
                    "method": "turn/completed",
                    "params": {"turn": {"id": "turn-1", "status": "completed"}},
                },
            ]
        )

        self.assertEqual(adapter._await_turn(session, "thread-1", "turn-1"), "[DISPLAY]\\nHello")

    def test_managed_transport_failure_is_returned_without_fallback(self):
        process = MagicMock()
        process.poll.return_value = None
        session = FakeSession(
            {
                "initialize": {},
                "account/read": {"account": None},
            }
        )
        adapter = CodexAppServerAdapter(process_factory=MagicMock(return_value=process))

        with patch("services.agents.codex_app_server._JsonRpcSession", return_value=session):
            result = adapter.generate_response("Hello")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "login_required")
        self.assertEqual(result["provider"], "luna")
        self.assertNotIn("Gemini", result["error"])

    def test_start_command_disables_configured_mcp_and_plugin_servers(self):
        process = MagicMock()
        factory = MagicMock(return_value=process)
        adapter = CodexAppServerAdapter(process_factory=factory)

        adapter._start_process()

        command = factory.call_args.args[0]
        self.assertIn("mcp_servers={}", command)
        self.assertIn("plugins={}", command)
        self.assertIn("allow_browser_and_computer_use=false", command)
        self.assertEqual(factory.call_args.kwargs["stderr"], subprocess.PIPE)

    def test_windows_start_hides_the_adapter_owned_cmd_window(self):
        process = MagicMock()
        factory = MagicMock(return_value=process)
        adapter = CodexAppServerAdapter(process_factory=factory)

        with patch("services.agents.codex_app_server.os.name", "nt"):
            adapter._start_process()

        self.assertEqual(factory.call_args.kwargs["creationflags"], subprocess.CREATE_NO_WINDOW)

    def test_windows_cleanup_ends_only_the_adapter_process_tree(self):
        process = MagicMock()
        process.pid = 12345
        process.poll.return_value = None

        with (
            patch("services.agents.codex_app_server.os.name", "nt"),
            patch("services.agents.codex_app_server.subprocess.run") as taskkill,
        ):
            CodexAppServerAdapter._stop_process(process)

        taskkill.assert_called_once_with(
            ["taskkill", "/PID", "12345", "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        process.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
