#!/bin/bash

NGINX_URL="$PROM_URL"
REGRESSION_URL="http://localhost:8090"
PROM_URL="http://localhost:9090"

IFS=',' read -ra ROUTES <<< "$1"
