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
                "source_commit": "0123456789abcdef0123456789abcdef01234567",
                "release_version": "0.3.0",
            }
        ),
        encoding="utf-8",
    )
    info = read_release_manifest(tmp_path)
    assert info is not None
    assert info["source_commit"] == "0123456789abcdef0123456789abcdef01234567"
    assert info["source_provenance"] == "release-manifest-declared"
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
        f'schema_version = 1\n\n[[assets]]\nname = "k2_urdf"\n'
        f'path = "robot.urdf"\nsha256 = "{digest}"\n',
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
    (tmp_path / "outputs").mkdir()
    with pytest.raises(ValueError, match="protected directory"):
        validate_output_path(tmp_path / "src" / "receipt.json", tmp_path, runtime_mode=False)
    with pytest.raises(ValueError, match="read-only or shared runtime"):
        validate_output_path(tmp_path / "outputs" / "receipt.json", tmp_path, runtime_mode=True)
    safe = validate_output_path(tmp_path.parent / "personal_out.json", tmp_path, runtime_mode=True)
    assert safe.name == "personal_out.json"


def test_audit_handoff_flags_placeholders_without_faking_ready(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "HANDOFF.md").write_text("状态：待实例化\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.py").write_text("VALUE = 1\n")
    report = audit_handoff(tmp_path)
    assert report["status"] == "PASS"
    assert report["handoff_ready"] is False
    assert any("待实例化" in w for w in report["warnings"])


def test_release_rejects_unverified_commit_label(tmp_path: Path) -> None:
    (tmp_path / "RELEASE_MANIFEST.json").write_text(
        json.dumps({"schema_version": 1, "source_commit": "made-up"})
    )
    with pytest.raises(ValueError, match="full Git"):
        read_release_manifest(tmp_path)


def test_audit_never_claims_human_acceptance(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# empty\n")
    report = audit_handoff(tmp_path)
    assert report["handoff_ready"] is not True
    assert report["handoff_readiness"] == "NOT_VERIFIED"
    assert report["git_hygiene"] == "NOT_TESTED"


def test_asset_cli_and_exclusive_receipt(tmp_path: Path) -> None:
    asset = tmp_path / "model.bin"
    asset.write_bytes(b"sample")
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    manifest = tmp_path / "assets.toml"
    manifest.write_text(
        f'schema_version = 1\n[[assets]]\nname = "model"\npath = "model.bin"\nsha256 = "{digest}"\n'
    )
    target = tmp_path / "receipt.json"
    args = [
        sys.executable,
        "-m",
        "research_project",
        "doctor",
        "--asset-manifest",
        str(manifest),
        "--receipt-out",
        str(target),
    ]
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["verified_assets"][0]["sha256"] == digest
    original = target.read_bytes()
    assert subprocess.run(args, cwd=ROOT, capture_output=True, check=False).returncode == 2
    assert target.read_bytes() == original
    asset.write_bytes(b"tampered")
    args[-1] = str(tmp_path / "second.json")
    bad = subprocess.run(args, cwd=ROOT, capture_output=True, check=False)
    assert bad.returncode == 2
    assert not (tmp_path / "second.json").exists()


def test_output_protects_all_source_and_existing_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("keep")
    with pytest.raises(ValueError, match="overwrite"):
        validate_output_path(repo / "README.md", repo)
    with pytest.raises(ValueError, match="protected"):
        validate_output_path(repo / "new.py", repo)
    (repo / "outputs").mkdir()
    assert (
        validate_output_path(repo / "outputs/run.json", repo)
        == (repo / "outputs/run.json").resolve()
    )


def test_shared_prefix_blocks_receipts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    shared = tmp_path / "shared"
    shared.mkdir()
    monkeypatch.setenv("RESEARCH_SHARED_PREFIXES", str(shared))
    with pytest.raises(ValueError, match="configured shared"):
        validate_output_path(shared / "run.json", tmp_path / "repo")


def test_audit_requires_actual_root_src(tmp_path: Path) -> None:
    assert audit_handoff(tmp_path)["status"] == "FAIL"
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "README.md").write_text("# not source")
    assert audit_handoff(tmp_path)["status"] == "FAIL"
    (tmp_path / "src" / "main.py").write_text("VALUE = 1")
    assert audit_handoff(tmp_path)["status"] == "PASS"


def write_profile(root: Path, profile: str) -> None:
    (root / "README.md").write_text(f"# Example\n\nRepository profile: {profile}\n")


def create_code(root: Path) -> None:
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("VALUE = 1")


def create_website(root: Path) -> None:
    (root / "src").mkdir(parents=True)
    (root / "src" / "index.astro").write_text("<h1>Site</h1>")
    (root / "astro.config.mjs").write_text("export default {}")


def test_audit_code_profile_does_not_require_website(tmp_path: Path) -> None:
    write_profile(tmp_path, "code")
    create_code(tmp_path)
    report = audit_handoff(tmp_path)
    assert report["status"] == "PASS"
    assert report["repository_profile"] == "code"
    (tmp_path / "astro.config.mjs").write_text("export default {}")
    assert audit_handoff(tmp_path)["status"] == "FAIL"


def test_audit_independent_website_root_src(tmp_path: Path) -> None:
    write_profile(tmp_path, "website")
    create_website(tmp_path)
    report = audit_handoff(tmp_path)
    assert report["status"] == "PASS"
    assert report["repository_profile"] == "website"
    assert not (tmp_path / "website").exists()
    assert report["handoff_readiness"] == "NOT_VERIFIED"


def test_audit_independent_website_nested_root_without_code(tmp_path: Path) -> None:
    write_profile(tmp_path, "website")
    create_website(tmp_path / "website" / "site")
    assert not (tmp_path / "src").exists()
    assert audit_handoff(tmp_path)["status"] == "PASS"
    (tmp_path / "astro.config.mjs").write_text("export default {}")
    assert audit_handoff(tmp_path)["status"] == "FAIL"


def test_audit_project_requires_both_actual_source_roots(tmp_path: Path) -> None:
    write_profile(tmp_path, "project")
    create_code(tmp_path)
    assert audit_handoff(tmp_path)["status"] == "FAIL"
    (tmp_path / "website").mkdir()
    (tmp_path / "website" / "astro.config.mjs").write_text("export default {}")
    assert audit_handoff(tmp_path)["status"] == "FAIL"
    create_website(tmp_path / "website")
    report = audit_handoff(tmp_path)
    assert report["status"] == "PASS"
    assert report["repository_profile"] == "project"
    (tmp_path / "astro.config.mjs").write_text("export default {}")
    assert audit_handoff(tmp_path)["status"] == "FAIL"


def test_audit_does_not_accept_duplicate_or_empty_website(tmp_path: Path) -> None:
    write_profile(tmp_path, "website")
    (tmp_path / "website").mkdir()
    (tmp_path / "website" / "astro.config.mjs").write_text("export default {}")
    assert audit_handoff(tmp_path)["status"] == "FAIL"
    create_website(tmp_path)
    assert audit_handoff(tmp_path)["status"] == "FAIL"


def test_audit_rejects_unknown_and_duplicate_profiles(tmp_path: Path) -> None:
    write_profile(tmp_path, "other")
    create_code(tmp_path)
    assert audit_handoff(tmp_path)["status"] == "FAIL"
    write_profile(tmp_path, "code\nRepository profile: project")
    assert audit_handoff(tmp_path)["repository_profile"] == "UNKNOWN"
    assert audit_handoff(tmp_path)["status"] == "FAIL"


def test_audit_unmarked_legacy_code_is_advisory(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Existing project")
    create_code(tmp_path)
    report = audit_handoff(tmp_path)
    assert report["status"] == "PASS"
    assert report["repository_profile"] == "UNKNOWN"
    assert any("No Repository profile declared" in warning for warning in report["warnings"])
    assert report["handoff_readiness"] == "NOT_VERIFIED"


def test_unmarked_website_is_not_misclassified_as_code(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Standalone site")
    create_website(tmp_path)
    report = audit_handoff(tmp_path)
    assert report["status"] == "PASS"
    assert report["repository_profile"] == "UNKNOWN"
    assert report["handoff_readiness"] == "NOT_VERIFIED"


def test_unmarked_combined_project_is_not_misclassified_as_code(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Research and companion site")
    create_code(tmp_path)
    create_website(tmp_path / "website")
    report = audit_handoff(tmp_path)
    assert report["status"] == "PASS"
    assert report["repository_profile"] == "UNKNOWN"
    assert report["handoff_readiness"] == "NOT_VERIFIED"
