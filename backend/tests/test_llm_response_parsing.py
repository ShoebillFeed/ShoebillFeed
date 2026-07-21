from app.services.llm.base import parse_newsletter_response

KNOWN = ["Technology", "Science"]


def test_parses_well_formed_newsletter_json():
    text = """{
        "items": [
            {"headline": "AI breakthrough", "url": "https://example.com/a", "summary": "Something happened.",
             "keywords": ["ai", "research"], "categories": ["Technology"], "relevance_score": 7, "impact_score": 6}
        ]
    }"""
    result = parse_newsletter_response(text, KNOWN)
    assert len(result.items) == 1
    assert result.items[0].headline == "AI breakthrough"
    assert result.items[0].category_names == ["Technology"]


def test_recovers_from_malformed_json_via_repair():
    # Trailing comma after the last item -- invalid per json.loads, but the
    # kind of thing a larger multi-item extraction is prone to and that
    # json_repair.repair_json is specifically meant to fix. Before the fix,
    # parse_newsletter_response had no fallback here and this raised
    # JSONDecodeError straight out of the function.
    text = """{
        "items": [
            {"headline": "First article", "url": "https://example.com/a", "summary": "Summary one.",
             "keywords": ["a"], "categories": [], "relevance_score": 5, "impact_score": 5},
        ]
    }"""
    result = parse_newsletter_response(text, KNOWN)
    assert len(result.items) == 1
    assert result.items[0].headline == "First article"


def test_strips_markdown_code_fence():
    text = """```json
    {"items": [{"headline": "Fenced", "url": null, "summary": "s", "keywords": [], "categories": [], "relevance_score": 5, "impact_score": 5}]}
    ```"""
    result = parse_newsletter_response(text, KNOWN)
    assert len(result.items) == 1
    assert result.items[0].headline == "Fenced"


def test_skips_entries_without_a_headline():
    text = '{"items": [{"headline": "", "summary": "no headline"}, {"headline": "Valid", "summary": "s"}]}'
    result = parse_newsletter_response(text, KNOWN)
    assert len(result.items) == 1
    assert result.items[0].headline == "Valid"
