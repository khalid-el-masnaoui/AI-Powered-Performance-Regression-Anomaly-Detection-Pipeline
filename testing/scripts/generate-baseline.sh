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
