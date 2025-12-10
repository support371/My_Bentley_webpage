#!/bin/bash

BASE_URL="${BASE_URL:-http://127.0.0.1:5000}"

echo "============================================"
echo "Smoke Test for Bentley iTwin Webhooks MVP"
echo "============================================"
echo "Base URL: $BASE_URL"
echo ""

PASS=0
FAIL=0

test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local expected="$3"
    local data="$4"
    
    if [ "$method" = "GET" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
    fi
    
    if [ "$status" = "$expected" ]; then
        echo "[PASS] $method $endpoint -> $status"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $method $endpoint -> Expected $expected, got $status"
        FAIL=$((FAIL + 1))
    fi
}

echo "Testing endpoints..."
echo ""

test_endpoint "GET" "/" "200"
test_endpoint "GET" "/health" "200"
test_endpoint "POST" "/webhook" "200" '{"eventType":"test.event.v1","content":{}}'
test_endpoint "GET" "/events" "200"
test_endpoint "GET" "/dashboard" "200"
test_endpoint "GET" "/dashboard/feed" "200"
test_endpoint "GET" "/dashboard/feed?timeRange=24h" "200"

echo ""
echo "============================================"
echo "Results: $PASS passed, $FAIL failed"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi

exit 0
