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


WEBSITE_CONFIG_PATTERNS = ("astro.config.*", "next.config.*", "nuxt.config.*", "svelte.config.*")
WEBSITE_SUFFIXES = {
    ".astro",
    ".html",
    ".htm",
    ".vue",
    ".svelte",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".mdx",
    ".php",
    ".py",
    ".rb",
    ".go",
    ".rs",
}


def has_source(directory: Path, *, web: bool = False) -> bool:
    """Minimum source-presence heuristic, not a language or ownership audit."""
    if directory.is_symlink() or not directory.is_dir():
        return False
    ignored = {"__pycache__", "node_modules", "dist", "build"}
    for path in directory.rglob("*"):
        parts = path.relative_to(directory).parts
        if any(part.startswith(".") or part in ignored for part in parts):
            continue
        if not path.is_file() or path.is_symlink():
            continue
        if web:
            if path.suffix.lower() in WEBSITE_SUFFIXES and ".config." not in path.name:
                return True
        elif path.suffix.lower() not in {".md", ".rst", ".txt", ""}:
            return True
    return False


def audit_layout(root: Path) -> tuple[str, list[str], list[str]]:
    """Check declared scope, or apply tentative layout checks if unmarked."""
    findings: list[str] = []
    warnings: list[str] = []
    readme = root / "README.md"
    declarations = (
        [
            line.split(":", 1)[1].strip()
            for line in readme.read_text(encoding="utf-8").splitlines()
            if line.startswith("Repository profile:")
        ]
        if readme.is_file()
        else []
    )
    if len(declarations) > 1 or (
        declarations and declarations[0] not in {"code", "website", "project"}
    ):
        return "UNKNOWN", ["Declare one valid Repository profile: code, website, or project."], []
    source = root / "src"
    website = root / "website"
    website_present = website.exists() or website.is_symlink()
    root_web_config = [
        pattern
        for pattern in WEBSITE_CONFIG_PATTERNS
        if any(path.is_file() for path in root.glob(pattern))
    ]
    # A README scope description can be valid without the recommended machine
    # marker. Use layout hints only for preliminary checks, never as identity.
    if declarations:
        profile = declarations[0]
    elif website_present:
        profile = "project" if has_source(source) else "website"
    elif root_web_config:
        profile = "website"
    else:
        profile = "code"
    if not declarations:
        warnings.append(
            f"No Repository profile declared; tentative {profile} layout check; confirm scope."
        )
    if profile in {"code", "project"} and not has_source(source):
        findings.append("Expected actual non-website source under root src/.")
    if profile == "code" and website_present:
        findings.append("Code profile has website/: declare project or website as appropriate.")
    if profile == "project" and not has_source(website, web=True):
        findings.append("Project profile needs actual website source under root website/.")
    if profile == "website":
        root_site = has_source(source, web=True)
        nested_site = has_source(website, web=True)
        if not root_site and not nested_site:
            findings.append("Website profile needs actual site source in src/ or website/.")
        if root_site and website_present:
            findings.append("Use one website source root; do not duplicate src/ and website/.")
        if source.is_symlink() or website.is_symlink():
            findings.append("Website source roots must not be symlinks.")
        if nested_site and source.exists():
            findings.append("Separate non-website src/ plus website/ belongs to Project profile.")
    if profile != "website" or website_present:
        for pattern in root_web_config:
            findings.append(f"Website framework configuration must follow site root: {pattern}")
    return profile if declarations else "UNKNOWN", findings, warnings


def audit_handoff(root: Path = ROOT) -> dict[str, object]:
    profile, findings, warnings = audit_layout(root)
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
        "repository_profile": profile,
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
