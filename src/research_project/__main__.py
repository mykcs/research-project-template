"""Minimal software checks; no scientific result is implied."""

import argparse
import json
import sys
import tomllib
from pathlib import Path


def smoke(config: Path) -> dict[str, str]:
    with config.open("rb") as stream:
        data = tomllib.load(stream)
    if data.get("kind") != "software-smoke":
        raise ValueError("Expected a software-smoke config")
    return {"kind": "software-smoke", "status": "PASS", "scientific_result": "NOT_TESTED"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["doctor", "smoke", "reproduce"])
    parser.add_argument("--config", type=Path, default=Path("configs/smoke.toml"))
    args = parser.parse_args()
    if args.command == "doctor":
        print(json.dumps({"python": sys.version.split()[0], "gpu": "NOT_TESTED"}))
        return 0 if sys.version_info[:2] == (3, 12) else 1
    if args.command == "smoke":
        print(json.dumps(smoke(args.config)))
        return 0
    print("No scientific reproduction has been configured.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
