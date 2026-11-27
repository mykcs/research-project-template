"""Minimal, evidence-labelled software checks; no scientific result is implied."""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from research_project.contracts import read_smoke_config

ROOT = Path(__file__).resolve().parents[2]


def smoke(config: Path) -> dict[str, str | int]:
    return {
        **read_smoke_config(config),
        "kind": "software-smoke",
        "status": "PASS",
        "scientific_result": "NOT_TESTED",
    }


def source_identity() -> dict[str, str | bool]:
    """Report observed Git identity; never guess a published snapshot's provenance."""
    unknown = {"source_commit": "UNKNOWN", "source_dirty": "UNKNOWN"}
    if os.environ.get("RESEARCH_RUNTIME_PYTHON") or not (ROOT / ".git").exists():
        return unknown
    try:
        env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
        git = ["git", "-C", str(ROOT), "--no-optional-locks"]
        commit = subprocess.check_output(
            [*git, "rev-parse", "HEAD"],
            env=env,
            text=True,
            timeout=3,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = subprocess.check_output(
            [*git, "status", "--porcelain", "--untracked-files=normal"],
            env=env,
            text=True,
            timeout=3,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return unknown
    return {"source_commit": commit, "source_dirty": bool(dirty.strip())}


def receipt(result: dict[str, str | int], started: float) -> dict[str, object]:
    return {
        "receipt_schema": "research-software-check/v1",
        "run_id": uuid.uuid4().hex,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "check_elapsed_seconds": round(time.perf_counter() - started, 6),
        "validation_scope": "SOFTWARE_ONLY",
        "backend": "NONE",
        "python": sys.version.split()[0],
        "gpu": "NOT_TESTED",
        **result,
        **source_identity(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["doctor", "smoke", "reproduce"])
    parser.add_argument("--config", type=Path, default=Path("configs/smoke.toml"))
    args = parser.parse_args()
    if args.command == "reproduce":
        print("No scientific reproduction has been configured.", file=sys.stderr)
        return 2

    started = time.perf_counter()
    try:
        if args.command == "doctor":
            result = {
                **read_smoke_config(args.config),
                "kind": "software-preflight",
                "status": "PASS" if sys.version_info[:2] == (3, 12) else "FAIL",
                "scientific_result": "NOT_TESTED",
            }
        else:
            result = smoke(args.config)
    except (OSError, ValueError) as exc:
        print(f"Input check failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt(result, started)))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
