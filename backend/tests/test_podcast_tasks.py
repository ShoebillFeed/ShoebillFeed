from unittest.mock import MagicMock, patch

from app.tasks.podcast_tasks import _synthesize_turn_with_retry, _TURN_SYNTHESIS_MAX_ATTEMPTS


class TestSynthesizeTurnWithRetry:
    def test_returns_the_result_on_first_success(self):
        tts = MagicMock()
        tts.synthesize.return_value = "result"

        with patch("app.tasks.podcast_tasks.time.sleep") as sleep:
            result = _synthesize_turn_with_retry(tts, "hi", "voice", "/tmp/x.wav", 1.0, 0)

        assert result == "result"
        tts.synthesize.assert_called_once()
        sleep.assert_not_called()

    def test_retries_after_a_failure_and_returns_the_eventual_success(self):
        tts = MagicMock()
        tts.synthesize.side_effect = [RuntimeError("boom"), "result"]

        with patch("app.tasks.podcast_tasks.time.sleep") as sleep:
            result = _synthesize_turn_with_retry(tts, "hi", "voice", "/tmp/x.wav", 1.0, 0)

        assert result == "result"
        assert tts.synthesize.call_count == 2
        sleep.assert_called_once()

    def test_returns_none_after_exhausting_all_attempts(self):
        tts = MagicMock()
        tts.synthesize.side_effect = RuntimeError("boom")

        with patch("app.tasks.podcast_tasks.time.sleep") as sleep:
            result = _synthesize_turn_with_retry(tts, "hi", "voice", "/tmp/x.wav", 1.0, 0)

        assert result is None
        assert tts.synthesize.call_count == _TURN_SYNTHESIS_MAX_ATTEMPTS
        # No sleep after the final (exhausted) attempt.
        assert sleep.call_count == _TURN_SYNTHESIS_MAX_ATTEMPTS - 1

    def test_passes_through_synthesize_arguments(self):
        tts = MagicMock()
        tts.synthesize.return_value = "result"

        _synthesize_turn_with_retry(tts, "Hello", "voice-1", "/tmp/out.wav", 1.25, 3)

        tts.synthesize.assert_called_once_with("Hello", "voice-1", "/tmp/out.wav", speech_rate=1.25)
