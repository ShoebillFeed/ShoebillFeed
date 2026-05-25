import email
import imaplib
import logging
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup

from app.services.fetchers.base import NewsFetcher, RawNewsItem, register_fetcher

logger = logging.getLogger(__name__)


def _decode_header(value: str) -> str:
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _extract_text(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    return BeautifulSoup(payload.decode(errors="replace"), "lxml").get_text(separator=" ", strip=True)[:8000]
            if ct == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="replace")[:8000]
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            ct = msg.get_content_type()
            text = payload.decode(errors="replace")
            if ct == "text/html":
                return BeautifulSoup(text, "lxml").get_text(separator=" ", strip=True)[:8000]
            return text[:8000]
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

                    content = _extract_text(msg)
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
