from pathlib import Path

import pytest

from bulletin.config import AppConfig, SelectorConfig, load_config


def test_load_config(tmp_path: Path):
    config_file = tmp_path / "sources.yaml"
    config_file.write_text(
        """
data_dir: output
sources:
  - id: test
    name: "Test Source"
    base_url: "https://example.com"
    list_path: "news.htm"
""",
        encoding="utf-8",
    )

    config = load_config(config_file)
    assert len(config.sources) == 1
    assert config.sources[0].id == "test"
    assert config.sources[0].adapter == "xidian_cms"
    assert config.data_dir == Path("output")
    assert config.content_limit == 5000


def test_load_config_with_content_limit(tmp_path: Path):
    config_file = tmp_path / "sources.yaml"
    config_file.write_text(
        """
data_dir: output
content_limit: 123
sources:
  - id: test
    name: "Test Source"
    base_url: "https://example.com"
    list_path: "news.htm"
""",
        encoding="utf-8",
    )

    config = load_config(config_file)
    assert config.content_limit == 123


def test_load_config_with_legacy_feed_limit_alias(tmp_path: Path):
    config_file = tmp_path / "sources.yaml"
    config_file.write_text(
        """
data_dir: output
feed_limit: 456
sources:
  - id: test
    name: "Test Source"
    base_url: "https://example.com"
    list_path: "news.htm"
""",
        encoding="utf-8",
    )

    config = load_config(config_file)
    assert config.content_limit == 456


def test_selector_defaults():
    sel = SelectorConfig()
    assert sel.list_container == "ul"
    assert sel.item == "li"
    assert sel.link == "a"
    assert sel.date_format == "text"


def test_config_requires_sources():
    with pytest.raises(Exception):
        AppConfig()  # type: ignore -- missing required 'sources' field


def test_real_config():
    """Test that the actual config/sources.yaml loads successfully."""
    config_path = Path("config/sources.yaml")
    if config_path.exists():
        config = load_config(config_path)
        assert len(config.sources) >= 1
        for source in config.sources:
            assert source.id
            assert source.base_url.startswith("https://")
