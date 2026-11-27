#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd -P)"
cd "$root"
case "${1:-}" in
  doctor|smoke|reproduce) uv run --locked python -m research_project "$@" ;;
  test) uv run --locked pytest ;;
  lint) uv run --locked ruff check .; uv run --locked ruff format --check . ;;
  ci) uv lock --check; "$root/run.sh" lint; "$root/run.sh" test; "$root/run.sh" smoke ;;
  *) echo "Usage: ./run.sh {doctor|smoke|reproduce|test|lint|ci}" >&2; exit 2 ;;
esac
