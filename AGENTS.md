# AGENTS.md

Minimal operating rules for AI coding agents in this repository. Keep this file short and non-redundant; do not duplicate directory listings already discoverable from files.

## Essential Commands
- Personal dev checks (before PR): `./run.sh ci` (lock check, ruff, pytest, smoke, handoff audit).
- Read-only shared runtime check (no `uv`, no writes to checkout):
  `RESEARCH_RUNTIME_PYTHON=/abs/path/to/python ./run.sh doctor|smoke|audit`
- Persist receipts outside checkout: `--receipt-out /path/to/personal_outputs/receipt.json`

## Hard Safety Boundaries
- **Never** modify shared/published directories, public simulation environments, other members' workspaces, or server permissions.
- **Never** run `uv sync`, `uv run`, or editable installs inside a shared/read-only checkout or public runtime environment.
- **Never** equate CPU CI, unit tests, mocks, or stitched clips with native simulation or real-robot scientific success. Unconfigured `reproduce` must fail closed.
- **Never** trigger GPU experiments, paid cloud runners, or automatic hosted CI without explicit approval.
- **Never** commit `.venv/`, checkpoints (`.pt/.pth/.onnx`), rosbag/mcap/USD binaries, or experiment outputs.

## Collaboration & Provenance
- Personal workspace: use agents freely to explore, prototype, and test.
- Shared branches / PRs: verify actual diff, tests, and interface impact before opening a PR; the submitter owns all AI-generated changes.
- Record real AI provenance (tool, model, role, verification basis) in PRs; mark unknown fields `Unknown` without guessing.
