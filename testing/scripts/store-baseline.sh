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
