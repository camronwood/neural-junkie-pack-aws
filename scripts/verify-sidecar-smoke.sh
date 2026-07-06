#!/usr/bin/env bash
# Smoke-test sidecar routes in dry-run mode (no AWS credentials required).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HUB="${ROOT}/assets/hub"
PORT="${NJ_AWS_SMOKE_PORT:-18792}"
export NJ_PACK_ID=aws
export NJ_PACK_DIR="${ROOT}"
export NJ_PACK_SETTINGS_JSON='{"aws_dry_run":true,"aws_profile":"smoke","aws_default_region":"us-east-2"}'

python3 "${HUB}/server.py" --port "${PORT}" &
PID=$!
cleanup() { kill "${PID}" 2>/dev/null || true; }
trap cleanup EXIT

for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; then
    break
  fi
  sleep 0.2
done

curl -sf "http://127.0.0.1:${PORT}/health" | grep -q '"ok"'
curl -sf -X POST "http://127.0.0.1:${PORT}/api/aws/get-caller-identity" \
  -H 'Content-Type: application/json' -d '{}' | grep -q '123456789012'
curl -sf -X POST "http://127.0.0.1:${PORT}/api/aws/describe-ec2-instances" \
  -H 'Content-Type: application/json' -d '{"page_size":5}' | grep -q 'dry_run'
curl -sf -X POST "http://127.0.0.1:${PORT}/api/aws/list-s3-buckets" \
  -H 'Content-Type: application/json' -d '{}' | grep -q 'example-bucket'
echo "OK sidecar smoke"
