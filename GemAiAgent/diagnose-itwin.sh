#!/usr/bin/env bash
set -euo pipefail

echo "=== 1) Environment (safe subset) ==="
echo "PWD: $(pwd)"
echo "NODE: $(node -v 2>/dev/null || echo 'not found')"
echo "NPM:  $(npm -v 2>/dev/null || echo 'not found')"
echo "REPLIT_DEPLOYMENT_URL: ${REPLIT_DEPLOYMENT_URL-}"
echo "REPLIT_URL: ${REPLIT_URL-}"
echo "REPL_URL: ${REPL_URL-}"
echo

echo "=== 2) Files (top-level) ==="
ls -la
echo

echo "=== 3) package.json (if any) ==="
if [ -f package.json ]; then
  cat package.json
else
  echo "package.json not found"
fi
echo

echo "=== 4) Entry candidates ==="
for f in index.js server.js app.js main.js; do
  if [ -f "$f" ]; then
    echo "--- $f ---"
    sed -n '1,200p' "$f"
    echo
  fi
done

echo "=== 5) Replit run config ==="
if [ -f .replit ]; then
  cat .replit
else
  echo ".replit not found"
fi
echo

echo "=== 6) Quick local route probe (if a server is running) ==="
BASE_LOCAL="http://127.0.0.1:${PORT-3000}"
echo "Assuming local base: $BASE_LOCAL"
for p in / /health /events /dashboard /dashboard/feed /dashboard/health /dashboard/kpis; do
  code="$(curl -s -o /dev/null -w "%{http_code}" "$BASE_LOCAL$p" || true)"
  printf "%-22s %s\n" "$p" "$code"
done
echo

echo "=== 7) What to check next ==="
echo "If /dashboard is 404 locally, your running file does not define the dashboard route."
echo "If /dashboard is 200 locally but 404 on the public URL, deployment is pointing at an older entrypoint."
