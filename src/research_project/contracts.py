"""Versioned input, release-manifest, asset, and output-isolation contracts."""

import hashlib
import json
import os
import tomllib
from pathlib import Path

RELEASE_MANIFEST_NAME = "RELEASE_MANIFEST.json"


def read_smoke_config(config: Path) -> dict[str, str | int]:
    """Validate and fingerprint the same input bytes, without modifying the source."""
    raw = config.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    if data.get("kind") != "software-smoke":
        raise ValueError("Expected a software-smoke config")
    unknown = set(data) - {"kind", "schema_version"}
    if unknown:
        raise ValueError(f"Unsupported config fields: {', '.join(sorted(unknown))}")
    # V0.1 configurations only declared kind; preserve that input as schema v1.
    version = data.get("schema_version", 1)
    if type(version) is not int or version != 1:
        raise ValueError("Unsupported smoke config schema_version; expected integer 1")
    return {
        "config_schema_version": version,
        "config_sha256": hashlib.sha256(raw).hexdigest(),
    }


def read_release_manifest(root: Path) -> dict[str, str] | None:
    """Read an optional, read-only release manifest for published snapshots."""
    manifest_path = root / RELEASE_MANIFEST_NAME
    if not manifest_path.exists():
        return None
    raw = manifest_path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Release manifest must be a JSON object")
    version = data.get("schema_version")
    if type(version) is not int or version != 1:
        raise ValueError("Unsupported release manifest schema_version; expected integer 1")
    commit = data.get("source_commit")
    if not isinstance(commit, str) or not commit.strip():
        raise ValueError("Release manifest requires a non-empty string source_commit")
    result = {
        "source_commit": commit.strip(),
        "source_dirty": "RELEASE_SNAPSHOT",
        "source_provenance": "release-manifest",
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
    }
    release_version = data.get("release_version")
    if isinstance(release_version, str) and release_version.strip():
        result["release_version"] = release_version.strip()
    return result


def verify_asset_manifest(manifest: Path, base_dir: Path | None = None) -> dict[str, object]:
    """Verify pinned external assets (URDF/USD/maps/checkpoints) via SHA-256 without mutating."""
    raw = manifest.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    version = data.get("schema_version")
    if type(version) is not int or version != 1:
        raise ValueError("Unsupported asset manifest schema_version; expected integer 1")
    assets = data.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("Asset manifest must contain a non-empty [[assets]] list")

    anchor = (base_dir or manifest.parent).resolve()
    verified: list[dict[str, str]] = []
    for entry in assets:
        if not isinstance(entry, dict):
            raise ValueError("Each asset entry must be a table")
        name = entry.get("name")
        rel_or_abs = entry.get("path")
        expected = entry.get("sha256")
        if not all(isinstance(v, str) and v.strip() for v in (name, rel_or_abs, expected)):
            raise ValueError("Each asset requires non-empty string name, path, and sha256")
        asset_path = Path(rel_or_abs)
        if not asset_path.is_absolute():
            asset_path = (anchor / asset_path).resolve()
        if not asset_path.is_file():
            raise ValueError(f"Missing asset '{name}': {asset_path}")
        actual = hashlib.sha256(asset_path.read_bytes()).hexdigest()
        if actual.lower() != expected.strip().lower():
            raise ValueError(
                f"SHA-256 mismatch for asset '{name}': expected {expected.strip()}, got {actual}"
            )
        verified.append({"name": name.strip(), "path": str(asset_path), "sha256": actual})
    return {
        "asset_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "verified_assets": verified,
    }


def validate_output_path(out: Path, root: Path, runtime_mode: bool = False) -> Path:
    """Refuse writing receipts/outputs into protected source trees or published releases."""
    resolved_root = root.resolve()
    resolved_out = out.resolve()
    protected_dirs = [resolved_root / "src", resolved_root / "configs", resolved_root / ".git"]
    for protected in protected_dirs:
        if resolved_out == protected or protected in resolved_out.parents:
            raise ValueError(f"Refusing to write output inside protected directory: {protected}")

    in_root = resolved_out == resolved_root or resolved_root in resolved_out.parents
    is_published = (resolved_root / RELEASE_MANIFEST_NAME).exists() or not os.access(
        resolved_root, os.W_OK
    )
    if in_root and (runtime_mode or is_published):
        raise ValueError(
            "Refusing to write output inside a read-only or shared runtime checkout; "
            "pass a personal output directory outside the checkout."
        )
    return resolved_out
