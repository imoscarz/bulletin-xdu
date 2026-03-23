import logging
import re
from datetime import date
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from bulletin.adapters.base import BaseAdapter
from bulletin.models import Notice
from bulletin.utils.http import fetch_page

logger = logging.getLogger(__name__)


class DedeCMSAdapter(BaseAdapter):
    """Adapter for DedeCMS sites (e.g., sme.xidian.edu.cn)."""

    async def fetch_notices(self, known_ids: set[str]) -> list[Notice]:
        new_notices: list[Notice] = []

        for page_num in range(1, self.config.pagination.max_pages + 1):
            url = self._get_page_url(page_num)
            logger.info("Fetching %s page %d: %s", self.config.id, page_num, url)

            html = await fetch_page(self.client, url)
            page_notices = self._parse_list_page(html)

            hit_known = False
            for notice in page_notices:
                if notice.id in known_ids:
                    hit_known = True
                    continue
                new_notices.append(notice)

            if hit_known:
                logger.info(
                    "Hit known notice on page %d, stopping pagination", page_num
                )
                break

            if not page_notices:
                break

        logger.info("Found %d new notices for %s", len(new_notices), self.config.id)
        return new_notices

    def _get_page_url(self, page_num: int) -> str:
        """Build URL with query-string pagination.

        Page 1: {base_url}/{list_path}
        Page 2+: {base_url}/{list_path}&PageNo={page_num}
        """
        base_url = self.config.base_url.rstrip("/")
        url = f"{base_url}/{self.config.list_path}"
        if page_num > 1:
            url += f"&PageNo={page_num}"
        return url

    def _parse_list_page(self, html: str) -> list[Notice]:
        soup = BeautifulSoup(html, "lxml")
        sel = self.config.selectors
        notices: list[Notice] = []

        container = soup.select_one(sel.list_container)
        if container is None:
            logger.warning(
                "Could not find list container with selector %r", sel.list_container
            )
            return []

        for item in container.select(sel.item):
            notice = self._parse_item(item)
            if notice is not None:
                notices.append(notice)

        return notices

    def _parse_item(self, item: Tag) -> Notice | None:
        link_tag = item.select_one("a")
        if link_tag is None or not link_tag.get("href"):
            return None

        href = str(link_tag["href"])
        if href.startswith(("javascript:", "#", "mailto:")):
            return None

        absolute_url = self._build_absolute_url(href)
        article_id = self._extract_article_id(href)
        notice_id = f"{self.config.id}:{article_id}"

        # Date from <span> or regex in item text
        pub_date = self._extract_date(item)
        title = link_tag.get_text(strip=True)
        if not title or pub_date is None:
            return None

        return Notice(
            id=notice_id,
            source_id=self.config.id,
            title=title,
            url=absolute_url,
            date=pub_date,
        )

    @staticmethod
    def _extract_date(item: Tag) -> date | None:
        text = item.get_text()
        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if match:
            try:
                return date.fromisoformat(match.group())
            except ValueError:
                pass
        return None

    def _build_absolute_url(self, relative_href: str) -> str:
        return urljoin(self.config.base_url + "/", relative_href)

    @staticmethod
    def _extract_article_id(href: str) -> str:
        filename = href.rstrip("/").rsplit("/", 1)[-1]
        for suffix in (".htm", ".html"):
            filename = filename.removesuffix(suffix)
        return filename
