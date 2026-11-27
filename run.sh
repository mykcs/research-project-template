#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
cd "$root"
command="${1:-}"
runtime="${RESEARCH_RUNTIME_PYTHON:-}"

usage() {
  cat <<'EOF'
Usage: ./run.sh <command>
  bootstrap   Prepare/update the personal environment from uv.lock.
  doctor      Read-only preflight; never installs dependencies.
  smoke       Software-only check; does not install dependencies.
  reproduce   Run the project's declared scientific reproduction.
  lint        Check code and formatting in the prepared environment.
  test        Run tests in the prepared environment.
  ci          Prepare the personal environment and run all software checks.
Set RESEARCH_RUNTIME_PYTHON to an approved shared Python interpreter for
doctor/smoke/reproduce only. No environment synchronization in runtime mode.
EOF
}
case "$command" in
  -h|--help|help) usage; exit 0 ;;
  bootstrap|doctor|smoke|reproduce|lint|test|ci) ;;
  *) usage >&2; exit 2 ;;
esac

unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1

if [[ -n "$runtime" ]]; then
  case "$command" in
    doctor|smoke|reproduce) ;;
    *) echo "Runtime mode is read-only; use a personal checkout for development checks." >&2; exit 2 ;;
  esac
  [[ "$runtime" = /* && -x "$runtime" ]] || {
    echo "RESEARCH_RUNTIME_PYTHON must be an absolute executable path." >&2
    exit 2
  }
  # Freeze a moving directory alias but preserve the final executable symlink:
  # resolving the Python binary itself could escape its virtual environment.
  runtime_dir="$(cd "$(dirname "$runtime")" && pwd -P)"
  runtime="$runtime_dir/$(basename "$runtime")"
  export PYTHONPATH="$root/src"
  exec "$runtime" -B -m research_project "$@"
fi

case "$root/" in
  /home/shared/*) echo "Shared checkout requires RESEARCH_RUNTIME_PYTHON; no uv sync." >&2; exit 2 ;;
esac
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
  doctor|smoke|reproduce)
    require_environment
    exec "$python" -B -m research_project "$@"
    ;;
  test)
    require_environment
    "$python" -B -m pytest
    ;;
  lint)
    require_environment
    "$python" -B -m ruff check .
    "$python" -B -m ruff format --check .
    ;;
  ci)
    bootstrap
    require_environment
    "$python" -B -m research_project doctor
    "$python" -B -m ruff check .
    "$python" -B -m ruff format --check .
    "$python" -B -m pytest
    "$python" -B -m research_project smoke
    ;;
esac
