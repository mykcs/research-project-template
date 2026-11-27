import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def runtime_env() -> dict[str, str]:
    return {
        **os.environ,
        "RESEARCH_RUNTIME_PYTHON": sys.executable,
        "PATH": "/usr/bin:/bin",
    }


def test_runtime_does_not_need_uv() -> None:
    result = subprocess.run(
        [str(ROOT / "run.sh"), "smoke"],
        env=runtime_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["scientific_result"] == "NOT_TESTED"


def test_runtime_rejects_development_sync() -> None:
    result = subprocess.run(
        [str(ROOT / "run.sh"), "ci"],
        env=runtime_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "personal checkout" in result.stderr


def test_symlinked_venv_rejected(tmp_path: Path) -> None:
    launcher = tmp_path / "run.sh"
    shutil.copy2(ROOT / "run.sh", launcher)
    target = tmp_path / "other-env"
    target.mkdir()
    (tmp_path / ".venv").symlink_to(target, target_is_directory=True)
    env = {**os.environ, "PATH": "/usr/bin:/bin"}
    env.pop("RESEARCH_RUNTIME_PYTHON", None)
    result = subprocess.run(
        [str(launcher), "doctor"], env=env, capture_output=True, text=True, check=False
    )
    assert result.returncode == 2
    assert "symlinked" in result.stderr


def test_release_entry_does_not_write_source(tmp_path: Path) -> None:
    release = tmp_path / "releases" / "candidate"
    release.mkdir(parents=True)
    shutil.copy2(ROOT / "run.sh", release / "run.sh")
    shutil.copytree(ROOT / "configs", release / "configs")
    shutil.copytree(
        ROOT / "src",
        release / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    current = tmp_path / "current"
    current.symlink_to(release, target_is_directory=True)
    before = sorted(str(path.relative_to(release)) for path in release.rglob("*"))
    result = subprocess.run(
        [str(current / "run.sh"), "smoke"],
        env=runtime_env(),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    after = sorted(str(path.relative_to(release)) for path in release.rglob("*"))
    report = json.loads(result.stdout)
    assert report["status"] == "PASS"
    assert report["source_commit"] == "UNKNOWN"
    assert report["scientific_result"] == "NOT_TESTED"
    assert before == after


def test_release_manifest_blocks_dev_sync_and_reports_commit(tmp_path: Path) -> None:
    release = tmp_path / "published_v03"
    release.mkdir(parents=True)
    shutil.copy2(ROOT / "run.sh", release / "run.sh")
    shutil.copytree(ROOT / "configs", release / "configs")
    shutil.copytree(
        ROOT / "src",
        release / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (release / "RELEASE_MANIFEST.json").write_text(
        json.dumps({"schema_version": 1, "source_commit": "deadbeef1234", "release_version": "0.3"}),
        encoding="utf-8",
    )

    dev_env = {**os.environ, "PATH": "/usr/bin:/bin"}
    dev_env.pop("RESEARCH_RUNTIME_PYTHON", None)
    blocked = subprocess.run(
        [str(release / "run.sh"), "doctor"],
        env=dev_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert blocked.returncode == 2
    assert "RESEARCH_RUNTIME_PYTHON" in blocked.stderr

    out_file = tmp_path / "personal_receipt.json"
    ok = subprocess.run(
        [str(release / "run.sh"), "smoke", "--receipt-out", str(out_file)],
        env=runtime_env(),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(ok.stdout)
    assert report["source_commit"] == "deadbeef1234"
    assert report["source_provenance"] == "release-manifest"
    assert json.loads(out_file.read_text(encoding="utf-8"))["run_id"] == report["run_id"]

    rejected_inside = subprocess.run(
        [str(release / "run.sh"), "smoke", "--receipt-out", str(release / "leak.json")],
        env=runtime_env(),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rejected_inside.returncode == 2
    assert not (release / "leak.json").exists()
