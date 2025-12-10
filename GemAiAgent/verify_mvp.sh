#!/usr/bin/env bash
set -e

BASE_URL="${BASE_URL:-https://bentley-itwins.replit.dev}"

echo "========================================"
echo "Bentley iTwin MVP Verification"
echo "BASE_URL: $BASE_URL"
echo "========================================"

check() {
  local path="$1"
  local label="$2"
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$path" || true)
  if [ "$code" = "200" ]; then
    echo "✅ $label ($path) OK"
  else
    echo "⚠️  $label ($path) HTTP $code"
  fi
}

check "/" "Service root"
check "/health" "Health"
check "/events" "Events"
check "/dashboard/feed" "Dashboard feed"
check "/dashboard/kpis" "Dashboard KPIs"
check "/dashboard/health" "Dashboard health"
check "/dashboard" "Dashboard UI"

echo "----------------------------------------"
echo "Tip: If /dashboard/* endpoints return 404,"
echo "the dashboard layer is not implemented in this repl yet."
echo "----------------------------------------"
