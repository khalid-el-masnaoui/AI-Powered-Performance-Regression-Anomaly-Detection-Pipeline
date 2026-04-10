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

echo "Storing baseline..."


# -----------------------------
# Query Prometheus + store baseline
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
