import subprocess
import sys
from pathlib import Path

import pytest

from research_project.__main__ import smoke


def test_smoke() -> None:
    assert smoke(Path("configs/smoke.toml"))["scientific_result"] == "NOT_TESTED"


def test_invalid_config(tmp_path: Path) -> None:
    path = tmp_path / "invalid.toml"
    path.write_text('kind = "unknown"\n')
    with pytest.raises(ValueError):
        smoke(path)


def test_reproduce_is_not_fake_success() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "research_project", "reproduce"],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
