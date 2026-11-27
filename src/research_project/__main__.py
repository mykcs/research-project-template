"""Evidence-labelled software checks; never imply scientific success."""

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
    verify_asset_manifest,
    write_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
MIN_PYTHON = (3, 11)
MAX_PYTHON = (3, 14)


def smoke(config: Path) -> dict[str, object]:
    return {
        **read_smoke_config(config),
        "kind": "software-smoke",
        "status": "PASS",
        "scientific_result": "NOT_TESTED",
    }


def source_identity(root: Path = ROOT) -> dict[str, object]:
    manifest = read_release_manifest(root)
    if manifest is not None:
        return manifest
    unknown = {"source_commit": "UNKNOWN", "source_dirty": "UNKNOWN"}
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
    return {
        "source_commit": commit,
        "source_dirty": bool(dirty.strip()),
        "source_provenance": "git",
    }


def audit_handoff(root: Path = ROOT) -> dict[str, object]:
    findings: list[str] = []
    warnings: list[str] = []
    if not (root / "README.md").is_file():
        warnings.append("No root README; identify the equivalent newcomer entry manually.")
    candidates = [
        root / "HANDOFF.md",
        root / "docs/HANDOFF.md",
        root / "docs/task/HANDOFF.md",
        root / "docs/task/README.md",
        root / "README.md",
    ]
    documents = [path for path in candidates if path.is_file()]
    if not documents:
        warnings.append("No known entry or handoff document; inspect equivalent project docs.")
    for doc in documents:
        content = doc.read_text(encoding="utf-8")
        for marker in ("待实例化", "TBD", "TODO:"):
            if marker in content:
                warnings.append(f"Unfilled placeholder: {doc.relative_to(root)}:{marker}")
    git_hygiene = "NOT_TESTED"
    if (root / ".git").exists() and not os.environ.get("RESEARCH_RUNTIME_PYTHON"):
        try:
            tracked = (
                subprocess.check_output(
                    ["git", "-C", str(root), "--no-optional-locks", "ls-files", "-z"],
                    env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
                    timeout=3,
                    stderr=subprocess.DEVNULL,
                )
                .decode("utf-8", errors="replace")
                .split("\0")
            )
            environments = [name for name in tracked if ".venv" in Path(name).parts]
            if environments:
                findings.append("Tracked .venv files: " + ", ".join(environments[:5]))
            suspicious = [
                name
                for name in tracked
                if Path(name).suffix.lower() in {".pt", ".pth", ".ckpt", ".mcap", ".bag", ".usd"}
            ]
            if suspicious:
                warnings.append(
                    "Review tracked asset rights and size: " + ", ".join(suspicious[:5])
                )
            git_hygiene = "FAIL" if environments else "PASS"
        except (OSError, subprocess.SubprocessError):
            warnings.append("Could not inspect tracked Git files")
    return {
        "kind": "handoff-audit",
        "status": "FAIL" if findings else "PASS",
        "handoff_ready": False if findings or warnings else None,
        "handoff_readiness": "NOT_VERIFIED",
        "git_hygiene": git_hygiene,
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
    parser.add_argument("--asset-manifest", type=Path, help="Optional trusted asset manifest")
    parser.add_argument("--receipt-out", type=Path, help="New receipt in a personal output folder")
    args = parser.parse_args()
    if args.command == "reproduce":
        print("No scientific reproduction has been configured.", file=sys.stderr)
        return 2
    started = time.perf_counter()
    runtime_mode = bool(os.environ.get("RESEARCH_RUNTIME_PYTHON"))
    try:
        out = (
            validate_output_path(args.receipt_out, ROOT, runtime_mode)
            if args.receipt_out is not None
            else None
        )
        if not MIN_PYTHON <= sys.version_info[:2] < MAX_PYTHON:
            raise ValueError("Unsupported Python; template supports 3.11–3.13")
        if args.command == "doctor":
            result = {
                **read_smoke_config(args.config),
                "kind": "software-preflight",
                "status": "PASS",
                "python_min_required": "3.11",
                "runtime_mode": "shared-runtime" if runtime_mode else "personal-dev",
                "source_writable": os.access(ROOT, os.W_OK),
                "scientific_result": "NOT_TESTED",
            }
        elif args.command == "audit":
            result = audit_handoff(ROOT)
        else:
            result = smoke(args.config)
        if args.asset_manifest is not None:
            result.update(verify_asset_manifest(args.asset_manifest))
        payload = receipt(result, started)
        serialized = json.dumps(payload)
        if out is not None:
            write_receipt(out, serialized)
    except (OSError, ValueError) as exc:
        print(f"Input check failed: {exc}", file=sys.stderr)
        return 2
    print(serialized)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
