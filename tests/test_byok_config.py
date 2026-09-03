import unittest

from services.byok_config import BYOKConfig, DEFAULT_GEMINI_MODEL


class BYOKConfigTests(unittest.TestCase):
    def test_gemini_selection_uses_the_user_selected_model(self):
        config = BYOKConfig.from_mapping(
            {
                "JARVIS_BRAIN_PROVIDER": "Gemini",
                "GEMINI_MODEL": "gemini-3.5-flash-lite",
                "GEMINI_ENABLED": "true",
            }
        )

        self.assertEqual(config.provider, "gemini")
        self.assertEqual(config.model, "gemini-3.5-flash-lite")
        self.assertTrue(config.enabled)
        self.assertTrue(config.is_supported)
        self.assertIsNone(config.error)

    def test_missing_model_uses_a_safe_default(self):
        config = BYOKConfig.from_mapping({})

        self.assertEqual(config.provider, "gemini")
        self.assertEqual(config.model, DEFAULT_GEMINI_MODEL)
        self.assertFalse(config.enabled)

    def test_unimplemented_provider_is_not_silently_treated_as_gemini(self):
        config = BYOKConfig.from_mapping(
            {"JARVIS_BRAIN_PROVIDER": "openai", "GEMINI_ENABLED": "true"}
        )

        self.assertFalse(config.is_supported)
        self.assertFalse(config.enabled)
        self.assertIn("Unsupported BYOK provider 'openai'", config.error)
