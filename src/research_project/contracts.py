"""Input, release, asset, and receipt contracts for software checks."""

import hashlib
import json
import os
import re
import tomllib
from pathlib import Path

RELEASE_MANIFEST_NAME = "RELEASE_MANIFEST.json"


def read_smoke_config(config: Path) -> dict[str, str | int]:
    raw = config.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    if data.get("kind") != "software-smoke":
        raise ValueError("Expected a software-smoke config")
    unknown = set(data) - {"kind", "schema_version"}
    if unknown:
        raise ValueError(f"Unsupported config fields: {', '.join(sorted(unknown))}")
    version = data.get("schema_version", 1)
    if type(version) is not int or version != 1:
        raise ValueError("Unsupported smoke config schema_version; expected integer 1")
    return {"config_schema_version": version, "config_sha256": hashlib.sha256(raw).hexdigest()}


def read_release_manifest(root: Path) -> dict[str, str] | None:
    path = root / RELEASE_MANIFEST_NAME
    if not path.exists() and not path.is_symlink():
        return None
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Release manifest must be a JSON object")
    version = data.get("schema_version")
    if type(version) is not int or version != 1:
        raise ValueError("Unsupported release manifest schema_version; expected integer 1")
    commit = data.get("source_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
        raise ValueError("Release manifest requires a full Git commit hash")
    result = {
        "source_commit": commit,
        "source_dirty": "UNKNOWN",
        "source_provenance": "release-manifest-declared",
        "source_integrity": "NOT_VERIFIED",
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
    }
    release_version = data.get("release_version")
    if isinstance(release_version, str) and release_version.strip():
        result["release_version"] = release_version.strip()
    return result


def verify_asset_manifest(manifest: Path) -> dict[str, object]:
    raw = manifest.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    version = data.get("schema_version")
    if type(version) is not int or version != 1:
        raise ValueError("Unsupported asset manifest schema_version; expected integer 1")
    assets = data.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("Asset manifest must contain a non-empty [[assets]] list")

    verified: list[dict[str, str]] = []
    names: set[str] = set()
    for entry in assets:
        if not isinstance(entry, dict):
            raise ValueError("Each asset entry must be a table")
        name, path, expected = (entry.get(k) for k in ("name", "path", "sha256"))
        if not all(isinstance(v, str) and v.strip() for v in (name, path, expected)):
            raise ValueError("Each asset requires name, path, sha256")
        if name in names or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise ValueError("Asset names must be unique and SHA-256 must be 64 hex digits")
        names.add(name)
        asset_path = (manifest.parent / path).resolve()
        if not asset_path.is_file():
            raise ValueError(f"Missing asset '{name}'")
        with asset_path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected.lower():
            raise ValueError(f"SHA-256 mismatch for asset '{name}'")
        verified.append({"name": name, "sha256": actual})
    return {"asset_manifest_sha256": hashlib.sha256(raw).hexdigest(), "verified_assets": verified}


def validate_output_path(out: Path, root: Path, runtime_mode: bool = False) -> Path:
    # This is a guard against mistakes, not an OS authorization boundary.
    root = root.resolve()
    if out.is_symlink():
        raise ValueError("Refusing a symlink receipt target")
    target = out.resolve()
    if target.exists():
        raise ValueError("Refusing to overwrite an existing receipt or file")
    if not target.parent.is_dir():
        raise ValueError("Receipt parent must be an existing personal output directory")
    in_root = target == root or root in target.parents
    published = (root / RELEASE_MANIFEST_NAME).exists() or not os.access(root, os.W_OK)
    if in_root and (runtime_mode or published):
        raise ValueError("Refusing output inside a read-only or shared runtime checkout")
    if in_root and not any(target.is_relative_to(root / folder) for folder in ("outputs", "runs")):
        raise ValueError(
            "Refusing output inside protected directory; use personal outputs/ or runs/"
        )
    prefixes = os.environ.get("RESEARCH_SHARED_PREFIXES", "/home/shared")
    for prefix in filter(None, prefixes.split(":")):
        if target.is_relative_to(Path(prefix).resolve()):
            raise ValueError("Refusing output in a configured shared directory")
    runtime = os.environ.get("RESEARCH_RUNTIME_PYTHON")
    if runtime and target.is_relative_to(Path(runtime).parent.parent.resolve()):
        raise ValueError("Refusing output inside the shared interpreter environment")
    return target


def write_receipt(out: Path, serialized: str) -> None:
    # Exclusive creation prevents clobbering source files or existing evidence.
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(serialized + "\n")
