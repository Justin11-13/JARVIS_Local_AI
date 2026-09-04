import json
import os
import unittest
from unittest.mock import MagicMock, patch

from services.fish_speech_service import FishSpeechError, FishSpeechService


class FishSpeechServiceTests(unittest.TestCase):
    def test_missing_key_does_not_attempt_a_network_request(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(FishSpeechError, "FISH_API_KEY"):
                FishSpeechService().synthesize("Hello")

    def test_authorized_request_uses_wav_and_never_puts_key_in_payload(self):
        response = MagicMock()
        response.read.return_value = b"RIFFtestWAVE"
        context = MagicMock()
        context.__enter__.return_value = response
        with patch.dict(
            os.environ,
            {"FISH_API_KEY": "secret", "FISH_REFERENCE_ID": "voice-id"},
            clear=True,
        ):
            with patch(
                "services.fish_speech_service.urlopen", return_value=context
            ) as open_url:
                audio = FishSpeechService().synthesize("Hello")

        request = open_url.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(audio, b"RIFFtestWAVE")
        self.assertEqual(payload["format"], "wav")
        self.assertEqual(payload["reference_id"], "voice-id")
        self.assertNotIn("secret", request.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
