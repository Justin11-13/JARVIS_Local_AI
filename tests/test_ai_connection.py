import unittest
from unittest.mock import MagicMock

from services.ai_connection import AiConnectionService, DIRECT_API, MANAGED_SUBSCRIPTION
from services.agents.openai_responses import DirectApiState


class AiConnectionServiceTests(unittest.TestCase):
    def setUp(self):
        self.subscription = MagicMock()
        self.subscription.active_model = "gpt-5.6-luna"
        self.subscription.state.status = "not_checked"
        self.subscription.state.detail = ""
        self.subscription.state.checked_at = None
        self.direct = MagicMock()
        self.direct.model = "gpt-5.6-luna"
        self.direct.state = DirectApiState("unconfigured")
        self.service = AiConnectionService(subscription=self.subscription, direct_api=self.direct)

    def test_manual_direct_mode_never_passes_subscription_thread_mapping(self):
        self.service.select_mode(DIRECT_API)
        self.subscription.invalidate.assert_called_once_with()
        self.service.set_direct_api_key("sk-test")
        self.direct.generate_response.return_value = {"success": False, "status": "network_error"}

        self.service.generate_response("Hello", transport_session={"thread_id": "must-not-cross"})

        self.subscription.generate_response.assert_not_called()
        self.direct.generate_response.assert_called_once_with("Hello", api_key="sk-test")

    def test_key_configured_is_not_reported_as_available(self):
        self.service.select_mode(DIRECT_API)
        snapshot = self.service.set_direct_api_key("sk-test")

        self.assertTrue(snapshot.key_configured)
        self.assertEqual(snapshot.status, "not_checked")

    def test_invalid_mode_is_rejected_without_silent_switch(self):
        with self.assertRaises(ValueError):
            self.service.select_mode("gemini")

        self.assertEqual(self.service.mode, MANAGED_SUBSCRIPTION)

    def test_returning_to_managed_mode_revalidates_the_subscription_transport(self):
        self.service.select_mode(DIRECT_API)
        self.service.select_mode(MANAGED_SUBSCRIPTION)

        self.assertEqual(self.subscription.invalidate.call_count, 2)

    def test_managed_check_delegates_without_submitting_inference(self):
        snapshot = self.service.check_ready()

        self.subscription.check_ready.assert_called_once_with()
        self.direct.generate_response.assert_not_called()
        self.assertEqual(snapshot.mode, MANAGED_SUBSCRIPTION)

    def test_direct_check_does_not_make_an_automatic_paid_request(self):
        self.service.select_mode(DIRECT_API)
        self.service.set_direct_api_key("sk-test")

        snapshot = self.service.check_ready()

        self.subscription.check_ready.assert_not_called()
        self.direct.generate_response.assert_not_called()
        self.assertEqual(snapshot.status, "not_checked")


if __name__ == "__main__":
    unittest.main()
