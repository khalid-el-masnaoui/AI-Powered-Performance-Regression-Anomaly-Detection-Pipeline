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
