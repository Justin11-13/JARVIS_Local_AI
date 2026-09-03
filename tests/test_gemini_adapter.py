import json
import unittest
from unittest.mock import MagicMock, patch

from services.agents.gemini import GeminiAdapter


class GeminiAdapterTests(unittest.TestCase):
    def test_system_instruction_identifies_jarvis_and_preserves_python_authority(self):
        instruction = GeminiAdapter.SYSTEM_INSTRUCTION

        self.assertIn("You are JARVIS", instruction)
        self.assertIn("personal Windows computer assistant", instruction)
        self.assertIn("local Python policy decides whether it runs", instruction)
        self.assertIn("High-risk actions require JARVIS confirmation", instruction)

    @patch("services.agents.gemini.urlopen")
    def test_memory_contents_are_sent_as_conversation_history_not_system_instruction(self, mocked_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "I remember."}]}}]}
        ).encode("utf-8")
        mocked_urlopen.return_value.__enter__.return_value = response
        adapter = GeminiAdapter(api_key="test-key", model="gemini-3.5-flash-lite", enabled=True)

        adapter.generate_response(
            "What did I ask?",
            memory_contents=[
                {"role": "user", "parts": [{"text": "Earlier question"}]},
                {"role": "model", "parts": [{"text": "Earlier answer"}]},
            ],
        )

        payload = json.loads(mocked_urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(payload["contents"][0]["role"], "user")
        self.assertEqual(payload["contents"][1]["role"], "model")
        self.assertIn("You are JARVIS", payload["system_instruction"]["parts"][0]["text"])

    def test_local_tool_declarations_cover_the_current_native_registry(self):
        names = {tool["name"] for tool in GeminiAdapter.LOCAL_TOOL_DECLARATIONS}

        self.assertTrue(
            {
                "open_app", "get_system_info", "list_projects", "get_project_info", "open_project",
                "git_status", "list_files", "read_file", "search_files", "refresh_project_registry",
                "get_battery_status", "get_network_status", "list_running_processes", "adjust_volume",
                "toggle_mute", "media_control", "open_known_folder", "open_windows_setting",
                "lock_computer", "shutdown_computer", "restart_computer", "sleep_computer",
            }.issubset(names)
        )

    def test_missing_configuration_is_reported_without_request(self):
        adapter = GeminiAdapter(api_key="", enabled=True)

        result = adapter.generate_response("Hello")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "unavailable")

    @patch("services.agents.gemini.urlopen")
    def test_approved_text_request_returns_gemini_text(self, mocked_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "你好！"}]}}]}
        ).encode("utf-8")
        mocked_urlopen.return_value.__enter__.return_value = response
        adapter = GeminiAdapter(api_key="test-key", model="gemini-3.5-flash-lite", enabled=True)

        result = adapter.generate_response("Hello")

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "你好！")
        self.assertEqual(result["model"], "gemini-3.5-flash-lite")
        self.assertNotIn("test-key", str(result))

    def test_invalid_model_name_is_not_configured(self):
        adapter = GeminiAdapter(api_key="test-key", model="bad/model", enabled=True)

        self.assertFalse(adapter.is_configured())

    @patch("services.agents.gemini.urlopen")
    def test_declared_tool_is_executed_once_then_result_is_explained(self, mocked_urlopen):
        first_response = MagicMock()
        first_response.read.return_value = json.dumps(
            {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {
                                    "functionCall": {
                                        "name": "list_projects",
                                        "args": {},
                                    }
                                }
                            ],
                        }
                    }
                ]
            }
        ).encode("utf-8")
        second_response = MagicMock()
        second_response.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "你有两个已注册项目。"}]}}]}
        ).encode("utf-8")
        mocked_urlopen.return_value.__enter__.side_effect = [first_response, second_response]
        execute_tool = MagicMock(
            return_value={"success": True, "status": "completed", "result": "Registered projects: A, B", "error": ""}
        )
        adapter = GeminiAdapter(api_key="test-key", model="gemini-3.5-flash-lite", enabled=True)

        result = adapter.generate_response("我有哪些项目？", execute_tool=execute_tool)

        execute_tool.assert_called_once_with("list_projects", {})
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "你有两个已注册项目。")
        self.assertEqual(result["tool_calls"], ["list_projects"])
        self.assertEqual(mocked_urlopen.call_count, 2)
        completion_payload = json.loads(mocked_urlopen.call_args_list[1].args[0].data.decode("utf-8"))
        function_response = completion_payload["contents"][-1]["parts"][0]["functionResponse"]
        self.assertNotIn("id", function_response)

    @patch("services.agents.gemini.urlopen")
    def test_undeclared_tool_is_returned_to_router_without_execution(self, mocked_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [
                                {
                                    "functionCall": {
                                        "name": "delete_file",
                                        "args": {"path": "important.txt"},
                                    }
                                }
                            ],
                        }
                    }
                ]
            }
        ).encode("utf-8")
        final_response = MagicMock()
        final_response.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "I cannot perform that action."}]}}]}
        ).encode("utf-8")
        mocked_urlopen.return_value.__enter__.side_effect = [response, final_response]
        execute_tool = MagicMock(
            return_value={"success": False, "status": "routing_blocked", "result": "", "error": "Blocked."}
        )
        adapter = GeminiAdapter(api_key="test-key", model="gemini-3.5-flash-lite", enabled=True)

        result = adapter.generate_response("delete a file", execute_tool=execute_tool)

        execute_tool.assert_called_once_with("delete_file", {"path": "important.txt"})
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "I cannot perform that action.")

    @patch("services.agents.gemini.urlopen")
    def test_failed_tool_can_retry_once_with_another_declared_tool(self, mocked_urlopen):
        first_response = MagicMock()
        first_response.read.return_value = json.dumps(
            {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [{"functionCall": {"name": "get_project_info", "args": {"project_name": "missing"}}}],
                        }
                    }
                ]
            }
        ).encode("utf-8")
        retry_response = MagicMock()
        retry_response.read.return_value = json.dumps(
            {
                "candidates": [
                    {
                        "content": {
                            "role": "model",
                            "parts": [{"functionCall": {"name": "list_projects", "args": {}}}],
                        }
                    }
                ]
            }
        ).encode("utf-8")
        final_response = MagicMock()
        final_response.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "The requested project is not registered; here are the registered projects."}]}}]}
        ).encode("utf-8")
        mocked_urlopen.return_value.__enter__.side_effect = [first_response, retry_response, final_response]
        execute_tool = MagicMock(
            side_effect=[
                {"success": False, "status": "failed", "result": "", "error": "Project is not registered."},
                {"success": True, "status": "completed", "result": "Registered projects: JARVIS", "error": ""},
            ]
        )
        adapter = GeminiAdapter(api_key="test-key", model="gemini-3.5-flash-lite", enabled=True)

        result = adapter.generate_response("Tell me about the missing project.", execute_tool=execute_tool)

        self.assertEqual(execute_tool.call_count, 2)
        self.assertEqual(result["tool_calls"], ["get_project_info", "list_projects"])
        self.assertTrue(result["success"])
        self.assertEqual(mocked_urlopen.call_count, 3)

    @patch("services.agents.gemini.urlopen")
    def test_successful_tools_can_form_a_bounded_sequence(self, mocked_urlopen):
        first_response = MagicMock()
        first_response.read.return_value = json.dumps(
            {"candidates": [{"content": {"role": "model", "parts": [{"functionCall": {"name": "list_projects", "args": {}}}]}}]}
        ).encode("utf-8")
        second_response = MagicMock()
        second_response.read.return_value = json.dumps(
            {"candidates": [{"content": {"role": "model", "parts": [{"functionCall": {"name": "list_files", "args": {"project_name": "JARVIS"}}}]}}]}
        ).encode("utf-8")
        final_response = MagicMock()
        final_response.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "The JARVIS project is registered and its root was listed."}]}}]}
        ).encode("utf-8")
        mocked_urlopen.return_value.__enter__.side_effect = [first_response, second_response, final_response]
        execute_tool = MagicMock(
            side_effect=[
                {"success": True, "status": "completed", "result": "Registered projects: JARVIS", "error": ""},
                {"success": True, "status": "completed", "result": "Files in project JARVIS", "error": ""},
            ]
        )
        adapter = GeminiAdapter(api_key="test-key", model="gemini-3.5-flash-lite", enabled=True)

        result = adapter.generate_response("Inspect JARVIS.", execute_tool=execute_tool)

        self.assertTrue(result["success"])
        self.assertEqual(result["tool_calls"], ["list_projects", "list_files"])
        self.assertEqual(execute_tool.call_count, 2)

    @patch("services.agents.gemini.urlopen")
    def test_pending_confirmation_is_returned_without_claiming_completion(self, mocked_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"candidates": [{"content": {"role": "model", "parts": [{"functionCall": {"name": "sleep_computer", "args": {}}}]}}]}
        ).encode("utf-8")
        mocked_urlopen.return_value.__enter__.return_value = response
        adapter = GeminiAdapter(api_key="test-key", model="gemini-3.5-flash-lite", enabled=True)

        result = adapter.generate_response(
            "Put the computer to sleep.",
            execute_tool=lambda *_: {"success": True, "status": "awaiting_confirmation", "message": "Please confirm."},
        )

        self.assertEqual(result["status"], "awaiting_confirmation")
        self.assertEqual(result["result"], "Please confirm.")
        self.assertEqual(result["tool_calls"], ["sleep_computer"])
        self.assertEqual(mocked_urlopen.call_count, 1)
