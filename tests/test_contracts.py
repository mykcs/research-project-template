import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research_project.__main__ import audit_handoff
from research_project.contracts import (
    read_release_manifest,
    read_smoke_config,
    validate_output_path,
    verify_asset_manifest,
)

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


def test_doctor_supports_python_311_plus_and_reports_runtime_mode() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "research_project", "doctor"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"
    assert report["python_min_required"] == "3.11"
    assert report["runtime_mode"] in {"personal-dev", "shared-runtime"}
    assert report["scientific_result"] == "NOT_TESTED"


def test_release_manifest_provenance_and_fail_closed(tmp_path: Path) -> None:
    assert read_release_manifest(tmp_path) is None
    manifest = tmp_path / "RELEASE_MANIFEST.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_commit": "abc123def456",
                "release_version": "0.3.0",
            }
        ),
        encoding="utf-8",
    )
    info = read_release_manifest(tmp_path)
    assert info is not None
    assert info["source_commit"] == "abc123def456"
    assert info["source_provenance"] == "release-manifest"
    assert info["release_version"] == "0.3.0"

    manifest.write_text(json.dumps({"schema_version": 2, "source_commit": "x"}), encoding="utf-8")
    with pytest.raises(ValueError):
        read_release_manifest(tmp_path)


def test_asset_manifest_verifies_sha256_and_fails_closed(tmp_path: Path) -> None:
    asset = tmp_path / "robot.urdf"
    payload = b"<robot name='kepler_k2'/>\n"
    asset.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    manifest = tmp_path / "assets.toml"
    manifest.write_text(
        f'schema_version = 1\n\n[[assets]]\nname = "k2_urdf"\npath = "robot.urdf"\nsha256 = "{digest}"\n',
        encoding="utf-8",
    )
    verified = verify_asset_manifest(manifest)
    assert len(verified["verified_assets"]) == 1
    assert verified["verified_assets"][0]["sha256"] == digest

    asset.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_asset_manifest(manifest)


def test_output_path_isolation_guards_protected_and_runtime_paths(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    with pytest.raises(ValueError, match="protected directory"):
        validate_output_path(tmp_path / "src" / "receipt.json", tmp_path, runtime_mode=False)
    with pytest.raises(ValueError, match="read-only or shared runtime"):
        validate_output_path(tmp_path / "outputs" / "receipt.json", tmp_path, runtime_mode=True)
    safe = validate_output_path(tmp_path.parent / "personal_out.json", tmp_path, runtime_mode=True)
    assert safe.name == "personal_out.json"


def test_audit_handoff_flags_placeholders_without_faking_ready(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "HANDOFF.md").write_text("状态：待实例化\n", encoding="utf-8")
    report = audit_handoff(tmp_path)
    assert report["status"] == "PASS"
    assert report["handoff_ready"] is False
    assert any("待实例化" in w for w in report["warnings"])
