#!/bin/bash

NGINX_URL="${NGINX_URL:-'http://nginx'}"
PROM_URL="${PROM_URL:-'http://prometheus:9090'}"
REGRESSION_URL="${REGRESSION_SERVICE_URL:-'http://regression-service:8090'}"


ROUTES=(
  "/"
  "/api/users"
)
