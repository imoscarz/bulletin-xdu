from datetime import date

from bulletin.models import Notice, SourceMeta


def test_notice_serialization():
    notice = Notice(
        id="jwc:21703",
        source_id="jwc",
        title="测试通知标题",
        url="https://jwc.xidian.edu.cn/info/1012/21703.htm",
        date=date(2026, 3, 13),
        is_new=True,
    )
    data = notice.model_dump(mode="json")
    assert data["id"] == "jwc:21703"
    assert data["date"] == "2026-03-13"
    assert data["is_new"] is True

    # Round-trip
    restored = Notice(**data)
    assert restored == notice


def test_notice_default_is_new():
    notice = Notice(
        id="cs:1234",
        source_id="cs",
        title="测试",
        url="https://cs.xidian.edu.cn/info/1003/1234.htm",
        date=date(2026, 1, 1),
    )
    assert notice.is_new is False


def test_source_meta_serialization():
    from datetime import datetime, timezone

    meta = SourceMeta(
        source_id="jwc",
        name="教务处通知公告",
        url="https://jwc.xidian.edu.cn/tzgg.htm",
        last_scraped=datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc),
        total_notices=150,
    )
    data = meta.model_dump(mode="json")
    assert data["source_id"] == "jwc"
    assert "2026-03-20" in data["last_scraped"]
