from app.services.llm.base import parse_podcast_script_response

HOST_IDS = ["h1", "h2"]


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
