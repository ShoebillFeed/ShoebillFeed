from app.services.llm.base import (
    LLMProvider,
    PODCAST_WORDS_PER_MINUTE,
    parse_podcast_script_response,
    podcast_script_max_tokens,
)

HOST_IDS = ["h1", "h2"]


class _FakePromptCapturingProvider(LLMProvider):
    """Minimal concrete LLMProvider whose only real behavior is capturing
    the system/user prompt generate_podcast_script() builds, so prompt
    construction can be tested without a real API call."""

    provider_name = "fake"

    def __init__(self):
        self.model_name = "fake-model"
        self.last_system = None
        self.last_user = None

    def process_item(self, *args, **kwargs):
        raise NotImplementedError

    def process_cluster(self, *args, **kwargs):
        raise NotImplementedError

    def extract_newsletter_items(self, *args, **kwargs):
        raise NotImplementedError

    def health_check(self):
        return True

    def _complete(self, system, user, max_tokens=512):
        self.last_system = system
        self.last_user = user
        return '{"turns": []}'


def test_parses_well_formed_script_json():
    text = """{
        "turns": [
            {"host_id": "h1", "text": "Welcome back to the show!"},
            {"host_id": "h2", "text": "Great to be here."}
        ]
    }"""
    result = parse_podcast_script_response(text, HOST_IDS)
    assert [t.host_id for t in result.turns] == ["h1", "h2"]
    assert result.turns[0].text == "Welcome back to the show!"


def test_recovers_from_malformed_json_via_repair():
    # Trailing comma after the last turn -- invalid per json.loads, the kind
    # of thing json_repair.repair_json is meant to fix.
    text = """{
        "turns": [
            {"host_id": "h1", "text": "Hello there."},
        ]
    }"""
    result = parse_podcast_script_response(text, HOST_IDS)
    assert len(result.turns) == 1
    assert result.turns[0].text == "Hello there."


def test_strips_markdown_code_fence():
    text = """```json
    {"turns": [{"host_id": "h1", "text": "Fenced turn"}]}
    ```"""
    result = parse_podcast_script_response(text, HOST_IDS)
    assert len(result.turns) == 1
    assert result.turns[0].text == "Fenced turn"


def test_drops_turns_with_unrecognised_host_id():
    text = '{"turns": [{"host_id": "h1", "text": "Real host"}, {"host_id": "ghost", "text": "Made up host"}]}'
    result = parse_podcast_script_response(text, HOST_IDS)
    assert [t.host_id for t in result.turns] == ["h1"]


def test_drops_turns_missing_text_or_host_id():
    text = '{"turns": [{"host_id": "h1", "text": ""}, {"host_id": "", "text": "no host"}, {"host_id": "h2", "text": "valid"}]}'
    result = parse_podcast_script_response(text, HOST_IDS)
    assert [t.host_id for t in result.turns] == ["h2"]


def test_missing_turns_key_yields_empty_result():
    result = parse_podcast_script_response('{"unexpected": "shape"}', HOST_IDS)
    assert result.turns == []


def test_turns_not_a_list_yields_empty_result():
    result = parse_podcast_script_response('{"turns": "not a list"}', HOST_IDS)
    assert result.turns == []


def test_parses_valid_story_index():
    text = '{"turns": [{"host_id": "h1", "story_index": 1, "text": "About story two"}]}'
    result = parse_podcast_script_response(text, HOST_IDS, story_count=3)
    assert result.turns[0].story_index == 1


def test_null_story_index_for_banter():
    text = '{"turns": [{"host_id": "h1", "story_index": null, "text": "Welcome!"}]}'
    result = parse_podcast_script_response(text, HOST_IDS, story_count=3)
    assert result.turns[0].story_index is None


def test_out_of_range_story_index_becomes_none():
    text = '{"turns": [{"host_id": "h1", "story_index": 5, "text": "Hallucinated story"}]}'
    result = parse_podcast_script_response(text, HOST_IDS, story_count=3)
    assert result.turns[0].story_index is None


def test_missing_story_index_defaults_to_none():
    text = '{"turns": [{"host_id": "h1", "text": "No index given"}]}'
    result = parse_podcast_script_response(text, HOST_IDS, story_count=3)
    assert result.turns[0].story_index is None


class TestPodcastScriptMaxTokens:
    def test_scales_with_target_minutes(self):
        assert podcast_script_max_tokens(5) < podcast_script_max_tokens(15)

    def test_floor_for_very_short_targets(self):
        assert podcast_script_max_tokens(1) == 2048

    def test_capped_for_long_targets(self):
        assert podcast_script_max_tokens(15) == 8192

    def test_previous_fixed_budget_would_have_truncated_a_ten_minute_episode(self):
        # Regression guard for the bug this replaces: the old hardcoded 4096
        # was already below budget at 10 minutes, well before the 15-minute max.
        assert podcast_script_max_tokens(10) > 4096


class TestGeneratePodcastScriptPromptWordCount:
    """A real end-to-end test showed models follow an explicit numeric word
    target far more closely than an indirect "words/minute pace" framing --
    these lock down that the prompt actually states one, derived from
    target_minutes and story count rather than hardcoded."""

    HOSTS = [{"id": "h1", "name": "Alex", "character_prompt": "curious"}]

    def test_states_the_target_word_count(self):
        provider = _FakePromptCapturingProvider()
        provider.generate_podcast_script(
            hosts=self.HOSTS,
            stories=[{"title": "T", "content": "C", "source_name": "S"}],
            target_minutes=10,
            language="en",
        )
        assert f"approximately {10 * PODCAST_WORDS_PER_MINUTE} words" in provider.last_system

    def test_words_per_story_divides_the_target_by_story_count(self):
        provider = _FakePromptCapturingProvider()
        provider.generate_podcast_script(
            hosts=self.HOSTS,
            stories=[{"title": f"T{i}", "content": "C", "source_name": "S"} for i in range(4)],
            target_minutes=10,
            language="en",
        )
        target_words = 10 * PODCAST_WORDS_PER_MINUTE
        assert f"roughly {target_words // 4} words" in provider.last_system

    def test_does_not_divide_by_zero_with_no_stories(self):
        provider = _FakePromptCapturingProvider()
        # Should not raise even though callers are expected to guard against
        # an empty story list before reaching this point.
        provider.generate_podcast_script(hosts=self.HOSTS, stories=[], target_minutes=5, language="en")
        assert provider.last_system is not None

    def test_an_explicit_words_per_minute_overrides_the_piper_calibrated_default(self):
        # Kokoro/Chatterbox deployments pass Settings.podcast_words_per_minute
        # (see podcast_script.py::build_script) instead of relying on this
        # provider-level default -- the prompt must actually reflect it.
        provider = _FakePromptCapturingProvider()
        provider.generate_podcast_script(
            hosts=self.HOSTS,
            stories=[{"title": "T", "content": "C", "source_name": "S"}],
            target_minutes=10,
            language="en",
            words_per_minute=80,
        )
        assert "approximately 800 words" in provider.last_system
        assert f"approximately {10 * PODCAST_WORDS_PER_MINUTE} words" not in provider.last_system
