import unittest

from services.native_intent import (
    NATIVE_INTENT_FUZZY_ALIASES,
    parse_native_intent_proposal,
    resolve_native_intent,
    should_request_native_intent_proposal,
)


class NativeIntentTests(unittest.TestCase):
    def test_system_usage_request_maps_to_existing_read_only_tool(self):
        for request in (
            "我的 CPU 和 RAM 现在用了多少？",
            "Show my current CPU and memory usage.",
        ):
            with self.subTest(request=request):
                intent = resolve_native_intent(request)
                self.assertIsNotNone(intent)
                self.assertEqual(intent.function_name, "get_system_info")
                self.assertEqual(intent.arguments, {})

    def test_open_app_request_keeps_only_the_app_name(self):
        for request in (
            "请打开 Chrome。",
            "打开Google Classroom",
            "打开 Google Classroom",
            "Please launch Chrome.",
        ):
            with self.subTest(request=request):
                intent = resolve_native_intent(request)
                self.assertIsNotNone(intent)
                self.assertEqual(intent.function_name, "open_app")
                expected_app = (
                    "google classroom"
                    if "classroom" in request.lower()
                    else "chrome"
                )
                self.assertEqual(intent.arguments, {"app": expected_app})

    def test_list_projects_request_maps_to_registered_project_tool(self):
        for request in ("我有哪些 project？", "What projects do I have?"):
            with self.subTest(request=request):
                intent = resolve_native_intent(request)
                self.assertIsNotNone(intent)
                self.assertEqual(intent.function_name, "list_projects")

    def test_registered_project_git_status_request_is_supported(self):
        for request in ("检查 FYP 的 Git status", "Check FYP Git status"):
            with self.subTest(request=request):
                intent = resolve_native_intent(request)
                self.assertIsNotNone(intent)
                self.assertEqual(intent.function_name, "git_status")
                self.assertEqual(intent.arguments, {"project_name": "fyp"})

    def test_explicit_power_requests_stay_in_the_native_confirmation_path(self):
        for request, expected_tool in (
            ("Please put my computer to sleep.", "sleep_computer"),
            ("sleep the computer", "sleep_computer"),
            ("帮我睡眠电脑。", "sleep_computer"),
            ("Please shut down my computer.", "shutdown_computer"),
            ("shutdown the pc", "shutdown_computer"),
            ("shutdown pc", "shutdown_computer"),
            ("Please shut down the computer.", "shutdown_computer"),
            ("关闭电脑。", "shutdown_computer"),
            ("请帮我重启电脑。", "restart_computer"),
        ):
            with self.subTest(request=request):
                intent = resolve_native_intent(request)
                self.assertIsNotNone(intent)
                self.assertEqual(intent.function_name, expected_tool)
                self.assertEqual(intent.arguments, {})

    def test_compound_or_general_requests_are_not_partially_executed(self):
        self.assertIsNone(resolve_native_intent("打开 Chrome，然后删除下载资料夹"))
        self.assertIsNone(resolve_native_intent("帮我写一个 Python 程序"))
        self.assertIsNone(resolve_native_intent("什么是 RAM？"))
        self.assertIsNone(resolve_native_intent("What is CPU usage?"))
        self.assertIsNone(resolve_native_intent("Please decide whether my computer should sleep."))
        self.assertIsNone(resolve_native_intent("Can you tell me how to shut down the pc?"))

    def test_native_proposal_gate_is_conservative(self):
        self.assertTrue(should_request_native_intent_proposal("turn off my computer"))
        self.assertTrue(should_request_native_intent_proposal("打开 Chrome"))
        self.assertTrue(should_request_native_intent_proposal("shutdowm my computer"))
        self.assertFalse(should_request_native_intent_proposal("Explain Python decorators"))
        self.assertFalse(should_request_native_intent_proposal("x" * 501))

    def test_native_proposal_aliases_cover_all_registered_tools(self):
        expected_tools = {
            "open_app", "get_system_info", "list_projects", "get_project_info", "open_project",
            "git_status", "list_files", "read_file", "search_files", "refresh_project_registry",
            "get_battery_status", "get_network_status", "list_running_processes", "adjust_volume",
            "toggle_mute", "media_control", "open_known_folder", "open_windows_setting",
            "lock_computer", "shutdown_computer", "restart_computer", "sleep_computer",
            "search_obsidian_notes", "open_obsidian_note", "create_obsidian_note",
            "append_obsidian_note", "update_obsidian_note",
        }
        self.assertEqual(set(NATIVE_INTENT_FUZZY_ALIASES), expected_tools)
        self.assertTrue(all(aliases for aliases in NATIVE_INTENT_FUZZY_ALIASES.values()))

    def test_native_proposal_parser_strips_valid_marker_and_checks_allowlist(self):
        text = (
            "[DISPLAY]\n我可以帮你关机。\n[VOICE_EN]\nI can help.\n"
            "[JARVIS_INTENT]{\"tool\":\"shutdown_computer\",\"arguments\":{},\"confidence\":0.94}[/JARVIS_INTENT]"
        )
        cleaned, proposal = parse_native_intent_proposal(text, {"shutdown_computer"})

        self.assertNotIn("JARVIS_INTENT", cleaned)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.function_name, "shutdown_computer")
        self.assertEqual(proposal.arguments, {})
        self.assertEqual(proposal.to_dict()["confidence"], 0.94)

    def test_native_proposal_parser_rejects_low_confidence_unknown_and_duplicate_markers(self):
        low_confidence = (
            "reply [JARVIS_INTENT]{\"tool\":\"shutdown_computer\",\"arguments\":{},\"confidence\":0.2}[/JARVIS_INTENT]"
        )
        unknown = (
            "reply [JARVIS_INTENT]{\"tool\":\"delete_file\",\"arguments\":{},\"confidence\":0.99}[/JARVIS_INTENT]"
        )
        duplicate = (
            "[JARVIS_INTENT]{\"tool\":\"shutdown_computer\",\"arguments\":{},\"confidence\":0.99}[/JARVIS_INTENT]"
            "[JARVIS_INTENT]{\"tool\":\"shutdown_computer\",\"arguments\":{},\"confidence\":0.99}[/JARVIS_INTENT]"
        )
        incomplete = "reply [JARVIS_INTENT]{\"tool\":\"shutdown_computer\"}"
        oversized_confidence = (
            "reply [JARVIS_INTENT]{\"tool\":\"shutdown_computer\",\"arguments\":{},"
            f"\"confidence\":{10 ** 1000}}}[/JARVIS_INTENT]"
        )

        for value in (low_confidence, unknown, duplicate, incomplete, oversized_confidence):
            with self.subTest(value=value):
                cleaned, proposal = parse_native_intent_proposal(value, {"shutdown_computer"})
                self.assertIsNone(proposal)
                self.assertNotIn("JARVIS_INTENT", cleaned)


if __name__ == "__main__":
    unittest.main()
