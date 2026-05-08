# 🤖 AI-Powered Performance Regression Anomaly Detection Pipeline

A containerized **AI-Powered performance observability and automated regression anomaly detection system** for PHP applications.

This repository combines:

- ⚡ Nginx + PHP-FPM service with 📊 Prometheus metrics
- 🔥 SPX profiling and flamegraph collection
- 🚨 Prometheus alerting and Alertmanager integration
- 🤖 AI-Powered anomaly and regression detection using historical metrics
- 📄 PDF reporting of baselines and regressions
- 🧪 k6 load testing workflows for baseline and regression simulation


This project is intended as a practical demo of how to wire **PHP request metrics**, **alerting**,  **dynamic profiler activation**,  **automatic regression detection** using **AI-powered anaomaly detection service** and **historical trend analysis & tracking** together into a reproducible Docker-based performance observability & automated regression detection pipeline.

## Summary

This project is designed to detect performance regressions automatically by combining metrics, historical trends, AI anomaly scoring, and profiling.

Instead of using fixed thresholds like `p95 > baseline * 1.3`, it learns from historical performance patterns and computes:

- **anomaly score**
- **regression decision**
- **severity**
- **confidence score**
- **z-score based on the route history**

It also triggers SPX profiling for slow endpoints and generates PDF reports for baselines and detected regressions.


## Architecture

### Services
The stack is composed of the following services:

- `nginx` — HTTP front-end for the PHP application, metrics, flamegraph UI, and SPX JSON assets
- `php` — PHP-FPM application with Prometheus instrumentation and SPX auto-trigger
- **`redis`** — Used by SPX trigger logic and baseline storage
- `prometheus` — Scrapes application, Nginx, and PHP-FPM metrics
- `alertmanager` — Routes alerts to the regression service via webhook
- `grafana` — Dashboarding (optional, not configured in repo)
- `php-fpm-exporter` — Exposes PHP-FPM metrics to Prometheus
- `nginx-exporter` — Exposes Nginx metrics to Prometheus
- **`ai-service`** — Python AI anomaly detection endpoint at `/detect` using **`IsolationForest`** ML model
- **`regression-service`** — Regression analysis service with `/baseline`, `/alert`, `/check`
- **`report-service`** — PDF report generator for baselines and regressions
- **`k6`** — Load testing and baseline generation runner

### Data flow

1. k6 or users hit the PHP app through Nginx
2. PHP app records Prometheus metrics
3. Prometheus scrapes metrics and evaluates alerts
4. Alertmanager POSTs matched alerts to **`regression-service`** `/alert`
5. **`regression-service`** queries Prometheus and history, forwards data to **`ai-service`**
6. **`ai-service`** returns anomaly/regression verdict
7. If regression is detected:
   - SPX profiling is triggered
   - Slack notification is sent
   - PDF regression report is generated


## Project Structure

```bash
├── docker-compose.yml          # Main orchestration
├── alertmanager/               # Alert routing
├── k6/                         # Load testing scripts
├── nginx/                      # Web server config
├── php/                        # PHP-FPM setup
├── prometheus/                 # Metrics config
├── regression-service/         # Python regression detector
├── ai-service/                 # Python AI-based anomaly detection service
├── report-service/             # Python PDF generator
├── src/                        # PHP application
├── reports/                    # Generated PDFs
├── spx-data/                   # Flamegraph storage
└── testing/                    # Test utilities
└──.env.example                 #sample environment configuration
```

## Prerequisites

- Docker
- Docker Compose

Optional:
- `K6` & `jq` (only if need to test locally with `/testing`)


## Quick start

**1. Prepare environment**

Copy the example env file:

```bash
cp .env.example .env
```

Update values as needed, especially **`SLACK_WEBHOOK`**.

**2. Start the full stack**

```bash
docker compose up -d --build
```

**3. Validate services**

```bash
curl http://localhost:5200/health # ai anomaly detection service
curl http://localhost:8090/health # regression service
curl http://localhost:5000/health # report service
```

**4. Generate baseline and run test scenarios**

The k6 service is configured to:

- warm up the app
- run baseline traffic
- collect Prometheus metrics
- send baseline snapshots to `regression-service`
- simulate slow requests (gradual degradations & spikes)

**Note**: k6 traffic is automatically triggered the first time the application is up (using `k6/entrypoint.sh`), so you do not need to do anything. 
You can however manually generate traffic locally using `testing/makefile` or Run the k6 entrypoint directly:

```bash
# Run the k6 entrypoint directly
docker compose run --rm k6
docker compose logs -f k6 # follow logs

# or locally
cd testing/
make test-ai-anomaly-detection
```

**5. Inspect reports and flamegraphs**

- Baseline and regression PDFs are written to `./reports`
- SPX JSON profiles are written to `./spx-data`
- Flamegraph browser is available at `http://localhost:8080/flamegraphs`
- Prometheus UI: `http://localhost:9090`
- Grafana UI: `http://localhost:3000`
- Alertmanager UI: `http://localhost:9093`


## Endpoints & Routes

### Service Endpoints
| Service | URL | Notes |
|---|---|---|
| PHP App | http://localhost:8080 | Main web app routes and `/flamegraphs` |
| Prometheus | http://localhost:9090 | Scrapes app and exporter metrics |
| Alertmanager | http://localhost:9093 | Receives alerts from Prometheus |
| Grafana | http://localhost:3000 | Dashboarding (not provisioned by default) |
| Regression Service | http://localhost:8090 | Baseline, alert, manual checks |
| AI anomaly service | http://localhost:5200 | evaluate route performance data |
| Report Service | http://localhost:5100 | PDF generation endpoints |
| SPX Web UI | http://localhost:8080/?SPX_KEY=dev&SPX_UI=1&SPX_UI_URI=/ | PHP-SPX Profiling Web UI


### Application routes

- `/` — home route
- `/api/users` — sample API route
- `/api/users?delay=<seconds>` — simulate slow requests

### Metrics and profiling

- `/metrics` — Prometheus metrics endpoint
- `/flamegraphs` — searchable SPX flamegraph list
- `/spx-data/` — raw SPX JSON profile output
