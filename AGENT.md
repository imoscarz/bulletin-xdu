# Development Guide

## Setup
```bash
uv sync --all-extras
```

## Run
```bash
uv run bulletin -v                    # scrape all sources
uv run bulletin -c config/sources.yaml  # specify config
```

## Test
```bash
uv run pytest
```

## Project Layout
- `src/bulletin/` — main package (src layout, built with hatchling)
- `config/sources.yaml` — source definitions
- `data/` — output JSON files (committed by CI)
- `tests/fixtures/` — saved HTML snapshots for testing

## Adding a new adapter
1. Create `src/bulletin/adapters/my_adapter.py` extending `BaseAdapter`
2. Implement `async fetch_notices(known_ids) -> list[Notice]`
3. Register in `src/bulletin/adapters/__init__.py` ADAPTER_REGISTRY
4. Reference as `adapter: my_adapter` in sources.yaml
