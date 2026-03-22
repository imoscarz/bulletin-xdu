from datetime import date
from pathlib import Path

import httpx
import pytest

from bulletin.adapters.xidian_cms import XidianCMSAdapter
from bulletin.config import PaginationConfig, SelectorConfig, SourceConfig


def _make_config(
    source_id: str = "jwc",
    base_url: str = "https://jwc.xidian.edu.cn",
    list_path: str = "tzgg.htm",
    date_format: str = "text",
    list_container: str = "div.list ul",
    date_selector: str = "span",
) -> SourceConfig:
    return SourceConfig(
        id=source_id,
        name=f"Test {source_id}",
        base_url=base_url,
        list_path=list_path,
        selectors=SelectorConfig(
            date_format=date_format,
            list_container=list_container,
            date=date_selector,
        ),
        pagination=PaginationConfig(max_pages=2),
    )


def _make_adapter(config: SourceConfig) -> XidianCMSAdapter:
    # We pass a dummy client since we test parsing, not HTTP
    client = httpx.AsyncClient()
    return XidianCMSAdapter(config, client)


class TestJwcParsing:
    def test_parse_list_page(self, jwc_html: str):
        config = _make_config()
        adapter = _make_adapter(config)

        notices = adapter._parse_list_page(jwc_html)

        assert len(notices) == 5
        assert notices[0].id == "jwc:21703"
        assert notices[0].source_id == "jwc"
        assert "四六级" in notices[0].title
        assert notices[0].date == date(2026, 3, 13)
        assert notices[0].is_new is True
        assert notices[0].url == "https://jwc.xidian.edu.cn/info/1012/21703.htm"

    def test_second_item(self, jwc_html: str):
        config = _make_config()
        adapter = _make_adapter(config)

        notices = adapter._parse_list_page(jwc_html)
        assert notices[1].id == "jwc:21680"
        assert notices[1].date == date(2026, 3, 10)
        assert notices[1].is_new is False

    def test_extract_total_pages(self, jwc_html: str):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(jwc_html, "lxml")
        total = XidianCMSAdapter._extract_total_pages(soup)
        assert total == 227


class TestMathParsing:
    @pytest.fixture
    def math_html(self, fixtures_dir: Path) -> str:
        return (fixtures_dir / "math_page1.html").read_text(encoding="utf-8")

    def test_parse_split_date(self, math_html: str):
        config = _make_config(
            source_id="math",
            base_url="https://math.xidian.edu.cn",
            list_path="xwgg/tzgg.htm",
            date_format="split",
            list_container="div.main ul",
            date_selector="div.date1 p",
        )
        adapter = _make_adapter(config)

        notices = adapter._parse_list_page(math_html)

        assert len(notices) == 3
        assert notices[0].id == "math:22152"
        assert notices[0].date == date(2026, 1, 19)
        assert "寒假值班" in notices[0].title

    def test_math_absolute_url(self, math_html: str):
        config = _make_config(
            source_id="math",
            base_url="https://math.xidian.edu.cn",
            list_path="xwgg/tzgg.htm",
            date_format="split",
            list_container="div.main ul",
            date_selector="div.date1 p",
        )
        adapter = _make_adapter(config)

        notices = adapter._parse_list_page(math_html)
        # ../info/1020/22152.htm relative to xwgg/tzgg.htm
        assert notices[0].url == "https://math.xidian.edu.cn/info/1020/22152.htm"


class TestUrlBuilding:
    def test_build_absolute_url_simple(self):
        config = _make_config()
        adapter = _make_adapter(config)
        url = adapter._build_absolute_url("info/1012/21703.htm")
        assert url == "https://jwc.xidian.edu.cn/info/1012/21703.htm"

    def test_build_absolute_url_relative(self):
        config = _make_config(
            base_url="https://math.xidian.edu.cn",
            list_path="xwgg/tzgg.htm",
        )
        adapter = _make_adapter(config)
        url = adapter._build_absolute_url("../info/1020/22152.htm")
        assert url == "https://math.xidian.edu.cn/info/1020/22152.htm"

    def test_extract_article_id(self):
        assert XidianCMSAdapter._extract_article_id("info/1012/21703.htm") == "21703"
        assert XidianCMSAdapter._extract_article_id("../info/1020/22152.htm") == "22152"


class TestPagination:
    def test_page1_url(self):
        config = _make_config()
        adapter = _make_adapter(config)
        url = adapter._get_page_url(1)
        assert url == "https://jwc.xidian.edu.cn/tzgg.htm"

    def test_page2_url(self):
        config = _make_config()
        adapter = _make_adapter(config)
        adapter._total_pages = 227
        url = adapter._get_page_url(2)
        assert url == "https://jwc.xidian.edu.cn/tzgg/226.htm"

    def test_page3_url(self):
        config = _make_config()
        adapter = _make_adapter(config)
        adapter._total_pages = 227
        url = adapter._get_page_url(3)
        assert url == "https://jwc.xidian.edu.cn/tzgg/225.htm"

    def test_page2_without_total_returns_none(self):
        config = _make_config()
        adapter = _make_adapter(config)
        assert adapter._get_page_url(2) is None
