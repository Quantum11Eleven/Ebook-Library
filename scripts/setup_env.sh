#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

python -m ensurepip --upgrade >/dev/null 2>&1 || true

if ! python -m pip install --upgrade pip setuptools wheel; then
  echo "Warning: Failed to upgrade pip/setuptools/wheel (likely due to missing network). Continuing with existing versions." 1>&2
fi

if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
  if ! python -m pip install -r "${PROJECT_ROOT}/requirements.txt"; then
    echo "Warning: Could not install packages from requirements.txt. Check your network connection or proxy settings." 1>&2
  fi
fi

if ! python -m pip install --no-build-isolation -e "${PROJECT_ROOT}"; then
  echo "Warning: Editable install failed. Ensure build requirements are available and rerun the script." 1>&2
  exit 1
fi

echo "Environment ready. Activate it with: source ${VENV_DIR}/bin/activate"
