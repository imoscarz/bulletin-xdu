from abc import ABC, abstractmethod
from urllib.parse import parse_qs, urljoin, urlparse

import httpx

from bulletin.config import SourceConfig
from bulletin.models import Notice


class BaseAdapter(ABC):
    """Abstract base class for notification source adapters."""

    def __init__(self, config: SourceConfig, client: httpx.AsyncClient) -> None:
        self.config = config
        self.client = client

    @abstractmethod
    async def fetch_notices(self, known_ids: set[str]) -> list[Notice]:
        """Fetch new notices from the source.

        Args:
            known_ids: Set of notice IDs already in storage.
                       Implementations should stop paginating when they
                       encounter a known ID (incremental scraping).

        Returns:
            List of new Notice objects, ordered newest-first.
        """
        ...

    def _build_absolute_url(self, relative_href: str) -> str:
        """Convert a relative href to an absolute URL."""
        base = self.config.base_url
        if not base.endswith("/"):
            base += "/"
        list_url = urljoin(base, self.config.list_path)
        return urljoin(list_url, relative_href)

    @staticmethod
    def _extract_article_id(href: str) -> str:
        """Extract a stable article ID from path-style and query-style URLs."""
        parsed = urlparse(href)
        query = parse_qs(parsed.query)

        # Query-style CMS links, e.g. ...content.jsp?...&wbnewsid=24808
        for key in ("wbnewsid", "newsid", "id", "articleid"):
            values = query.get(key)
            if values and values[0]:
                return values[0]

        filename = parsed.path.rstrip("/").rsplit("/", 1)[-1]
        for suffix in (".htm", ".html", ".shtml", ".jsp", ".php"):
            filename = filename.removesuffix(suffix)
        if filename:
            return filename

        # Last-resort fallback to avoid empty IDs.
        return href
