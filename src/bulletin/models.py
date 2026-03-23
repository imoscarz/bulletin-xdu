from datetime import date, datetime

from pydantic import BaseModel


class Notice(BaseModel):
    """A single notice/bulletin item."""

    id: str  # Unique identifier: "{source_id}:{article_id}"
    source_id: str  # Which source this came from (e.g., "jwc")
    title: str  # Notice title text
    url: str  # Absolute URL to the notice detail page
    date: date  # Publication date


class SourceMeta(BaseModel):
    """Metadata about a scraped source, stored alongside its notices."""

    source_id: str
    name: str  # Human-readable name (e.g., "教务处通知公告")
    url: str  # The list page URL
    last_scraped: datetime  # ISO timestamp of last successful scrape
    total_notices: int  # Number of notices stored
