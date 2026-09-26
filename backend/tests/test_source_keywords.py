"""Source-supplied keywords (arXiv subject categories) and how they merge.

Kept in NewsItem.source_keywords rather than written into
extracted_keywords at fetch time, because LLM processing overwrites that
column wholesale -- see migration 0056 and tasks/process_tasks.py.
"""

import pytest

from app.services.fetchers.arxiv_categories import category_label
from app.services.fetchers.base import RawNewsItem
from app.services.fetchers.scholar import ScholarFetcher
from app.services.normalization import merge_keywords


class TestCategoryLabel:
    def test_maps_a_known_code_to_a_readable_label(self):
        # "cs.LG" stored verbatim would normalize to the token "cs lg" --
        # opaque in the Trends tab and unable to overlap an LLM keyword.
        assert category_label("cs.LG") == "machine learning"
        assert category_label("quant-ph") == "quantum physics"

    def test_falls_back_to_the_archive_name_for_an_unlisted_subcategory(self):
        assert category_label("math.AT") == "mathematics"
        assert category_label("astro-ph.GA") == "astrophysics"

    def test_falls_back_to_the_code_itself_when_wholly_unknown(self):
        # A brand-new arXiv category should still group its papers together
        # rather than being silently dropped.
        assert category_label("zz.QQ") == "zz.qq"

    def test_ignores_empty_input(self):
        assert category_label("") is None
        assert category_label("   ") is None


class TestScholarFetcherCategories:
    def _entry(self, terms):
        return {"tags": [{"term": t} for t in terms]}

    def _fetcher(self):
        return ScholarFetcher({"query": "x"})

    def test_extracts_readable_labels_from_arxiv_tags(self):
        got = self._fetcher()._categories(self._entry(["cs.LG", "cs.CL"]))
        assert got == ["machine learning", "computation and language"]

    def test_deduplicates_repeated_labels(self):
        # cs.LG and stat.ML both mean "machine learning", and a paper's
        # primary category is usually repeated among its cross-lists.
        assert self._fetcher()._categories(self._entry(["cs.LG", "stat.ML"])) == ["machine learning"]

    def test_returns_none_when_a_paper_has_no_tags(self):
        assert self._fetcher()._categories({"tags": []}) is None
        assert self._fetcher()._categories({}) is None


class TestRawNewsItem:
    def test_keywords_default_to_none_so_other_fetchers_are_unaffected(self):
        raw = RawNewsItem(title="t", url="u", raw_content="c", published_at=None)
        assert raw.keywords is None


class TestMergeKeywords:
    def test_keeps_llm_keywords_first_then_appends_source_terms(self):
        assert merge_keywords(["rag", "eval"], ["machine learning"]) == ["rag", "eval", "machine learning"]

    def test_drops_case_insensitive_duplicates(self):
        assert merge_keywords(["Machine Learning"], ["machine learning"]) == ["Machine Learning"]

    def test_tolerates_either_side_being_absent(self):
        assert merge_keywords(["a"], None) == ["a"]
        assert merge_keywords(None, ["b"]) == ["b"]

    def test_returns_none_rather_than_an_empty_list(self):
        # Keeps the column NULL instead of storing an empty array.
        assert merge_keywords(None, None) is None
        assert merge_keywords([], []) is None

    def test_skips_blank_entries(self):
        assert merge_keywords(["a", "  ", ""], [None]) == ["a"]

    def test_is_idempotent_so_reprocessing_cannot_accumulate(self):
        once = merge_keywords(["rag"], ["machine learning"])
        assert merge_keywords(once, ["machine learning"]) == once
