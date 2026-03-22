import logging
import re
from datetime import date

from bs4 import BeautifulSoup, Tag

from bulletin.adapters.base import BaseAdapter
from bulletin.models import Notice
from bulletin.utils.http import fetch_page

logger = logging.getLogger(__name__)


class XidianCMSAdapter(BaseAdapter):
    """Adapter for Xidian University's Boda CMS sites."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._total_pages: int | None = None

    async def fetch_notices(self, known_ids: set[str]) -> list[Notice]:
        new_notices: list[Notice] = []

        for page_num in range(1, self.config.pagination.max_pages + 1):
            url = self._get_page_url(page_num)
            if url is None:
                break
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

    def _get_page_url(self, page_num: int) -> str | None:
        """Build the URL for a given page number.

        Page 1 = base list URL (e.g., tzgg.htm).
        Page 2+ uses reverse numbering: page 2 = tzgg/{total_pages-1}.htm
        """
        base_url = self.config.base_url.rstrip("/")
        if page_num == 1:
            return f"{base_url}/{self.config.list_path}"

        if self._total_pages is None:
            logger.warning("Could not determine total pages, stopping at page 1")
            return None

        list_base = self.config.list_path.removesuffix(".htm")
        reverse_page = self._total_pages - page_num + 1
        if reverse_page < 1:
            return None
        return f"{base_url}/{list_base}/{reverse_page}.htm"

    def _parse_list_page(self, html: str) -> list[Notice]:
        """Parse a list page and return notices found."""
        soup = BeautifulSoup(html, "lxml")
        sel = self.config.selectors

        if self._total_pages is None:
            self._total_pages = self._extract_total_pages(soup)

        notices: list[Notice] = []

        container = soup.select_one(sel.list_container)
        if container is None:
            logger.warning(
                "Could not find list container with selector %r", sel.list_container
            )
            return []

        items = container.select(sel.item)

        for item in items:
            notice = self._parse_item(item)
            if notice is not None:
                notices.append(notice)

        return notices

    def _parse_item(self, item: Tag) -> Notice | None:
        """Parse a single list item into a Notice."""
        sel = self.config.selectors

        # If item itself is the link tag (e.g. a.item structure)
        if item.name == sel.link:
            link_tag = item
        else:
            link_tag = item.select_one(sel.link)
        if link_tag is None or not link_tag.get("href"):
            return None

        href = str(link_tag["href"])

        # Skip non-article links (javascript, external, anchors)
        if href.startswith(("javascript:", "#", "mailto:")):
            return None

        absolute_url = self._build_absolute_url(href)
        article_id = self._extract_article_id(href)
        notice_id = f"{self.config.id}:{article_id}"

        # Extract date BEFORE title, since title extraction may modify the DOM
        pub_date = self._extract_date(item, link_tag)

        title = self._extract_title(item, link_tag)
        if not title:
            return None
        if pub_date is None:
            logger.warning("Could not extract date from item: %s", title[:50])
            return None

        is_new = item.select_one(sel.new_badge) is not None

        return Notice(
            id=notice_id,
            source_id=self.config.id,
            title=title,
            url=absolute_url,
            date=pub_date,
            is_new=is_new,
        )

    def _extract_title(self, item: Tag, link_tag: Tag) -> str:
        """Extract the notice title from a list item."""
        # Prefer the <a title="..."> attribute if available (most reliable)
        title_attr = link_tag.get("title")
        if title_attr and str(title_attr).strip():
            return str(title_attr).strip()

        sel = self.config.selectors

        if sel.date_format == "split":
            # For split-date sites, try dedicated title element first
            title_el = item.select_one("p.title")
            if title_el:
                return title_el.get_text(strip=True)
            # Fallback: date elements are [day, year-month], title is remaining text
            date_els = set(item.select(sel.date))
            parts = []
            for s in link_tag.stripped_strings:
                # Skip strings that belong to date elements
                if s.parent not in date_els:
                    parts.append(s)
            return " ".join(parts) if parts else link_tag.get_text(strip=True)
        else:
            # Standard: title is link text minus date text
            title = link_tag.get_text(strip=True)
            date_tag = item.select_one(sel.date)
            if date_tag:
                date_text = date_tag.get_text(strip=True)
                title = title.replace(date_text, "").strip()
            return title

    def _extract_date(self, item: Tag, link_tag: Tag) -> date | None:
        """Extract publication date from a list item."""
        sel = self.config.selectors

        if sel.date_format == "split":
            spans = item.select(sel.date)
            if len(spans) >= 3:
                # Order C (sie): parts=[DD, MM, YYYY]
                try:
                    day_s = spans[0].get_text(strip=True)
                    mon_s = spans[1].get_text(strip=True)
                    year_s = spans[2].get_text(strip=True)
                    return date(int(year_s), int(mon_s), int(day_s))
                except (ValueError, IndexError):
                    pass
            elif len(spans) >= 2:
                # Order A (math/phy): parts[0]=DD, parts[1]=YYYY-MM
                # Order B (soe):      parts[0]=MM-DD, parts[1]=YYYY
                a_text = spans[0].get_text(strip=True)
                b_text = spans[1].get_text(strip=True)
                try:
                    if "-" in a_text and len(b_text) == 4:
                        # Order B: MM-DD + YYYY
                        month_str, day_str = a_text.split("-")
                        return date(int(b_text), int(month_str), int(day_str))
                    else:
                        # Order A: DD + YYYY-MM
                        year_str, month_str = b_text.split("-")
                        return date(int(year_str), int(month_str), int(a_text))
                except (ValueError, IndexError):
                    pass

        # Try to find YYYY-MM-DD or YYYY.MM.DD anywhere in the item text
        text = item.get_text()
        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if match:
            try:
                return date.fromisoformat(match.group())
            except ValueError:
                pass
        match = re.search(r"\d{4}\.\d{2}\.\d{2}", text)
        if match:
            try:
                return date.fromisoformat(match.group().replace(".", "-"))
            except ValueError:
                pass

        return None

    @staticmethod
    def _extract_total_pages(soup: BeautifulSoup) -> int | None:
        """Extract total page count from pagination text like '共2946条 1/227'."""
        text = soup.get_text()
        match = re.search(r"\d+/(\d+)", text)
        if match:
            return int(match.group(1))

        # Fallback: find the last numbered page link in pagination widget
        pagination = soup.select_one(".pb_sys_common")
        if pagination:
            for link in reversed(pagination.select("a")):
                link_text = link.get_text(strip=True)
                if link_text.isdigit():
                    return int(link_text)

        return None
