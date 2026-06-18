#!/bin/bash
# SessionStart hook for Claude Code on the web.
#
# Installs the web-app's Python dependencies (the lif_core engine + FastAPI/test
# deps) into a dedicated venv so that `pytest` and `uvicorn` work in remote
# sessions. Kept out of the conda `sandbox-env` on purpose: the .githooks/pre-commit
# regenerates environment.yml from sandbox-env, and we don't want web deps there.
set -euo pipefail

# Only run in Claude Code on the web (remote) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

VENV="$CLAUDE_PROJECT_DIR/web-app/backend/.venv"

# Idempotent: only create the venv if it isn't there yet.
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --quiet --upgrade pip
# Editable install of the shared engine (absolute path: robust regardless of cwd).
"$VENV/bin/python" -m pip install --quiet -e "$CLAUDE_PROJECT_DIR/lif_core"
# Backend + test dependencies.
"$VENV/bin/python" -m pip install --quiet \
  "fastapi>=0.110" "uvicorn[standard]>=0.29" "pydantic>=2.6" "pytest>=7" "httpx>=0.27"

# Expose the venv's tools (pytest, uvicorn) for the rest of the session.
echo "export PATH=\"$VENV/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
