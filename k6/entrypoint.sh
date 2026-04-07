#!/bin/bash

NGINX_URL="${NGINX_URL:-'http://nginx'}"
PROM_URL="${PROM_URL:-'http://prometheus:9090'}"
REGRESSION_URL="${REGRESSION_SERVICE_URL:-'http://regression-service:8090'}"


ROUTES=(
  "/"
  "/api/users"
)

#ROUTES=$(shell curl -s $NGINX_URL/routes)

sleep 10

echo "Starting baseline generation..."

# -----------------------------
# 1. Warmup
# -----------------------------
echo "warmup phase..."
for i in {1..20}; do
  curl -s $NGINX_URL/ > /dev/null
  curl -s $NGINX_URL/api/users > /dev/null
done

sleep 5

# -----------------------------
# 2. Load phase
# -----------------------------
echo "Running k6 baseline load..."
k6 run /scripts/baseline.js

echo "⏳ Waiting for Prometheus to collect data..."
sleep 5

# -----------------------------
# 3. Query Prometheus + store baseline
# -----------------------------
echo "Collecting metrics..."

for route in "${ROUTES[@]}"; do

  echo "======================================"
  echo "Processing route: $route"
  echo "======================================"

  # ---------------------------------------------------
  # P95
  # ---------------------------------------------------

  P95_QUERY="histogram_quantile(
    0.95,
    sum(rate(app_request_duration_seconds_bucket{route=\"$route\"}[2m])) by (le)
  )"

  P95=$(curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=$P95_QUERY" \
    | jq -r '.data.result[0].value[1]')

  # ---------------------------------------------------
  # P99
  # ---------------------------------------------------

  P99_QUERY="histogram_quantile(
    0.99,
    sum(rate(app_request_duration_seconds_bucket{route=\"$route\"}[2m])) by (le)
  )"

  P99=$(curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=$P99_QUERY" \
    | jq -r '.data.result[0].value[1]')

  # ---------------------------------------------------
  # AVG
  # ---------------------------------------------------

  AVG_QUERY="
    rate(app_request_duration_seconds_sum{route=\"$route\"}[2m])
    /
    rate(app_request_duration_seconds_count{route=\"$route\"}[2m])
  "

  AVG=$(curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=$AVG_QUERY" \
    | jq -r '.data.result[0].value[1]')


  # ---------------------------------------------------
  # ERROR RATE
  # ---------------------------------------------------

  ERROR_QUERY="
    sum(rate(app_requests_total{route=\"$route\",status=~\"5..\"}[2m]))
    /
    sum(rate(app_requests_total{route=\"$route\"}[2m]))
  "

  ERROR_RATE=$(curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=$ERROR_QUERY" \
    | jq -r '.data.result[0].value[1]')

    if [[ "$ERROR_RATE" == "null" || "$ERROR_RATE" == "NaN" || -z "$ERROR_RATE" ]]; then
        ERROR_RATE=0
    fi

  # ---------------------------------------------------
  # MAX LATENCY
  # ---------------------------------------------------

  MAX_QUERY="
    max_over_time(
      app_request_duration_seconds_sum{route=\"$route\"}[5m]
    )
  "

  MAX_LATENCY=$(curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=$MAX_QUERY" \
    | jq -r '.data.result[0].value[1]')

  # ---------------------------------------------------
  # THROUGHPUT
  # ---------------------------------------------------

  THROUGHPUT_RPS_QUERY="
    sum(rate(app_request_duration_seconds_count{route=\"$route\"}[1m]))
  "

  THROUGHPUT_RPS=$(curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=$THROUGHPUT_RPS_QUERY" \
    | jq -r '.data.result[0].value[1]')

  
  # ---------------------------------------------------
  # VALIDATION
  # ---------------------------------------------------

  if [ "$P95" == "null" ] || [ -z "$P95" ]; then
    echo "⚠️ No p95 data for $route"
    continue
  fi

  # ---------------------------------------------------
  # DEFAULTS
  # ---------------------------------------------------

  AVG=${AVG:-0}
  P99=${P99:-0}
  ERROR_RATE=${ERROR_RATE:-0}
  MAX_LATENCY=${MAX_LATENCY:-0}
  THROUGHPUT_RPS=${THROUGHPUT_RPS:-0}

  # ---------------------------------------------------
  # LOGGING
  # ---------------------------------------------------

  echo "Route        : $route"
  echo "P95          : $P95"
  echo "P99          : $P99"
  echo "AVG          : $AVG"
  echo "Error Rate   : $ERROR_RATE"
  echo "Max Latency  : $MAX_LATENCY"
  echo "Throughput   : $THROUGHPUT_RPS"

  # ---------------------------------------------------
  # SEND BASELINE
  # ---------------------------------------------------

  curl -s -X POST "$REGRESSION_URL/baseline" \
    -H "Content-Type: application/json" \
    -d "{
      \"route\": \"$route\",
      \"p95\": $P95,
      \"p99\": $P99,
      \"avg\": $AVG,
      \"error_rate\": $ERROR_RATE,
      \"max_latency\": $MAX_LATENCY,
      \"throughput\": $THROUGHPUT_RPS
    }" > /dev/null

done

echo "✅ Baseline generation complete"

# -----------------------------
# 4. Create regression by stimulating slow requests (you can replace this with any other method to create regressions, e.g., deploying a new version with a known performance issue)
# -----------------------------
echo "Stimulating slow requests..."
k6 run /scripts/ingest_slow_requests.js

echo "✅ k6 tests completed"
