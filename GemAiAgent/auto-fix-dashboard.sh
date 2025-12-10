#!/usr/bin/env bash
set -e

echo "=== AUTO DETECTING PUBLIC URL ==="

if [ -n "$REPLIT_DEPLOYMENT_URL" ]; then
  BASE_URL="$REPLIT_DEPLOYMENT_URL"
elif [ -n "$REPLIT_URL" ]; then
  BASE_URL="$REPLIT_URL"
else
  BASE_URL=$(curl -s http://localhost:3000 2>/dev/null && echo "http://localhost:3000")
fi

echo "BASE URL DETECTED:"
echo "$BASE_URL"
echo

echo "=== TESTING CORE ROUTES ==="

check() {
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$1")
  printf "%-30s => %s\n" "$1" "$CODE"
}

check "$BASE_URL/"
check "$BASE_URL/health"
check "$BASE_URL/events"
check "$BASE_URL/dashboard"
check "$BASE_URL/dashboard/feed"
check "$BASE_URL/dashboard/health"
check "$BASE_URL/dashboard/kpis"

echo
echo "=== FINAL DASHBOARD ACCESS URL ==="
echo "$BASE_URL/dashboard"
echo
echo "If that shows 200, your dashboard is LIVE."
