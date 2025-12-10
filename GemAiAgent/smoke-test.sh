#!/bin/sh

BASE_URL=\${BASE_URL:-https://bentley-itwins.replit.dev}

pass() { echo "PASS - \$1"; }
warn() { echo "WARN - \$1"; }
fail() { echo "FAIL - \$1"; }

code() { curl -s -o /dev/null -w "%{http_code}" "\$1"; }

echo "=============================================="
echo "SMOKE TEST: Bentley iTwin Dashboard MVP"
echo "Base URL: \$BASE_URL"
echo "=============================================="

overall_fail=0

c=\`code "\$BASE_URL/"\`
[ "\$c" = "200" ] && pass "GET /" || { fail "GET / (HTTP \$c)"; overall_fail=1; }

c=\`code "\$BASE_URL/health"\`
[ "\$c" = "200" ] && pass "GET /health" || warn "GET /health (HTTP \$c)"

c=\`code "\$BASE_URL/events"\`
[ "\$c" = "200" ] && pass "GET /events" || { fail "GET /events (HTTP \$c)"; overall_fail=1; }

c=\`code "\$BASE_URL/dashboard/feed?timeRange=24h"\`
[ "\$c" = "200" ] && pass "GET /dashboard/feed" || warn "GET /dashboard/feed (HTTP \$c)"

c=\`code "\$BASE_URL/dashboard/health"\`
[ "\$c" = "200" ] && pass "GET /dashboard/health" || warn "GET /dashboard/health (HTTP \$c)"

c=\`code "\$BASE_URL/dashboard/kpis"\`
[ "\$c" = "200" ] && pass "GET /dashboard/kpis" || warn "GET /dashboard/kpis (HTTP \$c)"

c=\`code "\$BASE_URL/dashboard"\`
[ "\$c" = "200" ] && pass "GET /dashboard (UI)" || warn "GET /dashboard (HTTP \$c)"

echo "----------------------------------------------"
[ "\$overall_fail" -eq 0 ] && echo "OVERALL STATUS: PASS" || echo "OVERALL STATUS: FAIL"
echo "----------------------------------------------"
echo "UI:     \$BASE_URL/dashboard"
echo "Events: \$BASE_URL/events?limit=50"
echo "Feed:   \$BASE_URL/dashboard/feed?timeRange=24h"
