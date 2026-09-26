import socket
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime


@contextmanager
def socket_timeout(seconds: int):
    """Temporarily set the global socket timeout for blocking I/O (feedparser, imaplib, praw)."""
    old = socket.getdefaulttimeout()
    socket.setdefaulttimeout(seconds)
    try:
        yield
    finally:
        socket.setdefaulttimeout(old)


@dataclass
class RawNewsItem:
    title: str
    url: str
    raw_content: str
    published_at: datetime | None
    image_url: str | None = None
    # Keywords the SOURCE itself supplied (arXiv subject categories, say),
    # as opposed to the ones the LLM infers later. Persisted separately on
    # NewsItem.source_keywords and merged into extracted_keywords at
    # processing time -- the LLM overwrites extracted_keywords wholesale, so
    # anything stored there up front would be clobbered.
    keywords: list[str] | None = None


class NewsFetcher(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def fetch(self) -> list[RawNewsItem]:
        ...


FETCHER_REGISTRY: dict[str, type[NewsFetcher]] = {}


def register_fetcher(source_type: str):
    def decorator(cls: type[NewsFetcher]):
        FETCHER_REGISTRY[source_type] = cls
        return cls
    return decorator


def get_fetcher(source_type: str, config: dict) -> NewsFetcher:
    cls = FETCHER_REGISTRY.get(source_type)
    if not cls:
        raise ValueError(f"Unknown source type: {source_type}")
    return cls(config)
