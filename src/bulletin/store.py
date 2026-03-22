import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from bulletin.config import SourceConfig
from bulletin.models import Notice, SourceMeta

logger = logging.getLogger(__name__)


class Store:
    """Manages JSON file storage for notices."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _source_path(self, source_id: str) -> Path:
        return self.data_dir / f"{source_id}.json"

    def _index_path(self) -> Path:
        return self.data_dir / "index.json"

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

    def save_index(self, source_configs: list[SourceConfig]) -> None:
        """Write the global index.json listing all sources with their latest notices."""
        sources_summary = []

        for sc in source_configs:
            notices = self.load_notices(sc.id)
            latest = notices[:10]

            sources_summary.append(
                {
                    "source_id": sc.id,
                    "name": sc.name,
                    "url": f"{sc.base_url}/{sc.list_path}",
                    "total_notices": len(notices),
                    "latest": [n.model_dump(mode="json") for n in latest],
                    "data_url": f"{sc.id}.json",
                }
            )

        index = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": sources_summary,
        }

        path = self._index_path()
        path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        logger.info("Saved index to %s", path)
