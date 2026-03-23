import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from bulletin.adapters.base import BaseAdapter
from bulletin.config import SourceConfig
from bulletin.models import Notice, SourceMeta

logger = logging.getLogger(__name__)


class Store:
    """Manages JSON file storage for notices."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._sources_dir().mkdir(parents=True, exist_ok=True)

    def _source_path(self, source_id: str) -> Path:
        return self._sources_dir() / f"{source_id}.json"

    def _sources_dir(self) -> Path:
        return self.data_dir / "sources"

    def _index_path(self) -> Path:
        return self.data_dir / "feed.json"

    def _docs_index_path(self) -> Path:
        return self.data_dir / "index.md"

    def load_notices(self, source_id: str) -> list[Notice]:
        """Load existing notices for a source. Returns empty list if none exist."""
        path = self._source_path(source_id)
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [Notice(**item) for item in raw.get("notices", [])]

    def load_known_ids(self, source_id: str) -> set[str]:
        """Load the set of known notice IDs for a source."""
        return {n.id for n in self.load_notices(source_id)}

    def save_notices(
        self,
        source_config: SourceConfig,
        notices: list[Notice],
    ) -> None:
        """Save the full notice list for a source (merged, sorted by date desc)."""
        path = self._source_path(source_config.id)
        notices = self._normalize_notices(source_config.id, notices)

        meta = SourceMeta(
            source_id=source_config.id,
            name=source_config.name,
            url=f"{source_config.base_url}/{source_config.list_path}",
            last_scraped=datetime.now(timezone.utc),
            total_notices=len(notices),
        )

        output = {
            "meta": meta.model_dump(mode="json"),
            "notices": [n.model_dump(mode="json") for n in notices],
        }

        path.write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.info("Saved %d notices to %s", len(notices), path)

    @staticmethod
    def _normalize_notices(source_id: str, notices: list[Notice]) -> list[Notice]:
        """Normalize IDs and remove duplicates by URL, keeping first occurrence."""
        normalized: list[Notice] = []
        seen_urls: set[str] = set()

        for notice in notices:
            if notice.url in seen_urls:
                continue

            article_id = BaseAdapter._extract_article_id(notice.url)
            normalized.append(
                notice.model_copy(update={"id": f"{source_id}:{article_id}"})
            )
            seen_urls.add(notice.url)

        return normalized

    def save_index(
        self,
        source_configs: list[SourceConfig],
        content_limit: int = 5000,
    ) -> None:
        """Write global feed.json sorted by publication date across all notices."""
        source_names = {sc.id: sc.name for sc in source_configs}
        all_notices: list[dict[str, object]] = []

        for sc in source_configs:
            notices = self.load_notices(sc.id)
            for notice in notices:
                item = notice.model_dump(mode="json")
                item["source_name"] = source_names.get(sc.id, sc.id)
                all_notices.append(item)

        all_notices.sort(
            key=lambda item: (
                str(item["date"]),
                str(item["id"]),
            ),
            reverse=True,
        )

        limited_notices = all_notices[: max(0, content_limit)]

        generated_at = datetime.now(timezone.utc).isoformat()
        index = {
            "generated_at": generated_at,
            "total_notices": len(all_notices),
            "content_limit": max(0, content_limit),
            "notices": limited_notices,
        }

        path = self._index_path()
        path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.info("Saved index to %s", path)

        self._docs_index_path().write_text(
            self._build_api_docs(source_configs, generated_at),
            encoding="utf-8",
        )
        logger.info("Saved API docs to %s", self._docs_index_path())

    def _build_api_docs(
        self,
        source_configs: list[SourceConfig],
        generated_at: str,
    ) -> str:
        lines = [
            "# bulletin-xdu API",
            "",
            f"- generated_at: {generated_at}",
            "",
            "## Endpoints",
            "",
            "- `feed.json`: 全部通知（按发布时间倒序，受 content_limit 限制）",
            "",
            "## Sources",
            "",
        ]

        for sc in source_configs:
            lines.append(
                f"- `{sc.id}`: `sources/{sc.id}.json` ({sc.name})"
            )

        lines.append("")
        return "\n".join(lines)
