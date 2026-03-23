import argparse
import asyncio
import logging
from pathlib import Path

from bulletin.adapters import get_adapter
from bulletin.config import load_config
from bulletin.store import Store
from bulletin.utils.http import create_client


async def scrape(config_path: Path) -> bool:
    """Run the scrape pipeline. Returns True if any new notices were found."""
    config = load_config(config_path)
    store = Store(config.data_dir)
    any_new = False

    async with await create_client() as client:
        for source_config in config.sources:
            adapter_cls = get_adapter(source_config.adapter)
            adapter = adapter_cls(source_config, client)

            known_ids = store.load_known_ids(source_config.id)
            existing_notices = store.load_notices(source_config.id)

            try:
                new_notices = await adapter.fetch_notices(known_ids)
            except Exception:
                logging.exception("Failed to scrape %s", source_config.id)
                continue

            if new_notices:
                any_new = True
                merged = new_notices + existing_notices
                merged.sort(key=lambda n: (n.date, n.id), reverse=True)
                store.save_notices(source_config, merged)
            else:
                store.save_notices(source_config, existing_notices)

    store.save_index(config.sources, config.content_limit)
    return any_new


def cli() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="XDU Bulletin Scraper")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config/sources.yaml"),
        help="Path to sources config file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    asyncio.run(scrape(args.config))


if __name__ == "__main__":
    cli()
