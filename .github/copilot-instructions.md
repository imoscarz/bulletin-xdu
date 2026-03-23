# Copilot Instructions for bulletin-xdu

This repository is a Python 3.12 project for scraping XDU bulletin websites and publishing JSON outputs.

## Core Context

- Package layout uses `src/` (`src/bulletin/`).
- Main entry point is CLI script `bulletin` mapped to `bulletin.main:cli`.
- Source definitions live in `config/sources.yaml`.
- Scraped outputs are JSON files under `data/`.
- Tests are in `tests/` and use pytest.

## Tooling And Commands

- Use `uv` for dependency management and command execution.
- Setup environment:
  - `uv sync --all-extras`
- Run scraper:
  - `uv run bulletin -v`
  - `uv run bulletin -c config/sources.yaml`
- Run tests:
  - `uv run pytest`

## Coding Conventions

- Keep compatibility with Python `>=3.12`.
- Follow existing typing style (`list[T]`, `set[str]`, `X | None`).
- Preserve async boundaries:
  - network and scraping flow should remain async (`httpx.AsyncClient`, async adapter methods).
- Keep adapters incremental:
  - `fetch_notices(known_ids)` should stop pagination when known IDs are encountered.
- Prefer small, focused helpers for parsing logic.
- Reuse existing utilities in `bulletin.utils` before adding new abstractions.

## Adapter Development Rules

When adding a new source adapter:

1. Create `src/bulletin/adapters/<name>.py` and extend `BaseAdapter`.
2. Implement `async fetch_notices(known_ids) -> list[Notice]`.
3. Ensure notice IDs follow `"{source_id}:{article_id}"` format.
4. Register the adapter in `src/bulletin/adapters/__init__.py`.
5. Add/update source configuration in `config/sources.yaml`.
6. Add parser and pagination tests in `tests/` with fixture HTML when needed.

## Data And Test Expectations

- Do not break schema expectations of generated JSON consumed by `data/index.json` and per-source files.
- For parser changes, prioritize deterministic tests with fixtures under `tests/fixtures/`.
- Prefer updating tests together with behavior changes.

## Change Scope Guidance

- Keep edits minimal and localized.
- Avoid unrelated refactors in parser-heavy modules.
- Preserve public interfaces unless a task explicitly requires breaking changes.