import unittest

from services.native_intent import resolve_native_intent


class NativeIntentTests(unittest.TestCase):
    def test_content_open_requests_are_not_application_launches(self):
        for request in ("open the python tutorial", "打开 Python 教程", "open my notes", "open https://python.org"):
            with self.subTest(request=request):
                self.assertIsNone(resolve_native_intent(request))

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
        for request in ("请打开 Chrome。", "Please launch Chrome."):
            with self.subTest(request=request):
                intent = resolve_native_intent(request)
                self.assertIsNotNone(intent)
                self.assertEqual(intent.function_name, "open_app")
                self.assertEqual(intent.arguments, {"app": "chrome"})

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

    def test_compound_or_general_requests_are_not_partially_executed(self):
        self.assertIsNone(resolve_native_intent("打开 Chrome，然后删除下载资料夹"))
        self.assertIsNone(resolve_native_intent("帮我写一个 Python 程序"))
        self.assertIsNone(resolve_native_intent("什么是 RAM？"))
        self.assertIsNone(resolve_native_intent("What is CPU usage?"))


if __name__ == "__main__":
    unittest.main()
