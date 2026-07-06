#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
fail() { echo "verify-pack: $*" >&2; exit 1; }
[[ -f pack.yaml ]] || fail "missing pack.yaml"
id="$(grep '^id:' pack.yaml | head -1 | awk '{print $2}')"
ver="$(grep '^version:' pack.yaml | head -1 | awk -F'"' '{print $2}')"
[[ -n "${id}" ]] || fail "pack.yaml missing id"
[[ -n "${ver}" ]] || fail "pack.yaml missing version"
[[ -f assets/hub/server.py ]] || fail "missing assets/hub/server.py"
[[ -f assets/hub/routes/aws.py ]] || fail "missing assets/hub/routes/aws.py"
[[ -f assets/WORKSPACE.md ]] || fail "missing assets/WORKSPACE.md"
python3 -c "import ast; ast.parse(open('assets/hub/server.py').read())"
python3 -c "import ast; ast.parse(open('assets/hub/aws_common.py').read())"
"${ROOT}/scripts/verify-sidecar-smoke.sh"
"${ROOT}/scripts/build-pack-zip.sh" >/dev/null
echo "OK pack ${id} ${ver}"
