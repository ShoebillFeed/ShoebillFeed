from app.services.fetchers.base import register_fetcher
from app.services.fetchers.rss import RSSFetcher


@register_fetcher("atom")
class AtomFetcher(RSSFetcher):
    """Atom feed fetcher — feedparser handles both RSS and Atom transparently."""
