#!/bin/bash

NGINX_URL="$PROM_URL"
REGRESSION_URL="http://localhost:8090"
PROM_URL="http://localhost:9090"

IFS=',' read -ra ROUTES <<< "$1"


# ROUTES=(
#   "/"
#   "/api/users"
# )

#BASELINE_ROUTES=$(shell curl -s $PROM_URL/routes)

echo "Starting baseline generation..."

# -----------------------------
# 1. Warmup
# -----------------------------
echo "warmup phase..."
for i in {1..20}; do
  curl -s $PROM_URL/ > /dev/null
  curl -s $PROM_URL/api/users > /dev/null
done

sleep 5

# -----------------------------
# 2. Load phase
# -----------------------------
echo "Load phase..."
for i in {1..50}; do
  for route in "${ROUTES[@]}"; do
    curl -s "$PROM_URL$route" > /dev/null &
  done
done

wait
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
