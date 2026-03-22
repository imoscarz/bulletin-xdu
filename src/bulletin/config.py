from pathlib import Path

import yaml
from pydantic import BaseModel


class SelectorConfig(BaseModel):
    """CSS selector configuration for a CMS site variant."""

    list_container: str = "ul"
    item: str = "li"
    link: str = "a"
    date: str = "span"
    date_format: str = "text"  # "text" = YYYY-MM-DD span; "split" = day+year-month spans
    new_badge: str = "img[src*='new']"


class PaginationConfig(BaseModel):
    """Pagination URL pattern config."""

    pattern: str = "{base}/{page}.htm"
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

    data_dir: Path = Path("data")
    sources: list[SourceConfig]


def load_config(config_path: Path = Path("config/sources.yaml")) -> AppConfig:
    """Load and validate configuration from YAML file."""
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return AppConfig(**raw)
