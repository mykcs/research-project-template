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


def test_help_does_not_require_an_environment(tmp_path: Path) -> None:
    launcher = tmp_path / "run.sh"
    shutil.copy2(ROOT / "run.sh", launcher)
    env = {**os.environ, "PATH": "/usr/bin:/bin"}
    env.pop("RESEARCH_RUNTIME_PYTHON", None)
    result = subprocess.run(
        [str(launcher), "--help"], env=env, capture_output=True, text=True, check=True
    )
    assert "bootstrap" in result.stdout
    assert not (tmp_path / ".venv").exists()


def test_missing_environment_doctor_never_installs(tmp_path: Path) -> None:
    launcher = tmp_path / "run.sh"
    shutil.copy2(ROOT / "run.sh", launcher)
    trap_dir = tmp_path / "trap"
    trap_dir.mkdir()
    marker = tmp_path / "uv-was-invoked"
    trap = trap_dir / "uv"
    trap.write_text('#!/bin/sh\ntouch "$UV_TRAP_MARKER"\nexit 99\n')
    trap.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{trap_dir}:/usr/bin:/bin",
        "UV_TRAP_MARKER": str(marker),
    }
    env.pop("RESEARCH_RUNTIME_PYTHON", None)
    result = subprocess.run(
        [str(launcher), "doctor"], env=env, capture_output=True, text=True, check=False
    )
    assert result.returncode == 2
    assert "bootstrap" in result.stderr
    assert not marker.exists()
    assert not (tmp_path / ".venv").exists()


def test_prepared_doctor_and_smoke_never_call_uv() -> None:
    env = {**os.environ, "PATH": "/usr/bin:/bin"}
    env.pop("RESEARCH_RUNTIME_PYTHON", None)
    for command in ("doctor", "smoke"):
        result = subprocess.run(
            [str(ROOT / "run.sh"), command],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        report = json.loads(result.stdout)
        assert report["status"] == "PASS"
        assert report["scientific_result"] == "NOT_TESTED"


def test_runtime_pins_alias_without_resolving_executable_link(tmp_path: Path) -> None:
    bin_dir = tmp_path / "version-a" / "bin"
    bin_dir.mkdir(parents=True)
    wrapper = bin_dir / "wrapped-python"
    wrapper.write_text(
        '#!/bin/sh\n[ "$0" = "$EXPECTED_RUNTIME" ] || exit 99\nexec "$ACTUAL_PYTHON" "$@"\n'
    )
    wrapper.chmod(0o755)
    python = bin_dir / "python"
    python.symlink_to(wrapper.name)
    current = tmp_path / "current"
    current.symlink_to(bin_dir.parent, target_is_directory=True)
    env = {
        **runtime_env(),
        "RESEARCH_RUNTIME_PYTHON": str(current / "bin" / "python"),
        "EXPECTED_RUNTIME": str(python),
        "ACTUAL_PYTHON": sys.executable,
    }
    result = subprocess.run(
        [str(ROOT / "run.sh"), "doctor"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["status"] == "PASS"


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
        json.dumps(
            {
                "schema_version": 1,
                "source_commit": "0123456789abcdef0123456789abcdef01234567",
                "release_version": "0.3",
            }
        ),
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
    assert report["source_commit"] == "0123456789abcdef0123456789abcdef01234567"
    assert report["source_provenance"] == "release-manifest-declared"
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
