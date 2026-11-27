#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$root"
command="${1:-}"
runtime="${RESEARCH_RUNTIME_PYTHON:-}"

is_shared_or_readonly() {
  local prefixes="${RESEARCH_SHARED_PREFIXES:-/home/shared}"
  local IFS=':'
  local prefix
  for prefix in $prefixes; do
    [[ -n "$prefix" ]] || continue
    case "$root/" in
      "${prefix%/}/"*) return 0 ;;
    esac
  done
  [[ -f "$root/RELEASE_MANIFEST.json" || ! -w "$root" ]]
}

if [[ -n "$runtime" ]]; then
  [[ "$runtime" = /* && -x "$runtime" ]] || {
    echo "RESEARCH_RUNTIME_PYTHON must be an absolute executable path." >&2
    exit 2
  }
  case "$command" in
    doctor|smoke|reproduce|audit)
      unset PYTHONHOME
      export PYTHONPATH="$root/src" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
      exec "$runtime" -B -m research_project "$@"
      ;;
    *) echo "Runtime mode is read-only; use a personal checkout for development checks." >&2; exit 2 ;;
  esac
fi

if is_shared_or_readonly; then
  echo "Shared or read-only checkout requires RESEARCH_RUNTIME_PYTHON; no uv sync." >&2
  exit 2
fi
[[ ! -L "$root/.venv" ]] || {
  echo "Refusing a symlinked project .venv; use an independent personal environment." >&2
  exit 2
}
unset PYTHONPATH PYTHONHOME
export UV_PROJECT_ENVIRONMENT="$root/.venv"
case "$command" in
  doctor|smoke|reproduce|audit) uv run --locked python -m research_project "$@" ;;
  test) uv run --locked pytest ;;
  lint) uv run --locked ruff check .; uv run --locked ruff format --check . ;;
  ci)
    uv lock --check
    uv sync --locked
    uv run --locked --no-sync ruff check .
    uv run --locked --no-sync ruff format --check .
    uv run --locked --no-sync pytest
    uv run --locked --no-sync python -m research_project smoke
    uv run --locked --no-sync python -m research_project audit
    ;;
  *) echo "Usage: ./run.sh {doctor|smoke|reproduce|audit|test|lint|ci}" >&2; exit 2 ;;
esac
