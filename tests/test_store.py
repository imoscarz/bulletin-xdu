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
            is_new=True,
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
    store = Store(tmp_path / "data")
    config = _make_source_config()
    notices = _make_notices()

    store.save_notices(config, notices)
    loaded = store.load_notices("test")

    assert len(loaded) == 2
    assert loaded[0].id == "test:001"
    assert loaded[0].title == "第一条通知"
    assert loaded[1].date == date(2026, 3, 19)


def test_load_known_ids(tmp_path: Path):
    store = Store(tmp_path / "data")
    config = _make_source_config()
    store.save_notices(config, _make_notices())

    ids = store.load_known_ids("test")
    assert ids == {"test:001", "test:002"}


def test_load_nonexistent_returns_empty(tmp_path: Path):
    store = Store(tmp_path / "data")
    assert store.load_notices("nonexistent") == []
    assert store.load_known_ids("nonexistent") == set()


def test_json_output_format(tmp_path: Path):
    store = Store(tmp_path / "data")
    config = _make_source_config()
    store.save_notices(config, _make_notices())

    raw = json.loads((tmp_path / "data" / "test.json").read_text(encoding="utf-8"))
    assert "meta" in raw
    assert "notices" in raw
    assert raw["meta"]["source_id"] == "test"
    assert raw["meta"]["total_notices"] == 2
    assert raw["notices"][0]["title"] == "第一条通知"


def test_json_preserves_chinese(tmp_path: Path):
    store = Store(tmp_path / "data")
    config = _make_source_config()
    store.save_notices(config, _make_notices())

    text = (tmp_path / "data" / "test.json").read_text(encoding="utf-8")
    # ensure_ascii=False means Chinese chars appear directly
    assert "第一条通知" in text
    assert "\\u" not in text.split('"第一条通知"')[0][-10:]  # no unicode escapes nearby


def test_save_index(tmp_path: Path):
    store = Store(tmp_path / "data")
    config = _make_source_config()
    store.save_notices(config, _make_notices())

    store.save_index([config])

    raw = json.loads((tmp_path / "data" / "index.json").read_text(encoding="utf-8"))
    assert "generated_at" in raw
    assert len(raw["sources"]) == 1
    assert raw["sources"][0]["source_id"] == "test"
    assert raw["sources"][0]["total_notices"] == 2
    assert raw["sources"][0]["data_url"] == "test.json"
    assert len(raw["sources"][0]["latest"]) == 2
