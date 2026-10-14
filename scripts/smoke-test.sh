#!/usr/bin/env bash
# End-to-end check of a running StockPilot: full product lifecycle through the public URL.
#   BASE_URL=http://localhost:3000 ./scripts/smoke-test.sh        # docker compose
#   BASE_URL=http://stockpilot.local ./scripts/smoke-test.sh      # minikube ingress
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:3000}"
SKU="SMOKE-$(date +%s)"
pass() { printf '  \033[32m✔\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; exit 1; }
json() { python3 -c "import sys, json; print(json.load(sys.stdin)$1)"; }

echo "Smoke testing ${BASE_URL}"
curl -fsS "${BASE_URL}/api/info" | grep -q StockPilot && pass "GET /api/info" || fail "GET /api/info"

id=$(curl -fsS -X POST "${BASE_URL}/api/products" -H 'Content-Type: application/json' \
  -d "{\"sku\":\"${SKU}\",\"name\":\"Smoke test item\",\"category\":\"Testing\",\"quantity\":10,\"unit_price\":5}" | json "['id']")
pass "POST /api/products -> id ${id}"

[[ "$(curl -fsS "${BASE_URL}/api/products/${id}" | json "['quantity']")" == "10" ]] && pass "GET /api/products/${id}" || fail "GET product"

curl -fsS -X PUT "${BASE_URL}/api/products/${id}" -H 'Content-Type: application/json' -d '{"reorder_level":3}' | grep -q '"reorder_level":3' \
  && pass "PUT /api/products/${id}" || fail "PUT product"

bal=$(curl -fsS -X POST "${BASE_URL}/api/products/${id}/movements" -H 'Content-Type: application/json' \
  -d '{"movement_type":"SHIPPED","quantity":4,"note":"smoke"}' | json "['balance_after']")
[[ "$bal" == "6" ]] && pass "POST /api/products/${id}/movements (ship 4 -> 6 left)" || fail "movement"

code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE_URL}/api/products/${id}/movements" -H 'Content-Type: application/json' \
  -d '{"movement_type":"SHIPPED","quantity":99}')
[[ "$code" == "409" ]] && pass "over-shipping rejected with 409" || fail "expected 409, got ${code}"

curl -fsS "${BASE_URL}/api/stats" | grep -q total_products && pass "GET /api/stats" || fail "stats"

code=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "${BASE_URL}/api/products/${id}")
[[ "$code" == "204" ]] && pass "DELETE /api/products/${id}" || fail "delete returned ${code}"

echo "All smoke checks passed."
