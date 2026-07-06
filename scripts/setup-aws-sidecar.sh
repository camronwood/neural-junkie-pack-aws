#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${NJ_AWS_VENV:-${HOME}/.neural-junkie/aws/venv}"
PY="${VENV}/bin/python3"

echo "Setting up AWS sidecar venv at ${VENV}..."
mkdir -p "$(dirname "${VENV}")"
if [[ ! -x "${PY}" ]]; then
  python3 -m venv "${VENV}"
fi
"${PY}" -m pip install --upgrade pip
"${PY}" -m pip install boto3 botocore PyYAML
echo "OK AWS sidecar ready: ${PY}"
