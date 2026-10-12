#!/usr/bin/env bash
# Production health-check script for EKS deployments
# Usage:
#   ./scripts/health-check.sh [BASE_URL]
# Examples:
#   ./scripts/health-check.sh http://k8s-default-ecommerc-*.us-east-1.elb.amazonaws.com
#   ./scripts/health-check.sh http://localhost:80

set -euo pipefail

BASE_URL="${1:-http://localhost:80}"
# Strip trailing slash
BASE_URL="${BASE_URL%/}"

echo "=========================================================="
echo " AWS EKS Polyglot Microservices Health Check"
echo " Target Endpoint: ${BASE_URL}"
echo "=========================================================="

services=("auth" "catalog" "inventory" "orders" "payments" "notifications" "analytics")
all_healthy=true

for svc in "${services[@]}"; do
  url="${BASE_URL}/api/${svc}/health"
  printf "Checking %-18s -> " "${svc}"

  if response=$(curl -fsS --max-time 5 "${url}" 2>/dev/null); then
    echo "✓ UP (${response})"
  else
    echo "✗ DOWN (${url})"
    all_healthy=false
  fi
done

echo "----------------------------------------------------------"
printf "Checking %-18s -> " "frontend UI"
if curl -fsS --max-time 5 "${BASE_URL}/" >/dev/null 2>&1; then
  echo "✓ UP"
else
  echo "✗ DOWN (${BASE_URL}/)"
  all_healthy=false
fi

echo "=========================================================="
if [ "$all_healthy" = true ]; then
  echo "✓ ALL SERVICES ARE HEALTHY ON EKS!"
  exit 0
else
  echo "⚠ ONE OR MORE SERVICES FAILED HEALTH CHECK."
  exit 1
fi
