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
