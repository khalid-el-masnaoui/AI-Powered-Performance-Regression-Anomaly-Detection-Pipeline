BASELINE_ROUTES=/,/api/users

baseline_traffic:
	@echo "testing baseline..."
	k6 run scripts/baseline.js

slow_traffic:
	@echo "testing slow requests alerts and spx profiling trigger..."
	k6 run scripts/ingest_slow_requests.js
