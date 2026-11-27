"""Small, versioned input contract for the software-only template."""

import hashlib
import tomllib
from pathlib import Path


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
