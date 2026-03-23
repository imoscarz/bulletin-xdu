import json
from datetime import date
from pathlib import Path

from bulletin.config import SourceConfig
from bulletin.models import Notice
from bulletin.store import Store


def _make_notices() -> list[Notice]:
    return [
        Notice(
            id="test:001",
            source_id="test",
            title="第一条通知",
            url="https://example.com/info/1/001.htm",
            date=date(2026, 3, 20),
        ),
        Notice(
            id="test:002",
            source_id="test",
            title="第二条通知",
            url="https://example.com/info/1/002.htm",
            date=date(2026, 3, 19),
        ),
    ]


def _make_source_config() -> SourceConfig:
    return SourceConfig(
        id="test",
        name="Test Source",
        base_url="https://example.com",
        list_path="news.htm",
    )


def test_save_and_load_round_trip(tmp_path: Path):
    store = Store(tmp_path / "output")
    config = _make_source_config()
    notices = _make_notices()

    store.save_notices(config, notices)
    loaded = store.load_notices("test")

    assert len(loaded) == 2
    assert loaded[0].id == "test:001"
    assert loaded[0].title == "第一条通知"
    assert loaded[1].date == date(2026, 3, 19)


def test_load_known_ids(tmp_path: Path):
    store = Store(tmp_path / "output")
    config = _make_source_config()
    store.save_notices(config, _make_notices())

    ids = store.load_known_ids("test")
    assert ids == {"test:001", "test:002"}


def test_load_nonexistent_returns_empty(tmp_path: Path):
    store = Store(tmp_path / "output")
    assert store.load_notices("nonexistent") == []
    assert store.load_known_ids("nonexistent") == set()


def test_json_output_format(tmp_path: Path):
    store = Store(tmp_path / "output")
    config = _make_source_config()
    store.save_notices(config, _make_notices())

    raw = json.loads(
        (tmp_path / "output" / "sources" / "test.json").read_text(encoding="utf-8")
    )
    assert "meta" in raw
    assert "notices" in raw
    assert raw["meta"]["source_id"] == "test"
    assert raw["meta"]["total_notices"] == 2
    assert raw["notices"][0]["title"] == "第一条通知"


def test_json_preserves_chinese(tmp_path: Path):
    store = Store(tmp_path / "output")
    config = _make_source_config()
    store.save_notices(config, _make_notices())

    text = (tmp_path / "output" / "sources" / "test.json").read_text(
        encoding="utf-8"
    )
    # ensure_ascii=False means Chinese chars appear directly
    assert "第一条通知" in text
    assert "\\u" not in text.split('"第一条通知"')[0][-10:]  # no unicode escapes nearby


def test_save_notices_normalizes_query_ids_and_dedups(tmp_path: Path):
    store = Store(tmp_path / "output")
    config = SourceConfig(
        id="dzb",
        name="党政办公室",
        base_url="https://notice.xidian.edu.cn",
        list_path="index.htm",
    )
    notices = [
        Notice(
            id=(
                "dzb:2016content.jsp?urltype=news.NewsContentUrl&"
                "wbtreeid=1227&wbnewsid=24808"
            ),
            source_id="dzb",
            title="通知A",
            url=(
                "https://notice.xidian.edu.cn/2016content.jsp?"
                "urltype=news.NewsContentUrl&wbtreeid=1227&wbnewsid=24808"
            ),
            date=date(2023, 7, 10),
        ),
        Notice(
            id="dzb:24808",
            source_id="dzb",
            title="通知A",
            url=(
                "https://notice.xidian.edu.cn/2016content.jsp?"
                "urltype=news.NewsContentUrl&wbtreeid=1227&wbnewsid=24808"
            ),
            date=date(2023, 7, 10),
        ),
    ]

    store.save_notices(config, notices)

    raw = json.loads(
        (tmp_path / "output" / "sources" / "dzb.json").read_text(encoding="utf-8")
    )
    assert raw["meta"]["total_notices"] == 1
    assert raw["notices"][0]["id"] == "dzb:24808"


def test_save_index(tmp_path: Path):
    store = Store(tmp_path / "output")
    config = _make_source_config()
    store.save_notices(config, _make_notices())

    store.save_index([config], content_limit=1)

    raw = json.loads((tmp_path / "output" / "feed.json").read_text(encoding="utf-8"))
    assert "generated_at" in raw
    assert raw["total_notices"] == 2
    assert raw["content_limit"] == 1
    assert len(raw["notices"]) == 1
    assert raw["notices"][0]["id"] == "test:001"
    assert raw["notices"][0]["source_name"] == "Test Source"

    docs_text = (tmp_path / "output" / "index.md").read_text(encoding="utf-8")
    assert "# bulletin-xdu API" in docs_text
    assert "feed.json" in docs_text
    assert "sources/test.json" in docs_text
