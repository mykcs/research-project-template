"""Minimal, evidence-labelled software checks and executable handoff audit."""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from research_project.contracts import (
    read_release_manifest,
    read_smoke_config,
    validate_output_path,
)

ROOT = Path(__file__).resolve().parents[2]
MIN_PYTHON = (3, 11)
PLACEHOLDER_MARKERS = ("待实例化", "TBD", "TODO:")
BLOCKED_TRACKED_SUFFIXES = (
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".safetensors",
    ".bag",
    ".mcap",
    ".usd",
    ".usda",
    ".usdc",
)


def smoke(config: Path) -> dict[str, str | int]:
    return {
        **read_smoke_config(config),
        "kind": "software-smoke",
        "status": "PASS",
        "scientific_result": "NOT_TESTED",
    }


def source_identity(root: Path = ROOT) -> dict[str, str | bool]:
    """Report observed release-manifest or Git identity; never guess provenance."""
    manifest = read_release_manifest(root)
    if manifest is not None:
        return manifest

    unknown: dict[str, str | bool] = {"source_commit": "UNKNOWN", "source_dirty": "UNKNOWN"}
    if os.environ.get("RESEARCH_RUNTIME_PYTHON") or not (root / ".git").exists():
        return unknown
    try:
        env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
        git = ["git", "-C", str(root), "--no-optional-locks"]
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


def audit_handoff(root: Path = ROOT) -> dict[str, object]:
    """Executable, outcome-based audit of handoff discoverability and repo hygiene."""
    findings: list[str] = []
    warnings: list[str] = []

    readme = root / "README.md"
    if not readme.is_file():
        findings.append("Missing root README.md entrypoint.")

    handoff_candidates = [
        root / "HANDOFF.md",
        root / "docs" / "HANDOFF.md",
        root / "docs" / "task" / "HANDOFF.md",
    ]
    handoff_files = [p for p in handoff_candidates if p.is_file()]
    if not handoff_files:
        warnings.append("No dedicated handoff document found (README.md must cover handoff state).")

    placeholder_hits: list[str] = []
    for doc in handoff_files:
        text = doc.read_text(encoding="utf-8", errors="ignore")
        for marker in PLACEHOLDER_MARKERS:
            if marker in text:
                placeholder_hits.append(f"{doc.relative_to(root)}:{marker}")
    if placeholder_hits:
        warnings.append(
            "Template placeholders remain in handoff docs: " + ", ".join(sorted(placeholder_hits))
        )

    tracked_artifacts: list[str] = []
    if (root / ".git").exists() and not os.environ.get("RESEARCH_RUNTIME_PYTHON"):
        try:
            env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
            tracked = subprocess.check_output(
                ["git", "-C", str(root), "--no-optional-locks", "ls-files"],
                env=env,
                text=True,
                timeout=3,
                stderr=subprocess.DEVNULL,
            ).splitlines()
            for item in tracked:
                lower = item.lower()
                if lower.startswith(".venv/") or lower.endswith(BLOCKED_TRACKED_SUFFIXES):
                    tracked_artifacts.append(item)
        except (OSError, subprocess.SubprocessError):
            warnings.append("Could not inspect tracked Git files.")

    if tracked_artifacts:
        findings.append(
            "Large/environment artifacts tracked in Git: " + ", ".join(tracked_artifacts[:10])
        )

    return {
        "kind": "handoff-audit",
        "status": "FAIL" if findings else "PASS",
        "handoff_ready": not findings and not placeholder_hits,
        "findings": findings,
        "warnings": warnings,
        "scientific_result": "NOT_TESTED",
    }


def receipt(result: dict[str, object], started: float, root: Path = ROOT) -> dict[str, object]:
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
        **source_identity(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["doctor", "smoke", "reproduce", "audit"])
    parser.add_argument("--config", type=Path, default=Path("configs/smoke.toml"))
    parser.add_argument(
        "--receipt-out",
        type=Path,
        default=None,
        help="Optional JSON output path outside protected source/release directories.",
    )
    args = parser.parse_args()
    if args.command == "reproduce":
        print("No scientific reproduction has been configured.", file=sys.stderr)
        return 2

    started = time.perf_counter()
    runtime_mode = bool(os.environ.get("RESEARCH_RUNTIME_PYTHON"))
    try:
        out_path = (
            validate_output_path(args.receipt_out, ROOT, runtime_mode=runtime_mode)
            if args.receipt_out is not None
            else None
        )
        if args.command == "doctor":
            result: dict[str, object] = {
                **read_smoke_config(args.config),
                "kind": "software-preflight",
                "status": "PASS" if sys.version_info[:2] >= MIN_PYTHON else "FAIL",
                "python_min_required": f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}",
                "runtime_mode": "shared-runtime" if runtime_mode else "personal-dev",
                "source_writable": os.access(ROOT, os.W_OK),
                "scientific_result": "NOT_TESTED",
            }
        elif args.command == "audit":
            result = audit_handoff(ROOT)
        else:
            result = smoke(args.config)
        payload = receipt(result, started, ROOT)
    except (OSError, ValueError) as exc:
        print(f"Input check failed: {exc}", file=sys.stderr)
        return 2

    serialized = json.dumps(payload)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
