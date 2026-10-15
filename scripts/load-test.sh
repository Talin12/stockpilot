#!/usr/bin/env bash
# Generate sustained API load to drive the HPA and populate the Grafana dashboard.
#
#   URL=http://stockpilot.local ./scripts/load-test.sh            # 120s, 25 parallel workers
#   URL=http://<elb-dns> DURATION=300 CONCURRENCY=40 ./scripts/load-test.sh
#   URL=http://127.0.0.1:8081 HOST=stockpilot.local ./scripts/load-test.sh  # via port-forward, no /etc/hosts
#
# Watch it work in another terminal:
#   kubectl get hpa -n stockpilot -w
#   kubectl top pods -n stockpilot
set -euo pipefail

URL="${URL:-http://stockpilot.local}"
DURATION="${DURATION:-120}"
CONCURRENCY="${CONCURRENCY:-25}"
HOST="${HOST:-}"
host_header=()
[[ -n "$HOST" ]] && host_header=(-H "Host: ${HOST}")
PATHS=(/api/stats /api/products /api/products?stock_status=LOW_STOCK /api/movements?limit=50 /api/categories)

echo "Hammering ${URL} with ${CONCURRENCY} workers for ${DURATION}s ..."
end=$((SECONDS + DURATION))

worker() {
  local n=0 errors=0
  while (( SECONDS < end )); do
    path="${PATHS[$((RANDOM % ${#PATHS[@]}))]}"
    if ! curl -fsS -o /dev/null --max-time 5 ${host_header[@]+"${host_header[@]}"} "${URL}${path}"; then
      errors=$((errors + 1))
    fi
    n=$((n + 1))
  done
  echo "$n $errors"
}

pids=()
tmp="$(mktemp)"
for _ in $(seq "$CONCURRENCY"); do
  worker >>"$tmp" &
  pids+=($!)
done
wait "${pids[@]}"

awk '{req += $1; err += $2} END {printf "Done: %d requests, %d errors (%.1f req/s)\n", req, err, req / '"$DURATION"'}' "$tmp"
rm -f "$tmp"
