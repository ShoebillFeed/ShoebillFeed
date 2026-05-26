import email
import imaplib
import logging
import re
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup, Tag

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)

# Link text patterns that signal "this link opens the full article"
_READ_MORE_RE = re.compile(
    r"\b(weiterlesen|read\s+more|read\s+on|continue\s+reading|lire\s+la\s+suite|"
    r"en\s+savoir\s+plus|leer\s+m[aá]s|meer\s+lezen|l[eé]s\s+meer|"
    r"mehr\s+erfahren|zum\s+artikel|zur\s+news|zur\s+meldung|"
    r"full\s+article|see\s+more|view\s+article)\b",
    re.IGNORECASE,
)

# Text that indicates a non-content block (ads, nav, footer)
_NOISE_RE = re.compile(
    r"^(ANZEIGE|advertisement|sponsored|werbung|unsubscribe|abbestellen|"
    r"impressum|datenschutz|facebook|twitter|linkedin|instagram|youtube|"
    r"xing|bluesky|threads|newsletter\s+abonnieren)\b",
    re.IGNORECASE,
)


def _decode_header(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _article_container(a_tag: Tag, max_levels: int = 10) -> Tag | None:
    """Walk up from a 'read more' link to find the block that contains the article."""
    el = a_tag.parent
    for _ in range(max_levels):
        if el is None or el.name in ("html", "body", "[document]"):
            return None
        if el.name in ("td", "div", "article", "section", "li"):
            text = el.get_text(" ", strip=True)
            link_text = a_tag.get_text(" ", strip=True)
            # The container must hold more than just the link itself
            if len(text) > len(link_text) + 20:
                return el
        el = el.parent
    return None


def _extract_article_blocks(html_bytes: bytes) -> list[str]:
    """
    Parse newsletter HTML and return a compact list of article blocks in the form:
        TITLE: ...
        URL: ...
        TEASER: ...

    Finds blocks by locating 'read more' style links and pulling the nearby
    heading and teaser text from the same container. Generic heuristic —
    does not assume any specific newsletter template.
    """
    soup = BeautifulSoup(html_bytes.decode(errors="replace"), "lxml")
    for tag in soup(["script", "style", "head"]):
        tag.decompose()

    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    articles: list[str] = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href.startswith("http") or href in seen_urls:
            continue
        link_text = a_tag.get_text(" ", strip=True)
        if not _READ_MORE_RE.search(link_text):
            continue

        container = _article_container(a_tag)
        if not container:
            continue

        # Skip ad blocks
        container_text = container.get_text(" ", strip=True)
        if _NOISE_RE.search(container_text[:40]):
            continue

        # Prefer an explicit heading tag; fall back to first substantial text chunk
        title: str | None = None
        h = container.find(re.compile(r"^h[1-6]$"))
        if h:
            title = h.get_text(" ", strip=True)

        if not title:
            for elem in container.find_all(True):
                t = elem.get_text(" ", strip=True)
                if len(t) > 20 and not _READ_MORE_RE.search(t) and not _NOISE_RE.search(t):
                    title = t[:150]
                    break

        if not title or len(title) < 10 or title in seen_titles:
            continue

        # Teaser: first paragraph-like block that isn't the title or link text
        teaser = ""
        title_lower = title.lower()
        for elem in container.find_all(["p", "div", "td", "span"]):
            pt = elem.get_text(" ", strip=True)
            if (len(pt) > 40
                    and pt.lower() != title_lower
                    and title_lower not in pt.lower()
                    and not _READ_MORE_RE.search(pt)
                    and not _NOISE_RE.search(pt)):
                teaser = pt[:300]
                break

        seen_urls.add(href)
        seen_titles.add(title)

        block = f"TITLE: {title}\nURL: {href}"
        if teaser:
            block += f"\nTEASER: {teaser}"
        articles.append(block)

    return articles


def _extract_text_with_links(msg) -> str:
    """
    Return newsletter content in the most LLM-friendly format available.

    Preference order:
    1. Structured TITLE/URL/TEASER blocks (extracted via 'read more' link heuristic)
    2. Full HTML converted to text with inline [text](url) markers
    3. Plain-text fallback
    """
    html_payload: bytes | None = None
    plain_payload: bytes | None = None

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/html" and html_payload is None:
                html_payload = part.get_payload(decode=True)
            elif ct == "text/plain" and plain_payload is None:
                plain_payload = part.get_payload(decode=True)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            if msg.get_content_type() == "text/html":
                html_payload = payload
            else:
                plain_payload = payload

    if html_payload:
        # Try compact structured extraction first
        blocks = _extract_article_blocks(html_payload)
        if blocks:
            logger.debug("Newsletter: extracted %d article blocks via read-more heuristic", len(blocks))
            return "\n\n".join(blocks)

        # Fall back: convert HTML to text preserving links
        soup = BeautifulSoup(html_payload.decode(errors="replace"), "lxml")
        for tag in soup(["script", "style", "head"]):
            tag.decompose()
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            text = a.get_text(" ", strip=True)
            if href.startswith("http") and text:
                a.replace_with(f" [{text}]({href}) ")
            else:
                a.replace_with(a.get_text(" ", strip=True))
        lines = [ln.strip() for ln in soup.get_text(separator="\n").splitlines() if ln.strip()]
        return "\n".join(lines)[:15000]

    if plain_payload:
        return plain_payload.decode(errors="replace")[:15000]

    return ""


@register_fetcher("email")
class EmailIMAPFetcher(NewsFetcher):
    def fetch(self) -> list[RawNewsItem]:
        host = self.config.get("imap_host", "")
        port = int(self.config.get("imap_port", 993))
        username = self.config.get("username", "")
        password = self.config.get("password", "")
        folder = self.config.get("folder", "INBOX")
        subject_filter = self.config.get("subject_filter", "")

        if not all([host, username, password]):
            raise ValueError("Email source missing imap_host, username, or password in config")

        items: list[RawNewsItem] = []

        try:
            conn = imaplib.IMAP4_SSL(host, port)
            conn.login(username, password)
            conn.select(folder)

            search_criteria = "UNSEEN"
            if subject_filter:
                search_criteria = f'(UNSEEN SUBJECT "{subject_filter}")'

            _, data = conn.search(None, search_criteria)
            msg_ids = data[0].split()

            for msg_id in msg_ids[-50:]:
                try:
                    _, msg_data = conn.fetch(msg_id, "(RFC822)")
                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)

                    subject = _decode_header(msg.get("Subject", "(no subject)"))
                    date_str = msg.get("Date", "")
                    published_at = None
                    if date_str:
                        try:
                            published_at = parsedate_to_datetime(date_str).astimezone(timezone.utc)
                        except Exception:
                            pass

                    content = _extract_text_with_links(msg)
                    sender = msg.get("From", "")
                    url = f"email://{username}/{msg_id.decode()}"

                    items.append(RawNewsItem(
                        title=subject,
                        url=url,
                        raw_content=f"From: {sender}\n\n{content}",
                        published_at=published_at,
                    ))
                    conn.store(msg_id, "+FLAGS", "\\Seen")
                except Exception:
                    logger.exception("Error processing email message %s", msg_id)

            conn.logout()
        except Exception:
            logger.exception("Error connecting to IMAP server %s", host)

        return items
