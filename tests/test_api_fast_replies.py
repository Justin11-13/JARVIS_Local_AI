import unittest
from unittest.mock import patch

from app.api import (
    AiModeRequest,
    ChatRequest,
    _execute_gemini_safe_tool,
    _execute_native_tool,
    chat_with_jarvis,
    check_ai_connection,
    fast_reply,
    health,
    plain_display_text,
    set_ai_mode,
    shutdown_ai_transport,
    split_reply_for_speech,
    tasks,
)
from app.main import ai_connection, task_router
from app.api import jarvis_memory
from fastapi import HTTPException
from services.jarvis_memory import JarvisMemory


class ApiFastReplyTests(unittest.TestCase):
    def setUp(self):
        memory_patch = patch("app.api.jarvis_memory", JarvisMemory(max_turns=20))
        memory_patch.start()
        self.addCleanup(memory_patch.stop)
        ai_connection.select_mode("managed_subscription")
        task_router.pending_action_request = None

    def test_exact_greeting_uses_the_local_fast_path(self):
        self.assertEqual(fast_reply("  你好  "), "你好！我是 JARVIS。有什么可以帮你？")

    def test_question_stays_on_the_codex_migration_path(self):
        self.assertIsNone(fast_reply("你好，你可以做什么？"))

    def test_reply_protocol_keeps_display_and_english_narration_separate(self):
        display, speech = split_reply_for_speech(
            "[DISPLAY]\n您好。\n[VOICE_EN]\nHello."
        )

        self.assertEqual(display, "您好。")
        self.assertEqual(speech, "Hello.")

    def test_display_text_preserves_markdown_structure(self):
        display = plain_display_text(
            "***System management***\n* Check CPU\n```python\nvalue = ** 2\n```"
        )

        self.assertEqual(
            display,
            "***System management***\n* Check CPU\n```python\nvalue = ** 2\n```",
        )

    def test_missing_voice_block_keeps_markdown_display_but_sanitizes_speech(self):
        display, speech = split_reply_for_speech("**Ready**\n\n1. Check Core\n2. Send a message")

        self.assertEqual(display, "**Ready**\n\n1. Check Core\n2. Send a message")
        self.assertEqual(speech, "Ready\n\n1. Check Core\n2. Send a message")

    def test_fast_path_needs_no_reasoning_backend(self):
        result = chat_with_jarvis(ChatRequest(message="hello"))

        self.assertEqual(result["tool_results"], [])
        self.assertIn("JARVIS", result["reply"])

    def test_api_preserves_unknown_tool_failure(self):
        result = _execute_native_tool(
            "not_registered",
            {},
            "Run an unavailable tool.",
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIn("not available", result["error"])

    def test_api_preserves_native_exception_failure(self):
        def broken_tool():
            raise RuntimeError("native exploded")

        with patch.dict("app.api.AVAILABLE_TOOLS", {"get_system_info": broken_tool}, clear=True):
            result = _execute_native_tool(
                "get_system_info",
                {},
                "Check my system.",
            )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")
        self.assertIn("native exploded", result["error"])

    def test_api_preserves_awaiting_confirmation_without_completing_the_task(self):
        with patch.dict("app.api.AVAILABLE_TOOLS", {"sleep_computer": lambda: "slept"}, clear=True):
            result = _execute_native_tool(
                "sleep_computer",
                {},
                "Put the computer to sleep.",
            )

        self.assertIsNone(result["success"])
        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(result["task"]["status"], "waiting_approval")
        task_router.handle_pending_confirmation("no")

    def test_health_reports_the_active_routing_policy_without_calling_gemini(self):
        result = health()

        self.assertEqual(result["core"]["status"], "ready")
        self.assertIn("status", result["ai"])
        self.assertEqual(result["routing_mode"], "native_tools_first")

    @patch("app.api.ai_connection")
    def test_ai_check_returns_transport_verification_without_changing_health_semantics(self, connection):
        snapshot = connection.check_ready.return_value
        snapshot.mode = "managed_subscription"
        snapshot.to_dict.return_value = {
            "mode": "managed_subscription",
            "status": "available",
            "detail": "Managed subscription transport verified; no inference probe was run.",
        }

        result = check_ai_connection()

        connection.check_ready.assert_called_once_with()
        self.assertEqual(result["ai"]["status"], "available")
        self.assertEqual(result["verification"], "managed_transport")

    @patch("app.api.luna")
    def test_ai_response_exposes_only_safe_transport_timing_metadata(self, luna):
        luna.generate_response.return_value = {
            "success": True,
            "status": "completed",
            "result": "[DISPLAY]\nDone.\n[VOICE_EN]\nDone.",
            "error": "",
            "transport_session": {
                "thread_id": "thread-1",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "a" * 64,
            },
            "timings": {
                "request_id": "opaque-id",
                "transport_reused": True,
                "spawn_ms": None,
                "initialize_ms": None,
                "turn_completion_ms": 321.0,
                "first_token_ms": None,
                "total_ms": 325.0,
            },
        }

        result = chat_with_jarvis(ChatRequest(message="Tell me something"))

        self.assertGreaterEqual(result["timings"]["lock_wait_ms"], 0.0)
        self.assertTrue(result["timings"]["transport_reused"])
        self.assertIsNone(result["timings"]["first_token_ms"])
        self.assertNotIn("result", result["timings"])
        self.assertEqual(result["reply"], "Done.")

    @patch("app.api.luna")
    def test_core_shutdown_closes_only_the_managed_adapter(self, luna):
        shutdown_ai_transport()

        luna.close.assert_called_once_with()

    def test_tasks_exposes_current_in_process_records_without_mutation(self):
        with patch("app.api.task_manager.list_tasks", return_value=[{"id": "task_1", "status": "completed"}]) as listing:
            result = tasks()

        self.assertEqual(result, {"tasks": [{"id": "task_1", "status": "completed"}]})
        listing.assert_called_once_with()

    @patch("app.api.luna")
    def test_capability_question_is_an_immediate_bilingual_fast_reply(self, luna):
        result = chat_with_jarvis(ChatRequest(message="你能做什么？"))

        self.assertIn("CPU", result["reply"])
        self.assertIn("I can check CPU", result["speech"])
        self.assertEqual(result["tool_results"], [])
        luna.generate_response.assert_not_called()

    def test_chat_history_returns_completed_local_turns(self):
        from app.api import chat_history

        chat_with_jarvis(ChatRequest(message="hello"))

        history = chat_history()["turns"]
        self.assertEqual(history[0]["user"], "hello")
        self.assertIn("JARVIS", history[0]["assistant"])

    @patch("app.api.luna")
    def test_unavailable_luna_response_is_visible_without_fallback(self, luna):
        luna.generate_response.return_value = {
            "success": False,
            "status": "login_required",
            "result": "",
            "error": "Managed ChatGPT login is required.",
        }

        result = chat_with_jarvis(ChatRequest(message="检查我的项目"))

        self.assertIn("Managed ChatGPT login", result["reply"])
        self.assertEqual(result["tool_results"][0]["status"], "login_required")

    @patch("app.api._execute_native_tool")
    def test_known_safe_chat_request_uses_native_tool(self, execute_native_tool):
        execute_native_tool.return_value = {"result": "CPU usage: 10%. Memory usage: 20%."}

        result = chat_with_jarvis(ChatRequest(message="我的 CPU 和 RAM 现在用了多少？"))

        execute_native_tool.assert_called_once_with(
            "get_system_info",
            {},
            "我的 CPU 和 RAM 现在用了多少？",
        )
        self.assertEqual(result["reply"], "CPU usage: 10%. Memory usage: 20%.")
        self.assertEqual(len(result["tool_results"]), 1)

    @patch("app.api._execute_native_tool")
    @patch("app.api.luna")
    def test_explicit_power_chat_never_exposes_native_tools_to_luna(self, luna, execute_native_tool):
        execute_native_tool.return_value = {
            "success": None,
            "status": "awaiting_confirmation",
            "message": "Confirm before sleeping.",
        }

        result = chat_with_jarvis(ChatRequest(message="Please put my computer to sleep."))

        execute_native_tool.assert_called_once_with(
            "sleep_computer",
            {},
            "Please put my computer to sleep.",
        )
        luna.generate_response.assert_not_called()
        self.assertEqual(result["tool_results"][0]["status"], "awaiting_confirmation")
        self.assertEqual(result["reply"], "Confirm before sleeping.")
        self.assertEqual(result["speech"], "Confirm before sleeping.")

    @patch("app.api._execute_native_tool")
    @patch("app.api.luna")
    def test_shutdown_pc_alias_uses_native_confirmation_path(self, luna, execute_native_tool):
        execute_native_tool.return_value = {
            "success": None,
            "status": "awaiting_confirmation",
            "message": "Confirm before shutting down.",
        }

        result = chat_with_jarvis(ChatRequest(message="shutdown the pc"))

        execute_native_tool.assert_called_once_with(
            "shutdown_computer",
            {},
            "shutdown the pc",
        )
        luna.generate_response.assert_not_called()
        self.assertEqual(result["tool_results"][0]["status"], "awaiting_confirmation")
        self.assertEqual(result["reply"], "Confirm before shutting down.")
        self.assertEqual(result["speech"], "Confirm before shutting down.")

    @patch("app.api._execute_native_tool")
    @patch("app.api.luna")
    def test_luna_high_risk_proposal_uses_normal_permission_confirmation(self, luna, execute_native_tool):
        luna.generate_response.return_value = {
            "success": True,
            "status": "completed",
            "result": (
                "[DISPLAY]\n我可以帮你关闭电脑。\n[VOICE_EN]\nI can help.\n"
                "[JARVIS_INTENT]{\"tool\":\"shutdown_computer\",\"arguments\":{},\"confidence\":0.96}[/JARVIS_INTENT]"
            ),
            "error": "",
            "transport_session": {
                "thread_id": "thread-proposal",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "a" * 64,
            },
        }
        execute_native_tool.return_value = {
            "success": None,
            "status": "awaiting_confirmation",
            "message": "此操作需要确认。是否继续？请回复 yes 或 no。",
            "result": "",
            "error": "",
        }

        result = chat_with_jarvis(ChatRequest(message="turn off my computer"))

        execute_native_tool.assert_called_once_with(
            "shutdown_computer",
            {},
            "turn off my computer",
        )
        self.assertEqual(result["tool_results"][-1]["status"], "awaiting_confirmation")
        self.assertIn("确认", result["reply"])
        self.assertNotIn("JARVIS_INTENT", result["reply"])
        proposal_catalog = luna.generate_response.call_args.kwargs["intent_catalog"]
        self.assertIn("shutdown_computer", {entry["name"] for entry in proposal_catalog})
        task_router.pending_action_request = None

    @patch("app.api._execute_native_tool")
    @patch("app.api.luna")
    def test_luna_low_risk_proposal_executes_through_normal_permission_path(self, luna, execute_native_tool):
        luna.generate_response.return_value = {
            "success": True,
            "status": "completed",
            "result": (
                "[DISPLAY]\nI found the current hardware status.\n[VOICE_EN]\n"
                "I found the current hardware status.\n"
                "[JARVIS_INTENT]{\"tool\":\"get_system_info\",\"arguments\":{},\"confidence\":0.91}[/JARVIS_INTENT]"
            ),
            "error": "",
            "transport_session": {
                "thread_id": "thread-low-risk-proposal",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "a" * 64,
            },
        }
        execute_native_tool.return_value = {
            "success": True,
            "status": "completed",
            "result": "CPU usage: 3%. Memory usage: 40%.",
            "error": "",
        }

        result = chat_with_jarvis(ChatRequest(message="inspect my hardware status"))

        execute_native_tool.assert_called_once_with(
            "get_system_info",
            {},
            "inspect my hardware status",
        )
        self.assertEqual(result["tool_results"][-1]["status"], "completed")
        self.assertEqual(result["reply"], "CPU usage: 3%. Memory usage: 40%.")
        self.assertIsNone(task_router.pending_action_request)

    @patch("app.api._execute_native_tool")
    @patch("app.api.luna")
    def test_invalid_luna_native_proposal_is_visible_without_execution(self, luna, execute_native_tool):
        luna.generate_response.return_value = {
            "success": True,
            "status": "completed",
            "result": (
                "[DISPLAY]\n我无法确认这个操作。\n[VOICE_EN]\nI cannot confirm it.\n"
                "[JARVIS_INTENT]{\"tool\":\"delete_file\",\"arguments\":{},\"confidence\":0.99}[/JARVIS_INTENT]"
            ),
            "error": "",
            "transport_session": {
                "thread_id": "thread-invalid-proposal",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "a" * 64,
            },
        }

        result = chat_with_jarvis(ChatRequest(message="delete this file"))

        execute_native_tool.assert_not_called()
        self.assertIn("无法确认", result["reply"])
        self.assertNotIn("JARVIS_INTENT", result["reply"])

    @patch("app.api._execute_native_tool")
    @patch("app.api.luna")
    def test_luna_native_proposal_reuses_argument_boundary(self, luna, execute_native_tool):
        luna.generate_response.return_value = {
            "success": True,
            "status": "completed",
            "result": (
                "[DISPLAY]\n我找到一个设置。\n[VOICE_EN]\nI found a setting.\n"
                "[JARVIS_INTENT]{\"tool\":\"open_windows_setting\",\"arguments\":{\"setting\":\"registry\"},\"confidence\":0.98}[/JARVIS_INTENT]"
            ),
            "error": "",
            "transport_session": {
                "thread_id": "thread-invalid-argument",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "a" * 64,
            },
        }

        result = chat_with_jarvis(ChatRequest(message="configure a Windows setting"))

        execute_native_tool.assert_not_called()
        self.assertEqual(result["tool_results"][-1]["status"], "validation_failed")
        self.assertIn("unsupported", result["tool_results"][-1]["error"])

    @patch("app.api.luna")
    def test_unmatched_chat_starts_without_replaying_local_history_to_luna(self, luna):
        luna.generate_response.return_value = {
            "success": True,
            "status": "completed",
            "result": "[DISPLAY]\n这是 Luna 的回答。\n[VOICE_EN]\nThis is Luna's answer.",
            "error": "",
            "transport_session": {
                "thread_id": "thread-1",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "a" * 64,
            },
        }

        result = chat_with_jarvis(ChatRequest(message="帮我解释这个 Python error"))

        luna.generate_response.assert_called_once()
        args, kwargs = luna.generate_response.call_args
        self.assertEqual(args, ("帮我解释这个 Python error",))
        self.assertEqual(kwargs["transport_session"], None)
        self.assertEqual(result["reply"], "这是 Luna 的回答。")
        self.assertEqual(result["speech"], "This is Luna's answer.")
        self.assertEqual(result["tool_results"][0]["status"], "completed")
        task_router.pending_action_request = None

    @patch("app.api.luna")
    def test_external_waiting_result_remains_waiting_not_a_tool_failure(self, luna):
        luna.generate_response.return_value = {
            "success": None,
            "status": "awaiting_confirmation",
            "result": "此操作需要确认。是否继续？请回复 yes 或 no。",
            "error": "",
            "transport_session": {
                "thread_id": "thread-1",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "a" * 64,
            },
        }

        result = chat_with_jarvis(ChatRequest(message="Please explain a difficult topic"))

        self.assertEqual(result["reply"], "此操作需要确认。是否继续？请回复 yes 或 no。")
        self.assertIsNone(result["tool_results"][0]["success"])
        self.assertEqual(result["tool_results"][0]["status"], "awaiting_confirmation")
        self.assertEqual(result["tool_results"][0]["task"]["status"], "waiting_approval")
        task_router.pending_action_request = None

    @patch("app.api._get_rag_service")
    @patch("app.api.luna")
    def test_luna_chat_does_not_read_rag_or_expose_local_tools(self, luna, get_rag_service):
        luna.generate_response.return_value = {
            "success": True,
            "status": "completed",
            "result": "测试笔记记录了 Obsidian 与 JARVIS 的连接。",
            "error": "",
            "transport_session": {
                "thread_id": "thread-1",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "a" * 64,
            },
        }

        result = chat_with_jarvis(ChatRequest(message="我的 Obsidian 测试笔记写了什么？"))

        _, kwargs = luna.generate_response.call_args
        self.assertEqual(kwargs["transport_session"], None)
        get_rag_service.assert_not_called()
        self.assertIn("测试笔记", result["reply"])
        self.assertFalse(result["used_rag"])

    @patch("app.api.luna")
    def test_luna_reuses_one_owned_transport_session_for_one_conversation(self, luna):
        mapping = {
            "thread_id": "thread-1",
            "owner": "jarvis_foreground_luna",
            "version": 2,
            "auth_context_hash": "a" * 64,
        }
        luna.generate_response.side_effect = [
            {"success": True, "status": "completed", "result": "First", "error": "", "transport_session": mapping},
            {"success": True, "status": "completed", "result": "Second", "error": "", "transport_session": mapping},
        ]

        first = chat_with_jarvis(ChatRequest(message="First", conversation_id="jarvis-00000000-0000-0000-0000-000000000001"))
        second = chat_with_jarvis(ChatRequest(message="Second", conversation_id="jarvis-00000000-0000-0000-0000-000000000001"))

        self.assertEqual((first["reply"], second["reply"]), ("First", "Second"))
        self.assertIsNone(luna.generate_response.call_args_list[0].kwargs["transport_session"])
        self.assertEqual(luna.generate_response.call_args_list[1].kwargs["transport_session"]["thread_id"], "thread-1")

    @patch("app.api.luna")
    def test_luna_session_busy_is_shown_without_creating_a_replacement_mapping(self, luna):
        from app.api import jarvis_memory

        conversation_id = "jarvis-00000000-0000-0000-0000-000000000002"
        jarvis_memory.remember_transport_session(
            conversation_id,
            {
                "thread_id": "thread-occupied",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "b" * 64,
            },
        )
        luna.generate_response.return_value = {
            "success": False,
            "status": "session_busy",
            "result": "",
            "error": "This JARVIS conversation is active in another Codex client. Finish or close that client before retrying; JARVIS did not create a new chat.",
        }

        result = chat_with_jarvis(ChatRequest(message="Continue", conversation_id=conversation_id))

        self.assertIn("another Codex client", result["reply"])
        self.assertEqual(result["tool_results"][0]["status"], "session_busy")
        self.assertEqual(
            luna.generate_response.call_args.kwargs["transport_session"]["thread_id"],
            "thread-occupied",
        )
        self.assertEqual(
            jarvis_memory.transport_session(conversation_id)["thread_id"],
            "thread-occupied",
        )

    @patch("app.api.luna")
    @patch("app.api.ai_connection.generate_response")
    def test_direct_api_mode_does_not_receive_or_write_managed_thread_context(self, generate_response, luna):
        conversation_id = "jarvis-00000000-0000-0000-0000-000000000003"
        jarvis_memory.remember_transport_session(
            conversation_id,
            {
                "thread_id": "managed-thread",
                "owner": "jarvis_foreground_luna",
                "version": 2,
                "auth_context_hash": "c" * 64,
            },
        )
        set_ai_mode(AiModeRequest(mode="direct_api"))
        generate_response.return_value = {
            "success": False,
            "status": "model_unavailable",
            "result": "",
            "error": "Direct API cannot access Luna.",
            "tool_calls": [],
        }

        result = chat_with_jarvis(ChatRequest(message="Explain this", conversation_id=conversation_id))

        generate_response.assert_called_once_with("Explain this", transport_session=None)
        luna.generate_response.assert_not_called()
        self.assertEqual(result["tool_results"][0]["status"], "model_unavailable")
        self.assertEqual(jarvis_memory.transport_session(conversation_id)["thread_id"], "managed-thread")

    def test_mode_switch_rejects_a_pending_native_confirmation(self):
        task_router.pending_action_request = {"task_id": "pending"}

        with self.assertRaises(HTTPException) as error:
            set_ai_mode(AiModeRequest(mode="direct_api"))

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(ai_connection.mode, "managed_subscription")

    @patch("app.api._execute_native_tool")
    def test_gemini_safe_tool_allows_only_exact_registered_project_arguments(self, execute_native_tool):
        execute_native_tool.return_value = {"success": True, "status": "completed", "result": "Clean."}

        result = _execute_gemini_safe_tool(
            "git_status",
            {"project_name": "JARVIS"},
            "Is JARVIS clean?",
        )

        execute_native_tool.assert_called_once_with(
            "git_status",
            {"project_name": "JARVIS"},
            "Is JARVIS clean?",
        )
        self.assertTrue(result["success"])

    @patch("app.api._execute_native_tool")
    def test_gemini_local_tool_can_read_a_registered_project_file(self, execute_native_tool):
        execute_native_tool.return_value = {"success": True, "status": "completed", "result": "print('hello')"}

        result = _execute_gemini_safe_tool(
            "read_file",
            {"project_name": "JARVIS", "relative_path": "app/main.py"},
            "Explain app/main.py",
        )

        execute_native_tool.assert_called_once_with(
            "read_file",
            {"project_name": "JARVIS", "relative_path": "app/main.py"},
            "Explain app/main.py",
        )
        self.assertEqual(result["result"], "print('hello')")

    @patch("app.api._execute_native_tool")
    def test_gemini_local_tool_blocks_secret_files_and_redacts_common_secret_values(self, execute_native_tool):
        blocked = _execute_gemini_safe_tool(
            "read_file",
            {"project_name": "JARVIS", "relative_path": ".env"},
            "Read the environment file",
        )
        self.assertEqual(blocked["status"], "routing_blocked")
        execute_native_tool.assert_not_called()

        execute_native_tool.return_value = {
            "success": True,
            "status": "completed",
            "result": "API_KEY=do-not-send\npassword: also-do-not-send",
        }
        redacted = _execute_gemini_safe_tool(
            "read_file",
            {"project_name": "JARVIS", "relative_path": "example.txt"},
            "Read the example",
        )
        self.assertIn("[REDACTED]", redacted["result"])
        self.assertNotIn("do-not-send", redacted["result"])

    @patch("app.api._execute_native_tool")
    def test_gemini_safe_tool_blocks_file_and_write_proposals(self, execute_native_tool):
        result = _execute_gemini_safe_tool(
            "delete_file",
            {"path": "important.txt"},
            "Delete this file",
        )

        execute_native_tool.assert_not_called()
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "routing_blocked")

    @patch("app.api._execute_native_tool")
    def test_gemini_safe_tool_rejects_extra_arguments(self, execute_native_tool):
        result = _execute_gemini_safe_tool(
            "list_projects",
            {"include_paths": True},
            "Show my projects",
        )

        execute_native_tool.assert_not_called()
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "validation_failed")


if __name__ == "__main__":
    unittest.main()
