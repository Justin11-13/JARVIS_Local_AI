import io
import json
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from services.agents.luna_model import DEFAULT_LUNA_MODEL
from services.agents.openai_responses import OpenAIResponsesAdapter, RESPONSES_URL


class OpenAIResponsesAdapterTests(unittest.TestCase):
    def test_missing_key_is_explicit_and_does_not_open_a_network_request(self):
        adapter = OpenAIResponsesAdapter()

        with patch("services.agents.openai_responses.urlopen") as urlopen:
            result = adapter.generate_response("Hello", api_key=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "unconfigured")
        urlopen.assert_not_called()

    @patch("services.agents.openai_responses.urlopen")
    def test_direct_api_uses_exact_luna_without_tools_or_server_side_state(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"output": [{"content": [{"type": "output_text", "text": "Direct Luna reply"}]}]}
        ).encode()
        urlopen.return_value.__enter__.return_value = response
        adapter = OpenAIResponsesAdapter()

        result = adapter.generate_response("Explain this", api_key="sk-test")

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode())
        self.assertEqual(request.full_url, RESPONSES_URL)
        self.assertEqual(payload["model"], DEFAULT_LUNA_MODEL)
        self.assertFalse(payload["store"])
        self.assertNotIn("tools", payload)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["result"], "Direct Luna reply")

    @patch("services.agents.openai_responses.urlopen")
    def test_model_access_failure_is_not_reclassified_as_success_or_fallback(self, urlopen):
        urlopen.side_effect = HTTPError(RESPONSES_URL, 404, "missing", {}, io.BytesIO())
        result = OpenAIResponsesAdapter().generate_response("Hello", api_key="sk-test")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "model_unavailable")
        self.assertIn(DEFAULT_LUNA_MODEL, result["error"])

    @patch("services.agents.openai_responses.urlopen")
    def test_rate_and_network_failures_remain_distinct(self, urlopen):
        urlopen.side_effect = HTTPError(RESPONSES_URL, 429, "rate", {}, io.BytesIO())
        adapter = OpenAIResponsesAdapter()
        self.assertEqual(adapter.generate_response("Hello", api_key="sk-test")["status"], "rate_limited")

        urlopen.side_effect = URLError("offline")
        self.assertEqual(adapter.generate_response("Hello", api_key="sk-test")["status"], "network_error")


if __name__ == "__main__":
    unittest.main()
