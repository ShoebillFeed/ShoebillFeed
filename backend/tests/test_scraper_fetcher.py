from app.services.fetchers.scraper import parse_scraper_items

# Mirrors news.ycombinator.com's real per-item markup (verified against a
# live fetch): the item container's *first* <a> is an upvote-arrow link
# (href="vote?..."), which appears in the DOM before the titleline's own
# <a> to the actual external article. Any item container with a vote arrow,
# avatar, or "read more" icon preceding the title anchor hits the same
# shape, so this isn't HN-specific -- it's the general case a naive
# "first <a> in the item" link_selector gets wrong.
HN_LIKE_HTML = """
<table>
  <tr class="athing" id="1">
    <td class="votelinks"><a href="vote?id=1&amp;how=up&amp;goto=news">upvote</a></td>
    <td class="title">
      <span class="titleline">
        <a href="https://example.com/real-article">A Real Article</a>
        <span class="sitebit comhead">(<a href="from?site=example.com">example.com</a>)</span>
      </span>
    </td>
  </tr>
  <tr class="athing" id="2">
    <td class="votelinks"><a href="vote?id=2&amp;how=up&amp;goto=news">upvote</a></td>
    <td class="title">
      <span class="titleline">
        <a href="https://another.example/story">Another Story</a>
      </span>
    </td>
  </tr>
</table>
"""


class TestParseScraperItemsLinkResolution:
    def test_prefers_the_title_elements_own_link_over_an_earlier_sibling_anchor(self):
        items = parse_scraper_items(
            HN_LIKE_HTML,
            base_url="https://news.ycombinator.com/",
            item_selector="tr.athing",
            title_selector=".titleline > a",
            link_selector="a",
        )
        assert len(items) == 2
        assert items[0].title == "A Real Article"
        assert items[0].url == "https://example.com/real-article"
        assert items[1].url == "https://another.example/story"
        # Never the internal vote-action URL a naive "first <a>" pick would produce.
        assert all("vote?" not in i.url for i in items)

    def test_uses_link_nested_inside_a_non_anchor_title_element(self):
        html = """
        <div class="item">
          <a class="icon" href="/icon-link">icon</a>
          <h2 class="title"><a href="https://example.com/nested">Nested Link Title</a></h2>
        </div>
        """
        items = parse_scraper_items(
            html, base_url="https://example.com/", item_selector=".item",
            title_selector="h2.title", link_selector="a",
        )
        assert len(items) == 1
        assert items[0].url == "https://example.com/nested"

    def test_falls_back_to_link_selector_when_title_has_no_link_of_its_own(self):
        html = """
        <div class="item">
          <h2 class="title">Plain Text Title</h2>
          <a class="read-more" href="https://example.com/full-story">Read more</a>
        </div>
        """
        items = parse_scraper_items(
            html, base_url="https://example.com/", item_selector=".item",
            title_selector="h2.title", link_selector="a.read-more",
        )
        assert len(items) == 1
        assert items[0].url == "https://example.com/full-story"

    def test_skips_an_item_with_no_link_anywhere(self):
        html = '<div class="item"><h2 class="title">No Link Here</h2></div>'
        items = parse_scraper_items(
            html, base_url="https://example.com/", item_selector=".item",
            title_selector="h2.title", link_selector="a",
        )
        assert items == []

    def test_resolves_relative_hrefs_against_base_url(self):
        html = '<div class="item"><h2 class="title"><a href="/story/1">Relative</a></h2></div>'
        items = parse_scraper_items(
            html, base_url="https://example.com/section/", item_selector=".item",
            title_selector="h2.title", link_selector="a",
        )
        assert items[0].url == "https://example.com/story/1"
