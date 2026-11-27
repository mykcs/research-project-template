#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$root"
command="${1:-}"
runtime="${RESEARCH_RUNTIME_PYTHON:-}"

usage() {
  cat <<'EOF'
Usage: ./run.sh <command>
  bootstrap   Prepare personal environment from uv.lock.
  doctor      Check environment and inputs; never installs dependencies.
  smoke       Software-only validation.
  audit       Advisory handoff and Git hygiene audit, not human acceptance.
  reproduce   Run declared scientific experiment (unconfigured in template).
  lint        Check code and formatting in prepared environment.
  test        Run tests in prepared environment.
  ci          Explicitly prepare personal environment and run software checks.
Set RESEARCH_RUNTIME_PYTHON to an approved shared interpreter for
doctor/smoke/audit/reproduce. See README and Dev for receipt/asset options.
EOF
}
case "$command" in
  -h|--help|help) usage; exit 0 ;;
  bootstrap|doctor|smoke|audit|reproduce|lint|test|ci) ;;
  *) usage >&2; exit 2 ;;
esac

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
  [[ -e "$root/RELEASE_MANIFEST.json" || -L "$root/RELEASE_MANIFEST.json" || ! -w "$root" ]]
}

unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
if [[ -n "$runtime" ]]; then
  case "$command" in
    doctor|smoke|audit|reproduce) ;;
    *) echo "Runtime mode is read-only; use a personal checkout for development checks." >&2; exit 2 ;;
  esac
  [[ "$runtime" = /* && -x "$runtime" ]] || {
    echo "RESEARCH_RUNTIME_PYTHON must be an absolute executable path." >&2
    exit 2
  }
  # Freeze directory aliases but keep the last executable symlink (venv semantics).
  runtime_dir="$(cd "$(dirname "$runtime")" && pwd -P)"
  runtime="$runtime_dir/$(basename "$runtime")"
  export PYTHONPATH="$root/src"
  export RESEARCH_RUNTIME_PYTHON="$runtime"
  exec "$runtime" -B -m research_project "$@"
fi
if is_shared_or_readonly; then
  echo "Shared or read-only checkout requires RESEARCH_RUNTIME_PYTHON; no uv sync." >&2
  exit 2
fi
[[ ! -L "$root/.venv" && ! -L "$root/.venv/bin" ]] || {
  echo "Refusing a symlinked project .venv; use an independent personal environment." >&2
  exit 2
}
export UV_PROJECT_ENVIRONMENT="$root/.venv"
python="$root/.venv/bin/python"
export PYTHONPATH="$root/src"
require_environment() {
  [[ -x "$python" ]] || {
    echo "Personal environment not prepared; run ./run.sh bootstrap or ./run.sh ci." >&2
    exit 2
  }
}
bootstrap() {
  uv lock --check
  uv sync --locked
}
case "$command" in
  bootstrap) bootstrap ;;
  doctor|smoke|audit|reproduce) require_environment; exec "$python" -B -m research_project "$@" ;;
  test) require_environment; "$python" -B -m pytest ;;
  lint) require_environment; "$python" -B -m ruff check .; "$python" -B -m ruff format --check . ;;
  ci)
    bootstrap
    require_environment
    "$python" -B -m research_project doctor
    "$python" -B -m ruff check .
    "$python" -B -m ruff format --check .
    "$python" -B -m pytest
    "$python" -B -m research_project smoke
    "$python" -B -m research_project audit
    ;;
esac
