import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_project.contracts import read_smoke_config

ROOT = Path(__file__).resolve().parents[1]


def test_input_fingerprint_is_exact_and_read_only(tmp_path: Path) -> None:
    config = tmp_path / "input.toml"
    raw = b'schema_version = 1\nkind = "software-smoke"\n'
    config.write_bytes(raw)
    result = read_smoke_config(config)
    assert result["config_schema_version"] == 1
    assert result["config_sha256"] == hashlib.sha256(raw).hexdigest()
    assert config.read_bytes() == raw


def test_legacy_v01_config_still_works(tmp_path: Path) -> None:
    config = tmp_path / "input.toml"
    config.write_text('kind = "software-smoke"\n')
    assert read_smoke_config(config)["config_schema_version"] == 1


@pytest.mark.parametrize(
    "extra", ["schema_version = 2", "schema_version = true", "unsupported = 1"]
)
def test_invalid_contract_fails_closed(tmp_path: Path, extra: str) -> None:
    config = tmp_path / "input.toml"
    config.write_text(f'kind = "software-smoke"\n{extra}\n')
    with pytest.raises(ValueError):
        read_smoke_config(config)


def test_doctor_rejects_bad_input_without_scientific_execution(tmp_path: Path) -> None:
    config = tmp_path / "input.toml"
    config.write_text('kind = "software-smoke"\nschema_version = 99\n')
    result = subprocess.run(
        [sys.executable, "-m", "research_project", "doctor", "--config", str(config)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 2
    assert "Unsupported" in result.stderr
    assert not result.stdout


def test_smoke_receipt_has_explicit_evidence_scope() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "research_project", "smoke"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )
    report = json.loads(result.stdout)
    assert report["receipt_schema"] == "research-software-check/v1"
    assert report["validation_scope"] == "SOFTWARE_ONLY"
    assert report["scientific_result"] == "NOT_TESTED"
    assert report["backend"] == "NONE"
    assert report["gpu"] == "NOT_TESTED"
    assert len(report["run_id"]) == 32
    assert len(report["config_sha256"]) == 64
    assert report["check_elapsed_seconds"] >= 0
    assert "source_commit" in report
    assert "source_dirty" in report
