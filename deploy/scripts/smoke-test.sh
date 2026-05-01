#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:-http://localhost}

echo "Checking API health"
curl -fsS "$BASE_URL/api/v1/health" || exit 1

echo "Checking ML service health"
curl -fsS "$BASE_URL/ml/health" || exit 1

echo "Smoke test passed"
