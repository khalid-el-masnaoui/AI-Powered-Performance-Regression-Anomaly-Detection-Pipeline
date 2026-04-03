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
