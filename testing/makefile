BASELINE_ROUTES=/,/api/users

baseline_traffic:
	@echo "testing baseline..."
	k6 run scripts/baseline.js

slow_traffic:
	@echo "testing slow requests alerts and spx profiling trigger..."
	k6 run scripts/ingest_slow_requests.js


regression-service-baseline:
	@echo "Running k6 baseline load..."
	k6 run scripts/baseline.js

	@echo "⏳ Waiting for Prometheus to collect data..."
	sleep 5
