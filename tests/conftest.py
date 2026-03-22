from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def jwc_html(fixtures_dir: Path) -> str:
    return (fixtures_dir / "jwc_page1.html").read_text(encoding="utf-8")
