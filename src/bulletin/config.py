from pathlib import Path

import yaml
from pydantic import AliasChoices, BaseModel, Field


class SelectorConfig(BaseModel):
    """CSS selector configuration for a CMS site variant."""

    list_container: str = "ul"
    item: str = "li"
    link: str = "a"
    date: str = "span"
    date_format: str = "text"  # "text" = YYYY-MM-DD span; "split" = day+year-month spans


class PaginationConfig(BaseModel):
    """Pagination URL pattern config."""

    max_pages: int = 5  # Maximum pages to scrape per run


class SourceConfig(BaseModel):
    """Configuration for a single notification source."""

    id: str
    name: str
    adapter: str = "xidian_cms"
    base_url: str
    list_path: str
    selectors: SelectorConfig = SelectorConfig()
    pagination: PaginationConfig = PaginationConfig()


class AppConfig(BaseModel):
    """Top-level application configuration."""

    data_dir: Path = Path("output")
    # Prefer `content_limit`; keep `feed_limit` as backward-compatible alias.
    content_limit: int = Field(
        default=5000,
        validation_alias=AliasChoices("content_limit", "feed_limit"),
    )
    sources: list[SourceConfig]


def load_config(config_path: Path = Path("config/sources.yaml")) -> AppConfig:
    """Load and validate configuration from YAML file."""
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return AppConfig(**raw)
